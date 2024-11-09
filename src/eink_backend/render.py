import colorsys
import datetime
from pathlib import Path
from PIL import Image
import textwrap
import traceback
import urllib

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


def extract_black_and_gray(src: Image.Image) -> Image.Image:
    channels = src.split()
    # .split() may return either 3 or 4 channels (depending on whether the
    # image has an alpha channel). So take just the first 3
    red_img, green_img, blue_img = channels[0], channels[1], channels[1]
    red_data = red_img.getdata()
    green_data = green_img.getdata()
    blue_data = blue_img.getdata()
    grayscale = Image.new("LA", (src.width, src.height), 0)
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
    grayscale.putdata(grayscale_data)
    return grayscale


def image_extract_color_channel(img_url: str, color: str) -> str:
    EXTRACTED_CACHE.mkdir(exist_ok=True, parents=True)
    filename = image_single_color_channel_filename(img_url=img_url, color=color)
    filepath = EXTRACTED_CACHE / filename

    if color == "joined":
        if not img_url.startswith("file://"):
            return img_url
        srcpath = Path(img_url.replace("file://", ""))
        x = srcpath.read_bytes()
        filepath.write_bytes(x)
        return str(filepath)

    if should_download_to_cache(filepath):
        try:
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
        except Exception as ex:
            print(f"Warning: Could not extract color channel from {img_url}")
            print(textwrap.indent(traceback.format_exc(), prefix=INDENT))
            return f"-EXCEPTION: {ex}-"
    else:
        print(f"Using {str(filepath)} from cache")

    return str(filepath)


if __name__ == "__main__":
    src_filename = "assets/avatars/joined/other.png"
    src_image = Image.open(src_filename)
    breakpoint()
    black_image = extract_black_and_gray(src=src_image)
