# Interpreter-led instrumentation: execution integration contract

Status: **audit confirmed; no production integration**. This file documents the actual preserved adapter boundary.

## Verified behavior (2026-10-11 audit)

Preserved execution adapter: `AI_Comp_Genre_Execution_Adapter_002_WORKING_2026-10-02_184019_CDT.py`.

- `build_setup(...)` calls `generate_events(...)` without passing a musical instrument plan.
- `build_setup` publishes `palette=PALETTES[template]`.
- `generate_events(...)` independently reads `PALETTES[template]`.
- `generate_events` creates supplemental notes for each unused palette instrument.
- All 55 registered genres: 49 have 4 fixed instrument types; 5 have 5; 1 has 1.
- Classical is fixed to double_bass, violin, flute, clarinet.

## Required behavior

1. Genre interpreter resolves musical intention and returns an explicit `instrument_roles` array.
2. Shared `universal_arrangement_handoff` validates IDs against the **actual rendering library**; it must not pick a count.
3. Execution adapter receives the validated plan as an opt-in argument and generates distinct musical parts with those roles. It must not reread `PALETTES` for opt-in requests.
4. Renderer must confirm every requested part has an actual playable instrument binding and events; no silently dropped or generic-fallback instruments.
5. Preserve original adapter and its outputs for every non-opt-in request, especially all deployed requests.

## Blocking evidence still required

- Real interpreter's existing output shape and decision authority.
- Actual production renderer instrument IDs and polyphony/track limits.
- How the current genre definitions map to the 55 runtime names.
- Actual rendered multi-part listening test and regression test across all 55 genres.

## Safety gate

Do not merge/deploy until tests show identical legacy outputs for all genres when opt-in is off; correct interpreter-selected part count and roles when on; and no changes to the control panel. The current universal handoff is **not** wired into deployed composition.
