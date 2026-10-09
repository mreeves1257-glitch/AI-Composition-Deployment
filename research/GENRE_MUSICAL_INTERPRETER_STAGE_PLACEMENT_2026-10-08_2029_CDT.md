# Musical Interpreter — placed within existing genre flow

**Date and time:** October 8, 2026, 8:29 PM CDT (America/Chicago)
**Branch:** `external-arranger-interpreter-research-20261008`
**Status:** RESEARCH REFERENCES FILED, STRUCTURE VALIDATION PASSED; NO RUNTIME ACTIVATION
**CI verification:** https://github.com/mreeves1257-glitch/AI-Composition-Deployment/actions/runs/37869967846

## User's structural insight
"The were the the genres is a list of progression of how it's supposed to flow. So maybe it needs to be put in there."

**Decision:** That is the correct architectural location: honor the established per-genre seven-stage progression and file the new musical-arrangement interpreter as a *handoff component*, not another competing standalone master, universal genre override, or eighth activated stage.

## Exact existing stage order (preserved)
1. SELECT_GENRE
2. DEFINE_MUSICAL_STRUCTURE
3. CHOOSE_INSTRUMENTS_AND_DRUM_KIT
4. COMPOSE_SEPARATE_PARTS
5. PERFORM_MUSICALLY
6. RENDER_SEPARATE_AUDIO_STEMS
7. GENRE_MIX_THEN_STANDALONE_3D_MIX

The **Musical Intent/Arranger Interpreter** receives style, structure, harmony, phrase and beat plan from #2 and exact available instrument/sample bindings from #3. It compiles those into synchronized, executable **per-part** performance plans that #4 can compose into note events. Stage #5 remains responsible for source-specific articulations and performance gestures. Stages #6 and #7 remain recorded-source rendering and final independent 3D mixing.

The distinction is crucial:
- Stage #2 describes musical goals in the appropriate genre.
- Stage #3 confirms the real sounds and instruments available.
- The intermediate interpreter turns those goals into an actionable coordinated band plan, with rolls, fills, accents, cadence, response and section transitions for the actual available resources.
- Stage #4 creates independent synchronized instrument parts, avoiding the old constant beat-only rock arrangement.
- Stage #5 interprets each instrument's source-supported playing technique.

## New controlled reference files (no changes to existing genre profiles)
- `composer_overrides/genre_styles/GENRE_ARRANGER_INTERPRETER_HANDOFF_REFERENCE_R1.json`: genre-neutral seven-stage handoff contract and typed input/output aspirations.
- `composer_overrides/genre_styles/Rock/ROCK_ARRANGER_INTERPRETER_PLACEMENT_R1.json`: Rock-specific plan and authorized existing track roles (KICK, SNARE, HAT, TOMS, CRASH, RIDE, BASS, HARMONY, LEAD), musical intentions and safeguards, explicitly dormant.
- `research/validate_genre_arranger_slot_r1.py`: original-file read-only structural verifier.

## Verification
GitHub Actions #37869967846 **succeeded** and printed `GENRE_INTERPRETER_STAGE_SLOT_REFERENCE_PASS`: all 13 existing genre folders, 55 original profiles, every existing seven-stage order, and all six reserved handoffs unchanged/unactivated. The two new files are *research references*, NOT executable interpreter installation.

## Pre-existing external interpreter research
- Official original MMA 25.05.0 source checksum verified; independently ran 8-bar Rock accompaniment command producing separate MIDI tracks; MMA's original GPL license must be respected.
- JJazzLabToolkit Java-source research artifact retained, not integrated.
- Original source package checkpoint: `research/EXTERNAL_INTERPRETER_FETCH_AND_REAL_MIDI_PROOF_2026-10-08_2024_CDT.md`
- Treat external source as a separately versioned library/reference, not embedded/silently copied into current genre modules.

## Next limited experiment
Implement a **translator prototype** for an eight/sixteen-bar Rock fill/pickup/arrival: read Rock section intent from Stage #2 and capability mapping from Stage #3; use isolated MMA-generated MIDI reference to produce safe per-part score events for Stage #4. Explicitly validate samples/pitches, real timed rolls/toms, synchronized bass/guitar accents. Render each stem using the already preserved recorded SFZ banks and untouched 3D mixer, then audition beside the user's positively reviewed cleaned-drum recording. Do not assume MIDI channel 10 General MIDI maps directly to source SFZ piano-roll keys; do not import GPL code into user composer without licensing evaluation.

## Protection
No live Composer, Plug, Control Panel, genre activation flags, original profile.json files, existing SFZ/WAV banks, instrument levels, master/stems, or 3D mixer changed. User-preferred Rock audibility and earlier dated hard-copy archives remain frozen.
