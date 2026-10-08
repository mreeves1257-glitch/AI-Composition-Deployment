# AI Composer — Genre Architecture & Source Inventory Hard Save

**Checkpoint time:** 2026-10-08 14:33 CDT (America/Chicago)
**Source repository:** mreeves1257-glitch/AI-Composition-Deployment
**Source commit (immutable original snapshot):** `0416abec7b6cd047e2af01e30b3d81bf4b694e0f`
**Preservation branch:** `hardcopy-genre-structure-2026-10-08-1429-CDT`
**Status:** ARCHITECTURE FILED; REFERENCE INVENTORY IN PROGRESS; CONNECTIONS INACTIVE
**Intention:** Preserve all current project files without altering the production Composer, plug, original sound sources, or standalone 3D mixer.

## What was filed and preserved
- All **55 separate styles** live inside **13 musical-family reference files**, with individual identities, instruments, musical definitions, and mix-intensity proposals preserved.
- A **seven-stage ordered plan** is filed per style: (1) select genre; (2) define musical structure; (3) select instruments and shared drum kit; (4) compose separate parts; (5) perform musically; (6) render independent audio stems; (7) genre mix, then standalone 3D mix.
- **385/385 planned stage connections are inactive.** A specified stage is not proof that its required implementation or playable resource is complete.
- Rock's existing working contract and Jazz Ballad's working but listening-unverified configuration are preserved. Other 53 intensity profiles remain undeployed proposals.
- Shared drum catalog is separate from all 13 families; distinct drum roles and output stems remain independent.
- Original runtime assets are stored inside `composer/runtime.b64`. Named legacy paths inside the archive are not standalone files in the GitHub tree.

## Preliminary inventory findings, 2026-10-08
1. **Tempo definitions:** All 55 profiles have two numeric values in `musical_definition.tempo_bpm_range`; this confirms range metadata only, *not* correct live tempo, pulse, meter, groove, or audible speed. Rock's `normal_length_tempo_and_bars` routine currently chooses the upper bound from its configured tempo range (Rock profile: 100–145 BPM). Rock's genre development patch contains note-length logic documented as addressing a prior half-time-feel problem. Preserve both pending musical verification.
2. **Instrument tracks:** 315 individual track-role records across 55 styles; **129 have `instrument_id: null`**, marking roles without an assigned individual sound ID in the family reference file. A non-null ID is not necessarily a verified playable WAV/SFZ resource. Source filenames, patch mappings, licensing/attribution, expected articulation, and actual rendered stem availability must be separately checked.
3. **Drums:** 43 selected shared kits are marked `unverified_*`; this is a placeholder identifier, **not** proof of a recorded playable kit. Check actual per-piece sample/source and the independent kick, snare, hi-hat, tom and cymbal roles before authorizing any genre.
4. **Stage source paths:** 25 distinct direct stage source-file references appear in the plans; all **non-archive direct file paths** checked in the GitHub source tree exist. This establishes file presence, not working imports, sound availability, correct semantics, or validated runtime behavior.
5. **Potential identity reconciliation:** Rock family musical definition uses profile ID `ROCK_CORE_V2`, while `genre_styles/rock.py` lists `GENRE_PROFILE_ID = "ROCK_V1"`. This must be investigated before activating a style routing relationship; preserve current behavior rather than changing either side without tracing dependencies.
6. **Performance:** All 55 plans explicitly request articulation, timing, sustain, context-appropriate vibrato, dynamics, and melodic independence. In the stage inventory, **53** performance implementations are pending; Rock and Jazz Ballad remain works in progress, not certified final listening outputs.
7. **No completion claim:** The new filing architecture and staging sequence are present, but **complete playable music is not confirmed** by this audit for any genre. Production code is not changed by this checkpoint.

## Required distinctions during next inspection
For each of the 55 styles separately, distinguish:
- **Musical intent:** genre identity, form, BPM range, meter, rhythmic subdivisions, groove, harmonic vocabulary, melodic/bass/drum roles, articulation and dynamics.
- **Executable programming:** actual code/patterns that produce events and timing, expected mappings, note lengths/sustain, groove/humanization, gain controls, stage inputs and outputs.
- **Playable sources:** real WAV/SFZ/SF2/sample or equivalent data, instrument voice/patch mapping, provenance/attribution, correct source paths and license, whether sample load and render are verified.
- **Relationships:** source-to-role mapping, planned stage-to-stage contracts, independent output stem-to-mix mapping; *do not activate handoffs*.
- **Verification:** file exists / resource identified / playable source verified / musical performance audited / full audio rendered and listened to (these are separate states).

## Preserve and next actions
1. Hold current architecture fixed and preserve all original files; do not rename, delete, flatten, or mix genres.
2. Complete independent references and sound-source inventory for **every** genre. Mark missing, placeholder, present-unverified and verified separately.
3. Review tempo implementation, BPM selection, meter, beat-grid conversions and perceived groove; do not equate correct numeric BPM with a musically correct feel.
4. Verify relationships/file ownership, then document any missing pieces inside their existing family/style records.
5. Leave all stage connections **inactive** until a separate user-approved activation pass. The 3D mixer remains standalone at the end.
6. Do not alter Composer or mix behavior merely because audit findings suggest a possible improvement.

**Preserved original source commit:** `0416abec7b6cd047e2af01e30b3d81bf4b694e0f`.
**This checkpoint file is additive to the preservation branch, not a replacement for any source file.**
