import colorsys
from dataclasses import dataclass
import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import re
from PIL import Image, ImageDraw, ImageFont
import os
import shutil
from string import Template
import subprocess
import textwrap
import traceback
import urllib

from eink_backend.collect import PageData, collect_all_values_of_data

from . import my_calendar, weather, efrat_zmanim, chores, seating

"""How much to indent HTML code."""
INDENT = "    "

EXTRACTED_CACHE = Path("/image-cache")

root_dir = Path(os.path.abspath(__file__)).parent.parent.parent
"""This should point to the parent of the `src` directory"""


def image_single_color_channel_filename(img_url: str, color: str) -> str:
    url = urllib.parse.urlparse(img_url)
    return f"{color}-{Path(url.path).name}"


def should_download_to_cache(filepath: Path) -> bool:
    if not filepath.exists():
        return True
    SEVEN_DAYS = datetime.timedelta(days=7)
    file_datetime = datetime.datetime.fromtimestamp(filepath.stat().st_mtime)
    file_too_old = (file_datetime - datetime.datetime.now()) >= SEVEN_DAYS
    return file_too_old


def rgb_to_hsv(src):
    (r, g, b) = src
    (r, g, b) = (r / 255, g / 255, b / 255)
    (h, s, v) = colorsys.rgb_to_hsv(r, g, b)
    return (h, s, v)


def extract_red(src: Image.Image) -> Image.Image:
    color_channels = src.split()
    if len(color_channels) == 4:
        red_img, green_img, blue_img, alpha_img = color_channels
    elif len(color_channels) == 3:
        red_img, green_img, blue_img, alpha_img = color_channels
        alpha_img = None
    else:
        print(f"Found {len(color_channels)} color channels in image, expected 3 or 4.")
    red_data = red_img.getdata()
    green_data = green_img.getdata()
    blue_data = blue_img.getdata()
    if alpha_img:
        alpha_data = alpha_img.getdata()
    else:
        alpha_data = None
    grayscale = Image.new("LA", (src.width, src.height), 0)
    assert (alpha_data is None) or (len(red_data) == len(alpha_data))
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
    if alpha_img:
        grayscale.putalpha(alpha_img)
    return grayscale


@dataclass
class _GrayLevel:
    min_sat: float = 0.0
    max_sat: float = 1.0
    min_val: float = 0.0
    max_val: float = 1.0


# Hue: Red is at 0%/100%, so anything below 8% or over 92% is reddish.
# Saturation: Anything below 30% is mostly washed out, so we can treat it as gray.
# Value/Lightness: We can split lightness into steps for different levels of light/dark
#                  gray.
#
# Exceptions:
# 1. Regardless of Saturation, if lightness is under 20%, it's black.
# 2. Only if Saturation is under 15%, then Lightness over 95% is white.
#


def _check_if_dithering_pattern_would_give_black(
    x: int, y: int, gray_level: int
) -> bool:
    # Patterns taken from https://en.wikipedia.org/wiki/Ordered_dithering
    # Where I assume the patterns start from 0,0, and I pretend as if each black
    # pixel is a hole to see through an entire sheet filled with the dither pattern
    # matching the `gray_level`.

    # These are based on 4x4 dithering patterns, so convert the x and y into
    # x and y within the 4x4 dithering box
    x = x % 4
    y = y % 4

    if gray_level == 2:  # 3rd from the left
        # All are black, except for (0,0) and (2,2)
        return (x, y) not in ((0, 0), (2, 2))
    elif gray_level == 4:  # 5th from the left
        # All are black, except for (0,0) (0,2) (2,0) (2,2)
        return not ((x, y) in ((0, 0), (0, 2), (2, 0), (2, 2)))
    elif gray_level == 8:  # 9th from the left (middle)
        # Half are black.
        # black:
        # (0,0) (0,2)
        # (1,1) (1,3)
        # (2,0) (2,2)
        # (3,1) (3,3)
        # In other words, all the coords whose sum is even
        return (x + y) % 2 == 0
    elif gray_level == 14:  # Very light grey, 3rd from the right
        # Only (0,2) and (2,0) are black
        return (x, y) in ((0, 2), (2, 0))
    else:
        raise ValueError(f"Unsupported gray_level {gray_level}")


def apply_alpha(h, s, v, alpha) -> Tuple[float]:
    HSV_WHITE = (0.0, 0.0, 1.0)
    alpha_ratio = float(alpha) / 255.0
    h = h * alpha_ratio + HSV_WHITE[0] * (1 - alpha_ratio)
    s = s * alpha_ratio + HSV_WHITE[1] * (1 - alpha_ratio)
    v = v * alpha_ratio + HSV_WHITE[2] * (1 - alpha_ratio)
    return (h, s, v)


BLACK = 0
WHITE = 255


def gray_to_black_or_white(
    h: float, s: float, v: float, alpha: int, x: int, y: int
) -> int:
    """Return 0 for black, 255 for white"""
    (h, s, v) = apply_alpha(h, s, v, alpha=alpha)

    if v <= 0.20:
        return BLACK

    # Saturation under 30% means no color, treat as gray
    if s < 0.30:
        if v > 0.95:
            return WHITE

        gray_level = -1
        if v > 0.75:
            # Very light grey, 3rd from the right
            gray_level = 4
        elif v > 0.50:
            # Middling grey, 9th from the left (middle)
            gray_level = 8
        elif v > 0.20:
            # dark gray, 5rd from the left
            gray_level = 14
        black = _check_if_dithering_pattern_would_give_black(
            x=x, y=y, gray_level=gray_level
        )
        return BLACK if not black else WHITE
    return WHITE


def extract_black_and_gray(src: Image.Image) -> Image.Image:
    red_img = src.getchannel("R")
    green_img = src.getchannel("G")
    blue_img = src.getchannel("B")
    red_data = red_img.getdata()
    green_data = green_img.getdata()
    blue_data = blue_img.getdata()
    grayscale = Image.new("L", (src.width, src.height), 0)

    from collections import Counter

    alpha_data = None
    if src.has_transparency_data:
        print("Image has transparency channel")
        alpha_data = src.getchannel("A").getdata()

    grayscale_data: List[int] = []
    for i in range(0, len(red_data)):
        x = i % src.width
        y = int(i / src.width)
        alpha = alpha_data[i] if alpha_data else 100
        (h, s, v) = rgb_to_hsv((red_data[i], green_data[i], blue_data[i]))
        bw_value = gray_to_black_or_white(h=h, s=s, v=v, x=x, y=y, alpha=alpha)
        grayscale_data.append(bw_value)
    grayscale.putdata(grayscale_data)
    # alpha_data: List[int] = [0 for i in range(len(grayscale_data))]
    # grayscale.putalpha(alpha_data)
    return grayscale


def image_extract_color_channel(img_url: str, color: str) -> str:
    EXTRACTED_CACHE.mkdir(exist_ok=True, parents=True)
    filename = image_single_color_channel_filename(img_url=img_url, color=color)
    filepath = EXTRACTED_CACHE / filename
    print(f"{filepath=}")

    if color == "joined":
        if not img_url.startswith("file://"):
            return img_url
        srcpath = Path(img_url.replace("file://", ""))
        x = srcpath.read_bytes()
        filepath.write_bytes(x)
        return str(filepath)

    if True or should_download_to_cache(filepath):
        try:
            url = urllib.parse.urlparse(img_url)
            src_filename = f"/tmp/src.{Path(url.path).suffix}"
            print(f"Downloading {img_url}")
            urllib.request.urlretrieve(img_url, src_filename)
            src_image = Image.open(src_filename)
            # There's a lot of empty white space in the images, crop just the middle 80x80
            crop_area = (10, 10, 90, 90)
            cropped_image = src_image.crop(crop_area)
            if color == "red":
                red_image = extract_red(src=cropped_image)
                red_image.save(str(filepath))
            elif color == "black":
                black_image = extract_black_and_gray(src=cropped_image)
                print(f"Writing black file {str(filepath)}...")
                black_image.save(str(filepath))
        except Exception as ex:
            print(f"Warning: Could not extract color channel from {img_url}")
            print(textwrap.indent(traceback.format_exc(), prefix=INDENT))
            return f"-EXCEPTION: {ex}-"
    else:
        print(f"Using {str(filepath)} from cache")

    return str(filepath)


def untaint_filename(filename: str) -> str:
    return re.sub(r"[^a-zA-Z_-]", "_", filename)


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


def render_html_template_single_color(
    color: str, html_content: str, out_dir: Path
) -> Path:
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


def load_template_from_file(file: Path) -> Tuple[Template, List[str]]:
    template_text = file.read_text(encoding="utf-8")
    p = re.compile("\\$[a-z_]+")
    template_required_keys = set(p.findall(template_text)) - set(["$color"])
    template = Template(template_text)
    return (template, template_required_keys)


def load_template_by_time(now: datetime.datetime) -> Tuple[Template, List[str]]:
    FRIDAY = 4
    SATURDAY = 5

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


def generate_html_content(
    color: str, collected_data: PageData, now: datetime.datetime
) -> str:
    try:
        all_values = collect_all_values_of_data(
            zmanim=collected_data.zmanim,
            weather_forecast=collected_data.weather_forecast,
            calendar_content=collected_data.calendar_content,
            chores_content=collected_data.chores_content,
            seating_content=collected_data.seating_content,
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


if __name__ == "__main__":
    src_filename = "02n@2x_cloudy_sun.png"
    src_image = Image.open(src_filename)
    # outline_image = outline_grays(src=src_image)
    # outline_image.save("outlined_image.png")
    black_image = extract_black_and_gray(src=src_image)
    for i in range(100):
        if not Path(f"{i}.png").exists():
            break
    black_image.save(f"{i}.png")
