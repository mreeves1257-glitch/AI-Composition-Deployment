# AI Composer — External command and handoff research (read-only)
**Research checkpoint:** October 8, 2026, 15:54 CDT  
**Status:** EXTERNALLY SOURCED TECHNICAL REFERENCES — NOT INSTALLED, NOT TESTED, NOT CONNECTED  
**Source baseline:** `c7f63bd901cdaff294e65ca5c0233a2685765d9e`  
**Do not change:** working Composer, control panel, shared plug, Rock, Jazz Ballad, original instrument libraries, or external 3D mixer. Maintain all 385 filed stage connections inactive.

## User's key distinction
The music and recorded instruments are already collected in many places. The priority is **external authoritative operational/communications commands**, not another search for instrument sounds or a redesign. Determine how complete instrument implementations accept instructions, turn MIDI into WAV, hand off stems, and return the finished audio to the phone.

## A. Actual instrument performance instructions (standard, not invented)
Source: MIDI Association [Summary of MIDI 1.0 Messages](https://midi.org/summary-of-midi-1-0-messages) and [Control Change Messages](https://midi.org/midi-1-0-control-change-messages), [Standard MIDI Files](https://midi.org/standard-midi-files).

- MIDI Note On: status `0x90`–`0x9F` + pitch + velocity. Note Off: `0x80`–`0x8F` + pitch + release velocity (or equivalently Note On with zero velocity where the receiving implementation supports it).
- Program Change: `0xC0`–`0xCF`; this selects a program **within a compatible receiving instrument**, NOT the filesystem SFZ sample bank. Our external renderer receives an explicit `.sfz` file path for each bank/patch.
- Pitch Bend: `0xE0`–`0xEF`, 14-bit value, amount depends on receiver bend sensitivity. Use only when the instrument's mapped articulation supports the intended performance.
- CC1 Modulation Wheel; CC7 Volume; CC10 Pan; CC11 Expression; CC64 Sustain Pedal; CC65 Portamento; CC68 Legato; CC73 Attack; CC76 Vibrato Rate; CC77 Vibrato Depth; CC78 Vibrato Delay. **MIDI names alone do not prove a particular SFZ library responds to each controller**. Inspect per-instrument SFZ bindings and sfizz compatibility before claiming vibrato, legato, release and dynamics.
- The Standard MIDI File carries timed events and tempo meta-events; `FF 51 03` carries microseconds per quarter note. Converting the audio clock correctly and expressing tempo in all track MIDI files is essential. An externally documented example is [Standard MIDI file format, Set Tempo](https://github.com/Koseng/SimpleMidiLib/blob/master/Standard%20MIDI%20file%20format.html).

## B. Instrument renderer command — exact documented syntax
Source: [sfizz-render official upstream repository / usage](https://github.com/sfztools/sfizz-render#usage), now incorporated into sfizz.

```sh
sfizz-render --sfz /path/to/original-instrument.sfz \
             --midi /path/to/one-instrument-track.mid \
             --wav /path/to/independent-track.wav \
             --samplerate 44100
```

Documented options: `--sfz`, `--midi`, `--wav`, `--samplerate` (or `-s`), optional `--track`, `--blocksize`, `--oversampling`, `--use-eot`, and `--help`. No separate undocumented magical 'connect instrument' command was identified. The essential *contract* is one identifiable instrument role -> correct SFZ program/source -> correctly timed MIDI -> audible WAV. Check per-track output identity, length, levels, sample rate and error code.
- [sfizz opcode support table](https://sfztools.github.io/sfizz/development/status/opcodes/) identifies supported, unsupported and incomplete SFZ features. Beware `loprog`/`hiprog` marked unsupported by design and `lobpm`/`hibpm` marked work in progress in that published table. Support varies by version; **do not assume entire advanced library behavior works**.
- [SFZ trigger spec](https://sfzformat.com/opcodes/trigger/) covers attack, first, legato and release regions. A library must actually define the behavior; MIDI events alone cannot conjure a release sample or legato transition.
- [SFZ amp velocity tracking](https://sfzformat.com/opcodes/amp_veltrack/) explains how velocity-to-loudness behavior is controlled by instrument programming.

## C. Long-running job communication — standard HTTP pattern
Sources: [MDN 202 Accepted](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/202), [MDN 303 See Other](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/303), [Render background workers](https://render.com/docs/background-workers), [Render task run examples](https://render.com/docs/workflows-running).

Recommended conditional design **if existing synchronous output proves unreliable**, not an automatically available endpoint:
1. `POST /compose` JSON with `request_id`, `genre`, `mode`, `tuning_reference_hz`, `interface_version` -> `202 Accepted` and application-defined `job_id` plus `status_url`.
2. `GET /jobs/{job_id}` -> `queued`, `composing`, `rendering_stems`, `mixing_3d`, `completed` with `audio_url`, or `failed` with reason. The status route and JSON schema must be implemented by our application; HTTP does NOT define these paths or fields automatically.
3. A completed job returns a server-fetchable final-audio URL. Never report `AUDIO_RENDER_PASS` merely from successful note events or sample graph checks. Ensure idempotent `request_id` to prevent duplicate songs after a delayed response or retry.
4. Optional `303 See Other` to the finished audio URL for retrieval; only if the client expects/handles such redirect.
5. An alternative is retaining the existing synchronous `POST /compose` and robustly aligning timeout, status and complete audio response. **Do not introduce background workers, queues, or new routes unless a measured need establishes it.**

## D. Audio download/playback — standard HTTP methods
Source: [MDN HTTP Range requests](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Range_requests), [MDN Fetch API](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch).
- `GET /audio/<documented-filename>` -> `200 OK`, `Content-Type: audio/wav`, accurate `Content-Length`, complete nonempty audio.
- `HEAD` response without body helps media player discover length and byte-range availability.
- `GET /audio/... ` with `Range: bytes=0-` -> `206 Partial Content` with `Accept-Ranges: bytes`, accurate `Content-Range` and `Content-Length`. `416` on invalid range. Forward `Range` intact through the shared plug.
- Relay audio incrementally (stream/chunks), not by eagerly buffering an entire long WAV in the plug.
- Use a stable and accessible URL, not a server-local `wav_path` filesystem string. Browser `fetch()` needs a valid HTTP response/status, and `<audio>` still requires decodable finished media. Range and playback alone do not indicate song content success.
- [Render persistent storage guidance](https://render.com/docs/disks): default service files are ephemeral across redeploy/restart, so durable output delivery needs a deliberate storage/lifetime decision.

## E. Actual existing project boundaries needing reconciliation — observed in source
- Control panel `Control-Panel-Phone-R1-2026-10-07.html` in user Library posts `POST /plug`, checks `GET /health`, accepts JSON audio URL/WAV path or direct audio, and has a 405-second abort timer.
- Shared plug `mreeves1257-glitch/Plug-Sandbox/input_gateway.py` relays `/plug` POST to Composer `/compose`, relays `/audio/` `GET/HEAD` with optional `Range`, and declares default `COMPOSER_TIMEOUT_SECONDS=120`. This shorter plug timeout can terminate a song before the panel's 405 seconds. **Configurable, not proof of a live timeout.**
- Plug's health checks consider Composer HTTP response `<500` successful; Composer `render_server.py` does not explicitly forward `/health` through its GET override and returns `404` on unrecognized paths. **Source-visible probable false-ready condition**, to verify on deployed version; do not modify without approval.
- Composer's `composer_overrides/sfz_renderer_adapter.py` already invokes the external `sfizz_render --sfz --midi --wav --samplerate`. **Not a missing CLI syntax.** Validate real program selection, available MIDI expression and instrument-role consistency.
- Build logic runs isolated full performance and `standalone_3d_mixer.py` subprocess with a local JSON job input and explicit 240-second subprocess timeout. Its `spatial_master_handoff.py` writes `stereo_derivative.wav` and reports a local `wav_path`. Verify JSON nesting, exact public URL conversion, authorized serving route, and whether output survives long enough to retrieve.
- Composer `render_server.py` supports public final audio path `/audio/final_audio/composition_<id>/stereo_derivative.wav`, with GET/HEAD and byte-range handling. Plug relays audio requests but currently uses `response.read()` to buffer the full WAV in memory instead of forwarding bounded chunks.
- 55-style genre stage sequence is **architecture only**, all 385 inactive; prior verified isolated source tests are not the complete panel-to-audio pipeline.

## Targeted readiness evidence to collect, WITHOUT rewriting or repeated user-side tests
- **Health**: exact Composer `/health` status/body and plug translation, not merely any `<500`.
- **Command agreement**: panel POST schema == plug accepted schema == Composer actual parser; capture request and response keys.
- **Instrument**: each selected track has a sample backed SFZ program, MIDI expression mapped (when library supports), and measurable non-silent WAV render.
- **Mixer**: every expected stem is listed exactly once, sample rates match, final stereo derivative generated, valid output manifest and 3D gate.
- **Return**: completed response identifies public `audio_url` (or provably valid conversion), plug GET returns `200` or `206` with WAV bytes and no truncation, browser can play it.
- **Timing**: measure production worst-case timings before changing timeouts/adding queues. Respect panel/plug/Composer bounds.
- **Storage**: finished output accessible after request completion, without assuming ephemeral temporary files survive redeploy.
- **Failure handling**: no incorrect 'connected', 'composition complete' or 'music ready' claims on `404`, `202`, missing stems, missing audio or unresolved reference IDs.

## Conclusion
Standard MIDI performance commands, SFZ rendering CLI, and HTTP status/audio delivery mechanisms are documented externally. The more likely missing part is **the application-defined agreement between them**, especially health semantics, long-running job completion, instrument-to-MIDI articulation mapping and final public-audio URL. These are **specific audit hypotheses**, not confirmed live failure causes. Do not add new infrastructure or connect the dormant 385 stages based only on this research.

**Research only. No production file was edited, and no runtime pipeline test was performed.**
