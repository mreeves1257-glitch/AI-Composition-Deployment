# Rock Interpreter — User Listening: Better Groove, Bass Masks Band, Keyboard-Like Guitar
**Hard checkpoint:** October 8, 2026, 9:06 PM CDT (America/Chicago)
**Branch:** `rock-interpreter-bass-separation-20261008`, research only, NOT deployed

## User's actual listening assessment
- "The rhythm was a lot, lot better and ... the sound was a lot better. But it's still not where the quality that it should be."
- "I don't know if there was a piano or a keyboard that accompanied that particular. It just sounds real synthetic."
- "The bass guitar overwhelmed everything else."
- Earlier: "That was so much better ... That sounded more like it, but ... if it had that kick drum, it would have been better."

**Preserve that significantly improved 16-bar musical interpreter output as the selected positive reference, not a fully approved recording**. No new composing, changing instruments, substituting bank samples or global tempo to correct bass balance.

## Source facts (instrument identity, not a guess from sound)
- No **piano or keyboard** track is routed in the 16-bar MMA interpreter demonstration.
- The MMA `Chord-Clean` accompaniment is mapped to `HARMONY`, `electric_guitar`, using the existing actual recorded **Karoryfer Shinyguitar** SFZ program.
- The independent `LEAD` part has not yet been developed/added in this proof. Other external MMA guitar parts were intentionally not mapped.
- MMA-generated passage has 225 `HARMONY` guitar note events, 56 real `BASS` notes, and 32 `KICK` events in 16 bars. The real recorded instruments and separate stems rendered to 3D.
- That programmatic way of playing sample chords may explain the keyboard/synthetic impression; not evidence of a substituted synth or a genre requirement. It's a separate future articulation/voicing problem from bass guitar masking.

## Current single-variable listening experiment
Workflow (link after execution): `.github/workflows/rock-interpreter-bass-separation-audio.yml`
Source code: `research/rock_mma_bass_only_balance_audition_r1.py`
- Rebuild and checksum-verify the **exact** original user-liked `MMA_Rock_16Bar_Interpreted_Band_Fill_3D.wav` SHA256 `e2b8041276fe1253c7ed9a2e475562bd31a3e81c713e7161363b4a6e1964c187`.
- Use exact same already-rendered real sample stems and MIDI notes.
- Produce only two isolated master variants by reducing original bass-guitar gain metadata **-4 dB or -8 dB**, with kick, subkick, snare, hi-hat, toms, crash, rhythm guitar gain metadata, pan and exact source instrument recordings untouched.
- Do not change the final stereo 3D mixing algorithm. It peak-normalizes, so whole-master absolute loudness may change, but relative non-bass source gains remain identical.
- Confirm audio integrity and provide full-WAV, MP3 auditions before finalizing any balance.
- No live Composer, Plug, genre connections, Control Panel, recorded SFZ/WAV or 3D mixer edits.

## Next stage AFTER listening
If lighter bass makes kick audible and restores the band, select the appropriate version. Then examine the *rhythm guitar performance language* separately: human strums vs chord-block keyboard-like attacks, realistic source-supported articulation, chord voicing, and lead/rhythm separation, using the same liked musical arrangement.

The 55 genres each have an individually filed, inactive Stage 3→4 arrangement-interpreter reference and independently preserved original 7-stage flow. This experiment is ROCK ONLY.
