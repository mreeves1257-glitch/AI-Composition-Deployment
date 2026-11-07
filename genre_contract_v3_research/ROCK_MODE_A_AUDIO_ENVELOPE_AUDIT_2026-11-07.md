# Rock Mode A audio-envelope audit — rhythm guitar

Date: 2026-11-07  
Branch: `genre-contract-v3-no-reasoning-diagnostic`  
Scope: diagnostic only; no live promotion; no new performance behavior.

## Purpose

Quantify how strongly Mode A changes audible rhythm-guitar occupancy before making any additional performance changes.

The comparison uses the already-rendered 8-bar HARMONY intro A/B:

- A = before `A_GUITAR_DURATION_ONLY`
- B = after `A_GUITAR_DURATION_ONLY`
- pitch, onset, velocity, voicing, instrument, form and mix identity remain unchanged
- only note duration differs

## Measurement

- 123 BPM, 4/4.
- 10 ms RMS windows.
- "Audibly active" diagnostic threshold: RMS > 0.01 linear full-scale (approximately -40 dBFS).
- This is an envelope/occupancy metric, not a musical-quality score.

| Bar | A active fraction | B active fraction |
|---:|---:|---:|
| 1 | 14.9% | 63.1% |
| 2 | 14.9% | 70.3% |
| 3 | 14.4% | 44.1% |
| 4 | 14.9% | 70.8% |
| 5 | 13.8% | 52.8% |
| 6 | 43.1% | 84.6% |
| 7 | 14.4% | 62.6% |
| 8 | 41.0% | 88.2% |

## Interpretation

The Mode A rhythm-guitar change is not a subtle envelope polish. It changes the amount of each bar occupied by audible guitar sustain by a large margin.

The attack/peak distribution remains broadly similar between A and B, so the principal audible change is sustained occupancy rather than a simple attack-level increase.

This is consistent with the symbolic audit finding that 26 three-note rhythm-guitar chord gestures change from 0.5 beat to 2.8 beats.

No conclusion about musical quality is granted by this measurement. Human listening remains required.

## Current decision boundary

If B sounds more natural and spacious, retain the current HARMONY duration policy.

If B sounds smeared, pad-like, or too continuous while the LEAD treatment sounds good, repair only the HARMONY duration policy. Do not discard the lead duration treatment and do not add strum timing, bass sustain, random timing, or another performance dimension yet.
