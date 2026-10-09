# Rock composition diagnosis and protected next stage

**Hard checkpoint:** 2026-10-08 19:23 CDT (America/Chicago).

**User assessment after hearing complete 3D Rock WAV:** Recorded instruments sound good; the musical composition is poor. Treat this as a confirmed listening assessment, not an instrument or sound-bank failure. Preserve the completed original full-song audio and all source/sample/performance baselines. Pivot only to composition quality. 

## Measured musical score shortcomings

Analyzed the **actual full Rock score** saved in the verified 2026-10-08 complete-song archive, not a constructed example:

- Rock original: 127 bars, 145 BPM, 3,065 total note events across 9 score tracks (plus separate 3D sub-kick derivative).
- LEAD: **282 notes made from only six distinct MIDI pitches**. Each of those six appears exactly **47 times**. The 47 active lead bars each have exactly **six notes** and broadly regular six-to-a-bar timings. Musical motif development is overwhelmingly schematic.
- Approximately **110 of 282 lead notes (39%)** share pitch classes with the simultaneous bar's HARMONY (rhythm guitar) chord-tone set, calculated from the saved score. Non-chord melody notes can be intentional; this statistic is not an independent quality score. In context of the rigid six-pitch rule, however, it illustrates the missing chord-sensitive melody decisions.
- The original generator in the preserved `AI_Comp_Genre_Execution_Adapter_002_WORKING_2026-10-02_184019_CDT.py` emits Rock LEAD from repeating `pattern=[0,2,4,5,3,1]` with six equidistant attacks every alternate bar, without consulting the current chord or designing an answering phrase. The genre developer mostly shifts timing, velocity, and density.
- The same saved score includes **187 simultaneous duplicated KICK pitch/onset events** and **254 simultaneous duplicated SNARE pitch/onset events**. That is a separate percussion-arrangement issue; not caused by the underlying sample recordings. DO NOT fix drums during the current melody-only controlled A/B.

## Research melody composer — completely separate from original version

File `composer_overrides/rock_melodic_author_v1.py`. New gate `AI_COMP_ROCK_MELODY_V1=1`, **OFF by default**; all absent/other values preserve the old score. The author is called only in Rock, immediately before the existing guitar/instrument-performance stage of `genre_development_patch.develop_full_length`. When enabled:
- Only existing active Rock LEAD bars are rewritten; bars originally silent stay silent.
- Replaces uniform six-note runs with short A-call/A-answer/B-lift/reprise/cadence motifs and varied rhythmic positioning.
- Uses existing chord notes as phrase anchors and destinations, the existing key scale for intermediary movement, and bounded guitar register (MIDI 59–76).
- Maintains deterministic behavior and existing seed parameter.
- Preserves bass, drums, chord/rhythm guitar, instruments, recorded sample banks, plug, panel, final 3D mixer and genre structure without modification.
- It is an **experimental musical candidate**. Better melody metrics or successful rendering do not prove that it sounds like good Rock music.

Files `composer_overrides/test_rock_melodic_author_v1.py`, `research/run_rock_composition_melody_ab_v1.py`, workflow `.github/workflows/rock-melody-composer-audio-research.yml` provide score identity and real stereo A/B with other tracks protected. The previous Rock bass note-off candidate remains separate and OFF in both melody comparisons.

## What remains

Listen to the actual full 3D A/B when available and judge musical structure, tension/resolution, phrasing and emotional development rather than treating numerical metrics as a musical verdict. Later, examine duplicate rhythmic hits separately with isolated regressions if the composition still feels wrong. Do not activate all reserved genre links or touch the control panel/plug in a melody investigation. Do not merge research into production before artistic and complete technical validation.

**Research branch:** https://github.com/mreeves1257-glitch/AI-Composition-Deployment/tree/performance-language-research-20261008
