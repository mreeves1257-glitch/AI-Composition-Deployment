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


## Rock V3 blind strum listening result

User preferred:
**Blind 2 — guitar + treated lead**

Blind mapping reveal:
- Blind 1 context = current Mode A HARMONY vertical attacks + treated LEAD
- Blind 2 context = safe note-off-preserving strum HARMONY + the same treated LEAD

Therefore the preferred diagnostic Rock guitar treatment is now:
- current human-preferred HARMONY max ringing: **2.8 beats**
- HARMONY attack timing: **safe strum stagger**
- string attack gap: **0.038 beat**
- three-note total span: **0.076 beat**
- direction alternates low-to-high / high-to-low
- every original absolute note-off remains fixed
- treated LEAD remains unchanged

This result was blind and therefore not biased by knowing which version contained the strum.

Decision record:
`ROCK_V3_STRUM_HUMAN_LISTENING_DECISION_2026-11-07.json`

Promotion boundary:
This is a preferred **diagnostic-branch** Rock treatment only. It is not merged to main, not live, and does not authorize bass sustain or any other performance variable.

Next candidate, if work continues:
Inspect the already-disabled Rock BASS sustain candidate separately. Do not combine it with another new variable without its own safety proof and A/B.


## Rock V3 bass sustain safety gate launched

The user blind-preferred Rock guitar treatment remains fixed:
- HARMONY max ringing: 2.8 beats
- safe note-off-preserving strum attack
- treated LEAD unchanged

The next isolated candidate is:
`ROCK_BASS_SUSTAIN_V1_RESEARCH_DISABLED_DEFAULT`

Candidate parameters:
- next attack minimum: 0.80 beat
- next attack maximum: 2.50 beats
- spacing fraction: 0.78
- maximum sustain: 1.50 beats
- minimum extension: 0.14 beat
- default enabled: false
- listening approved: false

A symbolic-only safety analyzer was added:
`verify_rock_v3_bass_sustain_candidate_safety.py`

Safety rules:
- extend only; never shorten bass notes
- no changes outside the spacing window
- do not cross the next bass attack
- do not cross the current bar/harmony boundary
- require the 0.14-beat minimum extension
- preserve bass pitch/onset/velocity/event count
- preserve all guitar/lead/drum behavior

Workflow:
`Rock V3 Bass Sustain Candidate Safety`
Run:
`42394334886`

No audio, no bass enablement, no canonical/live mutation, and no reasoning-engine involvement.


## Rock V3 bass sustain — structural and resource gates passed; listening A/B launched

Current approved diagnostic guitar context remains fixed:
- HARMONY max ringing: 2.8 beats
- safe note-off-preserving strum attack
- treated LEAD unchanged

Bass candidate safety result:
- 147 total BASS events
- 58 duration changes
- extension distribution:
  - +0.225 beat: 18 events
  - +0.420 beat: 31 events
  - +0.615 beat: 9 events
- section changes:
  - INTRO_1: 2
  - VERSE_1: 14
  - CHORUS_1: 12
  - VERSE_2: 14
  - CHORUS_2: 12
  - OUTRO_1: 4
- no pitch/onset/velocity/event-count mutation
- no bar-boundary crossing

Important source-overlap distinction:
- the source bass writing already contains 33 pre-existing next-attack overlaps
- the bass sustain candidate introduces 0 new overlaps
- worsens 0 existing overlaps
- none of the 58 changed bass events overlap their next attack
- the earlier overbroad verifier incorrectly rejected any overlap in the finished score; the corrected verifier compares before vs after and rejects only candidate-introduced/worsened overlap

Corrected symbolic execution verification:
Run `42394761793` — PASS  
Artifact `13583281262`  
Digest `sha256:18d8e7604eff073c96d9892aa3959c4f9205f92209b56e7df6c32ef462e0919c`

Exact Growlybass resource proof:
Run `42394715088` — PASS  
Artifact `13583037189`  
Digest `sha256:002356c662b5c93fdb84b07c7e9ac40bcc0c9a886a5c4a385732af72793ea605`
- official v1.002 archive size: 167454256 bytes
- archive SHA256: `b92dca75494fa39d6e8d8b8addaabfe70c5aaa59b5f9a0f624be6de51a2374bc`
- target mapping: `growlybass_vicious.sfz`
- 86 sample references / 86 unique samples / 1 SFZ validated
- fallback: NO_SYNTHETIC_SUBSTITUTION
- production fidelity not certified

Strict listening gate:
`Rock V3 Bass Sustain Listening AB`
Run `42394879894`

Window:
- first 16 bars / 64 beats
- contains 23 changed bass notes
- covers intro, full first verse, and first part of Chorus 1

Listening outputs planned:
- current BASS only
- sustained BASS only
- current BASS + approved HARMONY strum + treated LEAD
- sustained BASS + exact same approved HARMONY strum + treated LEAD

No drums are included in this gate, so bass duration is the only new variable.
No live enablement, no main merge, no reasoning engine.


## Rock V3 bass sustain A/B completed and blinded

Listening workflow:
`Rock V3 Bass Sustain Listening AB`
Run `42394879894` — PASS

Artifact:
`13583535149`
Digest:
`sha256:7e3b01dc5330ccca45261428668251f2b9b62186281bb451eb61a7cb097c31c1`

16-bar listening window:
- 23 changed BASS events
- extension distribution: 7 × +0.225 beat, 13 × +0.420 beat, 3 × +0.615 beat
- about 4.33 seconds of aggregate added symbolic bass-note ring
- covers INTRO_1, VERSE_1, and part of CHORUS_1

Audio validation:
- exact Growlybass v1.002 mapping `growlybass_vicious.sfz`
- exact Shinyguitar mapping `Programs/composer_electric.sfz`
- current approved guitar treatment fixed: 2.8 HARMONY sustain + safe strum + treated LEAD
- drums omitted so bass duration is the only new variable
- no clipping: context peaks approximately -10.2 dBFS
- bass-only A/B difference ≈ -31.0 dB relative to current bass RMS
- context A/B difference ≈ -35.15 dB relative to current context RMS

Blind copies prepared byte-for-byte.
Mapping is recorded in:
`ROCK_V3_BASS_SUSTAIN_BLIND_LISTENING_MAP_2026-11-07.json`

Active gate:
User chooses Blind 1, Blind 2, no difference, or both wrong. Do not reveal mapping before that judgment. Do not add kick/drums or another performance variable before this decision.


## Rock V3 bass sustain — structural gate passed; current Vicious mapping rejected for sustain listening

Preferred guitar context remains fixed:
- HARMONY max ringing: 2.8 beats
- safe note-off-preserving strum
- treated LEAD unchanged

Bass symbolic candidate:
- source: `ROCK_BASS_SUSTAIN_V1_RESEARCH_DISABLED_DEFAULT`
- 147 bass events total
- 58 bass durations changed across full 40 bars
- extension range: +0.225 to +0.615 beat
- minimum remaining gap to next bass attack on changed events: 0.275 beat
- no candidate-introduced overlap
- no candidate-worsened overlap
- no changed-event overlap
- no bar-boundary crossing
- pitch/onset/velocity/event count unchanged
- all non-BASS roles unchanged

The later verifier failures were traced to non-chronological bass-event checking in the verifier, not the executor. The verifier was fixed to sort bass pairs by onset. Corrected workflow run `42394807720` passed.

Growlybass exact resource proof:
- release: v1.002
- official asset ID: 83416481
- archive size: 167454256 bytes
- archive SHA256: `b92dca75494fa39d6e8d8b8addaabfe70c5aaa59b5f9a0f624be6de51a2374bc`
- registry mapping: `growlybass_vicious.sfz`
- sample graph: 86 references / 86 unique samples / 1 SFZ
- no synthetic fallback

Current mapping note-length characterization:
- workflow run: `42394927340`
- artifact ID: `13583152249`
- classification: `NOTE_LENGTH_NONRESPONSIVE_OR_STACCATO`
- 0.25 s note active end: 0.34 s
- 2.00 s note active end: 0.48 s
- active-end delta: only 0.14 s
- therefore note-length response for current mapping: false

The technically successful bass A/B run `42394879894` is rejected as authority for bass-sustain musical judgment because the exact Vicious mapping does not materially express note-length differences.

Decision record:
`GROWLYBASS_VICIOUS_SUSTAIN_GATE_DECISION_2026-11-07.json`

Active gate:
Research-only characterization of `growlybass_clean.sfz` and `growlybass_dirty.sfz` from the same pinned v1.002 archive. The target registry remains unchanged. Only if a mapping proves note-length responsive should a new musical bass-sustain A/B be rendered.


## Growlybass sustain-capable mapping research

Current registry mapping remains:
- `growlybass_vicious.sfz`
- note-length response: false
- active-end delta for 0.25 s vs 2.00 s note: 0.14 s
- therefore not valid authority for bass-sustain listening

Sustain-oriented mappings from the same exact pinned Growlybass v1.002 archive were characterized without changing the registry.

Workflow:
`Growlybass Sustain Mapping Characterization`
Run:
`42395101164`
Artifact:
`13582853415`
Digest:
`sha256:369693f5f940620acb05b58f11c6f127c41e86a34e90c0ff80bfd2298a2c3e57`

Results:

`growlybass_clean.sfz`
- sample graph: 240 references / 240 unique samples
- note-length responsive: true
- 0.25 s note active end vs 2.00 s note active end delta: 1.72 s
- releases after long note: true
- classification: SUSTAIN_CAPABLE_NOTE_LENGTH_RESPONSIVE

`growlybass_dirty.sfz`
- sample graph: 310 references / 310 unique samples
- note-length responsive: true
- active-end delta: 1.68 s
- releases after long note: true
- classification: SUSTAIN_CAPABLE_NOTE_LENGTH_RESPONSIVE

Research mapping selected:
`growlybass_clean.sfz`

Reason:
- it is sustain-capable on the exact pinned v1.002 archive
- the target registry already names it as `production_preferred_mapping`
- choosing Clean avoids adding Dirty's release-sample behavior as another variable

Decision record:
`GROWLYBASS_SUSTAIN_RESEARCH_MAPPING_DECISION_2026-11-07.json`

Registry is still unchanged.

A new valid 16-bar bass sustain A/B has been launched with Clean held fixed in both versions and only bass duration changing:
Workflow: `Rock V3 Bass Sustain Clean Listening AB`
Run: `42395303554`

Approved guitar context remains fixed in both A/B conditions:
- HARMONY max ringing 2.8 beats
- safe note-off-preserving strum
- treated LEAD unchanged


## Rock bass — user clarified upbeat/pitch behavior

User listening diagnosis:
- the bass downbeat/attack is good;
- the bass tail resonates too far and can read as an upbeat;
- the pitch also changes on the upbeat;
- if bass sustain is allowed across that subdivision, it should remain the same tone.

Symbolic/source findings:
- 29 half-beat upbeat bass events in the 40-bar line;
- 26 already retain the preceding bass pitch;
- 3 half-beat upbeat pickups change pitch;
- source-pattern audit also found broader overlapping different-pitch bass attacks before any sustain treatment is applied.

Measured Vicious decay evidence at 123 BPM:
- half-beat upbeat = 0.243902 s after attack;
- 0.20-beat MIDI gate -> measured active end ~0.22 s / 0.451 beat;
- 0.25-beat gate -> active end ~0.24 s;
- 0.30-beat gate crosses the upbeat;
- decay-grid artifact ID: 13583455938.

Two repair candidates exist:
1. **Narrow pitch-coherence repair** — preferred first test:
   - never extends bass;
   - before a different-pitch attack with enough spacing, shorten prior note to leave 0.25 beat release gap;
   - for ultra-close different-pitch attacks <=0.30 beat, lock the later attack to the prior pitch;
   - preserves same-pitch continuation;
   - verified full40: 36 duration shortenings, 22 pitch locks, zero remaining different-pitch coherence violations.
2. **Blanket downbeat damping fallback**:
   - 0.20-beat gate on 146/147 bass notes;
   - 3 half-beat pitch locks;
   - final sustained arrival exempt;
   - structurally verified but intentionally held as fallback because it is much more invasive.

Current active gate:
`Rock V3 Bass Pitch Coherence Listening AB`
Run: `42395776007`

A/B uses current Growlybass Vicious mapping and approved guitar context:
- HARMONY max ringing 2.8 beats
- safe strum
- treated LEAD
- no drums
- A = current bass
- B = narrow pitch-coherence repair

Do not promote the blanket 0.20-beat damping candidate unless the narrower repair still sounds too resonant.


## Rock bass diagnosis revised from sustain to downbeat coherence

Human listening clarified the bass problem:
- the downbeat attack itself is good;
- bass resonance lasts too long and begins to read like an upbeat;
- pitch also changes on some upbeats;
- if bass carries into an upbeat, the sustained tone should remain the same pitch.

The prior bass sustain A/B is therefore rejected as the wrong repair direction.

Measured exact-resource evidence on Growlybass v1.002 / `growlybass_vicious.sfz`:
- workflow `Growlybass Vicious Decay Grid`
- run `42395436023`
- artifact `13583455938`
- at 123 BPM, half-beat upbeat occurs at 0.243902 s
- 0.20-beat MIDI gate: acoustic active end ≈ 0.22 s / 0.451 beat, clears upbeat
- 0.25-beat gate: active end ≈ 0.24 s, does not preserve desired pre-upbeat margin
- 0.30-beat and longer gates cross the upbeat
- selected measured maximum gate: **0.20 beat**

Upbeat pitch analysis:
- run `42395484055`
- artifact `13583207989`
- 147 bass events total
- 29 half-beat upbeat bass attacks
- 26 already same pitch as preceding same-bar bass tone
- 3 change pitch

Verified direct candidate:
`current_master_forward/rock_v3_bass_downbeat_coherence_candidate.py`
- cap all bass durations to 0.20 beat
- preserve all onsets/velocities/event count
- normalize only the 3 different-pitch half-beat upbeats to the preceding same-bar bass pitch
- all 29 half-beat upbeats become same-tone
- approved guitar context preserved: 2.8 HARMONY sustain + safe strum + treated LEAD
- no reasoning engine
- no live/main promotion

Symbolic verification:
`Rock V3 Bass Downbeat Coherence Verify`
run `42395657057` — PASS
artifact `13582939126`
digest `sha256:52f4412e36692af65b9db44f0b4440dfffa0c5446d8d007e512195459f44689a`

Listening gate launched:
`Rock V3 Bass Downbeat Coherence Listening AB`
run `42395850331`

A = current bass on current Vicious mapping.
B = measured 0.20-beat damping + same-tone half-beat upbeat guard on the exact same mapping.
Both use identical approved guitars. No drums in this gate.


## Rock bass pitch-coherence blind listening gate completed

Workflow:
`Rock V3 Bass Pitch Coherence Listening AB`
Run:
`42395776007`
Artifact:
`13582444349`
Digest:
`sha256:bb34eba27d3e4876c9ba0fb517ad1587ca393a22358bd9f72d98bb5785d1b0e5`

16-bar verified A/B:
- Growlybass Vicious mapping fixed in both;
- approved HARMONY 2.8 sustain fixed;
- safe strum fixed;
- treated LEAD fixed;
- no drums;
- A = current bass;
- B = narrow pitch-coherence repair.

Repair changes in 16-bar window:
- 56 bass events total
- 17 prior-note duration shortenings
- 5 ultra-close pitch locks to the prior tone
- 0 duration extensions
- 0 onset changes
- 0 velocity changes
- guitars unchanged

Full-40 symbolic verifier previously passed:
- 36 duration shortenings
- 22 pitch locks
- zero remaining different-pitch coherence violations

Blind mapping is recorded in:
`ROCK_V3_BASS_PITCH_COHERENCE_BLIND_MAP_2026-11-07.json`

Blind 1 = repaired candidate.
Blind 2 = current bass control.

The blanket 0.20-beat damping candidate remains fallback only because it shortens 146/147 bass notes and is substantially more invasive.

Active gate:
User blind judgment on the pitch-coherence A/B. Do not reveal mapping until user chooses Blind 1, Blind 2, no difference, or both wrong.


## Rock bass downbeat-coherence A/B completed and blinded

Human diagnosis:
- downbeat attack good
- bass resonance carries too long and reads as an upbeat
- pitch changes on some upbeats
- sustained bass should remain the same tone

Measured resource basis:
- Growlybass Vicious decay-grid run `42395436023`
- artifact `13583455938`
- selected gate: 0.20 beat
- measured active end: ~0.22 s / 0.451 beat
- half-beat upbeat: ~0.2439 s
- 0.20 beat is the longest tested gate retaining ~20 ms pre-upbeat margin

Upbeat pitch basis:
- run `42395484055`
- artifact `13583207989`
- 29 half-beat upbeat bass attacks
- 26 already same pitch
- 3 different pitch

Verified coherence candidate:
`current_master_forward/rock_v3_bass_downbeat_coherence_candidate.py`
- max bass duration 0.20 beat
- all 29 half-beat upbeats same tone
- only 3 bass pitches normalized
- no onset/velocity/event-count/non-bass mutation
- approved guitars preserved

Symbolic verification:
run `42395657057` — PASS
artifact `13582939126`
digest `sha256:52f4412e36692af65b9db44f0b4440dfffa0c5446d8d007e512195459f44689a`

Listening workflow:
`Rock V3 Bass Downbeat Coherence Listening AB`
run `42395850331` — PASS
artifact `13583163853`
digest `sha256:960bb39fa270a8b9beb151feedf4d42628387a83287d552a35dea2d4dcd90e0e`

16-bar render:
- 56 bass events
- all 56 duration-gated in candidate
- 3 pitch changes normalized
- exact same Growlybass Vicious mapping in A and B
- exact same approved HARMONY strum + treated LEAD
- no drums
- no clipping

Blind map:
`ROCK_V3_BASS_DOWNBEAT_COHERENCE_BLIND_MAP_2026-11-07.json`

Active gate:
User chooses Blind 1, Blind 2, no difference, or both wrong.
Do not reveal mapping before judgment.
Do not enable candidate live or merge to main before approval.


## Rock bass rule widened from half-beat-only to all off-beat subdivisions

New human listening feedback:
The bass still changed pitch on an upbeat after the half-beat-only repair.

Audit:
`Rock V3 Bass Offbeat Pitch Audit`
run `42396632709` — PASS
artifact `13583309618`
digest `sha256:ae84d055d367f0deb46602b1cf41d3acf17dff9d402a4c4ace6f917cd9a7fc31`

16-bar audit:
- 56 bass events
- 29 off-beat/subdivision bass attacks
- current source: 12 different-pitch off-beats
- previous half-beat-only candidate: 9 different-pitch off-beats still remained
- missed positions included quarter/three-quarter subdivisions such as local beat 2.25, 3.25, and 3.75

Corrected musical rule:
- pitch changes are allowed on strong integer beats
- every non-integer-beat bass attack must keep the immediately preceding bass pitch
- 0.20-beat bass damping remains in place

New candidate:
`current_master_forward/rock_v3_bass_offbeat_coherence_candidate.py`

Full 40-bar verification:
`Rock V3 Bass Offbeat Coherence Verify`
run `42396740749` — PASS
artifact `13583643022`
digest `sha256:0c15286293bb6fb368b0743f02fada791cd7182ff286e7a4ade7b3f65333472b`

Full-form result:
- 147 bass events
- 77 off-beat bass events
- 40 off-beat pitch changes normalized
- 0 different-pitch off-beats remain
- 63 strong-beat pitch changes remain allowed
- all 147 bass durations capped at 0.20 beat
- no onset/velocity/event-count/non-bass mutation
- approved guitar context preserved
- no reasoning engine, no main/live promotion

Listening workflow:
`Rock V3 Bass Offbeat Coherence Listening AB`
run `42396840622`
- first 16 bars
- expected 56 duration changes
- actual 14 pitch corrections in the 16-bar rendered window
- same Growlybass Vicious mapping in A/B
- same approved HARMONY strum + treated LEAD


## Rock bass all-offbeat coherence listening render completed

Workflow:
`Rock V3 Bass Offbeat Coherence Listening AB`
successful run:
`42397167804`

Artifact:
`13583961867`
Digest:
`sha256:c82f7a7ad8989a41a8159b0bab2c914a60048c78719f9d3a1d0e6dff42c4da6e`

Verified 16-bar render:
- 56 bass events
- all 56 bass durations use the measured 0.20-beat damping gate
- 14 bass pitches corrected in the rendered window
- 0 different-pitch offbeats remain after the candidate
- bass onset unchanged
- bass velocity unchanged
- event count unchanged
- exact same Growlybass Vicious mapping in A and B
- exact same approved HARMONY 2.8 + safe strum
- exact same treated LEAD
- no drums
- no reasoning engine
- no canonical/main/live promotion

Important count clarification:
The initial static audit found 12 source off-beat pitch changes in the first 16 bars. The sequential all-offbeat coherence rule produces 14 actual pitch corrections because once an early off-beat is normalized to the established strong-beat tone, later off-beats in the same run must also remain on that tone. This is intended behavior, not an error.

Full-form symbolic verifier remains:
- 77 off-beat bass events
- 40 full-form off-beat pitch normalizations
- 0 different-pitch offbeats remain
- strong-beat pitch changes remain allowed

Active gate:
Human listening of clearly labeled Current Bass vs Corrected Bass.


## Rock bass-only three-way sustain/body test completed

Workflow:
`Rock V3 Bass Three Way Listening`
run `42398125730` — PASS

Artifact:
`13584073354`
Digest:
`sha256:686e8b1697f6b435deb186ff57357386fb3862ca7c36dad233c7b1e204fe5382`

Human baseline entering this test:
- corrected bass-only is preferred
- unwanted offbeat pitch behavior is gone
- corrected bass-only is too dry / lacks sustain

Three bass-only conditions:
A. `A_ACCEPTED_VICIOUS_SHORT`
- human-preferred corrected bass baseline
- growlybass_vicious.sfz
- 56 events in first 16 bars
- 0.20-beat max gate
- offbeat re-attacks remain, but all are pitch-coherent
- 0 different-pitch offbeats

B. `B_CLEAN_SHORT_CONTROL`
- exact same symbolic bass performance as A
- growlybass_clean.sfz
- 56 events
- 0.20-beat max gate
- isolates mapping/timbre only

C. `C_CLEAN_HELD_TONE`
- sustain-capable growlybass_clean.sfz
- 27 strong-beat bass events in first 16 bars
- all offbeat bass re-attacks removed
- strong-beat notes held toward next strong beat
- maximum hold 1.50 beats
- 0.20-beat release gap
- 0 different-pitch offbeats

No guitars, no drums, no reasoning engine, no canonical/main/live promotion.

Active gate:
Human bass-only listening among A, B, and C to determine whether body/sustain can be added without reintroducing the unwanted upbeat behavior.


## Rock bass C preferred; crisp-downbeat hybrid test completed

Human listening result:
- C held-tone bass is preferred for what the bass should be doing.
- C has the desired sustain/body.
- remaining issue: C does not have a crisp enough downbeat.
- unwanted upbeat behavior remains absent.

Decision:
Preserve C's held-tone writing exactly:
- strong-beat bass attacks only
- no offbeat re-attacks
- no different-pitch offbeats
- Clean sustain-capable mapping

Do not reopen pitch/rhythm behavior.

New attack-layer test:
Workflow:
`Rock V3 Bass Attack Hybrid Listening`
run `42398615404` — PASS

Artifact:
`13584112748`
Digest:
`sha256:707295f6ac258295584469c78526fc7a5f321a01a4e4d5c7a5d995a477d917a3`

Conditions:
- C = Clean held-tone baseline, unchanged
- D = C + same-pitch/same-onset Vicious 0.20-beat transient at -9 dB
- E = C + same-pitch/same-onset Vicious 0.20-beat transient at -6 dB

Invariants:
- 27 strong-beat events in first 16 bars
- attack layer uses the exact same 27 onsets/pitches/velocities
- no offbeat events added
- no rhythmic/pitch changes
- no guitars/drums
- no reasoning engine
- no main/live promotion

Active gate:
Human listening chooses C, D, E, or none.


## Rock bass hybrid D selected by human listening

Human judgment:
**D preferred**

Preferred Rock bass diagnostic treatment:
- symbolic base: held-tone bass candidate
- strong-beat attacks only
- no offbeat bass re-attacks
- 0 different-pitch offbeats
- sustain/body mapping: `growlybass_clean.sfz`
- crisp attack mapping: `growlybass_vicious.sfz`
- attack layer gain: **-9 dB**
- attack gate: **0.20 beat**
- attack layer uses exact same onset/pitch/velocity as held note
- no extra rhythmic event is created

Rejected alternatives:
- C: held body alone; downbeat too soft
- E: stronger Vicious transient at -6 dB; not preferred

Decision record:
`ROCK_V3_BASS_ATTACK_HYBRID_HUMAN_DECISION_2026-11-07.json`

This is now the preferred diagnostic Rock bass treatment.
No main/live promotion yet. Reasoning engine remains excluded.

Next clean gate:
Integrate preferred bass D with the already-approved Rock guitar treatment (2.8 HARMONY sustain + safe strum + treated LEAD), with no additional performance variables.
