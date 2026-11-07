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


## 3D architecture — plan early, realize late

The Composer already has a preserved downstream 3D mixing stage. The experimental reasoning engine does **not** move or replace that mixer.

Instead, 3D is split into two responsibilities:

1. **Early spatial intent** — during pre-generation reasoning, the Composer decides how instruments should coexist in width, depth, register/frequency space, distance, and conversational placement.
2. **Late physical realization** — after independent instrument stems have been rendered, the existing 3D mixer realizes the approved spatial relationships in audio.

This prevents spatial depth from being merely a final cosmetic effect. Space becomes part of the composition and arrangement while preserving the proven downstream mixer.

### Bass and 3D

The rich-bass requirement uses the spatial plan to keep the bass deep and physically grounded with controlled low-frequency width. Bass and kick should have distinct low-end space, and other equal-importance instruments should remain clear.

Depth is not hierarchy. An instrument placed farther back, wider, or in a different depth zone does not become less important to the composition.


## Kick character — pronounced physical impact

Default: `kick_impact = 1.0`

The kick is intended to be distinctly pronounced in the low end: deep, punchy, full-bodied, physically felt, and easy to locate.

This does not make the kick more compositionally important than other instruments. It defines its sound character and low-end job.

The low-end relationship is:

- **kick:** impact, punch, transient definition, physical hit;
- **bass:** sustained depth, richness, warmth, tonal body.

The two should reinforce each other without collapsing into one muddy low-frequency mass. The 3D spatial plan keeps the kick in a firm, controlled low-frequency center while leaving distinct depth and body for the bass.

A pronounced kick must not be achieved by thinning the bass, masking other instruments, excessive click, uncontrolled boom, or flattening dynamics through overcompression.


## Spatial choreography

3D intent now evolves with song form rather than remaining static.

Examples:

- verses may contract slightly and feel more intimate;
- choruses may widen and deepen;
- bridges may reframe the space for contrast rather than simply becoming louder;
- breakdowns may expose depth by removing spatial clutter;
- outros may gradually release or recede.

Movement must follow musical intent. Random swirling, continuous autopan, and arbitrary depth motion are explicitly rejected unless a genre calls for them.

Kick and bass remain stable enough in the low-frequency center of gravity to preserve physical authority. The deepest low end stays tightly controlled while upper harmonics may contribute width and definition.

## Low-end musical interaction

Kick and bass are not treated as two unrelated parts that happen to occupy low frequencies.

Their default relationship is coordinated at the arrangement level:

- kick supplies physical impact and pulse definition;
- bass supplies sustained depth, tonal body, and motion;
- selected structural accents may lock together;
- other moments may interlock, answer, or leave intentional gaps;
- constant duplication is avoided unless genre identity calls for it;
- walking bass is not forced to mirror every kick;
- four-on-the-floor styles may keep the kick stable while bass moves around it.

Low-end clutter should be solved through timing, role, register, and space before simply reducing the strength of either part.
