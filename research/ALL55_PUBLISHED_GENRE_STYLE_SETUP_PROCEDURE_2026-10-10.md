# ALL 55 GENRES — PUBLISHED-STYLE SETUP PROCEDURE
Date: 2026-10-10
Status: CONTROLLED REFERENCE; not a live production update.

## Linked authorities
- All 55 individually indexed source candidates and source statuses: `research/ALL55_PUBLISHED_GENRE_STYLE_SOURCE_CATALOG_2026-10-10.json`
- 23 source-authored MMA style files preserved UNMODIFIED: `research/genre_reference_sources/mma/lib/` (with `research/genre_reference_sources/mma/UPSTREAM_GPL2_LICENSE.txt`)
- Instrument sample calibration documentation: `research/INSTRUMENT_TUNING_RESONANCE_AND_SFZ_CALIBRATION_REFERENCES_2026-10-10.md`
- Original published arranger setup documentation: `research/EXISTING_PUBLISHED_GENRE_STYLE_SETUP_INSTRUCTIONS_2026-10-10.md`
- MMA library frozen at commit `c52943c31aa1e64fa9b5313620d5065f91c22773`
- Official manual: https://www.mellowood.ca/mma/online-docs/html/ref/node1.html
- Official groove setup: https://www.mellowood.ca/music/essays/mma/mma-groove.html
- JJazzLab Yamaha style description: https://github.com/jjazzboss/JJazzLab-UserGuide/blob/master/rhythm-engines/yamjjazz-rhythm-engine/yamaha-styles.md

## Exactly the same verification process for EACH of the original 55 genres

1. **Select exact original genre ID** from `composer_overrides/genre_styles/index.json`. Read its original family `profile.json`, meter, tempo, authentic style/groove and recorded instrument assignments. Do not relabel a different genre as selected.
2. **Select published source** from `ALL55_PUBLISHED_GENRE_STYLE_SOURCE_CATALOG_2026-10-10.json`. Preserve the exact upstream filename and SHA. The catalog has 22 directly named candidates plus Rock2 (23 published direct/selected), 14 related-but-not-identical references, 18 without a verified source. Related or unmatched files CANNOT become playing styles without separate matching research and review. A named published match still needs actual audition and source verification.
3. **Follow the REAL published instructions.** For MMA, honor actual `Include`, `Time`, `SeqSize`, `Begin Drum/Bass/Chord/Walk`, `Sequence`, `DefGroove`, `Groove`, `Intro`, `Fill`, `Ending`, required included libraries and supported syntax. Do not invent placeholder `chord_progression` implementations to hide missing sections. Obtain a functional interpreter/groove source rather than merely marking a file active.
4. **Keep Composer's independent songwriting intact.** Compose fresh chords/key/lead/melody, form, sections and seed. The chosen published style supplies its authentic accompaniment/genre performance, not a single repeated song. The original performance pipeline remains Composer → MIDI → each genre's interpreter → original recorded SFZ instruments → normal stereo → OPTIONAL separate 3D mixer LAST. Do not duplicate or insert an extra unrelated interpreter globally.
5. **Prove the full MIDI handoff.** Verify genuine input/output, tempo/meter, separate named instrument tracks, note/duration integrity, score variation across new songs, correct intro/fill/ending, MIDI type/PPQ and source checksum. A 7-bar source sketch is NOT a complete recording. A name-only pass is NOT a functioning genre interpreter.
6. **Verify the recorded instruments NON-DESTRUCTIVELY.** Match EVERY original instrumental role to the exact licensed sound-library recording and SFZ program. Check keycenter, note zones, concert vs transposing pitch where relevant, note/velocity mapping, sustain/release, original natural resonance and acoustic timbre, one-shot percussion triggers, and headroom. Missing or incorrect sources must block. Use separate instrument calibration reference; do NOT impose new EQ, envelopes, resonance, 432/440 retuning, gain, vibrato or other changes in this phase.
7. **Render full stereo and listen.** Create complete independently verified audio with ALL expected stems actually audible, no doubled kick/snare/brush, no silent instruments, and recognizably authentic genre rhythm. Listening approval is separate from programming/tests. Only after passing should live activation be considered and checked, with existing controls and approved Rock2/Jazz Ballad audio preserved.

## Per-genre completion receipt
Track: exact original genre ID + profile ID; source path and frozen SHA; source status and documented commands; chosen groove/variation; tempo and meter; original role definitions; real Composer MIDI hash and musical section counts; recorded SFZ resource IDs/license/source checksums; note-range/velocity coverage; stem audio evidence; real complete stereo proof; user listening observations; separate DEVELOPMENT_CONNECTED, AUDIO_VERIFIED, and LIVE_ACTIVATED statuses.

## Protective boundaries
- No mixing, volume, clarinet/brush/timbre, filter-resonance, tuning or original-sample edits in this connectivity phase. Instrument tuning/calibration docs are research references for later, not permission to change settings now.
- The MMA source code and published GPL-2.0 style files remain verbatim with their upstream license; any integration/distribution must satisfy the applicable GPL license obligations.
- Yamaha/Korg proprietary voices/styles are NOT automatically interoperable with original SFZ recordings and must not be copied or substituted.
- The source library DOES NOT cover every one of the 55 custom/specialized genres precisely. Do not claim all 55 musical styles or recorded audio are active.
- Previously working Rock2 and Jazz Ballad remain protected; this guide adds no new audio execution.
