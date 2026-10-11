#!/usr/bin/env bash
# Install the Glamis Social reminders on this Mac (run once).
#   daily  3:00 PM  -> reminder if tomorrow's content is not ready
#   Monday 8:00 AM  -> weekly rundown reminder
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
AGENTS="$HOME/Library/LaunchAgents"
mkdir -p "$AGENTS" "$ROOT/.logs"

write_plist() {
  local label=$1 mode=$2 calendar=$3
  cat > "$AGENTS/$label.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$label</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/python3</string>
    <string>$ROOT/tools/nudge.py</string>
    <string>$mode</string>
  </array>
  <key>StartCalendarInterval</key>
  $calendar
  <key>StandardOutPath</key><string>$ROOT/.logs/$mode.log</string>
  <key>StandardErrorPath</key><string>$ROOT/.logs/$mode.log</string>
</dict>
</plist>
EOF
  launchctl bootout "gui/$(id -u)/$label" 2>/dev/null || true
  launchctl bootstrap "gui/$(id -u)" "$AGENTS/$label.plist"
}

write_plist com.glamisguide.nudge.daily daily \
  "<dict><key>Hour</key><integer>15</integer><key>Minute</key><integer>0</integer></dict>"
write_plist com.glamisguide.nudge.weekly weekly \
  "<dict><key>Weekday</key><integer>1</integer><key>Hour</key><integer>8</integer><key>Minute</key><integer>0</integer></dict>"

echo "Installed. Running a test now — allow Reminders access if macOS asks."
/usr/bin/python3 "$ROOT/tools/nudge.py" weekly
