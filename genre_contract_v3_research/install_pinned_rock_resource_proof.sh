#!/usr/bin/env bash
set -euo pipefail

# Research/diagnostic resource acquisition only.
# Reconstructs the real Rock sample-bank mappings expected by target_registry.json.
# No audio rendering, no live deployment, no synthetic substitution.

ROOT="${1:-composer/runtime}"
BANK="$ROOT/sound_resources"
mkdir -p "$BANK"

SHINY_COMMIT="57243cca85277dbcc120ce17c6178032f93c80f3"
RUSTY_COMMIT="f07ce00df34a46b6b08375be56fe116cf15782bc"
EXPECTED_SHINY_WRAPPER_SHA256="da026ba66ab34a4ebb99c6cda93a24d4bc48e57e252a26db5c1fd6916cbaed35"

rm -rf "$BANK/KARORYFER_SHINYGUITAR" "$BANK/KARORYFER_BIG_RUSTY_DRUMS"

git clone --filter=blob:none --no-checkout \
  https://github.com/sfzinstruments/karoryfer.shinyguitar.git \
  "$BANK/KARORYFER_SHINYGUITAR"
(
  cd "$BANK/KARORYFER_SHINYGUITAR"
  git sparse-checkout init --cone
  git sparse-checkout set Programs Samples
  git checkout "$SHINY_COMMIT"
)

git clone --filter=blob:none --no-checkout \
  https://github.com/sfzinstruments/karoryfer.big-rusty-drums.git \
  "$BANK/KARORYFER_BIG_RUSTY_DRUMS"
(
  cd "$BANK/KARORYFER_BIG_RUSTY_DRUMS"
  git sparse-checkout init --cone
  git sparse-checkout set \
    Programs \
    Samples/kick_24 \
    Samples/snare_14 \
    Samples/hihat_14 \
    Samples/tom_14 \
    Samples/tom_15 \
    Samples/tom_18 \
    Samples/tom_22 \
    Samples/crash_17 \
    Samples/ride_22 \
    Samples/china_18 \
    Samples/stack_3_layer
  git checkout "$RUSTY_COMMIT"
)

# Normalize SFZ path separators the same way the historical Composer build did.
find "$BANK/KARORYFER_SHINYGUITAR" "$BANK/KARORYFER_BIG_RUSTY_DRUMS" \
  -type f -name "*.sfz" -print0 | xargs -0 sed -i 's#\\#/#g'

# Recreate the current Composer-facing electric-guitar wrapper from the pinned
# upstream Shinyguitar program. This is a path/control wrapper around the real
# recorded library, not a synthesized replacement.
python - "$BANK/KARORYFER_SHINYGUITAR/Programs" "$EXPECTED_SHINY_WRAPPER_SHA256" <<'PY'
from pathlib import Path
import hashlib
import sys

root=Path(sys.argv[1])
expected=sys.argv[2]
src=(root/"main.sfz").read_text(encoding="utf-8")
src=src.replace("default_path=$sample_dir/", "default_path=../Samples/")
src="\n".join(
    line for line in src.splitlines()
    if '#include "acoustic_' not in line
)
if "set_cc106=0" in src:
    src=src.replace("set_cc106=0", "set_cc106=32")
out=root/"composer_electric.sfz"
out.write_text(src+"\n",encoding="utf-8")
digest=hashlib.sha256(out.read_bytes()).hexdigest()
if digest!=expected:
    raise SystemExit(
        f"SHINYGUITAR_WRAPPER_HASH_MISMATCH::{digest}::{expected}"
    )
print("SHINYGUITAR_WRAPPER_HASH_PASS",digest)
PY

# Historical Shinyguitar programs expect an electric directory reachable from
# Programs; preserve that real-sample link without copying or modifying samples.
ln -sfn \
  "$BANK/KARORYFER_SHINYGUITAR/Samples/electric" \
  "$BANK/KARORYFER_SHINYGUITAR/Programs/electric"

test -f "$BANK/KARORYFER_SHINYGUITAR/Programs/composer_electric.sfz"
test -f "$BANK/KARORYFER_BIG_RUSTY_DRUMS/Programs/01-full.sfz"

python - "$ROOT" "$SHINY_COMMIT" "$RUSTY_COMMIT" <<'PY'
from pathlib import Path
import json
import sys

root=Path(sys.argv[1])
report={
    "status":"PASS",
    "diagnostic_only":True,
    "audio_rendered":False,
    "live_runtime_promoted":False,
    "resources":{
        "KARORYFER_SHINYGUITAR":{
            "pinned_commit":sys.argv[2],
            "mapping":"sound_resources/KARORYFER_SHINYGUITAR/Programs/composer_electric.sfz",
        },
        "KARORYFER_BIG_RUSTY_DRUMS":{
            "pinned_commit":sys.argv[3],
            "mapping":"sound_resources/KARORYFER_BIG_RUSTY_DRUMS/Programs/01-full.sfz",
        },
    },
}
out=root/"ROCK_PINNED_RESOURCE_ACQUISITION.json"
out.write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps(report,indent=2))
PY
