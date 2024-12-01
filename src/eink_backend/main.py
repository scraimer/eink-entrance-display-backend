from dataclasses import dataclass
import datetime
import shutil
from string import Template
import subprocess
from typing import Any, Dict, List, Optional, Set, Tuple
from pathlib import Path
import os
import re
from PIL import Image, ImageDraw, ImageFont
from pyluach import dates, parshios
import traceback

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse

from . import my_calendar, weather, efrat_zmanim, chores, seating

FRIDAY = 4
SATURDAY = 5

root_dir = Path(os.path.abspath(__file__)).parent.parent.parent
"""This should point to the parent of the `src` directory"""
out_dir = Path("/tmp/eink-display")
out_dir.mkdir(parents=True, exist_ok=True)

app = FastAPI()


@app.get("/")
def read_root():
    return {"Help": "Go to '/docs' for an explanation of the API"}


def untaint_filename(filename: str) -> str:
    return re.sub(r"[^a-zA-Z_-]", "_", filename)


VALID_IMAGE_NAMES = ["red", "black", "joined"]


def image_to_mono(src: Image.Image):
    THRESH = 200
    fn = lambda x: 255 if x > THRESH else 0
    return src.convert("L").point(fn, mode="1")


def convert_png_to_mono_png(src: Path, dest: Path) -> Path:
    src_image = Image.open(src)
    mono_image = image_to_mono(src_image)
    mono_image.save(dest)


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


def is_tset_soon(tset_shabat: datetime.datetime, now: datetime.datetime) -> bool:
    if not tset_shabat:
        return False
    TSET_IS_SOON = datetime.timedelta(hours=2)
    diff: datetime.timedelta = tset_shabat - now
    return diff.total_seconds() > 0 and diff <= TSET_IS_SOON


def omer_count(today: datetime.date):
    today_heb = dates.HebrewDate.from_pydate(today)
    OMER_ZERO = dates.HebrewDate(year=today_heb.year, month=1, day=15).to_pydate()
    if today <= OMER_ZERO:
        return None
    delta = today - OMER_ZERO
    MAX_OMER = 49
    if delta.days <= 0 or delta.days > MAX_OMER:
        return None
    if delta.days > 7:
        return f"{delta.days // 7} * 7 + {delta.days % 7} = {delta.days} בעומר "
    else:
        return f"{delta.days} בעומר"


def collect_all_values_of_data(
    zmanim: Optional[efrat_zmanim.ShabbatZmanim],
    weather_forecast: weather.WeatherForecast,
    calendar_content: str,
    chores_content: chores.ChoreData,
    seating_content: seating.SeatingData,
    color: str,
    now: datetime.datetime,
) -> Dict[str, Any]:
    heb_date = dates.HebrewDate.from_pydate(now.date())
    omer = omer_count(today=now.date())
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
        print("Warning: Could not collect zmanim data.")
        # TODO: indent
        traceback.print_exc()
        zmanim_dict = {"Error": str(ex)}

    weather_dict = {"weather_report": ""}
    try:
        weather_report = weather.weather_report(
            weather_forecast=weather_forecast, color=color
        )
        if weather_report:
            weather_dict["weather_report"] = weather_report
    except Exception as ex:
        msg = f"Exception colecting error report: {ex}"
        weather_dict["weather_report"] = msg
        print(msg)

    if zmanim and is_tset_soon(zmanim.times.get("tset_shabat_as_datetime", None), now):
        additional_css = """
            #shul { display: none; }
            #test-big { display: block; }
        """
    else:
        additional_css = """
            #tset-big { display: none; }
        """
    page_dict = {
        "day_of_week": now.date().strftime("%A"),
        "date": now.date().strftime("%-d of %B %Y"),
        "render_timestamp": now.strftime("%Y-%d-%m %H:%M:%S"),
        "heb_date": heb_date.hebrew_date_string(),
        "additional_css": additional_css,
    }
    calendar_dict = {"calendar_content": calendar_content}

    if chores_content.error:
        chores_str = chores_content.error
    else:
        chores_str = chores.render_chores(
            chores=chores_content.chores, now=now, color=color
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


def load_template_from_file(file: Path) -> Tuple[Template, List[str]]:
    template_text = file.read_text(encoding="utf-8")
    p = re.compile("\\$[a-z_]+")
    template_required_keys = set(p.findall(template_text)) - set(["$color"])
    template = Template(template_text)
    return (template, template_required_keys)


def load_template_by_time(now: datetime.datetime) -> Tuple[Template, List[str]]:
    wkday = now.weekday()
    hour = now.hour

    # Default template is shabbat
    template_path = Path("/app/assets/layout-shabbat.html")
    # Friday until 16:00, use the chore template
    if wkday == FRIDAY and hour < 16:
        template_path = Path("/app/assets/layout-choreday.html")
    # Friday and Shabbat, around meal-time, show seating layout
    if (wkday == FRIDAY and hour >= 16) or (
        wkday == SATURDAY and (hour >= 10 and hour <= 13)
    ):
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


def generate_html_content(color: str, now: datetime.datetime) -> str:
    collected = collect_data(now=now)
    try:
        all_values = collect_all_values_of_data(
            zmanim=collected.zmanim,
            weather_forecast=collected.weather_forecast,
            calendar_content=collected.calendar_content,
            chores_content=collected.chores_content,
            seating_content=collected.seating_content,
            color=color,
            now=now,
        )
    # TODO: Can I do this try/except in some more uniform manner (print_exception_on_screen, and set value to {"error": "message of error"} or something)
    except Exception as ex:
        print("Warning: Could not collect all values of data.")
        # TODO: indent the exception under the warning
        traceback.print_exc()
        all_values = {"Error": str(ex)}
    (template, template_required_keys) = load_template_by_time(now=now)
    missing_keys = find_missing_template_keys(
        all_values=all_values, template_required_keys=template_required_keys
    )
    # Fill in missing keys
    for k in missing_keys:
        all_values[k[1:]] = "[ERR]"
    all_values["color"] = color
    return template.substitute(**all_values)


def render_html_template(color: str, now: datetime.datetime):
    html_content = generate_html_content(color=color, now=now)
    render_html_template_single_color(color=color, html_content=html_content)


def get_filename(color: str) -> Path:
    if color not in VALID_IMAGE_NAMES:
        raise HTTPException(
            status_code=404,
            detail=f"Invalid image name. Acceptable names: {VALID_IMAGE_NAMES}",
        )
    return out_dir / (color + ".png")


@dataclass
class PageData:
    zmanim: Optional[efrat_zmanim.ShabbatZmanim]
    weather_forecast: Optional[weather.WeatherForecast]
    calendar_content: str
    chores_content: chores.ChoreData
    seating_content: seating.SeatingData


def collect_data(now: datetime.datetime):
    return PageData(
        zmanim=efrat_zmanim.collect_data(now=now),
        weather_forecast=weather.collect_data(now=now),
        calendar_content=my_calendar.collect_data(),
        chores_content=chores.collect_data(now=now),
        seating_content=seating.collect_data(now=now),
    )


def render_one_color(color: str, now: datetime.datetime):
    color = untaint_filename(color)
    render_html_template(color=color, now=now)
    filename = get_filename(color=color)


@app.get("/html-dev/{color}", response_class=HTMLResponse)
async def html_dev(color: str, at: Optional[str] = None):
    now = datetime.datetime.now()
    if at:
        now = datetime.datetime.strptime(at, "%Y%m%d-%H%M%S")
    return generate_html_content(color=color, now=now)


@app.get("/render/{color}")
async def render_endpoint(color: str):
    now = datetime.datetime.now()
    render_one_color(color=color, now=now)
    return f"Rendered {color}. Waiting for download."


@app.get("/eink/{color}", response_class=FileResponse)
async def eink(color: str, at: Optional[str] = None):
    color = untaint_filename(color)
    now = datetime.datetime.now()
    if at:
        now = datetime.datetime.strptime(at, "%Y%m%d-%H%M%S")
    # always render "joined", since it's for dev work
    if color == "joined" or color == "black":
        render_one_color(color=color, now=now)
    image_path = get_filename(color=color)
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


from . import render


@app.get("/test-make-image", response_class=FileResponse)
async def read_image_from_cache():
    path = render.image_extract_color_channel(
        img_url="http://openweathermap.org/img/wn/03d@2x.png", color="black"
    )
    return path
