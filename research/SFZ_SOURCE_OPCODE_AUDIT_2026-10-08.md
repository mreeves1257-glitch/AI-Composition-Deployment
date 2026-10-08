# AI Composer: source-SFZ performance audit
**Date:** 2026-10-08 (America/Chicago)  
**State:** Reference research only. No build, original sample, routing or control-panel changes.

## Exact currently selected targets
From `build_current_composer.sh` in `mreeves1257-glitch/AI-Composition-Deployment`:

- **Rock RHYTHM_POWER_CHORDS:** `KARORYFER_SHINYGUITAR/Programs/composer-electric.sfz`, initial CC100=0, CC101=127, CC106=32, CC107=0.
- **Rock LEAD_MELODY:** `KARORYFER_SHINYGUITAR/Programs/composer-electric-lead.sfz`, initial CC1=88, CC100=0, CC101=127, CC103=85, CC104=90, CC105=64, CC106=24, CC107=0.
- **Electric bass guitar:** `KARORYFER_GROWLYBASS_V1_002/growlybass_clean.sfz`.

## Source-program findings

### Karoryfer Shinyguitar
`Programs/main.sfz` sets `label_cc1=Vibrato Depth`, `label_cc103=Vibrato Speed`, `label_cc104=Vibrato Delay`, `label_cc105=Vibrato Fade`, `label_cc106=Release Noise`, `label_cc107=Voices`, `label_cc110=Mute`. The native global `ampeg_hold`, `ampeg_decay`, `ampeg_sustain` respond to CC110 (mute), with CC110=0 by default. `lfo01_pitch_oncc1` plus its timing controls are a programmable pitch-LFO vibrato, not proof of real recorded legato slides.

`Programs/electric_one.sfz` through `electric_five.sfz` contain velocity-layered, recorded electric string notes with alternate sampled attacks and CC107 voice-selection ranges; they do **not** by themselves establish naturally flowing performed phrases. `electric_release.sfz` includes `trigger=release` regions with multiple recorded releases. `electric_noises.sfz` includes sampled string mute/noise events on separate low MIDI keys.

The build derives the Rock rhythm SFZ from `Programs/main.sfz` with electric includes and changes the release-noise default. Its lead derivative changes source CC vibrato parameters. Original upstream recordings must remain read-only. **No proof yet that the current MIDI performance path generates the right sequence of release/mute/transition instructions.**

### Karoryfer Growlybass
`growlybass_clean.sfz` is the *selected* program in the build. Inspection shows `sample=sustain/...` recorded notes with dynamic sampled alternatives and some scrape samples. It contains no `trigger=release` regions in the examined source. Upstream `growlybass_dirty.sfz` has `trigger=release` regions and the bank holds separate release WAV samples; however, it is **not** the selected sound. Do not swap patches or mix program articulations silently. Audit whether a derived clean-bass SFZ can lawfully and faithfully reference the associated native release files before authorizing anything.

## Implications for the chopped-up sound

1. Guitar or bass note duration is NOT the same thing as the audible lifetime of the recorded sample. A note can end early through MIDI note-off/envelope release, or a sample can run out even if MIDI note-on is held. Longer MIDI durations alone do not solve either problem universally.
2. A note-to-note `connected` instruction must be translated to a demonstrably supported sampled transition or renderer-specific legato behavior, not an invented global pitch glide.
3. Release noises and muted-string noises are musically useful only when triggered at correct times and at appropriate levels. Do not play every noise sample on every note.
4. The default Rock lead CC1=88 provides source-level vibrato capability, but it is not independent automatic phrase analysis. The existing opt-in phrase gesture route is currently off in ordinary production.
5. Test candidate controls against isolated recorded-instrument audio before connecting them to any genre. A passing source-opcode audit is not a successful full-song playback.

## Next research action
Compare actual program note-off behavior at the source, including sample durations and SFZ envelopes, with the generated MIDI event on/off times. Then record exact per-instrument capability contracts and controlled, safe additions to the existing output bridge, without touching deployed services until ready.

## Source trails
- https://github.com/mreeves1257-glitch/AI-Composition-Deployment/blob/main/build_current_composer.sh
- https://github.com/sfzinstruments/karoryfer.shinyguitar/blob/master/Programs/main.sfz
- https://github.com/sfzinstruments/karoryfer.shinyguitar/blob/master/Programs/electric_one.sfz
- https://github.com/sfzinstruments/karoryfer.shinyguitar/blob/master/Programs/electric_release.sfz
- https://github.com/sfzinstruments/karoryfer.shinyguitar/blob/master/Programs/electric_noises.sfz
- https://github.com/sfzinstruments/karoryfer.growlybass/blob/master/growlybass_clean.sfz
- https://github.com/sfzinstruments/karoryfer.growlybass/blob/master/growlybass_dirty.sfz