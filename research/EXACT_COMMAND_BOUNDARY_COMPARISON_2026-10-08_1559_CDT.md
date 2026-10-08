# Exact Command & Boundary Comparison — AI Composer
**October 8, 2026 — 15:59 CDT**  
**Scope:** read-only comparison of existing actual interfaces with published standards.  
**Status:** Findings from source inspection, NOT deployed diagnosis, NOT a repair or sound test.  
**Preserved working source baseline:** `c7f63bd901cdaff294e65ca5c0233a2685765d9e`.

## Inspected source snapshots

1. User Library: `Control-Panel-Phone-R1-2026-10-07.html` (latest phone R1 HTML examined). **Do not assume this is necessarily the exact version installed on the phone today.**
2. GitHub `mreeves1257-glitch/Plug-Sandbox/input_gateway.py` on main.
3. GitHub `mreeves1257-glitch/AI-Composition-Deployment/composer/runtime.b64` current source archive, decompressed read-only. Examined actual `input_gateway.py`, `engine.py`, `output_handoff.py`, `instrument_program.py`, and `target_program.py` inside.
4. GitHub `composer_overrides/render_server.py`, `sfz_renderer_adapter.py`, `spatial_master_handoff.py`, `standalone_3d_mixer.py`, and `build_current_composer.sh` on main.
5. Existing preserved output-core implementation `AI_Comp_Executable_Output_Core_001.py` as a Library source and Oct 3 protected archive; the current build restores that Output Core without a code patch in `build_current_composer.sh`.

## Evidence-backed comparison

| Interface | Current observed implementation | Standard / expected behavior | Classification |
|---|---|---|---|
| Panel POST -> plug | Panel posts JSON to `/plug` with `interface_version=COMPOSER_INTERFACE_V1`, `request_id`, `genre`, `command=compose`, `target=INTERNAL`, `mode=normal`, `tuning_reference_hz`, and `portal3_route`. | Plug forwards this body verbatim to Composer `POST /compose`. | Route exists. |
| Plug -> Composer | Plug validates interface version and JSON, passes whole body to `/compose`. | Composer `compose_request` only consumes `genre`, `target` and `mode`. | Accepted but unused fields. |
| Tuning selection | Panel supplies `tuning_reference_hz` (e.g., 440/432). Composer `compose_request` drops it, `AICompositionEngine.run` only takes genre, target, mode. | A requested tuning should be explicitly supported/validated and transmitted to compatible renderer/patch, or rejected honestly. | **CONFIRMED missing translation.** Do not assert 432 works. |
| Request identity | Panel sends `request_id`, plug forwards it; Composer gateway neither validates nor preserves this as a job identity. | Use an idempotency/request record if the user is to recover from timeouts without duplicated compositions. | **CONFIRMED missing end-to-end request accounting**; not necessarily root cause of missing audio. |
| Original music -> note MIDI | Output Core's `_midi_pitch_events` writes Note On `0x90`, Note Off `0x80`, tick duration and initial attack velocity. `MidiAdapter` writes conductor tempo `FF 51` and meter `FF 58`. | MIDI Association defines these precisely. | **Implemented** for base note/velocity timing. |
| Expression/articulation -> playable MIDI | `MusicalEvent` holds `articulation` and `dynamic`; `output_handoff.build_execution_package` passes them to events. `MidiAdapter` writes note-on/off only; it does NOT map articulation, continuous expression CC1/CC11, CC64, CC76-78, pitch bends, or dynamic controller changes. `midi_routing` metadata (including `initial_cc`) is attached to the composition package by `output_handoff.py`, but the preserved `MidiAdapter.render` doesn't read it. | Actual MIDI CC/pitch instructions (or instrument-specific SFZ patch controls) must be serialized correctly where required. Not every SFZ patch supports the same control. | **CONFIRMED missing translation layer** in the inspected Output Core; instrument presets may still have their own static embedded SFZ expression. |
| SFZ program/path -> renderer | `sfz_renderer_adapter.render_midi` invokes `sfizz_render --sfz <bank-program.sfz> --midi <track.mid> --wav <stem.wav> --samplerate 44100`. | Official sfizz-render usage supports these options. | **Implemented**. Must verify instrument-level playable articulation separately. |
| Sample resources | Preflight validates source bank ID, SFZ and referenced sample graph. | Resource existence != successful full ensemble audio. | **Implemented** preflight; final audio still must be proved. |
| Genre performance -> stems | `output_handoff.execute_audio_render` splits track events, renders independent MIDI/WAV. Full `build_current_composer.sh` patches output handoff to pass stems to the separate `standalone_3d_mixer.py` subprocess. | Sound samples shared; tracks/stems remain independent. | **Implemented in source**; full live test pending. |
| Mixer output -> response | Current archived `engine.py` **does** update top-level `audio_rendered` from `execute_audio_render`; Composer `compose_request` recursively attaches public `audio_url` to a `wav_path` under its `OUT` root. | Must return status only after genuine WAV+3D completion. | Source mechanism present. **Earlier suspicion of permanently-false engine success flag does NOT apply to the current archived engine**. |
| Composer health -> plug health | Archived parent input gateway supports `GET /health` returning `BRIDGE_READY`, but live entry class `ComposerWithJazzPreview.do_GET` overrides the parent and sends unknown GETs (including `/health`) to 404. Plug transforms ANY upstream HTTP <500, including 404, into `status=COMPOSER_READY`. | Health check should require a semantically correct upstream status (200 + expected body), rather than any <500. | **CONFIRMED source-level false-positive readiness path**, subject to deployment-version check. |
| Time bounds | Phone panel abort: **405s**; plug's `COMPOSER_TIMEOUT_SECONDS` default **120s**; 3D mixer subprocess **240s**; per-resource sfizz render subprocess **120s**. | All processing and upstream timeouts must align or use explicit async-job semantics. | **POTENTIAL operational limit**, real plug environment setting and actual render time unverified. |
| Public audio URL | Composer serves `/audio/final_audio/composition_<id>/stereo_derivative.wav` with GET/HEAD and Range; plug forwards GET/HEAD and Range; phone can resolve nested `audio_url`/WAV paths. | MDN range requests: 200/206 and content-range. | **Mostly implemented**, accessible live endpoint and complete response unverified. |
| Large audio transfer | Plug `_proxy` calls `response.read()` and then writes full bytes to client. | Streaming/chunked relay avoids holding full long WAV in plug memory. | **SOURCE-VISIBLE memory concern**, not verified as current failure. |
| Yamaha/Korg hardware | Manufacturer reference data exists but active target is `INTERNAL` and selects SFZ by explicit resource path. | Hardware typically uses exact bank/program mapping: Bank Select CC0+CC32 then Program Change, plus native voice/expressive controls; consult *exact model* data lists/implementation before using. | **FUTURE SEPARATE HARDWARE-TARGET investigation**, not missing internal SFZ CLI command. |

## Published primary references

- MIDI Association, Summary of MIDI 1.0 Messages: https://midi.org/summary-of-midi-1-0-messages
- MIDI Association, MIDI 1.0 Control Changes: https://midi.org/midi-1-0-control-change-messages
- sfizz-render official usage (archived separate repository; CLI now bundled with sfizz): https://github.com/sfztools/sfizz-render
- sfizz current opcode support table: https://sfztools.github.io/sfizz/development/status/opcodes/
- SFZ legato/release triggers: https://sfzformat.com/opcodes/trigger/
- MDN Range requests: https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Range_requests
- MDN 202 Accepted (not completion): https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/202
- Render background workers: https://render.com/docs/background-workers
- Yamaha Genos2 official manuals/data list: https://usa.yamaha.com/products/musical_instruments/keyboards/arranger_workstations/genos2/downloads.html
- Korg Pa5X official manuals: https://www.korg.com/us/support/download/product/0/895/

## Minimal evidence sequence BEFORE proposing code changes

1. **Lock exact deployed code revision and actual installed control-panel file version**. Do not treat a Library backup as necessarily the live phone file.
2. **Health contract offline**: inspect actual Composer `/health` and plug response; assert no 404 is advertised as COMPOSER_READY.
3. **Request-field trace offline**: take a realistic panel payload and classify every field as consumed, ignored, or unsupported by the Composer. Be explicit about tuning and request ID.
4. **MIDI serialization read-only**: verify whether any existing production patch to Output Core serializes CC/Pitch Bend/articulation beyond note events. If not, document exact minimal needed translation based on each instrument's actual SFZ mappings; avoid universal CC assumptions.
5. **Renderer protocol**: verify sfizz version/options, per-instrument SFZ supported opcodes, initial CC and MIDI duration; no repeated phone-side trials.
6. **Mixer and audio-return contract**: inspect final audio job/response fields and route under `/audio/final_audio/.../stereo_derivative.wav`; verify file-serving and byte-range externally only after user approves testing.
7. **Timeout/storage**: measure live request durations, deployment configuration and audio lifetime before considering job queues/worker redesign.
8. Document recommended narrowly scoped correction for each **confirmed** mismatch. Obtain explicit authorization before editing, redeploying or activating any dormant genre stages.

## Summary
**Likely missing routine isn't basic SFZ rendering syntax.** It's MIDI expression-to-player control serialization, forwarding of certain panel request fields, reliable readiness semantics, and operational timing of the complete delivery. The current exact source *does* contain per-track audio renders, 3D mixer handoff and public audio URL conversion. No broad reconstruction is justified.

**No production writes, source modifications or live music renders performed for this audit.**
