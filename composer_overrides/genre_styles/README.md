# Genre intensity ratios — 13 musical families, 55 separate styles

This reference folder contains **13 family JSON files**, each holding distinct style profiles by name. They replace the prior 55 flat genre-ratio JSON files, preserved in the immutable Git checkpoint branch `all-55-genre-ratio-reference-protected-20261008`.

Each `profiles[genre_name]` entry keeps that genre's own original instrument palette, separate instrument track slots, and mix intensity ratios. Related genres share a folder/file without merging their music or borrowing each other's ratio values.

**Drum kits are an independent shared module:** see `composer_overrides/drum_kits/drum_kit_catalog.json`. Every genre selects a kit by `selected_shared_drum_kit_id`, where appropriate. Kit sounds are original, universal, and read-only. Kick, snare, hi-hat, toms, and cymbals must remain separate output stems. The catalog's `unverified_*` entries are *only* old palette descriptors, not ready-to-play sampled kits.

**Production safeguards:** Rock retains its existing gain trims, Jazz Ballad retains its currently selected 0/0/+8/−3/−7/−22 dB relative instrumental goals, and the other 53 genre profiles are non-activated candidate balances. These files are organizational planning references, **not automatically loaded** by the production Composer; the standalone mixer and recorded instrument WAV/SFZ remain unchanged.

## Family organization
- **Rock:** ROCK
- **Jazz:** Swing, Jazz Ballad, Big Band, Jazz Waltz, Bebop, Cool Jazz, Dixieland, Jazz Fusion
- **R_and_B_Soul_Funk_Disco:** Rhythm and Blues, Soul, Funk, Contemporary R&B, Neo-Soul-related, DISCO
- **Country_Bluegrass:** Traditional Country, Country Rock, Country Ballad, Country Shuffle, Two-Step, Country Waltz, Bluegrass-related
- **Latin:** Bossa Nova, Samba, Salsa, Mambo, Rumba, Cha-Cha, Bolero
- **Electronic_Dance:** House, Techno, Trance, Ambient Electronic, Downtempo, Breakbeat-related, Garage-related, Experimental Electronic, Chugg / #chugg
- **Indie_Alternative:** Eclectic New Indie
- **Reggaeton:** Mexican Reggaeton
- **Afrobeats_AfroLatin:** Afrobeats, Afro-Latin / Afrobeats Fusion, Afro House
- **Trip_Hop:** Trip-Hop, Contemporary Trip-Hop / Trip-Hop Revival
- **Hybrid_Custom:** Regional Electronic Hybrids, Genre-Breaking / Borderless, Custom Hybrid, Custom Style, Controlled Custom Style Profile
- **Classical_Acoustic:** Classical, WALTZ, PIANIST
- **New_Age_Spiritual:** New Age, Spiritual

A common loudness measurement procedure helps calibrate original sample/stem intensities, but published standards don't supply a universal numeric gain table for all genres. Follow measurements and actual finished-music listening before approving a mix.
