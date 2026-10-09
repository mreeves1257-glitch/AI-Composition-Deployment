# ROCK — Musical-Language Interpretation Gap: Verified Source Audit

**Checkpoint:** October 8, 2026, 8:14 PM CDT (America/Chicago)
**Type:** Research/architecture finding only. No runtime modifications in this checkpoint.
**Branch:** `rock-groove-motion-research-20261008`.

## User's central hypothesis

"It's some kind of language problem. It's not interpreting correctly."

This is substantially supported by source inspection. Important distinction: it is not proof of a security *permission* being denied, a MIDI protocol bug or a faulty recorded drum bank. The source reveals **a missing high-level arrangement-to-performance translation** between human-readable Rock intentions and authored playable part events.

## Actual source evidence

1. `composer_overrides/genre_styles/Rock/profile.json` describes:
   - `groove_behavior`: “straight or lightly syncopated eighth-note rock pulse; backbeat remains structural but fills and pushes vary by section”
   - `percussion_behavior_if_applicable`: “kick/snare backbeat, hi-hat/ride timekeeping, tom/crash transitions; pattern variation required across sections”
   - `ensemble_player_behavior`: “rhythm section shares groove hierarchy; lead phrases leave space and answer vocal/melodic gaps”
   These are **descriptive natural-language strings**, not a tested sequence of machine-readable performance operations. Its `runtime_musical_connections.runtime_integration` explicitly says `FAMILY_DATA_REFERENCE_ONLY_RUNTIME_STILL_READS_ORIGINAL_PROFILE`; all six proposed seven-stage handoffs are `RESERVED_NOT_CONNECTED` and `enable_runtime_connections` is false.
2. `composer_overrides/genre_development_patch.py`: `compile_genre_template` describes itself as an **eight-section non-rendering VIEW** of authoritative profiles; the resulting dict preserves the strings but does not compile their performance semantics into score actions.
3. The same patch's `develop_full_length` hardcodes a KICK recipe 0.0/2.0 beats (plus small fixed offbeats), a SNARE backbeat on 1.0/3.0 **every bar**, and just three tom notes each at select 16-bar transitions. These recipes do not consume a structured `ROLL`, `FILL`, `GHOST`, `SECTION_PUSH` or `BAND_TURNAROUND` intent object. This produces audible beatkeeping without a complete drummer's authored performance.
4. `composer_overrides/instrument_performance_contract.py`, `perform`, declares its V1 scope **Rock electric-guitar note lengths only** and explicitly does *not* change drums/bass/other parts. It processes already generated note events with duration decisions, not full-band composition plans.
5. Lower-level modules `musical_gesture_author.py`, `expressive_gesture_bridge.py`, `instrument_gesture_handoff.py` DO exist for **explicit, sample-capability-validated note-level gestures** (e.g. electric-guitar vibrato) and should be preserved/reused. They are NOT a general musical arranger that interprets descriptive genre prose into drum parts and ensemble events.
6. The full recorded Rock music already passed through its existing MIDI/SFZ and 3D chain. The user likes the authenticity and separation of the recorded instruments. The failure is in *what the instruments are told to perform*, not evidence that their SFZ banks can't make the available sounds.

## Exact missing layer to design

An explicit, versioned **Musical Arrangement Intent -> Executable Performance Plan** boundary. It should sit BEFORE the per-instrument note generation and BEFORE the lower-level source-aware gesture translator.

Proposed flow:
`Genre style definition (prose)` -> `Validated Section/Groove Intent` -> `Shared Band Conductor plan` -> `Role-specific drum/bass/guitar phrase events` -> `Existing resource capability mapping and MIDI/SFZ execution` -> `Existing final separate 3D mixer`.

Unlike descriptive prose, the executable instruction model needs typed fields, for example:
```json
{
  "section_role": "CHORUS_ENTRY",
  "phrase_bar": 7,
  "meter": [4, 4],
  "tempo_bpm": 145,
  "groove_grid": "SIXTEENTH",
  "instructions": [
    {"track": "SNARE", "gesture": "ROLL", "start_beat": 2.0, "end_beat": 3.75,
     "subdivision": "SIXTEENTH", "accent": "CRESCENDO", "exit_target": "CHORUS_DOWNBEAT"},
    {"track": "TOMS", "gesture": "DESCENDING_FILL", "start_beat": 3.0, "end_beat": 3.75,
     "subdivision": "SIXTEENTH", "exit_target": "CHORUS_DOWNBEAT"},
    {"track": "KICK", "gesture": "ARRIVAL_ACCENT", "start_beat": 4.0,
     "sync_with": ["BASS", "HARMONY"]},
    {"track": "CRASH", "gesture": "SECTION_ARRIVAL", "start_beat": 4.0}
  ]
}
```
**Illustration only, not a valid deployed schema or executable code yet.** The example coordinates are relative to a phrase boundary, not automatically musical truth. A converter must interpret subdivisions and accents into actual timed sample note-ons, respect instrument mappings and polyphony, and check that the given 16th-note strikes and fills make sense together. Where a particular source recording lacks an articulation, fail safe instead of inventing controls.

## Recommended next verification

- **Trace one incoming Rock-profile instruction**, e.g. “snare fill into chorus”, and test whether it results in an explicit `SNARE` performance plan. Presently no complete high-level implementation was found in inspected paths.
- Define a small shared typed vocabulary: `PULSE`, `BACKBEAT`, `GHOST`, `ROLL`, `FLAM`, `TOM_FILL`, `PICKUP`, `CRASH_ARRIVAL`, `REST`, with `subdivision`, `density`, `accent`, `section`, `exit_target`, and `sync_with`.
- Write fail-closed tests for parsing, role permissions, intended phrase lengths, real source mappings, and cross-track synchronization. **Do not infer drum realism merely from larger event counts**.
- Test a single 8/16-bar musical transition with actual recorded Rock instrument banks and original mixer. Then user listens. Only then consider connecting such language to the wider Rock form. Do not activate all seven planned genre stages or alter any live service automatically.

## Protected baseline

Preserve user's liked all-instrument clarity, cleaned-up original Rock drums, actual recorded Karoryfer banks, current gain ratios, independent 3D mixer, Plug/Composer/Control Panel deployment, earlier complete audio hard saves and remaining 55-genre filing structure. The story V2 and groove V1 candidates remain separate research, unapproved artistically.

**Evidence status:** High confidence that human-readable musical intentions are not currently compiled into full-band playing instructions in the inspected Rock runtime. The narrower guitar source-gesture converter is real and partly implemented; do not mischaracterize the entire audio chain as incapable of interpreting MIDI.
