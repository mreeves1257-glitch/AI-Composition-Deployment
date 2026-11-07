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


## Musical memory

The reasoning engine now includes abstract musical-idea memory.

A remembered idea can retain descriptors such as contour, rhythmic character, harmonic relationship, expressive character, origin section, origin instrument, last carrier, age, appearances, and transformations.

The memory layer does not store an instruction to replay exact notes. Instead it can decide to:

- transform and recall an earlier idea;
- let another compatible instrument answer or carry it;
- develop it before introducing more major material;
- recontextualize it harmonically when the genre permits;
- fragment, extend, shift register, reshape rhythm, or vary contour;
- deliberately leave it dormant.

This supports musical continuity without turning the composition into a loop.

### Memory and equal instrument importance

Idea transfer can also support equal instrument importance. When an instrument has been underserved in the whole-composition importance ledger, the reasoning layer may prefer that instrument as the next carrier of a remembered idea when the existing genre and capability rules say the transfer is musically appropriate.

This does not make instruments interchangeable. Compatibility remains mandatory.

### Memory principle

Recognition should come from preserved identity across change, not from compulsory literal repetition.

Absence is also musically meaningful. A remembered idea does not need to return immediately, and not every stored idea must return at all.


## Bass character — maximum rich depth

Default: `bass_richness = 1.0`

The bass is required to sound powerful, deep, full, warm, and harmonically defined.

This is a **sound-character requirement**, not a compositional-importance override. Bass remains equal in compositional importance with every other active instrument.

The target character is:

- very deep low-register authority;
- strong fundamental weight;
- full low-mid body;
- warm tone;
- controlled attack rather than thin click;
- enough upper-harmonic definition for the bass line to remain perceptible on smaller speakers;
- clear coordination with kick and other low-register parts;
- no weak, hollow, or anemic bass timbre.

Richness must not turn into mud. If low-frequency parts collide, the arrangement and later mix/render stages should create separation rather than simply reducing the bass to insignificance.

V0.1 does not apply EQ, compression, saturation, synthesis, sample selection, or rendering. It emits a future realization contract that later audio stages must satisfy.
