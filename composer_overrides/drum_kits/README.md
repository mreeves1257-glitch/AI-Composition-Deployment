# Shared Drum Kit Catalog

A drum kit is a **reusable selection group** for verified original recordings, NOT a mixed sound or a new copy of the recordings. A genre points to one kit, and sets all kit members' intensity ratios in its own genre settings.

**Every kick, snare, hi-hat, tom, crash and ride remains its own independent track and WAV stem.** No drum parts are merged before the unchanged standalone 3D mixer. The original source instrument files/SFZ mappings stay unmodified.

The existing Rock and Jazz Ballad drum-kit source routes are preserved. The other historical kit names (e.g. `drums_latin`, `drums_electronic`) are **unverified group descriptors** and must not be treated as available recorded instrument mappings until verified.


## Preserved original recording references — 2026-10-08 inventory

The sound-source references recovered from existing Composer build instructions and Jazz Ballad's pinned sample list now live **inside this Drum Package**, without copying or editing original WAV/FLAC/SFZ recordings:

- `sources/rock_big_rusty_sources_2026-10-08.json` — real Big Rusty kick, snare, hi-hat, tom, crash, and ride program paths, including the existing `tom_tom` identifier alias.
- `sources/jazz_swirly_brush_sources_2026-10-08.json` — separate original recorded Jazz Ballad brush kick, snare, and hi-hat mappings. This does not replace Rock's kit.
- `sources/freepats_hand_percussion_sources_2026-10-08.json` — FreePats conga source mapping and the previously declared bongo onboarding configuration. Bongo availability is still subject to independent verification.
- `drum_package_inventory_2026-10-08.json` — a **dated, read-only** cross-reference for the selected drum kit and drum role identifiers in **all 55 genres**, including 11 preserved unverified historical kit descriptors.

These JSON files are **filing and provenance references only**: nothing automatically imports them into the Composer, no stage connection is active, and no genre was remapped to a different kit. The existing `drum_kit_catalog.json` continues to define the kit groups; each genre's own musical file continues to own rhythms, tempo, groove, dynamics, arrangement, and mix prominence.

**Audio-source caution:** A recorded bank listed here might be downloaded at build time rather than held in the Git repository. Source file recorded, mapping declared, sample graph validated, separate stem rendered, and finished audio heard are different verification levels. No silent synthetic substitutes and no claims that unverified kit names are playable.
