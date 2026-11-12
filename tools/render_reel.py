#!/usr/bin/env python3
"""Build the daily Story/Reel video: framed screen recording, spoken captions, end card.

Andy's screen recording plays inside a device frame (iPhone, iPad or Watch,
picked from the recording's size) over the darkened dune photo. The video opens
directly on the demo: no title screen and no headline overlay. Captions from
the voiceover sit in the band under the device. The end card carries a title
written for that video plus the App Store badge.

Usage:  python3 tools/render_reel.py 2026-11-13

Reads   <day>/directions.md  (feature:, device:, end title:)
        <day>/copy.json      (story_headline for the cover, end_title for the end card)
        <day>/video.*        (screen recording; its own sound is not used when a voiceover exists)
        <day>/voiceover.*    (separate voiceover; starts at the same moment as the video)
        <day>/captions.json  (optional; word timings, written on first run)
Writes  <day>/out/reel.mp4   (1080x1920, 30 fps, H.264 + AAC)
        <day>/out/reel-cover.png (title card, used as the Reel cover image)
        <day>/out/reel-end.png   (end card still, for review)
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
END_DUR = 3.5
XFADE = 0.4
TAIL = 0.8           # demo keeps running this long after the last spoken word

# The device sits inside this band; captions go in the band under it.
DEVICE_TOP, DEVICE_BOTTOM = 170, 1380
CAP_CENTER_Y = 1466  # above the Reels/Story caption + reply UI
CAP_SIZE = 64
CAP_MAX_W = 900
CAP_MAX_WORDS = 4

# Per device: largest screen box (w, h), bezel px, screen corner radius as a
# share of the screen's short side, and rim colour.
DEVICES = {
    "iphone": {"box": (900, 1130), "bezel": 16, "radius": 0.142, "rim": (112, 108, 104, 255)},
    "ipad":   {"box": (880, 1090), "bezel": 30, "radius": 0.030, "rim": (120, 120, 124, 255)},
    "watch":  {"box": (600, 740),  "bezel": 30, "radius": 0.230, "rim": (58, 58, 60, 255)},
}
AUDIO_EXTS = ("m4a", "mp3", "wav", "aac", "caf", "aiff", "aif", "mp4", "mov")


# ---------------------------------------------------------------- helpers

def run(cmd):
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        sys.exit(e.stderr.decode(errors="replace")[-2000:])


def probe_duration(path):
    out = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                   "-of", "default=nw=1:nk=1", str(path)])
    return float(out)


def has_audio(path):
    out = subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "a",
                                   "-show_entries", "stream=index", "-of", "csv=p=0", str(path)])
    return bool(out.strip())


def is_silent(path):
    """True when the loudest sample is below -50 dB (a screen recording made with the mic off)."""
    err = subprocess.run(["ffmpeg", "-i", str(path), "-vn", "-af", "volumedetect", "-f", "null", "-"],
                         stderr=subprocess.PIPE, stdout=subprocess.DEVNULL).stderr.decode(errors="replace")
    for line in err.splitlines():
        if "max_volume" in line:
            return float(line.split("max_volume:")[1].split("dB")[0]) < -50
    return True


def find_video(day):
    for p in sorted(day.glob("video.*")):
        return p
    sys.exit(f"No video.* in {day}")


def find_voiceover(day):
    for p in sorted(day.glob("voiceover.*")):
        if p.suffix.lower().lstrip(".") in AUDIO_EXTS:
            return p
    return None


def frame_size(video, tmp):
    """Displayed size of the recording (ffmpeg applies any rotation flag)."""
    p = Path(tmp) / "first.png"
    run(["ffmpeg", "-y", "-i", str(video), "-frames:v", "1", str(p)])
    return Image.open(p).size


def pick_reel_device(size, override=""):
    """Same rule as render.pick_device, applied to the recording instead of the screenshot."""
    override = (override or "").strip().lower()
    if override in DEVICES:
        return override
    w, h = size
    ratio = w / h
    if max(w, h) < 1000 and 0.7 < ratio < 1.0:
        return "watch"
    if ratio < 0.6:
        return "iphone"
    return "ipad"


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


# ---------------------------------------------------------------- device stage

def render_stage(device, size, tmp):
    """Background (blurred dune photo + device shadow), device frame with a
    transparent screen, and the rounded screen mask. Returns their paths and
    the screen rectangle (x, y, w, h)."""
    spec = DEVICES[device]
    bw, bh = spec["box"]
    s = min(bw / size[0], bh / size[1])
    sw, sh = int(size[0] * s) // 2 * 2, int(size[1] * s) // 2 * 2
    bz = spec["bezel"]
    r = round(min(sw, sh) * spec["radius"])
    px = (STORY[0] - sw) // 2
    py = DEVICE_TOP + bz + (DEVICE_BOTTOM - DEVICE_TOP - 2 * bz - sh) // 2

    # Background: blurred, darkened dune photo so the screen and captions carry the frame.
    bg = cover(Image.open(BRAND / "photo-glamis-dunes.jpg").convert("RGBA"), STORY)
    bg = bg.filter(ImageFilter.GaussianBlur(16))
    shade = Image.new("RGBA", STORY, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shade)
    for y in range(STORY[1]):
        sd.line([(0, y), (STORY[0], y)], fill=(24, 12, 2, int(150 * (0.8 + 0.2 * y / STORY[1]))))
    bg.alpha_composite(shade)
    drop = Image.new("RGBA", STORY, (0, 0, 0, 0))
    ImageDraw.Draw(drop).rounded_rectangle([px - bz, py - bz + 34, px + sw + bz, py + sh + bz + 34],
                                           radius=r + bz, fill=(0, 0, 0, 170))
    bg.alpha_composite(drop.filter(ImageFilter.GaussianBlur(40)))
    bg_png = Path(tmp) / "stage_bg.png"
    bg.convert("RGB").save(bg_png)

    # Frame, drawn at 3x and scaled down for clean edges.
    k = 3
    fr = Image.new("RGBA", (STORY[0] * k, STORY[1] * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(fr)

    def box(g):
        return [(px - g) * k, (py - g) * k, (px + sw + g) * k, (py + sh + g) * k]

    def button(x, y, w, h, fill):
        d.rounded_rectangle([x * k, y * k, (x + w) * k, (y + h) * k], radius=min(w, h) / 2 * k, fill=fill)

    side = (70, 68, 66, 255)
    if device == "iphone":
        left, right = px - bz - 4, px + sw + bz - 2
        for by, bh_ in ((0.22, 0.05), (0.30, 0.10), (0.41, 0.10)):
            button(left, py + sh * by, 6, sh * bh_, side)
        button(right, py + sh * 0.35, 6, sh * 0.15, side)
    elif device == "watch":
        right = px + sw + bz - 6
        button(right, py + sh * 0.22, 26, sh * 0.20, (86, 86, 90, 255))   # crown
        button(right, py + sh * 0.56, 14, sh * 0.22, (66, 66, 70, 255))   # side button
    d.rounded_rectangle(box(bz), radius=(r + bz) * k, fill=spec["rim"])
    d.rounded_rectangle(box(bz - 3), radius=(r + bz - 3) * k, fill=(8, 8, 9, 255))
    d.rounded_rectangle(box(0), radius=r * k, fill=(0, 0, 0, 0))
    frame_png = Path(tmp) / "stage_frame.png"
    fr.resize(STORY, Image.LANCZOS).save(frame_png)

    m = Image.new("L", (sw * k, sh * k), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, sw * k, sh * k], radius=r * k, fill=255)
    mask_png = Path(tmp) / "stage_mask.png"
    m.resize((sw, sh), Image.LANCZOS).save(mask_png)
    return bg_png, frame_png, mask_png, (px, py, sw, sh)


# ---------------------------------------------------------------- cards

def render_title(feature, headline, out):
    """Feature name big and centred, headline under it, brand lockup on top. Reel cover image only."""
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


def render_end(title, out):
    """Closing title for this video, then offline + free, App Store badge, site."""
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

    # Title: as large as fits in three lines or fewer.
    for size in (120, 108, 96, 84, 72):
        hf = font("InterDisplay-Bold.otf", size)
        lines = wrap(d, title, hf, 940)
        if len(lines) <= 3:
            break
    off, _ = ink(d, hf, "H")
    lh = round(size * 1.1)
    text_block(stack, lines, hf, 540, y - off, lh, shadow=0.5)
    last_off, last_h = ink(d, hf, lines[-1])
    y += lh * (len(lines) - 1) + (last_off + last_h - off) + 52

    sf = font("Inter-Medium.otf", 46)
    sub = "Works offline. Always free."
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


# ---------------------------------------------------------------- captions

def transcribe(audio_src, tmp):
    from faster_whisper import WhisperModel
    import numpy as np
    raw = Path(tmp) / "a.raw"
    run(["ffmpeg", "-y", "-i", str(audio_src), "-vn", "-f", "s16le", "-ac", "1", "-ar", "16000", str(raw)])
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
                        radius=26, fill=(20, 12, 6, 185))
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
    headline = copy.get("story_headline", "")
    end_title = (directions.get("end title") or copy.get("end_title") or headline
                 or "The dunes, in your pocket.")
    video = find_video(day)
    outdir = day / "out"
    outdir.mkdir(exist_ok=True)

    # Sound: the separate voiceover when there is one, else the recording's own track.
    audio_src = find_voiceover(day)
    if audio_src is None and has_audio(video) and not is_silent(video):
        audio_src = video
    if audio_src is None:
        print("WARNING: no voiceover.* and the video is silent. Building without sound or captions.",
              file=sys.stderr)

    with tempfile.TemporaryDirectory() as tmp:
        cap_json = day / "captions.json"
        if cap_json.exists():
            words = json.loads(cap_json.read_text())
        elif audio_src is not None:
            words = transcribe(audio_src, tmp)
            cap_json.write_text(json.dumps(words, indent=1))
        else:
            words = []

        # The demo runs until just after the last spoken word. That drops the tail of the
        # recording (Control Center, stopping the recording). If the voiceover outlasts the
        # video, the last frame holds.
        vdur = probe_duration(video)
        main_end = (words[-1]["e"] + TAIL) if words else vdur
        hold = max(0.0, main_end - vdur) + 0.5

        size = frame_size(video, tmp)
        device = pick_reel_device(size, directions.get("device", ""))
        bg_png, frame_png, mask_png, (px, py, sw, sh) = render_stage(device, size, tmp)

        cover_png, end_png = Path(tmp) / "cover.png", Path(tmp) / "end.png"
        render_title(feature, headline, cover_png)
        render_end(end_title, end_png)
        caps = build_caption_track(words, 0, main_end, tmp)

        off_end = main_end - XFADE                    # end card starts here
        total = off_end + END_DUR
        fc = (
            f"[1:v]fps={FPS},scale={sw}:{sh}:flags=lanczos,setsar=1,"
            f"tpad=stop_mode=clone:stop_duration={hold:.3f},"
            f"trim=0:{main_end:.3f},setpts=PTS-STARTPTS,format=rgba[scr0];"
            f"[2:v]format=gray[mk];[scr0][mk]alphamerge[scr];"
            f"[0:v][scr]overlay={px}:{py}[m0];"
            f"[m0][3:v]overlay=0:0[m1];"
            f"[4:v]fps={FPS},format=rgba[c];"
            f"[m1][c]overlay=0:0:eof_action=pass,trim=0:{main_end:.3f},setpts=PTS-STARTPTS,"
            f"fps={FPS},format=yuv420p[m];"
            f"[5:v]scale=1080:1920,setsar=1,fps={FPS},format=yuv420p[e];"
            f"[m][e]xfade=transition=fade:duration={XFADE}:offset={off_end:.3f},format=yuv420p[v];"
        )
        cmd = ["ffmpeg", "-y",
               "-loop", "1", "-framerate", str(FPS), "-t", f"{main_end:.3f}", "-i", str(bg_png),
               "-i", str(video),
               "-loop", "1", "-i", str(mask_png),
               "-loop", "1", "-i", str(frame_png),
               "-f", "concat", "-safe", "0", "-i", str(caps),
               "-loop", "1", "-framerate", str(FPS), "-t", f"{END_DUR}", "-i", str(end_png)]
        if audio_src is not None:
            cmd += ["-i", str(audio_src)]
            fc += (f"[6:a]atrim=0:{main_end:.3f},asetpts=PTS-STARTPTS,"
                   f"loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000,"
                   f"afade=t=out:st={max(0.0, main_end - 0.4):.3f}:d=0.4,apad=whole_dur={total:.3f}[a]")
        else:
            cmd += ["-f", "lavfi", "-t", f"{total:.3f}", "-i", "anullsrc=r=48000:cl=stereo"]
            fc += "[6:a]anull[a]"
        out = outdir / "reel.mp4"
        run(cmd + ["-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-t", f"{total:.3f}",
                   "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-r", str(FPS),
                   "-c:a", "aac", "-b:a", "160k", "-ac", "2", "-movflags", "+faststart", str(out)])
        # Stills: cover for the Reel thumbnail, plus the end card for review.
        Image.open(cover_png).convert("RGB").save(outdir / "reel-cover.png")
        Image.open(end_png).save(outdir / "reel-end.png")
        for old in ("reel-title.png", "reel-headline.png"):
            if (outdir / old).exists():
                (outdir / old).unlink()
    print(f"{out}  (device: {device}, sound: {audio_src.name if audio_src else 'none'})")


if __name__ == "__main__":
    main()
