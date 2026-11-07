#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-current_master_forward}"
BANK="$ROOT/sound_resources"
DEST="$BANK/KARORYFER_GROWLYBASS_V1_002"
URL="https://github.com/sfzinstruments/karoryfer.growlybass/releases/download/v1.002/Karoryfer.Growlybass.v1.002.zip"
EXPECTED_SIZE="167454256"
EXPECTED_SHA256="b92dca75494fa39d6e8d8b8addaabfe70c5aaa59b5f9a0f624be6de51a2374bc"
TMP_ZIP="/tmp/Karoryfer.Growlybass.v1.002.zip"
TMP_DIR="/tmp/growlybass-v1002-unpack"

rm -rf "$TMP_ZIP" "$TMP_DIR" "$DEST"
mkdir -p "$TMP_DIR" "$DEST"

curl -L --fail --retry 3 --retry-delay 2 -o "$TMP_ZIP" "$URL"

size="$(stat -c '%s' "$TMP_ZIP")"
if [ "$size" != "$EXPECTED_SIZE" ]; then
  echo "GROWLYBASS_SIZE_MISMATCH::$size::$EXPECTED_SIZE" >&2
  exit 1
fi

sha="$(sha256sum "$TMP_ZIP" | awk '{print $1}')"
if [ "$sha" != "$EXPECTED_SHA256" ]; then
  echo "GROWLYBASS_SHA256_MISMATCH::$sha::$EXPECTED_SHA256" >&2
  exit 1
fi

unzip -q "$TMP_ZIP" -d "$TMP_DIR"
mapping="$(find "$TMP_DIR" -type f -name growlybass_vicious.sfz | head -n 1)"
test -n "$mapping"
src_root="$(dirname "$mapping")"
cp -a "$src_root"/. "$DEST"/

test -f "$DEST/growlybass_vicious.sfz"
test -f "$DEST/growlybass_clean.sfz"
test -f "$DEST/growlybass_angry.sfz"

echo "GROWLYBASS_V1002_PIN_PASS $sha $size"
