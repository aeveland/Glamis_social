#!/usr/bin/env bash
# Commit and push a day folder when its directions.md says "status: ready".
# Runs automatically on save (Run on Save extension) or by hand:
#   tools/publish.sh 2026-10-12/directions.md
set -euo pipefail
cd "$(dirname "$0")/.."

FILE="${1:?usage: publish.sh <day>/directions.md}"
DAY=$(basename "$(dirname "$FILE")")

notify() {
  echo "$1"
  osascript -e "display notification \"$1\" with title \"Glamis Social\"" 2>/dev/null || true
}

[[ "$DAY" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]] || exit 0

STATUS=$(grep -E '^status:' "$DAY/directions.md" | head -1 | sed 's/^status:[[:space:]]*//; s/[[:space:]]*#.*//' | tr 'A-Z' 'a-z')
[ "$STATUS" = "ready" ] || exit 0

missing=()
ls "$DAY"/video.* >/dev/null 2>&1 || missing+=("video.mp4")
ls "$DAY"/screenshot.* >/dev/null 2>&1 || missing+=("screenshot.png")
FEATURE=$(grep -E '^feature:' "$DAY/directions.md" | head -1 | sed 's/^feature:[[:space:]]*//')
[ -n "$FEATURE" ] || missing+=("feature name")
if [ ${#missing[@]} -gt 0 ]; then
  notify "$DAY not published. Missing: ${missing[*]}"
  exit 1
fi

for v in "$DAY"/video.*; do
  size=$(stat -f%z "$v" 2>/dev/null || stat -c%s "$v")
  if [ "$size" -gt 95000000 ]; then
    notify "$DAY not published. Video is over 95 MB. Export at 1080p."
    exit 1
  fi
done

git add "$DAY"
if git diff --cached --quiet; then
  notify "$DAY already published"
  exit 0
fi
git commit -q -m "Ready: $DAY — $FEATURE"
git pull -q --rebase
git push -q
notify "$DAY published: $FEATURE"
