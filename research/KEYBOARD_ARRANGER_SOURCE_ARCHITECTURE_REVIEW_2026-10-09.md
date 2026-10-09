# Keyboard Arranger Source Architecture: October 9, 2026
Status: READ-ONLY SOURCES + INDEPENDENT MIDI TESTING. NO LIVE COMPOSER CHANGES.

## A. Cadenza / most directly relevant Yamaha-style arranger
Original: https://github.com/Piskocis/Cadenza
Exact commit: 47da8f71670daa4caa1b3db2bf8f60a323f6c6b1
GPL-3.0 research source, separately preserved with LICENSE and docs. Do NOT paste or combine its code into a closed-source Composer without licensing review.
Distinct capabilities: chord detection; Yamaha CASM/Ctab interpretation; root transposition NTR; chord-quality note transposition NTT; held-note retrigger, stop or shift RTR; source-playable note bounds; intro/main/fill/ending conductor; original multi-part MIDI. See upstream IMPLEMENTED.md and tests.
Original application is JUCE C++ / Windows using SoundFont by default, not a tested Linux sample-backed replacement for our Composer.
Candidate gaps from our 22: 02-09, 10, 20. This mapping is a RESEARCH HYPOTHESIS, not installed behavior.

## B. Backing Tracks / readable composition sequences
Original: https://github.com/ako/backing-tracks
Exact commit: 534b7be0d07595121a9e782c8793244604a1cd41
MIT license source and attribution retained. Provides BTML Yamaha-like style/section/chord plan, bass walking/root patterns, kit drum pulses, strum/fingerpicking patterns, MIDI exports and per-genre styles. Go compiled CLI can be independently tested.
Precise limitation: source midi/generator.go hard-codes ticksPerBar=1920 at 480 PPQ, effectively 4/4. NOT suitable for 3/4 jazz waltz without fixing/testing meter. GM drums not automatically our specific SFZ real kick/snare. Programmatic chord events can sound keyboard-like unless actually strummed.
Candidate gaps: 02,03,08-10,12,18,20-21. No production deployment.

## C. Impro-Visor / jazz style and musical grammar
Original: https://github.com/Impro-Visor/Impro-Visor
Exact commit: 550bbb554962249aceb0e82a72142e3e5b3c0d4a
GPL-2.0; selected source only: src/imp/style, src/imp/lickgen, src/imp/roadmap, src/imp/voicing, LICENSE, README. No artist phrase corpora, leadsheets, sound banks or installers.
Why useful: jazz harmony/voicing and phrase grammars, accompaniment styles, responding melodies rather than blind loops. Not a universal engine for 55 genres and not tested against exact recorded SFZ resources.
Candidate gaps: 02-03,07-10,12,14.

## D. ALREADY ACQUIRED (do not duplicate)
JJazzLab Toolkit 5.2.1 LGPL-2.1 actual engine JAR plus source JAR; needs Java25 and isolated runtime proof.
music21 10.5.0 music theory and harmonic score algorithms, not a complete arranger.
mingus 0.6.1 GPL-3.0 chord and MIDI library; keep licensed research separate.
MMA 25.05.0 GPL independent interpreter and the strongly preferred real Rock MIDI-to-SFZ proof.
All software above is in already saved and validated dated October 8/9 research hard archives.

## E. Proprietary arranger keyboards
Yamaha Genos2, Korg Pa5X, Ketron Live Modeling, Roland Style Composer, Casio arranger: their documented musical sequence behaviors are useful, but no manufacturer firmware/code/styles/samples are taken or redistributed. We cannot assume they are portable software libraries.

## Exact ORIGINAL seven-stage genre procedure, not replaced
1 SELECT_GENRE
2 DEFINE_MUSICAL_STRUCTURE
3 CHOOSE_INSTRUMENTS_AND_DRUM_KIT
  RESERVE musical interpreter and source-aware translation handoff between 3 and 4
4 COMPOSE_SEPARATE_PARTS (existing Composer)
5 PERFORM_MUSICALLY (existing Performance)
6 RENDER_SEPARATE_AUDIO_STEMS (existing recorded SFZ sources)
7 GENRE_MIX_THEN_STANDALONE_3D_MIX (existing mixer)

The original 55 genres have 22 capability requirements FILED and INACTIVE, not 55 implemented output engines. Every musical rule must be genre-specific; conditional checks prohibit instrument behavior with no selected playable instrument (guitar without guitar, drums in solo piano, or Rock logic in Jazz).

## ACTIONABLE MODULES to investigate and test individually
1. Chord and section timeline conductor (source of harmonic truth)
2. Role-aware chord note-transformation (NTR/NTT/RTR) with register bounds
3. Song-section/fill/break/ending transitions and shared rhythm clock
4. Instrument-specific musical phrasing, human guitar voicing/strum, bass and drum expression; no random independent jitter
5. Per-bank SFZ MIDI capability map, per-track valid notes and exact real sample stems
6. Independent audible comparison with existing 3D mixer and protected selected reference.

This is not authorization to replace existing project programs, mix balance, samples or deployed services. The exact user-preferred 16-bar MMA Rock performance with -8dB bass is the baseline; preserve it. Technical MIDI success is not musical realism.
