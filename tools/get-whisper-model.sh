#!/usr/bin/env bash
# Fetch the Whisper "small" speech-to-text model (CTranslate2 int8) for render_reel.py.
# Hugging Face is blocked in the cloud build environment, so this pulls the same
# MIT-licensed model from npm (split into 4 parts) and checks its sha256.
#
# Usage:  tools/get-whisper-model.sh [dest]      (default: ~/.cache/glamis-whisper)
# Then:   export WHISPER_MODEL=<dest>
set -euo pipefail
DEST="${1:-$HOME/.cache/glamis-whisper}"
if [ -f "$DEST/model.bin" ]; then echo "$DEST"; exit 0; fi
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$DEST"
for i in 0 1 2 3; do
  (cd "$TMP" && npm pack -s "@skillninja/shortmovie-telop-model-p$i@1.0.0" >/dev/null)
  mkdir -p "$TMP/p$i" && tar -xzf "$TMP"/skillninja-shortmovie-telop-model-p$i-1.0.0.tgz -C "$TMP/p$i"
done
cat "$TMP"/p0/package/model.bin.part0 "$TMP"/p1/package/model.bin.part1 \
    "$TMP"/p2/package/model.bin.part2 "$TMP"/p3/package/model.bin.part3 > "$DEST/model.bin"
cp "$TMP"/p0/package/{config.json,preprocessor_config.json,tokenizer.json,vocabulary.json} "$DEST/"
EXPECT="ca732cb1379efc49417d028465f543d83a39de2c61f3027678de103dc404ce73"
GOT="$(sha256sum "$DEST/model.bin" | cut -d' ' -f1)"
if [ "$GOT" != "$EXPECT" ]; then rm -rf "$DEST"; echo "Model checksum mismatch" >&2; exit 1; fi
echo "$DEST"
