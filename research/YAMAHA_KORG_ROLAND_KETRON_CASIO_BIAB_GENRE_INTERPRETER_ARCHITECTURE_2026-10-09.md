# GENRE-OWNED INTERPRETERS — DEEP MANUFACTURER RESEARCH & CONTROLLED DECISION
**Date:** October 9, 2026
**Scope:** Yamaha Genos2, Korg Pa5X, Roland E-A7, Ketron SD80/EVENT, Casio MZ-X500, PG Music Band-in-a-Box, JJazzLab/YamJJazz; how arrangers interpret each genre.
**Project development branch:** `genre-specific-interpreters-55-rock-restored-20261009`. NOT production.
**Preserved project hard copy:** `hard-copy-ai-composer-2026-10-09-1128-CDT`, commit `352e2a4d9d13bbe9f8a76bd336488bae14e042ee`. Untouched.

## Main evidence-grounded answer to user's question
**No public evidence supports "one independently installed full software interpreter executable per genre" as the standard Yamaha/Korg/Roland arranger implementation.** Their published owner/technical manuals describe ONE arranger/style playback capability supporting many *selected individual Styles* with distinct sections, patterns, chord/root mappings, rules and per-instrument behavior. They generally do NOT publish internal source-code module boundaries, so don't claim knowledge of proprietary firmware internals.

**YES, each music style needs an individual, active musical language.** A label and a passive JSON profile are not an interpreter. A style's patterns, chord variations, dynamic shaping, rhythm timing, instrument techniques and section transitions must materially change the actual note/control messages and recorded audio.

**Our controlled architectural conclusion:** 55 independent **genre-owned interpreter contracts and musical decision backends**, using ONE reusable *technical* interpreter/renderer/translation infrastructure, without cloning Yamaha/Korg/Roland code. The distinction is **independent MUSICAL AUTHORITY** per genre, not 55 separate MIDI/SFZ/3D executors.

## Manufacturer evidence (primary/manual sources)

| Manufacturer | Verified documented mechanics | Specific implication | Sources |
|---|---|---|---|
| Yamaha Genos2 | Each Style = Intro/Main/Fill/Ending sections with **eight Source Pattern** channels: Rhythm1, Rhythm2, Bass, Chord1, Chord2, Pad, Phrase1, Phrase2. Groove permits push/heavy/swing timing and dynamics. NTR/NTT selects root transposition, chord-quality tables, guitar strum/arpeggio voicing, slash-bass, per-channel note limits and RTR: Stop, Pitch Shift, Retrigger. | Genre owner must produce actual 8-way/variable per-part arrangements and role-specific voice leading, timing, attacks, note-offs, not just expose `CAP_09` metadata. Guitar != bass != kit. | https://usa.yamaha.com/files/download/other_assets/1/2318561/Genos2_reference_manual_En_C0.pdf (style creator pp20-31) |
| Korg Pa5X | Style has **eight parts** (drums, percussion, bass, five ACC). Style Elements Intro/Variation/Fill/Break/Ending; individual track Chord Variations (CV), Note Transposition Tables, Guitar Mode with strums, strings/fret positions and noises, specific Bass/Drum/Guitar/Accompaniment track types. | Phrase/chord mapping and guitar articulation depend on the exact selected genre AND exact instrument/program. Track-type-specific conversion required. | https://cdn.korg.com/us/support/download/files/06f9cc2455d2237e98bed4e5948527cf.pdf ; https://www.korg.com/us/products/synthesizers/pa5x/specifications.php |
| Roland E-A7 | Style Composer has separately recorded looped Main1–4, one-shot Intro/Fill/Ending; **eight parts** (1 drum, 1 bass, 6 accomp). Patterns may be designated major/minor/seventh; individual channel settings and expressive CC11. | Notes and patterns must CHANGE with harmonic mode and section. Phrase density is genre-owned, not a generic short loop. | https://cdn.roland.com/assets/media/pdf/E-A7_r_e01W.pdf, Style Composer pp39-46 |
| Ketron SD80 / EVENT | Five chord accompaniment parts with Normal vs Retrigger and Close vs Parallel conversions; explicit Jazz, Folk, Blues harmony variants; EVENT has Real Styles and recorded Real Drums often longer than short 1-bar loops. | This is unusually explicit support for reusable engine mechanics **with selected style-specific harmony modes**. Audio-source availability and real groove material matter. | https://shop.ketron.it/images/ketron/Manuali_HTML/SD80/english/45_style_chord.html ; https://ketron.it/ketron-event-chrom-keyboard/ |
| Casio MZ-X500 | Pattern Sequencer 12 patterns (Intro1–2, Var1–4, Fill1–4, Ending1–2), eight instrument parts, and 19 selectable conversion tables for Bass/Chord/Phrase, including minor/seventh/dorian. | Use per-role/genre conversion strategy registry, not universal `transpose N semitones`. | https://www.casio.com/content/dam/casio/global/support/manuals/electronic-musical-instruments/pdf/008-en/w/Web_MZX500_300-E-2A_EN.pdf |
| PG Music Band-in-a-Box | StyleMaker/RealTracks/RealDrums; style parts and rhythmic feel, rests/shots/holds/pushes, substyle intensity and section markers; source audio availability, tempo feel and half-/double-time policies are explicit controls. | Timed patterns and live sample audio require their OWN sources, musical feel and output validation. Simply raising BPM may not fix half-time phrasing. | https://www.pgmusic.com/manuals/bbw2026full/chapter14.htm ; https://www.pgmusic.com/manuals/bbw2026full/chapter5.htm ; https://www.pgmusic.com/manuals/bbw2026full/chapter7.htm |
| JJazzLab/YamJJazz | Rhythm engines process Yamaha-style variation/intro/ending tracks, and per-section variation/intensity/fill parameters. Its Yamaha import documentation warns some Yamaha Mega Voices, articulation notes/CC/SysEx etc. will not transfer correctly to generic instruments. | A plain SMF or GM mapping is NOT enough to reproduce manufacturer-specific physical performance; our own SFZ physical controls must be verified. | https://github.com/jjazzboss/JJazzLab-UserGuide/blob/master/rhythm-engines/yamjjazz-rhythm-engine/yamaha-styles.md ; https://jjazzlab.gitbook.io/user-guide/editors/song-structure |

**Not proven:** Any manufacturer's private internal implementation count of language interpreter classes, their source files, actual programming APIs, or that a proprietary style can lawfully or accurately be installed as a plug-in in this project.

## Genre-specific MUSICAL interpreter contract — exact required fields
Each named genre, with a distinct path in the original family folder, must supply:

1. `genre_id` and immutable reference to its OWN original `profile.json`/`musical_definition.profile_id`.
2. An **ensemble beat clock**: explicit tempo, meter, subdivisions, feel (straight/swing/clave/shuffle/half-time etc), selected Stage-2/3 owner, no independent silent tempo override.
3. Separate source **style variations** per section: intro, verse/main (at least sparse vs dense), fills, breaks, chorus/arrival, transitions, endings. Do not assume all genres need drums, four-four, or identical structure.
4. Harmonic **chord type/variation selection**: quality/bass inversion, source/root transposition, NTT-like genre-specific mapping, voice-leading and retrigger/stop/pitch-shift/rearticulation decisions per track.
5. Exact individual instrument roles/tracks: which source SFZ and MIDI mapping each role owns, and valid pitch/velocity/gesture zone; physical instrument ID **is not** its target recording program key.
6. Drum/percussion score in correct rhythmic language: independent kick/snare/hat/toms/cymbals as appropriate, coherent bar/beat locations, round-robin/velocity, real fills and arrivals. Some genres have NO drums.
7. Bass-to-kick interaction and guitar/keyboard/lead response, space for phrases, appropriate bass motion and chord-specific register.
8. Section-specific **microtiming** plan: shared groove template, push/layback/swing, not random independent note jitter.
9. Section-shaped dynamics and intensity: MIDI velocity/accent/CC if source supports, note density, breaks and phrase boundaries—not only output gain.
10. Physical playing techniques by recorded source: guitar strings/strum/palm mute/vibrato, bass sustain/mute, natural drum hits/rolls, keyboard pedal/voicing, horns breath/attack etc. Never send unsupported CC and pretend it works.
11. Explicit **original note-event output** for Stage 4 + performance instructions for Stage 5. Passive text or existence of `CAP_01...CAP_22` is NOT a playable genre interpreter.
12. Provenance and sample-install audit: native SFZ text/includes + physically present wave files + MIDI keyzone + audible WAV + per-track/scene gain.
13. Explicit blocked/unsupported paths: absent instrument, unlicensed style, unknown physical sample/voice, invalid chord conversion => BLOCK, never cheap GM piano or silence sold as real music.
14. Independent **acceptance gates**: reproduce exact event stream, verify correct 7 stages, isolated real stems, preserved standalone 3D mixer, and human audition for genre authenticity. Distinguish technical PASS from musical approval.

## Why Rock sounded too slow despite 123 BPM
The recently rendered **7-bar** project-authored Rock seed used 123 BPM, sparse early kicks/hats, no separate lead, toms, ride or crash. It was a *different piece of music* from the archived **16-bar 145 BPM** Rock interpretation the user liked on Oct 8. A 123-BPM numerical clock with weak sparse beat accents can feel half-time, and no intensity instruction can fix a missing beat without changing actual note events. Do not misdiagnose this as an SFZ renderer speed bug.

## RECOVERED Rock backend — exact prior user-preferred research
- Original user's Oct 8 **16-bar** Rock experiment: https://github.com/mreeves1257-glitch/AI-Composition-Deployment/actions/runs/37870594722
- Its retained artifact: https://github.com/mreeves1257-glitch/AI-Composition-Deployment/actions/runs/37870594722/artifacts/11589859245 (downloaded and inspected October 9).
- Archived exact project-authored translator: `research/archived_rock_20261009/original/rock_pinned_mma_interpreter.py`, Git blob `7ea8c0e59768a9695cd98f9c6888c8e64e68b33f`; restored untouched into `composer_overrides/genre_styles/Rock/rock_pinned_mma_interpreter.py`.
- Archived exact Rock guitar-strum gesture: Git blob `b6d5ce7119de22af29b00a5cdf876e76c61b3d9e`; restored untouched into Rock folder.
- Original MIDI recovered from original successful artifact: `MMA_Rock_16Bar_Two_Sections.mid`, SHA256 **`7253c3715299018dc540bdbaf29883bfbd7615ab7e5d943bde45f8d1b19555fe`**, **5,395 bytes**; 145 BPM, 16 bars. Text MMA score is 16 bars, Dm/Bb/F/C -> Dm/Bb/Gm/A7 progression, verse/chorus BasicRock to BasicRock4 groove change.
- Typed score from original project Rock module: **420 notes / seven roles**: HARMONY 225, BASS 56, KICK 32, SNARE 38, HAT 64, TOMS 4, CRASH 1; exactly authored snare rolls, tom descents, chorus arrival crash. One unsupported original source tambourine MIDI 54 and a GM open-hat-to-closed-hat recorded-source approximation remain transparently documented. LEAD/ride not part of this particular 16-bar score.
- MMA itself is **external GPL-licensed software**. Its source is NOT copied into the user project. Original MMA *MIDI as data* and project-owned Rock translation are kept separate, without claiming rights to proprietary Yamaha/Korg style/samples.
- This 16-bar Rock source (the user's positive listening reference) **must not be replaced** by the disconnected 7-bar sample sketch. Retain user-preferred bass −8 dB candidate and kick development as separate audition decisions, not generic global settings.

## CONTROLLED filesystem changes in this branch
- **55 unique `INTERPRETER_<EXACT_GENRE_ID>_R1.json`** paths in the existing 13 family folders, lookup `GENRE_INTERPRETER_REGISTRY_R1.json`. Each contains only unique interpreter ownership / pointers to original musical data, **not copies or alternate profiles**.
- **ROCK only** has its exact previous executable score translator and guitar-strum file recovered in its own Rock folder.
- Other 54 slots explicitly read `EXECUTABLE_GENRE_INTERPRETATION_NOT_YET_IMPLEMENTED`; they are not mislabeled as functioning because their profiles/22 slots exist.
- No new global stage or new renderer; no live link to Composer's old `theory['events']`; no silent notes promoted as live; original recorded SFZ libraries, current Rock mix, Plug, Control Panel, separate Stage7 3D mixer and frozen hard copy unchanged.

## Next implementation gates, in order
1. **Rock only:** test recovered pinned 5,395-byte MIDI against restored exact Rock translator checksum; require 420 unchanged events / section trace / seven separate original recorded SFZ resource identities. Restore missing input from audited original archive, not remake score.
2. Determine explicit `genre_id -> family interpreter module` dispatch invoked after Stage 3. Stop passing only symbolic metadata from the shared 22 handlers. **Rock interpreter output must supply actual Stage 4 notes** in isolated test without replacing legacy events in production.
3. Use separate Stage5 physical gesture performer (native guitar strum, bass sustain, kit rolls) and recorded SFZ proof. Protect user's preferred original 16-bar arrangement and focus kick level rather than blindly changing tempo.
4. Design/read distinct genre-specific policies and tests, one at a time: Jazz Swing != Jazz Ballad; Salsa clave and cross-bar accents != Rock; WALTZ 3/4 != Rock; solo PIANIST no drums; Electronic genres need their own rhythmic modulation, not same guitar/bass engine.
5. For each additional genre, do not mark functional until authored output plus exact resources plus separate recorded stems plus listening audit are demonstrated.

**This is a research/placement checkpoint, NOT a new full downloadable user hard copy. Every later full hard copy must include a downloadable ZIP for the user.**
