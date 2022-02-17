import os
import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageColor, ImageMath, ImageOps
from urllib.parse import unquote, quote
from types import SimpleNamespace
from pathlib import Path

scriptdir = Path(os.path.dirname(os.path.realpath(__file__)))
outdir = scriptdir / 'out'
picdir = outdir / 'pic'
fontdir = scriptdir / 'fonts'

def paste_red_and_black_image(name:str, red_image:Image, black_image:Image, position):
    with Image.open(picdir / f"{name}-red.png") as im:
        red_image.paste(im, position)
    with Image.open(picdir / f"{name}-black.png") as im:
        black_image.paste(im, position)

def create_weather_image(width:int, height:int):
    font_title = ImageFont.truetype(str(fontdir / 'arial.ttf'), 54)
    font_text = ImageFont.truetype(str(fontdir / 'arial.ttf'), 40)
    weather_font = ImageFont.truetype(str(fontdir / 'Pe-icon-7-weather.ttf'),128)

    # create a single color image with black and red and white

    red_image = Image.new('1', (width, height), 255)  # 255: clear the frame
    red_draw = ImageDraw.Draw(red_image)
    black_image = Image.new('1', (width, height), 255)  # 255: clear the frame
    black_draw = ImageDraw.Draw(black_image)

    #with Image.open(picdir / "black-white-landscape-5.jpg") as im:
    #    black_image.paste(im, (0,int(height/2)))

    weather_sunny_icon = unquote("%EE%98%8C%0A")
    red_draw.text((432, 700), weather_sunny_icon, font = weather_font, fill=0)

    y = -15
    x = 0
    LINE_SPACING = 3

    lines = []
    lines.append({
        "font":font_title,
        "text":"Some Title",
        "center": True,
        "bottom-margin": LINE_SPACING * 3
    })
    for title,times in [('title1', ['value']), ('title2', ['value2'])]:
        times = [t if t[-3]==':' else t for t in times]
        lines.append({"font":font_text, "text": f"{', '.join(sorted(times, reverse=True))} :{title}"})

    boxes = [line["font"].getbbox(line["text"]) for line in lines]
    max_line_height = max([box[3] - box[1] for box in boxes])

    for line in lines:
        box = line["font"].getbbox(line["text"])
        if line.get("center", False):
            actual_x = (width - box[2]) / 2 - x
        else:
            actual_x = width - x - box[2]
        red_draw.text((actual_x, y), line["text"], font = line["font"], fill=0)
        y = y + max_line_height + LINE_SPACING
        if line.get("bottom-margin", False):
            y = y + line["bottom-margin"]

    #paste_red_and_black_image(name="sneaker", red_image=red_image, black_image=black_image, position=(30,height - 50))

    return SimpleNamespace(red=red_image, black=black_image)

def join_image(source_red:Image, source_black:Image):
    red_rgb = ImageMath.eval("convert(a,'RGB')", a=source_red)
    red_mask, _, _ = red_rgb.split()
    red_inverted = ImageOps.invert(red_rgb)
    red_r,red_g,red_b = red_inverted.split()
    #zero = ImageMath.eval("convert(band ^ band,'L')", band=red_g)

    black_r, black_g, black_b = (ImageMath.eval("convert(img,'RGB')", img=source_black)).split()

    out_r = ImageMath.eval("convert(red | black, 'L')", red=red_r, black=black_r, red_mask=red_mask)
    out_b = ImageMath.eval("convert((black & red_mask), 'L')", red=red_b, black=black_b, red_mask=red_mask)
    out_g = ImageMath.eval("convert((black & red_mask), 'L')", red=red_g, black=black_g, red_mask=red_mask)

    out = Image.merge("RGB", (out_r,out_b,out_g))
    return out

def make_image(dest:Path):
    # Note: Image size is 528 width, and 880 height
    weather_image = create_weather_image(width=528, height=880)
    color_image = join_image( source_black=weather_image.black, source_red=weather_image.red )

    color_image.save(str(dest / "joined.png"))
    weather_image.black.save(str(dest / "black.png"))
    weather_image.red.save(str(dest / "red.png"))

    return weather_image


if __name__ == '__main__':
    make_image(Path("."))

