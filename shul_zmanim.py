from pathlib import Path
from bs4 import BeautifulSoup
import sys
import requests
import os

from eink_image import EinkImage

scriptdir = Path(os.path.dirname(os.path.realpath(__file__)))

def extract_shabbat_times(html:str):
    soup = BeautifulSoup(html, 'html.parser')

    # Since I've no idea on how the tags are laid out, I'm going to focus on
    # two constants:
    # * "8:30"
    # * The words "צאת השבת"
    eight_thirty = soup.find(lambda tag:tag.name=="span" and "8:30" in tag.text)
    eight_thirty_div = eight_thirty.find_parent("div")
    #first_column_div = eight_thirty_div.prev_sibling
    first_column_div = eight_thirty_div
    print (first_column_div)
    END_OF_SHABBAT_TEXT = "צאת השבת וערבית"
    shabbat_end = soup.find(lambda tag:tag.name=="span" and END_OF_SHABBAT_TEXT in tag.text)
    end_column_div = shabbat_end.find_parent("div")

    parent = first_column_div.parent
    assert parent == end_column_div.parent

    # Find all the children between the first and last columns
    cols = []
    started = False
    for col in parent.children:
        if (not started) and (col == first_column_div):
            started = True
        if started:
            cols.append(col)
        if col == end_column_div:
            break

    # Turn the columns into lists of texts
    text_cols = []
    for col in cols:
        texts = col.findAll(text=True)
        for t in texts:
            t = t.strip()
            #print(f"'>{t}<'")
        text_cols.append([t.strip().replace('\u200b','') for t in col.findAll(text=True)])

    # Pivot the columns into rows
    rows_count = max([len(col) for col in cols])
    rows = []
    for i in range(0,rows_count):
        row = [col[i] if i < len(col) else '' for col in text_cols]
        # Skip rows of empty data
        if all([not x for x in row]):
            continue
        rows.append(row)

    # Look for the word "פרשת "
    PARASHAT_TEXT = "פרשת "
    parasha_elem = soup.find(lambda tag:tag.name=="span" and PARASHAT_TEXT in tag.text)
    title_div = parasha_elem.find_parent("div")
    title_lines = title_div.findAll(text=True)
    title_lines = [x for x in title_lines if x.strip()]
    parasha_name = ' '.join(title_lines)
    print(f"Parasha Name: {parasha_name}")

    ### This is the part that hasn't been modified

    TIME_AFTER_SHUL = 'אחרי התפילה'
    rows_keyed = {}
    for row in rows:
        if len(row) == 1 and len(row[0]) == 0:
            continue

        times = []
        names = []
        for v in row:
            v = v.strip()
            if len(v) == 0:
                continue
            elif (v[-3] == ':') or (v == TIME_AFTER_SHUL):
                times.append(v)
            elif len(v) > 0:
                names.append(v)

        if len(names) != 1:
            if len(names) == 2:
                names = [names[0]]
            else:
                print(f"Warning: Expected 1 name but found {len(names)} names (names={names}) in the row: {row} (len={len(row)})")
                continue

        key = names[0]
        if key in rows_keyed:
            print(f"Warning: Duplicate key: {key} from row {row}")

        if len(times) == 0:
            continue

        rows_keyed[key] = times

    return {'parasha_name': parasha_name, 'times': rows_keyed}

def scrape_shabbat_items():
    ZMANIM_URL = 'https://reshitd.wixsite.com/home/zmanim'
    r = requests.get(ZMANIM_URL)
    if r.status_code != 200:
        print(f"HTTP Error {r.status_code} fetching {ZMANIM_URL}")
        sys.exit(1)
    html = r.text
    return extract_shabbat_times(html)

# =======


import sys
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageColor, ImageMath, ImageOps
from urllib.parse import unquote, quote
from types import SimpleNamespace
from pathlib import Path

titles_to_remove = [
    unquote('%D7%94%D7%A6%D7%92%D7%AA%20%D7%99%D7%9C%D7%93%D7%99%D7%9D'),
    unquote('%D7%A9%D7%99%D7%A2%D7%95%D7%A8%20%D7%9C%D7%9E%D7%91%D7%95%D7%92%D7%A8%D7%99%D7%9D'),
]

picdir = Path(os.path.dirname(os.path.realpath(__file__))) / 'pic'
fontdir = scriptdir / 'fonts'

def reverse(source:str):
    return source[::-1]

def paste_red_and_black_image(name:str, red_image:Image, black_image:Image, position):
    with Image.open(picdir / f"{name}-red.png") as im:
        red_image.paste(im, position)
    with Image.open(picdir / f"{name}-black.png") as im:
        black_image.paste(im, position)

def create_erev_shabbat_image(width:int, height:int) -> EinkImage:
    font_title = ImageFont.truetype(str(fontdir / 'arial.ttf'), 54)
    font_text = ImageFont.truetype(str(fontdir / 'arial.ttf'), 40)
    weather_font = ImageFont.truetype(str(fontdir / 'Pe-icon-7-weather.ttf'),128)

    # create a single color image with black and red and white

    red_image = Image.new('1', (width, height), 255)  # 255: clear the frame
    red_draw = ImageDraw.Draw(red_image)
    black_image = Image.new('1', (width, height), 255)  # 255: clear the frame
    black_draw = ImageDraw.Draw(black_image)

    with Image.open(picdir / "black-white-landscape-5.jpg") as im:
        black_image.paste(im, (0,int(height/2)))

    weather_sunny_icon = unquote("%EE%98%8C%0A")
    red_draw.text((432, 700), weather_sunny_icon, font = weather_font, fill=0)

    y = -15
    x = 0
    LINE_SPACING = 3

    lines = []
    shabbat_items = scrape_shabbat_items()
    lines.append({
        "font":font_title,
        "text":reverse(shabbat_items['parasha_name']),
        "center": True,
        "bottom-margin": LINE_SPACING * 3
    })
    for title,times in shabbat_items['times'].items():
        if title in titles_to_remove:
            continue
        times = [t if t[-3]==':' else reverse(t) for t in times]
        lines.append({"font":font_text, "text": f"{', '.join(sorted(times, reverse=True))} :{reverse(title)}"})

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

    #draw_red.line((10, 90, 60, 140), fill = 0)
    #draw_red.line((60, 90, 10, 140), fill = 0)
    #draw_red.rectangle((10, 90, 60, 500), outline = 0)
    #draw_red.line((95, 90, 95, 140), fill = 0)
    #draw_black.line((70, 115, 120, 115), fill = 0)
    #draw_black.arc((70, 90, 120, 140), 0, 360, fill = 0)
    #draw_black.rectangle((10, 150, 60, 200), fill = 0)
    #draw_black.chord((70, 150, 120, 200), 0, 360, fill = 0)

    paste_red_and_black_image(name="sneaker", red_image=red_image, black_image=black_image, position=(30,height - 50))

    return EinkImage(red=red_image, black=black_image)

def join_image(src: EinkImage):
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
    color_image.save(dest / "joined.png")
    shabbat_image.black.save(str(dest / "black.png"))
    shabbat_image.red.save(str(dest / "red.png"))


    return shabbat_image


