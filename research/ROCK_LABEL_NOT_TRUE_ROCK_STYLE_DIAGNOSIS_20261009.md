# Rock recording: genre label vs actual behavior (2026-10-09)

**Listening finding (user):** The recordings are NOT convincing Rock; they sound like repetitive oompa/marching accompaniment. Only the lead guitar, bass guitar, and drums are distinguishable; the rhythm guitar is not distinctly heard. User does like instrument clarity/separation. User wants a fuller band.

## Confirmed in project code

- The full-song test called `AICompositionEngine.run("ROCK",...,mode="normal")`, set the genre template `rock`, and selected 145 BPM. This verifies a **Rock request/label**, not correct Rock musical behavior.
- `genre_styles/Rock/INTERPRETER_ROCK_R1.json` has `activated_in_live_composer: false` and `source_specific_note_score_approved_for_production: false`. The Rock-specific `rock_midi_interpreter.receive_composer_midi` checks MIDI identity and explicitly states `musical_rearrangement_or_phrase_rules_applied: false`, `instrument_renderer_connected: false`. The actual rendered audio did NOT go through the full dedicated Rock performer.
- Legacy `genre_development_patch.py` always appends new kick notes on beats 1 and 3 (plus predictable pushes) and snare hits on 2 and 4 to the legacy pattern; it DOES NOT deduplicate original kick/snare note-on events. Prior measured score had many duplicates. That is a credible source of the repeated drum rhythm.
- The actual Rock preset has three separately rendered pitched roles (LEAD, HARMONY, BASS) plus a recorded drum kit. In listening, HARMONY/rhythm guitar was not clear. Ten stems are NOT ten distinct musical instruments.
- There are unactivated authentic Rock reference styles in the project; `genre_styles/Rock/basicrock.mma` includes a syncopated bass pattern, guitar off-beat attacks and alternate chord-guitar parts, and varied kick and drum patterns. `rock-128.mma` is explicitly doo-wop/12-8, therefore a poor choice for the user's expected driving straight Rock.
- The existing `Greg Sullivan E-Pianos` recorded Wurlitzer electric piano is installed and registered as `electric_piano`; it is a candidate additional distinct instrumental voice for Rock if explicitly selected/verified, not a replacement for guitars/bass/kit.

## Repair boundaries

**Do not relabel existing audio as successful Rock.** Correct the original genre's actual MIDI/performance connection first. Do not change the good recorded instrument sources or clean separated stereo mix; don't cure rhythmic composition by turning up drums; don't activate unverified interpreter or substitute generic General MIDI playback. Use existing verified straight Rock reference structures, not the doo-wop/12-8 style. Add a distinct audible rhythm-guitar role and at least one extra genuinely separate playable instrument part, using original recorded banks subject to verification.

Before any new recording is called Rock, verify: genre-owned behavior actually influences performed MIDI; nonduplicated kick/snare events; varied rock kick/snare/hat and rhythm guitar/bass interactions; original sampled instrument identities preserved; real separate stems; and audible result. An automated PASS never means the user likes how it sounds.

**Status:** Diagnosis and user feedback checkpoint only. No claim that the dedicated Rock interpreter, fuller ensemble or corrected music was deployed or verified.
