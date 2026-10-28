# Glamis Social

Daily Instagram (@glamisguide) and Facebook Page content for **Glamis Guide**, a free iOS map app for the Imperial Sand Dunes. Site: glamisguide.app. Owner: Andy.

## Daily deliverables

Posting started Mon 2026-10-12.

Evening before each posting day: Andy has the video, screenshot and `directions.md` (status: ready) in by **7:30 PM PT**. The nightly build runs at **7:45 PM PT** ("Glamis nightly build" scheduled task). Reminders: create content 6:30 PM, review drafts 8:15 PM (`tools/nudge.py`).

| Time (PT) | Type | Asset | Publishing | Days |
|---|---|---|---|---|
| 10:00 AM | Story 1 | `<day>/out/reel.mp4` (title card + captioned feature demo + end card) | **Not in Metricool.** Andy posts it by hand in Instagram with the `ig_story` link sticker (9:58 reminder) | Every day |
| 10:01 AM | Story 2 | `<day>/out/story-download.png` | **Not in Metricool.** Andy posts it by hand in Instagram with the `ig_story` link sticker (9:58 reminder) | Every day |
| 12:00 PM | Reel | Same `<day>/out/reel.mp4` + `reel_caption` | Auto-publish | Every day |
| 5:00 PM | Feed post | `<day>/out/post.png` + `caption` | Auto-publish | **Tue, Thu, Sat only**, plus every day in a ramp-up window |
| 12:00 PM | Facebook Reel | Same `<day>/out/reel.mp4` + `fb_reel_caption` | Auto-publish | Every day |
| 5:00 PM | Facebook post | `<day>/out/post.png` + `fb_caption` | Auto-publish | Same days as the Instagram feed post |
| 12:00 PM | TikTok | Same `<day>/out/reel.mp4` + `tt_caption` | Auto-publish | Every day, once TikTok is connected in Metricool |

Facebook goes to the Glamis Guide **Page**. Facebook Groups cannot be scheduled by any tool (Meta removed Groups API access), so never try to post to the group.

Ramp-up windows (feed post daily): Halloween Oct 24–Nov 1 2026, Thanksgiving Nov 19–29 2026, New Year's Dec 26 2026–Jan 3 2027, Presidents' Day Feb 6–15 2027. The same list is in `tools/nudge.py`. Keep both in sync.

Everything goes into Metricool **as drafts for review** (`createScheduledPostForReview`). Andy approves each evening. Never publish directly.

## Folder layout

- `brand/`: fixed assets. Do not edit without Andy.
- `_template/directions.md`: copied into each new day.
- `YYYY-MM-DD/`: one per posting day. Holds `video.mp4`, `screenshot.png`, `directions.md` (Andy), plus `copy.json` and `out/` (Claude).
- `2026-10-11/`: test day and the approved reference (never posted). Never schedule it.
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
     "reel_caption": "…  (every day)",
     "fb_reel_caption": "…  (every day, Facebook Reel)",
     "fb_caption": "…  (feed days only, Facebook post)",
     "tt_caption": "…  (every day, TikTok)"
   }
   ```
3. Run `python3 tools/render.py <day>`. Open both PNGs and check them: no overflow, headline at most 3 lines, the screenshot reads clearly.
4. Build the video: `pip install --break-system-packages faster-whisper pillow`, `export WHISPER_MODEL=$(tools/get-whisper-model.sh)`, then `python3 tools/render_reel.py <day>`. First run writes `<day>/captions.json` (word timings from the voiceover). Read it and fix only clearly misheard words (app name "Glamis Guide", feature names, landmark names from `directions.md`) by editing the `"w"` values, then delete `out/reel.mp4` and re-run so captions match. Check `out/reel-title.png`, `out/reel-end.png` and a few frames of `out/reel.mp4` (captions readable, not covering the demo's key tap).
5. Commit `copy.json`, `captions.json` + `out/` with the message `Build: <day> — <feature>`, then push.
6. Create that day's Metricool items (see below): Instagram Reel + Facebook Reel every day, plus Instagram post + Facebook post on feed days, plus a TikTok video every day if `getBrandSettings` shows TikTok in `networksData` (if not, skip TikTok and say so in the report). Stories are never created in Metricool.
7. Report back with the copy and send Andy the two Story files (`out/reel.mp4` and `out/story-download.png`) with SendUserFile, plus `out/post.png` on feed days.

If `headline:` is filled in `directions.md`, use it verbatim as `story_headline`. Use `post_headline` only if it fits that pattern.

## Copy rules

- **Headlines:** 3–6 words. Sentence case. End with a period. Benefit first, about the rider and not the app. Examples: "Never lose camp again." / "The dunes, in your pocket." / "Know every hill by name."
- **Post subline:** two short sentences. Plain facts that explain the headline. Example: "NAIP imagery stored on your phone. Zero bars required."
- **Reel caption:** 1–2 short lines plus "Free on the App Store. Link in bio." and up to 5 hashtags. Different wording from the feed caption.
- **Caption:** 2–4 short lines. Say what it does, why it matters out there, then "Free on the App Store. Link in bio." Up to 5 hashtags from: #glamis #glamisdunes #imperialsanddunes #duning #sxs #utv #offroad #sanddunes.
- **Facebook captions** (`fb_reel_caption`, `fb_caption`): start from the matching Instagram caption (`reel_caption`, `caption`). Replace "Free on the App Store. Link in bio." with "Free on the App Store: https://apps.apple.com/app/apple-store/id6797360883?pt=118293478&ct=glamisguide_fb&mt=8". Facebook links are clickable, so the link goes in the caption. Keep at most 3 hashtags.
- **TikTok caption** (`tt_caption`): start from `reel_caption` and keep "Free on the App Store. Link in bio." (the TikTok bio link is the `glamisguide_tt` campaign link). Captions are not clickable on TikTok, so never paste a URL. 3–5 hashtags from the same list.
- Use only facts from `directions.md` or the screenshot. Never invent numbers, landmark counts, or features. If a fact is missing, write around it.
- Speak to dune riders: camp, the flats, Oldsmobile, Competition Hill, holiday weekends. No travel-brochure tone.

## Device frame

`render.py` picks the device from the screenshot dimensions. A `device:` line in `directions.md` overrides it.
- Narrow portrait (width/height < 0.6) → `iphone` (hand holding iPhone)
- Small and near-square (under 1000 px, ratio 0.7–1.0) → `watch` (watch on wrist)
- Anything else → `ipad` (two hands, landscape). iPad screenshots should be taken in landscape.

## Approved layouts

- Story/Reel video: approved 2026-10-28 (`2026-10-28/out/reel.mp4` is the reference). `tools/render_reel.py` wraps Andy's raw `video.*`: 2.4 s title card (dune photo, icon + "Glamis Guide" lockup, orange rule, the `feature:` from `directions.md` large, `story_headline` under it), the demo scaled to 1080×1920 with spoken captions (2–4 words in a dark rounded pill at y≈1400, current word in icon orange), then a 4 s end card ("Works offline. Always free." / "No signal. No account. No ads." / App Store badge / glamisguide.app), 0.4 s fades between. Never post the raw `video.*`. Do not change the layout without Andy's sign-off.

- Download Story: approved 2026-10-10 (`2026-10-11/out/story-download.png` is the reference). Icon and app name grouped tight, the whole stack pinned to the bottom with 200 px of padding. Do not change the layout in `render.py` without Andy's sign-off.

## Instagram specs

- Story: 1080×1920. Keep text out of the top 250 px and bottom 250 px.
- Feed post: 1080×1350 (4:5).

## Metricool

- Brand: Glamis Guide, `blogId` **7334820**, Instagram `glamisguide`, timezone America/Los_Angeles.
- Create each piece with `createScheduledPostForReview` (reviewers: `aeveland@me.com`, approvalSystem `any`). If that tool errors because the plan has no team review, fall back to `createScheduledPost` with `"draft": true`, and tell Andy the drafts need scheduling in Metricool.
- **Stories are not created in Metricool** (changed 2026-10-13). The Instagram API cannot add link stickers, and Metricool's notification flow didn't reliably hand off to Instagram, so Andy posts both Stories directly in the Instagram app. Never create Story items in Metricool.
- **The link sticker is required on both Stories.** A daily "Glamis sticker reminder" scheduled task pings Andy at 9:58 AM with the link and steps. Every build report sends both Story files (`out/reel.mp4` and `story-download.png`) with SendUserFile, gives their commit-hash raw URLs so Andy can save them on his phone, and lists the Story step first:
  1. Save `reel.mp4` and `story-download.png` to Photos (from the file cards or the raw links).
  2. In Instagram as @glamisguide: **+** → **Story** → pick the video. Sticker icon → **Link** → paste the `ig_story` link → Customize sticker text: **Get Glamis Guide**.
  3. Place it in the lower third, clear of the phone screen, and share. Repeat for the image at 10:01, sticker over the App Store badge.
- Reel: `instagramData.type: "REEL"`, `showReelOnFeed: true`, media = `out/reel.mp4` URL, `reel_caption` as `text`, 12:00, `autoPublish: true`.
- Post (feed days only): `instagramData.type: "POST"`, media = post.png URL, `caption` as `text`, 17:00, `autoPublish: true`.
- Media URLs: use the commit hash instead of `main` (`.../Glamis_social/<sha>/<day>/...`) so Metricool never gets a stale cached copy.
- Always include `"instagramData"` and `"providers":[{"network":"instagram"}]` on Instagram items.
- Facebook Page is connected to the same brand (Page id 1449931404851665). Create Facebook items as **separate** posts, never combined with Instagram, because the captions differ. Use `"providers":[{"network":"facebook"}]` and include `"facebookData"`.
- Facebook Reel: `facebookData.type: "REEL"`, media = `out/reel.mp4` URL, `fb_reel_caption` as `text`, 12:00, `autoPublish: true`.
- Facebook post (feed days only): `facebookData.type: "POST"`, media = post.png URL, `fb_caption` as `text`, 17:00, `autoPublish: true`.

## TikTok

- Account `glamisguide`, connected to the same Metricool brand (blogId 7334820). Check `getBrandSettings` → `networksData` before creating TikTok items.
- TikTok video: `"providers":[{"network":"tiktok"}]`, media = `out/reel.mp4` commit-hash URL, `tt_caption` as `text`, 12:00, `autoPublish: true`, `"tiktokData": {"privacyOption": "PUBLIC_TO_EVERYONE", "disableComment": false, "disableDuet": false, "disableStitch": false, "commercialContentOwnBrand": true, "autoAddMusic": false, "isAigc": false}`. `commercialContentOwnBrand` is true because the videos promote Andy's own app.
- Create TikTok as its own post, never combined with Instagram or Facebook.

## Campaign links (App Store Connect)

- `ig_story`: https://apps.apple.com/app/apple-store/id6797360883?pt=118293478&ct=ig_story&mt=8
- `glamisguide_fb`: https://apps.apple.com/app/apple-store/id6797360883?pt=118293478&ct=glamisguide_fb&mt=8 (Facebook captions)
- `glamisguide_tt`: https://apps.apple.com/app/apple-store/id6797360883?pt=118293478&ct=glamisguide_tt&mt=8 (the TikTok profile/bio link; never in captions)
- `ig_bio`: https://apps.apple.com/app/apple-store/id6797360883?pt=118293478&ct=ig_bio&mt=8 (the Instagram profile link)

## Media hosting

The repo is public. Use raw GitHub URLs, built only after the files are pushed:

`https://raw.githubusercontent.com/aeveland/Glamis_social/main/<day>/<file>`

Example: `https://raw.githubusercontent.com/aeveland/Glamis_social/main/2026-10-12/out/post.png`
