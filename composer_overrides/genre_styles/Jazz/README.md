# Jazz family — one heading, eight related genres

This folder is the **only Jazz family home** in the Composer's 13-family organization. Its `profile.json` defines **Swing, Jazz Ballad, Big Band, Jazz Waltz, Bebop, Cool Jazz, Dixieland, and Jazz Fusion**, each with its distinct musical definition, instrument-track reference, individual mix metadata, and seven-stage planning sequence.

**Operational status (2026-10-10 development checkpoint):** Jazz Ballad now passes an isolated full-length Composer MIDI → its own Jazz slot → original recorded SFZ instruments → ordinary stereo WAV test with six original tracks and 931 Composer notes (GitHub Actions run 38027121172). Musical quality remains subject to listening and the live control panel has NOT been deployed or verified. The other seven Jazz subgenres retain verified identity/MIDI inlet connections only; their own complete instrument sources and finished genre audio remain unverified. Preserve past work rather than assuming all eight styles are finished.

## Gathered under this single home
- `jazz_ballad.py`, `harmony.py`, `jazz_arranger_style.py`: prior composition and musical-performance efforts, not proven functional.
- `jazz_balance_contract.py`, `ballad_leveler.py`, `jazz_ballad_mix.json`: prior Jazz-specific mixing work.
- `jazz_ballad_recorded_resources.py`, `instrument_library.json`, `instrument_packages/`: source-onboarding code and per-genre **references**; original recorded samples remain in the shared library.
- `swing.py`, `big_band.py`, `jazz_waltz.py`, `bebop.py`, `cool_jazz.py`, `dixieland.py`, `jazz_fusion.py`: earlier placeholders or incomplete style modules; their differences are retained.
- `test_jazz_arranger_style.py`, `test_jazz_ballad_equal_intensity.py`: diagnostic code; passing unit checks are **not** proof of finished music.

## Architecture
The seven planned stages and handoffs in `profile.json` remain inactive for all eight styles, including Jazz Ballad. All profiles are governed by the same family-filing rules as the other 12 headings. Do not use any Jazz style as a mandatory template for unrelated Jazz genres or Rock.

Separate shared resources and renderer/mixer are linked, not duplicated. Previous revisions and checkpoints remain in Git history. The prior `genre_mix_ratios/Jazz.json` is superseded by **this** `Jazz/profile.json`, not an independent competing Jazz collection.
