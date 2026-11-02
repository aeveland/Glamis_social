#!/usr/bin/env python3
"""Build the daily Story/Reel video: captioned demo (headline over the opening), end card.

The demo starts on frame one so viewers see motion immediately (a static title
card made people swipe before they realised it was a video). The headline sits
over the first seconds of the demo, and the old title card is saved as
out/reel-cover.png for use as the Reel cover image.

Usage:  python3 tools/render_reel.py 2026-10-28

Reads   <day>/directions.md  (feature: line becomes the title)
        <day>/copy.json      (story_headline under the title)
        <day>/video.*        (hand + voiceover demo)
        <day>/captions.json  (optional; word timings, written on first run)
Writes  <day>/out/reel.mp4   (1080x1920, 30 fps, H.264 + AAC)
        <day>/out/reel-cover.png (title card, used as the Reel cover image)
        <day>/captions.json  (word timings from the voiceover; edit the "w"
                              values to fix a misheard word, then re-run)

Transcription uses faster-whisper (pip install faster-whisper). Set
WHISPER_MODEL to a model path; tools/get-whisper-model.sh downloads one.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from render import (BRAND, ROOT, STORY, WHITE, cover, font, parse_directions,  # noqa: E402
                    text_block, wrap)

ORANGE = (232, 98, 26, 255)      # app icon orange
FPS = 30
HEADLINE_DUR = 2.6   # headline overlay on the opening of the demo
HEADLINE_FADE = 0.4
HEADLINE_TOP = 290   # just below the top safe zone
END_DUR = 4.0
XFADE = 0.4

# Captions: lower third, above the Reels/Story caption + reply UI.
CAP_CENTER_Y = 1400
CAP_SIZE = 66
CAP_MAX_W = 900
CAP_MAX_WORDS = 4


# ---------------------------------------------------------------- helpers

def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def probe_duration(path):
    out = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                   "-of", "default=nw=1:nk=1", str(path)])
    return float(out)


def find_video(day):
    for ext in ("mp4", "mov", "MOV", "MP4", "m4v"):
        p = day / f"video.{ext}"
        if p.exists():
            return p
    sys.exit(f"No video.* in {day}")


def dune_background(darken=150):
    c = cover(Image.open(BRAND / "photo-glamis-dunes.jpg").convert("RGBA"), STORY)
    shade = Image.new("RGBA", STORY, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shade)
    for y in range(STORY[1]):
        a = int(darken * (0.35 + 0.65 * y / STORY[1]))
        sd.line([(0, y), (STORY[0], y)], fill=(30, 14, 0, a))
    c.alpha_composite(shade)
    return c


def app_icon(size):
    icon = Image.open(BRAND / "app-icon.png").convert("RGBA")
    solid = icon.split()[3].point(lambda v: 255 if v > 200 else 0).getbbox()
    return icon.crop(solid).resize((size, size), Image.LANCZOS)


def paste_icon(c, icon, x, y):
    sh = Image.new("RGBA", c.size, (0, 0, 0, 0))
    sh.paste((0, 0, 0, 90), (x, y + 14, x + icon.width, y + 14 + icon.height), icon.split()[3])
    c.alpha_composite(sh.filter(ImageFilter.GaussianBlur(16)))
    c.alpha_composite(icon, (x, y))


def ink(d, fnt, text="Hg"):
    b = d.textbbox((0, 0), text, font=fnt)
    return b[1], b[3] - b[1]


# ---------------------------------------------------------------- cards

def render_title(feature, headline, out):
    """Feature name big and centred, headline under it, brand lockup on top."""
    c = dune_background(170)
    d = ImageDraw.Draw(c)

    # Brand lockup: small icon + name, one line.
    icon = app_icon(96)
    nf = font("InterDisplay-SemiBold.otf", 50)
    nw = d.textlength("Glamis Guide", font=nf)
    gap = 24
    total = icon.width + gap + nw
    x0 = int(540 - total / 2)
    top = 560
    paste_icon(c, icon, x0, top)
    off, h = ink(d, nf, "Glamis Guide")
    text_block(c, ["Glamis Guide"], nf, x0 + icon.width + gap + nw / 2,
               top + (icon.height - h) / 2 - off, 60, shadow=0.45)

    # Orange rule
    y = top + icon.height + 90
    d.rounded_rectangle([540 - 60, y, 540 + 60, y + 10], radius=5, fill=ORANGE)
    y += 10 + 70

    # Feature title
    tf = font("InterDisplay-Bold.otf", 150)
    lines = wrap(d, feature, tf, 960)
    off, _ = ink(d, tf, "H")
    lh = 160
    text_block(c, lines, tf, 540, y - off, lh, shadow=0.55)
    last_off, last_h = ink(d, tf, lines[-1])
    y += lh * (len(lines) - 1) + (last_off + last_h - off) + 60

    # Headline
    if headline:
        hf = font("Inter-Medium.otf", 58)
        hl = wrap(d, headline, hf, 900)
        off, _ = ink(d, hf, "H")
        text_block(c, hl, hf, 540, y - off, 72, shadow=0.6)

    c.convert("RGB").save(out, quality=95)


def render_end(out):
    """Offline, free, App Store. Same lockup family as the download Story."""
    c = dune_background(160)
    stack = Image.new("RGBA", STORY, (0, 0, 0, 0))
    d = ImageDraw.Draw(stack)
    y = 0

    icon = app_icon(200)
    paste_icon(stack, icon, (STORY[0] - icon.width) // 2, y)
    y += icon.height + 30

    nf = font("InterDisplay-SemiBold.otf", 58)
    off, h = ink(d, nf, "Glamis Guide")
    text_block(stack, ["Glamis Guide"], nf, 540, y - off, 68, shadow=0.45)
    y += h + 80

    hf = font("InterDisplay-Bold.otf", 120)
    lines = ["Works offline.", "Always free."]
    off, _ = ink(d, hf, "H")
    lh = 132
    text_block(stack, lines, hf, 540, y - off, lh, shadow=0.5)
    last_off, last_h = ink(d, hf, lines[-1])
    y += lh * (len(lines) - 1) + (last_off + last_h - off) + 52

    sf = font("Inter-Medium.otf", 46)
    sub = "No signal. No account. No ads."
    off, h = ink(d, sf, sub)
    text_block(stack, [sub], sf, 540, y - off, 56, shadow=0.55)
    y += h + 56

    badge = Image.open(BRAND / "app-store-badge-cutout.png").convert("RGBA")
    bw = 500
    badge = badge.resize((bw, round(badge.height * bw / badge.width)), Image.LANCZOS)
    stack.alpha_composite(badge, ((STORY[0] - bw) // 2, y))
    y += badge.height + 44

    uf = font("Inter-Medium.otf", 42)
    url = "glamisguide.app"
    off, h = ink(d, uf, url)
    text_block(stack, [url], uf, 540, y - off, 50, shadow=0.55)
    bottom = y + h

    # Centre the stack between the top and bottom safe zones (Reels UI is tall at the bottom).
    safe_top, safe_bottom = 250, STORY[1] - 380
    shift = int(safe_top + (safe_bottom - safe_top - bottom) / 2)
    c.alpha_composite(stack, (0, shift))
    c.convert("RGB").save(out, quality=95)


def render_headline(headline, out):
    """Transparent overlay: headline in a dark pill near the top, same style as captions."""
    img = Image.new("RGBA", STORY, (0, 0, 0, 0))
    if headline:
        d = ImageDraw.Draw(img)
        fnt = font("InterDisplay-Bold.otf", 76)
        lines = wrap(d, headline, fnt, 880)
        off, h = ink(d, fnt, "Hg")
        lh = 92
        widest = max(d.textlength(l, font=fnt) for l in lines)
        padx, pady = 40, 30
        block_h = lh * (len(lines) - 1) + h
        top = HEADLINE_TOP
        d.rounded_rectangle([540 - widest / 2 - padx, top - pady,
                             540 + widest / 2 + padx, top + block_h + pady],
                            radius=30, fill=(20, 12, 6, 190))
        for i, line in enumerate(lines):
            w = d.textlength(line, font=fnt)
            d.text((540 - w / 2, top + i * lh - off), line, font=fnt, fill=WHITE)
        # Orange accent under the pill, echoing the cover's rule.
        y = top + block_h + pady + 18
        d.rounded_rectangle([540 - 50, y, 540 + 50, y + 8], radius=4, fill=ORANGE)
    img.save(out)


# ---------------------------------------------------------------- captions

def transcribe(video, tmp):
    from faster_whisper import WhisperModel
    import numpy as np
    raw = Path(tmp) / "a.raw"
    run(["ffmpeg", "-y", "-i", str(video), "-f", "s16le", "-ac", "1", "-ar", "16000", str(raw)])
    audio = np.fromfile(raw, dtype="<i2").astype("float32") / 32768.0
    model = WhisperModel(os.environ.get("WHISPER_MODEL", "small.en"), device="cpu", compute_type="int8")
    segs, _ = model.transcribe(audio, language="en", word_timestamps=True, vad_filter=True)
    return [{"w": w.word.strip(), "s": round(w.start, 2), "e": round(w.end, 2)}
            for s in segs for w in s.words]


def chunk_words(words, d, fnt):
    chunks, cur = [], []
    for w in words:
        trial = cur + [w]
        text = " ".join(x["w"] for x in trial)
        gap = cur and w["s"] - cur[-1]["e"] > 0.6
        if cur and (len(trial) > CAP_MAX_WORDS or d.textlength(text, font=fnt) > CAP_MAX_W or gap):
            chunks.append(cur)
            cur = [w]
        else:
            cur = trial
        if cur and cur[-1]["w"][-1:] in ".?!,":
            chunks.append(cur)
            cur = []
    if cur:
        chunks.append(cur)
    return chunks


def caption_frame(chunk, active, fnt):
    img = Image.new("RGBA", STORY, (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    words = [x["w"] for x in chunk]
    space = d.textlength(" ", font=fnt)
    widths = [d.textlength(w, font=fnt) for w in words]
    total = sum(widths) + space * (len(words) - 1)
    off, h = ink(d, fnt, "Hg")
    padx, pady = 34, 22
    x = 540 - total / 2
    top = CAP_CENTER_Y - h / 2
    d.rounded_rectangle([x - padx, top - pady, x + total + padx, top + h + pady],
                        radius=26, fill=(20, 12, 6, 175))
    for i, (w, ww) in enumerate(zip(words, widths)):
        d.text((x, top - off), w, font=fnt, fill=ORANGE if i == active else WHITE)
        x += ww + space
    return img


def build_caption_track(words, start, end, tmp):
    """Transparent PNG sequence (via concat list) timed to the voiceover."""
    fnt = font("InterDisplay-Bold.otf", CAP_SIZE)
    probe = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    blank = Path(tmp) / "cap_blank.png"
    Image.new("RGBA", STORY, (0, 0, 0, 0)).save(blank)

    events = []  # (t_start, t_end, png)
    chunks = chunk_words(words, probe, fnt)
    n = 0
    for ci, ch in enumerate(chunks):
        nxt = chunks[ci + 1][0]["s"] if ci + 1 < len(chunks) else ch[-1]["e"] + 0.6
        chunk_end = min(nxt, ch[-1]["e"] + 0.6)
        for wi, w in enumerate(ch):
            t0 = w["s"] if wi else ch[0]["s"]
            t1 = ch[wi + 1]["s"] if wi + 1 < len(ch) else chunk_end
            p = Path(tmp) / f"cap_{n:04d}.png"
            caption_frame(ch, wi, fnt).save(p)
            events.append((t0, t1, p))
            n += 1

    lines, t = [], start
    for t0, t1, p in events:
        t0, t1 = max(t0, start), min(t1, end)
        if t1 <= t:
            continue
        if t0 > t:
            lines += [f"file '{blank}'", f"duration {t0 - t:.3f}"]
            t = t0
        lines += [f"file '{p}'", f"duration {t1 - t:.3f}"]
        t = t1
    if t < end:
        lines += [f"file '{blank}'", f"duration {end - t:.3f}"]
    lines.append(f"file '{blank}'")
    lst = Path(tmp) / "captions.txt"
    lst.write_text("\n".join(lines) + "\n")
    return lst


# ---------------------------------------------------------------- main

def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    day = ROOT / sys.argv[1]
    directions = parse_directions(day / "directions.md")
    copy = json.loads((day / "copy.json").read_text()) if (day / "copy.json").exists() else {}
    feature = directions.get("feature") or "Glamis Guide"
    video = find_video(day)
    outdir = day / "out"
    outdir.mkdir(exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        cap_json = day / "captions.json"
        if cap_json.exists():
            words = json.loads(cap_json.read_text())
        else:
            words = transcribe(video, tmp)
            cap_json.write_text(json.dumps(words, indent=1))

        dur = probe_duration(video)
        main_end = min(dur, (words[-1]["e"] + 0.8) if words else dur)

        cover_png, end_png = Path(tmp) / "cover.png", Path(tmp) / "end.png"
        head_png = Path(tmp) / "headline.png"
        headline = copy.get("story_headline", "")
        render_title(feature, headline, cover_png)
        render_headline(headline, head_png)
        render_end(end_png)
        caps = build_caption_track(words, 0, main_end, tmp)

        off_end = main_end - XFADE                    # end card starts here
        total = off_end + END_DUR
        fade_st = HEADLINE_DUR - HEADLINE_FADE
        fc = (
            f"[0:v]trim=0:{main_end:.3f},setpts=PTS-STARTPTS,scale=1080:1920:force_original_aspect_ratio=increase,"
            f"crop=1080:1920,setsar=1,fps={FPS}[m0];"
            f"[1:v]fps={FPS},format=rgba[c];"
            f"[2:v]fps={FPS},format=rgba,fade=t=out:st={fade_st:.3f}:d={HEADLINE_FADE}:alpha=1[h];"
            f"[m0][c]overlay=0:0:shortest=1[m1];"
            f"[m1][h]overlay=0:0:eof_action=pass,format=yuv420p[m];"
            f"[3:v]scale=1080:1920,setsar=1,fps={FPS},format=yuv420p[e];"
            f"[m][e]xfade=transition=fade:duration={XFADE}:offset={off_end:.3f},format=yuv420p[v];"
            f"[0:a]atrim=0:{main_end:.3f},asetpts=PTS-STARTPTS,afade=t=out:st={main_end - 0.4:.3f}:d=0.4,"
            f"apad=whole_dur={total:.3f}[a]"
        )
        out = outdir / "reel.mp4"
        run(["ffmpeg", "-y",
             "-i", str(video),
             "-f", "concat", "-safe", "0", "-i", str(caps),
             "-loop", "1", "-t", f"{HEADLINE_DUR}", "-i", str(head_png),
             "-loop", "1", "-t", f"{END_DUR}", "-i", str(end_png),
             "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-r", str(FPS),
             "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(out)])
        # Stills: cover for the Reel thumbnail, plus the headline and end card for review.
        Image.open(cover_png).convert("RGB").save(outdir / "reel-cover.png")
        Image.open(head_png).save(outdir / "reel-headline.png")
        Image.open(end_png).save(outdir / "reel-end.png")
        old_title = outdir / "reel-title.png"
        if old_title.exists():
            old_title.unlink()
    print(out)


if __name__ == "__main__":
    main()
