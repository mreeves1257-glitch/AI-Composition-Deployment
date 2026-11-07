# Rock Mode A component-context listening comparison

Date: 2026-11-07  
Branch: `genre-contract-v3-no-reasoning-diagnostic`  
Status: diagnostic listening only.

## Source authority

Role-isolated source package:
- workflow run: `42390723896`
- artifact: `Rock_Mode_A_Role_Isolated_Listening`
- artifact ID: `13581427805`
- artifact digest: `sha256:4969d1f60fc2b494c04f79e979568c79c691ca5a0dcfb41739daeb5d7c935726`
- all six MP3s passed workflow `ffprobe` validation as MP3 / 44.1 kHz / stereo.

The earlier role-isolated artifacts from runs `42389872268` and `42390219578` must not be used as lead-listening authority: their HARMONY MP3s were valid, but the LEAD MP3 packaging was malformed despite the workflow reporting success. They are superseded by run `42390723896`.

## Component mixes

These are secondary diagnostic mixes assembled from the validated role-isolated MP3s. They do not change notes or performance logic.

Existing target gains were preserved:
- HARMONY: -5 dB
- LEAD: -6 dB
- no additional common gain
- no normalization
- no limiter
- 256 kbps MP3 output

Four context conditions:

1. `A_BASELINE`
   - A HARMONY + A LEAD
   - SHA-256: `60cc85ebc30edf4709ae6823d581f60a3ec392fb92b585da09f8a41773d53caa`

2. `C_LEAD_ONLY_MODE_A`
   - A HARMONY + B LEAD
   - isolates the modest lead-duration connection treatment in otherwise-baseline context
   - SHA-256: `ee3e5e60d0ef2719dace458abf3a25ad3a9c5d283bff196e0cb29a1de7f4919c`

3. `D_HARMONY_ONLY_MODE_A`
   - B HARMONY + A LEAD
   - isolates the strong rhythm-guitar sustain treatment in otherwise-baseline context
   - SHA-256: `c2d3e87be7a55751cfa0e07228efb988689626583abe9f2e1df86476ddfbe9c3`

4. `B_FULL_MODE_A`
   - B HARMONY + B LEAD
   - SHA-256: `3c14d6f31791f5c0b25124eb8748795f5102d785a9abb8c3f84f516e128faefa`

All four validate as MP3 / 44.1 kHz / stereo / approximately 78.21 s.

Peak level after mixing is approximately -9.0 dBFS in every condition, so no condition is clipping and there is no level-normalization confound.

## Audio-envelope evidence

Using 10 ms RMS windows on the validated full role files:

At RMS > 0.01 linear full-scale (approximately -40 dBFS):
- LEAD active fraction: A 48.48% -> B 52.21% (about +3.73 percentage points)
- HARMONY active fraction: A 25.07% -> B 66.13% (about +41.06 percentage points)

90th-percentile envelope level is essentially unchanged in both roles. This supports the interpretation that Mode A primarily changes sustain/occupancy rather than attack loudness.

## Decision use

Compare:
- A vs C to judge LEAD Mode A in context.
- A vs D to judge HARMONY Mode A in context.
- C vs B to hear what adding HARMONY Mode A does after lead connection is already present.

No new performance behavior is authorized by these mixes. Human listening remains the gate before changing the HARMONY duration policy or enabling any other performance dimension.
