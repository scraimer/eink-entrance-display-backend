import my_calendar
import datetime
import shutil
from string import Template
import subprocess
from typing import Dict, Optional
from pathlib import Path
import os
import re
import weather
import shul_zmanim
from PIL import Image
from datetime import date
from pyluach import dates, parshios
import urllib

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

root_dir = Path(os.path.dirname(os.path.abspath(__file__)))
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


def render_html_template_single_color(
    template_values: Dict, color: str, template: Template
) -> Path:
    template_values["color"] = color
    content = template.substitute(**template_values)
    content_filename = "/tmp/content.html"
    Path(content_filename).write_text(data=content, encoding="utf-8")
    out_firefox_filename = f"/app/firefox-{color}.png"
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
            '<span class="tomorrow">tomorrow</span>' if len(hour.hour) > 5 else ""
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
    </div>
    """


def render_html_template(
    zmanim: Optional[shul_zmanim.ShabbatZmanim],
    weather_forecast: weather.WeatherForToday,
    calendar_content: str,
    color: str,
):
    heb_date = dates.HebrewDate.today()
    zmanim_dict = {
        "parasha": parshios.getparsha_string(heb_date, israel=True, hebrew=True)
    }
    zmanim_dict = {**zmanim_dict, **{k: v for k, v in zmanim.times.items()}}
    weather_dict = {
        "current_temp": round(weather_forecast.current.feels_like),
        "weather_warning_icon": "",
        "weather_report": weather_report(weather_forcast=weather_forecast, color=color),
    }
    if weather_forecast.current.feels_like <= 13:
        x = f"""
            <span id="current-weather-warning-icon">
                <img src="/app/pic/jacket-black.png" class="black" />
            </span>"""
        weather_dict["weather_warning_icon"] = x
    page_dict = {
        "day_of_week": date.today().strftime("%A"),
        "date": date.today().strftime("%-d of %B %Y"),
        "render_timestamp": datetime.datetime.now().strftime("%Y-%d-%m %H:%M:%S"),
        "heb_date": heb_date.hebrew_date_string(),
    }
    calendar_dict = {"calendar_content": calendar_content}
    all_values = {**zmanim_dict, **page_dict, **weather_dict, **calendar_dict}

    TEMPLATE_FILENAME = "/app/layout-shabbat.html"
    template_text = Path(TEMPLATE_FILENAME).read_text(encoding="utf-8")
    p = re.compile("\\$[a-z_]+")
    template_required_keys = set(p.findall(template_text)) - set(["$color"])
    template = Template(template_text)

    dollar_keys = set([f"${x}" for x in all_values.keys()])
    missing_keys = template_required_keys - dollar_keys
    if missing_keys:
        print(
            "Warning: the follow template variable missing.\n"
            "They will be replaced by a placeholder:\n" + str(missing_keys)
        )
        # raise KeyError("Required keys are missing:", missing_keys)
        # Fill in the missing keys, to avoid failing
        for k in missing_keys:
            all_values[k[1:]] = "[ERR]"

    render_html_template_single_color(
        template_values=all_values, template=template, color=color
    )


def get_filename(color: str) -> Path:
    if color not in VALID_IMAGE_NAMES:
        raise HTTPException(
            status_code=404,
            detail=f"Invalid image name. Acceptable names: {VALID_IMAGE_NAMES}",
        )
    return out_dir / (color + ".png")


def render(color: str):
    zmanim = shul_zmanim.collect_data()
    weather_forecast = weather.collect_data()
    calendar_content = my_calendar.collect_data()
    color = untaint_filename(color)
    render_html_template(
        zmanim=zmanim,
        weather_forecast=weather_forecast,
        calendar_content=calendar_content,
        color=color,
    )

    filename = get_filename(color=color)
    # TODO: Verify that the image is 528x880.
    #       If not, make it that size, and send an alert to Shalom


@app.get("/render/{color}")
async def read_item(color: str):
    render(color=color)
    return f"Rendered {color}. Waiting for download."


@app.get("/eink/{color}", response_class=FileResponse)
async def read_item(color: str):
    static_file = Path("/app/static/static.png")
    if static_file.exists():
        return str(static_file)

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
