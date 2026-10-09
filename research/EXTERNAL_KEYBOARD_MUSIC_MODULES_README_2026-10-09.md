# Keyboard-arranger intelligence — downloaded research modules, NOT production integrations

**Date:** October 9, 2026 (America/Chicago)  
**Scope:** Separately licensed original distributor archives and research references. No changes to the original AI Composer, Plug, Control Panel, audio stems, SFZ banks, or 3D mixer.

## Public modules in the companion archive

1. **JJazzLab Toolkit 5.2.1**, binary engine and full source JARs. Official upstream https://github.com/jjazzboss/JJazzLabToolkit/releases/tag/5.2.1 — LGPL-2.1. This is JJazzLab's arranger/chord/style/phrase MIDI engine; **requires Java 25+**. A downloadable library is not a working interface to the current Composer until Java/version, API, license and exact SFZ resource mapping are independently tested.
2. **music21 10.5.0**, pinned official PyPI Python wheel, https://pypi.org/project/music21/ — BSD-3-Clause style. Music theory, chord timelines, voice-leading, patterns, music forms and note sequences. It is NOT a finished automatic keyboard arranger.
3. **mingus 0.6.1**, pinned official PyPI Python wheel, https://pypi.org/project/mingus/ — GPL-3.0. Chord theory, progressions, notation and MIDI. Keep as separately licensed reference/research utility, not silently merged source.

## Already saved October 8, no new copy required
- Official independent **MMA Musical MIDI Accompaniment 25.05.0** source and working demo in original preserved `AI_Composer_Musical_Interpreter_Fetched_and_Tested_2026-10-08_2024_CDT.zip`. The original Rock A/B is already preserved in the dated hard stop.
- Separate early **JJazzLab Toolkit source-reference-only** small archive also exists, but did NOT contain its full distributable engine. This download remedies that gap.

## Manufacturer capabilities NOT downloadable as reusable software
- **Yamaha** SFF NTR/NTT/RTR, MegaVoice/S.Art and style-to-chord interpretation
- **Korg** Pa5X chord-variation engine, Guitar Mode 2 and DNC expressive playback
- **Ketron** Live Modeling pattern sections/drums/performances
- **Roland** Style Composer and accompaniment section sequencing
- **Casio** accompaniment and chord progressions

These are reference designs described by the manufacturers and **not redistributable plug-in engines**. No piracy, proprietary sound banks or firmware are collected.

## Existing original structure, still unchanged
1. Select Genre
2. Define Musical Structure
3. Choose Instruments and Drum Kit
   - original reserved **musical interpreter / translation handoff** to Stage 4
4. Compose Separate Parts
5. Perform Musically
6. Render Independent Recorded Audio Stems
7. Genre Mix then Standalone 3D Mixer

The **22 missing-or-partial capability procedure** is an inactive, conditional, genre-specific checklist in each of 55 genres, not 22 functioning modules installed today. `GENRE_22_CAPABILITY_PROCEDURE_MASTER_R1.json` owns the single source-of-truth capability definitions; family files are XRefs. Each genre must choose only relevant capabilities based on actual selected sounds; no Rock drum/guitar assumption for the 54 other genres.

## Future controlled engineering investigations
- Evaluate JJazzLab Toolkit as an isolated chord/section/rhythm phrase source and standard MIDI export; do not confuse its FluidSynth demo with our recorded sampled outputs. Confirm Java 25 runtime first.
- Evaluate music21 harmony and voice-leading against our existing Stage 2 and Stage 4 functionality. Only introduce missing algorithms.
- Use mingus as licensed reference for chord/progression rule checks, not an installed core dependency.
- Focus separately on human guitar strums, sample-aware articulation, shared groove and arrangement variation; original -8dB user-preferred Rock audition is immutably retained until further user instruction.

## Authenticity
Source release SHA256 checksums were taken directly from the official JJazzLab Toolkit v5.2.1 GitHub release and the Python package indexes, and are checked during the download workflow. Output manifest records SHA256 and sizes for every copied file. Downloads remain inactive.
