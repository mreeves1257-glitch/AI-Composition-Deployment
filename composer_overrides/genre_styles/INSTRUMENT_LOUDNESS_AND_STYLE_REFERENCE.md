# Universal Instrument Measurement and Genre Mix Reference — v1

## Purpose and boundaries
All downloaded audio samples, SFZ programs, pinned hashes and instrument source definitions are **universal, read-only reference material**. No genre correction edits or replaces them. Each instrument occupies its own logical track and final-render stem. Each individual genre sets its own score, performance, arrangement, instrument roles, and MIX METADATA; the standalone 3D mixer uses the final separate rendered stems.

**There is no generally accepted industry-wide numeric table for "piano X dB, clarinet Y dB, kick Z dB" across every genre.** Never represent provisional Composer levels as an AES/EBU or manufacturer standard. Sample libraries describe/how to play recorded sounds; most do not supply a calibrated cross-library mix.

## Verified technical references
1. AES — Loudness Basics / ITU-R BS.1770: standardized loudness measurement, spectral weighting and gating.
   https://aes.org/resources/audio-topics/loudness-project/loudness-basics/
2. EBU — Tech 3341 / EBU Mode: momentary 400 ms, short-term 3 s, integrated programme loudness meters.
   https://tech.ebu.ch/publications/tech3341/
3. AES — Loudness Normalization: preserving musical balance matters; don't simply normalize all instruments or tracks to identical loudness.
   https://aes.org/resources/audio-topics/loudness-project/loudness-normalization/
4. Korg Pa arranger style editing: separate Sound and Expression (MIDI CC#11) for each style-element track; per-intro/variation/ending relative levels; track Volume is separate.
   https://www.manualzz.com/doc/o/2o1a6/korg-pa4x-oriental-user-manual--customizing--recording-and-editing-the-styles-and-pads
5. Yamaha — MIDI Song to Style: arranger accompaniment has intros/main/fills/endings and user-selected/re-mixed individual tracks.
   https://usa.yamaha.com/products/musical_instruments/keyboards/apps/midisong_to_style/index.html
6. Karoryfer — Swirly Drums original source description: 20-inch marching kick, brushed snare stirs/flutter, kit described as more indie than traditional jazz; if a sound is naturally swishy or lacks a deep sub-frequency response, genre gain cannot turn it into a different instrument.
   https://shop.karoryfer.com/pages/free-swirly-drums
7. SFZ brush stir explanation: continuous, noise-like brush stirs are distinct from transient snare strikes.
   https://sfzlab.github.io/sfz-website/documentation/tutorials/brush_stirs/
8. Sound On Sound real jazz session mixing notes: solo, listen, adjust instrument contributions over musical sections, preserve relationships, use automation and separate bass/drum balancing.
   https://www.soundonsound.com/techniques/session-notes-selwyn-jazz-part-2

## Universal method, applied WITHOUT changing source files
- **Identify** each original sample source and SFZ program using catalog key, resource_id, file/path and pinned provenance. Verify identity on every mix render.
- **Render** each instrument into one isolated track/stem from the SAME musical score used for the mix. Do not merge instruments and do not test with a different sample substituted for the source.
- **Measure** on each stem: source sample peak and preferably true peak, active sound level (RMS and optionally BS.1770 K-weighted momentary/short-term loudness), timing/duration, transient crest factor, silence ratio, number of notes, and broad low/mid/high spectral character. Always document the actual measurement method and settings.
- **Distinguish** percussive short hits (kick, snare, hat) from sustained notes (clarinet, piano, bass). A whole-song loudness figure cannot by itself establish whether short kick transients are perceptible; neither identical RMS nor identical gain guarantees equal musical presence.
- **Assign roles** inside the selected genre: foreground melody, harmonic support, acoustic low foundation, kick pulse, and quiet percussion. Check overlapping notes and frequency masking: two separate tracks can still be perceptually indistinct if they double the same note at the same time.
- **Choose a reference** from the musical arrangement, normally its important foreground musical voice/anchor. Store per-role *relative gain targets* in that genre's own mix profile, not in a sample bank or shared registry.
- **Balance by section** where musically justified (intro, main, bridge, ending). This follows professional arranger style practice. This is a DESIGN RULE for future work, NOT a claim that our Composer already implements section-wise fader automation.
- **Render and audit** the complete actual music: verify separate stems, number of kick hits, each stem audible/non-silent, measured ratio achieved under headroom limits, and reference playback on expected speakers. A successful static test or built service does not prove a deep kick is audible.
- **Do not** change recorded sample amplitude, SFZ volume opcode, velocity maps or instrument identity to achieve a genre level. Affect only that genre's final per-track mix gain.

## Present Jazz Ballad project-selected listening ratios — not standards
Current request before audition: piano 0 dB reference, clarinet 0 dB (independent melodic track, same intensity), kick +8 dB to bring up the short transient, double bass -3 dB, hi-hat -7 dB, brush snare -22 dB (ten dB below previous). These are ACTIVE RMS relative mix TARGETS, not necessarily achieved or perceived outcomes. Final adjustments must follow audio.
The clarinet's different melody and rhythmic entrances belong in Jazz Ballad arranger instructions, *not* in a new clarinet instrument file. Brush snare sound is a Swirly stir/brush articulation, not verified as a separate ocean drum.
