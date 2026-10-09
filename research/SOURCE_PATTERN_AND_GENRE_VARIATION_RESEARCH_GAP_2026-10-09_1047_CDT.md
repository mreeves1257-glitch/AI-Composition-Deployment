# NEW RESEARCH FINDING — Source Patterns & Style/Chord Variations
**Research date/time:** October 9, 2026, 10:47 AM CDT (America/Chicago)
**Type:** Future implementation research / verified architecture gap, NOT working code, NOT production approval

## What official manufacturers actually do
1. **Yamaha Genos2 Reference Manual**, Styles > Style Creator p.20 onward: a style has section-based **source patterns** recorded/imported individually for 8 channels: rhythm 1, rhythm 2, bass, chord 1, chord 2, pad, phrase 1, phrase 2. Intro, main, fill, ending all have associated patterns. Primary PDF: https://usa.yamaha.com/files/download/other_assets/1/2318561/Genos2_reference_manual_En_C0.pdf
2. Yamaha Style File Format controls include NTR root transposition, NTT chord type, high-key / note limits, RTR retrigger/stop; guitar-specific NTR/NTT and slash-bass handling are source/sound specific. Same manual pp.28–32.
3. **Korg Pa5X user manual:** styles are organized into Style Elements (intro/variations/fill/ending) and each track may have several Chord Variations (CV), with chord-to-variation assignment. Chord-variation-specific pattern content is separate from the generic style name. Official Korg Pa5X manual: https://cdn.korg.com/us/support/download/files/013db58cced0d6e5550256afafaac4ac.pdf
4. Pa5X new-features manual documents independent chord variation length and timing; not mandatory to copy Korg's file structure. Official manual: https://cdn.korg.com/us/support/download/files/69f13112591895c3222b45805422b393.pdf

## Project gap — source patterns are not the same as definitions
Current project stores musical *descriptions* for all 55 and a common executable chord/section/range interface; **the 55 do not have a complete bank of playable, licensed/original note-source patterns**. The shared symbolic grammar accepts explicitly supplied patterns; it does not automatically invent/author human-quality melodic/drum/guitar patterns for each genre. Existing 22 handlers do not close this gap by themselves.

## Implementation direction inside the existing system, not new architecture
- Place **genre-specific source-pattern data** under each existing genre/family, NOT individual interpreter engines. Common validator/selector stays near ONE shared interpreter.
- Pattern entry should carry: genre/source identity, role/selected instrument, meter and grid, section and phrase context, original or clearly licensed provenance, source chord/key where needed, chord-quality and variation selection criteria, multiple human-musical alternatives, dynamics and intentional rests/accents, fills/breaks/endings, role-specific physical constraints, and source sample mapping requirement.
- Shared interpreter chooses a per-role pattern suited to selected style/section/chord and transforms it by existing CAP_02–CAP_10; Stage 5 maps gestures to **verified** sample-native controls; Stage 6 generates **separate** real recorded audio; Stage 7 retains separate 3D mixer.
- Produce small actual per-genre authored fixtures for Rock/Jazz/Salsa/solo Pianist/Waltz with **different legitimate rhythmic/voice behavior**, prove that these make independently distinct symbolic note plans, then scale to all 55. **Do not impose eight Yamaha channels on every genre**: solo Pianist may have one piano part; Salsa may have layered percussion; styles and physical instruments vary.
- Correctness gate: meaningful intro→verse→chorus→fill→ending coordination, melodic breathing, selective kit transitions, guitar articulation not keyboard blocks, no repeated exact same beats on all instruments, no unverified sound mappings, source provenance and no hidden cross-genre Rock fallback.
- This is the most consequential missing **content/arrangement** implementation, encompassed by existing CAP_01 (musical arranger), CAP_03 (variation choice), CAP_08 (section change), CAP_09 (ensemble), CAP_10 (genre language), not a new 23rd required system module.
- Avoid copying copyrighted proprietary Yamaha/Korg style files or importing GPL program code into production without license evaluation. Use manufacturer publications as reference for behavior, not source to duplicate.
