# HARD STOP ADDENDUM — Seven Original Stages plus Interpreter → Bridge → Composer → Performance
**Timestamp:** October 8, 2026, 9:24 PM CDT (America/Chicago)
**Status:** DOCUMENTATION ONLY. NO production or musical change.

## Verbatim user architecture correction
- "Do we need the bridge?"
- "So is this, we had seven steps. So this took its place, this setup? The interpreter bridge composer performance. Did we replace that with the, the stuff that we had there?"
- "Well, I hope you save that information because we may need to go back to it and see what else we can pick up."
- "It also had composer and performance."

**Preserve all FOUR explicit labels:** **Musical Interpreter → Translation Bridge → Composer → Performance**.
The user's central question is whether these replace the original seven genre stages. **Answer: NO.** They describe how functions pass information through the already-designed stages, not four competing new or replacement programs.

## Existing original seven steps — exact authoritatively filed order
1. `SELECT_GENRE`
2. `DEFINE_MUSICAL_STRUCTURE`
3. `CHOOSE_INSTRUMENTS_AND_DRUM_KIT`
4. `COMPOSE_SEPARATE_PARTS`
5. `PERFORM_MUSICALLY`
6. `RENDER_SEPARATE_AUDIO_STEMS`
7. `GENRE_MIX_THEN_STANDALONE_3D_MIX`

## Precise relationship
- **Original Stage 2** owns the genre's structural musical instructions.
- **Original Stage 3** owns real recorded instrument/kit selection, resource IDs, SFZ pitch and articulation capabilities.
- **Musical Interpreter** receives the stage-2 style/form/phrase/section intentions plus stage-3 instrument capabilities and produces a coordinated musical arrangement plan **at the handoff from stage 3 to stage 4**.
- **Translation Bridge** maps that arrangement/MIDI plan to this Composer's *specific* part/track IDs, recorded-source key mappings, supported articulations, synchronized onsets/durations/roles. This **translation behavior is necessary**, but a second permanent standalone program may NOT be necessary: first reuse/extend the current Composer handoff/adapter if sufficient.
- **Composer = ORIGINAL STAGE 4 `COMPOSE_SEPARATE_PARTS`**. It composes/materializes distinct synchronized parts and note instructions. It is NOT removed or replaced by the Interpreter or the Bridge.
- **Performance = ORIGINAL STAGE 5 `PERFORM_MUSICALLY`**. It applies recorded-instrument-aware phrasing, articulation, accents, sustain, mutes, source-supported controls, expressive dynamics and musicianship. It is NOT removed or replaced.
- **Original Stage 6** renders each recorded-source part to its own independent real-audio stem.
- **Original Stage 7** handles per-genre balance then passes to the *existing standalone 3D mixer*, which remains the last processing component.

### Schematic (four terms intact, original seven steps kept)
```text
[1 Select Genre]
        |
[2 Define Musical Structure]
        |
[3 Choose Instruments & Drum Kit]
        |
  MUSICAL INTERPRETER
        |
  TRANSLATION BRIDGE
        |
[4 COMPOSER: Compose Separate Parts]
        |
[5 PERFORMANCE: Perform Musically]
        |
[6 Render Separate Audio Stems]
        |
[7 Genre Mix → Standalone 3D Mixer]
```

The interpreter and bridge are **subfunctions of a stage-3→4 handoff**, not eighth/ninth mandatory active production stages. Do not duplicate existing composition or performance mechanisms. Real-world source-sounding notes may require performance messages planned earlier; clarify the single ownership before wiring.

## Evidence versus uncompleted integration
- An isolated GPL-external official MMA experiment proved **Rock arrangement MIDI → original bridge mapping → distinct real Karoryfer SFZ recordings → unmodified 3D mixer** and sounded drastically better to the user.
- The -8 dB electric-bass attenuation is the user's **provisional preferred listening version** of that exact 16-bar Rock experiment, saved separately, NOT a global Rock or live Composer configuration.
- **No piano/keyboard** was included in this 16-bar sample demo; its keyboard-like accompaniment was actually the Shinyguitar rhythm-guitar chord part, and explicit human guitar articulation is still unfinished.
- Current handoff reference paths for **all 55 genres** in 13 families are documented as inactive. No auto-activation, no final 55-genre functionality claim.
- The stand-alone Rock experiment is **not proof** that Interpreter→Bridge→Composer→Performance are already functioning as four fully integrated new modules in the live system. Those labels are the required target information flow; stage-4/5 should continue as originally planned.

## Resume questions to audit later (DO NOT execute tonight)
1. Which translation behavior is ALREADY implemented in Stage 3's chosen-source mapping and Stage 4's existing adapter? Keep it and add only what is missing.
2. How exactly does Stage 4 read an interpreted part/phrase plan without duplicating the original composer?
3. How does Stage 5 apply supported human expression—including realistic chord strum offsets, source articulations, note lengths, vibrato, shared rhythmic timing—without changing the chosen genre language?
4. How do kick and bass preserve deliberate anchors without masking one another?
5. How do Stage 6's independent source stems and Stage 7's per-genre mix plus separate final 3D mixer remain protected?
6. For all 55 genres, does the same handoff interface permit truly different musical grammars and optional instrument roles?

## XRefs and immutable references
- Original per-genre `seven_stage_plan`: `composer_overrides/genre_styles/*/profile.json`.
- Stage-slot decision: `research/GENRE_MUSICAL_INTERPRETER_STAGE_PLACEMENT_2026-10-08_2029_CDT.md`.
- Generic interface: `composer_overrides/genre_styles/GENRE_ARRANGER_INTERPRETER_HANDOFF_REFERENCE_R1.json`.
- Rock slot: `composer_overrides/genre_styles/Rock/ROCK_ARRANGER_INTERPRETER_PLACEMENT_R1.json`.
- All-55 handoffs: branch `genre-interpreter-all-55-20261008`.
- Exact preferred Rock listening balance: `research/ROCK_USER_SELECTED_BASS_MINUS_8DB_WORKING_BALANCE_2026-10-08.md`.
- Earlier hard stop: `research/HARD_STOP_ROCK_INTERPRETER_MINUS8DB_ALL55_2026-10-08_2117_CDT.md`.
- No current Composer, Plug, Control Panel, sample resource, 3D mixer, live service, or executable workflow changes in this addendum.

**STOP HERE. Preserve all four named functions and original seven steps together for later investigation.**
