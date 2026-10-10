#!/usr/bin/env python3
"""Render the daily Glamis Guide graphics.

Usage:  python3 tools/render.py 2026-10-12

Reads   <day>/directions.md, <day>/copy.json, <day>/screenshot.png
Writes  <day>/out/story-download.png  (1080x1920, 10 AM download Story)
        <day>/out/post.png            (1080x1350, 5 PM feed post)

Layouts are fixed here on purpose. Daily variation comes only from copy.json
and the screenshot, so every post looks like part of one series.
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
BRAND = ROOT / "brand"
FONTS = BRAND / "fonts"

STORY = (1080, 1920)
POST = (1080, 1350)
WHITE = (255, 255, 255, 255)

# Transparent screen hole in each mockup PNG: x, y, w, h (source pixels).
# Re-measure with tools/measure_mockups.py if a mockup file is replaced.
MOCKUPS = {
    "iphone": {"file": "mockup-iphone-hand.png", "hole": (156, 87, 431, 915)},
    "ipad": {"file": "mockup-ipad-hands.png", "hole": (364, 118, 809, 546)},
    "watch": {"file": "mockup-apple-watch-wrist.png", "hole": (826, 317, 177, 206)},
}

# Where each device's screen lands on the 1080x1350 post:
# target screen width, screen centre x, screen top y.
POST_PLACEMENT = {
    "iphone": {"screen_w": 470, "cx": 540, "top": 500},
    "ipad": {"screen_w": 820, "cx": 540, "top": 590},
    "watch": {"screen_w": 330, "cx": 540, "top": 700},
}


def font(name, size):
    return ImageFont.truetype(str(FONTS / name), size)


def parse_directions(path):
    data = {}
    for line in path.read_text().splitlines():
        line = line.split("#", 1)[0].rstrip()
        if ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1)
            data[k.strip().lower()] = v.strip()
    return data


def find_screenshot(day):
    for ext in ("png", "PNG", "jpg", "jpeg", "JPG", "JPEG", "heic"):
        p = day / f"screenshot.{ext}"
        if p.exists():
            return p
    return None


def pick_device(shot, override=""):
    override = (override or "").strip().lower()
    if override in MOCKUPS:
        return override
    w, h = shot.size
    ratio = w / h
    if max(w, h) < 1000 and 0.7 < ratio < 1.0:
        return "watch"
    if ratio < 0.6:
        return "iphone"
    return "ipad"


def cover(img, size):
    tw, th = size
    s = max(tw / img.width, th / img.height)
    r = img.resize((round(img.width * s), round(img.height * s)), Image.LANCZOS)
    x = (r.width - tw) // 2
    y = (r.height - th) // 2
    return r.crop((x, y, x + tw, y + th))


def wrap(draw, text, fnt, max_w):
    """Use explicit line breaks if given, otherwise balance into the fewest lines."""
    if "\\n" in text or "\n" in text:
        return [l.strip() for l in text.replace("\\n", "\n").split("\n")]
    words = text.split()
    for n in range(1, len(words) + 1):
        # balanced split into n lines
        best = None
        def splits(ws, k):
            if k == 1:
                yield [" ".join(ws)]
                return
            for i in range(1, len(ws) - k + 2):
                for rest in splits(ws[i:], k - 1):
                    yield [" ".join(ws[:i])] + rest
        for cand in splits(words, n):
            widths = [draw.textlength(l, font=fnt) for l in cand]
            if max(widths) <= max_w:
                score = max(widths) - min(widths)
                if best is None or score < best[0]:
                    best = (score, cand)
        if best:
            return best[1]
    return [text]


def text_block(canvas, lines, fnt, cx, top, line_h, fill=WHITE, shadow=0):
    """Centered multi-line text with an optional soft drop shadow."""
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    y = top
    for l in lines:
        w = d.textlength(l, font=fnt)
        d.text((cx - w / 2, y), l, font=fnt, fill=fill)
        y += line_h
    if shadow:
        a = layer.split()[3]
        sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        sh.putalpha(a.point(lambda v: int(v * shadow)))
        sh = sh.filter(ImageFilter.GaussianBlur(10))
        canvas.alpha_composite(sh, (0, 5))
    canvas.alpha_composite(layer)
    return y


def render_story(copy, out):
    c = cover(Image.open(BRAND / "photo-glamis-dunes.jpg").convert("RGBA"), STORY)
    # gentle darkening so white type holds on bright sand
    shade = Image.new("RGBA", STORY, (40, 20, 0, 0))
    sd = ImageDraw.Draw(shade)
    for y in range(STORY[1]):
        a = int(70 * max(0, (y - 600) / 1320))
        sd.line([(0, y), (STORY[0], y)], fill=(40, 20, 0, a))
    c.alpha_composite(shade)

    base = c
    c = Image.new("RGBA", STORY, (0, 0, 0, 0))  # stack is drawn here, then pinned to the bottom
    d = ImageDraw.Draw(c)

    def ink(fnt, text="Hg"):
        """Top offset and height of the visible glyphs, for tight spacing."""
        b = d.textbbox((0, 0), text, font=fnt)
        return b[1], b[3] - b[1]

    # Vertical stack, top to bottom. Gaps are the visible space between elements.
    y = 0                        # stack starts at 0; it is shifted down at the end
    ICON = 220
    GAP_ICON_TITLE = 32          # icon and app name read as one unit
    GAP_TITLE_HEAD = 84
    GAP_HEAD_SUB = 56
    GAP_SUB_BADGE = 36
    GAP_BADGE_URL = 44

    icon = Image.open(BRAND / "app-icon.png").convert("RGBA")
    solid = icon.split()[3].point(lambda v: 255 if v > 200 else 0).getbbox()
    icon = icon.crop(solid).resize((ICON, ICON), Image.LANCZOS)  # trim baked-in shadow + padding
    ix = (STORY[0] - ICON) // 2
    ish = Image.new("RGBA", STORY, (0, 0, 0, 0))
    ish.paste((0, 0, 0, 90), (ix, y + 16, ix + ICON, y + 16 + ICON), icon.split()[3])
    c.alpha_composite(ish.filter(ImageFilter.GaussianBlur(18)))
    c.alpha_composite(icon, (ix, y))
    y += ICON + GAP_ICON_TITLE

    tf = font("InterDisplay-SemiBold.otf", 60)
    off, h = ink(tf, "Glamis Guide")
    text_block(c, ["Glamis Guide"], tf, 540, y - off, 70, shadow=0.45)
    y += h + GAP_TITLE_HEAD

    hf = font("InterDisplay-Bold.otf", 132)
    lines = wrap(d, copy["story_headline"], hf, 960)
    off, _ = ink(hf, "H")
    lh = 140
    text_block(c, lines, hf, 540, y - off, lh, shadow=0.5)
    last_off, last_h = ink(hf, lines[-1])
    y += lh * (len(lines) - 1) + (last_off + last_h - off) + GAP_HEAD_SUB

    sf = font("Inter-Medium.otf", 46)
    sub = "Free. No account. No ads."
    off, h = ink(sf, sub)
    text_block(c, [sub], sf, 540, y - off, 56, shadow=0.55)
    y += h + GAP_SUB_BADGE

    badge = Image.open(BRAND / "app-store-badge-cutout.png").convert("RGBA")
    bw = 480
    badge = badge.resize((bw, round(badge.height * bw / badge.width)), Image.LANCZOS)
    c.alpha_composite(badge, ((STORY[0] - bw) // 2, y))
    y += badge.height + GAP_BADGE_URL

    uf = font("Inter-Medium.otf", 42)
    url = "glamisguide.app"
    off, h = ink(uf, url)
    text_block(c, [url], uf, 540, y - off, 50, shadow=0.55)
    w = d.textlength(url, font=uf)
    uy = y + h + 8
    d.line([(540 - w / 2, uy), (540 + w / 2, uy)], fill=WHITE, width=3)
    # Pin the stack: its last line sits BOTTOM_PAD above the bottom edge.
    BOTTOM_PAD = 200             # bottom padding; Instagram reply bar covers roughly the last 150-200 px
    shift = STORY[1] - BOTTOM_PAD - uy
    base.alpha_composite(c, (0, shift))
    c = base

    c.convert("RGB").save(out, quality=95)


def render_post(copy, shot, device, out):
    c = cover(Image.open(BRAND / "gradient-orange.jpg").convert("RGBA"), POST)
    d = ImageDraw.Draw(c)

    m = MOCKUPS[device]
    p = POST_PLACEMENT[device]
    mock = Image.open(BRAND / m["file"]).convert("RGBA")
    hx, hy, hw, hh = m["hole"]
    s = p["screen_w"] / hw
    mock = mock.resize((round(mock.width * s), round(mock.height * s)), Image.LANCZOS)
    sx = round(p["cx"] - (hx + hw / 2) * s)
    sy = round(p["top"] - hy * s)

    # screenshot sits behind the mockup, filling the screen hole
    pad = 4
    sw, sh = round(hw * s) + pad * 2, round(hh * s) + pad * 2
    scr = cover(shot.convert("RGBA"), (sw, sh))
    c.alpha_composite(scr, (sx + round(hx * s) - pad, sy + round(hy * s) - pad))

    # soft shadow under the device + hand
    sh_layer = Image.new("RGBA", POST, (0, 0, 0, 0))
    a = mock.split()[3].point(lambda v: int(v * 0.35))
    shadow = Image.new("RGBA", mock.size, (90, 30, 0, 0))
    shadow.putalpha(a)
    sh_layer.paste(shadow, (sx, sy + 24), shadow)
    c.alpha_composite(sh_layer.filter(ImageFilter.GaussianBlur(28)))
    layer = Image.new("RGBA", POST, (0, 0, 0, 0))
    layer.paste(mock, (sx, sy), mock)
    c.alpha_composite(layer)

    hf = font("InterDisplay-Bold.otf", 98)
    lines = wrap(d, copy["post_headline"], hf, 960)
    y = text_block(c, lines, hf, 540, 84, 102)
    sf = font("Inter-Regular.otf", 42)
    sub = wrap(d, copy["post_subline"], sf, 940)
    text_block(c, sub, sf, 540, y + 26, 52)

    c.convert("RGB").save(out, quality=95)


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: render.py <YYYY-MM-DD>")
    day = ROOT / sys.argv[1]
    directions = parse_directions(day / "directions.md")
    copy = json.loads((day / "copy.json").read_text())
    shot_path = find_screenshot(day)
    if not shot_path:
        sys.exit(f"no screenshot in {day}")
    shot = Image.open(shot_path)
    device = pick_device(shot, directions.get("device", ""))
    (day / "out").mkdir(exist_ok=True)
    render_story(copy, day / "out" / "story-download.png")
    render_post(copy, shot, device, day / "out" / "post.png")
    print(f"rendered {day.name}: device={device}")


if __name__ == "__main__":
    main()
