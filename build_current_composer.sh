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
install_library "GREG_SULLIVAN_E_PIANOS" "https://github.com/sfzinstruments/GregSullivan.E-Pianos.git" "master"
install_library "FREEPATS_WORLD_PERCUSSION" "https://github.com/freepats/world-percussion.git" "main"
# All future compatible sample banks use the single manifest below.
python composer_overrides/sample_bank_onboarding.py --self-test
find "$BANK/KARORYFER_SHINYGUITAR" "$BANK/KARORYFER_BIG_RUSTY_DRUMS" -type f -name "*.sfz" -print0 | xargs -0 sed -i 's#\\#/#g'

python - <<'PY'
from pathlib import Path
root=Path("composer/runtime/sound_resources/KARORYFER_SHINYGUITAR/Programs")
src=(root/"main.sfz").read_text(encoding="utf-8")
src=src.replace("default_path=$sample_dir/", "default_path=../Samples/")
src="\n".join(line for line in src.splitlines() if '#include "acoustic_' not in line)
src=src.replace("set_cc106=0", "set_cc106=32")
(root/"composer-electric.sfz").write_text(src+"\n", encoding="utf-8")
# Separate recorded-guitar SFZ program for Rock leads. Keep the rhythm program
# completely unchanged. The built-in Shinyguitar LFO creates true pitch vibrato
# on sustained notes after a natural onset delay/fade, not on every quick pick.
lead=src
for previous, desired in (
    ("set_cc1=0", "set_cc1=88"),
    ("set_cc103=32", "set_cc103=85"),
    ("set_cc104=0", "set_cc104=90"),
    ("set_cc105=36", "set_cc105=64"),
    ("lfo01_pitch_oncc1=14", "lfo01_pitch_oncc1=30"),
):
    if lead.count(previous)!=1:
        raise SystemExit("LEAD_VIBRATO_SFZ_ANCHOR_NOT_FOUND:"+previous)
    lead=lead.replace(previous,desired,1)
(root/"composer-electric-lead.sfz").write_text(lead+"\n", encoding="utf-8")
PY
ln -sfn "$BANK/KARORYFER_SHINYGUITAR/Samples/electric" "$BANK/KARORYFER_SHINYGUITAR/Programs/electric"
ln -sfn "$BANK/KARORYFER_BIG_RUSTY_DRUMS/Samples" "$BANK/KARORYFER_BIG_RUSTY_DRUMS/Programs/mappings/Samples"
ln -sfn "$BANK/KARORYFER_BIG_RUSTY_DRUMS/Programs/mappings" "$BANK/KARORYFER_BIG_RUSTY_DRUMS/Programs/mappings/mappings"
cat > "$BANK/KARORYFER_BIG_RUSTY_DRUMS/Programs/composer-hihat-lite.sfz" <<'SFZ'
<global> key=42 loop_mode=one_shot seq_length=4 ampeg_release=0.20

<group> hivel=15
<region> sample=../Samples/hihat_14/tc/cl/ht_tc_vl1_rr1.flac
<region> sample=../Samples/hihat_14/tc/cl/ht_tc_vl1_rr2.flac seq_position=2
<region> sample=../Samples/hihat_14/tc/cl/ht_tc_vl1_rr3.flac seq_position=3
<region> sample=../Samples/hihat_14/tc/cl/ht_tc_vl1_rr4.flac seq_position=4

<group> lovel=16 hivel=31
<region> sample=../Samples/hihat_14/tc/cl/ht_tc_vl2_rr1.flac
<region> sample=../Samples/hihat_14/tc/cl/ht_tc_vl2_rr2.flac seq_position=2
<region> sample=../Samples/hihat_14/tc/cl/ht_tc_vl2_rr3.flac seq_position=3
<region> sample=../Samples/hihat_14/tc/cl/ht_tc_vl2_rr4.flac seq_position=4

<group> lovel=32 hivel=47
<region> sample=../Samples/hihat_14/tc/cl/ht_tc_vl3_rr1.flac
<region> sample=../Samples/hihat_14/tc/cl/ht_tc_vl3_rr2.flac seq_position=2
<region> sample=../Samples/hihat_14/tc/cl/ht_tc_vl3_rr3.flac seq_position=3
<region> sample=../Samples/hihat_14/tc/cl/ht_tc_vl3_rr4.flac seq_position=4

<group> lovel=48 hivel=63
<region> sample=../Samples/hihat_14/tc/cl/ht_tc_vl4_rr1.flac
<region> sample=../Samples/hihat_14/tc/cl/ht_tc_vl4_rr2.flac seq_position=2
<region> sample=../Samples/hihat_14/tc/cl/ht_tc_vl4_rr3.flac seq_position=3
<region> sample=../Samples/hihat_14/tc/cl/ht_tc_vl4_rr4.flac seq_position=4

<group> lovel=64 hivel=79
<region> sample=../Samples/hihat_14/tc/cl/ht_tc_vl5_rr1.flac
<region> sample=../Samples/hihat_14/tc/cl/ht_tc_vl5_rr2.flac seq_position=2
<region> sample=../Samples/hihat_14/tc/cl/ht_tc_vl5_rr3.flac seq_position=3
<region> sample=../Samples/hihat_14/tc/cl/ht_tc_vl5_rr4.flac seq_position=4

<group> lovel=80 hivel=95
<region> sample=../Samples/hihat_14/tc/cl/ht_tc_vl6_rr1.flac
<region> sample=../Samples/hihat_14/tc/cl/ht_tc_vl6_rr2.flac seq_position=2
<region> sample=../Samples/hihat_14/tc/cl/ht_tc_vl6_rr3.flac seq_position=3
<region> sample=../Samples/hihat_14/tc/cl/ht_tc_vl6_rr4.flac seq_position=4

<group> lovel=96 hivel=111
<region> sample=../Samples/hihat_14/tc/cl/ht_tc_vl7_rr1.flac
<region> sample=../Samples/hihat_14/tc/cl/ht_tc_vl7_rr2.flac seq_position=2
<region> sample=../Samples/hihat_14/tc/cl/ht_tc_vl7_rr3.flac seq_position=3
<region> sample=../Samples/hihat_14/tc/cl/ht_tc_vl7_rr4.flac seq_position=4

<group> lovel=112 hivel=127
<region> sample=../Samples/hihat_14/tc/cl/ht_tc_vl8_rr1.flac
<region> sample=../Samples/hihat_14/tc/cl/ht_tc_vl8_rr2.flac seq_position=2
<region> sample=../Samples/hihat_14/tc/cl/ht_tc_vl8_rr3.flac seq_position=3
<region> sample=../Samples/hihat_14/tc/cl/ht_tc_vl8_rr4.flac seq_position=4
SFZ

# Memory-bounded Composer-facing Big Rusty drum programs. These keep real
# Big Rusty recordings, velocity layers, and round robin while avoiding the
# full library graphs that exceed the 512 MiB Render instance in normal mode.

cat > "$BANK/KARORYFER_BIG_RUSTY_DRUMS/Programs/composer-kick-lite.sfz" <<'SFZ'
<global> key=36 loop_mode=one_shot seq_length=4 ampeg_hold=0.08 ampeg_decay=1.00 ampeg_sustain=100 ampeg_release=0.20
<group> hivel=31
<region> sample=../Samples/kick_24/kick/kick/k_vl1_rr1.flac
<region> sample=../Samples/kick_24/kick/kick/k_vl1_rr2.flac seq_position=2
<region> sample=../Samples/kick_24/kick/kick/k_vl1_rr3.flac seq_position=3
<region> sample=../Samples/kick_24/kick/kick/k_vl1_rr4.flac seq_position=4
<group> lovel=32 hivel=63
<region> sample=../Samples/kick_24/kick/kick/k_vl5_rr1.flac
<region> sample=../Samples/kick_24/kick/kick/k_vl5_rr2.flac seq_position=2
<region> sample=../Samples/kick_24/kick/kick/k_vl5_rr3.flac seq_position=3
<region> sample=../Samples/kick_24/kick/kick/k_vl5_rr4.flac seq_position=4
<group> lovel=64 hivel=95
<region> sample=../Samples/kick_24/kick/kick/k_vl9_rr1.flac
<region> sample=../Samples/kick_24/kick/kick/k_vl9_rr2.flac seq_position=2
<region> sample=../Samples/kick_24/kick/kick/k_vl9_rr3.flac seq_position=3
<region> sample=../Samples/kick_24/kick/kick/k_vl9_rr4.flac seq_position=4
<group> lovel=96 hivel=127
<region> sample=../Samples/kick_24/kick/kick/k_vl13_rr1.flac
<region> sample=../Samples/kick_24/kick/kick/k_vl13_rr2.flac seq_position=2
<region> sample=../Samples/kick_24/kick/kick/k_vl13_rr3.flac seq_position=3
<region> sample=../Samples/kick_24/kick/kick/k_vl13_rr4.flac seq_position=4
SFZ

# Preserve the original recorded kick sample program unchanged.
# The independent low-frequency stem is derived after real SFZ rendering,
# at the Composer -> standalone 3D mixer boundary (see recorded_subkick.py).

cat > "$BANK/KARORYFER_BIG_RUSTY_DRUMS/Programs/composer-snare-lite.sfz" <<'SFZ'
<global> key=38 loop_mode=one_shot seq_length=4 ampeg_hold=0.08 ampeg_decay=1.20 ampeg_sustain=100 ampeg_release=0.25
<group> hivel=31
<region> sample=../Samples/snare_14/center/top/sn_center_vl1_rr1.flac
<region> sample=../Samples/snare_14/center/top/sn_center_vl1_rr2.flac seq_position=2
<region> sample=../Samples/snare_14/center/top/sn_center_vl1_rr3.flac seq_position=3
<region> sample=../Samples/snare_14/center/top/sn_center_vl1_rr4.flac seq_position=4
<group> lovel=32 hivel=63
<region> sample=../Samples/snare_14/center/top/sn_center_vl4_rr1.flac
<region> sample=../Samples/snare_14/center/top/sn_center_vl4_rr2.flac seq_position=2
<region> sample=../Samples/snare_14/center/top/sn_center_vl4_rr3.flac seq_position=3
<region> sample=../Samples/snare_14/center/top/sn_center_vl4_rr4.flac seq_position=4
<group> lovel=64 hivel=95
<region> sample=../Samples/snare_14/center/top/sn_center_vl7_rr1.flac
<region> sample=../Samples/snare_14/center/top/sn_center_vl7_rr2.flac seq_position=2
<region> sample=../Samples/snare_14/center/top/sn_center_vl7_rr3.flac seq_position=3
<region> sample=../Samples/snare_14/center/top/sn_center_vl7_rr4.flac seq_position=4
<group> lovel=96 hivel=127
<region> sample=../Samples/snare_14/center/top/sn_center_vl10_rr1.flac
<region> sample=../Samples/snare_14/center/top/sn_center_vl10_rr2.flac seq_position=2
<region> sample=../Samples/snare_14/center/top/sn_center_vl10_rr3.flac seq_position=3
<region> sample=../Samples/snare_14/center/top/sn_center_vl10_rr4.flac seq_position=4
SFZ

cat > "$BANK/KARORYFER_BIG_RUSTY_DRUMS/Programs/composer-tom-lite.sfz" <<'SFZ'
<global> lokey=41 hikey=47 pitch_keycenter=45 loop_mode=one_shot seq_length=4 ampeg_hold=0.08 ampeg_decay=1.30 ampeg_sustain=100 ampeg_release=0.25
<group> hivel=31
<region> sample=../Samples/tom_14/center/cl/t14_vl1_rr1.flac
<region> sample=../Samples/tom_14/center/cl/t14_vl1_rr2.flac seq_position=2
<region> sample=../Samples/tom_14/center/cl/t14_vl1_rr3.flac seq_position=3
<region> sample=../Samples/tom_14/center/cl/t14_vl1_rr4.flac seq_position=4
<group> lovel=32 hivel=63
<region> sample=../Samples/tom_14/center/cl/t14_vl2_rr1.flac
<region> sample=../Samples/tom_14/center/cl/t14_vl2_rr2.flac seq_position=2
<region> sample=../Samples/tom_14/center/cl/t14_vl2_rr3.flac seq_position=3
<region> sample=../Samples/tom_14/center/cl/t14_vl2_rr4.flac seq_position=4
<group> lovel=64 hivel=95
<region> sample=../Samples/tom_14/center/cl/t14_vl4_rr1.flac
<region> sample=../Samples/tom_14/center/cl/t14_vl4_rr2.flac seq_position=2
<region> sample=../Samples/tom_14/center/cl/t14_vl4_rr3.flac seq_position=3
<region> sample=../Samples/tom_14/center/cl/t14_vl4_rr4.flac seq_position=4
<group> lovel=96 hivel=127
<region> sample=../Samples/tom_14/center/cl/t14_vl6_rr1.flac
<region> sample=../Samples/tom_14/center/cl/t14_vl6_rr2.flac seq_position=2
<region> sample=../Samples/tom_14/center/cl/t14_vl6_rr3.flac seq_position=3
<region> sample=../Samples/tom_14/center/cl/t14_vl6_rr4.flac seq_position=4
SFZ

cat > "$BANK/KARORYFER_BIG_RUSTY_DRUMS/Programs/composer-crash-lite.sfz" <<'SFZ'
<global> key=49 loop_mode=one_shot seq_length=4 ampeg_release=1.80
<group> hivel=31
<region> sample=../Samples/crash_17/cr/cl/cr_vl1_rr1.flac
<region> sample=../Samples/crash_17/cr/cl/cr_vl1_rr2.flac seq_position=2
<region> sample=../Samples/crash_17/cr/cl/cr_vl1_rr3.flac seq_position=3
<region> sample=../Samples/crash_17/cr/cl/cr_vl1_rr4.flac seq_position=4
<group> lovel=32 hivel=63
<region> sample=../Samples/crash_17/cr/cl/cr_vl2_rr1.flac
<region> sample=../Samples/crash_17/cr/cl/cr_vl2_rr2.flac seq_position=2
<region> sample=../Samples/crash_17/cr/cl/cr_vl2_rr3.flac seq_position=3
<region> sample=../Samples/crash_17/cr/cl/cr_vl2_rr4.flac seq_position=4
<group> lovel=64 hivel=95
<region> sample=../Samples/crash_17/cr/cl/cr_vl4_rr1.flac
<region> sample=../Samples/crash_17/cr/cl/cr_vl4_rr2.flac seq_position=2
<region> sample=../Samples/crash_17/cr/cl/cr_vl4_rr3.flac seq_position=3
<region> sample=../Samples/crash_17/cr/cl/cr_vl4_rr4.flac seq_position=4
<group> lovel=96 hivel=127
<region> sample=../Samples/crash_17/cr/cl/cr_vl5_rr1.flac
<region> sample=../Samples/crash_17/cr/cl/cr_vl5_rr2.flac seq_position=2
<region> sample=../Samples/crash_17/cr/cl/cr_vl5_rr3.flac seq_position=3
<region> sample=../Samples/crash_17/cr/cl/cr_vl5_rr4.flac seq_position=4
SFZ

cat > "$BANK/KARORYFER_BIG_RUSTY_DRUMS/Programs/composer-ride-lite.sfz" <<'SFZ'
<global> key=51 loop_mode=one_shot seq_length=3 ampeg_release=1.30
<group> hivel=31
<region> sample=../Samples/ride_22/rd/cl/rd_vl1_rr1.flac
<region> sample=../Samples/ride_22/rd/cl/rd_vl1_rr2.flac seq_position=2
<region> sample=../Samples/ride_22/rd/cl/rd_vl1_rr3.flac seq_position=3
<group> lovel=32 hivel=63
<region> sample=../Samples/ride_22/rd/cl/rd_vl4_rr1.flac
<region> sample=../Samples/ride_22/rd/cl/rd_vl4_rr2.flac seq_position=2
<region> sample=../Samples/ride_22/rd/cl/rd_vl4_rr3.flac seq_position=3
<group> lovel=64 hivel=95
<region> sample=../Samples/ride_22/rd/cl/rd_vl7_rr1.flac
<region> sample=../Samples/ride_22/rd/cl/rd_vl7_rr2.flac seq_position=2
<region> sample=../Samples/ride_22/rd/cl/rd_vl7_rr3.flac seq_position=3
<group> lovel=96 hivel=127
<region> sample=../Samples/ride_22/rd/cl/rd_vl10_rr1.flac
<region> sample=../Samples/ride_22/rd/cl/rd_vl10_rr2.flac seq_position=2
<region> sample=../Samples/ride_22/rd/cl/rd_vl10_rr3.flac seq_position=3
SFZ
cp composer_overrides/production_resource_policy.py composer/runtime/production_resource_policy.py
cp composer_overrides/real_electric_piano_probe.py composer/runtime/real_electric_piano_probe.py
cp composer_overrides/real_conga_probe.py composer/runtime/real_conga_probe.py
cp composer_overrides/sample_bank_onboarding.py composer/runtime/sample_bank_onboarding.py
cp composer_overrides/verified_future_instruments.json composer/runtime/verified_future_instruments.json
cp composer_overrides/genre_resource_readiness.py composer/runtime/genre_resource_readiness.py
cp composer_overrides/sfz_renderer_adapter.py composer/runtime/sfz_renderer_adapter.py
cp composer_overrides/genre_development_patch.py composer/runtime/genre_development_patch.py
cp -R composer_overrides/genre_styles composer/runtime/genre_styles
cp composer_overrides/test_genre_style_files.py composer/runtime/test_genre_style_files.py
cp composer_overrides/instrument_performance_contract.py composer/runtime/instrument_performance_contract.py
cp composer_overrides/test_instrument_performance_contract.py composer/runtime/test_instrument_performance_contract.py
# Research-only opt-in Rock bass release: copying module does not activate it.
cp composer_overrides/rock_bass_sustain_policy_v1.py composer/runtime/rock_bass_sustain_policy_v1.py
cp composer_overrides/test_rock_bass_sustain_policy_v1.py composer/runtime/test_rock_bass_sustain_policy_v1.py
# Composition quality research: OFF by default; preserves all source instruments.
cp composer_overrides/rock_melodic_author_v1.py composer/runtime/rock_melodic_author_v1.py
cp composer_overrides/test_rock_melodic_author_v1.py composer/runtime/test_rock_melodic_author_v1.py
cp composer_overrides/AI_Comp_3D_Spatialization_Scene_Engine_009_RESTORED_2026-10-03.py composer/runtime/
cp composer_overrides/AI_Comp_Object_Based_3D_Master_006_RESTORED_2026-10-03.py composer/runtime/
cp composer_overrides/global_3d_output_gate.py composer/runtime/
cp composer_overrides/spatial_master_handoff.py composer/runtime/
cp composer_overrides/standalone_3d_mixer.py composer/runtime/
cp composer_overrides/render_server.py composer/runtime/
# Replay ONLY documented target-native initial MIDI controls into generated MIDI.
# Leave the immutable runtime.b64 and original instrument libraries unchanged.
cp composer_overrides/midi_initial_cc_bridge.py composer/runtime/
cp composer_overrides/expressive_gesture_bridge.py composer/runtime/
cp composer_overrides/musical_gesture_author.py composer/runtime/
cp composer_overrides/performance_capabilities.json composer/runtime/
cp composer_overrides/test_midi_initial_cc_bridge.py composer/runtime/
cp composer_overrides/test_expressive_gesture_bridge.py composer/runtime/
cp composer_overrides/instrument_gesture_handoff.py composer/runtime/
cp composer_overrides/phrase_expression_decisions.py composer/runtime/
cp composer_overrides/automatic_phrase_handoff.py composer/runtime/
cp composer_overrides/test_automatic_phrase_decisions.py composer/runtime/
cp composer_overrides/test_instrument_gesture_handoff.py composer/runtime/
python composer_overrides/install_midi_control_bridge.py --core composer/runtime/AI_Comp_Executable_Output_Core_001.py
python composer_overrides/install_instrument_gesture_handoff.py --handoff composer/runtime/output_handoff.py
python - <<'PY'
import json
from pathlib import Path
path=Path("composer/runtime/target_registry.json"); registry=json.loads(path.read_text())
bindings=registry["targets"]["INTERNAL"].setdefault("instrument_bindings",{})
# FreePats conga samples. The composer-specific SFZ is prepared and
# measured in the build; it preserves all 5 recorded stroke groups.
bindings["conga"]={
    "resource_id":"FREEPATS_WORLD_PERCUSSION",
    "resource_type":"SFZ_SAMPLE_LIBRARY",
    "preferred_mapping":"composer-conga-five-strokes.sfz",
    "library":"FreePats World Percussion",
    "license":"CC0-1.0",
    "fallback_policy":"NO_SYNTHETIC_SUBSTITUTION",
    "renderer_requirement":"SFZ_COMPATIBLE_SAMPLE_RENDERER",
    "target_gain_db":-6.0,
    "strike_map":{
        "60":"standard_conga",
        "61":"high_conga",
        "62":"low_conga",
        "63":"muted_conga",
        "64":"muted_low_conga"
    },
    "source":"https://github.com/freepats/world-percussion"
}
bindings["electric_piano"]={
    "resource_id":"GREG_SULLIVAN_E_PIANOS","target_gain_db":-6.0,
    "resource_type":"SFZ_SAMPLE_LIBRARY",
    "preferred_mapping":"Wurlitzer EP200/composer-wurlitzer.sfz",
    "library":"Greg Sullivan E-Pianos / Wurlitzer EP200",
    "license":"CC-BY-3.0","renderer_requirement":"SFZ_COMPATIBLE_SAMPLE_RENDERER",
    "fallback_policy":"NO_SYNTHETIC_SUBSTITUTION",
    "attribution":"Greg Sullivan; Wurlitzer EP200; sfz mapping kinwie; CC BY 3.0",
}
bindings["electric_bass_guitar"]={
    "resource_id":"KARORYFER_GROWLYBASS_V1_002","target_gain_db":0.0,
    "resource_type":"SFZ_SAMPLE_LIBRARY","preferred_mapping":"growlybass_clean.sfz",
    "library":"Karoryfer Growlybass","license":"CC0",
    "renderer_requirement":"SFZ_COMPATIBLE_SAMPLE_RENDERER",
    "fallback_policy":"NO_SYNTHETIC_SUBSTITUTION",
    "articulation_policy":"SUSTAINED_REAL_BASS_WITH_NATIVE_VELOCITY_AND_ROUND_ROBIN"
}
bindings["electric_guitar:RHYTHM_POWER_CHORDS"]={
    "resource_id":"KARORYFER_SHINYGUITAR","target_gain_db":-7.0,
    "resource_type":"SFZ_SAMPLE_LIBRARY","preferred_mapping":"Programs/composer-electric.sfz",
    "library":"Karoryfer Shinyguitar","license":"CC0-1.0",
    "renderer_requirement":"SFZ_COMPATIBLE_SAMPLE_RENDERER",
    "fallback_policy":"NO_SYNTHETIC_SUBSTITUTION",
    "midi_mapping":{"initial_cc":{"100":0,"101":127,"106":32,"107":0}}
}
bindings["electric_guitar:LEAD_MELODY"]={
    "resource_id":"KARORYFER_SHINYGUITAR","target_gain_db":-8.0,
    "resource_type":"SFZ_SAMPLE_LIBRARY","preferred_mapping":"Programs/composer-electric-lead.sfz",
    "library":"Karoryfer Shinyguitar","license":"CC0-1.0",
    "renderer_requirement":"SFZ_COMPATIBLE_SAMPLE_RENDERER",
    "fallback_policy":"NO_SYNTHETIC_SUBSTITUTION",
    "midi_mapping":{"initial_cc":{"1":88,"100":0,"101":127,"103":85,"104":90,"105":64,"106":24,"107":0}},
    "articulation_policy":"SUSTAINED_LEAD_VIBRATO_DELAYED_NO_RHYTHM_MODULATION"
}
programs={
    "kick_drum_rock":(10.0,"Programs/composer-kick-lite.sfz"),
    "snare_drum":(9.0,"Programs/composer-snare-lite.sfz"),
    "hi_hat":(4.0,"Programs/composer-hihat-lite.sfz"),
    "ride_cymbal":(5.0,"Programs/composer-ride-lite.sfz"),
    "crash_cymbal":(6.0,"Programs/composer-crash-lite.sfz"),
    "tom_drum":(9.0,"Programs/composer-tom-lite.sfz"),
    "tom_tom":(9.0,"Programs/composer-tom-lite.sfz"),
}
for instrument_id,(gain,mapping) in programs.items():
    bindings[instrument_id]={
        "resource_id":"KARORYFER_BIG_RUSTY_DRUMS","target_gain_db":gain,
        "resource_type":"SFZ_SAMPLE_LIBRARY","preferred_mapping":mapping,
        "library":"Karoryfer Big Rusty Drums","license":"CC0-1.0",
        "renderer_requirement":"SFZ_COMPATIBLE_SAMPLE_RENDERER",
        "fallback_policy":"NO_SYNTHETIC_SUBSTITUTION"}

# The legacy genre palettes use these musical names for the SAME
# authentic sampled bass guitar and sampled electric lead guitar. These
# are identity aliases, not new instruments or synthetic substitutions.
bindings["electric_bass"] = dict(bindings["electric_bass_guitar"])
bindings["electric_bass"]["alias_of"] = "electric_bass_guitar"
bindings["lead_guitar"] = dict(bindings["electric_guitar:LEAD_MELODY"])
bindings["lead_guitar"]["alias_of"] = "electric_guitar:LEAD_MELODY"

path.write_text(json.dumps(registry,indent=2)+"\n")
# Preserve the existing composer and add long-form development at its established
# genre-adapter boundary. Quick/test mode stays untouched.
adapter=Path("composer/runtime/AI_Comp_Genre_Execution_Adapter_002_WORKING_2026-10-02_184019_CDT.py")
a=adapter.read_text()
override=r"""
# --- full-length development override ---
from genre_development_patch import (
    build_developed_progression as _build_developed_progression,
    build_profile_progression as _build_profile_progression,
    build_jazz_progression as _build_jazz_progression,
    realize_jazz_voicings as _realize_jazz_voicings,
    apply_jazz_phrase_expression as _apply_jazz_phrase_expression,
    develop_full_length as _develop_full_length,
)
from genre_styles.Jazz.jazz_ballad import arrange_events as _arrange_jazz_ballad
_legacy_build_setup = build_setup

def build_setup(name, profile, mode='quick', creation_seed=0):
    result = _legacy_build_setup(name, profile, mode, creation_seed)
    if mode != 'normal' or result.get('status') != 'PASS':
        return result

    req = dict(result['theory_request'])
    bars = int(result['bars'])
    tempo_bpm = int(result['tempo_bpm'])
    seedv = int(hashlib.sha256(
        f"{profile['profile_id']}:{creation_seed}".encode()
    ).hexdigest()[:8], 16)

    # Rock was landing at 125 BPM for the baseline seed, which is too relaxed
    # for the driving test the Control Panel is using. Stay inside the approved
    # ROCK profile (100-145) but bias normal Rock into its faster band.
    if name == 'ROCK':
        approved = profile.get('tempo_bpm_range') or [tempo_bpm, tempo_bpm]
        profile_lo, profile_hi = int(approved[0]), int(approved[-1])
        tempo_bpm = profile_hi
        # The preserved Output Core builds the MIDI execution package from
        # theory['tempo_bpm'], so write the selected Rock tempo back into the
        # theory request before rebuilding composition context.
        req['tempo_bpm'] = tempo_bpm

        num, den = map(int, str(result['meter']).split('/'))
        beats_per_bar = float(num) * 4.0 / float(den)
        bars = max(24, min(320, round(210.0 * tempo_bpm / (60.0 * beats_per_bar))))
        req['bars'] = bars

    jazz_progression = _build_jazz_progression(name, profile, req['mode'], bars, seedv)
    if jazz_progression is None:
        req['roman_progression'] = _build_profile_progression(
            name, profile, req['mode'], bars, seedv, _build_developed_progression
        )
    else:
        req['roman_progression'] = jazz_progression

    ctx = engine.build_composition_context(req)
    if ctx.get('status') not in ('PASS', 'REVIEW_REQUIRED'):
        blocked = dict(result)
        blocked.update(
            status='THEORY_BLOCK',
            theory=ctx,
            theory_request=req,
            events=[],
        )
        return blocked

    # The existing Theory engine validates harmonic roots and meter. For
    # exact approved Jazz profiles, add diatonic sevenths/sixths before
    # the existing event generator realizes the notes.
    ctx = _realize_jazz_voicings(ctx, name, profile)

    events = generate_events(
        name,
        result['execution_template'],
        profile,
        ctx,
        tempo_bpm,
        creation_seed,
    )
    events = _develop_full_length(
        events,
        ctx,
        result['execution_template'],
        creation_seed,
    )
    # Jazz phrasing is a shared chord gesture, not per-note timing jitter.
    meter_beats = float(ctx['meter']['numerator']) * 4.0 / float(ctx['meter']['denominator'])
    events = _apply_jazz_phrase_expression(
        events, name, profile, meter_beats, creation_seed,
    )
    if name == 'Jazz Ballad':
        # Chord-aware arranger layer: protect the recorded piano, resolve
        # bass/clarinet playable ranges and limit overlapping brush one-shots.
        # The existing output engine, Rock and all other styles are unchanged.
        events = _arrange_jazz_ballad(events, ctx, creation_seed)

    developed = dict(result)
    developed['theory_request'] = req
    developed['theory_status'] = ctx['status']
    developed['tempo_bpm'] = tempo_bpm
    developed['bars'] = bars
    developed['events'] = events
    # One shared, source-grounded genre grammar, not a second Rock interpreter.
    # Attach ONLY symbolic intent metadata; the original notes, sampled audio,
    # plug and independent 3D mixing are untouched and remain gated.
    from genre_styles.shared_musical_grammar import compile_musical_plan
    developed['shared_musical_plan'] = compile_musical_plan(
        name, meter=result['meter'], tempo_bpm=tempo_bpm, bars=bars,
        original_stage3_result=result,
    )
    # Genre-owned original seed data enters the SAME Stage3->4 interpreter.
    # These are separately auditionable symbolic patterns, NOT a replacement
    # for the old Composer events and NOT an authorized audio render.
    from genre_styles.source_pattern_library import compile_original_source_seed
    developed['source_pattern_seed_plan'] = compile_original_source_seed(name)
    # Convert exact genre-owned source notes into a separate Stage4 proposal.
    # Fail closed for unknown recorded programs; NEVER override the original
    # events/renderer or enable the independent final 3D mixer automatically.
    from genre_styles.source_pattern_composer_handoff import prepare_source_pattern_composer_handoff
    developed['source_pattern_composer_handoff'] = prepare_source_pattern_composer_handoff(
        developed['source_pattern_seed_plan'],
        original_stage3_result=result,
        existing_events=events,
    )
    if name == 'ROCK':
        # The legacy palette declares one generic "drums" instrument even
        # though developed Rock events use separate sample-backed kit members.
        # Keep the completeness guard: declare the required real instruments.
        declared = []
        for instrument in result['palette']:
            if instrument == 'drums':
                declared.extend(('kick_drum_rock', 'snare_drum', 'hi_hat'))
            else:
                declared.append(instrument)
        developed['palette'] = declared
    developed['development_model'] = 'FULL_LENGTH_SECTIONAL_V2'
    return developed
"""
adapter.write_text(a + "\n" + override + "\n")
p=Path("composer/runtime/output_handoff.py"); s=p.read_text()
old="""    # Source stems cannot be promoted to a final master without the separate 3D module.
    return {'status':'AUDIO_STEMS_READY_MASTER_REQUIRED','audio_rendered':False,
            'source_audio_rendered':True,'stems':stems,'reason':'SPATIAL_MASTER_HANDOFF_REQUIRED',
            'next_stage':'EXTERNAL_3D_MASTER','fallback_policy':'NO_SYNTHETIC_SUBSTITUTION'}
"""
new="""    # Composition and SFZ rendering are complete here. The 3D mixer is a
    # separate final-stage process so it cannot alter composition or instrument
    # rendering and does not share the Composer's audio working memory.
    import subprocess, sys
    final_root = OUT / 'final_audio'
    job_dir = OUT / package.package_id / 'three_d_mixer'
    job_dir.mkdir(parents=True, exist_ok=True)
    job_path = job_dir / 'job.json'
    # Composer chooses the balance profile; the independent 3D mixer remains
    # unchanged. This is a pure, Rock-only metadata overlay.
    from genre_styles.Rock.rock_balance_contract import apply_rock_balance
    mixer_instructions = apply_rock_balance(engine_result)
    from genre_styles.Jazz.jazz_ballad import balance_mix as apply_jazz_ballad_balance
    mixer_instructions = apply_jazz_ballad_balance(mixer_instructions, stems)
    # A separate recorded-kick derivative follows the same existing drum
    # events as KICK. The independent 3D mixer remains entirely unchanged.
    from genre_styles.Rock.recorded_subkick import prepare_recorded_subkick
    mixer_instructions, mixer_stems = prepare_recorded_subkick(
        mixer_instructions, stems, job_dir
    )
    job_path.write_text(json.dumps({
        'engine_result': mixer_instructions, 'stems': mixer_stems
    }), encoding='utf-8')
    cp = subprocess.run(
        [sys.executable, str(ROOT / 'standalone_3d_mixer.py'), str(job_path), str(final_root)],
        capture_output=True, text=True, timeout=240
    )
    try:
        mixed = json.loads((cp.stdout or '').strip())
    except json.JSONDecodeError:
        return {'status':'AUDIO_3D_MIX_FAILED','audio_rendered':False,
                'reason':'UNREADABLE_3D_MIXER_RESPONSE',
                'mixer_stderr':(cp.stderr or '')[-800:]}
    if cp.returncode != 0 or mixed.get('status') != 'AUDIO_RENDER_PASS':
        mixed.setdefault('status','AUDIO_3D_MIX_FAILED')
        mixed.setdefault('audio_rendered',False)
        mixed['mixer_stderr']=(cp.stderr or '')[-800:]
        return mixed
    mixed['pipeline_order']=['COMPOSITION','REAL_INSTRUMENT_RENDER','STANDALONE_3D_FINAL_STAGE']
    return mixed
"""
if old not in s: raise SystemExit("OUTPUT_HANDOFF_PATCH_TARGET_NOT_FOUND")
p.write_text(s.replace(old,new))
PY
test -f "$BANK/KARORYFER_GROWLYBASS_V1_002/growlybass_clean.sfz"
test -f "$BANK/KARORYFER_SHINYGUITAR/Programs/composer-electric.sfz"
test -f "$BANK/KARORYFER_SHINYGUITAR/Programs/composer-electric-lead.sfz"
test -f "$BANK/KARORYFER_BIG_RUSTY_DRUMS/Programs/composer-kick-lite.sfz"
test -f "$BANK/KARORYFER_BIG_RUSTY_DRUMS/Programs/composer-snare-lite.sfz"
test -f "$BANK/KARORYFER_BIG_RUSTY_DRUMS/Programs/composer-hihat-lite.sfz"
test -f "$BANK/KARORYFER_BIG_RUSTY_DRUMS/Programs/composer-tom-lite.sfz"
test -f "$BANK/KARORYFER_BIG_RUSTY_DRUMS/Programs/composer-crash-lite.sfz"
test -f "$BANK/KARORYFER_BIG_RUSTY_DRUMS/Programs/composer-ride-lite.sfz"
AI_COMP_RESOURCE_BANK="$BANK" PATH="$TOOLS_DIR/bin:$PATH" python - <<'PY'
from pathlib import Path
import sys
sys.path.insert(0, str(Path("composer/runtime").resolve()))
from sfz_renderer_adapter import validate_sfz_samples
bank=Path("composer/runtime/sound_resources")
checks=[
    bank/"KARORYFER_GROWLYBASS_V1_002/growlybass_clean.sfz",
    bank/"KARORYFER_SHINYGUITAR/Programs/composer-electric.sfz",
    bank/"KARORYFER_BIG_RUSTY_DRUMS/Programs/composer-kick-lite.sfz",
    bank/"KARORYFER_BIG_RUSTY_DRUMS/Programs/composer-snare-lite.sfz",
    bank/"KARORYFER_BIG_RUSTY_DRUMS/Programs/composer-hihat-lite.sfz",
]
for path in checks:
    report=validate_sfz_samples(path)
    print("REAL_INSTRUMENT_RESOURCE_READY", path.name, report, flush=True)
PY
python - <<'PY'
from pathlib import Path
p=Path("composer/runtime/input_gateway.py")
s=p.read_text()
old="""    return {
        'status': result.get('status'),
        'genre': result.get('genre',genre.strip()),
        'reason': result.get('reason'),
        'stage': result.get('stage'),
        'audio_rendered': result.get('audio_rendered',False),
        'output_handoff': result.get('output_handoff'),
"""
new="""    stems=(result.get('audio_render') or {}).get('stems',[])
    diagnostics=[{
        'track_id':stem.get('track_id'),
        'instrument_id':stem.get('instrument_id'),
        'note_count':stem.get('note_count'),
        'peak_dbfs':stem.get('peak_dbfs'),
        'rms_dbfs':stem.get('rms_dbfs'),
    } for stem in stems]
    return {
        'status': result.get('status'),
        'genre': result.get('genre',genre.strip()),
        'tempo_bpm': result.get('modules',{}).get('theory',{}).get('tempo_bpm'),
        'render_diagnostics': diagnostics,
        'reason': result.get('reason'),
        'stage': result.get('stage'),
        'audio_rendered': result.get('audio_rendered',False),
        'output_handoff': result.get('output_handoff'),
"""
if old not in s:
    raise SystemExit("INPUT_GATEWAY_DIAGNOSTIC_PATCH_TARGET_NOT_FOUND")
p.write_text(s.replace(old,new))
PY
python composer/runtime/real_electric_piano_probe.py
PYTHONPATH=composer/runtime python -m genre_styles.Rock.real_rock_alias_probe
PYTHONPATH=composer/runtime python -m genre_styles.Rock.rock_expression_depth_probe
python composer/runtime/real_conga_probe.py
python composer/runtime/sample_bank_onboarding.py --install
python composer/runtime/sample_bank_onboarding.py --apply
AI_COMP_SFZ_RENDERER="$PWD/.composer_tools/bin/sfizz_render" PYTHONPATH=composer/runtime python -m genre_styles.Jazz.jazz_ballad_recorded_resources

# Resolve every Jazz Ballad instrument from its OWN genre file. This checks
# links against the existing registry and on-disk sample bank, not duplicate
# audio copies. No other genre or sound engine is changed.
python - <<'PY'
import json, sys
from pathlib import Path
root=Path("composer/runtime").resolve()
sys.path.insert(0,str(root))
from genre_styles.Jazz.jazz_ballad import instrument_links, validate_instrument_links
package=instrument_links()
registry=json.loads((root/"target_registry.json").read_text(encoding="utf-8"))
bindings=registry["targets"]["INTERNAL"]["instrument_bindings"]
validate_instrument_links(bindings)
for role, spec in package["instruments"].items():
    sfz=root/package["shared_root"]/spec["resource_id"]/spec["sfz"]
    assert sfz.is_file(), ("JAZZ_LINK_SOURCE_MISSING", role, str(sfz))
print("JAZZ_BALLAD_INDEPENDENT_INSTRUMENT_LINKS_PASS",
      sorted(package["instruments"]), flush=True)
PY

python composer/runtime/production_resource_policy.py --self-test
python composer/runtime/production_resource_policy.py --audit-registry composer/runtime/target_registry.json
python -m py_compile composer/runtime/midi_initial_cc_bridge.py composer/runtime/expressive_gesture_bridge.py composer/runtime/musical_gesture_author.py composer/runtime/instrument_gesture_handoff.py composer/runtime/phrase_expression_decisions.py composer/runtime/automatic_phrase_handoff.py composer/runtime/AI_Comp_Executable_Output_Core_001.py composer/runtime/input_gateway.py composer/runtime/engine.py composer/runtime/output_handoff.py composer/runtime/spatial_master_handoff.py composer/runtime/standalone_3d_mixer.py composer/runtime/render_server.py composer/runtime/genre_development_patch.py composer/runtime/instrument_performance_contract.py composer/runtime/genre_styles/Rock/rock_balance_contract.py composer/runtime/AI_Comp_Genre_Execution_Adapter_002_WORKING_2026-10-02_184019_CDT.py

# Verify routed harmony for all 55 without changing sample routing or sound.
python - <<'PY'
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path("composer/runtime").resolve()))
from genre_development_patch import build_profile_progression, build_developed_progression
profiles = json.loads(Path(
    "composer/runtime/AI_Comp_Genre_Performance_Registry_002_WORKING_COMPLETE_2026-10-02_182810_CDT.json"
).read_text())["profiles"]
assert len(profiles) == 55
automatic = controlled = 0
for name, profile in profiles.items():
    if profile["resolution_policy"] != "AUTOMATIC_BASELINE_ALLOWED":
        controlled += 1
        try:
            build_profile_progression(name, profile, "major", 48, 7, build_developed_progression)
        except ValueError as e:
            assert str(e) == "GENRE_HARMONY_CONTROLLED_INPUT_REQUIRED"
        else:
            raise AssertionError("CONTROLLED_GENRE_NOT_BLOCKED:" + name)
        continue
    automatic += 1
    mode = "natural_minor" if name == "Funk" else "major"
    progression = build_profile_progression(
        name, profile, mode, 48, 7, build_developed_progression
    )
    assert len(progression) == 48, name
    if name == "Funk":
        assert progression.count("i") >= 34 and progression[-1] == "i"
    elif name in ("Traditional Country", "Two-Step"):
        assert set(progression) == {"I", "IV", "V"} and progression[-1] == "I"
    elif name == "ROCK":
        assert progression == build_developed_progression(mode, 48, 7)
assert (automatic, controlled) == (48, 7), (automatic, controlled)
print("GENRE_PROFILE_HARMONY_ROUTING_PASS", automatic, controlled, flush=True)
PY

# Audition arranger behavior as pure score processing before any live rendering.
# Guard piano integrity, actual sample MIDI ranges, developed chord movement,
# and absence of changes to working Rock and unrelated genres.
PYTHONPATH=composer/runtime python -m genre_styles.Jazz.test_jazz_arranger_style -v
PYTHONPATH=composer/runtime python -m genre_styles.Jazz.test_jazz_ballad_equal_intensity -v
python composer/runtime/test_genre_style_files.py -v

# Keep the six confirmed recorded Jazz Ballad roles and extended harmony.
# The seven other Jazz names are only placeholders until Ballad is finished.
# The legacy non-Ballad Composer remains untouched; no early templates.
python - <<'PY'
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path("composer/runtime").resolve()))
from genre_development_patch import (
    JAZZ_GENRE_PROFILES, build_jazz_progression,
    realize_jazz_voicings, apply_jazz_phrase_expression,
)
from genre_styles.registry import get_style
from executable_theory_engine_SOURCE_PRESERVED import TheoryEngine
profiles = json.loads(Path(
    "composer/runtime/AI_Comp_Genre_Performance_Registry_002_WORKING_COMPLETE_2026-10-02_182810_CDT.json"
).read_text())["profiles"]
theory = TheoryEngine()
assert len(profiles) == 55 and len(JAZZ_GENRE_PROFILES) == 8
for name, profile_id in JAZZ_GENRE_PROFILES.items():
    p = profiles[name]
    assert p["profile_id"] == profile_id
    if name != "Jazz Ballad":
        assert get_style(name, p) is None, ("PREMATURE_JAZZ_STYLE",name)
        mode = "natural_minor" if name == "Jazz Fusion" else "major"
        assert build_jazz_progression(name, p, mode, 32, 19) is None, name
        continue
    prog = build_jazz_progression(name, p, "major", 32, 19)
    assert len(prog) == 32 and prog[-1] == "I"
    ctx = theory.build_composition_context({
        "tonic":"C", "mode":"major", "meter":"4/4",
        "bars":32, "roman_progression":prog,
    })
    assert ctx["status"] == "PASS", ctx.get("status")
    jazz_ctx = realize_jazz_voicings(ctx,name,p)
    assert all(len(ch["notes"]) == 4 for ch in jazz_ctx["harmony"]["chords"])
    assert len(ctx["harmony"]["chords"][0]["notes"]) == 3, "ORIGINAL_CONTEXT_CHANGED"
    note = [{"track_id":"HARMONY","start_beat":4,"velocity":100}]
    assert apply_jazz_phrase_expression(note,name,p,4) != note
    assert note[0]["velocity"] == 100
for name in ("ROCK","New Age","Traditional Country","Funk"):
    assert build_jazz_progression(name, profiles[name], "major", 32, 19) is None
c = theory.build_composition_context({
    "tonic":"C","mode":"major","meter":"4/4","bars":3,
    "roman_progression":["ii","V","I"],
})
j = realize_jazz_voicings(c,"Jazz Ballad",profiles["Jazz Ballad"])
assert [x["notes"] for x in j["harmony"]["chords"]] == [
    ["D","F","A","C"],["G","B","D","F"],["C","E","G","B"]
]
print("JAZZ_BALLAD_ONLY_EXTENDED_HARMONY_PASS", len(JAZZ_GENRE_PROFILES), len(profiles), flush=True)
PY

# Verify rich Jazz voicings survive the legacy long-form arrangement edits.
# Musical event-level only. Does not claim audio rendering is complete.
python - <<'PY'
import sys
from pathlib import Path
sys.path.insert(0,str(Path("composer/runtime").resolve()))
from genre_development_patch import develop_full_length
ctx = {
    "meter":{"numerator":4,"denominator":4},
    "harmony":{"voicing_model":"JAZZ_EXTENDED_HARMONY_V1"},
}
notes = (60, 64, 67, 71)
def chord_at(bar, beat):
    return [
        {"track_id":"HARMONY","instrument_id":"piano",
         "start_beat":4*bar+beat,"duration_beats":0.45,
         "midi":midi,"velocity":85,"articulation":"genre_harmony"}
        for midi in notes
    ]
# Bar 8 reaches the former odd-MIDI-note dropping rule.
for bar, beat, seed in ((8,3,0), (40,1,0)):
    original = chord_at(bar,beat)
    out = develop_full_length(original,ctx,"swing",seed)
    harmony = [e for e in out if e["track_id"] == "HARMONY"]
    assert set(e["midi"] for e in harmony) == set(notes), (bar,harmony)
    assert len(harmony) == 4, (bar,harmony)
    assert len({round(e["velocity"],6) for e in harmony}) == 1, bar
    assert original == chord_at(bar,beat), "MUTATED_INPUT"
# The standard non-Jazz branch still receives its former parity treatment.
non_jazz_ctx = {"meter":ctx["meter"],"harmony":{}}
former = develop_full_length(chord_at(8,3),non_jazz_ctx,"swing",0)
assert {e["midi"] for e in former} == {60,64}, former
print("JAZZ_CHORD_TONES_PRESERVED_PASS",flush=True)
PY

# Isolated Jazz audio evidence using actual GENRE-GENERATED piano notes,
# not a hand-created chord, an instrument substitution, or the final 3D master.
# Never change the approved Wurlitzer SFZ/sample bank.
python - <<'PY'
import collections, importlib.util, json, struct, sys
from pathlib import Path
root = Path("composer/runtime").resolve()
sys.path.insert(0, str(root))
from sfz_renderer_adapter import render_midi
import os
renderer = root.parent.parent / ".composer_tools" / "bin" / "sfizz_render"
assert renderer.is_file(), "JAZZ_PROBE_SFIZZ_RENDERER_MISSING"
os.environ["AI_COMP_SFZ_RENDERER"] = str(renderer)
source = root / "AI_Comp_Genre_Execution_Adapter_002_WORKING_2026-10-02_184019_CDT.py"
spec = importlib.util.spec_from_file_location("jazz_real_recorded_audio_probe", source)
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)
result = adapter.GenreExecutionAdapter().resolve("Jazz Ballad", mode="normal", creation_seed=0)
assert result["status"] == "PASS", result.get("status")
assert result["execution_template"] == "jazz_ballad"
piano = [e for e in result["events"] if e.get("track_id") == "HARMONY"]
assert piano and all(e.get("instrument_id") == "electric_piano" for e in piano)
groups = collections.defaultdict(list)
for note in piano:
    groups[round(float(note["start_beat"]), 6)].append(note)
# Two original, genre-generated chord attacks per bar over eight whole bars.
onsets = sorted(groups)[:16]
assert len(onsets) == 16, "JAZZ_EIGHT_BAR_PIANO_ONSETS_MISSING"
meter_value = result["meter"]
assert meter_value in ("3/4", "4/4"), ("JAZZ_BALLAD_UNEXPECTED_METER", meter_value)
numerator, denominator = map(int, meter_value.split("/"))
bar_beats = numerator * 4.0 / denominator
bars_covered = {int(beat // bar_beats) for beat in onsets}
assert bars_covered == set(range(8)), ("JAZZ_EIGHT_BAR_GAP", sorted(bars_covered))
for onset in onsets:
    voices = groups[onset]
    assert len(voices) == 4, ("JAZZ_CHORD_LOST_VOICE", onset, voices)
    assert len({int(n["midi"]) for n in voices}) == 4
    assert len({int(n["velocity"]) for n in voices}) == 1
# Phrase structure should be audibly non-uniform: preserve distinct changes
# already made by Genre Development. This test DOES NOT add humanization.
distinct_chords = {tuple(sorted(int(n["midi"]) for n in groups[o])) for o in onsets}
attack_velocities = [int(groups[o][0]["velocity"]) for o in onsets]
assert len(distinct_chords) >= 3, ("JAZZ_HARMONY_STATIC", sorted(distinct_chords))
assert len(set(attack_velocities)) >= 4, ("JAZZ_EXPRESSION_STATIC", attack_velocities)
assert max(attack_velocities) - min(attack_velocities) >= 4, "JAZZ_EXPRESSION_DYNAMIC_RANGE_TOO_SMALL"
chosen = [note for onset in onsets for note in groups[onset]]
assert len(chosen) == 64, "JAZZ_CHORD_NOTE_COUNT_CHANGED"
# Standard MIDI: preserve the generated note pitch/onset/duration/velocity.
def vlq(n):
    assert n >= 0
    values = [n & 0x7f]
    n >>= 7
    while n:
        values.insert(0, (n & 0x7f) | 0x80)
        n >>= 7
    return bytes(values)
tempo_us = max(1, round(60_000_000 / int(result["tempo_bpm"])))
messages = [(0, 0, b"\xff\x51\x03" + tempo_us.to_bytes(3, "big"))]
for n in chosen:
    pitch, vel = int(n["midi"]), int(n["velocity"])
    assert 0 <= pitch <= 127 and 1 <= vel <= 127
    start = round(float(n["start_beat"]) * 480)
    end = start + max(1, round(float(n["duration_beats"]) * 480))
    messages.extend(((start, 2, bytes([0x90, pitch, vel])),
                     (end, 1, bytes([0x80, pitch, 0]))))
messages.sort(key=lambda x: (x[0], x[1], x[2]))
track = bytearray()
position = 0
for when, _, msg in messages:
    track += vlq(when - position) + msg
    position = when
track += b"\x00\xff\x2f\x00"
out = root / "output" / "jazz_recorded_chord_probe"
out.mkdir(parents=True, exist_ok=True)
midi_path = out / "jazz-ballad-eight-bars-generated-piano.mid"
wav_path = out / "jazz-ballad-eight-bars-generated-piano.wav"
midi_path.write_bytes(b"MThd" + struct.pack(">IHHH", 6, 0, 1, 480) +
                      b"MTrk" + struct.pack(">I", len(track)) + track)
bindings = json.loads((root / "target_registry.json").read_text())[
    "targets"]["INTERNAL"]["instrument_bindings"]
resource = bindings["electric_piano"]
assert resource["resource_id"] == "GREG_SULLIVAN_E_PIANOS"
assert resource["preferred_mapping"] == "Wurlitzer EP200/composer-wurlitzer.sfz"
rendered = render_midi(resource, midi_path, wav_path, sample_rate=44100)
assert rendered["status"] == "AUDIO_RENDER_PASS"
assert rendered["peak_linear"] > 0 and rendered["rms_linear"] > 0
# A/B listening control: original score and timing; constant MIDI velocity.
# This diagnostic is independent of instrument definitions and genre profiles.
flat_velocity = sorted(attack_velocities)[len(attack_velocities) // 2]
flat_events = [(0, 0, b"\xff\x51\x03" + tempo_us.to_bytes(3, "big"))]
for n in chosen:
    pitch = int(n["midi"])
    start = round(float(n["start_beat"]) * 480)
    end = start + max(1, round(float(n["duration_beats"]) * 480))
    flat_events.extend((
        (start, 2, bytes([0x90, pitch, flat_velocity])),
        (end, 1, bytes([0x80, pitch, 0])),
    ))
flat_events.sort(key=lambda x: (x[0], x[1], x[2]))
flat_track = bytearray()
position = 0
for when, _, msg in flat_events:
    flat_track += vlq(when - position) + msg
    position = when
flat_track += b"\x00\xff\x2f\x00"
flat_midi_path = out / "jazz-ballad-eight-bars-flat-dynamics.mid"
flat_wav_path = out / "jazz-ballad-eight-bars-flat-dynamics.wav"
flat_midi_path.write_bytes(b"MThd" + struct.pack(">IHHH", 6, 0, 1, 480) +
                           b"MTrk" + struct.pack(">I", len(flat_track)) + flat_track)
flat_rendered = render_midi(resource, flat_midi_path, flat_wav_path, sample_rate=44100)
assert flat_rendered["audio_rendered"] and flat_rendered["peak_linear"] > 0
assert flat_rendered["frames"] == rendered["frames"], "JAZZ_AB_TIMELINE_MISMATCH"
import hashlib
assert hashlib.sha256(wav_path.read_bytes()).digest() != hashlib.sha256(
    flat_wav_path.read_bytes()).digest(), "JAZZ_AB_WAVEFORMS_IDENTICAL"
print("JAZZ_FLAT_DYNAMICS_COMPARISON_AUDIO_PASS", json.dumps({
    "same_generated_melody_harmony_and_timing": True,
    "flat_velocity": flat_velocity,
    "notes": len(chosen),
    "duration_seconds": round(flat_rendered["frames"] / flat_rendered["sample_rate"], 2),
    "recorded_piano_bank": resource["resource_id"],
    "full_song_3d_verified": False,
}, sort_keys=True), flush=True)

print("JAZZ_BALLAD_EIGHT_BAR_REAL_RECORDED_EXPRESSION_PASS", json.dumps({
    "profile": "Jazz Ballad", "source": "ACTUAL_GENERATED_HARMONY_EVENTS",
    "real_recorded_sample_bank": resource["resource_id"],
    "bars": len(bars_covered), "chord_onsets": len(onsets),
    "midi_note_count": len(chosen),
    "distinct_chords": len(distinct_chords),
    "velocity_levels": len(set(attack_velocities)),
    "velocity_range": [min(attack_velocities), max(attack_velocities)],
    "duration_seconds": round(rendered["frames"] / rendered["sample_rate"], 2),
    "peak_dbfs": round(rendered["peak_dbfs"], 2),
    "rms_dbfs": round(rendered["rms_dbfs"], 2),
    "audio_status": "EIGHT_BAR_PIANO_DIAGNOSTIC_ONLY",
    "full_song_3d_verified": False,
}, sort_keys=True), flush=True)
PY

python composer/runtime/test_midi_initial_cc_bridge.py
python composer/runtime/test_expressive_gesture_bridge.py -v
python composer/runtime/test_instrument_gesture_handoff.py -v
python composer/runtime/test_automatic_phrase_decisions.py -v
python composer/runtime/test_instrument_performance_contract.py
PYTHONPATH=composer/runtime python composer/runtime/test_rock_bass_sustain_policy_v1.py
PYTHONPATH=composer/runtime python composer/runtime/test_rock_melodic_author_v1.py
PYTHONPATH=composer/runtime python -m genre_styles.Rock.test_rock_lead_register
PYTHONPATH=composer/runtime python -m genre_styles.Rock.test_rock_balance_contract
# Exercise the actual genre setup with no audio rendering. A bad palette,
# missing core drum part, or mixed instrument IDs must fail this build rather
# than leave an apparently-live composer that rejects every Rock composition.
python - <<'PY'
from pathlib import Path
import importlib.util, sys
root = Path("composer/runtime").resolve()
sys.path.insert(0, str(root))
source = root / "AI_Comp_Genre_Execution_Adapter_002_WORKING_2026-10-02_184019_CDT.py"
spec = importlib.util.spec_from_file_location("composer_rock_smoketest", source)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
result = module.GenreExecutionAdapter().resolve("ROCK", mode="normal", creation_seed=0)
assert result.get("status") == "PASS", result.get("status")
events = result["events"]
assert events, "ROCK_HAS_NO_EVENTS"
declared = set(result["palette"])
used = {e["instrument_id"] for e in events}
missing = sorted(declared - used)
assert not missing, "ROCK_DECLARED_PART_NOT_GENERATED:" + repr(missing)
required = {"kick_drum_rock", "snare_drum", "hi_hat"}
assert required <= declared, "ROCK_REQUIRED_PART_NOT_DECLARED"
by_track = {}
for event in events:
    by_track.setdefault(event["track_id"], set()).add(event["instrument_id"])
mixed = {k: sorted(v) for k, v in by_track.items() if len(v) != 1}
assert not mixed, "ROCK_MULTIPLE_INSTRUMENT_IDS:" + repr(mixed)
print("ROCK_THEORY_MIDI_ROUTING_CHECK PASS", "events=" + str(len(events)),
      "tracks=" + str(len(by_track)), flush=True)
PY
python composer/runtime/genre_resource_readiness.py
echo "CURRENT COMPOSER BASELINE READY"
