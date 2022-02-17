from typing import Optional
from pathlib import Path
import os
import re
import weather

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

@app.get("/eink/{color}", response_class=FileResponse)
async def read_item(color: str):
    color = untaint_filename(color)
    if color not in VALID_IMAGE_NAMES:
        raise HTTPException(status_code=404, detail=f"Invalid image name. Acceptable names: {VALID_IMAGE_NAMES}")
    image_path = out_dir / (color + ".png")
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="The requested image could not be found")
    return str(image_path)

@app.get("/eink/render/weather")
async def render_weather():
    result = weather.make_image(dest=out_dir)
    if not result:
        raise HTTPException(status_code=500, detail="Error rendering weather images")
    return {"result": "success"}

