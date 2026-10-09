# Rock Interpreter — Bass-Only Mixing Proof PASSED

**Hard checkpoint:** October 8, 2026, 9:13 PM CDT (America/Chicago)
**Status:** Successful stereo audio A/B research; no production deployment.
**Branch:** `rock-interpreter-bass-separation-20261008`
**Successful source/render workflow:** https://github.com/mreeves1257-glitch/AI-Composition-Deployment/actions/runs/37873197996

## User's immediate observations to preserve
- "The rhythm was a lot, lot better and ... the sound was a lot better. But it's still not where the quality that it should be."
- "I don't know if there was a piano or a keyboard that accompanied that particular. It just sounds real synthetic."
- "The bass guitar overwhelmed everything else."
- Previously: "That was so much better ... sounded more like it, but ... if it had that kick drum, it would have been better."

## Verified instrument identity
There was NO keyboard or piano note track in the 16-bar MMA Rock audio. The externally authored `Chord-Clean` accompaniment was routed to `HARMONY`, an actual recorded Karoryfer Shinyguitar electric guitar, 225 MIDI notes. BASS uses Karoryfer Growlybass (56 notes); the KICK uses Karoryfer Big Rusty (32 attacks) and SUBKICK is a separate recorded-kick-derived low frequency stem. The 16-bar proof has NO lead guitar yet. The keyboard-like quality may be overly simultaneous/quantized chord attacks rather than a synth substitution, but its specific perceptual cause has not been established.

## False start and correction; why it matters
First automated rebuild generated a NEW random MMA accompaniment arrangement. The reference mixed WAV SHA and all new MIDI hashes differed, so the **fail-closed checksum correctly blocked bass-only A/B**. No faulty work was promoted.

Corrected method: retrieve the preserved original `MMA_Rock_16Bar_Two_Sections.mid` from the successful user's preferred 16-bar artifact in run 37870594722; verify its SHA256:
`7253c3715299018dc540bdbaf29883bfbd7615ab7e5d943bde45f8d1b19555fe`.
The independent bridge `research/mma_rock_band_handoff_16bar_r1.py` takes this immutable original MIDI when `AI_COMP_MMA_PRESERVED_MIDI` points to it, and does not call MMA to regenerate the score.

**The corrected run reconstructed the exact recorded user-liked original stereo WAV** with matching SHA256:
`e2b8041276fe1253c7ed9a2e475562bd31a3e81c713e7161363b4a6e1964c187`.
Full musical note count **420**, eight exact recorded stems. This establishes that the comparison really holds all other notes and source recordings constant.

## Complete successful experimental A/B
Research-only script: `research/rock_mma_bass_only_balance_audition_r1.py`.
- Candidate A `Rock_Interpreter_Bass_Reduced_4dB.wav`: Reduce ONLY Growlybass mix gain by 4 dB; SHA256 `02b0acf0f3ebc86c524f6f9defe7ab5b098f6a2c168b210364d4467bc8a1f5c4`.
- Candidate B `Rock_Interpreter_Bass_Reduced_8dB.wav`: Reduce ONLY Growlybass gain by 8 dB; SHA256 `7cbc7f8eef52dbc48b3e7ba15612d46c62f2e67bc6f719d059c561fe46950393`.
- Stereo both 44.1 kHz 16-bit two-channel, 30.46458 seconds.
- Same 420 note events, exactly the same eight original recorded audio stems; KICK and SUBKICK gains and source WAVs unchanged; all other musical instrument gain/pan metadata identical; original independent 3D mixer source/algorithm unchanged. Note that peak-normalized master amplitude can change as a consequence of less bass gain, but relative gains of other tracks are not touched.
- Source libraries and actual live Composer, Plug, Control Panel, per-genre seven-stage wiring all unchanged.

## Research artifacts
Workflow action artifact `rock-interpreter-bass-only-reduced-4-and-8db-recorded-20261008`, ID 11591301258, provides original and two alternatives plus JSON provenance. User also gets short MP3 copies and dated hard-save ZIP.

## Next authorized direction
**Ask the user's ears:** Does A or B make the drummer/kick audible while preserving the engaging performance? Do not choose automatically from signal measurements. Then a SEPARATE Rock rhythm-guitar performance-language audition can test realistic strummed attacks and playable chord voicings, and later restore independent lead line. Do not edit both bass balance and guitar performance simultaneously. Rock remains the sole executable experiment; all other 55 genre interpreter handoffs are filed but inactive.
