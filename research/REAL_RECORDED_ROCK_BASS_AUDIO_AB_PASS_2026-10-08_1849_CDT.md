# Real Recorded Rock Bass Note-Off A/B: PASS
**Checkpoint:** 2026-10-08 18:49 CDT (America/Chicago)  
**GitHub Actions run:** https://github.com/mreeves1257-glitch/AI-Composition-Deployment/actions/runs/37861189599  
**Status:** source-audio behavior measured; musical quality unapproved. Live services unmodified.

The preserved Composer build ran in an isolated runner, composed a normal Rock song at 145 BPM (seed 0), producing **3,065 musical events** including **254 BASS** events. Eight real generated bars (16 bass notes) were extracted and rendered twice using the **same recorded Karoryfer Growlybass clean SFZ**, sfizz renderer and velocities/onsets/pitches.

Only note-off timing changed:
- Original rendered MIDI: 16 note-on commands, 16 note-off commands. Typical note durations **0.48–0.62 beats**.
- Candidate: identical MIDI note-ons, all 16 note-offs later. Durations **1.365–1.5 beats** in this passage.
- First original note-off: tick 298 at 480 PPQ. Candidate: tick 720.
- Actual WAV baseline: **−41.957 dBFS RMS**; candidate: **−39.893 dBFS RMS**.
- Audio delta RMS between aligned signals: **0.006004887**; clearly different actual recorded-source WAVs.
- First 0.02–0.15 s of the audio recordings: **sample-identical PCM** (RMS 0.011155 each, difference exactly zero).
- First 0.31–0.50 s after starting: original RMS **0.0003937**; candidate **0.0056547**; difference emerges after original note-off.
- Both SFZ audio renders and the full isolated workflow completed successfully. WAV and MIDI evidence were saved in GitHub Actions artifact `rock-bass-real-sfz-original-vs-candidate-20261008` (artifact ID 11586013603).

**Supported interpretation:** Early MIDI note-offs are causally contributing to bass notes stopping very quickly. This is a measurable playback-control issue, not a need for a replacement sound library or a master-volume adjustment. A longer hold changes real sampled bass audio. The candidate is merely one experiment, **not a universally approved articulation**; full musical realism and full-song integration are not yet shown.

**Preservation:** no deployed Composer, plug, control panel, genre links, original sound banks, or standalone 3D mixer were changed. Do not connect these research controls by default. Other pre-existing percussion performance research is cross-referenced in this branch; don't rebuild it.

**Audio hard copy:** `AI_Composer_Performance_Real_Bass_AB_2026-10-08_1849_CDT.zip` available in the October 8 conversation; includes original + candidate WAV, mobile MP3, MIDI, JSON data, dated findings, and the prior 22-test interpreter checkpoint.

**Next bounded step:** Test a candidate bass-duration policy that respects explicit short/mute notes, prevents unwanted overlap, checks source sample duration and release characteristics, and preserves real phrase breaks; evaluate against the full ensemble instead of assuming long=human.
