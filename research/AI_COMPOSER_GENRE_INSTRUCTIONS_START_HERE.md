# AI Composer — Genre Instructions: START HERE

**Single navigation and resumption point for all 55 genres**  
**Current development branch:** `swing-original-mma-execution-proof-20261010` (original 55-source catalog preserved on parent branch `source-controlled-genre-instructions-all55-20261010`)  
**Checkpoint:** October 10, 2026  
**Current task:** preserve existing published genre-style instructions; use them for accurate genre-specific performance and source-instrument connections, without restarting earlier project work.

## Use this page instead of hunting through old conversation feeds

**ONE authoritative source catalog:** [ALL55_PUBLISHED_GENRE_STYLE_SOURCE_CATALOG_2026-10-10.json](ALL55_PUBLISHED_GENRE_STYLE_SOURCE_CATALOG_2026-10-10.json)

This is the **one** index linking all 55 existing original genre names, their family, any upstream MMA style candidate, its immutable Git blob SHA, retained local copy where applicable, and match/readiness status. **Update this exact catalog** when evidence changes; do not start a competing 55-genre catalog.

**Published manuals and architecture:** [EXISTING_PUBLISHED_GENRE_STYLE_SETUP_INSTRUCTIONS_2026-10-10.md](EXISTING_PUBLISHED_GENRE_STYLE_SETUP_INSTRUCTIONS_2026-10-10.md)

**Stored unmodified source files:** [genre_reference_sources/mma/](genre_reference_sources/mma/) — copied published MMA `.mma` style files, retaining the exact original directory layout and the [upstream GNU GPL v2 license](genre_reference_sources/mma/UPSTREAM_GPL2_LICENSE.txt). MMA original source revision: [`infojunkie/mma@c52943c31aa1e64fa9b5313620d5065f91c22773`](https://github.com/infojunkie/mma/tree/c52943c31aa1e64fa9b5313620d5065f91c22773).

**Existing implementation checkpoint:** [HARD_CHECKPOINT_ALL55_ORIGINAL_GENRE_SETTINGS_ROUTED_2026-10-10.md](HARD_CHECKPOINT_ALL55_ORIGINAL_GENRE_SETTINGS_ROUTED_2026-10-10.md) is on the existing `configure-activate-all55-genre-routing-20261010` development branch. The new catalog is **research**, not a replacement for the 55 genre settings or completed audio recordings.

## Verified source coverage

| Catalog status | Number | Meaning |
| --- | ---: | --- |
| Existing Rock2 listening reference | 1 | Keep existing listenable Rock2 style/recordings untouched |
| Direct authored MMA style reference | 22 | Distinct genre-like published MMA files copied verbatim; MIDI and SFZ integration **not** thereby proven |
| Jazz Ballad — related reference only | 1 | Preserve separately verified Jazz Ballad audio; do not substitute another arrangement |
| Related but not identical style | 13 | Research lead only; **must not automatically select** as if the precise genre |
| No verified exact source | 18 | Explicit gap; preserve original genre profile and research further |
| **Total** | **55** | **13 original genre families** |

Exactly **23 original MMA files** have been copied into our repository and verified against original upstream immutable Git blob SHA values. This protects their exact written instructions; it does not establish musical authenticity for all proposed mappings, installed interpreter execution, complete SFZ programs, or finished playable audio.

## Repeat this exact proven connection procedure for each genre

1. **Select existing Composer genre**, consult its authoritative original `composer_overrides/genre_styles/<family>/profile.json`. Preserve its exact name, tempo/meter range, independent instruments, groove identity, and source-specific rules. Do **not** rename or relabel tracks to hide a mismatch.
2. **Select a genuinely appropriate published arrangement**, consulting this catalog and source's written instructions. Verify actual musical match (beat, swing subdivision, bass, drums, chord roles, fills, transitions, sections). A related-looking file is **not** an approved exact style. Keep unmodified reference separate from new code.
3. **Use the arranger's documented pattern/section interface**, e.g. MMA `Sequence`, `DefGroove`, `Groove`, intro/main/variation/fill/ending in the *actual working MMA engine*. If source has no complete applicable instructions, mark **NEEDS VERIFIED SOURCE**, do not invent a `chord_progression` placeholder to make the code appear complete.
4. **Composer remains responsible for making genuinely new songs** — chord timeline, harmonic key, lead/composed melody, song sections, duration, seed variation. Genre style arranges/accompanies that song and does not force the old repetitive 127-bar Rock tune.
5. **Validate actual generated Type-1 MIDI routed to that one genre's OWN interpreter**: exact identity, original role track names, 480 PPQ handoff contract, tempo/meter and note-off pairs. Correct true instrument name/note-range mappings explicitly and locally, without changing other genres.
6. **Bind every instrument to an original verified recorded SFZ instrument**, with source sample identity, playable note ranges, drum note numbers, separate stems and no silent General MIDI or synthetic fallback. Preserve the correct original sample sound; unresolved resources **block finished audio** rather than vanish.
7. **Render full-length standard stereo and listen**. Verify actual waveform, distinct active stems and musical genre feel. The 3D mixer is optional and LAST; leave the existing good standard-stereo sound separation, clarinet/piano timbres and drum brush level/settings untouched in this wiring pass.
8. **Mark readiness honestly:** `SOURCE_RETAINED` → `OWN_STYLE_SELECTED` → `MIDI_INTERPRETER_VERIFIED` → `ORIGINAL_SFZ_CONNECTED` → `FULL_STEREO_VERIFIED` → `LISTENER_ACCEPTED` → `PRODUCTION_DEPLOYED`. No skip from archived style file directly to live.

All source/distribution usage must respect MMA's GPL v2 license and independently verified upstream sources. Yamaha/JJazzLab/Korg documents explain architecture; a Yamaha/Korg file is not automatically executable in our independent SFZ environment.

## Where we actually stopped

- **Rock2:** new hard-driving arrangement was auditioned by the user and judged workable; its sounds and clearer separation are protected. Fine arrangement/lead tuning deferred.
- **Jazz Ballad:** independent six-original-sampled-instrument recording completed with clear clarinet, piano and bass. Clarinet sustain and prominent brush strokes are **not** adjusted in this phase.
- **Swing:** We have now RUN the **actual upstream MMA interpreter** against the **verbatim original published** `lib/stdlib/swing.mma` (not a placeholder). Two different example songs generated real full accompaniment MIDI, and the original 192-PPQ MIDI has been converted faithfully to the existing Composer's 480-PPQ contract. CI PASSED: https://github.com/mreeves1257-glitch/AI-Composition-Deployment/actions/runs/38054419407. Instrument-role incompatibilities remain: the MMA accompaniment has Drum, Walk, Chord-Guitar, Chord and Bass parts; the Composer's Swing profile requires trumpet, piano, double bass and ride-led drums. The Composer's trumpet lead must remain separate. **Full original-SFZ Swing stereo is NOT yet complete.** The next operational step is actual Composer chord-timeline input to the original MMA engine and strict authentic recorded-instrument mapping, without changing timbre or mix. Full checkpoint: [HARD_CHECKPOINT_SWING_ORIGINAL_MMA_MIDI_EXECUTION_2026-10-10.md](HARD_CHECKPOINT_SWING_ORIGINAL_MMA_MIDI_EXECUTION_2026-10-10.md).
- **Other 52 non-Rock, non-Jazz-Ballad, non-Swing styles:** all have original configuration/genre-MIDI routing development tests; actual genre-style musical execution, appropriate sample program availability, full song and listener acceptance remain individual tasks. No blanket claim of 55 playable productions.
- **Live deployment:** The new research/reference branch is **not** merged to `main` or deployed to a live Composer/control panel. Never describe source archiving as live activation.

## Resumption instruction for any new conversation/feed

> Continue the existing AI Composer project from `research/AI_COMPOSER_GENRE_INSTRUCTIONS_START_HERE.md` on branch `swing-original-mma-execution-proof-20261010`, preserving its single 55-genre source catalog from parent branch `source-controlled-genre-instructions-all55-20261010`. Use `research/ALL55_PUBLISHED_GENRE_STYLE_SOURCE_CATALOG_2026-10-10.json` as the single source index for all 55 genre-style references. Protect user-approved Rock2/Jazz Ballad sound settings and recorded banks. Next: connect Swing's published MMA accompaniment instructions to the existing Composer's original song MIDI and original recorded instruments, then validate complete stereo. Do not create new master files or reinterpret related styles as exact matches.

**Key principle:** Copy the established *procedure* to every genre; follow each selected published genre's *actual musical instructions*. Never copy Rock or Jazz Ballad's musical behavior into another genre.
