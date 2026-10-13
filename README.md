# Glamis Social

Daily Instagram ([@glamisguide](https://www.instagram.com/glamisguide)) and Facebook Page content for **Glamis Guide**, a free iOS map app for the Imperial Sand Dunes ([glamisguide.app](https://glamisguide.app)).

Andy records a short feature demo and a screenshot each evening and hands them off with the Glamis Post Mac app. A nightly Claude build writes the copy, renders the graphics, and queues everything in Metricool for the next day.

## How a day works

| When (PT) | Who | What |
|---|---|---|
| By 7:30 PM, the evening before | Andy | Adds `video`, `screenshot.png` and `directions.md` (`status: ready`) to a new day folder and publishes it |
| 7:45 PM | Claude (scheduled task "Glamis nightly build") | Writes `copy.json`, renders `out/`, commits, creates the Metricool items, sends a report |
| After the report | Andy | Checks the items in Metricool and schedules them |
| 9:58 AM | Claude (scheduled task "Glamis sticker reminder") | Phone reminder with the `ig_story` link |
| 10:00 / 10:01 AM | Andy | Posts both Stories by hand in Instagram (files from the build report) with the link sticker |
| 12:00 PM, 5:00 PM | Metricool | Reels and feed posts publish on their own |

## What gets posted

| Time (PT) | Item | Asset | Publishing |
|---|---|---|---|
| 10:00 AM | Instagram Story 1 | Feature video | By hand in Instagram (not in Metricool). Andy adds the link sticker |
| 10:01 AM | Instagram Story 2 | `out/story-download.png` | By hand in Instagram (not in Metricool). Andy adds the link sticker |
| 12:00 PM | Instagram Reel + Facebook Reel | Feature video + captions | Auto |
| 5:00 PM | Instagram feed post + Facebook post | `out/post.png` + captions | Auto. Tue, Thu, Sat, plus every day in holiday ramp-up windows |

Facebook posts go to the Glamis Guide Page. The Facebook Group can't be scheduled through any tool.

## Adding a day

Use the Glamis Post Mac app (below). Or by hand in VS Code: **Run Task → New Day**, add `video.mp4` and `screenshot.png`, fill in `directions.md`, set `status: ready` and save. The Run on Save extension pushes it (`tools/publish.sh`).

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

## Glamis Post (Mac app)

A small Mac app on Andy's Desktop for preparing a posting day in one window. Source: `tools/GlamisPost/main.swift`.

1. **Date:** the day the content will **post**, not today. It opens on tomorrow. The line under the title shows that day's lineup (Video Story · Download Story · Reel, plus Feed post on feed days and in ramp-up windows).
2. **Video** and **Screenshot:** drop or click to choose. The video is copied in as `video.<ext>` (95 MB max, to stay under GitHub's file limit). A JPG screenshot is converted to `screenshot.png`.
3. **Feature**, **What it does**, **Key facts (optional):** written into `directions.md`.
4. **Mark Ready:** creates `YYYY-MM-DD/`, writes `directions.md` with `status: ready`, then commits (`Ready: <day> — <feature>`), pulls and pushes to GitHub. The 7:45 PM build picks it up.

Install or update it (needs Xcode or the Command Line Tools):

```bash
tools/build-app.sh
```

This compiles the app, builds its icon from `brand/app-icon.png`, and puts **Glamis Post.app** on the Desktop. The app remembers this repo's location, so rebuild if the repo folder moves. Run it again after any change to `main.swift`.

The posting schedule (feed days, ramp-up windows) is coded into the app too. Keep it in sync with `CLAUDE.md` and `tools/nudge.py`.

## Raspberry Pi (in setup)

An always-on Raspberry Pi on the home Wi-Fi, being set up as a background automation server. Its Glamis Guide jobs:

- **App Store Connect analytics:** pull Glamis Guide download and campaign data on a schedule and commit it to this repo, so downloads can be read alongside the Instagram and Facebook results.
- **Stats dashboard:** a Glamis Guide App Store stats dashboard on the Pi's touchscreen that launches at startup.

None of the Pi's scripts live in this repo yet. Add their location, schedule and data format here once they're running.

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
| `tools/GlamisPost/` + `tools/build-app.sh` | The Glamis Post Mac app (see above). |
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
