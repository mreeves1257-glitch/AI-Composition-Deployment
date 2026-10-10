# RESEARCH REFERENCE — EXISTING WRITTEN GENRE/ARRANGER INSTRUCTIONS
**Date:** 2026-10-10
**Status:** SOURCE RESEARCH ONLY — NO GENRE AUDIO, INSTRUMENT, MIX OR PRODUCTION CODE MODIFIED.

## User directive
Stop inventing/guessing new per-genre instructions. Find EXISTING published arranger documentation and usable fully authored genre style files. Preserve the established path:
**Composer -> original MIDI and harmonic data -> selected genre-owned musical interpreter -> original recorded sample instruments -> original standard stereo mix -> optional 3D mixer LAST.**
Rock2 and Jazz Ballad sound clarity remain protected. No fine tuning clarinet sustain, brush loudness, piano or individual instrument levels in this research branch.

## Authoritative sources actually located and checked
1. **MMA author's official manual and style-library index:** https://www.mellowood.ca/mma/online-docs/html/mma.html
   - Author's tutorial/reference documents and independent Library Reference.
   - Official distribution/download: https://mellowood.ca/mma/downloads.html
   - The archive includes the executable, Python modules, standard library of **more than 1,000 grooves/rhythm patterns**, examples, and HTML reference docs. Latest source site lists version 25.05.3 with package 25.05.0 as of site date 2026-06-19; do not assume installed project version matches.
2. **Written groove setup from MMA author:** https://www.mellowood.ca/music/essays/mma/mma-groove.html
   - Real definitions for separate Drum, Chord and Bass tracks with `Sequence`; save a named `DefGroove Main`, then switch `Groove Main` / `Groove Fill` against chord bars. Illustrates genre-owned arrangement control; not merely a label.
3. **MMA source tree at immutable commit `c52943c31aa1e64fa9b5313620d5065f91c22773`:** https://github.com/infojunkie/mma/tree/c52943c31aa1e64fa9b5313620d5065f91c22773/lib
   - Complete, already-authored **Swing**: `lib/stdlib/swing.mma` (594 lines, default swing, walking bass, piano, guitar, drums, fills, multiple variations, 4-bar intro, ending); https://github.com/infojunkie/mma/blob/c52943c31aa1e64fa9b5313620d5065f91c22773/lib/stdlib/swing.mma
   - Another **Swing**: `lib/casio/swing.mma` (146 lines, Swing main/intro/end with original Casio-derived bass, piano, jazz guitar, drum patterns); https://github.com/infojunkie/mma/blob/c52943c31aa1e64fa9b5313620d5065f91c22773/lib/casio/swing.mma
   - A third **Jazz Swing**: `lib/yamaha/jazzswing.mma` (580 lines, Yamaha-style conversion with Main A/B, fills, intro, ending, per-instrument MIDI patterns); conversion itself warns it may not preserve all Yamaha special behavior or be optimized.
   - Other directly inspected source styles include `lib/stdlib/bebop.mma` (174 lines) and `lib/stdlib/salsa.mma` (212 lines), with independently written rhythm parts/variation/intro/end. Available additional families include `lib/stdlib/jazzwaltz.mma`, `lib/stdlib/countryswing.mma`, `lib/stdlib/rockballad.mma`, `lib/stdlib/blues.mma`, `lib/stdlib/bossanova.mma`, `lib/stdlib/tango.mma`, `lib/zoom/reggae.mma`, `lib/zoom/hiphop.mma`, `lib/casio/funk1.mma`, etc.
4. **JJazzLab documented Yamaha style format and track/section types:** https://github.com/jjazzboss/JJazzLab-UserGuide/blob/master/rhythm-engines/yamjjazz-rhythm-engine/yamaha-styles.md
   - Recognizes `.sty`, `.prs`, `.bcs`, `.sst` (SFF1/SFF2). Typical sections Intro A/B/C, Main A/B/C/D, Fill A/B and Ending A/B/C. Individual instrument tracks Rhythm, Sub-rhythm, Bass, Chord1/2, Pad, Phrase1/2.
   - Warning: proprietary Yamaha Mega Voices/controller/patch details are not generally portable to third-party SFZ.
5. **JJazzLab actual song structure/rhythm engine:** https://jjazzlab.gitbook.io/user-guide/editors/song-structure and https://jjazzlab.gitbook.io/user-guide/rhythm-engines/overview
   - Chord/section arrangement, rhythm per song part, variation, intensity, fills, instrument mute. A rhythm generator consumes this data; naming a genre is not musical execution.
6. **Korg arranger hardware architectural reference:** https://www.korg.com/us/products/synthesizers/pa5x/specifications.php
   - Eight separate style tracks, Intro/Variation/Fill/Break/Ending parts, note-transposition tables (NTT). This validates arranger architecture but NOT that Korg-specific proprietary style files can be installed in the independent project.
7. **Yamaha arranger Style Creator, manual authority:** https://usa.yamaha.com/files/download/other_assets/7/1131007/genos_en_rm_h0.pdf
   - Each style section has eight separately authored rhythm/bass/chord/pad/phrase source-pattern channels. Treat as reference, do not copy proprietary style data.

## How to apply this to the EXISTING Composer (research, not yet implemented)
1. Preserve the 55 original genre identities and already working Composer MIDI routing, individual genre selection, instrument sample libraries, standard stereo, and optional independent 3D mixer. Do not overwrite Rock2 or Jazz Ballad.
2. For **Swing**, *select one independently authored working Swing style/groove* from MMA, rather than invent a `swing.chord_progression()` just to make old placeholder code pass. Prove the chosen MMA engine can accept the Composer's actual chord timeline and section instructions and generate MIDI accompaniment from that existing groove.
3. Composer owns new SONG (chord progression, melody, form, seed) rather than reusing one 7-bar symbolic preview. An MMA style defines the PERFORMANCE RHYTHM for each instrument role; it does not choose a never-changing song.
4. For each selected style, use real, named instrument tracks, not an assumed generic GM patch. Map MIDI drum note keys, pitches and program identities to exact existing recorded SFZ libraries, with independent note-range and resource preflight. Prevent unmapped instruments disappearing in mix.
5. Keep Swing's known 6 original full tracks (DOUBLE_BASS, ELECTRIC_PIANO, TRUMPET, KICK, SNARE, HAT/ride-led part), even if external groove has optional more channels. Do not silently substitute Jazz Ballad's clarinet or wrong percussion. Additional channels require authentic source verification.
6. Verify genre groove identity, actual MIDI content, full section variation, accurate drum/cymbal note map, original SFZ note ranges, separate stems and complete real stereo before considering activation. The user's listening judgment controls acceptance.
7. Repeat common process across genres with independently appropriate documented styles. Do NOT assume MMA library covers all 55 original project names by exact matching. Explicitly inventory style coverage and licensed source before adoption.

## Crucial legal/technical boundaries
- Original MMA source and library files are GPL licensed. Using/distributing derivatives must honor license obligations; do not silently copy code into existing project.
- External YAML, Yamaha/Korg data and proprietary arranger formats are not interoperable by filename. Select an actual *working implementation* (e.g. external MMA MIDI arranger for a specific groove) and verify its inputs and output, not a wishful adapter.
- MMA traditionally generates accompaniment and may not contain the independent lead melody; preserve/merge Composer's lead as a distinct musical role.
- Direct MIDI output must be suitable for existing Type-1 480-PPQ genre-inlet contract; conversion to type 1 and correct tempo/meter/note metadata must be explicitly verified.
- No tone, envelope, mixing, drum volume, stereo or other instrument adjustments were performed as part of this research.

**Project development checkpoint:** Existing Swing attempts on branch `connect-swing-original-recorded-jazz-20261010` faced missing placeholder `chord_progression`, unverified trumpet note-range and drum note identity. This research branch is isolated so those attempts and previously approved audio remain unchanged. These documents provide an actual alternative to custom, unverified style authorship. Full playable Swing audio is NOT asserted by these findings.
