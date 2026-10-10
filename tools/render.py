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

    icon = Image.open(BRAND / "app-icon.png").convert("RGBA").resize((300, 300), Image.LANCZOS)
    ish = Image.new("RGBA", STORY, (0, 0, 0, 0))
    ish.paste((0, 0, 0, 90), (390, 438, 690, 738), icon.split()[3])
    c.alpha_composite(ish.filter(ImageFilter.GaussianBlur(18)))
    c.alpha_composite(icon, (390, 420))

    d = ImageDraw.Draw(c)
    text_block(c, ["Glamis Guide"], font("InterDisplay-SemiBold.otf", 64), 540, 755, 70, shadow=0.45)

    hf = font("InterDisplay-Bold.otf", 132)
    lines = wrap(d, copy["story_headline"], hf, 960)
    text_block(c, lines, hf, 540, 940, 138, shadow=0.5)

    text_block(c, ["Free. No account. No ads."], font("Inter-Medium.otf", 46), 540, 1300, 56, shadow=0.55)

    badge = Image.open(BRAND / "app-store-badge-cutout.png").convert("RGBA")
    bw = 500
    badge = badge.resize((bw, round(badge.height * bw / badge.width)), Image.LANCZOS)
    c.alpha_composite(badge, ((STORY[0] - bw) // 2, 1395))

    uf = font("Inter-Medium.otf", 44)
    y = text_block(c, ["glamisguide.app"], uf, 540, 1600, 50, shadow=0.55)
    w = d.textlength("glamisguide.app", font=uf)
    d.line([(540 - w / 2, 1656), (540 + w / 2, 1656)], fill=WHITE, width=3)

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
