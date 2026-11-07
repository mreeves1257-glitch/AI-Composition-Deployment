# Composer Musical Reasoning Engine v0.1

## Status

Experimental and isolated. This branch does **not** modify the live Composer pipeline, note generator, audio renderer, mixer, sample selection, or existing 55-genre authority.

Planned future position:

```
Genre selection/profile/interpreter
        ↓
Pre-generation genre plan
        ↓
Composer Musical Reasoning Engine
        ↓
Existing note/event generation
        ↓
Existing performance / separation / mix / render chain
```

## Core purpose

The reasoning engine decides what the composition should do next from musical state rather than merely applying a fixed pattern.

Current reasoning dimensions include section function, energy movement, density, repetition/development, transitions, contrast, instrument interaction, and whole-composition memory.

## Parameter 001 — Equal Instrument Importance

Default: `instrument_balance = 1.0`

This means **all active instruments have equal compositional importance**.

It does **not** mean:

- equal note quantity;
- equal loudness;
- equal foreground time;
- identical rhythms;
- identical roles;
- every instrument playing at every moment.

It does mean:

- every active instrument must have a meaningful musical function in the composition;
- no active instrument is treated as disposable filler;
- no instrument is permanently classified as less important background material;
- temporary focus or solos are allowed without creating permanent structural superiority;
- intentional rest is allowed when it shapes space, expectation, or contrast;
- chronic neglect is not allowed.

The engine tracks a meaningful-function ledger across composition windows. If one instrument has repeatedly received less meaningful participation than the others, it becomes a priority for an appropriate role in a later window.

## Instrument interaction

Equal importance is implemented through interaction rather than uniformity.

The engine creates abstract role slots such as:

- foundation or anchor;
- groove or pulse;
- harmonic motion or color;
- answer or counter-motion;
- texture or space shaping;
- transition or section link.

The reasoning layer does not force a specific instrument into an incompatible role. Existing genre and instrument-capability layers remain authoritative for what each instrument can appropriately do.

When parts collide for register, rhythm, or attention, the rule is to redesign the interaction rather than declare one instrument unimportant.

## Other v0.1 rules already present

- repeated sections should develop rather than simply clone;
- a verse after a strong chorus can pull back rather than stay at peak intensity;
- bridges create contrast without requiring simple loudness escalation;
- transitions consider the next section;
- genre-specific groove and harmony remain authoritative;
- decision packets are hashed so accidental mutation can be detected;
- v0.1 emits reasoning only — no MIDI, note events, or audio.

## Integration guardrail

Do not connect this branch to live generation until its decision behavior has been tested against representative genres and section sequences. The existing Composer remains unchanged until a deliberate integration step is approved.
