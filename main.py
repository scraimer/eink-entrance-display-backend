import datetime
import shutil
from string import Template
import subprocess
from sys import stderr
from typing import Dict, Optional
from pathlib import Path
import os
import re
import weather
import shul_zmanim
from PIL import Image
from datetime import date
from pyluach import dates, hebrewcal, parshios

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

root_dir = Path(os.path.dirname(os.path.abspath(__file__)))
out_dir = Path("/tmp/eink-display")
out_dir.mkdir(parents=True, exist_ok=True)

app = FastAPI()

@app.get("/")
def read_root():
    return {"Help": "Go to '/docs' for an explanation of the API"}

def untaint_filename(filename:str) -> str:
    return re.sub(r'[^a-zA-Z_-]', "_", filename)

VALID_IMAGE_NAMES = ['red', 'black', 'joined']

# https://openweathermap.org/img/wn/02d.png
@app.get("/test/{name}", response_class=FileResponse)
async def read_item(name: str):
    name = untaint_filename(name)
    src_path = out_dir / name
    if not src_path.exists():
        raise HTTPException(status_code=404, detail="The requested image could not be found")
    red, black = flatten(image_path)
    joined = join_images(red=red, black=black)
    joined_path = out_dir / (name + "-joined.png")
    joined_path.write(joined)
    return str(joined_path)


def image_to_mono(src:Image.Image):
    THRESH = 200
    fn = lambda x : 255 if x > THRESH else 0
    return src.convert('L').point(fn, mode='1')

def convert_png_to_mono_png(src:Path, dest:Path) -> Path:
    src_image = Image.open(src)
    mono_image = image_to_mono(src_image)
    mono_image.save(dest)

def render_html_template_single_color(template_values: Dict, color: str, template: Template) -> Path:
    template_values["color"] = color
    content = template.substitute(**template_values)
    content_filename = "/tmp/content.html"
    Path(content_filename).write_text(data=content, encoding="utf-8")
    out_firefox_filename = f"/app/firefox-{color}.png"
    p = subprocess.run(
        ["firefox", "--screenshot", out_firefox_filename, "--window-size=528", f"file://{content_filename}"], timeout=60)
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

def render_html_template(zmanim: shul_zmanim.Zmanim):
    template_filename = "/app/layout-test-src.html"
    template = Template(Path(template_filename).read_text(encoding="utf-8"))
    heb_date = dates.HebrewDate.today()
    zmanim_dict = {
        "parasha": parshios.getparsha_string(heb_date, israel=True, hebrew=True)
    }
    page_dict = {
        "date": date.today().strftime("%A, %-d of %B %Y"),
        "render_timestamp": datetime.datetime.now().strftime("%Y-%d-%m %H:%M:%S"),
        "heb_date": heb_date.hebrew_date_string()
    }
    all_values = {**zmanim_dict, **page_dict}
    render_html_template_single_color(template_values=all_values, template=template, color="red")
    render_html_template_single_color(template_values=all_values, template=template, color="black")
    render_html_template_single_color(template_values=all_values, template=template, color="joined")

@app.get("/eink/{color}", response_class=FileResponse)
async def read_item(color: str):
    static_file = Path("/app/static/static.png")
    if static_file.exists():
        return str(static_file)

    zmanim = shul_zmanim.collect_data()
    render_html_template(zmanim)

    color = untaint_filename(color)
    if color not in VALID_IMAGE_NAMES:
        raise HTTPException(status_code=404, detail=f"Invalid image name. Acceptable names: {VALID_IMAGE_NAMES}")
    image_path = out_dir / (color + ".png")
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="The requested image could not be found")
    return str(image_path)

@app.get("/eink/render/weather")
async def render_weather():
    try:
        result = weather.make_image(dest=out_dir)
        if not result:
            raise HTTPException(status_code=500, detail="Error rendering weather images")
        return {"result": "success"}
    except Exception as ex:
        raise
        #formatted_ex = "".join(traceback.format_exception(type(ex), ex, ex.__traceback__))
        #raise HTTPException(status_code=500, detail=f"Error rendering weather images\n\n{formatted_ex}") from ex

@app.get("/eink/render/zmanim")
async def render_zmanim():
    try:
        result = shul_zmanim.make_image(dest=out_dir)
        if not result:
            raise HTTPException(status_code=500, detail="Error rendering zmanim images")
        return {"result": "success"}
    except Exception as ex:
        raise
        #formatted_ex = "".join(traceback.format_exception(type(ex), ex, ex.__traceback__))
        #raise HTTPException(status_code=500, detail=f"Error rendering weather images\n\n{formatted_ex}") from ex

