# AI Composer - Independent Sub-Bass Sidecar - HARD COPY
**Checkpoint date:** October 9, 2026
**Status:** Prepared source only; OFFLINE, DISCONNECTED, UNTESTED IN AUDIO. This checkpoint does NOT indicate a live installation or successful mixer handoff.
**Repository:** `mreeves1257-glitch/AI-Composition-Deployment`
**Development branch:** `sub-bass-sidecar-2026-10-09`
**Hard copy archival branch:** `hard-copy-sub-bass-sidecar-2026-10-09` (to be created from the fully saved checkpoint commit)
**Canonical submodule:** `sub_bass_sidecar/`

## User's decision
The sub-bass generator must be an **independent module off to the side**, not part of the instrument category or instrument sample banks. It must create new low-frequency sound (rather than merely boosting/filtering existing drum samples), yet be straightforward to introduce later without rebuilding the Composer, MIDI routing, genre interpreter, original instruments, renderer, standalone 3D mixer, plug, or phone control panel.

## Fixed authoritative music path (unchanged)
```text
COMPOSER
   -> MIDI
   -> SPECIFIC GENRE INTERPRETER
   -> INSTRUMENT RENDERER
   -> 3D MIXER
   -> FINISHED MUSIC
```
The **planned optional** sub-bass sidecar would receive a *read-only event/timing handoff* from the chosen genre/performance and produce a separate waveform stem **parallel** to instrument rendering, with controlled admission to the final mix only after compatibility is validated. It does not introduce a replacement instrument or an additional interpreter into this path.

## Saved working-source files
- `sub_bass_sidecar/generate.py` - standalone numpy-based synthesizer, renders a new WAV.
- `sub_bass_sidecar/example_request.json` - example independent opt-in hit/timing configuration.
- `sub_bass_sidecar/test_generate.py` - local automated checks for WAV structure, isolation and no overwrite (tests *written*, not yet claimed run).
- `sub_bass_sidecar/README.md` - use, configuration, safety and integration gates.
- `checkpoints/AI_COMPOSER_SUB_BASS_SIDECAR_HARD_COPY_2026-10-09.md` - this recovery and decision checkpoint.

## Capability and boundaries
- Synthesized low-frequency fundamentals: **20-80 Hz** with optional short downward pitch sweep; distinct from the existing filtered recorded Rock SUBKICK.
- Emits its own mono PCM16 WAV at 44,100 or 48,000 samples/second, using bounded-memory blocks.
- Controls include hit start time, duration, frequency, sweep, velocity, attack/release and overall gain.
- Requires `enabled: true` and explicit event times to render; not wired to genre note events.
- Produces clearly named `SYNTHETIC_OSCILLATOR` source; **never call it a recorded SFZ instrument**.
- Refuses an already-existing output file and rejects high combined peak levels.
- No source instruments or production wiring were modified to create this branch.
- Note: playback devices such as phone speakers may be unable to reproduce very low frequencies.

## Existing project discovery
- Rock already has `composer_overrides/genre_styles/Rock/recorded_subkick.py`, a **filtered, recorded-sample** sub-kick layer (95 Hz lowpass), not a low-frequency oscillator.
- The existing standalone 3D mixer and `spatial_master_handoff.py` assume recorded instrument metadata for their incoming stems. A synthesized sidecar stem **must not** be sneaked in using false sample provenance.
- Never alter or overwrite that recorded-kick module as part of this sidecar.

## NOT DONE - strict verification gate before activation
1. Run `python sub_bass_sidecar/test_generate.py` and a standalone actual audio render; validate waveform, timestamps, level, playback.
2. Implement a read-only musical timing/event adapter outside the existing genres.
3. Verify truthful auxiliary/synthetic-stem provenance can pass the existing independent 3D mixer handoff; avoid modifying the core architecture.
4. Check alignment/phase, headroom and dynamics, compare against real Rock/Jazz stems and 3D output.
5. Ask for user listening approval; only enable per genre after successful end-to-end proof.

## Recovery
Retrieve the development or hard copy archival GitHub branch under the repository above. Restore the entire `sub_bass_sidecar/` directory and this checkpoint, but do **not** connect it to production merely because these files exist. Source preparation is complete; integration is NOT complete.

**Hard-copy rule:** no silent scope extension, no automatic instrument substitution, no change of authoritative music path, no representation that the work is live, tested, or activated.
