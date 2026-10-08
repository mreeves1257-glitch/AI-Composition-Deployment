# Universal Composer Instrument and Genre Boundaries

Effective for all current and future genre-specific development.

1. **Downloaded instruments are universal, original, read-only sources.** Preserve original WAV/FLAC samples, SFZ mappings, source revisions, and pinned hashes. No mixing or genre correction edits a sample or instrument definition. If a new source is ever wanted, treat that as an explicitly approved separate acquisition, not an overwrite.
2. **One independent instrument role per logical track and rendered audio stem.** Piano/HARMONY, clarinet/LEAD, acoustic BASS, KICK, SNARE, and HAT remain separate through the Composer output handoff to the standalone final 3D mixer. Do not pre-bundle instruments into a single stem or substitute one track's audio for another.
3. **Genre-specific composition belongs in the selected genre's file.** Tempo, chord progression, stylistic harmonic voicings, phrasing, instrumental relationships and expressive arrangement must suit the selected genre. Shared utility code must not silently force two instruments to play identical melody lines.
4. **Genre-specific relative intensities belong in that genre's mix profile.** Calibrate against actual measured rendered stem audio; keep numerical adjustments in each genre's own settings. Never convert genre mix corrections into global changes to samples, instrument registry, plug, Rock or other styles.
5. **Separate melody and accompaniment by musical role.** A lead should have its own phrasing, contour and entrances; unison or doubling is permitted only if explicitly intended by that genre's composition, not as an unexamined side-effect.
6. **No genre-by-genre cloning before an approved complete reference.** Reserved Jazz genres remain unimplemented until Jazz Ballad is approved. No promise of audible sound without a real completed audio render and listening evaluation.
7. **Mixer is last and separate.** The standalone 3D mixer mixes independent instrument stems using the genre-approved per-track metadata; it does not create the score, edit source instruments or perform hidden rearrangements.

## Current Jazz Ballad application (2026-10-08)
- The six actual downloadable instrument source references remain unchanged in `Jazz/instrument_library.json` and `Jazz/instrument_packages/jazz_ballad.json`.
- The style's only output-level adjustments are in `Jazz/jazz_ballad_mix.json`, applied by `Jazz/ballad_leveler.py`.
- Clarinet's independent melody is composed by `jazz_arranger_style.py` through the *Jazz Ballad* routing only; piano data remain unchanged.
- Instrument content is untouched, and Rock and other Jazz styles are unaffected by these Ballad-only changes.

## Universal measurement method (not a universal fixed mix ratio)
For each isolated rendered stem: record instrument/source identity, active-window RMS, true/sample peak as appropriate, and final genre gain; use the same measurement methodology regardless of genre. A numeric target for a genre is a mixing preference requiring ear-based review, not a property of the downloaded WAV file.
