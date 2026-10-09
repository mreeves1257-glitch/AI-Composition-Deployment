# Rock Musical Storytelling V2 — controlled songwriting experiment

**Checkpoint date:** 2026-10-08 (America/Chicago).

## Protected existing work
- Rock instrument sound and approved original recorded SFZ/WAV libraries are intact.
- Completed full original and Melody R1 127-bar 145-BPM stereo recordings remain archived in earlier dated hard saves.
- The first Melody R1 full 3D song is a listening candidate, not a user-approved musical master.
- Rock drum duplicate-hit correction has independently **passed** real full-song A/B (Actions run 37866443990). It removed 187 duplicated KICK and 254 duplicated SNARE note-on events, exactly 441, while retaining all non-kick/snare notes and all original recorded instruments. That fix is isolated, OFF by default, and is **not folded into this story experiment**.
- Production Composer, external plug, control panel and standalone 3D mixer are not modified.

## The user's direction
The user's priority is the quality of **composing music**: an intelligible musical idea, a melody that develops, phrases that answer, variation, tension/release, transitions, identity, and an overall satisfying arc. Their judgment was that the instruments sound good but the composition does not. Do not chase sound banks, volume, more instrument software or arbitrary extra genres to remedy writing.

## Composition experiment isolation
- Branch `rock-musical-storytelling-v2-20261008` derives from protected `performance-language-research-20261008`.
- Module `composer_overrides/rock_story_arc_v2.py`.
- Exact second flag `AI_COMP_ROCK_STORY_V2=1` alone is **not sufficient**: also requires `AI_COMP_ROCK_MELODY_V1=1`; all missing/other values preserve original. There is no accidental combination with `AI_COMP_ROCK_CHORD_GRAMMAR_V1` from a different research branch.
- V2 happens in the original composition development before unchanged guitar performance, note rendering, recorded sample libraries, and separate final 3D mixer.
- User's previously authored Rock lead entry/rest bars remain respected; other instruments have exactly the same notes, velocities, timing, resources, and bindings.
- Explicit form development: intro, verse, recognizable chorus hook, verse variation, hook return, contrasting bridge, final chorus return, outro. Shapes use source music's actual chord roots/tones and key scale, not randomly emitted MIDI or unrelated equal-size six-note runs.
- The candidate is a modest rule-based songwriting experiment; it is not proven artistically good, human-composed, or genuinely expressive until an informed listener judges the full recording.
- V1 vs V2 full recorded 3D A/B source and proof script: `research/run_rock_story_v2_full_song_ab.py`.
- Workflow: `.github/workflows/rock-story-v2-full-song.yml`, GitHub Actions #37866888426.

## Research boundaries
Keep Melody R1 baseline, new storytelling experiment, and separate drum cleanup as **three separate choices**. Only combine changes when independent listening warrants it, and then run a controlled combined A/B. Never deploy speculative research to the live system or activate untested genre links.
