# Rock rhythmic-composition research — quarter/eighth/sixteenth distinction

**Date:** October 8, 2026 (America/Chicago)  
**Study branch:** `rock-groove-motion-research-20261008` (separate from Melody R1, musical storytelling V2, and the protected live Composer).

## User's identification
The user hears the Rock drum strikes as repetitively landing on every beat, creating an unexpectedly slow feeling despite 145 BPM. They liked that the separately cleaned-up drum recording made every instrument clearly audible and sounded much better, but its timekeeping was too regular. Preserve that **actual listened-to balance and clarity**.

## Evidence in verified 127-bar score of their preferred cleaner-drum arrangement
- Kick: 127 downbeats at beat 1 and 127 beat-3 anchors, with some existing offbeats.
- Snare: exactly 127 strikes on beat 2 and 127 on beat 4, repeating without variation across every bar.
- Hi-hat: 127 strikes each on 1, 2, 3, and 4, with only 40–48 occurrences of each eighth-note offbeat (0.5, 1.5, 2.5, 3.5 beats); some existing eight-note passages.
- Bass: 254 notes, mostly two per bar; sometimes late offbeats at 2.25 beats.
- Existing exact simultaneous drum collision cleanup removes 187 redundant kicks and 254 redundant snares; test passed and user preferred its sound.

**Theory distinction:** Quarter, half, eighth and sixteenth notes are musical duration/subdivision values. Real drum samples are largely one-shot sounds whose perceptual pacing depends on the strike's *onset, subdivision, accent and rests*, not merely changing MIDI note-off lengths. Rock can still use anchored backbeats, but constant unchanged 1-3 kick and 2-4 snare + quarter-note hats across every bar sounds schematic.

## Actual new gated experiment
- `composer_overrides/rock_groove_motion_v1.py`, **OFF by default** via `AI_COMP_ROCK_GROOVE_MOTION_V1=1`, and **requires** `AI_COMP_ROCK_DRUM_COLLISION_V1=1` so the original doubly triggered drum sounds can never be the basis accidentally.
- Introduces **audibly lower-velocity eighth-note hi-hat subdivisions** with selective sixteenth-note turnaround hits. Existing hi-hat events remain identical and all new events use the same original Karoryfer recorded hi-hat resource, MIDI key 42, exact original articulation and unchanged mixing.
- Makes selected additional offbeat KICK at 2.5 beats anticipate at 2.25 **only where a real existing BASS hit is at 2.25**, to express bass–kick rhythmic interplay. No extra kick note count or stronger kick volume; quarter anchors preserved.
- All existing SNARE, LEAD, HARMONY, BASS, TOMS, RIDE, CRASH events and samples unchanged, as is BPM 145 and standalone 3D mixer.
- Do not infer any musical preference from a successful rendering. User gets a new complete full-song recording to compare against the cleaner-drum baseline.

Tests: `composer_overrides/test_rock_groove_motion_v1.py` and full recorded real-SFZ A/B `research/run_rock_groove_motion_full_audio_ab.py`. Workflow: `.github/workflows/rock-groove-motion-full-audio.yml`, run #37867790315.

The original 3:31.8-song baseline and the cleaned-up drum listening master are preserved as checkpoints, not replaced. No deployment, plug, control panel or 3D mixer change is authorized by this experiment.
