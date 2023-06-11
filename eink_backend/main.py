import datetime
import shutil
from string import Template
import subprocess
from typing import Any, Dict, Optional, Set
from pathlib import Path
import os
import re
from PIL import Image, ImageDraw, ImageFont
from datetime import date
from pyluach import dates, parshios
import urllib

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse

from . import my_calendar, weather, efrat_zmanim

root_dir = Path(os.path.dirname((os.path.dirname(os.path.abspath(__file__)))))
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


def clip_image_to_device_dimensions_in_place(file_to_modify:Path, color:str) -> None:
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
        text_width, text_height = draw.textsize(text, font=font)
        text_x = DEVICE_WIDTH - text_width
        text_y = DEVICE_HEIGHT - text_height

        text_fill = (0,0,0)
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


def image_single_color_channel_filename(img_url: str, color: str) -> str:
    url = urllib.parse.urlparse(img_url)
    return f"{color}-{Path(url.path).name}"


EXTRACTED_CACHE = Path("/image-cache")


import colorsys


def rgb_to_hsv(src):
    (r, g, b) = src
    (r, g, b) = (r / 255, g / 255, b / 255)
    (h, s, v) = colorsys.rgb_to_hsv(r, g, b)
    return (h, s, v)


def extract_red(src: Image.Image) -> Image.Image:
    red_img, green_img, blue_img, alpha_img = src.split()
    red_data = red_img.getdata()
    green_data = green_img.getdata()
    blue_data = blue_img.getdata()
    alpha_data = alpha_img.getdata()
    grayscale = Image.new("LA", (src.width, src.height), 0)
    assert len(red_data) == len(alpha_data)
    THRESH = 180
    fn = lambda x: 255 if x < THRESH else 0
    grayscale_data = []
    for i in range(0, len(red_data)):
        (h, s, v) = rgb_to_hsv((red_data[i], green_data[i], blue_data[i]))
        if (h <= 0.1 or h >= 0.9) and (v >= 0.8) and (s >= 0.3):
            grayscale_data.append(0)
        else:
            grayscale_data.append(255)
    # grayscale_data = [fn(x) for x in red_data]
    grayscale.putdata(grayscale_data)
    grayscale.putalpha(alpha_img)
    return grayscale


def extract_black_and_gray(src: Image.Image) -> Image.Image:
    red_img, green_img, blue_img, alpha_img = src.split()
    red_data = red_img.getdata()
    green_data = green_img.getdata()
    blue_data = blue_img.getdata()
    alpha_data = alpha_img.getdata()
    grayscale = Image.new("LA", (src.width, src.height), 0)
    assert len(red_data) == len(alpha_data)
    THRESH = 180
    fn = lambda x: 255 if x < THRESH else 0
    grayscale_data = []
    dither_counter = 0
    for i in range(0, len(red_data)):
        (h, s, v) = rgb_to_hsv((red_data[i], green_data[i], blue_data[i]))
        if s <= 0.3:
            if v < 0.3:
                grayscale_data.append(0)
            elif v > 0.99:
                grayscale_data.append(255)
            else:
                dither_counter += 1
                if dither_counter % 3 == 0:
                    grayscale_data.append(0)
                else:
                    grayscale_data.append(255)
        else:
            grayscale_data.append(255)
    # grayscale_data = [fn(x) for x in red_data]
    grayscale.putdata(grayscale_data)
    grayscale.putalpha(alpha_img)
    return grayscale


def image_extract_color_channel(img_url: str, color: str) -> str:
    if color == "joined":
        return img_url

    filename = image_single_color_channel_filename(img_url=img_url, color=color)
    EXTRACTED_CACHE.mkdir(exist_ok=True, parents=True)
    filepath = EXTRACTED_CACHE / filename
    if not filepath.exists():  # TODO: Make sure the file is no more than 7d old
        url = urllib.parse.urlparse(img_url)
        src_filename = f"/tmp/src.{Path(url.path).suffix}"
        print(f"Downloading {img_url}")
        urllib.request.urlretrieve(img_url, src_filename)
        src_image = Image.open(src_filename)
        if color == "red":
            red_image = extract_red(src=src_image)
            red_image.save(str(filepath))
        elif color == "black":
            black_image = extract_black_and_gray(src=src_image)
            black_image.save(str(filepath))
    else:
        print(f"Using {str(filepath)} from cache")

    return str(filepath)


def weather_report(weather_forcast: weather.WeatherForToday, color: str):
    hours_template = Template(
        """
        <li>
        <ul>
            <li class="black hour">$hour_modified</li>
            <li class="black temp">$feels_like_rounded&deg;C</li>
            <li class="$color icon"><img src="$icon_url_modified"/></li>
            <li class="black type">$hour_desc</li>
            <li class="black status">$detailed_status</li>
        </ul>
        </li>"""
    )

    hours_str = ""
    hours_to_display = list(weather_forcast.hourlies.values())[0:4]
    for hour in hours_to_display:
        hour_modified = hour.hour[0:5] + (
            f'<span class="tomorrow">{hour.relative_day}</span>' if hour.relative_day else ""
        )
        hours_str += hours_template.substitute(
            **hour.__dict__,
            hour_modified=hour_modified,
            icon_url_modified=image_extract_color_channel(
                img_url=hour.icon_url, color=color
            ),
            feels_like_rounded=round(hour.feels_like),
            color=color,
        )

    return f"""
    <div id="weather-table">
        <ul>
            {hours_str}
        </ul>
        <span class="min_max_notes">{weather_forcast.min_max_soon}</span>
    </div>
    """


def is_tset_soon(tset_shabat: datetime.datetime) -> bool:
    if not tset_shabat:
        return False
    TSET_IS_SOON = datetime.timedelta(hours=2)
    diff: datetime.timedelta = tset_shabat - datetime.datetime.now()
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
    weather_forecast: weather.WeatherForToday,
    calendar_content: str,
    color: str,
) -> Dict[str, Any]:
    heb_date = dates.HebrewDate.today()
    omer = omer_count(today=datetime.datetime.today().date())
    zmanim_dict = {
        "parasha": parshios.getparsha_string(heb_date, israel=True, hebrew=True),
        **{k: v for k, v in zmanim.times.items()},
    }
    weather_dict = {
        "current_temp": round(weather_forecast.current.feels_like),
        "weather_warning_icon": "",
        "weather_report": weather_report(weather_forcast=weather_forecast, color=color),
    }
    JACKET_WEATHER_TEMPERATURE = 13
    if weather_forecast.current.feels_like <= JACKET_WEATHER_TEMPERATURE:
        x = f"""
            <span id="current-weather-warning-icon">
                <img src="/app/assets/pic/jacket-black.png" class="black" />
            </span>"""
        weather_dict["weather_warning_icon"] = x
    if is_tset_soon(zmanim.times.get("tset_shabat_as_datetime", None)):
        additional_css = """
            #shul { display: none; }
            #test-big { display: block; }
        """
    else:
        additional_css = """
            #tset-big { display: none; }
        """
    page_dict = {
        "day_of_week": date.today().strftime("%A"),
        "date": date.today().strftime("%-d of %B %Y"),
        "render_timestamp": datetime.datetime.now().strftime("%Y-%d-%m %H:%M:%S"),
        "heb_date": heb_date.hebrew_date_string(),
        "additional_css": additional_css,
    }
    calendar_dict = {"calendar_content": calendar_content}
    omer_dict = {
        "omer": f"{omer}",
        "omer_display": "inline" if omer else "none",
    }
    all_values = {
        **zmanim_dict,
        **page_dict,
        **weather_dict,
        **calendar_dict,
        **omer_dict,
    }
    return all_values


def load_template_for_shabbat():
    TEMPLATE_FILENAME = "/app/assets/layout-shabbat.html"
    template_text = Path(TEMPLATE_FILENAME).read_text(encoding="utf-8")
    p = re.compile("\\$[a-z_]+")
    template_required_keys = set(p.findall(template_text)) - set(["$color"])
    template = Template(template_text)
    return (template, template_required_keys)


def find_missing_template_keys(all_values:Dict[str, Any], template_required_keys: Set[Any]):
    dollar_keys = set([f"${x}" for x in all_values.keys()])
    missing_keys = template_required_keys - dollar_keys
    if missing_keys:
        print(
            "Warning: the follow template variable missing.\n"
            "They will be replaced by a placeholder:\n" + str(missing_keys)
        )
        # raise KeyError("Required keys are missing:", missing_keys)
        # Fill in the missing keys, to avoid failing
    return missing_keys


def generate_html_content(color: str) -> str:
    (zmanim, weather_forecast, calendar_content) = collect_data()
    all_values = collect_all_values_of_data(zmanim=zmanim, weather_forecast=weather_forecast, calendar_content=calendar_content, color=color)
    (template, template_required_keys) = load_template_for_shabbat()
    missing_keys = find_missing_template_keys(all_values=all_values, template_required_keys=template_required_keys)
    # Fill in missing keys
    for k in missing_keys:
        all_values[k[1:]] = "[ERR]"
    all_values["color"] = color
    return template.substitute(**all_values)


def render_html_template(
    color: str,
):
    html_content = generate_html_content(color=color)
    render_html_template_single_color(color=color, html_content=html_content)


def get_filename(color: str) -> Path:
    if color not in VALID_IMAGE_NAMES:
        raise HTTPException(
            status_code=404,
            detail=f"Invalid image name. Acceptable names: {VALID_IMAGE_NAMES}",
        )
    return out_dir / (color + ".png")


def collect_data():
    zmanim = efrat_zmanim.collect_data()
    weather_forecast = weather.collect_data()
    calendar_content = my_calendar.collect_data()
    return (zmanim, weather_forecast, calendar_content)

def render(color: str):
    color = untaint_filename(color)
    render_html_template(color=color)
    filename = get_filename(color=color)


@app.get("/html-dev/{color}", response_class=HTMLResponse)
async def read_item(color: str):
    return generate_html_content(color=color)


@app.get("/render/{color}")
async def read_item(color: str):
    render(color=color)
    return f"Rendered {color}. Waiting for download."


@app.get("/eink/{color}", response_class=FileResponse)
async def read_item(color: str):
    color = untaint_filename(color)
    # always render "joined", since it's for dev work
    if color == "joined":
        render(color=color)
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
