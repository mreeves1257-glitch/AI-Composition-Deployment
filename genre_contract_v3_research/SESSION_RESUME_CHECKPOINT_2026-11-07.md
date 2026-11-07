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
