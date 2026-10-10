# AI Composer — Genre Instructions: START HERE

**Single navigation and resumption point for all 55 genres**  
**Development branch:** `source-controlled-genre-instructions-all55-20261010`  
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

## New verified executable Swing checkpoint — 2026-10-10

**Development continuation:** [Swing original MMA engine proof](https://github.com/mreeves1257-glitch/AI-Composition-Deployment/actions/runs/38054987885) on branch `swing-official-mma-engine-proof-20261010`.

- The REAL upstream MMA program from immutable Git commit `c52943c31aa1e64fa9b5313620d5065f91c22773` executed the archived byte-identical `lib/stdlib/swing.mma` musical style. Tested published grooves `SwingIntro`, `SwingWalk`, `Swing1Walk`, `SwingFill`, `Swing2`, `SwingEnd`, generating actual distinct named instrument MIDI tracks (bass, walking bass, piano chords, guitar, sax, drums) from an independently authored 28-bar chord chart.
- The original MMA output is Type-1 MIDI at 192 PPQ. The tested **common transport-only** converter `composer_overrides/genre_styles/external_mma_midi_bridge.py` produces a valid Type-1 **480-PPQ** copy with every note/event, velocity, drum channel, program change, tempo, meter and separate original track retained; position error at most half an output tick. This is NOT a fake music interpreter and NOT an instrument sound adjustment.
- Test source and real MIDI archives: `research/test_original_mma_swing_engine_20261010.py`; CI artifact `ORIGINAL_MMA_SWING_ENGINE_28BAR_GENERATED_MIDI_20261010`. The source file, raw original MMA MIDI, and 480-PPQ normalized MIDI are all preserved in the CI run artifact.
- **Still required:** Composer's new-song chord timeline and lead trumpet merge, approved mapping of MMA's separate roles into Swing's SIX original recorded instrument parts. The MMA source includes guitar and sax patterns that have no automatic approved target in the present Swing six-part scheme; they MUST NOT disappear without an explicit decision/verified sample. Existing original Swing bass, recorded trumpet and ride/cymbal mapping must each pass actual source and note-range checks; the final original SFZ stereo rendering/listener acceptance remains pending.
- All 55 original project settings, licensed reference library files, Rock2, Jazz Ballad, source instrument sounds, balances, and the live control panel remain unchanged. **Do not claim Swing has full audio or 55 genres are live.**

## Where we actually stopped

- **Rock2:** new hard-driving arrangement was auditioned by the user and judged workable; its sounds and clearer separation are protected. Fine arrangement/lead tuning deferred.
- **Jazz Ballad:** independent six-original-sampled-instrument recording completed with clear clarinet, piano and bass. Clarinet sustain and prominent brush strokes are **not** adjusted in this phase.
- **Swing:** original MIDI identity configured; project discovered the Swing placeholder lacked `chord_progression`. Original recorded VSCO trumpet source and sample zones have been verified independently. Swing's **full finished genre audio is not yet certified**, and the earlier placeholder attempts must not be claimed a success. New instruction research found a full authored source: `lib/stdlib/swing.mma` (walking bass, drums, piano, variation, fills, intro and ending). **Next operational step:** follow *that* source's documented MMA arrangement and plug its generated MIDI into the original Swing instruments, test actual full song, preserve standard stereo.
- **Other 52 non-Rock, non-Jazz-Ballad, non-Swing styles:** all have original configuration/genre-MIDI routing development tests; actual genre-style musical execution, appropriate sample program availability, full song and listener acceptance remain individual tasks. No blanket claim of 55 playable productions.
- **Live deployment:** The new research/reference branch is **not** merged to `main` or deployed to a live Composer/control panel. Never describe source archiving as live activation.

## Resumption instruction for any new conversation/feed

> Continue the existing AI Composer project from `research/AI_COMPOSER_GENRE_INSTRUCTIONS_START_HERE.md` on branch `source-controlled-genre-instructions-all55-20261010`. Use `research/ALL55_PUBLISHED_GENRE_STYLE_SOURCE_CATALOG_2026-10-10.json` as the single source index for all 55 genre-style references. Protect user-approved Rock2/Jazz Ballad sound settings and recorded banks. Next: connect Swing's published MMA accompaniment instructions to the existing Composer's original song MIDI and original recorded instruments, then validate complete stereo. Do not create new master files or reinterpret related styles as exact matches.

**Key principle:** Copy the established *procedure* to every genre; follow each selected published genre's *actual musical instructions*. Never copy Rock or Jazz Ballad's musical behavior into another genre.
