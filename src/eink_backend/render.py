import colorsys
from dataclasses import dataclass
import datetime
from pathlib import Path
from typing import List, Tuple
from PIL import Image
import textwrap
import traceback
import urllib

from pprint import pprint

"""How much to indent HTML code."""
INDENT = "    "

EXTRACTED_CACHE = Path("/image-cache")


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
        red_img, green_img, blue_img = color_channels
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
