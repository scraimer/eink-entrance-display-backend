import os
from PIL import Image, ImageDraw, ImageFont, ImageMath, ImageOps
from urllib.parse import unquote
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict
from eink_image import EinkImage
from image_cache import ImageCache

scriptdir = Path(os.path.dirname(os.path.realpath(__file__)))
outdir = scriptdir / 'out'
picdir = outdir / 'pic'
fontdir = scriptdir / 'fonts'
_cache = ImageCache(cache_dir = picdir)

@dataclass
class WeatherDataPoint:
    feels_like: float = None
    icon_url: str = None
    hour: str = None
    hour_desc: str = None
    detailed_status: str = None

@dataclass
class WeatherForToday:
    current:WeatherDataPoint
    hourlies:Dict[str,WeatherDataPoint] = field(default_factory=dict)


def paste_red_and_black_image(name:str, red_image:Image, black_image:Image, position):
    with Image.open(picdir / f"{name}-red.png") as im:
        red_image.paste(im, position)
    with Image.open(picdir / f"{name}-black.png") as im:
        black_image.paste(im, position)

def create_weather_image(width:int, height:int, data:WeatherForToday) -> EinkImage:
    font_title = ImageFont.truetype(str(fontdir / 'arial.ttf'), 28)
    font_text = ImageFont.truetype(str(fontdir / 'arial.ttf'), 14)

    # create two single color images: black/white and red/white

    red_image = Image.new('1', (width, height), 255)  # 255: clear the frame
    red_draw = ImageDraw.Draw(red_image)
    black_image = Image.new('1', (width, height), 255)  # 255: clear the frame
    black_draw = ImageDraw.Draw(black_image)

    # Draw current

    # Draw hourlies
    DEG = unquote("%C2%B0")
    num = len(data.hourlies)
    margins = 30
    hourly_width = (width - 30) / num
    for i, hourly in enumerate(data.hourlies.values()):
        y = 50
        x = int((margins / 2) +  hourly_width * i)
        # TODO: use ImageCache to get the file (and download it if missing)
        with Image.open(picdir / "04d.png") as im:
            black_image.paste(im, (x,y))
        y += 50
        black_draw.text((x,y), str(hourly.feels_like) + f"{DEG}F", font=font_text, fill=0)
        print(hourly)
        box = font_text.getbbox(hourly.detailed_status)
        box_height = box[3] - box[1]
        y += box_height
        black_draw.text((x,y), hourly.detailed_status, font=font_text, fill=0)
        
    #red_draw.text((432, 700), weather_sunny_icon, font = weather_font, fill=0)

    # y = -15
    # x = 0
    # LINE_SPACING = 3

    # lines = []
    # lines.append({
    #     "font":font_title,
    #     "text":"Some Title",
    #     "center": True,
    #     "bottom-margin": LINE_SPACING * 3
    # })
    # for title,times in [('title1', ['value']), ('title2', ['value2'])]:
    #     times = [t if t[-3]==':' else t for t in times]
    #     lines.append({"font":font_text, "text": f"{', '.join(sorted(times, reverse=True))} :{title}"})

    # boxes = [line["font"].getbbox(line["text"]) for line in lines]
    # max_line_height = max([box[3] - box[1] for box in boxes])

    # for line in lines:
    #     box = line["font"].getbbox(line["text"])
    #     if line.get("center", False):
    #         actual_x = (width - box[2]) / 2 - x
    #     else:
    #         actual_x = width - x - box[2]
    #     red_draw.text((actual_x, y), line["text"], font = line["font"], fill=0)
    #     y = y + max_line_height + LINE_SPACING
    #     if line.get("bottom-margin", False):
    #         y = y + line["bottom-margin"]

    #paste_red_and_black_image(name="sneaker", red_image=red_image, black_image=black_image, position=(30,height - 50))

    return EinkImage(red=red_image, black=black_image)

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
    # TODO: get the values of `data` from internet', perhaps in a function or another class
    data = WeatherForToday(
        current=WeatherDataPoint(feels_like=15.79, icon_url="http://openweathermap.org/img/wn/04n.png")
    )
    data.hourlies['07:00'] = WeatherDataPoint()
    data.hourlies['07:00'] = WeatherDataPoint(
        hour='07:00',
        hour_desc='To school',
        feels_like=16.18,
        icon_url='http://openweathermap.org/img/wn/01d.png',
        detailed_status='clear sky'
    )
    data.hourlies['14:00'] = WeatherDataPoint(
        hour='14:00',
        hour_desc='From school',
        feels_like=16.67,
        icon_url='http://openweathermap.org/img/wn/04d.png',
        detailed_status='broken clouds'
    )
    data.hourlies['16:00'] = WeatherDataPoint(
        hour='16:00',
        hour_desc='Pickup',
        feels_like=16.53,
        icon_url='http://openweathermap.org/img/wn/04n.png',
        detailed_status='overcast clouds'
    )

    # Note: Image size is 528 width, and 880 height
    weather_image = create_weather_image(width=528, height=880, data=data)
    color_image = join_image( source_black=weather_image.black, source_red=weather_image.red )

    color_image.save(str(dest / "joined.png"))
    weather_image.black.save(str(dest / "black.png"))
    weather_image.red.save(str(dest / "red.png"))

    return weather_image


if __name__ == '__main__':
    make_image(Path("."))

