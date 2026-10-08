# AI Composer — Genre family directory (October 8, 2026)

**One family folder per heading: 13 family folders, 55 distinct genres.** `index.json` maps each named genre to its family's `profile.json`. Every family owns its own independent style parameters, instrument-role references, seven ordered **planned** stages and six reserved handoffs. The source filing structure does not mean any complete song is operational.

## One authoritative home per family

- `Rock/profile.json`: ROCK. Older, unsuccessful Rock music, balance, source probes, subkick, and tests are gathered **under Rock/**.
- `Jazz/profile.json`: Swing, Jazz Ballad, Big Band, Jazz Waltz, Bebop, Cool Jazz, Dixieland, Jazz Fusion. Existing style code, arranger, source links, mix controls and tests are gathered **under Jazz/**.
- `R_and_B_Soul_Funk_Disco/profile.json`, `Country_Bluegrass/profile.json`, `Latin/profile.json`, `Electronic_Dance/profile.json`, `Indie_Alternative/profile.json`, `Reggaeton/profile.json`, `Afrobeats_AfroLatin/profile.json`, `Trip_Hop/profile.json`, `Hybrid_Custom/profile.json`, `Classical_Acoustic/profile.json`, `New_Age_Spiritual/profile.json`.

No duplicate Rock.py or Jazz profiles outside those homes. The former `genre_mix_ratios/` collection has been consolidated into these family directories. The `profile.json` files are the authoritative organization references; associated `.py` files may contain earlier, unsuccessful musical code.

## IMPORTANT operational status

**ROCK and JAZZ: DYSFUNCTIONAL.** Neither delivered reliable finished, playable full-song output in the user's experience. They must not be treated as working examples or templates. Their accumulated files are retained for examination, not assumed correct.

**Other 11 families:** end-to-end output unverified. All **55** genre entries remain not ready for verified composition. No selected family is marked production-ready.

All 385 reserved per-genre stage entries are inactive; all 330 planned cross-stage links are `RESERVED_NOT_CONNECTED`. (Each genre has 7 stages and 6 handoffs.) This directory does not enable the genre engine, alter the already deployed services, or assert a full 3D master exists.

## Shared libraries and runtime

The immutable recorded WAV/SFZ samples live in shared `sound_resources`, not copied into family folders. Drum kit catalog is `composer_overrides/drum_kits/drum_kit_catalog.json` (shared). The SFZ renderer, core engine, HTTP plug, and standalone 3D mixer remain common services/utilities.

A genre's family `profile.json` can cross-reference universal sound libraries without owning the original sample. Genre-specific code and tests are stored in the family folder. Runtime construction installs the `genre_styles` package as one unit, without extraneous flat Rock/Jazz source copies.

Run `python composer_overrides/genre_styles/validate_profiles.py` to verify 13 folders/55 profiles/operational labels/relative pointers and no activated stage wiring. This is *not* a live music test. Full song work remains separate.
