# Listening guidance + Story V2 checkpoint — 2026-10-08

## User listening feedback: preferred instrument audibility

The user listened to the separate full Rock Melody R1 drum-collision-cleaned stereo audition and reported the result "**sounds a lot better**" and "**I definitely can hear all the instruments on it this time**." They also said "**it's still pretty slow**." This is a listening observation about effective groove/pace despite 145 score BPM. Preserve source recordings, instrument separation, current 3D mixer, and positive arrangement balance.

## Story V2 experiment status

GitHub Actions run https://github.com/mreeves1257-glitch/AI-Composition-Deployment/actions/runs/37866888426: SUCCESS.
Both full 127-bar (~211.766s) 145 BPM songs rendered with ten genuine source/derived 3D sound objects and unmodified recorded instruments.
- Existing Melody R1: 2,981 note events, 198 lead notes, 16 distinct lead pitch sequences.
- Story V2: 2,949 note events, 166 lead notes, 18 distinct lead pitch sequences.
- All **non-lead note events identical**, even the original duplicate drum hits; lead entrances/rests unchanged; source samples and mixer unchanged. Artistic improvement NOT proven by score statistics. V2 is behind explicit flag `AI_COMP_ROCK_STORY_V2=1` and requires existing R1 flag `AI_COMP_ROCK_MELODY_V1=1`.
- Complete original and V2 WAVs and exact source comparison: GitHub Actions artifact #11588836656 (`rock-musical-story-v2-full-recorded-audio-20261008`).
- Independently exported V2 listening MP3 from this complete WAV is supplied in the Oct 8, 2026 conversation; not deployed.

## Essential separation of concerns

The user liked the **drum-cleaned version**, whereas the Story V2 A/B intentionally left the original doubled drums unchanged, so its standalone MP3 is NOT directly comparable to that preferred cleaner groove. Do not override the working cleaned drum candidate with Story V2.

**Next musical research**, once desired: use the liked Melody R1 + single-hit drum version as protected baseline; separately test an unchanged-tempo (145 BPM) groove-propulsion change in drum/hi-hat/bass/rhythm-guitar interplay. Only after this audition, explore combination with song-scale motifs if artistically preferable. Keep everything feature-gated, reversible and research-only; do not touch deployed plug, control panel, mixer or original recorded SFZ samples.
