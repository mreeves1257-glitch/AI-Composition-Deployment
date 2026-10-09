# AI Composer — Rock Melody R1 Completed Listening Comparison

**Checkpoint:** October 8, 2026, 7:39 PM CDT (America/Chicago)
**Preserved complete original + musical candidate A/B run:** https://github.com/mreeves1257-glitch/AI-Composition-Deployment/actions/runs/37864520547
**Status:** Completed successful 127-bar real recorded-SFZ stereo 3D audio comparison. Research only. Do not deploy or silently activate.

## Experiment and exact outputs
- Original: 145 BPM, 127 bars, 3,065 score events, full 211.766-sec final 3D WAV.
- Melody R1: 145 BPM, 127 bars, 2,981 score events, full 211.766-sec final 3D WAV.
- Both compositions use the SAME authentic recorded instrument banks, same untouched mixer, same tempo, other instrument note data unchanged.
- LEAD count: 282 -> 198; unique pitches: 6 -> 9.
- Percentage of lead notes from that bar's rhythm-guitar chord: 39.01% -> 87.37%. This is **not** a musical-quality score or proof of subjective improvement.
- Lead timing locations inside a bar: 10 -> 16 distinct onset positions.
- Melody R1 composition module: `composer_overrides/rock_melodic_author_v1.py`.
- Feature flag: `AI_COMP_ROCK_MELODY_V1=1`; absent/off keeps the original score. Actual deployed Composer, plug and control panel remain unmodified.
- Both full songs and independent scores/report are preserved in GitHub Actions artifact #11587572664. Additional listener archive `AI_Composer_Rock_Composition_AB_HARD_SAVE_2026-10-08_1939_CDT.zip` delivered in the conversation Oct 8, with WAVs, MP3s, source score events, comparison JSON, and a dated stopping-point README.

## Important limitations / don't confuse separate experiments
- The user judged the original full Rock composition musically poor but liked the instrument sounds. This experiment preserves the good instrument result; the composer writing is the target.
- R1 is **a candidate**, not an approved musical standard. Listen for memorable melody, good song form, genuine transitions, and expressive development; being within the chord is necessary for much tonal rock writing but insufficient for compelling composition.
- The original score contains duplicated drum hits: 187 redundant KICK note-on events at exact same times and 254 redundant SNARE note-on events at exact same times. R1 deliberately leaves the drum data unchanged; any correction is a separate controlled composition/arrangement decision.
- A distinct, more restrictive chord-tone-only research prototype exists on `rock-composition-research-20261008` and is not part of the finished R1 baseline. Its proposed flag is unique: `AI_COMP_ROCK_CHORD_GRAMMAR_V1`. Do not stack experimental melody composers.
- No live Control Panel-to-Plug-to-Composer-to-audio HTTP handoff or musician listening approval has been demonstrated by these isolated audio research workflows.

## Continue from here
1. Use the two completed A/B recordings to judge melodic musicality without changing instruments or mixing.
2. Keep original frozen. Retain or reject melody R1 by listening, NOT formulaic objective metrics.
3. Separately address duplicate Rock kick/snare note events and deeper song-form/motif quality with a discrete branch and test.
4. Do not work on other genres' activation or new instrument research before Rock composition is coherent.
