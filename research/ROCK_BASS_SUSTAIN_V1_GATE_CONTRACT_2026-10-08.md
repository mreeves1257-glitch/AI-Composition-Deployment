# Rock Bass Sustain V1 — Feature Gate and Safety Contract

**Date:** 2026-10-08 (America/Chicago)  
**Development workspace:** `performance-language-research-20261008`  
**Code:** `composer_overrides/rock_bass_sustain_policy_v1.py`  
**Integration:** `composer_overrides/genre_development_patch.py`, AFTER the preserved `instrument_performance_contract.perform` and Rock expression functions.  
**Source experiment:** see `research/ROCK_BASS_REAL_WAV_PROOF_2026-10-08_1852_CDT.md` and `research/ROCK_FULL_3D_MIX_SUSTAIN_AB_PROOF_2026-10-08_1859_CDT.md`.

## Activation

OFF by default. Feature flag: `AI_COMP_ROCK_BASS_SUSTAIN_V1=1`.

Anything other than literal `1` (including absent, `0`, `true`, or `on`) keeps original notes. The flag affects ONLY genre `ROCK`, track `BASS`, and recorded bass instrument IDs `electric_bass_guitar` / `electric_bass`. No control-panel input was added. The separate plug/composer/3D architecture stays as before. This is a laboratory gate; DO NOT set it on the deployed Render service before listening evidence and end-to-end completed audio proof.

## Exact candidate rule

For each Rock bass note, identify the next DISTINCT bass attack in the existing score.
- Leave short explicit articulations (`mute`, `staccato`, `short`, `chop`, `pizz`, `stop`, `ghost`, `dead`) unchanged.
- Leave rapid playing with next attack less than 0.8 beats away unchanged.
- Leave suspected phrase gaps greater than 2.5 beats alone; do not invent continuous sustaining.
- Where attack spacing is 0.8–2.5 beats, candidate note duration is `min(1.5, 0.78 * next_attack_spacing)` beats, but only when it extends the source note by at least 0.14 beats.
- Leave the final note unchanged because its intended end cannot be inferred from the next attack.
- Retain every note onset, pitch, velocity, original resource, mixing configuration and separate 3D master.

**Scientific status:** Source audio confirms early MIDI note-off was audibly curtailing recorded bass sustain; independent full-band A/B produced real recorded instrument stereo derivatives with 16 adjusted bass notes and 6 untouched non-bass parts. Candidate artistic preference is not established; full completed song is not yet verified.

## Verification

- Standalone tests: `composer_overrides/test_rock_bass_sustain_policy_v1.py`
- Real full composition scoring comparison: `research/test_full_rock_bass_policy_v1.py`
- CI workflow: `.github/workflows/rock-bass-feature-gate-proof.yml`
- Rebuilt original composer and verifies no-flag default, source routing, exact preservation of all non-bass events. Reports hard evidence.
- Rollback: remove/unset `AI_COMP_ROCK_BASS_SUSTAIN_V1`, no changes to original sample library or source file.

**Do not treat this research branch as a deployable production release.**
