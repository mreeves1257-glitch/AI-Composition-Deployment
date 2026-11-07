# Genre V3 Foreground / Melody Execution Diagnosis
Date: 2026-11-07
Branch: genre-contract-v3-no-reasoning-diagnostic

## Why this diagnosis exists

The Genre Contract V3 source, structured pre-generation data, source-pattern
accompaniment, and current instrument identities now survive the reconstructed
Composer path. The remaining musical gap is the foreground/melody layer.

This diagnostic intentionally excludes the experimental reasoning engine and
does not authorize audio.

## Confirmed source-pattern limitation

The restored original project-authored source-pattern packs cover all 55 genres
and remain structurally compatible with the current V3 profile IDs.

Their role vocabulary is limited to:

BASS, BRUSH, CLAP, CLAVE, CONGA, CYMBAL, HAND_DRUM, HARMONY, HAT, KICK,
LEFT_HAND, RIDE, RIGHT_HAND, SHAKER, SNARE.

Across all 55 seeds there are zero explicit roles named LEAD, MELODY, SOLO,
HOOK, THEME, COUNTER or VOCAL.

Therefore the source-pattern system is an accompaniment/groove/role seed layer.
It is not a finished-composition melody authority.

## What the old Stage-4 lead generator actually did

The legacy automatic generator selected the first eligible lead-capable
instrument from a fixed list:

lead_guitar, alto_sax, tenor_sax, baritone_sax, trumpet, trombone, clarinet,
flute, violin, synth_lead, synth_arp.

It then:
- placed the lead mainly on alternating bars, with a few template exceptions;
- selected four or six notes per bar from one shared _melody_cells mechanism;
- used only coarse semantic switches such as lyrical/space/energetic;
- chose a generic register by instrument group;
- used common duration presets;
- reused the same broad melodic machinery across substantially different genres.

This means correct genre selection and correct instrument identity could still
reach a foreground composer that flattened genre differences into one generic
melody mechanism.

## Why the old interpreter files do not solve this by themselves

The 2026-10-09 genre-owned interpreter slots explicitly state that they own the
Stage-3-to-4 translation of section density, groove, chord conversion,
retrigger/voice-leading behavior, fills and player instructions.

They explicitly leave STAGE4_COMPOSE_SEPARATE_PARTS to the original Composer.

The restored source-pattern seeds were therefore never intended to be complete
melody scores.

## Existing genre-specific foreground work

Rock has a real research-only melodic author:

composer_overrides/rock_melodic_author_v1.py

That author:
- rewrites only an existing LEAD track;
- preserves the old Composer's lead-entry/rest bars;
- uses harmonic/motivic phrase logic;
- preserves all non-lead events;
- is Rock-specific and 4/4-specific;
- was disabled by default and not a universal melody engine.

It cannot simply be dropped onto the recovered source-pattern accompaniment,
because those source-pattern seeds contain no LEAD track or lead-window
scaffold.

It is useful evidence for the architecture, not a generic 55-genre solution.

## V3 foreground information that already exists

All 55 current V3 contracts contain:
- musical_grammar.melody_model
- musical_grammar.phrase_model
- musical_grammar.development_model
- ensemble.role_handoff_rules
- ensemble.foreground_window_rules

Classical additionally has bounded candidate melody behavior for Classical
Period and Romantic tonal variants and has a separate V3 research lane.

The missing step is not more prose. It is a genre-specific foreground execution
compiler that converts these V3 rules into explicit ownership windows,
phrase/rhythm/contour constraints and then note events.

## New guardrails now in the diagnostic branch

1. Source-pattern accompaniment may not be promoted as a finished composition.
2. The 40 automatic source-pattern genres stop after current-instrument
   resolution until foreground execution is compiled.
3. The 7 automatic genres with explicit researched V3 formations stop before
   the old generic melody generator. A formation is not permission to invent
   a composition.
4. Classical remains on its separate V3 structural/note/orchestration research
   path.
5. The legacy generic melody generator is no longer allowed to silently become
   V3 execution authority.
6. No audio or live promotion is authorized by these diagnostic gates.
7. The experimental reasoning engine remains preserved but excluded.

## Reconstructed-runtime proof

Workflow:
Genre V3 Symbolic Runtime Instrument Resolution

Run ID: 42379740623
Result: PASS

Artifact:
V3_Runtime_Symbolic_Instrument_Resolution_Audit
Artifact ID: 13577216479
Artifact SHA256:
31b3b90ab7f8af7b1ff9c73bc46137156bb4f7f698d0b8dd0066cbfaa5d02760

The reconstructed Composer proves:
- 40 automatic source-pattern genres use V3-governed symbolic events and current
  instrument identities while bypassing the old note generator;
- 7 automatic explicit-formation genres stop safely before the legacy generic
  melody generator;
- source-pattern packages remain marked accompaniment-only;
- finished-composition authority is false;
- foreground notes are not fabricated;
- audio remains blocked.

## Next repair

Build the foreground layer separately from accompaniment:

V3 genre/variant
→ foreground ownership / role handoff
→ phrase windows
→ rhythm/contour/harmonic constraints
→ genre-specific foreground note execution
→ accompaniment interaction / thinning
→ structural validation
→ human listening
→ only then audio/live promotion.

Do not solve this by reactivating the shared generic melody-cell generator.
