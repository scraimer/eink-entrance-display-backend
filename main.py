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


def weather_report(weather_forcast: weather.WeatherForToday):
    hours_template = Template(
        """
        <li>
        <ul>
            <li class="hour">$hour_modified</li>
            <li class="temp">$feels_like_rounded&deg;C</li>
            <li class="icon"><img src="$icon_url"/></li>
            <li class="type">$hour_desc</li>
            <li class="status">$detailed_status</li>
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
            feels_like_rounded=round(hour.feels_like),
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
    color: str,
):
    template_filename = "/app/layout-test-src.html"
    template = Template(Path(template_filename).read_text(encoding="utf-8"))
    heb_date = dates.HebrewDate.today()
    zmanim_dict = {
        "parasha": parshios.getparsha_string(heb_date, israel=True, hebrew=True)
    }
    zmanim_dict = {**zmanim_dict, **{k: v for k, v in zmanim.times.items()}}
    weather_dict = {
        "current_temp": round(weather_forecast.current.feels_like),
        "weather_report": weather_report(weather_forcast=weather_forecast),
    }
    page_dict = {
        "day_of_week": date.today().strftime("%A"),
        "date": date.today().strftime("%-d of %B %Y"),
        "render_timestamp": datetime.datetime.now().strftime("%Y-%d-%m %H:%M:%S"),
        "heb_date": heb_date.hebrew_date_string(),
    }
    all_values = {**zmanim_dict, **page_dict, **weather_dict}
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
    color = untaint_filename(color)
    render_html_template(zmanim=zmanim, weather_forecast=weather_forecast, color=color)

    filename = get_filename(color=color)
    # TODO: Verify that the image is 528x880


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
