# AI Composer — resumed diagnostic checkpoint (2026-11-07)

## Scope and protection

- Repository: `mreeves1257-glitch/AI-Composition-Deployment`
- Research branch: `genre-contract-v3-no-reasoning-diagnostic` (not the live Composer)
- Experimental Musical Reasoning Engine v0.1 remains preserved on its own branches/history and is excluded from this diagnostic lane.
- No live merge, deployment, synthetic instrument substitution, or production-fidelity approval is authorized here.

## Recovered verified project records

1. V3 research holds all **55** genre contracts in `genre_contract_v3_research/GENRE_CONTRACT_V3_ALL_55.json`.
2. `GENRE_EXECUTION_WIRING_DIAGNOSIS_2026-11-07.md` records the original fault: the October registry, hard-coded palettes, and generic melody path did not execute the improved V3 information.
3. `V3_FOREGROUND_EXECUTION_DIAGNOSIS_2026-11-07.md` records the reconstructed-runtime symbolic-instrument validation (workflow run 42379740623) and the separation between accompaniment pattern seeds and original foreground composition.
4. Rock has since received dedicated V3 form, harmony, development, foreground, and performance modules in `current_master_forward/rock_v3_*.py`. Rock Core candidate is a **40-bar symbolic score**; the reviewed first performance mode changes **electric-guitar note duration only**, preserving melodic pitch/onsets and the bass/drum parts. These are research candidates, not listening approval.
5. Rock INTERNAL target registry maps rhythm and lead guitar separately to the same recovered Karoryfer Shinyguitar resource; bass to Growlybass and the drums to Big Rusty Drums. Mapping/source identity is not evidence of auditory realism or performance capability.

## Exact handoff at feed stall

- Branch head inspected: `e54b91b71d9528c4a70a804598f31e56a8f29e33`, **Add isolated Shinyguitar note-length response proof workflow**.
- Source proof: `genre_contract_v3_research/verify_shinyguitar_note_length_response.py`.
- Pinned resource installer: `genre_contract_v3_research/install_pinned_rock_resource_proof.sh`.
- GitHub Actions workflow: `.github/workflows/shinyguitar-note-length-response-proof.yml`.
- Test compares two renders with identical SFZ mapping, pitch, velocity, onset, tempo, total MIDI duration and renderer; it changes only note-off time (0.25 vs 2.00 s).
- This checkpoint **does not claim that the workflow has run or passed**. Available linked GitHub commit-workflow lookup returned no PR-associated runs, which cannot establish the status of push-triggered runs.
- **Next required gate:** inspect actual workflow result and measurement artifact; if green, record a scoped Shinyguitar NOTE_LENGTH_RESPONSE certificate for this exact resource/mapping/renderer, without claiming production fidelity. If red, diagnose and repair only the failing test or renderer/resource boundary. After that, perform narrow Rock Mode A listening A/B; do not promote live automatically.

## Musical quality issue remains open

Earlier Classical MP3s had mechanically repetitive, weakly developed melodies. Successful symbolic wiring or one guitar resource-response proof cannot by itself solve composition quality. Keep melody/phrasing, genre-specific execution, orchestration and human listening as separate validation gates.


## Rock Mode A capability + listening gate completed

- Shinyguitar NOTE_LENGTH_RESPONSE proof passed in workflow run `42388034436`.
- Exact mapping: `Programs/composer_electric.sfz`; wrapper SHA-256 `da026ba66ab34a4ebb99c6cda93a24d4bc48e57e252a26db5c1fd6916cbaed35`.
- Sample graph proof: 6,798 sample references, 846 unique samples, 16 SFZ files validated.
- Scoped capability certificate recorded at `SHINYGUITAR_NOTE_LENGTH_CAPABILITY_CERTIFICATE_2026-11-07.json`.
- Production fidelity, full-composition quality, and live promotion remain explicitly uncertified.

### Controlled Rock Mode A guitar A/B
- Workflow run `42388941089`: PASS.
- Artifact `Rock_Mode_A_Guitar_Listening_AB`, artifact ID `13580902032`.
- 40 bars, 123 BPM; HARMONY + LEAD electric guitar only.
- A = developed Rock Core symbolic score before Mode A.
- B = same score after Mode A.
- Only A/B difference: electric-guitar note durations.
- 268 guitar events changed duration.
- Pitch, onset, velocity, instrument identity, and structure remained unchanged.
- Bass and drums deliberately excluded.
- Reasoning engine excluded.
- Human listening review is now the active gate. Do not add strum timing, bass sustain, or other performance variables until A/B is judged.


## Continued diagnostic results — Shinyguitar capability and Rock Mode A listening gate

### Shinyguitar NOTE_LENGTH_RESPONSE — proven

Workflow: `Shinyguitar Note Length Response Proof`  
Successful run: **42388034436**

Exact scope:
- resource: `KARORYFER_SHINYGUITAR`
- mapping: `Programs/composer_electric.sfz`
- wrapper SHA-256: `da026ba66ab34a4ebb99c6cda93a24d4bc48e57e252a26db5c1fd6916cbaed35`
- renderer pin: `sfizz 1.2.3@4e70dc0bef53b41f2853ed46e26f5911114c92d0`
- full recovered sample graph validated: 6,798 references / 846 unique samples / 16 SFZ files
- short note active end: 0.34 s
- long note active end: 2.04 s
- active-duration difference: 1.70 s

The isolated test held pitch, velocity, onset, tempo, mapping and total MIDI length constant and changed note-off time only. It therefore certifies NOTE_LENGTH_RESPONSE for this exact mapping/backend combination. It does **not** certify production fidelity or the full composition.

Certificate:
`genre_contract_v3_research/SHINYGUITAR_NOTE_LENGTH_CAPABILITY_CERTIFICATE_2026-11-07.json`

### Controlled Rock Mode A guitar A/B — rendered

Workflow: `Rock Mode A Guitar Listening AB`  
Successful run: **42388941089**

Comparison:
- A = Rock V3 40-bar developed score before Mode A
- B = same score after `A_GUITAR_DURATION_ONLY`
- exact same Karoryfer Shinyguitar mapping
- 123 BPM
- rhythm guitar + lead guitar only
- **268 guitar events** have changed duration
- no pitch changes
- no onset changes
- no velocity changes
- no instrument changes
- bass/drums deliberately excluded from this first listening gate
- experimental reasoning engine excluded
- same fixed target gains in both conditions: HARMONY -5 dB, LEAD -6 dB
- one common mix gain; no separate normalization that could bias the comparison

Published diagnostic listening files:
- `genre_contract_v3_research/listening_outputs/rock_mode_a_guitar_ab/A_BEFORE_MODE_A.mp3`
- `genre_contract_v3_research/listening_outputs/rock_mode_a_guitar_ab/B_AFTER_MODE_A.mp3`
- `genre_contract_v3_research/listening_outputs/rock_mode_a_guitar_ab/ROCK_MODE_A_GUITAR_AB_LISTENING_REPORT.json`

### Current gate

**STOP FOR HUMAN LISTENING REVIEW.**

Question: Does B sound more connected/natural than A without blurring intentional rests, rhythm-guitar riff articulation, or lead phrase gaps?

Do not add strum timing, bass sustain, random timing, full-band mix, or live promotion until this A/B is judged by ear.


## Rock Mode A symbolic duration-shape audit

Workflow: `Rock Mode A Duration Shape Audit`  
Run ID: `42389442115`  
Artifact ID: `13581210356`  
Result: PASS

Measured state:
- 897 total events.
- 268 guitar duration changes; 629 events unchanged.
- 244 extensions and 24 shortenings.
- HARMONY: 186 changed events; mean delta +1.30597 beats, median +1.18, max +2.3, min -0.28.
- LEAD: 82 changed events; mean delta +0.08024 beat, median +0.0825, range +0.05 to +0.1675.
- No same-track overlaps.
- No cross-bar duration spill.
- No split duration inside vertical rhythm-guitar chord gestures.
- No cross-bar lead phrase-gap mutation.
- Minimum remaining same-track gap: 0.03 beat.
- Pitch/onset/velocity/instrument/bass/drums unchanged.
- Reasoning engine excluded; live runtime untouched.

Important listening risk:
- 78 HARMONY note events use the largest +2.3-beat extension.
- Because harmony attacks are three-note vertical voicings, this is 26 chord gestures changing from 0.5 beat to 2.8 beats.
- This is structurally safe but may be musically over-sustained.
- Focused cue sheet saved as `ROCK_MODE_A_LISTENING_CUE_SHEET_2026-11-07.md`.

Active gate remains human A/B listening. Do not add strum timing, bass sustain, random timing, or other performance variables until Mode A duration behavior is judged.


## Rock Mode A role-isolated listening package

Workflow: `Rock Mode A Role Isolated Listening`  
Corrected run ID: `42390219578`  
Artifact ID: `13580684994`  
Artifact digest: `sha256:19e7e4a6beec1233dc60af79a04c5010e7c51f40c68b4f09c208fd4d3c8497d5`  
Result: PASS

Purpose:
- No new performance behavior added.
- Re-rendered the exact existing A/B and exported role-isolated listening pairs.
- Full HARMONY A/B, full LEAD A/B, and focused 8-bar HARMONY intro A/B.
- Exact Shinyguitar resource and sample graph revalidated.
- Pinned sfizz renderer unchanged.
- Chunked MP3 encoding used to avoid malformed long-buffer output.
- All six MP3s validated after download as MPEG Layer III, 256 kbps, 44.1 kHz, stereo.
- Reasoning engine excluded; live runtime untouched.

Active gate:
- Judge HARMONY sustain separately from LEAD connection.
- Do not add strum timing, bass sustain, random timing, continuous control, or other performance variables until this role-isolated A/B is judged.


## Corrected role-isolated Rock Mode A listening authority

Supersedes the earlier role-isolated MP3 artifacts.

Validated workflow run: `42390723896`  
Artifact ID: `13581427805`  
Artifact digest: `sha256:4969d1f60fc2b494c04f79e979568c79c691ca5a0dcfb41739daeb5d7c935726`

- Workflow now installs ffmpeg and encodes with libmp3lame.
- Every listening MP3 is validated with ffprobe before upload.
- Six files pass as MP3 / 44.1 kHz / stereo.
- Earlier role-isolated artifacts from runs `42389872268` and `42390219578` are superseded for LEAD listening because their lead MP3 packaging was malformed despite successful workflow status.
- Reasoning engine excluded; live runtime untouched.

### Audio-envelope comparison

Using the validated full role-isolated files and 10 ms RMS windows:

At approximately -40 dBFS activity threshold:
- LEAD active fraction: A 48.48% -> B 52.21% (+3.73 percentage points).
- HARMONY active fraction: A 25.07% -> B 66.13% (+41.06 percentage points).

This strongly localizes the large Mode A occupancy change to HARMONY sustain rather than LEAD connection.

### Component-context listening mixes

Secondary diagnostic mixes were built from the validated role files with the existing Composer target gains:
- HARMONY -5 dB
- LEAD -6 dB
- no normalization / limiter / new performance behavior

Conditions:
- A_BASELINE = A HARMONY + A LEAD
- C_LEAD_ONLY_MODE_A = A HARMONY + B LEAD
- D_HARMONY_ONLY_MODE_A = B HARMONY + A LEAD
- B_FULL_MODE_A = B HARMONY + B LEAD

All four validate as MP3 / 44.1 kHz / stereo / ~78.21 s.

Active listening gate:
- Compare A vs C for LEAD Mode A in context.
- Compare A vs D for HARMONY Mode A in context.
- Compare C vs B to hear the incremental effect of adding HARMONY Mode A after the lead treatment.
- Do not add strum timing, bass sustain, random timing, continuous control, or any other performance variable yet.


## Rock Mode A component-in-context localization

Verified role-isolated workflow run: `42390723896`  
Artifact ID: `13581427805`  
Artifact digest: `sha256:4969d1f60fc2b494c04f79e979568c79c691ca5a0dcfb41739daeb5d7c935726`

The corrected package passed ffmpeg encoding and ffprobe validation for every MP3.

A context-mix diagnostic was built with the original mix gains:
- HARMONY: -5 dB
- LEAD: -6 dB
- common mix gain: 1

Compared with baseline A:
- LEAD-only Mode A difference RMS: `0.00128279`, about 14.8% of the full A→B difference RMS.
- HARMONY-only Mode A difference RMS: `0.00858549`, about 99.0% of the full A→B difference RMS.
- Full Mode A difference RMS: `0.00867396`.

These ratios are magnitude comparisons, not additive percentages. They strongly localize Mode A's audible impact to the HARMONY/rhythm-guitar duration treatment. The LEAD treatment is materially smaller.

Saved report:
`ROCK_MODE_A_COMPONENT_AUDIO_DIFFERENCE_REPORT_2026-11-07.json`

No new performance variable was added. Active gate remains human listening before changing the HARMONY duration policy.


## Rock Mode A HARMONY sustain-cap sweep started

Purpose: isolate the one parameter now strongly implicated by the component analysis — maximum rhythm-guitar ringing duration — without changing any other performance behavior.

Canonical current HARMONY maximum:
- `max_ringing_beats = 2.8`

Diagnostic listening brackets:
- BASELINE: no Mode A HARMONY duration realization
- CAP_1_4: same Mode A HARMONY policy, positive extensions capped at 1.4 beats
- CAP_2_0: same Mode A HARMONY policy, positive extensions capped at 2.0 beats
- CURRENT_2_8: canonical Mode A HARMONY control

Existing Mode A shortenings remain unchanged in capped candidates. Pitch, onset, velocity, voicing, event count, lead, bass, drums and reasoning remain untouched.

First 8-bar symbolic forecast:
- 10 affected rhythm-guitar chord gestures.
- Canonical after-duration distribution: six at 2.8 beats, two at 1.68, one at 1.26, one at 1.05.
- 1.4 cap trims 8 of 10 gestures.
- 2.0 cap trims only the six extreme 2.8-beat gestures.

Full 40-bar symbolic forecast:
- 62 affected HARMONY chord gestures.
- 26 gestures currently reach 2.8 beats.
- 2.0 cap therefore targets only those 26 extreme gestures.
- 1.4 cap also trims the 1.68- and 1.47-beat groups, for 39 gestures total.

Files:
- `render_rock_mode_a_harmony_cap_sweep.py`
- `ROCK_MODE_A_HARMONY_CAP_SWEEP_SYMBOLIC_FORECAST_2026-11-07.json`
- workflow `Rock Mode A Harmony Cap Sweep`

Workflow run `42391402408` is active. Exact Shinyguitar restore and 846-sample graph validation have passed; pinned sfizz build is the current stage.

No live promotion and no canonical duration-policy modification has been made.


## Rock Mode A HARMONY sustain-cap sweep completed

Audio workflow run: `42391402408` — PASS  
Artifact ID: `13581711960`  
Artifact digest: `sha256:1e19cc89b0536a2e1f6e35d4271c28728eb39216d9d53d9fb5dd636ef3d0ec96`

Symbolic verification workflow run: `42391580885` — PASS  
Artifact ID: `13581249726`  
Artifact digest: `sha256:fdd5493367abd09331605c7be725a2f6b980b34c9fc9d51b463f312ac8b3428a`

Four verified 8-bar rhythm-guitar conditions:
- BASELINE — no Mode A HARMONY extension, max duration 0.5 beat.
- CAP_1_4 — existing Mode A extension behavior capped at 1.4 beats.
- CAP_2_0 — existing Mode A extension behavior capped at 2.0 beats.
- CURRENT_2_8 — canonical current Mode A, 2.8-beat maximum.

All candidates preserve pitch, onset, velocity, voicing, event count, instrument identity and non-HARMONY roles. Canonical shortenings are preserved. No bar crossing or split vertical chord durations.

10 ms RMS envelope occupancy at threshold 0.01:
- BASELINE mean active bar fraction: 21.27%
- CAP_1_4: 46.84%
- CAP_2_0: 58.62%
- CURRENT_2_8: 67.27%

This establishes a clean sustain-density ladder. No canonical policy has been changed. Active gate is human listening to choose whether the shortest natural-sounding cap is 1.4, 2.0 or the current 2.8 beats. If all capped candidates still sound wrong, duration should no longer be treated as the primary issue.


## Rock Mode A HARMONY cap sweep — treated-lead context mixes

Four 8-bar context mixes were created locally from verified artifacts:
- BASELINE HARMONY + treated LEAD
- 1.4-beat HARMONY cap + treated LEAD
- 2.0-beat HARMONY cap + treated LEAD
- current 2.8-beat HARMONY + treated LEAD

Mix gains are unchanged from the original Rock A/B:
- HARMONY: -5 dB
- LEAD: -6 dB
- common gain: 1

All four context files are 15.908571 s, 44.1 kHz stereo MP3.

Pairwise difference RMS relative to baseline mix level:
- baseline → 1.4: 0.5083
- baseline → 2.0: 0.5559
- baseline → 2.8: 0.5781
- 1.4 → 2.0: 0.2086
- 2.0 → 2.8: 0.1508

Interpretation:
- The 1.4→2.0 change remains materially distinct in context.
- The 2.0→2.8 change is smaller.
- From a minimal-change standpoint, 2.0 is the targeted candidate because it trims only the extreme 2.8-beat gesture group; this is not human listening approval.

Saved report:
`ROCK_MODE_A_HARMONY_CAP_CONTEXT_REPORT_2026-11-07.json`

No canonical policy change, no live promotion, and no reasoning-engine involvement.
