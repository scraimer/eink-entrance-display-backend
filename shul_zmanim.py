from dataclasses import dataclass
import subprocess
from pathlib import Path
from typing import Dict, List
from bs4 import BeautifulSoup
import sys
import requests
import os
from PIL import Image, ImageDraw, ImageFont, ImageMath, ImageOps
from urllib.parse import unquote

from eink_image import EinkImage

scriptdir = Path(os.path.dirname(os.path.realpath(__file__)))

picdir = Path(os.path.dirname(os.path.realpath(__file__))) / 'pic'
fontdir = scriptdir / 'fonts'

def reverse(source:str):
    return source[::-1]

def paste_red_and_black_image(name:str, red_image:Image, black_image:Image, position):
    with Image.open(picdir / f"{name}-red.png") as im:
        red_image.paste(im, position)
    with Image.open(picdir / f"{name}-black.png") as im:
        black_image.paste(im, position)

def join_image(src: EinkImage) -> Image.Image:
    red_rgb = ImageMath.eval("convert(a,'RGB')", a=src.red)
    red_mask, _, _ = red_rgb.split()
    red_inverted = ImageOps.invert(red_rgb)
    red_r,red_g,red_b = red_inverted.split()
    #zero = ImageMath.eval("convert(band ^ band,'L')", band=red_g)

    black_r, black_g, black_b = (ImageMath.eval("convert(img,'RGB')", img=src.black)).split()

    out_r = ImageMath.eval("convert(red | black, 'L')", red=red_r, black=black_r, red_mask=red_mask)
    out_b = ImageMath.eval("convert((black & red_mask), 'L')", red=red_b, black=black_b, red_mask=red_mask)
    out_g = ImageMath.eval("convert((black & red_mask), 'L')", red=red_g, black=black_g, red_mask=red_mask)

    out = Image.merge("RGB", (out_r,out_b,out_g))
    return out

def make_image(dest: Path) -> EinkImage:
    # Note: Image size is 528 width, and 880 height
    shabbat_image = create_erev_shabbat_image(width=528, height=880)
    color_image = join_image(src=shabbat_image)

    ## XXX: Debug, save to file
    # TODO: Move this out of this function (To where?)
    color_image.save(str(dest / "joined.png"))
    shabbat_image.black.save(str(dest / "black.png"))
    shabbat_image.red.save(str(dest / "red.png"))


    return shabbat_image


@dataclass
class Zmanim:
    parasha: str
    times: Dict[str,List[str]]

def collect_data() -> Zmanim:
    return Zmanim("פלוני אלמוני", 
        {
            "הדלקת נרות": ["12:34"],
            "קבלת שבת": ["12:34"],
            "שחרית": ["12:34", "23:45", "34:56"],
            "מוצאי שבת": ["12:34"],
        })
