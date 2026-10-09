# HARD CHECKPOINT — Additional Arranger Engines, October 9 2026, 8:55 AM CDT

## Exact project stopping point
The original AI Composer has seven stages, 55 genres, one active production identity and a separate final 3D mixer. The 22-capability register is filed across all 55 genres in 13 family handoffs; none are activated. The original user-liked 16-bar Rock MMA recording with the provisional -8dB electric-bass mix was never replaced.

## New source evidence
Three repositories were fetched at explicit pinned commits into independent LICENSE-preserving research directories:
1. Cadenza (GPL-3.0), commit 47da8f71670daa4caa1b3db2bf8f60a323f6c6b1. Windows/JUCE C++ arranger source only, including actual StyleEngine, StyParser, PatternTransposer, SectionFlow, SectionChangeQueue, RuntimePlayback, SongPlayer and tests. No compilation/execution of Cadenza was attempted. Strong research example for NTR/NTT/RTR and section/held-note behavior.
2. backing-tracks (MIT), commit 534b7be0d07595121a9e782c8793244604a1cd41. Go source compiled; go test -vet=off ./... succeeded (upstream main.go has harmless printf newline vet complaint), and example .btml style files produced original multitrack MIDI, independently verified with mido:
   ROCK 1361 note-on events, 5 MIDI tracks, channels 0/1/2/9
   JAZZ 928 note-on events, 4 MIDI tracks, channels 0/1/9
   FOLK 612 note-on events, 3 MIDI tracks, channels 0/1.
   The code hardcodes 4/4 1920 ticks/bar at 480 PPQ, and uses GM tracks: NOT safe to deploy to 3/4 Jazz Waltz or our real recorded SFZ resources without a reimplemented/verified typed adapter.
3. Impro-Visor (GPL-2.0), commit 550bbb554962249aceb0e82a72142e3e5b3c0d4a. Selected Java source directories for style, lick generation, harmonic roadmap, and voicing only; not compiled or installed, no artist leadsheets/audio.

Proof workflow: https://github.com/mreeves1257-glitch/AI-Composition-Deployment/actions/runs/37940166522
Source path: research/KEYBOARD_ARRANGER_SOURCE_ARCHITECTURE_REVIEW_2026-10-09.md
Actual download: GitHub run artifact EXTRA_Cadenza_ImproVisor_BackingTracks_Genre_MIDI_20261009, id 11620712953.

Previously archived JJazzLab Toolkit 5.2.1 binary/source, music21, mingus and original MMA are NOT forgotten and must not be overwritten. Their research archive is dated October 9 2026 and includes all original 55 genre interpreter handoffs plus 22 gates.

## Next implementation priorities
Do not copy a generic style blindly or duplicate the existing Composer. The code from Cadenza makes chord rule adaptation, proper held-note changes, section planning and context-aware behavior clear enough to investigate. The MIT BTML engine offers text structure and verified MIDI generator. Source mapping for Rock sampled chord guitar needs physically meaningful strum offsets and note envelopes to avoid keyboard-like blocks. Every candidate must demonstrate one specified musical improvement through original SFZ resource stems and the unchanged final 3D mixer. Preserve genre individuality, proper meter (including 3/4), no mandatory drums for solo piano, no unlicensed proprietary styles.

**Source code license / deployment:** Cadenza GPLv3 and Impro-Visor GPLv2 are separately held research references, not copied into the Composer. MIT code can be considered with attribution. JJazzLab LGPL license has its own linking/distribution rules. All modules remain inactive.

**Frozen original:** https://github.com/mreeves1257-glitch/AI-Composition-Deployment/blob/rock-interpreter-bass-separation-20261008/research/HARD_STOP_ROCK_INTERPRETER_MINUS8DB_ALL55_2026-10-08_2117_CDT.md
