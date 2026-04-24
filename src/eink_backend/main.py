from bs4 import BeautifulSoup
from contextlib import asynccontextmanager
from dataclasses import dataclass
import datetime
import logging
import shutil
from string import Template
import subprocess
from typing import Any, Dict, List, Optional, Set, Tuple
from pathlib import Path
import os
import re
from enum import Enum
from PIL import Image, ImageDraw, ImageFont
from fastapi.params import Query
from pyluach import dates, parshios
import zoneinfo
import traceback
import sqlite3

from apscheduler.schedulers.background import BackgroundScheduler

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse

from . import my_calendar, weather, efrat_zmanim, chores, seating, data_cache
from .config import LOCAL_TZ
from .chores_db import ChoresDatabase
from .chores_api import create_chores_router
from .chores_audit import cleanup_audit_log
from .chores_ui import generate_chores_ui_html
from .sync_chores_from_sheets import sync_chores_from_sheets

class CacheMissError(Exception):
    """Raised when required data is not available in the cache."""
    pass


def _setup_logging():
    """Configure logger to write to the screen."""
    logger = logging.getLogger()
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    return logger


_logger = _setup_logging()

FRIDAY = 4
SATURDAY = 5

# Data refresh interval for the background scheduler
_DATA_REFRESH_INTERVAL = datetime.timedelta(minutes=15)

root_dir = Path(os.path.abspath(__file__)).parent.parent.parent
"""This should point to the parent of the `src` directory"""
out_dir = Path("/tmp/eink-display")
out_dir.mkdir(parents=True, exist_ok=True)


def _is_data_type_relevant_at_time(data_type: str, now_utc: datetime.datetime) -> bool:
    """
    Determine if a data type is relevant for display at the given time.
    
    This centralizes the logic for when each data type should be shown:
    - Always shown: zmanim, weather, calendar
    - Friday before 16:00: chores (displayed instead of seating)
    - Friday after 16:00 or Saturday 10:00-13:00: seating (displayed instead of chores)
    
    Args:
        data_type: The type of data ("zmanim", "weather", "calendar", "chores", "seating")
        now_utc: The current datetime to check relevance for
        
    Returns:
        True if the data type is relevant for display at the given time
    """
    assert(now.tzinfo is None or now.tzinfo.utcoffset(now) == datetime.timedelta(0)), "now_utc must be timezone-aware in UTC"
    now = now_utc.replace(tzinfo=LOCAL_TZ)
    wkday = now.weekday()
    hour = now.hour
    
    # Always relevant data types
    if data_type in ("zmanim", "weather", "calendar"):
        return True
    
    # TODO: Make sure this times match the template-choosing code
    # Conditional data types
    if data_type == "chores":
        # Chores are shown Friday until 16:00
        return wkday == FRIDAY and hour < 16
    
    if data_type == "seating":
        # Seating is shown Friday after 16:00 or Saturday 10:00-13:00
        return (wkday == FRIDAY and hour >= 16) or (wkday == SATURDAY and 10 <= hour <= 13)
    
    return False

# Global scheduler instance
scheduler: Optional[BackgroundScheduler] = None

# Global chores database instance
chores_db: Optional[ChoresDatabase] = None


def collect_all_data_task():
    """
    Background task that collects all data and updates the cache.
    Called every DATA_REFRESH_INTERVAL by the scheduler.
    Each data type is only refreshed if it has expired.
    """
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    _logger.info("Starting scheduled data collection task")

    data_types = [
        ("zmanim", lambda: efrat_zmanim.collect_data(now_utc=now_utc)),
        ("weather", lambda: weather.collect_data(now_utc=now_utc)),
        ("calendar", lambda: my_calendar.collect_data()),
        ("chores", lambda: chores.collect_data(now_utc=now_utc)),
        ("seating", lambda: seating.collect_data(now_utc=now_utc)),
    ]

    for data_type, fetch_fn in data_types:
        try:
            # Check if data is expired
            if data_cache.is_data_expired(data_type, now_utc=now_utc):
                _logger.info(f"Collecting fresh {data_type} data")
                data = fetch_fn()
                if data is not None:
                    data_cache.save_cached_data(data_type, data, now_utc=now_utc)
            else:
                _logger.debug(f"Skipping {data_type} - still fresh")
        except Exception as ex:
            _logger.error(f"Error collecting {data_type}: {ex}")
            traceback.print_exc()

    _logger.info("Scheduled data collection task completed")


def cleanup_audit_log_task():
    """
    Background task that cleans up old audit log entries.
    Runs daily, removing entries older than 365 days.
    """
    global chores_db
    if not chores_db:
        _logger.warning("Chores database not initialized; skipping audit cleanup")
        return
    
    try:
        session = chores_db.get_session()
        try:
            count = cleanup_audit_log(session, days_to_keep=365)
            _logger.info(f"Audit log cleanup completed: removed {count} old entries")
        finally:
            session.close()
    except Exception as ex:
        _logger.error(f"Error cleaning up audit log: {ex}")
        traceback.print_exc()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the database on startup, start the scheduler, and clean up on shutdown."""
    global scheduler, chores_db

    # Initialize the cache database
    data_cache.init_db(_logger)
    data_cache.clean_expired_records(older_than_days=30)
    _logger.info("Cache database initialized.")

    # Initialize the chores database
    database_path = root_dir / "chores.sqlite"
    database_url = f"sqlite:///{database_path}"
    chores_db = ChoresDatabase(database_url)
    chores_db.init_db()
    _logger.info("Chores database initialized.")

    # Register chores router (must happen before OpenAPI schema generation)
    router = create_chores_router(chores_db)
    app.include_router(router)
    _logger.info("Chores API router registered.")

    # Optionally sync chores from Google Sheets on startup
    if os.getenv("SYNC_CHORES_FROM_SHEETS", "").lower() == "true":
        try:
            _logger.info("Syncing chores from Google Sheets...")
            sync_chores_from_sheets(chores_db)
            _logger.info("Chores sync from Google Sheets completed.")
        except Exception as e:
            _logger.error(f"Error syncing chores from Google Sheets: {e}")
            # Don't fail startup if sync fails, just log the error
            pass

    # Start the background scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        collect_all_data_task,
        'interval',
        seconds=int(_DATA_REFRESH_INTERVAL.total_seconds()),
        id='collect_all_data',
        name=f'Collect all data every {int(_DATA_REFRESH_INTERVAL.total_seconds() / 60)} minutes'
    )
    scheduler.add_job(
        cleanup_audit_log_task,
        'cron',
        hour=2,
        minute=0,
        id='cleanup_audit_log',
        name='Cleanup old audit log entries daily at 2 AM'
    )
    scheduler.start()
    _logger.info(f"Background scheduler started (collecting data every {int(_DATA_REFRESH_INTERVAL.total_seconds() / 60)} minutes).")

    yield

    # Shutdown the scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown()
        _logger.info("Background scheduler stopped.")
    
    # Close the chores database
    if chores_db:
        chores_db.close()
        _logger.info("Chores database closed.")


app = FastAPI(lifespan=lifespan)


@app.get("/")
def read_root():
    return {"Help": "Go to '/docs' for API docs, or '/chores' for the chores UI"}


@app.get("/chores", response_class=HTMLResponse)
def chores_ui():
    """Single-page web application for managing chores."""
    return generate_chores_ui_html()


def untaint_filename(filename: str) -> str:
    return re.sub(r"[^a-zA-Z_-]", "_", filename)


def image_to_mono(src: Image.Image):
    THRESH = 200
    fn = lambda x: 255 if x > THRESH else 0
    return src.convert("L").point(fn, mode="1")


def convert_png_to_mono_png(src: Path, dest: Path) -> Path:
    src_image = Image.open(src)
    mono_image = image_to_mono(src_image)
    mono_image.save(dest)

class ColorName(str, Enum):
    """Valid color names for the e-ink display output."""
    RED = "red"
    BLACK = "black"
    JOINED = "joined"

_VALID_COLOR_NAMES = [color.value for color in ColorName]

def _is_valid_color(color: str) -> bool:
    return color in _VALID_COLOR_NAMES

def clip_image_to_device_dimensions_in_place(file_to_modify: Path, color: str) -> None:
    DEVICE_HEIGHT = 880
    DEVICE_WIDTH = 528

    image = Image.open(file_to_modify)
    if image.width > DEVICE_WIDTH or image.height > DEVICE_HEIGHT:
        text = "Image too large."
        if image.width > DEVICE_WIDTH:
            text += (
                f" Width of image is {image.width}, exceeding max of {DEVICE_WIDTH}."
            )
        if image.height > DEVICE_HEIGHT:
            text += (
                f" Height of image is {image.height}, exceeding max of {DEVICE_HEIGHT}."
            )
        print(text)
        font_size = 10
        font = ImageFont.truetype(str(root_dir / "assets/fonts/arial.ttf"), font_size)
        draw = ImageDraw.Draw(image)
        left, top, right, bottom = font.getbbox(text)
        text_width = bottom - top
        text_height = right - left
        text_x = DEVICE_WIDTH - text_width
        text_y = DEVICE_HEIGHT - text_height

        text_fill = (0, 0, 0)
        if color in ("red", "black"):
            text_fill = 0
        draw.text((text_x, text_y), text, font=font, fill=text_fill)
        draw.text((text_x, text_y), text, font=font, fill=text_fill)
        cropped_image = image.crop((0, 0, DEVICE_WIDTH, DEVICE_HEIGHT))
        cropped_image.save(file_to_modify)


def render_html_template_single_color(color: str, html_content: str) -> Path:
    content_filename = "/tmp/content.html"
    Path(content_filename).write_text(data=html_content, encoding="utf-8")
    out_firefox_filename = f"/app/tmp/firefox-{color}.png"
    p = subprocess.run(
        [
            "firefox",
            "--screenshot",
            out_firefox_filename,
            "--window-size=528",
            f"file://{content_filename}",
        ],
        timeout=60,
    )
    p.check_returncode()
    p = subprocess.run(["chmod", "666", out_firefox_filename])
    p.check_returncode()

    out_path = out_dir / f"{color}.png"
    make_mono = color in ("red", "black")
    if make_mono:
        convert_png_to_mono_png(src=out_firefox_filename, dest=out_path)
    else:
        shutil.copy(src=out_firefox_filename, dst=str(out_path))
    clip_image_to_device_dimensions_in_place(file_to_modify=out_path, color=color)
    return out_path


def is_tset_soon(tset_shabat: datetime.datetime, now_utc: datetime.datetime) -> bool:
    if not tset_shabat:
        return False
    TSET_IS_SOON = datetime.timedelta(hours=2)
    diff: datetime.timedelta = tset_shabat - now_utc
    return diff.total_seconds() > 0 and diff <= TSET_IS_SOON


def omer_count(now_utc: datetime.datetime, now_is_after_starlight: bool): 

    def calc_omer_count(today: datetime.date) -> Optional[int]:
        today_heb = dates.HebrewDate.from_pydate(today)
        OMER_ZERO = dates.HebrewDate(year=today_heb.year, month=1, day=15).to_pydate()
        if today <= OMER_ZERO:
            return None
        delta = today - OMER_ZERO
        MAX_OMER = 49
        if delta.days <= 0 or delta.days > MAX_OMER:
            return None
        return delta.days

    today = now_utc.date()
    LAST_SECOND = datetime.time(hour=23, minute=59, second=59)
    if now_is_after_starlight and now_utc.time() <= LAST_SECOND:
        # show the count for tomorrow, since it's already time for it
        today = today + datetime.timedelta(days=1)
    count = calc_omer_count(today)
    if not count:
        return None
    display_text = f"{count} בעומר"
    if count > 7:
        display_text = f"{count // 7} * 7 + {count % 7} = {count} בעומר "
    if not now_is_after_starlight:
        display_text = "(אתמול) " + display_text
    return display_text


def _is_now_after_starlight(now_utc: datetime.datetime, tzet_shabbat: Optional[str]) -> bool:
    """
    Returns true if `now` is after the stars have come out.
    Used for checking if Shabbat is already over.
    """
    starlight_estimate_s = tzet_shabbat
    if not starlight_estimate_s:
        return False
    hour_s = starlight_estimate_s[0:2]
    minute_s = starlight_estimate_s[3:5]
    starlight = datetime.time(hour=int(hour_s), minute=int(minute_s))
    print(f"'{starlight=}'")
    if now_utc.time() > starlight:
        return True
    return False


def collect_all_values_of_data(
    zmanim: Optional[efrat_zmanim.ShabbatZmanim],
    weather_forecast: weather.WeatherForecast,
    calendar_content: str,
    chores_content: chores.ChoreData,
    seating_content: seating.SeatingData,
    color: str,
    now_utc: datetime.datetime,
) -> Dict[str, Any]:
    heb_date = dates.HebrewDate.from_pydate(now_utc.date())
    if zmanim:
        try:
            parasha = parshios.getparsha_string(heb_date, israel=True, hebrew=True)
            if not parasha and zmanim and zmanim.name:
                parasha = zmanim.name
            zmanim_dict = {
                "parasha": parasha,
                **{k: v for k, v in zmanim.times.items()},
            }
        # TODO: Can I do this try/except in some more uniform manner (print_exception_on_screen, and set value to {"error": "message of error"} or something)
        except Exception as ex:
            print(f"Warning: Could not collect zmanim data. Exception: {ex}")
            # TODO: indent
            traceback.print_exc()
            zmanim_dict = {"Error": str(ex)}
    else:
        print("Warning: no zmanim data available.")

    now_is_after_starlight = _is_now_after_starlight(now_utc=now_utc, tzet_shabbat=zmanim_dict.get("tzet_shabat", None))
    omer = omer_count(now_utc=now_utc, now_is_after_starlight=now_is_after_starlight)

    weather_dict = {"weather_report": ""}
    try:
        # print(f"Collecting weather report with forecast: {weather_forecast}")
        weather_report = weather.weather_report(
            weather_forecast=weather_forecast, color=color
        )
        if weather_report:
            weather_dict["weather_report"] = weather_report
    except Exception as ex:
        msg = f"Exception colecting error report: {ex}"
        weather_dict["weather_report"] = msg
        print(msg)

    if zmanim and is_tset_soon(zmanim.times.get("tset_shabat_as_datetime", None), now_utc=now_utc):
        additional_css = """
            #shul { display: none; }
            #test-big { display: block; }
        """
    else:
        additional_css = """
            #tset-big { display: none; }
        """
    now_local = now_utc.astimezone(LOCAL_TZ)
    page_dict = {
        "day_of_week": now_local.date().strftime("%A"),
        "date": now_local.date().strftime("%-d of %B %Y"),
        "render_timestamp": now_local.strftime("%Y-%d-%m %H:%M:%S"),
        "heb_date": heb_date.hebrew_date_string(),
        "additional_css": additional_css,
    }
    calendar_dict = {"calendar_content": calendar_content}

    if chores_content.error:
        chores_str = chores_content.error
    else:
        chores_str = chores.render_chores(
            chores=chores_content.chores, now_utc=now_utc, color=color
        )
    chores_dict = {
        "chores_content": chores_str,
    }
    omer_dict = {
        "omer": f"{omer}",
        "omer_display": "inline" if omer else "none",
    }
    seating_dict: Dict[str, str] = {}
    for seat in seating_content.seats:
        seating_dict[f"seat{seat.number}"] = seat.name
    all_values = {
        **zmanim_dict,
        **page_dict,
        **weather_dict,
        **calendar_dict,
        **chores_dict,
        **seating_dict,
        **omer_dict,
    }
    return all_values


def replace_css_link_with_css_content(html_content:str) -> str:
    new_content = ""
    lines = html_content.splitlines()
    for line in lines:
        if "<link" not in line:
            new_content += line + "\n"
            continue

        if 'rel="stylesheet"' not in line:
            print("Warning: Found 'link' tag that isn't a stylesheet:\n\t" + line)
            continue

        soup = BeautifulSoup(line, 'html.parser')
        link_tag = soup.find('link')
        href_value = link_tag.get('href')
        css_path:Optional[Path] = None
        href_path = Path(href_value)
        if href_path.parent == Path("/css"):
            css_path = Path("/app/assets/" + href_path.name)
        else:
            raise FileNotFoundError(href_value)
        if not css_path.exists():
            raise FileNotFoundError(css_path)
        css_content = css_path.read_text(encoding="utf-8")
        css_in_html = f"\n<!-- {str(href_value)} -->\n<style>\n{css_content}\n</style>\n"
        new_content += css_in_html
    return new_content


def load_template_from_file(file: Path) -> Tuple[Template, List[str]]:
    template_text = file.read_text(encoding="utf-8")
    template_text = replace_css_link_with_css_content(template_text)
    p = re.compile("\\$[a-z_]+")
    template_required_keys = set(p.findall(template_text)) - set(["$color"])
    template = Template(template_text)
    return (template, template_required_keys)


def load_template_by_time(now_utc: datetime.datetime) -> Tuple[Template, List[str]]:
    now_local = now_utc.astimezone(LOCAL_TZ)
    wkday = now_local.weekday()
    hour = now_local.hour

    # Default template is shabbat
    template_path = Path("/app/assets/layout-shabbat.html")
    # Friday until 16:00, use the chore template
    if wkday == FRIDAY and hour < 16:
        template_path = Path("/app/assets/layout-choreday.html")
    # Friday and Shabbat, around meal-time, show seating layout
    # (Uses the same logic as _is_data_type_relevant_at_time for seating)
    if (wkday == FRIDAY and hour >= 16) or (wkday == SATURDAY and 10 <= hour <= 13):
        template_path = Path("/app/assets/layout-shabbat-seating.html")
    return load_template_from_file(file=template_path)


def find_missing_template_keys(
    all_values: Dict[str, Any], template_required_keys: Set[Any]
):
    dollar_keys = set([f"${x}" for x in all_values.keys()])
    missing_keys = template_required_keys - dollar_keys
    if missing_keys:
        print(
            "Warning: the following template variable missing.\n"
            "They will be replaced by a placeholder:\n" + str(missing_keys)
        )
        # raise KeyError("Required keys are missing:", missing_keys)
        # Fill in the missing keys, to avoid failing
    return missing_keys


def generate_html_content(color: str, now_utc: datetime.datetime, force_refresh: bool = False) -> str:
    collected = collect_data(now_utc=now_utc, force_refresh=force_refresh)
    try:
        all_values = collect_all_values_of_data(
            zmanim=collected.zmanim,
            weather_forecast=collected.weather_forecast,
            calendar_content=collected.calendar_content,
            chores_content=collected.chores_content,
            seating_content=collected.seating_content,
            color=color,
            now_utc=now_utc,
        )
    # TODO: Can I do this try/except in some more uniform manner (print_exception_on_screen, and set value to {"error": "message of error"} or something)
    except Exception as ex:
        print("Warning: Could not collect all values of data.")
        # TODO: indent the exception under the warning
        traceback.print_exc()
        all_values = {"Error": str(ex)}
    (template, template_required_keys) = load_template_by_time(now_utc=now_utc)
    missing_keys = find_missing_template_keys(
        all_values=all_values, template_required_keys=template_required_keys
    )
    # Fill in missing keys
    for k in missing_keys:
        all_values[k[1:]] = "[ERR]"
    all_values["color"] = color
    return template.substitute(**all_values)


def render_html_template(color: str, now_utc: datetime.datetime, force_refresh: bool = False):
    html_content = generate_html_content(color=color, now_utc=now_utc, force_refresh=force_refresh)
    render_html_template_single_color(color=color, html_content=html_content)


def get_filename(color: str) -> Path:
    if not _is_valid_color(color):
        raise HTTPException(
            status_code=404,
            detail=f"Invalid image name. Acceptable names: {_VALID_COLOR_NAMES}",
        )
    return out_dir / (color + ".png")


@dataclass
class PageData:
    zmanim: Optional[efrat_zmanim.ShabbatZmanim]
    weather_forecast: Optional[weather.WeatherForecast]
    calendar_content: str
    chores_content: chores.ChoreData
    seating_content: seating.SeatingData


def get_cached_data_or_error(data_type: str, now_utc: datetime.datetime, force_refresh: bool = False) -> Any:
    """
    Retrieve data from cache, or fetch fresh if force_refresh is True.

    Args:
        data_type: The type of data to retrieve
        now_utc: Current time for reference
        force_refresh: If True, bypass cache and fetch fresh data

    Returns:
        The cached or freshly-fetched data

    Raises:
        CacheMissError: If data is missing from cache and force_refresh is False
    """
    if force_refresh:
        # Bypass cache and fetch fresh data
        _logger.info(f"force_refresh=True, fetching fresh {data_type} data")
        if data_type == "zmanim":
            return efrat_zmanim.collect_data(now_utc=now_utc)
        elif data_type == "weather":
            return weather.collect_data(now_utc=now_utc)
        elif data_type == "calendar":
            return my_calendar.collect_data()
        elif data_type == "chores":
            return chores.collect_data(now_utc=now_utc)
        elif data_type == "seating":
            return seating.collect_data(now_utc=now_utc)
    
    # Try to get from cache
    cached_result = data_cache.get_cached_data(data_type, now_utc=now_utc)
    if cached_result:
        data, timestamp = cached_result
        return data
    
    # Data not in cache
    raise CacheMissError(f"No cached data available for {data_type}. Try again with \"force_refresh=true\".")


def collect_data(now_utc: datetime.datetime, force_refresh: bool = False):
    """
    Collect all page data from cache.

    Args:
        now_utc: Current time for reference
        force_refresh: If True, bypass cache and fetch fresh data for all sources

    Returns:
        PageData with all current data

    Raises:
        CacheMissError: If any required data is not in cache (unless force_refresh=True)
    """
    return PageData(
        zmanim=get_cached_data_or_error("zmanim", now_utc=now_utc, force_refresh=force_refresh),
        weather_forecast=get_cached_data_or_error("weather", now_utc=now_utc, force_refresh=force_refresh),
        calendar_content=get_cached_data_or_error("calendar", now_utc=now_utc, force_refresh=force_refresh),
        chores_content=get_cached_data_or_error("chores", now_utc=now_utc, force_refresh=force_refresh),
        seating_content=get_cached_data_or_error("seating", now_utc=now_utc, force_refresh=force_refresh),
    )


def render_one_color(color: str, now_utc: datetime.datetime, force_refresh: bool = False):
    color = untaint_filename(color)
    render_html_template(color=color, now_utc=now_utc, force_refresh=force_refresh)
    filename = get_filename(color=color)

_DATETIME_FORMAT_IN_URL = "%Y%m%d-%H%M%S"
_DATETIME_FORMAT_WITH_TZ = "%Y%m%d-%H%M%S%z"

@app.get("/html-dev/{color}", response_class=HTMLResponse)
async def html_dev(color: ColorName, at: Optional[str] = None, force_refresh: bool = False):
    """
    Generates and returns HTML content for the specified color.
    
    Args:
        color: The color variant (red, black, joined)
        at: Optional datetime to render (format: "%Y%m%d-%H%M%S", must be UTC timezone). Defaults to current UTC time.
        force_refresh: If True, bypass cache and fetch fresh data
    """
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    if at:
        now_utc = datetime.datetime.strptime(at, _DATETIME_FORMAT_IN_URL).replace(tzinfo=datetime.timezone.utc)
    try:
        html = generate_html_content(color=color.value, now_utc=now_utc, force_refresh=force_refresh)
    except CacheMissError as e:
        raise HTTPException(
            status_code=503,
            detail=str(e)
        )
    now_as_string = f'<!-- at={now_utc.strftime(_DATETIME_FORMAT_WITH_TZ)} -->\n'
    return now_as_string + html


@app.get("/render/{color}")
async def render_endpoint(color: ColorName, force_refresh: bool = False):
    now = datetime.datetime.now(datetime.timezone.utc)
    try:
        render_one_color(color=color.value, now_utc=now, force_refresh=force_refresh)
    except CacheMissError as e:
        raise HTTPException(
            status_code=503,
            detail=str(e)
        )
    return f"Rendered {color.value}. Waiting for download."


@app.get("/eink/{color}", response_class=FileResponse)
async def eink(color: ColorName, at: Optional[str] = None, force_refresh: bool = False):
    """
    Returns the rendered image file for the specified color.
    
    Args:
        color: The color variant (red, black, joined)
        at: Optional datetime to render (format: "%Y%m%d-%H%M%S", must be UTC timezone). Defaults to current UTC time.
        force_refresh: If True, bypass cache and fetch fresh data
    """
    color_str = color.value
    color_str = untaint_filename(color_str)
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    if at:
        datetime.datetime.strptime(at, _DATETIME_FORMAT_IN_URL).replace(tzinfo=datetime.timezone.utc)
    try:
        # always render "joined", since it's for dev work
        if color_str == "joined" or color_str == "black":
            render_one_color(color=color_str, now_utc=now_utc, force_refresh=force_refresh)
    except CacheMissError as e:
        raise HTTPException(
            status_code=503,
            detail=str(e)
        )
    image_path = get_filename(color=color_str)
    if not image_path.exists():
        raise HTTPException(
            status_code=404,
            detail="The requested image could not be found. "
            "Did you render it first?",
        )
    return str(image_path)


@app.get("/image-cache/{filename}", response_class=FileResponse)
async def read_image_from_cache(filename: str):
    file = Path(f"/image-cache/{filename}")
    if file.exists():
        return str(file)
    else:
        raise HTTPException(
            status_code=404,
            detail="The requested image could not be found.",
        )

@app.get("/css/{filename}")
async def read_css_file(filename: str):
    file = Path(f"/app/assets/{filename}")
    if file.exists():
        return FileResponse(str(file), media_type="text/css")
    else:
        raise HTTPException(
            status_code=404,
            detail="The requested CSS file could not be found.",
        )



@app.get("/cache-status")
async def cache_status(client_last_updated_at: Optional[str] = Query(None, example="20260327-100000")):
    """
    Debug endpoint: returns the current state of all cached data.
    
    Args:
        client_last_updated_at: Optional datetime when client last updated (format: "%Y%m%d-%H%M%S", must be UTC timezone).
                                Used to determine if client needs to refresh.
    """
    import sqlite3
    
    now = datetime.datetime.now(datetime.timezone.utc)
    client_last_updated_at_dt = None
    if client_last_updated_at:
        client_last_updated_at_dt = datetime.datetime.strptime(client_last_updated_at, _DATETIME_FORMAT_IN_URL)
        # Ensure timezone-aware by adding UTC if naive
        if client_last_updated_at_dt.tzinfo is None:
            client_last_updated_at_dt = client_last_updated_at_dt.replace(tzinfo=datetime.timezone.utc)
    cache_info = {}
    
    try:
        conn = sqlite3.connect(str(data_cache.DB_PATH))
        cursor = conn.cursor()
        
        cursor.execute("SELECT data_type, timestamp, expiration FROM data_cache")
        rows = cursor.fetchall()
        conn.close()
        
        for data_type, timestamp_str, expiration_str in rows:
            timestamp = datetime.datetime.fromisoformat(timestamp_str)
            # Ensure timezone-aware
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=datetime.timezone.utc)
            expiration = datetime.datetime.fromisoformat(expiration_str)
            # Ensure timezone-aware
            if expiration.tzinfo is None:
                expiration = expiration.replace(tzinfo=datetime.timezone.utc)
            is_expired = expiration <= now
            client_should_update = is_expired or (client_last_updated_at_dt and timestamp > client_last_updated_at_dt)
            
            cache_info[data_type] = {
                "updated_at": timestamp.isoformat(),
                "client_should_update": client_should_update,
                "expiration": expiration.isoformat(),
                "expired": is_expired,
                "ttl_hours": data_cache.EXPIRATION_HOURS.get(data_type, "unknown"),
            }
    except Exception as e:
        cache_info["error"] = str(e)
        cache_info["error_stack_trace"] = traceback.format_exc()
    
    return {
        "now": now.isoformat(),
        "scheduler_running": scheduler.running if scheduler else False,
        "cache_data": cache_info
    }


@app.get("/what-has-changed")
async def what_has_changed(client_last_updated_at: Optional[str] = Query(None, example="20260327-100000"), at: Optional[str] = None):
    """
    Debug endpoint: reports which cached data types have changed since client_last_updated_at,
    and whether those changes are relevant to the display at the given time.
    
    This helps clients determine whether they need to refresh the display based on:
    1. Whether data has actually changed (newer timestamp than client_last_updated_at)
    2. Whether that data type is relevant for display at the current time
    
    Args:
        client_last_updated_at: Optional datetime when client last updated (format: "%Y%m%d-%H%M%S", must be UTC timezone).
                                Used to determine if client needs to refresh.
        at: Optional datetime to check relevance for (format: "%Y%m%d-%H%M%S", must be UTC timezone). Defaults to current UTC time.
    """
    
    _logger.info(f"Received /what-has-changed request with client_last_updated_at={client_last_updated_at} and at={at}")

    now_utc = datetime.datetime.now(datetime.timezone.utc)
    if at:
        now_utc = datetime.datetime.strptime(at, _DATETIME_FORMAT_IN_URL).replace(tzinfo=datetime.timezone.utc)
    
    client_last_updated_at_dt = None
    if client_last_updated_at:
        client_last_updated_at_dt = datetime.datetime.strptime(client_last_updated_at, _DATETIME_FORMAT_IN_URL)
        _logger.debug(f"Parsed client_last_updated_at: {client_last_updated_at_dt} from input: {client_last_updated_at}")
        # Ensure timezone-aware by adding UTC if naive
        if client_last_updated_at_dt.tzinfo is None:
            client_last_updated_at_dt = client_last_updated_at_dt.replace(tzinfo=datetime.timezone.utc)
            _logger.debug(f"Added timezone information, so now client_last_updated_at is {client_last_updated_at_dt}")
    else:
        _logger.warning("client_last_updated_at is not provided, cannot determine if data has changed. Defaulting to None.")
    
    changes_report = {}
    
    try:
        conn = sqlite3.connect(str(data_cache.DB_PATH))
        cursor = conn.cursor()
        
        cursor.execute("SELECT data_type, timestamp FROM data_cache")
        rows = cursor.fetchall()
        conn.close()
        
        for data_type, timestamp_str in rows:
            timestamp = datetime.datetime.fromisoformat(timestamp_str)
            # Ensure timezone-aware
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=datetime.timezone.utc)
            
            # Determine if data has changed since client_last_updated_at
            has_changed = False
            if client_last_updated_at_dt:
                _logger.debug(f"Comparing timestamp for {data_type}: {timestamp} with client_last_updated_at: {client_last_updated_at_dt}")
                has_changed = timestamp > client_last_updated_at_dt
            else:
                _logger.warning("client_last_updated_at is not provided, cannot determine if data has changed. Defaulting to False.")
            
            # Determine if this data type is relevant to the display at the given time
            is_relevant = _is_data_type_relevant_at_time(data_type, now_utc)
            
            changes_report[data_type] = {
                "updated_at": timestamp.isoformat(),
                "has_changed": has_changed,
                "is_relevant_to_display": is_relevant
            }
    except Exception as e:
        changes_report["error"] = str(e)
        changes_report["error_stack_trace"] = traceback.format_exc()
    
    return {
        "now": now_utc.isoformat(),
        "client_last_updated_at": client_last_updated_at,
        "changes": changes_report
    }

#if __name__ == "__main__":
#    now_utc = datetime.datetime.now(datetime.timezone.utc)
#    breakpoint()
#    _is_data_type_relevant_at_time("seating", now_utc)

