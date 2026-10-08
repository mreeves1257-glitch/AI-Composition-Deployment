# Existing Percussion Work — Reuse, Do Not Rebuild
Checkpoint: 2026-10-08 18:46 CDT (America/Chicago)
Status: reference only; no runtime connection or merge.

Another existing research branch `recorded-instrument-control-inventory-2026-10-08` contains:
- `composer_overrides/recorded_percussion_performance_map.json`
- `composer_overrides/recorded_percussion_strike_interpreter.py`
- `composer_overrides/test_recorded_percussion_actual_audio.py`
- `.github/workflows/recorded-percussion-layer-audio-proof.yml`

That branch maps explicitly authored drum-hit intent (ghost, soft, accent, strong and dynamics) to velocity layers/round-robin source mappings of selected actual Big Rusty drums. Its source-specific actual-sound study found different rendered snare waveforms, including a severe level difference between very soft and strong hits. Consequently musical loudness calibration is still pending. It is NOT an approved completed genre drummer and is NOT active in the Composer.

Avoid creating a parallel drum interpreter. Any future performance-language orchestration should reference this existing map and verify exact resource identity, action-to-sample consistency and source-specific loudness. Do not copy modules onto main or silently enable them.

Current separate task: original Rock bass generated phrase A/B study on same Growlybass clean SFZ, with only MIDI note release altered. All genre connections remain inactive and live services unchanged.
