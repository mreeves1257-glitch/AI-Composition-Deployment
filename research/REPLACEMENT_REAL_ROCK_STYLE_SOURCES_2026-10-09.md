# Replacement Rock Style Selection — 2026-10-09

## User direction
The previous audio *was labeled ROCK* but was not recognizably Rock to the listener: repetitive oompa/oompa drum groove, only lead guitar, bass and drums independently audible. Stop trying to polish that flawed Rock-template groove. Use a **different externally authored Rock musical reference**. The original sampled instrument sounds and distinct separation are approved and must stay protected. The user would also prefer more audible band instruments.

## Primary NEW reference — Rock2
- Source: official maintained MMA repository `infojunkie/mma`, `lib/casio/rock2.mma`, frozen at commit `c52943c31aa1e64fa9b5313620d5065f91c22773` (2026-06-20).
- Author/source metadata in original file: Bob van der Poel / Casio WK-3000; described as **Hard driving rock beat**.
- Unmodified, preserved copy: `composer_overrides/genre_styles/Rock/EXTERNAL_MMA_ROCK2_UPSTREAM_REFERENCE.mma`.
- The actual original style has syncopated kick patterns, backbeat snare, 8th-note hi-hat motion, bass movement through multiple rhythmic positions, separate overdriven and muted rhythm-guitar roles, and its own intro/main/ending.
- Its MIDI voices are symbolic instructions, NOT approval to switch to General MIDI patches. Map every part to the original recorded SFZ instruments before executable use.

## Additional distinct Rock references (not stacked into the same score)
- `lib/pflib/rock1.mma` written by Peter Falk, marked **Classic Rock Style** and includes piano and plectrum guitar plus bass and kit. Copy: `EXTERNAL_MMA_CLASSIC_ROCK1_UPSTREAM_REFERENCE.mma`.
- `lib/casio/poprock1.mma` marked 1970s pop-rock and includes organ, piano, overdrive guitar, bass and drums. Copy: `EXTERNAL_MMA_POPROCK1_UPSTREAM_REFERENCE.mma`.
- Both are alternatives for comparing coherent complete genre profiles, **not** automatically combined or activated.

## Integrity and license
- All three files are copied unmodified from the project and GitHub revision above, alongside their upstream GNU GPL v2 license in `EXTERNAL_MMA_UPSTREAM_GPL2_LICENSE.txt`.
- Original code and recorded instruments untouched; the GPL license needs to be respected if distributing derivative code.
- Older `basicrock.mma`, `rock-128.mma` and generic template remain preserved for traceability, but are **rejected as sources for the next Rock listening audition**.
- Do not assume a style-source selection by itself makes playable audio. Verified Rock-specific interpreter/MMA execution into Composer MIDI and source SFZ stems remains necessary before an actual new recording.
- New recording must retain original separate instrument sounds/standard stereo output and avoid doubled kick/snare events. Add at least one genuinely distinct audible instrument part if coherent and verified (existing recorded Wurlitzer available; no forced addition if it undermines selected style). No 3D requirement.
- Success criterion is **listener recognizes it as Rock**, not just filename, BPM, note counts, or a green software test.

**State: Alternative Rock sources obtained; not yet connected to executable Rock MIDI or recorded.**
