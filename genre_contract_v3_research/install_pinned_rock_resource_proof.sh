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
  git sparse-checkout set Programs Samples
  git checkout "$RUSTY_COMMIT"
)

# Preserve all publisher-controlled files byte-for-byte. The October 17
# recovery architecture adds only the Composer routing wrapper below.
# Recreate the exact current Composer-facing electric-guitar wrapper recovered
# from /Working File/INTEGRATED_WORKING_COPY on 2026-10-17. The preserved file
# is 109 bytes and has the SHA-256 recorded below. It does not alter the factory
# program or samples; it only supplies the Composer sample-directory context and
# includes the untouched upstream main.sfz.
cat > "$BANK/KARORYFER_SHINYGUITAR/Programs/composer_electric.sfz" <<'EOF'
// Composer wrapper; original SFZ/sample files unchanged.
#define $sample_dir ../Samples
#include "main.sfz"
EOF

actual_wrapper_sha="$(sha256sum "$BANK/KARORYFER_SHINYGUITAR/Programs/composer_electric.sfz" | awk '{print $1}')"
if [ "$actual_wrapper_sha" != "$EXPECTED_SHINY_WRAPPER_SHA256" ]; then
  echo "SHINYGUITAR_WRAPPER_HASH_MISMATCH::$actual_wrapper_sha::$EXPECTED_SHINY_WRAPPER_SHA256" >&2
  exit 1
fi
echo "SHINYGUITAR_WRAPPER_HASH_PASS $actual_wrapper_sha"

# Prove the pinned publisher trees were not edited. The Composer wrapper is
# intentionally untracked and therefore excluded from this tracked-file check.
git -C "$BANK/KARORYFER_SHINYGUITAR" diff --exit-code
git -C "$BANK/KARORYFER_BIG_RUSTY_DRUMS" diff --exit-code

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
    "publisher_files_modified":False,
    "wrapper_policy":"ADD_TINY_COMPOSER_ROUTING_WRAPPER_ONLY__PUBLISHER_FILES_UNCHANGED",
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
