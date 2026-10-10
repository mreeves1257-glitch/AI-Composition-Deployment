# External Written Genre-Style Instructions — Research Checkpoint
**Date:** 2026-10-10. **Scope:** source discovery and integration instructions ONLY; no sound, mix or production activation changes. **Repository:** `mreeves1257-glitch/AI-Composition-Deployment`. **Source MMA commit:** `c52943c31aa1e64fa9b5313620d5065f91c22773`.

## Confirmed published implementation manuals
1. [MMA manual, tutorial and standard library](https://www.mellowood.ca/mma/online-docs/html/mma.html) (author Bob van der Poel). [MMA setup overview](https://www.mellowood.ca/mma/online-docs/html/ref/node1.html): Composer supplies chords/key/tempo/song sections; MMA reads a text input selecting the actual accompaniment GROOVE and outputs MIDI. Its style library has multiple independently authored variations. [Groove preview instructions](https://mellowood.ca/mma/online-docs/html/ref/node33.html) include `mma -V <groove_name>`. **Do not mistake preview audio for full music.**
2. [JJazzLab Yamaha styles](https://jjazzlab.gitbook.io/user-guide/rhythm-engines/yamjjazz-rhythm-engine/yamaha-styles): accompaniment patterns are divided into Intro/Endings, Main A/B/C/D, fills and independent rhythm, bass, chord, pad and phrase tracks. Existing `.sty/.prs/.sst` styles have their own MIDI/chord transposition semantics (CASM).
3. [JJazzLab extended Yamaha styles](https://jjazzlab.gitbook.io/user-guide/rhythm-engines/yamjjazz-rhythm-engine/extended-yamaha-styles): multi-variation alternate source phrases explicitly tackle monotonous repeat patterns. `.yjz` is an extension requiring an original base `.sty/.prs` file, NOT a stand-alone instrument renderer. Preserve source phrase duration/track names/keys.
4. [Korg Pa style structure](https://www.manualslib.com/manual/688476/Korg-Pa600.html?page=40): explicit chord variations, separate bass/accompaniment/drum/perc parts and phrase transposition according to chords. Do not treat Korg proprietary binary arrangement formats as MMA files.
5. [MMA source library, immutable commit](https://github.com/infojunkie/mma/tree/c52943c31aa1e64fa9b5313620d5065f91c22773/lib); MMA code and styles are GPL-licensed; preserve upstream attributions/license, evaluate distribution requirements before inclusion. Style VOICE names are *symbolic* and NOT approval to replace original real recorded SFZ instruments with generic MIDI synthesizers.

## Important architecture correction exposed by Swing
Swing's existing project module was still a placeholder, while its entry/tempo/instrument mapping appeared configured. A prior trial called a missing `chord_progression` function on that module. **Do not manufacture the absent function and claim musical authenticity.** The REAL Composer already calculates harmony and sections; the selected external accompaniment engine consumes that chord sequence and produces accompaniment phrases. Swing's trumpet lead remains a distinct original recorded instrument mapped after the accompaniment MIDI source. Keep all original Jazz Ballad clarinet/piano/brush settings unchanged; the listener approved sound clarity and wants rhythm and genuine genre instructions first.

### Intended established path (not new stage)
**Composer (song form, melody, harmony/chords) → original MIDI + named authentic genre groove (MMA/Yamaha style interpreter) → genre-owned phrase/rhythm MIDI with original-role track IDs → actual recorded SFZ instrument binding for EVERY needed role → separate real stems → standard stereo → optional independent 3D mixer last.**

Use the *real existing interpreter* as a music-generation engine. A `genre` label in a JSON file and a successful Type-1 MIDI transport test are NOT equivalent to having executed the genre groove.

For Swing **first audition actual established reference patterns**:
- [MMA original Swing with SwingWalk, SwingFill, SwingTriple variations](https://github.com/infojunkie/mma/blob/c52943c31aa1e64fa9b5313620d5065f91c22773/lib/stdlib/swing.mma). Real bass walks, hi-hat/ride options, section shifts, chord accompaniment.
- [Casio-derived MMA Swing](https://github.com/infojunkie/mma/blob/c52943c31aa1e64fa9b5313620d5065f91c22773/lib/casio/swing.mma), with encoded four-bar kick/snare/hat, bass, piano/guitar patterns; independent SwingIntro and SwingEnd.
- [Yamaha-converted JazzSwing](https://github.com/infojunkie/mma/blob/c52943c31aa1e64fa9b5313620d5065f91c22773/lib/yamaha/jazzswing.mma). Source itself notes a computer-assisted style conversion needs human optimization. It has Main A, Fill, Intro/Ending data. These are competing options, NOT a preapproved blend.

**Before audition**: (1) verify source/license, (2) make the original Composer provide chord chart/form, (3) execute chosen MMA style's REAL groove instructions to produce MIDI, (4) verify bass/piano/percussion rhythm and independent trumpet melody, (5) map MIDI triggers/roles and key zones to preflighted original SFZ recordings; block absent instruments, (6) render only when all separate stems and source identity are confirmed, (7) listen for authentic genre, clarity and variety. Keep sound/gain/envelope knobs exactly as approved; do not substitute General MIDI patches. No style is approved based on its name, BPM or test count.

## MMA file candidates found across all 55 configured original genres
**Method:** path exists in MMA immutable Git tree, NOT proof the musical behavior is appropriate, not audio-verified, and not installed in our original Composer. "Related style" is exploratory only and should never be misrepresented as the requested genre. Unknown is only a lack of *an identified candidate in this particular inspected library*, not proof no style exists anywhere.

| Existing family | Existing genre | Published, existing MMA source file candidate(s) | Research status |
|---|---|---|---|
| Rock | ROCK | `lib/casio/rock2.mma`; `lib/stdlib/rockballad.mma` | DIRECT GENRE CANDIDATE / UNTESTED |
| Jazz | Swing | `lib/stdlib/swing.mma`; `lib/casio/swing.mma`; `lib/yamaha/jazzswing.mma` | DIRECT GENRE CANDIDATE / UNTESTED |
| Jazz | Jazz Ballad | `lib/stdlib/slowjazz.mma`; `lib/stdlib/mellowjazz.mma` | RELATED STYLE ONLY / MUST NOT MISLABEL |
| Jazz | Big Band | `lib/stdlib/bigband.mma`; `lib/casio/fastbigband.mma` | DIRECT GENRE CANDIDATE / UNTESTED |
| Jazz | Jazz Waltz | `lib/stdlib/jazzwaltz.mma`; `lib/yamaha/jazzwaltz.mma` | DIRECT GENRE CANDIDATE / UNTESTED |
| Jazz | Bebop | `lib/stdlib/bebop.mma` | DIRECT GENRE CANDIDATE / UNTESTED |
| Jazz | Cool Jazz | `lib/stdlib/mellowjazz.mma`; `lib/stdlib/nitejazz.mma` | RELATED STYLE ONLY / MUST NOT MISLABEL |
| Jazz | Dixieland | `lib/stdlib/dixie.mma` | DIRECT GENRE CANDIDATE / UNTESTED |
| Jazz | Jazz Fusion | `lib/casio/fusion.mma`; `lib/stdlib/jazzrock.mma` | RELATED STYLE ONLY / MUST NOT MISLABEL |
| R and B Soul Funk Disco | Rhythm and Blues | `lib/zoom/rnb.mma` | DIRECT GENRE CANDIDATE / UNTESTED |
| R and B Soul Funk Disco | Soul | `lib/casio/soul.mma` | DIRECT GENRE CANDIDATE / UNTESTED |
| R and B Soul Funk Disco | Funk | `lib/zoom/funk.mma` | DIRECT GENRE CANDIDATE / UNTESTED |
| R and B Soul Funk Disco | Contemporary R&B | `lib/zoom/rnb.mma` | RELATED STYLE ONLY / MUST NOT MISLABEL |
| R and B Soul Funk Disco | Neo-Soul-related | Further source search required | NOT IDENTIFIED IN INSPECTED MMA LIBRARY |
| R and B Soul Funk Disco | DISCO | `lib/casio/discosoul.mma` | RELATED STYLE ONLY / MUST NOT MISLABEL |
| Country Bluegrass | Traditional Country | `lib/zoom/country.mma` | DIRECT GENRE CANDIDATE / UNTESTED |
| Country Bluegrass | Country Rock | `lib/stdlib/folkrock.mma` | RELATED STYLE ONLY / MUST NOT MISLABEL |
| Country Bluegrass | Country Ballad | `lib/stdlib/slowcountry.mma` | RELATED STYLE ONLY / MUST NOT MISLABEL |
| Country Bluegrass | Country Shuffle | `lib/stdlib/countryswing.mma` | RELATED STYLE ONLY / MUST NOT MISLABEL |
| Country Bluegrass | Two-Step | `lib/stdlib/hillcountry.mma` | RELATED STYLE ONLY / MUST NOT MISLABEL |
| Country Bluegrass | Country Waltz | `lib/stdlib/countrywaltz.mma` | DIRECT GENRE CANDIDATE / UNTESTED |
| Country Bluegrass | Bluegrass-related | `lib/stdlib/bluegrass.mma` | DIRECT GENRE CANDIDATE / UNTESTED |
| Latin | Bossa Nova | `lib/stdlib/bossanova.mma` | DIRECT GENRE CANDIDATE / UNTESTED |
| Latin | Samba | `lib/stdlib/samba.mma` | DIRECT GENRE CANDIDATE / UNTESTED |
| Latin | Salsa | `lib/stdlib/salsa.mma`; `lib/yamaha/salsa1.mma` | DIRECT GENRE CANDIDATE / UNTESTED |
| Latin | Mambo | `lib/stdlib/mambo.mma` | DIRECT GENRE CANDIDATE / UNTESTED |
| Latin | Rumba | `lib/stdlib/rhumba.mma` | DIRECT GENRE CANDIDATE / UNTESTED |
| Latin | Cha-Cha | `lib/stdlib/chacha.mma` | DIRECT GENRE CANDIDATE / UNTESTED |
| Latin | Bolero | `lib/stdlib/bolero.mma` | DIRECT GENRE CANDIDATE / UNTESTED |
| Electronic Dance | House | `lib/casio/house.mma` | DIRECT GENRE CANDIDATE / UNTESTED |
| Electronic Dance | Techno | `lib/casio/techno.mma` | DIRECT GENRE CANDIDATE / UNTESTED |
| Electronic Dance | Trance | `lib/stdlib/trance.mma` | DIRECT GENRE CANDIDATE / UNTESTED |
| Electronic Dance | Ambient Electronic | `lib/casio/ambient1.mma`; `lib/zoom/ambient.mma` | DIRECT GENRE CANDIDATE / UNTESTED |
| Electronic Dance | Downtempo | Further source search required | NOT IDENTIFIED IN INSPECTED MMA LIBRARY |
| Electronic Dance | Breakbeat-related | Further source search required | NOT IDENTIFIED IN INSPECTED MMA LIBRARY |
| Electronic Dance | Garage-related | Further source search required | NOT IDENTIFIED IN INSPECTED MMA LIBRARY |
| Electronic Dance | Experimental Electronic | Further source search required | NOT IDENTIFIED IN INSPECTED MMA LIBRARY |
| Electronic Dance | Chugg / #chugg | Further source search required | NOT IDENTIFIED IN INSPECTED MMA LIBRARY |
| Indie Alternative | Eclectic New Indie | Further source search required | NOT IDENTIFIED IN INSPECTED MMA LIBRARY |
| Reggaeton | Mexican Reggaeton | Further source search required | NOT IDENTIFIED IN INSPECTED MMA LIBRARY |
| Afrobeats AfroLatin | Afrobeats | Further source search required | NOT IDENTIFIED IN INSPECTED MMA LIBRARY |
| Afrobeats AfroLatin | Afro-Latin / Afrobeats Fusion | `lib/stdlib/afro-cuban.mma` | RELATED STYLE ONLY / MUST NOT MISLABEL |
| Afrobeats AfroLatin | Afro House | `lib/zoom/afro.mma`; `lib/casio/house.mma` | RELATED STYLE ONLY / MUST NOT MISLABEL |
| Trip Hop | Trip-Hop | `lib/casio/triphop.mma` | DIRECT GENRE CANDIDATE / UNTESTED |
| Trip Hop | Contemporary Trip-Hop / Trip-Hop Revival | Further source search required | NOT IDENTIFIED IN INSPECTED MMA LIBRARY |
| Hybrid Custom | Regional Electronic Hybrids | Further source search required | NOT IDENTIFIED IN INSPECTED MMA LIBRARY |
| Hybrid Custom | Genre-Breaking / Borderless | Further source search required | NOT IDENTIFIED IN INSPECTED MMA LIBRARY |
| Hybrid Custom | Custom Hybrid | Further source search required | NOT IDENTIFIED IN INSPECTED MMA LIBRARY |
| Hybrid Custom | Custom Style | Further source search required | NOT IDENTIFIED IN INSPECTED MMA LIBRARY |
| Hybrid Custom | Controlled Custom Style Profile | Further source search required | NOT IDENTIFIED IN INSPECTED MMA LIBRARY |
| Classical Acoustic | Classical | Further source search required | NOT IDENTIFIED IN INSPECTED MMA LIBRARY |
| Classical Acoustic | WALTZ | `lib/stdlib/waltz.mma` | DIRECT GENRE CANDIDATE / UNTESTED |
| Classical Acoustic | PIANIST | `lib/stdlib/pianoballad.mma` | RELATED STYLE ONLY / MUST NOT MISLABEL |
| New Age Spiritual | New Age | `lib/casio/ambient2.mma` | RELATED STYLE ONLY / MUST NOT MISLABEL |
| New Age Spiritual | Spiritual | `lib/stdlib/spiritual.mma` | DIRECT GENRE CANDIDATE / UNTESTED |
## Verification boundary and next action
- Original project still has 55 independently named genre settings and 55 separate real MIDI entries, but just Rock2 and Jazz Ballad have verified *full sampled stereo* before this research. Swing trumpet has completed independent WAV/SFZ sample tests, NOT a fully listener-approved Swing song.
- More than one category of missing link: an existing actual genre groove/interpreter; a separate instrument assignment; recorded sample-zone preflight; complete genre-appropriate composition and real stereo.
- No new genre files, arrangement algorithms, mix profiles, audio samples, or live service settings are changed by this research. Other exact source matches from MMA/Yamaha/Korg may need separate verification, licensing review and listening.
- **Resume with source-driven Swing GROOVE selection and real MMA input/output inspection, not new invented Swing chord methods.** Then follow the identical execution procedure for other verified source styles. Preserving original approved recordings is mandatory.
