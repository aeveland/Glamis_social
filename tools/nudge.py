#!/usr/bin/env python3
"""Add Apple Reminders when upcoming Glamis Social content is not ready.

  python3 tools/nudge.py weekly   # Monday 8 AM: two reminders per day for the next 7 days
  python3 tools/nudge.py daily    # 3 PM: makes sure tomorrow's two reminders exist

Per posting day, both due the evening before:
  "Glamis: create content for <day>"  5 PM
  "Glamis: review drafts for <day>"   7 PM

Runs on Andy's Mac via launchd (see tools/install-nudge.sh).
Reminders go to the list "Glamis Social" and sync to iPhone through iCloud.
"""
import datetime as dt
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIST = "Glamis Social"
FEED_DAYS = {1, 3, 5}  # Tue, Thu, Sat (Mon = 0)

# Ramp-up windows: feed post every day inside these dates (inclusive).
RAMPS = [
    ("Halloween", dt.date(2026, 10, 24), dt.date(2026, 11, 1)),
    ("Thanksgiving", dt.date(2026, 11, 19), dt.date(2026, 11, 29)),
    ("New Year's", dt.date(2026, 12, 26), dt.date(2027, 1, 3)),
    ("Presidents' Day", dt.date(2027, 2, 6), dt.date(2027, 2, 15)),
]


def ramp_for(day):
    for name, start, end in RAMPS:
        if start <= day <= end:
            return name
    return None


def is_feed_day(day):
    return day.weekday() in FEED_DAYS or ramp_for(day) is not None


def missing_for(day):
    """List what is still needed for a day. Empty list = ready."""
    folder = ROOT / day.isoformat()
    if not folder.is_dir():
        return ["folder (run New Day)", "video", "screenshot", "directions.md"]
    need = []
    if not any(folder.glob("video.*")):
        need.append("video")
    if not any(folder.glob("screenshot.*")):
        need.append("screenshot")
    d = folder / "directions.md"
    fields = {}
    if d.exists():
        for line in d.read_text().splitlines():
            line = line.split("#", 1)[0]
            if ":" in line:
                k, v = line.split(":", 1)
                fields[k.strip().lower()] = v.strip()
    if not fields.get("feature"):
        need.append("feature name in directions.md")
    if fields.get("status", "").lower() != "ready":
        need.append("status: ready + save")
    return need


def describe(day):
    parts = ["Story pair", "Reel"]
    if is_feed_day(day):
        parts.append("feed post")
    ramp = ramp_for(day)
    return " + ".join(parts) + (f" ({ramp} ramp-up)" if ramp else "")


def osa(s):
    return s.replace("\\", "\\\\").replace('"', '\\"')


def add_reminder(title, notes, due):
    due_str = due.strftime("%A, %B %-d, %Y at %-I:%M:%S %p")
    script = f'''
tell application "Reminders"
  if not (exists list "{LIST}") then make new list with properties {{name:"{LIST}"}}
  set L to list "{LIST}"
  if (count of (reminders of L whose name is "{osa(title)}" and completed is false)) is 0 then
    make new reminder at end of L with properties {{name:"{osa(title)}", body:"{osa(notes)}", due date:date "{due_str}"}}
  end if
end tell'''
    subprocess.run(["osascript", "-e", script], check=True)


def pull():
    subprocess.run(["git", "-C", str(ROOT), "pull", "-q", "--rebase"],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def add_day(day):
    """Two checkable reminders for one posting day, both due the evening before."""
    label = day.strftime("%a %b %-d")
    eve = day - dt.timedelta(days=1)
    need = missing_for(day)
    still = f"\nStill needed: {', '.join(need)}." if need else "\nFolder is ready."
    add_reminder(
        f"Glamis: create content for {label}",
        f"Posts: {describe(day)}.\nAdd video, screenshot, directions.md. Set status: ready and save.{still}",
        dt.datetime.combine(eve, dt.time(17, 0)),
    )
    add_reminder(
        f"Glamis: review drafts for {label}",
        "Metricool Planner: check the drafts and schedule them. The build runs at 5:55 PM.",
        dt.datetime.combine(eve, dt.time(19, 0)),
    )
    print(f"{label}: {describe(day)}")


def daily():
    """Safety net: make sure tomorrow's pair exists (no duplicates are created)."""
    add_day(dt.date.today() + dt.timedelta(days=1))


def weekly():
    """Create the pair for each of the next 7 posting days."""
    today = dt.date.today()
    for i in range(1, 8):
        add_day(today + dt.timedelta(days=i))


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "daily"
    pull()
    {"daily": daily, "weekly": weekly}[mode]()
