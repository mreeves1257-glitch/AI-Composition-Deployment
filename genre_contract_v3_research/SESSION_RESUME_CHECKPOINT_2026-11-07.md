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
