#!/usr/bin/env bash
set -euo pipefail
rm -rf composer/runtime
mkdir -p composer/runtime
base64 -d composer/runtime.b64 | tar -xzf - -C composer/runtime
TOOLS_DIR="$PWD/.composer_tools"
mkdir -p "$TOOLS_DIR/bin"
python -m pip install numpy
if ! command -v sfizz_render >/dev/null 2>&1 && [ ! -x "$TOOLS_DIR/bin/sfizz_render" ]; then
  rm -rf "$TOOLS_DIR/sfizz-src" "$TOOLS_DIR/sfizz-build"
  mkdir -p "$TOOLS_DIR/sfizz-src"
  curl -fsSL "https://github.com/sfztools/sfizz/releases/download/1.2.3/sfizz-1.2.3.tar.gz" -o "$TOOLS_DIR/sfizz.tar.gz"
  tar -xzf "$TOOLS_DIR/sfizz.tar.gz" -C "$TOOLS_DIR/sfizz-src" --strip-components=1
  cmake -S "$TOOLS_DIR/sfizz-src" -B "$TOOLS_DIR/sfizz-build" -DCMAKE_BUILD_TYPE=Release -DSFIZZ_JACK=OFF -DSFIZZ_SHARED=OFF -DPLUGIN_LV2=OFF -DPLUGIN_LV2_UI=OFF -DPLUGIN_VST3=OFF -DSFIZZ_RENDER=ON
  cmake --build "$TOOLS_DIR/sfizz-build" --target sfizz_render -j2
  SFIZZ_BIN="$(find "$TOOLS_DIR/sfizz-build" -type f -name sfizz_render -perm -111 | head -1)"
  test -n "$SFIZZ_BIN"; cp "$SFIZZ_BIN" "$TOOLS_DIR/bin/sfizz_render"
fi
BANK="$PWD/composer/runtime/sound_resources"; mkdir -p "$BANK"
install_library () {
  local rid="$1" repo="$2" branch="$3"; local dest="$BANK/$rid"
  rm -rf "$dest"; git clone --depth 1 --branch "$branch" "$repo" "$dest"
  if command -v git-lfs >/dev/null 2>&1; then (cd "$dest" && git lfs pull); fi
}
install_library "KARORYFER_GROWLYBASS_V1_002" "https://github.com/sfzinstruments/karoryfer.growlybass.git" "master"
install_library "KARORYFER_SHINYGUITAR" "https://github.com/sfzinstruments/karoryfer.shinyguitar.git" "master"
install_library "KARORYFER_BIG_RUSTY_DRUMS" "https://github.com/sfzinstruments/karoryfer.big-rusty-drums.git" "main"
find "$BANK/KARORYFER_SHINYGUITAR" "$BANK/KARORYFER_BIG_RUSTY_DRUMS" -type f -name "*.sfz" -print0 | xargs -0 sed -i 's#\\#/#g'
ln -sfn "$BANK/KARORYFER_SHINYGUITAR/Samples/electric" "$BANK/KARORYFER_SHINYGUITAR/Programs/electric"
ln -sfn "$BANK/KARORYFER_BIG_RUSTY_DRUMS/Samples" "$BANK/KARORYFER_BIG_RUSTY_DRUMS/Programs/mappings/Samples"
ln -sfn "$BANK/KARORYFER_BIG_RUSTY_DRUMS/Programs/mappings" "$BANK/KARORYFER_BIG_RUSTY_DRUMS/Programs/mappings/mappings"
cp composer_overrides/sfz_renderer_adapter.py composer/runtime/sfz_renderer_adapter.py
cp composer_overrides/AI_Comp_3D_Spatialization_Scene_Engine_009_RESTORED_2026-10-03.py composer/runtime/
cp composer_overrides/AI_Comp_Object_Based_3D_Master_006_RESTORED_2026-10-03.py composer/runtime/
cp composer_overrides/global_3d_output_gate.py composer/runtime/
cp composer_overrides/spatial_master_handoff.py composer/runtime/
cp composer_overrides/render_server.py composer/runtime/
python - <<'PY'
import json
from pathlib import Path
path=Path("composer/runtime/target_registry.json"); registry=json.loads(path.read_text())
bindings=registry["targets"]["INTERNAL"].setdefault("instrument_bindings",{})
bindings["electric_guitar:RHYTHM_POWER_CHORDS"]={"resource_id":"KARORYFER_SHINYGUITAR","target_gain_db":-5.0,"resource_type":"SFZ_SAMPLE_LIBRARY","preferred_mapping":"Programs/electric_one.sfz","library":"Karoryfer Shinyguitar","license":"CC0-1.0","renderer_requirement":"SFZ_COMPATIBLE_SAMPLE_RENDERER","fallback_policy":"NO_SYNTHETIC_SUBSTITUTION"}
bindings["electric_guitar:LEAD_MELODY"]={"resource_id":"KARORYFER_SHINYGUITAR","target_gain_db":-6.0,"resource_type":"SFZ_SAMPLE_LIBRARY","preferred_mapping":"Programs/electric_one.sfz","library":"Karoryfer Shinyguitar","license":"CC0-1.0","renderer_requirement":"SFZ_COMPATIBLE_SAMPLE_RENDERER","fallback_policy":"NO_SYNTHETIC_SUBSTITUTION"}
for instrument_id,gain in {"kick_drum_rock":-1.0,"snare_drum":-5.0,"hi_hat":-9.0,"ride_cymbal":-8.0,"crash_cymbal":-8.0,"tom_drum":-4.0,"tom_tom":-4.0}.items():
    bindings[instrument_id]={"resource_id":"KARORYFER_BIG_RUSTY_DRUMS","target_gain_db":gain,"resource_type":"SFZ_SAMPLE_LIBRARY","preferred_mapping":"Programs/01-full.sfz","library":"Karoryfer Big Rusty Drums","license":"CC0-1.0","renderer_requirement":"SFZ_COMPATIBLE_SAMPLE_RENDERER","fallback_policy":"NO_SYNTHETIC_SUBSTITUTION"}
path.write_text(json.dumps(registry,indent=2)+"\n")
p=Path("composer/runtime/output_handoff.py"); s=p.read_text()
old="""    # Source stems cannot be promoted to a final master without the separate 3D module.
    return {'status':'AUDIO_STEMS_READY_MASTER_REQUIRED','audio_rendered':False,
            'source_audio_rendered':True,'stems':stems,'reason':'SPATIAL_MASTER_HANDOFF_REQUIRED',
            'next_stage':'EXTERNAL_3D_MASTER','fallback_policy':'NO_SYNTHETIC_SUBSTITUTION'}
"""
new="""    from spatial_master_handoff import finalize_real_stems
    final_root = OUT / 'final_audio'
    return finalize_real_stems(engine_result, stems, final_root)
"""
if old not in s: raise SystemExit("OUTPUT_HANDOFF_PATCH_TARGET_NOT_FOUND")
p.write_text(s.replace(old,new))
PY
test -f "$BANK/KARORYFER_GROWLYBASS_V1_002/growlybass_vicious.sfz"
test -f "$BANK/KARORYFER_SHINYGUITAR/Programs/electric_one.sfz"
test -f "$BANK/KARORYFER_BIG_RUSTY_DRUMS/Programs/01-full.sfz"
python -m py_compile composer/runtime/input_gateway.py composer/runtime/engine.py composer/runtime/output_handoff.py composer/runtime/spatial_master_handoff.py composer/runtime/render_server.py
echo "CURRENT COMPOSER BASELINE READY"
