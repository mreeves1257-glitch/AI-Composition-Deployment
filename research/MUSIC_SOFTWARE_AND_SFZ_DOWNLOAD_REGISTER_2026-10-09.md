# MUSIC SOFTWARE & RECORDED-SAMPLE DOWNLOAD REGISTER — 2026-10-09

**Scope:** Research downloads for the existing AI Composer only. This does not activate production, replace the ONE shared interpreter or overwrite original recorded instruments.

| Resource | Type / status | License | Why |
|---|---|---|---|
| Mido 1.3.3 | APPROVED OPTIONAL RESEARCH TOOL. PyPI downloads captured by isolated GitHub Action, not included in deployment. | MIT | Reads/writes real Standard MIDI Files (SMF); the existing Composer already consumes MIDI in its SFZ renderer. We can export exactly the 55 original genre source-pattern seeds while retaining isolated instrument tracks. |
| Ethan Winer Collection (SFZ) | CANDIDATE SOURCE; NOT ADDED TO TARGET REGISTRY. https://github.com/sfzinstruments/EthanWiner.Soundfonts | Listed Public Domain (original samples); review converted SFZ license. | Small (~17 MB) public-domain recorded source candidate for cello, bassoon etc. Contains ARIA extension opcodes; check sfizz support and original sample zones before using or claiming 130 unresolved roles filled. |
| SFZ Instruments catalog | REFERENCE ONLY. https://sfzinstruments.github.io | Various; check *each* source. | Discover other recorded original SFZ sources by identity and license; don't automatically download hundreds of megabytes. |
| Yamaha MIDI Song to Style v1.2.0 | EXTERNAL WINDOWS 11 / macOS software; REFERENCE ONLY. https://usa.yamaha.com/products/musical_instruments/keyboards/apps/midisong_to_style/index.html | Yamaha proprietary license, must accept individually. | MIDI→style examples. Not a Linux Render dependency; do not redistribute/install as part of Composer. |
| Korg Pa5X Style Creator Bot | BUILT INTO Pa5X firmware, NOT downloadable standalone. https://cdn.korg.com/us/support/download/files/69f13112591895c3222b45805422b393.pdf | Korg proprietary | Behavioral reference for MIDI song→style composition. No separate software module to add. |
| sfizz / sfizz_render | **ALREADY PART OF ORIGINAL BUILD**. https://github.com/sfztools/sfizz | Check upstream bundled licenses | Existing build_current_composer.sh installs sfizz renderer from pinned upstream 1.2.3. Do not add duplicate renderer. |
| MMA / Musical MIDI Accompaniment | RESEARCH ONLY. https://github.com/infojunkie/mma | GPL-2.0 | May help as comparative arranger research. Earlier Rock-only MMA-backed experiment archived. Do not restore into shared runtime or silently copy GPL code. |

## Actual downloadable Composer deliverable
`research/export_55_original_genre_midi_previews_20261009.py` uses `mido==1.3.3` to generate 55 original **seven-bar** Standard MIDI Files, one per genre, independent role tracks, with exact tempo/meter and genre-authored note patterns. Does not contain proprietary styles or audio. The GitHub Action publishes a downloadable research artifact containing the 55 MIDI previews, manifest and optional licensed Mido Python wheel.

**Crucial limitation:** Standard MIDI files contain events, not recordings. Generic MIDI playback on an Android phone or computer will not sound like our actual SFZ instruments, so no full song/audio claims. All preserved seven stages, 22 capability modules, 55 genre profiles, original audio and standalone final 3D mixer remain as before.

## Remaining unresolved
130 source-pattern role links remain blocked pending exact recorded-program mapping and sample zone/articulation confirmation. The 55 previews prove note-structure export, not quality or sample authority. Real audio audition, Rock kick/bass/guitar balance and full-length genre arrangements remain separate.

**Download/research order:** 1. Mido 1.3.3 for standard MIDI workflow, 2. preserve/download separate 55-preview archive, 3. inspect only selected recorded SFZ candidate banks on sandbox, 4. verified source mapping, 5. instrument audio stems/listening. Yamaha/Korg apps are *not* necessary Composer code dependencies.
