# Rock Interpreter — User-Liked Performance and Kick-Only Restoration

**Hard checkpoint:** 2026-10-08 20:50 CDT (America/Chicago)
**Study branch:** `rock-kick-presence-research-20261008`
**Verified real recorded-instrument 3D audition run:** https://github.com/mreeves1257-glitch/AI-Composition-Deployment/actions/runs/37871425381
**Complete source/score verified original Rock interpretation run:** https://github.com/mreeves1257-glitch/AI-Composition-Deployment/actions/runs/37870594722

## Musical preference (user, exact feedback)

"That was so much better. I can't even tell you how much better. That was really good. That sounded more like it, but it is definitely, if it had that kick drum, it would have been better."

Protect the **MMA 16-bar Rock composition + project-typed fill/chorus translator + recorded Shinyguitar/Growlybass/Big Rusty SFZ source stems**. That is the positively evaluated first band-like composition. It is NOT to be overwritten by the earlier Melody R1 or other temporary Rock groove experiments. The kick needs improvement, not composition replacement. The user also identified a broader need for this interpreter in ALL genres, handled by a parallel validated stage-filing branch (`genre-interpreter-all-55-20261008`), not by copying Rock patterns into them.

## Grounded kick diagnosis

The original Rock MMA 16-bar score contains 32 authentic KICK events. The source Karoryfer Big Rusty kick WAV stem is non-silent and the low-frequency SUBKICK stem is derived from the original kick; neither track is missing. In the live-like original mix handoff:
- Recorded kick source peak: -24.323 dBFS; source RMS -46.988 dBFS
- Kick original target gain: +10.5 dB, effective RMS -36.488 dBFS
- Bass effective RMS -34.625 dBFS
- Recorded subkick target gain: +4.5 dB, effective RMS -43.854 dBFS.
These objective levels do not prove exact perceived audibility on the user's speakers/phone, but support a perceptual masking/balance hypothesis. Never confuse the absence of the audible kick with missing note events.

## Tested kick-only variants

`research/rock_mma_kick_focused_remix_only_r1.py` rebuilt the exact user-liked 16-bar real audio and reused **identical original rendered audio stems, scores, the same SFZ programs, and the original standalone 3D mixer code**, changing only the researched `target_gain_db` in isolated mixer-job copies for KICK and its derived SUBKICK.

- ORIGINAL: exact original full-quality 30.465 s WAV preserved, SHA-256 `e2b8041276fe1253c7ed9a2e475562bd31a3e81c713e7161363b4a6e1964c187`
- MODERATE: KICK +6.0 dB, SUBKICK +6.0 dB, SHA-256 `d7a07da973665ac5136e2c5a5ec2d0feadae8d7ac3c4391ad518af3d809d1867`
- STRONG: KICK +9.0 dB, SUBKICK +6.0 dB, SHA-256 `e8ddf20723471f13255a718fdfd952fd8a21b2ebbe75ab461e252109b8485dcc`

Both output WAVs 44.1 kHz signed 16-bit stereo, ~30.4646 seconds, real master and original 3D code. Each instrument stem's SHA-256 unchanged; all originally sounded guitars, bass, snare, hats, toms and crash retain original parts and per-resource mix config. As with any normalized stereo mix, the aggregate global peak normalization adjusts gain when one stem changes; do not claim the PCM of every other track remains bit-for-bit identical in the final master. No changes to the original approved mix job or any live code.

The files have been downloaded into this conversation and converted to phone-friendly MP3s:
- `Rock_Interpreter_Moderate_Kick_2026-10-08.mp3`
- `Rock_Interpreter_Strong_Kick_2026-10-08.mp3`

**Do not choose a new default until user listens.** This is a tested isolated A/B, not an approved replacement or a permanent rock instrument gain change. If the kick still lacks character, inspect transient spectral balance and original source samples rather than assuming additional gain solves timbre.

## Genre integration pointer

All 13 family-specific `GENRE_INTERPRETER_HANDOFF_R1.json` references and 55 controlled genre entries are verified in https://github.com/mreeves1257-glitch/AI-Composition-Deployment/actions/runs/37871321181, branch `genre-interpreter-all-55-20261008`.
Each uses that genre's ORIGINAL musical language, NOT a Rock substitute, keeping all existing seven-stage flows, and all runtime genre links remain disabled pending individual musical and resource mapping validation. Separate entire-user-library hard copy archive `All_55_Genre_Musical_Interpreter_Handoffs_2026-10-08.zip` is preserved.

**Never overwrite or activate production Composer, Plug, Control Panel, original genre profile data, recorded sample libraries, user-approved audio, or standalone final 3D mixer from research experiments.**
