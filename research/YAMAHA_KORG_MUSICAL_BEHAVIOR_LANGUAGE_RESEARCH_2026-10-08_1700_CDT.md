# Yamaha Genos2 / Korg Pa5X — What Makes Instrument Playback Musically Human?
**Research checkpoint:** 2026-10-08 approximately 17:00 CDT (time supplied from current conversation)  
**Scope:** Primary-source technical investigation for the existing AI Composer. **RESEARCH ONLY; NO RUNTIME PATCH, NO LIVE TEST, NO PROPRIETARY CODE EXTRACTED.**  
**Examined saved Composer main at beginning:** `d2b7e4a84f75bb089774fdb8669f2e6f141bfd1e`.  
**User direction:** Rock and Jazz are dysfunctional for complete-song playback and are **not** to be used as working genre templates. All 55 genres are in 13 canonical folders, with 7 stages per genre and all stage handoffs dormant. Concentrate on the missing *behavior instruction language*, not more instrument recordings or another file reorganization.

## Central finding

No single Yamaha or Korg universal "human sound" MIDI command exists. Arranger instruments combine at least THREE distinct engines:
1. **Style/arranger logic**: musical sections, genre grooves, dedicated instrumental parts, chord recognition, chord-variation selection, pattern transposition, register constraints, and note retrigger/retuning at chord changes.
2. **Instrument-specific expressive state machine**: knows how an instrument is played (slurred versus detached, first note versus connected note, repeated note versus different note, selected strings/frets, breath/finger noise, damping, note-release or slide). This maps musical intent and context to the particular player's articulated samples and controller/keyswitch functions.
3. **Time-varying performance event writer**: emits correctly ordered Note On/Off with velocities, overlaps, note lengths, CC1/CC11/CC64/etc., pitch bends, aftertouch or instrument-specific switches. Changes occur at musical times, not only at tick zero. Whether any message has an effect depends on the chosen SFZ patch's actual controller mapping and the sfizz renderer's support.

These are not the same as the final stereo mixer or a generic random "humanize" knob.

## Yamaha Genos2 — primary reference findings

Yamaha Genos2 [Reference Manual](https://usa.yamaha.com/files/download/other_assets/1/2318561/Genos2_reference_manual_En_C0.pdf) and [Genos2 owner's manual](https://data.yamaha.com/files/download/other_assets/4/2318564/Genos2_owners_manual_En_D0.pdf):
- **Super Articulation (S.Art)** recognizes the way successive notes are played, e.g. connected saxophone notes, slides between guitar tones, attack/fingering/breath noises. It may select different articulations from note overlap, speed/interval, velocity, or an assigned articulation control.
- **S.Art2 with AEM (Articulation Element Modeling)** uses additional recordings/techniques for wind/strings; e.g. slurs, glissandi, note-end nuances; appropriate default vibrato can be adjusted by joystick. It is not a generic effect to be applied after mixing. Yamaha documents ART.1 / ART.2 / ART.3 controls; their effect varies by *selected Voice*.
- **MegaVoice**: individual **velocity ranges can choose distinct instrumental techniques**, not only loudness. Random velocity changes are unsafe for these sounds because a strum may turn into a mute/fret noise/slide. Yamaha warns S.Art/S.Art2/MegaVoice are model-dependent and not interoperable across random instruments.
- **Style Creator**: each song section (Intro, Main, Fill, Ending) can contain EIGHT separately defined source-pattern channels (Rhythm1, Rhythm2, Bass, Chord1, Chord2, Pad, Phrase1, Phrase2). This is compositional architecture, not just choosing an instrument name.
- **SFF Edit**: separate NTR (note-transposition rule based on changing chord root), NTT (transpose according to chord type), *High Key/Note Limit*, and RTR (retrigger rule for sounding notes at chord changes: stop, pitch shift, retrigger and root variants). Drums are treated differently from tonal instruments. See [Genos2 Reference Manual NTR/NTT](https://usa.yamaha.com/files/download/other_assets/5/2179945/Genos2_reference_manual_En_B0.pdf).
- Yamaha's [Data List](https://usa.yamaha.com/products/musical_instruments/keyboards/arranger_workstations/genos2/downloads.html) includes Voice/Articulation assignments; do not guess from instrument names. Yamaha examples: [Genos product-specific MegaVoice technique/velocity map](https://usa.yamaha.com/files/download/other_assets/3/1131013/genos_en_dl_f0.pdf) is a *different model* and must NOT be copied as universal Genos2/SFZ mappings.

## Korg Pa5X — primary reference findings

Korg's official [Pa5X specifications](https://www.korg.com/us/products/synthesizers/pa5x/specifications.php), [product explanation](https://www.korg.com/us/products/synthesizers/pa5x/index.php), and [Performance Guide](https://cdn.korg.com/us/support/download/files/236a30b24d559c6b63e0ab5e3e962556.pdf):
- **Style engine**: 8 independent style tracks; 3 Intros, 4 Variations, 4 Fills, Break and 3 Endings. Each section's accompaniment adapts to recognized chords through style elements/chord variations/chord tables. Patterns are chosen/translated based on musical context, not merely replayed unchanged.
- **NTT** (parallel/fixed note-transposition alternatives), chord-sequence and **Guitar Mode 2** are instrumental/compositional behaviors. Korg has developed guitar-specific fingering/strum logic, rather than playing stacked piano-like chords as guitar. Detailed key-to-strum note mappings are **device- and version-specific**.
- **DNC (Defined Nuance Control)** triggers per-sound nuance/articulation through controllers and switches. Official Performance Guide specifically identifies Sound Controller 1/2/3 as **MIDI CC#80, CC#81, CC#82** respectively, but the assigned meaning depends on the SOUND PATCH, not on genre label. Sample trigger state may also depend on legato/non-legato, register, velocity, aftertouch, joystick or released note.
- **Round-robin drums**, smooth transitions, physical sample articulations, multi-layer programs and effects support convincing timbral behavior. Korg states Pa5X PCM sample import capabilities, but its proprietary DNC programs are NOT automatically compatible with SFZ.
- Some Korg style workflows use markers such as `v4cv3` and timing of Program Change/Bank Select/CC11 at tick zero. **These are for Korg-specific style importing, not an SFZ command to make the Composer human.** See [Korg arranger tutorial](https://www.korg.com/us/features/arrangers/tutorials/) and Pa5X guide.

## Crosswalk — actual standardized control language available outside vendor engines

[MIDI Association Control Change specification](https://midi.org/midi-1-0-control-change-messages) and [MPE specification](https://midi.org/mpe-midi-polyphonic-expression), plus [SFZ trigger](https://sfzformat.com/opcodes/trigger/), [SFZ legato tutorial](https://sfzformat.com/tutorials/legato/), [round robin](https://sfzformat.com/opcodes/seq_length/), and [sfizz support table](https://sfztools.github.io/sfizz/development/status/opcodes/):

| Intent | Potential MIDI/patch mechanism | Implementation precondition |
|---|---|---|
| Attack and release | Note On, Note Off, note velocity, time in MIDI ticks | Sample/patch has right playable range/velocity |
| Increasing expression through a phrase | CC11 or instrument-specific mapped dynamic CC curve, timed after initial value | Controller actually mapped to amplitude/timbre |
| Vibrato on a held lead | Pitch-bend curve or mapped CC1/LFO depth/rate with onset delay | Receiver bend range and pitch/LFO mapping known; should not bend whole polyphonic chord |
| Slur / legato | overlap/gating, `trigger=first` versus `trigger=legato`, optional keyswitch | Patch includes suitable legato regions/transitions and sfizz supports them |
| Release / breath / finger noise | `trigger=release` or `release_key`, explicit mapped noise layers | Recorded layers exist; avoid fabricating/noise overlay |
| Repeated drums | SFZ `seq_length` + `seq_position`; velocity-aware sample choice | Real alternatives in sound bank; avoid machine-gun repetition |
| Guitar attack and strum | Physical string/fret voicings, per-string note delays, down/up stroke, mutes/slides/hammer-ons | Instrument playable range/articulations, no blanket 1-layer guitar program |
| Changing chord while accompaniment is sustaining | Rule-based role-specific NTR/NTT and RTR-equivalent behavior | A musically valid chord/section transition engine is required |
| Expressive bend on ONE voice in polyphonic music | Separate monophonic tracks or verified MPE/per-note expression receiver | MIDI 1.0 channel pitch bend affects all notes on that channel; sfizz MPE must not be assumed |

**Example of MIDI bytes for first MIDI channel (illustration only, NOT universal):**
- Note on C4 velocity 90: `90 3C 5A`; note off: `80 3C 00`.
- Mod wheel CC1 value 80: `B0 01 50`.
- Expression CC11 value 95: `B0 0B 5F`.
- Sustain CC64 on (127): `B0 40 7F`, off (0): `B0 40 00`.
- Korg DNC sound-controller 1 CC80 on (127): `B0 50 7F` — works only on Korg sound (or a separately mapped SFZ patch); *do not inject CC80 into all genres*.
- Pitch Bend centered: `E0 00 40`; other values depend on desired bend amount and patch bend range. **Do not assume MIDI hex bytes alone create a slide or vibrato**.

## Exact code-state gaps from current AI Composer repository (read-only inspection)

- `composer_overrides/genre_styles/index.json` maps **all 55** genres into **13** family folders, but `automatic_application_enabled=false`; the 7 planned stages per genre are inactive. **Genre filing exists; no proven route from that filed plan into complete output.**
- `composer_overrides/instrument_performance_contract.py` explicitly says V1 enables only **ROCK electric-guitar timing**, not generic performance realization.
- `composer_overrides/genre_development_patch.py` makes targeted Rock strum/note velocity changes, some Jazz harmony decisions; does not implement universal per-instrument patch state machines.
- `composer_overrides/midi_initial_cc_bridge.py` inserts a configured CC at **tick 0**, before first Note On, based on existing `midi_routing.initial_cc`; it does *not* output changing CC/bend/keyswitch curves throughout the phrase.
- The preserved `AI_Comp_Executable_Output_Core_001.py` (in project working artifacts) carries `MusicalEvent.articulation` and `.dynamic` but the underlying MIDI note writer serializes note-on/off with velocity. Current hook adds *initial* controls only. That is an end-to-end serialization **GAP** between planned musical behavior and audio-producing sampler.
- `composer_overrides/sfz_renderer_adapter.py` already calls `sfizz_render --sfz --midi --wav --samplerate`; basic rendering command is not the missing language.
- The 3D mixer operates **after** sample rendering; it cannot restore articulation transitions or physical note playing choices absent at source.

## Specific missing mechanism: performance realization / articulation interpretation

Proposed architectural contract, for design discussion **only**:

`family profile -> musical gesture plan -> target-specific articulation mapping -> correctly timed MIDI event stream -> existing sfizz-render -> WAV stems -> existing standalone 3D mixer`

A *musical gesture plan* needs to represent each instrument/track/note: event time, note pitch/velocity, intended relationship to previous and next notes, articulation (short, long, slide, muted, legato, release etc.), dynamic curves, physical voicing constraints, ensemble groove/section context.

A **per-instrument capability declaration** must specify whether the actual selected SFZ program supports legato switching, keyswitches, velocity-layer techniques, sustain pedal, pitch bend, expression CC and round-robin. A separate mapping from abstract intents to the *actual bank's MIDI and SFZ controls* is necessary. If a requested expression is unsupported, refuse/cross-reference that limitation rather than silently claim it happened.

For chord variation and accompaniment: a later **style/arranger interpretation layer** handles structure/sections/grooves; independent instrument performance handles nuance. These are distinct.

## Targeted minimal verification — do not repeat endless user-side tests

1. Read only ONE EXISTING SFZ lead-guitar source program and one sustained instrument (e.g. clarinet) to enumerate their actually supported articulations. Compare to sfizz 1.2.3 supported opcode table, not abstract SFZ features.
2. Identify `articulation`/`dynamic` fields already emitted per track in composer event dict.
3. Define a single expressive MIDI event serialization interface with exact ordering and per-instrument compatibility, without changing sample banks and without declaring a generic humanization rule.
4. Offline/isolated: same generated phrase, MIDI without performance instructions versus with mapped instructions, inspect bytes and listen to actual resulting WAV. Verify intended sustained and legato behaviors, instrument correctness and no regression to existing sample graph/genre file indexing. This is NOT full end-to-end song readiness.
5. Keep all 55 genre routing/hand-offs **inactive** until actual expressive response and complete WAV output are verified. Rock and Jazz remain **DYSFUNCTIONAL**, regardless of successful build or tone-sample checks.

## Source hierarchy and caveats

Yamaha and Korg manuals are evidence of the principles and manufacturer-specific behavior, **not reusable proprietary source code**. Neither Yamaha S.Art/S.Art2, AEM, MegaVoice, nor Korg DNC is a free universal engine or self-contained patch the user can plug into a Linux SFZ renderer. We can use publicly documented MIDI/SFZ command standards and independent algorithms; not extract or assume rights to manufacturers' waveforms, binaries or proprietary style code.

**Research saved without editing any live Composer code or using a Yamaha/Korg sound library.**
