"""
Generates a 2-slide minimalist Instagram carousel for a Bhagavad Gita verse.

Slide 1: Sanskrit + English translation
Slide 2: Short explanation

Usage:
    python3 generate_card.py                 # generates all verses in data/verses.json
    python3 generate_card.py --chapter 2 --verse 47   # generate a single verse
"""

import json
import os
import argparse
import textwrap
from PIL import Image, ImageDraw, ImageFont

# ---------- Config ----------
WIDTH, HEIGHT = 1080, 1350  # Instagram 4:5 portrait (best feed real estate)
MARGIN = 90

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS_DIR = os.path.join(BASE_DIR, "fonts")
DATA_PATH = os.path.join(BASE_DIR, "data", "verses.json")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

# Minimalist palette: warm cream background, deep maroon/ink text, soft gold accent
BG_TOP = (250, 246, 238)
BG_BOTTOM = (241, 233, 219)
TEXT_MAIN = (61, 32, 30)      # deep maroon-brown
TEXT_SOFT = (120, 96, 84)     # muted brown-grey
ACCENT = (176, 124, 42)       # soft gold

FONT_SANS_REG = os.path.join(FONTS_DIR, "NotoSans-Regular.ttf")
FONT_SANS_BOLD = os.path.join(FONTS_DIR, "NotoSans-Bold.ttf")
FONT_DEV_REG = os.path.join(FONTS_DIR, "NotoSansDevanagari-Regular.ttf")
FONT_DEV_BOLD = os.path.join(FONTS_DIR, "NotoSansDevanagari-Bold.ttf")


def vertical_gradient(size, top_color, bottom_color):
    w, h = size
    base = Image.new("RGB", size, top_color)
    top = Image.new("RGB", size, top_color)
    bottom = Image.new("RGB", size, bottom_color)
    mask = Image.new("L", size)
    mask_data = []
    for y in range(h):
        mask_data.extend([int(255 * (y / h))] * w)
    mask.putdata(mask_data)
    base.paste(bottom, (0, 0), mask)
    return base


def wrap_text(draw, text, font, max_width):
    """Wrap text (handles literal newlines in source) to fit max_width."""
    lines = []
    for para in text.split("\n"):
        if para.strip() == "":
            lines.append("")
            continue
        words = para.split(" ")
        current = ""
        for word in words:
            trial = (current + " " + word).strip()
            bbox = draw.textbbox((0, 0), trial, font=font)
            if bbox[2] - bbox[0] <= max_width or current == "":
                current = trial
            else:
                lines.append(current)
                current = word
        lines.append(current)
    return lines


def draw_centered_lines(draw, lines, font, start_y, max_width, fill, line_spacing=1.35):
    y = start_y
    bbox_sample = draw.textbbox((0, 0), "Ag", font=font)
    line_height = (bbox_sample[3] - bbox_sample[1]) * line_spacing
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        x = (WIDTH - w) / 2
        draw.text((x, y), line, font=font, fill=fill)
        y += line_height
    return y


def draw_kicker(draw, text, y, fill=ACCENT, font=None):
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    x = (WIDTH - w) / 2
    draw.text((x, y), text, font=font, fill=fill)


def draw_footer(draw, page_label, font):
    bbox = draw.textbbox((0, 0), page_label, font=font)
    w = bbox[2] - bbox[0]
    x = (WIDTH - w) / 2
    draw.text((x, HEIGHT - MARGIN - 20), page_label, font=font, fill=TEXT_SOFT)
    # thin rule above footer
    draw.line(
        [(WIDTH / 2 - 40, HEIGHT - MARGIN - 40), (WIDTH / 2 + 40, HEIGHT - MARGIN - 40)],
        fill=ACCENT,
        width=3,
    )


def fit_font_to_lines(draw, text, font_path, max_width, max_lines, start_size, min_size):
    """Shrink font size until wrapped text fits within max_lines."""
    size = start_size
    while size >= min_size:
        font = ImageFont.truetype(font_path, size)
        lines = wrap_text(draw, text, font, max_width)
        if len(lines) <= max_lines:
            return font, lines
        size -= 4
    return ImageFont.truetype(font_path, min_size), wrap_text(
        draw, text, ImageFont.truetype(font_path, min_size), max_width
    )


def make_slide_1(verse):
    img = vertical_gradient((WIDTH, HEIGHT), BG_TOP, BG_BOTTOM)
    draw = ImageDraw.Draw(img)
    max_width = WIDTH - 2 * MARGIN

    kicker_font = ImageFont.truetype(FONT_SANS_BOLD, 30)
    kicker = f"BHAGAVAD GITA  ·  CHAPTER {verse['chapter']}, VERSE {verse['verse']}"
    draw_kicker(draw, kicker, MARGIN, font=kicker_font)

    # thin rule under kicker
    draw.line([(WIDTH / 2 - 60, MARGIN + 60), (WIDTH / 2 + 60, MARGIN + 60)], fill=ACCENT, width=3)

    y = MARGIN + 110
    sans_font, sans_lines = fit_font_to_lines(
        draw, verse["sanskrit"], FONT_DEV_REG, max_width, max_lines=6, start_size=58, min_size=38
    )
    y = draw_centered_lines(draw, sans_lines, sans_font, y, max_width, TEXT_MAIN, line_spacing=1.4)

    y += 50
    draw.line([(WIDTH / 2 - 40, y), (WIDTH / 2 + 40, y)], fill=ACCENT, width=2)
    y += 40

    trans_font, trans_lines = fit_font_to_lines(
        draw, f"\u201c{verse['translation']}\u201d", FONT_SANS_REG, max_width, max_lines=8,
        start_size=36, min_size=26,
    )
    draw_centered_lines(draw, trans_lines, trans_font, y, max_width, TEXT_SOFT, line_spacing=1.35)

    footer_font = ImageFont.truetype(FONT_SANS_REG, 26)
    draw_footer(draw, "1 / 2  ·  VERSE", footer_font)
    return img


def make_slide_2(verse):
    img = vertical_gradient((WIDTH, HEIGHT), BG_TOP, BG_BOTTOM)
    draw = ImageDraw.Draw(img)
    max_width = WIDTH - 2 * MARGIN

    kicker_font = ImageFont.truetype(FONT_SANS_BOLD, 30)
    draw_kicker(draw, "WHAT IT MEANS", MARGIN, font=kicker_font)
    draw.line([(WIDTH / 2 - 60, MARGIN + 60), (WIDTH / 2 + 60, MARGIN + 60)], fill=ACCENT, width=3)

    y = MARGIN + 120
    body_font, body_lines = fit_font_to_lines(
        draw, verse["explanation"], FONT_SANS_REG, max_width, max_lines=13,
        start_size=38, min_size=26,
    )
    draw_centered_lines(draw, body_lines, body_font, y, max_width, TEXT_MAIN, line_spacing=1.45)

    footer_font = ImageFont.truetype(FONT_SANS_REG, 26)
    draw_footer(draw, "2 / 2  ·  MEANING", footer_font)
    return img


def generate(verse, out_dir=OUTPUT_DIR):
    os.makedirs(out_dir, exist_ok=True)
    tag = f"ch{verse['chapter']}_v{verse['verse']}"
    slide1 = make_slide_1(verse)
    slide2 = make_slide_2(verse)
    path1 = os.path.join(out_dir, f"{tag}_slide1.png")
    path2 = os.path.join(out_dir, f"{tag}_slide2.png")
    slide1.save(path1)
    slide2.save(path2)
    return path1, path2


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--chapter", type=int)
    parser.add_argument("--verse", type=int)
    args = parser.parse_args()

    with open(DATA_PATH, encoding="utf-8") as f:
        verses = json.load(f)

    if args.chapter is not None and args.verse is not None:
        verses = [v for v in verses if v["chapter"] == args.chapter and v["verse"] == args.verse]
        if not verses:
            print("Verse not found in data/verses.json")
            return

    for v in verses:
        p1, p2 = generate(v)
        print(f"Generated: {p1}, {p2}")


if __name__ == "__main__":
    main()
