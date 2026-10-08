# Real Instrument Onboarding — R1

The first **automatic onboarding test** uses FreePats' already-installed, recorded bongo samples. This leaves the five previously verified audio libraries unchanged.

To add a compatible *new* recorded SFZ instrument, edit only `composer_overrides/verified_future_instruments.json`:

1. If the bank is new, enter `resource_id`, the official GitHub HTTPS `.git` URL, `branch`, **exact 40-character upstream commit SHA**, source title and verified license (CC0 / CC-BY 3.0 / CC-BY 4.0). This prevents upstream content changing silently.
2. Add one `new_instruments` entry using the bank ID, source SFZ path, actual MIDI audition notes, and exact sample-reference count. If the source MIDI notes differ from the genre notes, provide `note_map` and a separate `derived_sfz` basename. All remapped notes must be audited.
3. Commit the manifest. The standard composer build clones new banks, confirms the exact SHA, checks every sample, renders each required audition note, and registers the instrument only after all checks succeed. Failed builds do not replace the live composer.

Current proof entry: `bongo` from authentic FreePats recorded bongos; original SFZ notes 51/52/53 map to 60/61/62 (muted/high/low), with 31 recorded sample references.

**Scope:** standard SFZ mappings and simple group-note remaps. Complex articulations, custom macros, proprietary dependencies or altered SFZ file layouts need an explicit compatibility adapter and its own tests. Do **not** pretend those are automatically compatible.

**Boundaries:** this never edits the genre composer, source audio, existing instrument mappings, control panel, plug, or 3D mixer. It does not prove an entire genre has successfully composed and mixed a song. The existing build still compiles sfizz when the Render build cache misses; faster binary caching is a separate infrastructure improvement.
