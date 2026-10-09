# ROCK STAGE-4 ORIGINAL RUNTIME INTEGRATION — VERIFIED INTERFACE REPAIR

**Date:** October 9, 2026  
**Development branch:** `rock-stage4-identity-contract-20261009`  
**Original frozen hard copy:** `hard-copy-ai-composer-2026-10-09-1128-CDT` (preserved, **not changed**)  
**Successful verified CI:** https://github.com/mreeves1257-glitch/AI-Composition-Deployment/actions/runs/37977137766  
**Earlier whole-machine connection map:** `research/VERIFIED_ENTIRE_MACHINE_CONNECTION_MAP_2026-10-09_1342_CDT.md`.

## Exact corrected boundary
The separate original-source Stage4 note proposal mistakenly wrote `instrument_id="electric_guitar:RHYTHM_POWER_CHORDS"`, which is **a TargetProgram recording/resource lookup key**, not a physical instrument ID recognized by `InstrumentProgram`. A test using the extracted original `composer/runtime.b64` InstrumentProgram reproduced the rejection: `INSTRUMENT_PROFILE_MISSING::electric_guitar:RHYTHM_POWER_CHORDS`.

The one shared `source_pattern_composer_handoff.py` now writes `instrument_id="electric_guitar"` (the physical instrument), and separately attaches `expected_target_binding_id="electric_guitar:RHYTHM_POWER_CHORDS"` as audit metadata. The original `InstrumentProgram.resolve_events` transforms the physical instrument and HARMONY track into role `RHYTHM_POWER_CHORDS`; the original `TargetProgram.resolve` then selects that exact recording program. No legacy engine files or original Rock source were changed.

## Actual preserved original Composer tested (not a mocked engine)
The isolated test `research/test_real_stage4_instrument_target_contract_20261009.py` extracted from original `composer/runtime.b64` the authentic `instrument_program.py`, `target_program.py`, `performance_executor.py`, `output_handoff.py`, `AI_Comp_Executable_Output_Core_001.py`, and original instrument/target registries.

With *explicit* source identity and licensing fixture values pinned to the October 9 build script, the separate proposed Rock score of **102 notes / five tracks** passed:
1. Actual original `InstrumentProgram.resolve_events` — PASS, five distinct parts.
2. Actual original `TargetProgram.resolve` — PASS: correct recorded Growlybass, Shinyguitar rhythm-guitar, Big Rusty kick/snare/hat program IDs. These are **source identity fixtures**, not installed sample graph proof.
3. Actual original `PerformanceExecutor.execute` — PASS, preserved all notes unmodified.
4. Actual original `output_handoff.build_execution_package` plus `OutputManager.execute` and `write_output_package` — PASS, produced an actual isolated Standard MIDI file (Type 1, 480 ticks per quarter note) with 102 score notes in five separate instrument tracks and a conductor track. File header and track separation verified. **No recorded audio was rendered or routed to the Plug.**

## Authoritative source program pitch-zone check
`research/test_rock_source_sfz_keyzone_authority_20261009.py` read public, commit-pinned original **SFZ program text** from:
- Karoryfer Growlybass `4f483268fc66b5a6d5781d421c0d11b8d08d3fc6`: bass melodic sample-key coverage **MIDI 33–79** in the checked program zones. Keys used in this 7-bar seed: 36, 38, 40, 43, 47, 50. Separate scrape-effect triggers excluded.
- Karoryfer Shinyguitar `57243cca85277dbcc120ce17c6178032f93c80f3`: `Programs/electric_one.sfz` coverage **MIDI 33–91** under the original program's controller defaults, including actual authored Harmony notes 60, 62, 64, 66, 67, 71.
- Big Rusty original Composer-generated isolated SFZ programs: KICK note 36, SNARE note 38, HAT note 42; actual per-track seed note values match exactly.
- **102 of 102** notes have corresponding note numbers in the cited source program zones. Key-zone coverage does **NOT** demonstrate that the exact WAV/FLAC sample bytes exist on today's deployed instance, every velocity/round-robin layer plays, that full arrangements are present, or that expressive musical playing is correct.

## Catalogued missing physical instrument identities across all 55 genres
A second real-code check against original `instrument_library.json` found **66 source-pattern role assignments using 13 physical instrument names not currently recognized as-is** by `InstrumentProgram`, including its existing documented aliases:

| Source pattern instrument ID | Role assignments | Decision |
|---|---:|---|
| acoustic_bass | 17 | Investigate `double_bass` original sound identity; no automatic remap |
| clave | 8 | Need exact sampled instrument ID and recording |
| hand_clap | 7 | Need percussive recording/program identity |
| hi_hat_electronic | 7 | Need electronic kit/sample program identity |
| kick_drum_electronic | 7 | Need electronic kit/sample program identity |
| kick_drum_soft | 6 | Source needs style-appropriate recorded kick program; do not assume Rock kick |
| nylon_guitar | 4 | Need verified instrument profile and native recorded nylon sample |
| brush_snare | 3 | Some Jazz Ballad brush recordings exist in original live audio; reconcile exact instrument and role |
| banjo | 2 | Need native bank/program; do not borrow guitar sound |
| hand_drum | 2 | Need specific native drum type and source program |
| horn_section | 1 | Need explicit section instrument program / real sample policy |
| choir_pad | 1 | Needs a legitimate recorded choir/pad source, not a generic oscillator |
| string_ensemble | 1 | Need explicit source instrument palette/profile |
| **TOTAL** | **66** | **NOT YET RESOLVED; NOT ENABLED** |

These 66 are **physical catalogue-name mismatches**, a different level of the earlier **130 unverified recorded-program role references**. Counts must NOT be added together as if independent: they overlap.

## Strict next integration gates
1. Check installed runtime **SFZ + every referenced sample file**, chosen note + velocity layer, held note/release and guitar controller behaviors for these five Rock sources. Existing October 8 Render logs show original Rock source audio, but do not constitute a new-pattern recording test.
2. Add independently authored lead-guitar, tom, ride and crash musical parts before calling a Rock score complete. Existing source-pattern seed has BASS/HARMONY/KICK/SNARE/HAT only. The original Rock audio also has a separate subkick output derived after the kick recording.
3. Independently render/stem-test the seven-bar Rock source proposal behind a development gate **without** changing the authoritative original `theory['events']`; inspect natural bass sustain, vibrato, drum depth and phrasing.
4. Then, only on explicit review, enable original seven-stage flow for the new candidate and retest standalone independent 3D mixer/Plug/phone return.
5. For remaining genres, resolve physical names and recording banks individually, not via generic fallback.

## What this work did NOT do
- **No** live production deployment or Render setting change.
- **No** user-facing score replacement, sample recreation, original Rock overwrite, Plug edit, Control Panel edit, Portal Four, additional interpreter or eighth stage.
- **No** audio rendered or human listening certification.
- Original hard-copy October 9 11:28 CDT remains unchanged. This is a **development interface checkpoint**, not a new complete hard-copy ZIP. At next user-requested hard copy, include downloadable copy for the user as required.
