# REFERENCE — Instrument Tuning, Timbre, Resonance, and Calibration Instructions

**Date:** 2026-10-10
**Purpose:** Record real published instrument/sample calibration instructions relevant to all 55 genres without altering or "tuning" any sound now.

## Critical distinction
A genre's MMA groove controls **when instruments play, which symbolic notes/voices, rhythmic patterns, articulation length, sequence, transitions, fills, and dynamics**. The SFZ sampler's instrument/sample mapping controls **which original recorded WAV responds to each MIDI note/velocity, natural pitch, attack/release behavior, articulation switching, filters, and (where explicitly installed) resonance parameters**. A manufacturer arranger's own Voice/Program parameters apply to *that manufacturer's sound engine* and do not automatically transfer to project SFZ WAV instruments. No manufacturer-proprietary patch shall be silently used as a substitute.

A sampled clarinet, trumpet, acoustic bass, piano, or drum **already has a recorded acoustic spectrum and instrument resonance**. Setting an SFZ filter's `resonance` property is **an electronic filter effect**, not measurement of or correction for the instrument's natural resonances. Physical body/bore resonances and instrument tuning/intonation can be investigated from authentic sample audio separately. Calibrating does not mean that every genre or instrument needs added resonant boost, EQ, global A4 retuning, or envelopes.

## Official / documented reference sources and their scope
**1 — SFZ format (the actual sampler program format used by the project)**
- SFZ home, instrument creation tutorials and technical reference: https://sfzformat.com/
- Whole opcode index (including pitch, sample maps, filter/resonance, note/velocity ranges): https://sfzformat.com/opcodes/
- Key/note mapping: https://sfzformat.com/opcodes/key/
- Per-sample root note: https://sfzformat.com/opcodes/pitch_keycenter/
- Pitch fine tuning, in cents: https://sfzformat.com/opcodes/tune/
- Filters' cutoff, in Hz: https://sfzformat.com/opcodes/cutoff/
- Filter resonance, in dB: https://sfzformat.com/opcodes/resonance/
- ADSR envelopes / sustain / release: https://sfzformat.com/tutorials/sfz-1-egs/
- Sustained note mapping: https://sfzformat.com/tutorials/sustained_note_basics/
- More tutorials for vibrato, legato, sympathetic resonance, drums, cymbal muting and brush stirs from https://sfzformat.com/ (these are HOW-TO references, not mandatory DSP treatments).

**2 — Yamaha's own instrument editing and keyboard tuning references (architectural, not project sound files)**
- Genos/Genos2 official download/manual library: https://usa.yamaha.com/products/musical_instruments/keyboards/arranger_workstations/genos/downloads.html
- Official Genos specifications and Tuning reference (414.8 to 466.8 Hz around 440 reference, approximated): https://usa.yamaha.com/products/musical_instruments/keyboards/arranger_workstations/genos/specs.html
- Genos reference manual describes **Voice Edit** and per-part attack, release, filter cutoff/resonance, transpose/tuning, vibrato/modulation and EQ. Original PDF linked through official downloads above: https://usa.yamaha.com/files/download/other_assets/7/1131007/genos_en_rm_h0.pdf
- These parameters belong to Yamaha internal voices, NOT automatically to our recorded SFZ sample banks.

**3 — Korg arranger instrument calibration/voice editing references (architectural, not project presets)**
- Official Korg Pa5X User, Performance Guide and sound creation references: https://www.korg.com/us/support/download/product/0/895/
- Includes `Making Pa5X Sounds using TX16Wx Sampler`, demonstrating a sample-based sound construction path.
- Do not assume Korg proprietary oscillators/samples/styles will be copied or work in our sampler.

**4 — MMA original instructions (music/style, not physical calibration)**
- Official author reference: https://www.mellowood.ca/mma/online-docs/html/ref/node1.html
- MMA `Voice`, `Articulate`, `Octave`, `Rtime`, `Rvolume`, named tracks and MIDI directives affect symbolic MIDI playback/performance. They are not acoustic body-resonance measurements or automated tuning of an SFZ library.

## Non-destructive calibration procedure FOR EVERY RECORDED INSTRUMENT

These are **inspection/verification gates**, not approval to modify. Reuse same procedure for instrument programs across the 55 genres, but retain separate genre-specific playing rules.

1. **Identify the original source** — instrument, performing technique/articulation, sample library and publisher, license, immutable source checksum(s), installed SFZ program and all referenced WAV paths. Do not use a generic GM patch just because voice names look similar.
2. **Capture intended musical register** — original instrument's written/sounding pitch distinction where applicable (B-flat clarinet or trumpet in B-flat), expected playable MIDI notes, per-sample `key` / `lokey` / `hikey`, `pitch_keycenter`. Determine whether the project uses concert MIDI pitch and whether a transposing notation layer is involved before mapping. Make no default octave corrections without evidence.
3. **Measure actual tuning safely** — keep a clean original, measure pitched sample fundamentals/relative intonation at stable note positions and compare to its documented pitch center and **explicit reference tuning**; record cents discrepancy and stable vs time-varying pitch. **Do not automatically pitch-shift samples or universally force A4=432 or 440**. A4 reference is a controlled choice, not a "better" instrument sound claim.
4. **Check SFZ velocity/sample zones** — `lovel`, `hivel`, articulation/keyswitch layers, transients and release; play every mapped key and several velocities with the real original SFZ renderer. Test low/high border notes and note-off behavior to catch silent notes or stuck notes.
5. **Preserve acoustic identity/resonance** — optionally inspect recorded spectral energy, attacks, decays, harmonics/partials, body resonance, sample release tails and round robins. These characterize the recording; do not overwrite with artificial global resonance, filter, EQ or reverb values. If an approved instrument program already uses SFZ `cutoff` or `resonance`, preserve and verify it; note that increasing filter resonance can create large peaks and clipping.
6. **Verify MIDI performance** — note lengths, legato, sustain, articulation, vibrato or modulation availability should be distinguished from native sample traits. A short MIDI note cannot create natural long breath sustain unless the sample and SFZ envelope/loop can support it. For drums, verify incoming MIDI triggers (e.g. ride vs hi-hat), one-shot lengths, and no duplicates.
7. **Check clarity with isolated stems** — compare original WAV sound, dry SFZ note, original composed stem, and full stereo mix using immutable sample data; verify headroom and distinct role audibility. Separate instrument calibration findings from stereo mixer/3D effects.
8. **Record, do not silently change** — store measurements, source citations, sample source checksum, program ID, pitch reference and confidence, any change request, and a user-approved decision. Flag unknowns `NEEDS_VERIFICATION`. Stop before destructive tuning or level adjustments.

## Required instrument-specific kinds of checks
- **Clarinet/trumpet/winds:** transposing instrument notation vs concert MIDI, sampled register coverage, breath attack, natural sustain and release, vibrato/legato availability, audible partials.
- **Piano/electric piano:** per-note sample center pitch, velocity layers, sustain/release and natural decays (do not impose wind ADSR); harmonic overtones can be inharmonic with stiff strings.
- **Double/electric bass:** note mapping, pitch and low-frequency energy, plucked sustain/damping, bass-guitar/subkick distinction.
- **Electric guitars:** fret registers, strum/chord overlaps, vibrato techniques recorded or safely controllable, note-off lengths and natural sustain.
- **Drums/cymbals/brushes:** *unpitched in a musical sense*; do not try to force each sample to A440. Verify trigger mapping, brush stroke vs one-shot, dynamic sample layers and sonic decay/resonant tails. Brushes can sound too loud at the same MIDI velocity due to sample recording; note it but do not adjust during the current connectivity phase.
- **Synthesizers/spectral instruments:** explicitly documented oscillator/sample parameter model needed; electronic filter resonance is a possible expressive parameter, not evidence of a physical instrument resonance.

## Locked project constraints
- User's current round permits **original instrument clarity, genre rhythm, authentic source routing, and real complete playback ONLY**. This document does not authorize changes to clarinet sustain, brush level, piano, bass, guitar, trumpet, tune, reverb, resonance or stereo position.
- Preserve approval checkpoints: Rock2's clearer upbeat arrangement and Jazz Ballad's recognizable separate clarinet/piano/other original instruments.
- All new instruments must be backed by original licensed recordings and verified sample maps before claiming audio readiness. The optional 3D mixer stays LAST.
- No per-instrument frequency data or specific "ideal resonance" values are contained in MMA style files. Need source-specific recorded audio measurements for such data; mark unknown rather than invent.

**Controlled relationship:** This is a REFERENCE companion to `research/ALL55_PUBLISHED_GENRE_STYLE_SOURCE_CATALOG_2026-10-10.json`; it does not replace that catalog, source code, active genre configurations, or hard copies.
