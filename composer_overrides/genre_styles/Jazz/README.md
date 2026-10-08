# Jazz — shared instruments, separate musical styles

The Jazz family is one directory, with eight independent music-style modules.
No genre's musical arrangement is stored in a giant cross-genre file.

## Canonical resources

- `instrument_library.json` is the **one source of truth** for available Jazz instruments: instrument ID, registry binding, SFZ program, source bank, verified MIDI note range, and role.
- All actual recorded WAV/SFZ files remain in the shared runtime `sound_resources` library. The Jazz directory references those files. It **does not duplicate or re-render** them.
- `instrument_packages/<style>.json` lists only instrument IDs from the shared Jazz catalog, selected for that style. Each has the same structural schema and six initial role links.
- `instrument_packages/__init__.py` resolves each selected role back to the canonical Jazz catalog. It rejects missing mappings and never substitutes synthetic instruments.

## Individual styles

| Genre | Style file | Instrument link manifest |
| --- | --- | --- |
| Jazz Ballad | `jazz_ballad.py` | `instrument_packages/jazz_ballad.json` |
| Swing | `swing.py` | `instrument_packages/swing.json` |
| Big Band | `big_band.py` | `instrument_packages/big_band.json` |
| Jazz Waltz | `jazz_waltz.py` | `instrument_packages/jazz_waltz.json` |
| Bebop | `bebop.py` | `instrument_packages/bebop.json` |
| Cool Jazz | `cool_jazz.py` | `instrument_packages/cool_jazz.json` |
| Dixieland | `dixieland.py` | `instrument_packages/dixieland.json` |
| Jazz Fusion | `jazz_fusion.py` | `instrument_packages/jazz_fusion.json` |

`harmony.py` is a shared *Jazz-family* seventh/sixth-chord helper, not a store of style-specific chord patterns. Each style owns its own progression and will own future stylistic refinements.

## Source and verification boundaries

The Jazz library currently contains **six verified recorded mappings**, originally established for Jazz Ballad: Wurlitzer piano, VSCO clarinet, Karoryfer double bass, and three Swirly drum/brush roles (soft kick, brush snare, hi-hat). Jazz Ballad's instrument binding status is `VERIFIED_RECORDED_SOURCES`. The other seven styles have links to the same available library but remain marked `STYLE_ROUTING_NOT_YET_VERIFIED` until their score-specific palette/notes and audio are checked. Linking is not equivalent to proving that the instruments are playing audibly.

The electric-piano recording and the instrument rendering files are **preserved unchanged**. Jazz Ballad's arranger-style event transformation, relative mixer gains and repetition controls are separate from the piano source.

## Isolation rule

- The root `genre_styles/registry.py` only dispatches the chosen genre to its own module.
- **Rock stays in `genre_styles/rock.py`** and keeps its established performance/balance implementation.
- Theory validation, the sample library, audio rendering, plug, control panel and standalone 3D mixer remain common infrastructure; their musical policies do not get merged into Jazz files.
- Never move entire recorded sample banks into a genre folder or rewrite another genre to implement a Jazz correction.

## Preserved checkpoints

The prior cross-genre working snapshot is retained in Git under `jazz-pre-consolidation-hardcopy-20261008`, and the pre-Jazz-audibility baseline under `protected-composer-before-jazz-audibility-2026-10-08`. The changes here are project organization and shared-resource linking, **not** evidence that every Jazz genre has finished, audibly verified music.
