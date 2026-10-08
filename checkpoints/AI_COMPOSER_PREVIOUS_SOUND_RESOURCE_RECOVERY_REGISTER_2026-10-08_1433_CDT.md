# AI Composer — Previous Sound Resources Recovery Register

**October 8, 2026, 14:33 CDT | Recovery inventory, NOT activation**
**Original protected source commit:** `0416abec7b6cd047e2af01e30b3d81bf4b694e0f`
**Source preservation branch:** `hardcopy-genre-structure-2026-10-08-1429-CDT`
**Companion per-style table:** `checkpoints/AI_COMPOSER_55_STYLE_RESOURCE_CROSS_REFERENCE_2026-10-08_1433_CDT.csv`

## Important distinction

All **55 original musical definitions** and **385 inactive planned stages** are present in the source snapshot, grouped into 13 musical-family references. This does NOT prove that 55 separate genres' recorded sound samples are all present in the GitHub working tree, mapped, and ready to play.

The project includes **program logic, pinned sample mappings, sound-library retrieval instructions and an archived runtime bundle** at `composer/runtime.b64`. Actual WAV/FLAC libraries are normally downloaded from upstream during `build_current_composer.sh`; their binary files are NOT all bundled into this GitHub source snapshot.

Do not conflate **source definitions preserved** / **sample bank download instructions preserved** / **sample files retrieved into deployment** / **playable render confirmed**.

## Recovered existing sample-bank sources already named in build/production code

| Existing resource ID | Source / program use | Caution |
|---|---|---|
| `KARORYFER_GROWLYBASS_V1_002` | Karoryfer Growlybass; sampled electric bass; `electric_bass_guitar`; legacy `electric_bass` alias declared in build | Check actual install and current alias routing |
| `KARORYFER_SHINYGUITAR` | Karoryfer Shinyguitar; distinct rhythm and lead programs; legacy `lead_guitar` alias declared in build | Preserve lead vibrato program and separate stems |
| `KARORYFER_BIG_RUSTY_DRUMS` | Karoryfer Big Rusty Drums; rock kick, snare, hat, tom, ride and crash instrument programs | Verify independent original sample graphs and separate stems |
| `GREG_SULLIVAN_E_PIANOS` | Greg Sullivan E-Pianos / Wurlitzer EP200; `electric_piano` | Read original license and preserve attribution |
| `FREEPATS_WORLD_PERCUSSION` | FreePats World Percussion; five-stroke conga mapping | Verify sample data and original kit relationships |
| `JAZZ_MEATBASS_PINNED` | Karoryfer Meatbass, sampled Jazz pizzicato double bass | Jazz Ballad's pinned samples only unless separately reviewed |
| `JAZZ_VSCO_CLARINET_PINNED` | VSCO 2 Community Edition sampled clarinet | Jazz Ballad's pinned samples only unless separately reviewed |
| `JAZZ_SWIRLY_BRUSH_PINNED` | Karoryfer Swirly Drums recorded brushed percussion | Jazz Ballad's pinned samples only; do not modify Rock kit |

The October 8 Jazz hard copy records **47 source-verified Jazz samples**, five recorded instrument role bindings and passing resource checks, but **not** a finished Jazz recording/3D audio return. The October 7 separate instrument audit records **five previously sample-graph-validated identities**: electric bass guitar, electric guitar, rock kick, snare, and hi-hat. Later changes must be checked independently against deployed output.

## References and storage locations

- Full genre profiles: `composer_overrides/genre_styles/genre_mix_ratios/{family}.json` (13 family reference files)
- Family and style lookup: `composer_overrides/genre_styles/genre_mix_ratios/index.json`
- Shared kit manifest: `composer_overrides/drum_kits/drum_kit_catalog.json`
- Original runtime archive: `composer/runtime.b64` (recreated at build time into `composer/runtime/`)
- Source bank installation instructions: `build_current_composer.sh`
- Jazz pinned source metadata and exact sample SHA/byte counts: `composer_overrides/jazz_ballad_recorded_resources.py`
- Resource admission and licenses: `composer_overrides/production_resource_policy.py`
- Future resource declarations: `composer_overrides/verified_future_instruments.json`
- October 7 prior audit (separate Library artifact): `AI_Composer_Instrument_Resource_Audit_R1_2026-10-07.md`
- October 7 prior 55-style CSV (separate Library artifact): `AI_Composer_55_Genre_Instrument_Audit_R1.csv`
- October 8 Jazz source snapshot (separate Library artifact): `AI_Composer_Jazz_HARD_COPY_2026-10-08.pdf`

## Preliminary audit totals of current family reference definitions

- 13 musical families, 55 independent styles, seven planned stages per style = **385** stages, **all inactive**.
- 315 individual track records; **129 with null instrument IDs** in the family-reference files (not proof corresponding sounds don't exist elsewhere).
- 43 styles point to a shared drum kit with an `unverified_*` reference identifier (not proof that no actual sample exists).
- All 55 profiles preserve numeric BPM lower and upper values. Verify live selection, timing and groove separately.
- The reviewed stage files that point directly to ordinary tracked files exist; legacy source paths may refer to files unpacked from `composer/runtime.b64`.
- Potential ID drift: preserved Rock musical profile is `ROCK_CORE_V2` while current isolated module `rock.py` announces `ROCK_V1`. Investigate without editing either file until traceability is established.

## Recovery method, no activation and no replacement

1. Recover every named original source and upstream license from existing build/manifest/pinned records, rather than inventing new sound banks.
2. For each genre and instrument, match musical role → code identifier → exact bank → exact mapping file → actual playable sample graph → separate stem output.
3. Mark individual entries as `DEFINITION_PRESERVED`, `REFERENCE_PRESENT`, `SAMPLE_MISSING_OR_UNVERIFIED`, `SAMPLE_GRAPH_VERIFIED`, or `RENDER_VERIFIED` independently.
4. Reconcile actual deployment state separately; a recorded file in an upstream repo is not a verified present installation.
5. Preserve all original files and existing work. Keep all 385 stage connections OFF, with no production code/mixer change.
6. Do not silently substitute GM/SF2 placeholders, generated synthetic samples, or a different drum kit.

**This register is additive documentation on an isolated backup branch. No original file, connection or runtime behavior has been modified.**
