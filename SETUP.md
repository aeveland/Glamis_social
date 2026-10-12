# One-time setup

Run these in the VS Code terminal from the Glamis_social folder.

## 1. Connect the folder to your GitHub repo

The folder is already a git repo with no remote and no commits yet.

```bash
rm -f .probe _scaffold.zip
git remote add origin https://github.com/<you>/<repo>.git
git add .
git commit -m "Scaffold daily social workflow"
git push -u origin main
```

If the GitHub repo already has a commit (a README, say), run `git pull --rebase origin main` before the push.

## 2. Install the Run on Save extension

VS Code shows a "recommended extension" prompt. Install **Run on Save** (emeraldwalk). After that, saving a `YYYY-MM-DD/directions.md` with `status: ready` publishes the folder.

## 3. Preview tooling (optional)

`python3 -m pip install --user pillow` lets you run the **Render Day** task for a local preview.

# Every day

1. **Cmd+Shift+P → Run Task → New Day.** Leave it blank for tomorrow.
2. Drop `video.mp4` (1080p) and `screenshot.png` into the new folder.
3. Fill in `directions.md`, set `status: ready`, and save. It pushes automatically, and you get a Mac notification.
4. That evening, approve the drafts in Metricool.
5. At 10:01 AM, tap the Metricool notification, add the `ig_story` link sticker (link is in the post text and the 9:58 reminder), and post. Don't share Story 2 without the sticker.
