# Glamis Social

Daily Instagram content for **Glamis Guide** (@glamisguide), a free iOS map app for the Imperial Sand Dunes. Site: glamisguide.app. Owner: Andy.

## Daily deliverables

Posting started Mon 2026-10-12.

| Time (PT) | Type | Asset | Publishing | Days |
|---|---|---|---|---|
| 10:00 AM | Story 1 | `<day>/video.*`, the feature demo (hand + voiceover) | Auto-publish | Every day |
| 10:01 AM | Story 2 | `<day>/out/story-download.png` | Phone notification. Andy adds the link sticker by hand | Every day |
| 12:00 PM | Reel | Same `<day>/video.*` + `reel_caption` | Auto-publish | Every day |
| 5:00 PM | Feed post | `<day>/out/post.png` + `caption` | Auto-publish | **Tue, Thu, Sat only**, plus every day in a ramp-up window |

Ramp-up windows (feed post daily): Halloween Oct 24–Nov 1 2026, Thanksgiving Nov 19–29 2026, New Year's Dec 26 2026–Jan 3 2027, Presidents' Day Feb 6–15 2027. The same list is in `tools/nudge.py`. Keep both in sync.

Everything goes into Metricool **as drafts for review** (`createScheduledPostForReview`). Andy approves each evening. Never publish directly.

## Folder layout

- `brand/`: fixed assets. Do not edit without Andy.
- `_template/directions.md`: copied into each new day.
- `YYYY-MM-DD/`: one per posting day. Holds `video.mp4`, `screenshot.png`, `directions.md` (Andy), plus `copy.json` and `out/` (Claude).
- `_example/`: reference render only. Never schedule it.
- `tools/render.py`: the only way graphics get made. Layouts live in code so the series stays consistent.

## Building a day

A day is buildable when `directions.md` has `status: ready` and the folder holds a video and a screenshot.

1. Read `directions.md`. Look at `screenshot.png` and a frame of the video to confirm the feature.
2. Write `<day>/copy.json`:
   ```json
   {
     "story_headline": "Know every hill by name.",
     "post_headline": "Every landmark, one tap away.",
     "post_subline": "Elevation, coordinates, directions. Oldsmobile Hill to Glamis Flats.",
     "caption": "…  (feed post, only used on feed days)",
     "reel_caption": "…  (every day)"
   }
   ```
3. Run `python3 tools/render.py <day>`. Open both PNGs and check them: no overflow, headline at most 3 lines, the screenshot reads clearly.
4. Commit `copy.json` + `out/` with the message `Build: <day> — <feature>`, then push.
5. Create that day's Metricool items (see below): 3 on normal days, 4 on feed days. Report back with the images and the copy.

If `headline:` is filled in `directions.md`, use it verbatim as `story_headline`. Use `post_headline` only if it fits that pattern.

## Copy rules

- **Headlines:** 3–6 words. Sentence case. End with a period. Benefit first, about the rider and not the app. Examples: "Never lose camp again." / "The dunes, in your pocket." / "Know every hill by name."
- **Post subline:** two short sentences. Plain facts that explain the headline. Example: "NAIP imagery stored on your phone. Zero bars required."
- **Reel caption:** 1–2 short lines plus "Free on the App Store. Link in bio." and up to 5 hashtags. Different wording from the feed caption.
- **Caption:** 2–4 short lines. Say what it does, why it matters out there, then "Free on the App Store. Link in bio." Up to 5 hashtags from: #glamis #glamisdunes #imperialsanddunes #duning #sxs #utv #offroad #sanddunes.
- Use only facts from `directions.md` or the screenshot. Never invent numbers, landmark counts, or features. If a fact is missing, write around it.
- Speak to dune riders: camp, the flats, Oldsmobile, Competition Hill, holiday weekends. No travel-brochure tone.

## Device frame

`render.py` picks the device from the screenshot dimensions. A `device:` line in `directions.md` overrides it.
- Narrow portrait (width/height < 0.6) → `iphone` (hand holding iPhone)
- Small and near-square (under 1000 px, ratio 0.7–1.0) → `watch` (watch on wrist)
- Anything else → `ipad` (two hands, landscape). iPad screenshots should be taken in landscape.

## Approved layouts

- Download Story: approved 2026-10-10 (`2026-10-11/out/story-download.png` is the reference). Icon and app name grouped tight, the whole stack pinned to the bottom with 200 px of padding. Do not change the layout in `render.py` without Andy's sign-off.

## Instagram specs

- Story: 1080×1920. Keep text out of the top 250 px and bottom 250 px.
- Feed post: 1080×1350 (4:5).

## Metricool

- Brand: Glamis Guide, `blogId` **7334820**, Instagram `glamisguide`, timezone America/Los_Angeles.
- Create each piece with `createScheduledPostForReview` (reviewers: `aeveland@me.com`, approvalSystem `any`). If that tool errors because the plan has no team review, fall back to `createScheduledPost` with `"draft": true`, and tell Andy the drafts need scheduling in Metricool.
- Story 1: `instagramData.type: "STORY"`, media = video URL, 10:00, `autoPublish: true`, no text.
- Story 2: `instagramData.type: "STORY"`, media = story-download.png URL, 10:00 (or 10:01 so it follows Story 1), `autoPublish: false`, which sends a phone notification so Andy can add the link sticker. Put the `ig_story` campaign link in the build report so Andy can copy it.
- Reel: `instagramData.type: "REEL"`, `showReelOnFeed: true`, media = video URL, `reel_caption` as `text`, 12:00, `autoPublish: true`.
- Post (feed days only): `instagramData.type: "POST"`, media = post.png URL, `caption` as `text`, 17:00, `autoPublish: true`.
- Media URLs: use the commit hash instead of `main` (`.../Glamis_social/<sha>/<day>/...`) so Metricool never gets a stale cached copy.
- Always include `"instagramData"` and `"providers":[{"network":"instagram"}]`.

## Campaign links (App Store Connect)

- `ig_story`: https://apps.apple.com/app/apple-store/id6797360883?pt=118293478&ct=ig_story&mt=8
- `ig_bio`: https://apps.apple.com/app/apple-store/id6797360883?pt=118293478&ct=ig_bio&mt=8 (the Instagram profile link)

## Media hosting

The repo is public. Use raw GitHub URLs, built only after the files are pushed:

`https://raw.githubusercontent.com/aeveland/Glamis_social/main/<day>/<file>`

Example: `https://raw.githubusercontent.com/aeveland/Glamis_social/main/2026-10-12/out/post.png`
