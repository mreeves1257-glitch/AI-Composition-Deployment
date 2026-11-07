# Genre Contract V3 → Composer Execution Wiring Diagnosis
Date: 2026-11-07
Branch: genre-contract-v3-no-reasoning-diagnostic

## Purpose

Diagnose why richer Genre Contract V3 research is not reliably changing generated music or instrument behavior. The experimental Composer Musical Reasoning Engine v0.1 is deliberately excluded from this diagnostic branch but preserved on its dedicated branches/history.

## Confirmed findings

1. **The active Composer engine was still selecting from the legacy October genre registry.**
   - `current_master_forward/engine.py` constructs `GenreSelector` from:
     `genre_registry_WORKING_GENRE_COMPLETE_2026-10-02_182810_CDT.json`
   - The execution adapter separately loaded:
     `AI_Comp_Genre_Performance_Registry_002_WORKING_COMPLETE_2026-10-02_182810_CDT.json`
   - Therefore improvements in `genre_contract_v3_research/GENRE_CONTRACT_V3_ALL_55.json` were not the execution authority.

2. **Instrument choice is upstream of the instrument resolver and was largely hard-coded.**
   - `resolve_genre_parts()` in the execution adapter selects from the static `PALETTES` table.
   - The function explicitly treats profile prose as recognition/context rather than executable instrumentation.
   - `instrument_program.py` does not choose instruments from genre intelligence; it only resolves instrument IDs already present in generated events.
   - Therefore richer V3 ensemble/role research cannot affect instrument choice unless the upstream genre→arrangement stage is wired to it.

3. **The legacy semantic compiler reads only a narrow subset of profile text.**
   - `genre_pre_generation_compiler.py` scans a limited list of legacy fields and converts matched words to semantic tags.
   - Structured V3 sections such as `musical_grammar`, `ensemble`, `performance`, `variant_resolution`, empirical references, role-state rules, and safeguards are not compiled into executable generation behavior.

4. **Classical bypasses the generic communication blueprint.**
   - `build_setup()` special-cases `Classical` and calls `classical_composition.build_classical_setup()`.
   - `genre_communication_blueprint.py` explicitly rejects Classical.
   - `genre_performance_realization.py` explicitly leaves Classical's specialized path unchanged.
   - The Classical implementation fixes a specific tonal chamber/orchestral pilot with its own form, meter, harmonic vocabulary, motif/rhythm tables and orchestration.
   - Therefore new V3 Classical variant research does not automatically control Classical composition.

5. **Last night's piano listening tests were research harnesses, not full Composer executions.**
   - They intentionally bypassed the live Composer to isolate harmony/melody/rhythm before orchestration.
   - Consequently those MP3s could not demonstrate whether the live Composer was consuming V3 genre intelligence.
   - Their musical failures remain useful validation evidence, but they are not proof of successful V3→Composer communication.

## Diagnostic isolation completed

- The experimental reasoning engine remains preserved.
- A new diagnostic branch was created:
  `genre-contract-v3-no-reasoning-diagnostic`
- `experimental_reasoning/` and its reasoning workflow were removed from this branch only.
- No reasoning-engine source was deleted from its preserved branches/history.

## V3 source bridge added

A read-only canonical access module now exists:

`current_master_forward/genre_contract_v3_execution_bridge.py`

It:
- requires all 55 V3 contracts,
- returns the V3 `current_profile_snapshot`,
- carries the complete structured V3 contract sections,
- hashes the exact loaded contract,
- invokes no reasoning engine,
- generates no music.

On this diagnostic branch, the engine selection profile and execution adapter have been switched to V3 snapshots and attach a V3 execution packet so the source can be audited.

## Current status

**Root cause identified: the improved genre research and the executable Composer were not the same data path.**

Reading V3 is only the first repair. The remaining work is to make the generation stages execute V3 structure rather than merely carry it.

## Repair order

1. Prove V3 source identity survives selection and execution handoff for all 55 genres.
2. Replace hard-coded genre instrument palettes with explicit V3-backed arrangement/formation authority where evidence is ready; retain clearly marked fallback only where V3 formation evidence is incomplete.
3. Compile structured V3 musical grammar into executable tempo, meter, form, harmonic rhythm, melody, bass, texture, cadence and rhythm behavior.
4. Remove Classical's informational isolation by giving its specialized generator an explicit resolved V3 variant package before note generation.
5. Keep instrument resolution downstream and non-creative: it should render the already-selected genre-correct roles, not invent genre identity.
6. Only after source→generation communication is proven, resume piano/orchestral listening tests.
7. Keep the experimental reasoning engine out of this diagnostic until the base genre communication path works without it.

## Safety rule

Do not promote this diagnostic branch into the live Composer merely because V3 data can be read. Promotion requires structural tests plus human listening validation that the resulting music actually reflects the selected genre/variant.
