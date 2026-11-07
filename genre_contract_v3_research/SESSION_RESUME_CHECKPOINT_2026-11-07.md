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


## Rock Mode A HARMONY 2.0 cap — full 40-bar diagnostic launched

A full-form diagnostic comparison has been started without changing the canonical Composer policy.

Workflow:
`Rock Mode A Harmony Cap Full 40`

Run:
`42392024204`

Comparison:
- diagnostic HARMONY cap 2.0 beats + canonical treated LEAD
- current canonical HARMONY cap 2.8 beats + the exact same treated LEAD

The full-40 renderer asserts:
- exactly 78 HARMONY note-events trimmed from current canonical Mode A
- exactly 26 vertical rhythm-guitar gestures trimmed
- all canonical HARMONY shortenings preserved
- pitch, onset, velocity, voicing and event identity unchanged
- LEAD policy unchanged
- bass/drums unchanged
- no bar-boundary crossing
- reasoning engine excluded
- canonical policy not modified
- live runtime not promoted

The workflow started successfully and is running through the pinned Shinyguitar/sfizz validation and render path.


## Rock Mode A HARMONY 2.0 cap — full 40-bar diagnostic completed

Workflow run: `42392024204` — PASS  
Artifact ID: `13581124287`  
Artifact digest: `sha256:b13b9b2c2a95eb9664ec09b4252f9157ebbc6bf233b78d22b28bac1ae5e6b9c3`

The full-40 renderer, matched context mixes, ffprobe validation and artifact upload all passed.

Verified full-form comparison:
- candidate: HARMONY positive extensions capped at 2.0 beats + canonical treated LEAD
- control: current 2.8-beat HARMONY maximum + identical treated LEAD

Structural checks:
- 78 HARMONY note-events trimmed
- 26 vertical rhythm-guitar gestures trimmed
- all 24 canonical HARMONY shortenings preserved
- pitch/onset/velocity/voicing/event identity unchanged
- LEAD policy unchanged
- bass/drums unchanged
- no reasoning-engine involvement
- canonical policy unchanged
- live runtime unchanged

The 26 extreme gestures are distributed across the full form:
- INTRO_1: 4
- VERSE_1: 5
- CHORUS_1: 5
- VERSE_2: 5
- CHORUS_2: 5
- OUTRO_1: 2

Policy diagnosis:
- `ring_fraction = 0.84`
- `release_gap_beats = 0.15`
- current `max_ringing_beats = 2.8`
- at 4-beat spacing, ring_fraction would allow 3.36 beats and release-gap logic would allow 3.85 beats, so the 2.8 hard ceiling is the controlling term.
- 2.0 therefore tests only that ceiling, not the rest of the duration model.

Full-40 objective audio difference:
- overall difference RMS: `0.00207851`
- difference relative to 2.0 mix RMS: `0.1123`
- INTRO_1 relative difference: `0.1804`
- VERSE_1: `0.1135`
- CHORUS_1: `0.0944`
- VERSE_2: `0.1158`
- CHORUS_2: `0.0892`
- OUTRO_1: `0.1208`

The largest relative change is in the intro; both chorus sections show smaller relative changes than the verses and intro. This is objective only and is not musical approval.

Saved supporting files:
- `ROCK_MODE_A_CAP_2_0_FULL40_SECTION_MAP_2026-11-07.json`
- `ROCK_MODE_A_CAP_2_0_FULL40_DURATION_REMOVAL_2026-11-07.json`
- `ROCK_MODE_A_HARMONY_CAP_POLICY_DOMINANCE_2026-11-07.json`
- `ROCK_MODE_A_CAP_2_0_FULL40_AUDIO_DIFFERENCE_2026-11-07.json`
- `ROCK_MODE_A_CAP_2_0_FULL40_LISTENING_CUE_SHEET_2026-11-07.md`
- `ROCK_MODE_A_CAP_2_0_DECISION_GATE_2026-11-07.md`

Active gate:
Human full-40 listening comparison of 2.0 vs 2.8. Do not change the canonical policy or add another performance variable before that judgment.

Infrastructure note:
A reusable cached pinned-sfizz composite action was added at `.github/actions/setup-pinned-sfizz/action.yml` for future diagnostics so repeated renderer compiles can be avoided.


## Blind human listening gate prepared

To reduce expectation bias, exact byte-for-byte copies of the verified full-40 and focused 2.0-vs-2.8 comparisons were created under neutral A/B names.

No remix, normalization, transcoding or audio modification was performed. SHA256 hashes match the verified originals exactly.

Blind mapping is recorded in:
`ROCK_MODE_A_CAP_2_0_BLIND_LISTENING_MAP_2026-11-07.json`

Active gate:
- User listens to Blind A and Blind B without seeing the cap identity.
- User judges which version sounds more natural across the full form and/or focused montage.
- Only after that judgment should the mapping be revealed.
- No canonical policy change before blind judgment.


## Blind sustain-cap result and next Rock candidate

Blind human result:
- User preferred **Blind B**.
- Blind B maps to the **current 2.8-beat HARMONY sustain ceiling**.
- The 2.0-beat replacement candidate is therefore rejected.
- No canonical change was required because 2.8 was already the current Mode A setting.

Decision record:
`ROCK_MODE_A_CAP_2_0_HUMAN_LISTENING_DECISION_2026-11-07.json`

Next disabled Rock performance candidate inspected:
- `ROCK_SHINYGUITAR_STRUM_ATTACK_TIMING_V1`
- note gap: 0.038 beat
- max strum span: 0.14 beat
- alternating direction: true
- default enabled: false
- listening approved: false

Provenance finding:
The branch contains the strum candidate parameters but no dedicated strum renderer/verifier/listening artifact. Older instrument-performance code groups near-simultaneous electric-guitar notes as one gesture for duration logic but does not actually stagger their attacks. The strum candidate is therefore unvalidated research, not an already-proven implementation.

A symbolic-only safety verifier has been added:
`verify_rock_v3_strum_candidate_safety.py`

Workflow:
`Rock V3 Strum Candidate Safety`

Run:
`42393038398`

The verifier asks whether 0.038-beat string staggering can be applied as a pure onset change without causing next-gesture overlap or bar-boundary violations. If not, it separately checks whether preserving original note-off times would be mechanically safe before any implementation is considered.

No audio, no strum enablement, no canonical policy mutation, no live promotion, and no reasoning-engine involvement.


## Rock V3 strum candidate safety result

Workflow run:
`42393038398` — PASS

Artifact:
`13582362211`
Digest:
`sha256:0aa2ac71e40d52aafc9cb61738355dc8fbc3559236acaef49bd2d2a2496379f1`

Current Rock HARMONY score:
- 219 HARMONY note-events
- 73 vertical chord gestures
- all 73 gestures contain exactly 3 notes
- proposed note gap: 0.038 beat
- required 3-note strum span: 0.076 beat
- candidate maximum span: 0.14 beat

Unsafe form rejected:
**pure onset stagger with durations unchanged**
- 8 bar-boundary crossing notes
- 16 next-gesture overlap notes
- 8 gestures with at least one overlap
- worst resulting overlap: 0.046 beat

Safe mechanical form:
**onset stagger with each original absolute note-off preserved**
- 0 nonpositive durations
- minimum resulting duration: 0.144 beat
- 146 delayed note-events
- maximum mechanical duration reduction: 0.076 beat
- no new sustain; release times stay exactly where Mode A put them

This means any future strum A/B must use note-off preservation. The unchanged-duration version is explicitly rejected.

A symbolic candidate executor has been added:
`current_master_forward/rock_v3_strum_candidate_executor.py`

A symbolic execution verifier has been added:
`genre_contract_v3_research/verify_rock_v3_strum_candidate_execution.py`

Execution verification workflow:
`Rock V3 Strum Candidate Execution Verify`
Run:
`42393131339`

No audio yet. Strum remains disabled. Canonical Mode A remains unchanged. Reasoning remains excluded. Live runtime remains untouched.


## Rock V3 strict strum A/B listening gate launched

Symbolic execution verification:
`Rock V3 Strum Candidate Execution Verify`
Run `42393131339` — PASS

Verified candidate behavior:
- 73 HARMONY vertical chord gestures
- 3 notes per gesture
- alternating low-to-high / high-to-low direction
- offsets per gesture: 0.000 / 0.038 / 0.076 beat
- 146 delayed note-events
- every original absolute note-off preserved exactly
- current 2.8-beat Mode A HARMONY sustain policy preserved
- no pitch/velocity/event-count changes
- LEAD/BASS/DRUMS unchanged
- no live enablement
- no reasoning engine

Strict listening workflow:
`Rock V3 Strum Listening AB`
Run:
`42393208378`

Listening definitions:
- A = current Mode A HARMONY vertical attacks
- B = same Mode A score plus safe note-off-preserving strum attack staggering
- both keep the human-preferred current 2.8 sustain ceiling
- workflow produces HARMONY-only A/B and HARMONY+fixed treated-LEAD context A/B

No other performance variable is allowed in this gate.


## Rock V3 strict strum A/B completed and blinded

Strict listening workflow:
`Rock V3 Strum Listening AB`
Run `42393208378` — PASS

Artifact:
`13582452120`
Digest:
`sha256:b7b8ea8c3d0c3626af991e0e066f69f6c607891c6bb53ea29958b8459d3ca1d8`

Verified 8-bar A/B:
- current Mode A HARMONY attack timing
- safe note-off-preserving strum attack timing
- human-preferred 2.8-beat HARMONY sustain ceiling fixed in both
- treated LEAD fixed in both context mixes
- 24 HARMONY note attacks moved in the 8-bar excerpt
- zero HARMONY note-off times moved
- pitch, velocity, event count, LEAD, BASS and DRUMS unchanged
- exact Shinyguitar resource and mapping verified
- all listening MP3s passed ffprobe

Strum timing:
- 0.038 beat between strings
- 0.076 beat three-note span
- approximately 18.5 ms between strings / 37.1 ms total at 123 BPM
- alternating low-to-high / high-to-low direction

Blind copies were created byte-for-byte with no remixing, normalization or transcoding.
Mapping is recorded in:
`ROCK_V3_STRUM_BLIND_LISTENING_MAP_2026-11-07.json`

Active gate:
User blind judgment of context A vs B. Do not reveal mapping or enable strum before that judgment.
