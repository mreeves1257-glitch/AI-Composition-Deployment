#!/usr/bin/env bash
set -euo pipefail

# Diagnostic-only acquisition of the exact pinned Big Rusty Drums resource
# required by Programs/01-full.sfz. Publisher-controlled files are never edited.

ROOT="${1:-current_master_forward}"
BANK="$ROOT/sound_resources"
DEST="$BANK/KARORYFER_BIG_RUSTY_DRUMS"
RUSTY_COMMIT="f07ce00df34a46b6b08375be56fe116cf15782bc"

mkdir -p "$BANK"
rm -rf "$DEST"

git clone --filter=blob:none --no-checkout \
  https://github.com/sfzinstruments/karoryfer.big-rusty-drums.git \
  "$DEST"

(
  cd "$DEST"
  git sparse-checkout init --cone
  git sparse-checkout set Programs Samples
  git checkout "$RUSTY_COMMIT"
  test "$(git rev-parse HEAD)" = "$RUSTY_COMMIT"
  git diff --exit-code
)

test -f "$DEST/Programs/01-full.sfz"
test -f "$DEST/Programs/keymap/keymap.sfz"

for d in \
  kick_24 kick_24_nodamp snare_14 hihat_14 \
  tom_14 tom_15 tom_18 tom_22 \
  crash_17 crash_sizzle_17 ride_22 ride_sizzle_19 \
  china_18 stack_3_layer
do
  test -d "$DEST/Samples/$d"
done

python - "$ROOT" "$RUSTY_COMMIT" <<'PY'
from pathlib import Path
import json
import sys

root=Path(sys.argv[1])
commit=sys.argv[2]
bank=root/"sound_resources"/"KARORYFER_BIG_RUSTY_DRUMS"
sample_families=sorted(
    p.name for p in (bank/"Samples").iterdir() if p.is_dir()
)
report={
    "schema":"PINNED_BIG_RUSTY_COMPLETE_ACQUISITION_001",
    "status":"PASS",
    "diagnostic_only":True,
    "resource_id":"KARORYFER_BIG_RUSTY_DRUMS",
    "pinned_commit":commit,
    "mapping":"Programs/01-full.sfz",
    "publisher_files_modified":False,
    "sample_families_present":sample_families,
    "required_full_mapping_sample_families":[
        "kick_24","kick_24_nodamp","snare_14","hihat_14",
        "tom_14","tom_15","tom_18","tom_22",
        "crash_17","crash_sizzle_17","ride_22","ride_sizzle_19",
        "china_18","stack_3_layer",
    ],
    "audio_rendered":False,
    "live_runtime_promoted":False,
}
out=root/"BIG_RUSTY_COMPLETE_ACQUISITION.json"
out.write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps(report,indent=2))
PY
