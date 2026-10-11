#!/usr/bin/env python3
"""Add Apple Reminders when upcoming Glamis Social content is not ready.

  python3 tools/nudge.py daily    # 3 PM: checks tomorrow, reminder due 5 PM today
  python3 tools/nudge.py weekly   # Monday 8 AM: rundown of the next 7 days

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


def daily():
    today = dt.date.today()
    tomorrow = today + dt.timedelta(days=1)
    need = missing_for(tomorrow)
    if not need:
        print(f"{tomorrow} ready")
        return
    label = tomorrow.strftime("%a %b %-d")
    title = f"Glamis: content for {label} due 5 PM"
    notes = f"Tomorrow: {describe(tomorrow)}.\nStill needed: {', '.join(need)}."
    add_reminder(title, notes, dt.datetime.combine(today, dt.time(17, 0)))
    print(title, "|", notes)


def weekly():
    today = dt.date.today()
    lines = []
    for i in range(7):
        day = today + dt.timedelta(days=i)
        need = missing_for(day)
        status = "ready" if not need else "needs " + ", ".join(need)
        lines.append(f"{day.strftime('%a %b %-d')}: {describe(day)} — {status}")
    upcoming = [(n, s) for n, s, e in RAMPS if s >= today]
    if upcoming:
        n, s = upcoming[0]
        lines.append(f"\nNext ramp-up: {n}, starts {s.strftime('%a %b %-d')} ({(s - today).days} days).")
    title = f"Glamis: week of {today.strftime('%b %-d')}"
    add_reminder(title, "\n".join(lines), dt.datetime.combine(today, dt.time(9, 0)))
    print(title)
    print("\n".join(lines))


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "daily"
    pull()
    {"daily": daily, "weekly": weekly}[mode]()
