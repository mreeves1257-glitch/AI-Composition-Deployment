# Rock Composition — Drum Collision and Remaining Melody Audit

**Checkpoint:** 2026-10-08 (America/Chicago)
**Based on:** preserved full-song `melodic_v1/score_events.json` from the verified Oct 8 19:39 CDT Rock Composition R1 audio hard save.

## Drum collisions: verified, not speculative

The 127-bar Melody R1 music has 559 KICK events, 508 SNARE events, 684 HAT events and 21 TOMS events. An exact onset/pitch/track collision check found:
- KICK: 187 pairs. Each pair contains one original `kick` articulation and one supplemental `rock_kick` articulation.
- SNARE: 254 pairs (all 254 backbeats). Each pair contains one original `snare` articulation and one supplemental `rock_backbeat` articulation.
- HAT and TOMS: zero such collisions.

The supplemental percussion was explicitly appended by `genre_development_patch.develop_full_length` to ensure a punchy audible Rock groove, but did not first check whether the original score already placed a hit at that onset and pitch. These collisions may retrigger the same SFZ program and are a compositional *arrangement concern*, distinct from source sample fidelity.

## Controlled experimental remedy

The new `composer_overrides/rock_drum_collision_policy_v1.py`, **OFF BY DEFAULT**, resolves ONLY the exact known two-event pair (legacy + supplemental) when `AI_COMP_ROCK_DRUM_COLLISION_V1=1`. It retains the existing supplemental `rock_kick` or `rock_backbeat` unchanged, including its registered sample, pitch, velocity, onset, and duration. It never changes an unpaired hit, a third simultaneous voice, hats, toms, bass, melodic lines, rhythm guitar, or another genre. No instrument, sample, gain, mixer or 3D code changes.

The feature is called in the post-composition Rock performance stage *after* baseline genre expression and after the independent bass flag. No other existing flags are enabled by the change. Verify exactly 187+254=441 event removals on Melody R1, plus full real recorded-source/3D audio, before treating this as working. A listening comparison is still necessary; less sample retriggering is not itself artistic approval.

Test: `composer_overrides/test_rock_drum_collision_policy_v1.py`; A/B runner: `research/run_rock_drum_arrangement_ab_v1.py`. Neither contains production deployment.

## Separate remaining long-form composition limitation

From the same preserved Melody R1 score, 198 LEAD notes occupy 47 active bars, with 16 distinct exact pitch patterns and 12 distinct contour patterns. A four-note `(65,65,65,65)` phrase appears eight times, and several other contours also repeat nearly identically. Chord-tone alignment improvement does not automatically create expressive, memorable form. Theme introduction, recall, development, contrast and phrase-to-phrase harmonic movement must be evaluated separately, NOT conflated with percussion collision cleanup.

**Protection:** Original working R1 and completed recordings retained; research branch `rock-drum-arrangement-research-20261008`; live plug/control panel/composer untouched; original SFZ banks and standalone 3D mixer untouched.
