# ROCK SOURCE MUSIC — REAL RECORDED STEMS + PRESERVED STANDALONE 3D: VERIFIED

**Date:** October 9, 2026
**Development branch:** `rock-original-five-stem-sfz-proof-20261009`
**Successful isolated GitHub Actions run:** https://github.com/mreeves1257-glitch/AI-Composition-Deployment/actions/runs/37978134864
**Downloadable Research Artifact:** https://github.com/mreeves1257-glitch/AI-Composition-Deployment/actions/runs/37978134864/artifacts/11639119780
**Protected original project hard copy:** `hard-copy-ai-composer-2026-10-09-1128-CDT`, commit `352e2a4d9d13bbe9f8a76bd336488bae14e042ee`, unchanged.
**Control:** Not a new master/hard-copy snapshot. Research source checkpoint; any future complete hard copy must additionally supply a personally downloadable ZIP to the user.

## New *real* proof, beyond the previous instrument-identity and symbolic-note checks

The original 55-genre authored **ROCK** seven-bar seed, 102 original events (21 bass, 18 rhythm guitar, 12 kick, 15 snare, 36 hi-hat), was passed through the actual preserved Composer InstrumentProgram, TargetProgram, PerformanceExecutor and MIDI Output Core. The original `build_current_composer.sh` installed the existing approved sampled libraries and SFZ renderer in a **separate GitHub Actions runner**, not on Render.

The existing `sfz_renderer_adapter.preflight` verified real installed SFZ programs and their recursively referenced recordings. Actual `sfizz_render` generated five individually isolated, measurable non-silent **recorded-source WAV stems**:

| Role | Original recorded bank / program | SFZ references (unique) | Notes | WAV duration | Unmixed WAV peak |
|---|---|---:|---:|---:|---:|
| BASS | Karoryfer Growlybass / `growlybass_clean.sfz` | 240 (240) | 21 | 12.40 s | −13.3 dBFS |
| HARMONY | Karoryfer Shinyguitar / `Programs/composer-electric.sfz` | 3399 (423) | 18 | 12.19 s | −12.3 dBFS |
| KICK | Karoryfer Big Rusty Drums / `Programs/composer-kick-lite.sfz` | 16 (16) | 12 | 13.44 s | −24.4 dBFS |
| SNARE | Karoryfer Big Rusty Drums / `Programs/composer-snare-lite.sfz` | 16 (16) | 15 | 13.68 s | −30.5 dBFS |
| HAT | Karoryfer Big Rusty Drums / `Programs/composer-hihat-lite.sfz` | 32 (32) | 36 | 12.89 s | −31.2 dBFS |

Unmixed peaks were measured directly on the real WAVs. These differences motivate drum-level investigation, but note attack, density, envelope and final mixer gain mean simple per-track peak/RMS numbers are **not** a listening verdict.

**Actual standalone Stage 7 connection also passed:** `research/run_preserved_standalone_3d_mixer_rock_partial_20261009.py` confirmed the five stems' recorded WAV SHA256 values and supplied actual original InstrumentProgram/TargetProgram/PerformanceExecutor runtime outputs to a *separate process* running the untouched `composer/runtime/standalone_3d_mixer.py`. The original `spatial_master_handoff.finalize_real_stems` created scene/object-master metadata and a 13.677-second, 44.1 kHz, stereo diagnostic derivative. WAV SHA256: `9496225588c812c65158101389cd071679b419f0f372928ea18c018e439d87fb`. Left peak −1.0 dBFS, right peak −1.53 dBFS; about −23 dBFS summed-channel RMS. This was not a replacement final mix in the user's live pipeline.

**Archive:** GitHub Actions artifact `ROCK_5_Real_Recorded_Source_Stems_2026-10-09` includes the 5 separate MIDI/WAV files, complete actual-sample validation manifest, and independently mixed *partial-development* listening diagnostic.

## What remains blocked or missing
1. New Rock seven-bar sketch lacks original Rock arrangement's **LEAD, TOMS, CRASH and RIDE** parts; a finished/full-length Rock performance is still missing. Do not count a separately derived subkick as a missing new recording instrument.
2. No qualified user audition yet. Bass sustain/release, convincing lead vibrato, rhythmic dynamics, drum depth, human musical phrasing and arrangement remain subjective and technical review tasks.
3. No production switching of `theory['events']` from the legacy original score to new `candidate_stage4_events`. Research score is explicit nonproduction and stays so.
4. No Rock source test through live Plug, phone Control Panel, or external Render production. Neither production nor original protected hard-copy branch was changed.
5. Remaining 55-genre mapping: 66 physical catalog name mismatches (overlaps the 130 unmapped SFZ source role references). These are other-genre integration needs, not failures of this five-source Rock audio test.

## Immediate controlled next step
First inspect the partial Rock stereo diagnostic and the five stems; isolate which differences come from program levels and which from musical arrangement and phrasing. Then give Rock its missing lead/drum-fill parts with exact original recorded SFZ resources, validate their event identities/ranges, and repeat the isolated seven-stage workflow before any live activation. No new interpreter, stage 8, generic timbres or substituted/mixed instrument recordings.
