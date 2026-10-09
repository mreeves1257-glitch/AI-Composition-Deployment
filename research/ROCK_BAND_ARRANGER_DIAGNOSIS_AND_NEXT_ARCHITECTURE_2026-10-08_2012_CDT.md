# Rock Band Arranger — Diagnosis and Forward Architecture
**Hard checkpoint:** October 8, 2026, 8:12 PM CDT (America/Chicago)
**Status:** Research and design only, not deployed or approved as an audio result.
**Branch:** `rock-groove-motion-research-20261008`

## User's direct musical assessment
"The instrument sounds really good but the composition is pretty bad." "Like it much better, but it's still pretty slow." "I definitely can hear all the instruments on it this time." "The reason why it sounds so slow is because of the drum strikes. It's every beat." "Right now it doesn't sound like a rock band at all."

**Meaning:** Preserve all recorded instrument banks, separate tracks, the clarity of the cleaned-drum version, current mix ratios and standalone 3D mixer. The user expects an *actual rock band performance*: coherent verse/chorus/bridge, driving internal drum subdivisions and rolls, bass/drum/guitar interlock, musical accents, real transitions and climaxes. The project is not to raise BPM, double hits arbitrarily, or add reverb to mask an unconvincing arrangement. The user's dry/depth observation is a separate acoustics issue.

## Verified actual code/pattern limitation
In `composer_overrides/genre_development_patch.py`:
- The supplemental KICK bar recipe is fixed beat positions 0.0 and 2.0, plus occasional fixed offbeats.
- SNARE is forced on beats 1.0 and 3.0 EVERY bar: two backbeats without a drummer's rolls, ghost-note swells or fill grammar.
- TOMS only get three-hit transitions when no tom track is present; the verified 127-bar score had only 21 tom events total (seven three-hit fills).
- RIDE is only a 4-bar timekeeping phrase at selected 32-bar intervals.
- CRASH is primarily used to flag 16-bar boundaries.
- The Rock melody original scored six repeated pitches, fixed-note roll patterns. Melody R1 introduced harmonic call/response but was not musically approved by user.
- The earlier drum collision fix removed exactly 441 overlapping duplicate sample triggers and was positively received for its clear instrument sound. It is a preserved opt-in research baseline, not automatically deployed.
- The latest experimental groove motion `rock_groove_motion_v1.py` added 374 lighter hi-hat 8th/16th attacks and repositioned 32 kick pickups; this still does **not** author snare roll language, tom movement, shared bass/guitar accents, or coherent band form. The real 127-bar stereo WAV A/B technically PASSED but has not been approved musically.

## External primary guidance / precedent
Yamaha's "MIDI Song to Style" says arranger style data explicitly composes **main variations, intros, fill-ins, and endings** with per-part editing and source MIDI regions: https://usa.yamaha.com/products/musical_instruments/keyboards/apps/midisong_to_style/index.html
Korg's arranger tutorials define Style Elements (variations, intros, fills, endings) and chord variations via Standard MIDI File markers: https://www.korg.com/us/features/arrangers/tutorials/
Yamaha's older official Style Creator specification likewise describes independent rhythm, bass, chord and phrase MIDI parts within Main A-D, Fill A-D, Break, Intro, Ending.
These are research examples of *complete accompaniment grammar*, not code to copy, vendor endorsement or a claim that their particular files/algorithms can be dropped into the Composer unchanged.

## Architectural decision for the NEXT experimental branch (not implemented or live)
Instead of stacking independent beat patches or adjusting drum tone, establish one **Rock Band Conductor** that produces the full rhythmic/arrangement *intent* BEFORE separate musical parts are authored. Its job:
1. Select the section role (intro, verse A/B, chorus/lift A/B, bridge, break, turnaround, ending), 4/8/16-bar phrase number, current chord and key, expected tension/release.
2. Publish a SHARED groove grid: quarter/eighth/sixteenth offsets, bar-level syncopation, strong/weak accents, and intentional rests. Tempo is NOT inferred from number of hits.
3. Assign coordinated but distinct band roles:
   - KICK establishes grounded pulse and matches selected real bass attacks;
   - SNARE builds the backbeat and may ghost, drag, flam, or roll purposefully as phrase context warrants;
   - HAT/RIDE subdivide 8ths/16ths with occasional rests and contrasting verse/chorus textures;
   - TOMS create musically timed fills (sometimes 16ths across 1/2/4 beats) into a NEW section;
   - CRASH accents arrivals, not every repeated micro-motif;
   - BASS gives the kick/rhythm guitar a common groove while using own note lengths and occasional connecting movement;
   - HARMONY guitar strums/power chords at complementary accents and leaves space for the lead;
   - LEAD repeats recognizable motifs with development, answer, tension and resolution, not six fixed notes per bar.
4. Shared transition instruction: all applicable parts anticipate an upcoming section together; drummer fill and last-beat bass/guitar pickup lead to the SAME destination.
5. Verify with at most a controlled 16/32-bar recorded excerpt before a full 127-bar rendition: written 16th snare/tom rolls, audio from authentic existing SFZ stems, track identities separate, no clipping, no unapproved source changes. Sound must be judged by listening, not event-count growth.
6. Use existing live-recorded instrument resources, untouched, through existing performance interpreter, MIDI/SFZ renderer and independent 3D final stage. The first listening baseline is Melody R1 with duplicate drum strikes removed; do not replace its original copy. New opt-in research work only.

## Next engineering milestone
Prototype the conductor's **8-bar A groove, 8-bar B/chorus contrast and cross-part pickup/fill transition**. Create score-level identity/safety tests and a short real-sample 3D WAV comparison. This must show the kit as a musical performer and interaction with bass/guitar; more hi-hat alone does not count.

### Immutable protections
No modification of production Composer, external Plug, Control Panel, original recorded SFZ/WAV banks, standalone 3D mixer, genre-family filing structure, original Rock mix balances, or prior hard-copy archives. Genre seven-stage links remain inactive unless separately authorized.
