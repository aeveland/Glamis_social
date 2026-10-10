#!/usr/bin/env bash
# Create a dated day folder from the template.
# Usage: tools/new-day.sh [YYYY-MM-DD]   (default: tomorrow)
set -euo pipefail
cd "$(dirname "$0")/.."

DAY="${1:-}"
if [ -z "$DAY" ]; then
  DAY=$(date -v+1d +%F 2>/dev/null || date -d tomorrow +%F)
fi
if ! [[ "$DAY" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
  echo "Date must be YYYY-MM-DD"; exit 1
fi
if [ -d "$DAY" ]; then
  echo "$DAY already exists"
else
  mkdir -p "$DAY"
  cp _template/directions.md "$DAY/directions.md"
  echo "Created $DAY/ — add video.mp4 and screenshot.png, then fill in directions.md"
fi
command -v code >/dev/null && code "$DAY/directions.md" || true
