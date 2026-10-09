# Rock interpreter — kick/bass rhythmic-overlap audit

**Checkpoint:** 2026-10-08 (America/Chicago), following user stereo listening.
**Status:** Verified actual external MMA MIDI note-on pattern; NO source, music or production modifications.
**Listening baseline:** User preferred the 16-bar MMA + musical-intent Rock arrangement, but cannot hear a pronounced kick. User then observed: "The bass guitar and the kick drum has identical beat pattern."

## Exact evidence from the preserved source MIDI
File in completed A/B artifact: `MMA_Rock_16Bar_Two_Sections.mid`
- 16 bars, 145 BPM, 4/4; 32 KICK (MIDI 36) note-on events, 56 BASS notes.
- 24/32 kick attacks occur within 0.12 beats of a bass note onset; 11/32 exactly coincide in quantized MIDI time.
- Bars 1–8: kick consistently onsets near bar-local 0 and 1.5 beats; bass attacks at 0, 1.5, 2.0, 3.5 beats. Thus ALL the kick onsets of this verse match or approximately match a bass-guitar onset, before the user even judges kick timbre.
- Bars 9–16: kick *still* onsets near bar-local 0 and 1.5; bass switches largely to 0, 2.0, 3.5 (sometimes 2.5). The kick pattern fails to vary despite new section role.
- Bass guitar's 56 events differ from kick's 32; it is inaccurate to say every bass event is identical to the kick or to claim verified spectral masking solely from timing coincidence.
- Original recorded KICK and derived SUBKICK audio WAV stems are present and non-silent. Earlier boosted kick/subkick A/B (+6/+6dB and +9/+6dB) passed render but user still reports an indistinct kick, so do not keep indiscriminately raising kick gain.
- User was listening over phone speakers initially and later through stereo; playback frequency response could also contribute but does not erase the rhythmic overlap in source MIDI.

## Musical interpretation
Kick and bass locking together for important accents is NORMAL AND DESIRABLE in Rock. The root defect is the *same recurring kick placement every bar*, poor section-aware contrast and no distinct kick presence in the combined recording. Do NOT randomly offset bass/kick; do NOT sidechain everything automatically. A whole-band conductor should maintain shared downbeats, create bass motion BETWEEN kick anchors, vary kick pickups/fills intentionally, and render a clearly audible real kick attack without changing bass-guitar identity or composition the user already likes.

## Controlled next test — not yet executed
Keep two protected original 16-bar recordings, notes, source SFZ samples, original 3D mixer, and all 55 genre handoffs unchanged. Isolated research candidate options:
1. **Rhythmic contrast only:** preserve bass score, original sounds, and volume; write purposeful kick placement variations on section transitions via the stage-3-to-4 interpreter, while preserving central kick/bass anchors and not forcing identical 0/1.5 beat on every bar. User auditions beside liked baseline.
2. **Timbre/attack contrast only:** with same kick and bass notes, audition subtle **recorded-kick transient presence** or small bass band carve against unchanged source master. A real kick should remain recognizable without subwoofer. Not a new synthesized drum; do not assume global volume boost is enough.
Never combine these changes in a single first A/B, and evaluate whether the existing sound remains good.

## Hard protections
Current liked Rock 16bar mix and previous separate kick-boost A/B kept intact. External MMA original (GPL) stays isolated; Composer/Plug/Control Panel unmodified. Original SFZ recorded Karoryfer sources unchanged. All 55 genre handoffs remain references with inactive routing, each style retains its own music language. No change to original seven-stage order or final stereo 3D mixer.
