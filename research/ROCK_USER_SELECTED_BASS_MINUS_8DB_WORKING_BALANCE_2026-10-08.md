# Rock interpreter — user listening selection: stronger bass reduction

**Date:** October 8, 2026 (America/Chicago)  
**Branch:** `rock-interpreter-bass-separation-20261008`  
**Status:** USER-PREFERRED WORKING AUDITION / NOT YET A LIVE DEPLOYMENT

## User preference
After hearing the two controlled mixes of the *same exact preferred 16-bar Rock interpreter recording*, the user said:

> "I think I like the stronger reduction"

This refers specifically to the **bass guitar reduced by 8 dB** compared with the original interpreter audition, rather than the -4 dB comparison. Treat -8 dB as the preferred provisional **Rock interpreter working mix**. "I think" is a preference, **not a final approval for permanent deployment**.

## Precisely selected artifact
Source: `research/rock_mma_bass_only_balance_audition_r1.py`  
Candidate: `Rock_Interpreter_Bass_Reduced_8dB.wav`  
Confirmed SHA-256: `7cbc7f8eef52dbc48b3e7ba15612d46c62f2e67bc6f719d059c561fe46950393`  
User-facing MP3: `Rock_Interpreter_Bass_Separation_2026-10-08_2113_CDT/03_Rock_Bass_Reduced_8dB.mp3`
Original like-for-like master (unchanged): `MMA_Rock_16Bar_Interpreted_Band_Fill_3D.wav`  
Original SHA-256: `e2b8041276fe1253c7ed9a2e475562bd31a3e81c713e7161363b4a6e1964c187`  
Verified GitHub Actions run: https://github.com/mreeves1257-glitch/AI-Composition-Deployment/actions/runs/37873197996

This candidate was built from *the exact original checksum-pinned external MMA MIDI* recovered from the positive-listening experiment, so the full 420 score note events and **all eight original real recorded source stems** remained unchanged. Only electric bass guitar **gain metadata** was adjusted by -8 dB in the copied external mixing job. Kick and real recorded sub-kick, snare, hi-hat, toms, crash and rhythm guitar retained original role levels/notes/sources. The original 3D mixer peak-normalizes the finished stereo, so absolute master loudness might differ even when other source ratios are not adjusted. No mixer code edited.

## Next musical issue, separate from bass balance
User previously heard a synthetic/keyboard-like accompaniment in the 16-bar demonstration. Source inspection confirmed **no keyboard or piano** was routed; this was the real Karoryfer Shinyguitar rhythm-chord part with MIDI chord-block behavior. The isolated demonstration still lacks a full independent lead guitar. Investigate realistic guitar playing techniques, chord voicing/strum timing and appropriate lead/rhythm separation in a *separate* research experiment; never bury the improved groove or casually reset the -8 dB working balance.

## Protection
All earlier mixes remain unchanged as auditable references. Preserve the official original MMA license boundary, the original 55 genre stage-3→4 interpreter filings (reference-only), the seven-stage genre order, all recorded Karoryfer assets, independent SFZ stems, live Composer, Plug and Control Panel. **No deployment or global cross-genre mixing change was authorized by this subjective choice.**
