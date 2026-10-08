# FULL Rock ensemble, real recorded instruments + 3D A/B checkpoint

**Checkpoint:** 2026-10-08 18:59 CDT (America/Chicago)  
**GitHub Actions:** https://github.com/mreeves1257-glitch/AI-Composition-Deployment/actions/runs/37862027331 (SUCCESS)  
**Dated user audio archive:** `AI_Composer_Rock_Full_Band_3D_AB_2026-10-08_1859_CDT.zip` (saved as a separate conversation artifact; not in repository).  
**Status:** Isolated research only, NOT deployed.

## What actually ran
- Built the unchanged Composer and its real SFZ sample banks in a GitHub Actions runner.
- Original generated Rock score normal mode seed=0 at 145 BPM; 3,065 whole-score events; first 8 bars used for controlled A/B.
- 190 events from 7 source tracks: BASS, CRASH, HARMONY, HAT, KICK, LEAD, SNARE, plus existing recorded lowpassed SUBKICK stem. TOMS/RIDE not present in this particular excerpt, which says nothing about other bars.
- All **six non-bass** source tracks (MIDI + WAV) kept identical. Onsets, pitches, velocities, banks, resources, mixed source levels, spatial configuration unchanged. Candidate changed exactly 16 bass note durations (0.48 or 0.62 to 1.365–1.5 beats) using `research/rock_bass_full_band_ab_v1.py`.
- Preserved separate original 3D scene/object-master compiler and final stereo derivative for both variants. Both WAV files are 44.1kHz, 16-bit, stereo and 22.221s long, including near-silent tails. User-facing separately marked 14.5s listening copies trim those tails, never overwriting the mixer derivatives.
- First-8-second stereo RMS: original **0.077234097**, candidate **0.077511465** (~+0.031dB). MIDI onset attacks remain essentially unchanged. Musical preference/human realism is NOT proven by this test.
- Test job **success**; full instrumental output artifact ID 11586800548.

## Interpretation
An early MIDI note-off was confirmed to curtail actual recorded bass sustain in a prior isolated A/B; the longer bass now also produces a measurable difference *inside* a seven-instrument 3D mix. The candidate is not automatically artistically better and must not be blindly enabled. The source of other audible choppiness elsewhere in the score is not established.

## Safe continuation
Review the saved full-band A/B and distinguish musical flow from volume. If warranted, implement a Rock BASS-only, configurable and rollback-safe duration policy at the original composition-to-performance boundary, with original explicit short/mute articulations respected and the same source bank. Test one complete Rock song and playback handoff before activation. Preserve all existing genre structures and raw recordings. No modification of control panel, plug, stand-alone 3D mixer, or the rest of the composer until specifically required by verified evidence.
