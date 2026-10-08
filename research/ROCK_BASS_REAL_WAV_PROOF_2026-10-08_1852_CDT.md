# Rock Bass — Real Recorded A/B Evidence

**Date/time:** 2026-10-08 18:52 CDT (America/Chicago)
**Workflow:** https://github.com/mreeves1257-glitch/AI-Composition-Deployment/actions/runs/37861189599
**Status:** Real SFZ audio A/B rendered successfully; research only, not production.
**Research audio archive:** `AI_Composer_Rock_Bass_AB_2026-10-08_1852_CDT.zip` generated as a separate user-facing archive in the Oct 8 ChatGPT session; original WAV, candidate WAV, MIDI and JSON reside there. GitHub workflow artifact #11586013603 also holds these recordings.

## Confirmed
Composer ROCK normal-mode seed=0, 145 BPM, generated 3065 events with 254 BASS events. The chosen 8-bar research excerpt held 16 bass events. Both versions rendered with the **same actual Karoryfer Growlybass clean SFZ**, same notes/pitches, onsets, velocities, and sample bank; only the note-off timing changed.

Baseline bass lengths in eight bars: 0.62 / 0.48 beats. Candidate durations: 1.365–1.5 beats. Both WAV render jobs passed. Rendered WAVs: ~13.05s original, ~13.40s candidate.

Objective RMS evidence (measured on rendered WAV mono downmix, same unnormalized amplitude scale):
- Initial attack 0.04–0.17 s: original 0.0098607, candidate 0.0098607 (0 dB change)
- Post-baseline note off 0.28–0.38 s: 0.00126545 vs 0.00611242 (+13.68 dB)
- Ongoing sustain 0.40–0.56 s: 0.00003997 vs 0.00515238 (+42.21 dB)
- Second attack 0.86–1.00 s: 0.01339109 vs 0.01339092 (approximately 0 dB change)
- Whole first 8 s: 0.00796304 vs 0.01000903 (+1.99 dB)

**Interpretation:** Early MIDI note-off demonstrably removes real sample sustain and substantially contributes to isolated bass choppiness. This is NOT proof that the proposed longer release sounds musically better in a complete band mix. Stronger RMS does not by itself signify improvement. In-band timing, timbre, and balance still require listening.

## Candidate, NOT approved/deployed

The research A/B code at `research/rock_bass_real_sample_ab_v1.py` examines Rock BASS note-spacing. Explicit muted/staccato/short notes and rapid passages are untouched. For eligible separate attacks spaced at least 0.8 beats apart, candidate duration may extend to at most 78% of next onset spacing, limited to 1.5 beats. The A/B does not change original source code.

## Status / next boundary

- **Protected:** production Composer; Render service; plug; control panel; original recorded SFZ/WAV libraries; 3D mixer; 13-family/55-genre structures.
- **Proven:** real observed acoustic change with note-off; both recordings exist; same initial attacks; workflow succeeded.
- **Not proven:** best artistic release policy; complete song; genre-wide correction; bass sound within complete ensemble.
- **Next:** compare gain-matched complete Rock ensemble excerpt with the two bass versions (and unchanged guitar, drum, and 3D mix settings), then decide on a narrowly scoped, feature-gated change to Rock bass only. Preserve all earlier baselines.
