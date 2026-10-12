# Glamis Social

Daily Instagram ([@glamisguide](https://www.instagram.com/glamisguide)) and Facebook Page content for **Glamis Guide**, a free iOS map app for the Imperial Sand Dunes ([glamisguide.app](https://glamisguide.app)).

Andy records a short feature demo and a screenshot each evening. A nightly Claude build writes the copy, renders the graphics, and queues everything in Metricool for the next day.

## How a day works

| When (PT) | Who | What |
|---|---|---|
| By 7:30 PM, the evening before | Andy | Adds `video`, `screenshot.png` and `directions.md` (`status: ready`) to a new day folder and publishes it |
| 7:45 PM | Claude (scheduled task "Glamis nightly build") | Writes `copy.json`, renders `out/`, commits, creates the Metricool items, sends a report |
| After the report | Andy | Checks the items in Metricool and schedules them |
| 9:58 AM | Claude (scheduled task "Glamis sticker reminder") | Phone reminder with the `ig_story` link |
| 10:00 / 10:01 AM | Andy | Opens each Story notification, adds the link sticker, and shares |
| 12:00 PM, 5:00 PM | Metricool | Reels and feed posts publish on their own |

## What gets posted

| Time (PT) | Item | Asset | Publishing |
|---|---|---|---|
| 10:00 AM | Instagram Story 1 | Feature video | Notification. Andy adds the link sticker |
| 10:01 AM | Instagram Story 2 | `out/story-download.png` | Notification. Andy adds the link sticker |
| 12:00 PM | Instagram Reel + Facebook Reel | Feature video + captions | Auto |
| 5:00 PM | Instagram feed post + Facebook post | `out/post.png` + captions | Auto. Tue, Thu, Sat, plus every day in holiday ramp-up windows |

Facebook posts go to the Glamis Guide Page. The Facebook Group can't be scheduled through any tool.

## Adding a day

The easiest way is the **Glamis Post** Mac app (`tools/build-app.sh` puts it on the Desktop):

1. Pick the date the content should **post** (it defaults to tomorrow).
2. Drop in the video and the screenshot.
3. Fill in the feature and what it does, then publish. It commits and pushes for you.

Or by hand in VS Code: **Run Task → New Day**, add `video.mp4` and `screenshot.png`, fill in `directions.md`, set `status: ready` and save. The Run on Save extension pushes it (`tools/publish.sh`).

### directions.md

```
status: ready
feature: Home Screen Widgets
what it does: Mark camp, create a waypoint, or record a ride
key facts:
angle:
headline:
device:
notes:
```

Only `status` and `feature` are required. Claude uses only facts from this file and the screenshot. `headline:` is used word for word if filled. `device:` (`iphone`, `ipad`, `watch`) overrides the automatic frame.

## Folder layout

```
brand/                 Fixed assets: icon, badge, fonts, photos, device mockups. Don't edit casually.
_template/             directions.md copied into each new day
YYYY-MM-DD/            One per posting day
  video.mp4|.mov       Feature demo (Andy)
  screenshot.png       App screenshot (Andy)
  directions.md        Brief (Andy)
  copy.json            Headlines and captions (Claude)
  out/                 story-download.png, post.png (Claude)
2026-10-11/            Test day and approved reference. Never posted.
tools/                 Scripts (below)
CLAUDE.md              Full rules for the nightly build: copy, layouts, Metricool settings
SETUP.md               One-time setup and the daily checklist
```

## Tools

| File | What it does |
|---|---|
| `tools/render.py <day>` | Renders `out/story-download.png` (1080×1920) and `out/post.png` (1080×1350) from `copy.json` and the screenshot. Needs Pillow. The layouts are fixed here on purpose. |
| `tools/new-day.sh [YYYY-MM-DD]` | Creates a day folder from the template (defaults to tomorrow). |
| `tools/publish.sh <day>/directions.md` | Checks the folder is complete and pushes it when `status: ready`. |
| `tools/GlamisPost/` + `tools/build-app.sh` | The Glamis Post Mac app. |
| `tools/nudge.py` + `tools/install-nudge.sh` | Apple Reminders on Andy's Mac: "create content" at 6:30 PM and "review drafts" at 8:15 PM the evening before each posting day. Also holds the ramp-up windows. |
| `tools/measure_mockups.py` | Finds the screen area in each mockup PNG after a mockup is replaced. |

Preview a day locally:

```bash
python3 -m pip install --user pillow
python3 tools/render.py 2026-10-12
```

## Links and tracking

Every App Store link carries an App Store Connect campaign so downloads can be traced by source:

| Campaign | Used in |
|---|---|
| `ig_story` | Link sticker on both Instagram Stories |
| `ig_bio` | Instagram profile link |
| `glamisguide_fb` | Facebook captions |

The full URLs are in `CLAUDE.md`. Campaign numbers show up in App Store Connect after 24–48 hours and only count people who share analytics with developers.

## Media hosting

The repo is public so Metricool can fetch media from `raw.githubusercontent.com`. Each build uses the commit hash in the URL so Metricool never gets a stale cached copy.
