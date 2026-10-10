# Optional Sub-Bass Sidecar — NOT CONNECTED

**Purpose:** Create genuine low-frequency oscillator audio (20–80 Hz fundamental)
separately from the 55 genre folders, original recorded instrument bank, SFZ
mappings, Composer MIDI, live 3D mixer, and control panel.

## Architecture

```text
COMPOSER → MIDI → SPECIFIC GENRE INTERPRETER
                            ├── original INSTRUMENT RENDERER → recorded WAV stems
                            └── independent SUB-BASS SIDECAR → synthesized WAV stem
                                      (not yet wired; optional)
                    future verified stem integration → existing 3D mixer → finished music
```

The sidecar is **not** a recorded SFZ instrument and must never be labeled as
one. The current 3D mixer input contract assumes recorded SFZ source metadata
for every track; its acceptance of a synthetic auxiliary stem has **not** been
validated. Do not insert a synthetic stem into the live mixer manifest by
mislabeling it as an instrument. Introduce it only after a controlled
integration plan verifies source identification, gain, alignment and mix behavior.

## Standalone preview

Requires Python 3.10+ and numpy (already installed by the Composer build).

```bash
python sub_bass_sidecar/generate.py \
  --request sub_bass_sidecar/example_request.json \
  --wav /tmp/ai-composer-sub-bass-preview.wav \
  --manifest /tmp/ai-composer-sub-bass-preview.json
```

The request explicitly opts in with `"enabled": true`. It produces a
**new separate mono 16-bit WAV**, with low-frequency oscillations, per-hit
attack/release, velocity, and an optional decaying pitch sweep. It renders in
small blocks to constrain memory use, refuses overwriting audio, and stops if
combined tone peaks are too high. The output is a candidate **audio stem**, not
a new instrument in the category or library.

## Input contract

- `duration_seconds`: 0.1–600, whole output file duration.
- `sample_rate`: 44100 or 48000 Hz, must match original WAV stems when mixed.
- `level_dbfs`: -48 to -12 dBFS, default -21 dBFS (may be too loud when overlapping; generator rejects peak >= 0.98).
- `attack_ms`: 2–50, default 6; `release_ms`: 30–600, default 120.
- `events`: explicit musical event timings (up to 10,000).
- `start_seconds`: timestamp in output; `duration_seconds`: 0.04–10 seconds per event.
- `frequency_hz`: fundamental frequency, 20–80 Hz. `sweep_hz`: extra initial frequency, 0–70 Hz, with initial total no greater than 120 Hz.
- `velocity`: 0–1, default 1.

Event timing can later be derived from existing kick or bass note events by a
**read-only** adapter; do not alter genre interpreter or MIDI to supply it.
Frequency range alone is not a guarantee of audible sub-bass on phone speakers.
Use appropriate headphones or subwoofer for physical evaluation.

## Verification gates — NOT DONE

1. Run standalone sine-tone render and inspect WAV metadata/peak plus audible output.
2. Read musical event timestamps **without modifying** genre events.
3. Decide how to admit a clearly marked **synthetic auxiliary stem** through a
   safe, verified mixer input contract. The existing mixer should stay standalone.
4. Verify no unwanted phase cancellation, gain buildup, clipping or latency.
5. Test with low-frequency-capable playback, compare OFF/ON by ear and measurement.
6. Only then consider enabling it for individual genres.

**Status:** source file saved on isolated branch; live installation, true audio
render validation and mixer handoff have not been completed. Existing working
Rock/Jazz audio, 3D mixer, control panel and 55 genre folders unchanged.
