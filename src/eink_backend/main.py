import datetime
import json
from typing import Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse

from eink_backend.collect import PageData, collect_data
from eink_backend.render import (
    generate_html_content,
    render_html_template_single_color,
    untaint_filename,
)

out_dir = Path("/tmp/eink-display")
out_dir.mkdir(parents=True, exist_ok=True)

app = FastAPI()


@app.get("/")
def read_root():
    return {"Help": "Go to '/docs' for an explanation of the API"}


VALID_IMAGE_NAMES = ["red", "black", "joined"]


def get_filename(color: str) -> Path:
    if color not in VALID_IMAGE_NAMES:
        raise HTTPException(
            status_code=404,
            detail=f"Invalid image name. Acceptable names: {VALID_IMAGE_NAMES}",
        )
    return out_dir / (color + ".png")


def render_one_color(color: str, collected_data: PageData, now: datetime.datetime):
    color = untaint_filename(color)
    html_content = generate_html_content(
        color=color, collected_data=collected_data, now=now
    )
    render_html_template_single_color(
        color=color, html_content=html_content, out_dir=out_dir
    )
    filename = get_filename(color=color)


@app.get("/html-dev/{color}", response_class=HTMLResponse)
async def html_dev(color: str, at: Optional[str] = None):
    now = datetime.datetime.now()
    if at:
        now = datetime.datetime.strptime(at, "%Y%m%d-%H%M%S")
    return generate_html_content(color=color, now=now)


@app.get("/collect")
async def collect_endpoint(at: Optional[str] = None):
    now = datetime.datetime.now()
    if at:
        now = datetime.datetime.strptime(at, "%Y%m%d-%H%M%S")
    collected_data = collect_data(now=now)  # TODO Make data collection periodic
    return json.dumps(collect_data, indent=4)


@app.get("/render/{color}")
async def render_endpoint(color: str):
    now = datetime.datetime.now()
    collected_data = collect_data(now=now)  # TODO Make data collection periodic
    render_one_color(color=color, collected_data=collected_data, now=now)
    return f"Rendered {color}. Waiting for download."


@app.get("/eink/{color}", response_class=FileResponse)
async def eink(color: str, at: Optional[str] = None):
    color = untaint_filename(color)
    now = datetime.datetime.now()
    if at:
        now = datetime.datetime.strptime(at, "%Y%m%d-%H%M%S")
    # always render "joined", since it's for dev work
    if color == "joined":
        collected_data = collect_data(now=now)  # TODO Make data collection periodic
        render_one_color(color=color, collected_data=collected_data, now=now)
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
