# AI Composer — Rock note-off timing and sample lifetime (2026-10-08 18:42 CDT)

**Status:** isolated research only; live Composer, plug, control panel, source audio, genre routing and standalone 3D mixer untouched.

## Direct source finding

In the existing `composer_overrides/genre_development_patch.py` around lines 303–315, Rock BASS notes go through:

```python
original = float(e.get("duration_beats", 0.1))
e["duration_beats"] = min(original, 0.90 if phrase_in_section in (0, 2) else 0.48)
e["duration_beats"] = max(0.22, e["duration_beats"])
```

The normal Rock build currently targets 145 BPM. These bounds correspond to 0.091034 seconds minimum, 0.198621 seconds for a 0.48-beat cap, and 0.372414 seconds for a 0.90-beat cap. This is note-off timing only, **not recorded-sample or audible lifetime**. The later `instrument_performance_contract.perform(..., "ROCK")` acts only on guitars, not the bass.

This makes excessive bass note truncation a **plausible source-level cause** of choppy playback, not yet a proven sole cause. The selected clean Growlybass program has sustain samples but no release-trigger regions in the examined source. In SFZ, sample length/embedded loops and envelope release independently determine actual acoustic lifetime.

## Completed separate offline investigation

The independently preserved archive `ai-composer-performance-language_2026-10-08_1842_CDT.zip` contains:

- Existing research vocabulary, exact-resource-gated read-only interpreter, tests and SFZ opcode inventory
- `noteoff_sustain_diagnostic_v1.py`: inspect actual Composer event JSON or any MIDI file for note on/off time, gaps, durations, tempo changes and CC messages
- `sfz_sample_lifetime_probe_v1.py`: inspect installed SFZ includes, sample-file existence, sample durations, WAV embedded loop metadata and release triggers
- Two new test files and `NOTE_OFF_AND_SUSTAIN_FINDINGS_2026-10-08.md`

**22 offline unit tests passed** with synthetic MIDI/WAV and research fixtures. ZIP integrity check passed. None of these tests constitute a live song render or listening proof.

## Next experiment

Using a *real generated Rock song* once a non-destructive output capture becomes available, measure its BASS event durations, actual MIDI note-off timing and isolated Growlybass audio. Then compare unchanged original vs one narrowly scoped candidate that preserves authored bass sustain where supported, while retaining explicit short/muted notes and real phrase gaps. No genre stage activation, control panel revision or deployment without audio verification.

## Original code anchor

https://github.com/mreeves1257-glitch/AI-Composition-Deployment/blob/main/composer_overrides/genre_development_patch.py#L303-L319
