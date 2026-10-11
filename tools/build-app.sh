#!/usr/bin/env bash
# Build "Glamis Post.app" and put it on the Desktop. Run once (and again after updates).
# Needs Xcode or the Xcode Command Line Tools.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP="$HOME/Desktop/Glamis Post.app"
WORK="$(mktemp -d)"

rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"

echo "Compiling…"
swiftc -O -parse-as-library \
  -o "$APP/Contents/MacOS/GlamisPost" \
  "$ROOT/tools/GlamisPost/main.swift"

echo "Making icon…"
ICONSET="$WORK/AppIcon.iconset"
mkdir -p "$ICONSET"
for s in 16 32 64 128 256 512; do
  sips -z $s $s "$ROOT/brand/app-icon.png" --out "$ICONSET/icon_${s}x${s}.png" >/dev/null
  d=$((s * 2))
  sips -z $d $d "$ROOT/brand/app-icon.png" --out "$ICONSET/icon_${s}x${s}@2x.png" >/dev/null
done
iconutil -c icns "$ICONSET" -o "$APP/Contents/Resources/AppIcon.icns"

cat > "$APP/Contents/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleName</key><string>Glamis Post</string>
  <key>CFBundleDisplayName</key><string>Glamis Post</string>
  <key>CFBundleIdentifier</key><string>com.glamisguide.post</string>
  <key>CFBundleExecutable</key><string>GlamisPost</string>
  <key>CFBundleIconFile</key><string>AppIcon</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleShortVersionString</key><string>1.0</string>
  <key>LSMinimumSystemVersion</key><string>13.0</string>
  <key>NSHighResolutionCapable</key><true/>
  <key>GlamisRepoPath</key><string>$ROOT</string>
</dict>
</plist>
EOF

codesign --force --deep -s - "$APP" >/dev/null 2>&1 || true
rm -rf "$WORK"
echo "Done: $APP"
