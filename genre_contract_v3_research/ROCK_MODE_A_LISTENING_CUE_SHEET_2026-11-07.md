# Rock Mode A Guitar A/B — Focused Listening Cue Sheet

Date: 2026-11-07  
Branch: `genre-contract-v3-no-reasoning-diagnostic`  
Status: diagnostic only; no live promotion; reasoning engine excluded.

## What this A/B changes

- A = developed Rock Core V3 guitar writing before Mode A.
- B = the identical symbolic writing after `A_GUITAR_DURATION_ONLY`.
- Pitch, onset, velocity, event count, instrument identity, form, harmony, bass, and drums are unchanged.
- Only electric-guitar note duration changes.
- The symbolic duration-shape audit passed with zero same-track overlap, zero cross-bar spill, zero split rhythm-guitar chord durations, and zero changed cross-bar lead phrase gaps.

## Why these cues matter

The lead-guitar duration changes are small and conservative:

- 82 lead events changed.
- Lead extension range: about +0.05 to +0.1675 beat.
- Mean lead extension: about +0.0802 beat.

The rhythm-guitar changes are much stronger:

- 186 harmony events changed.
- 78 harmony-note events use the largest +2.3-beat extension.
- Because rhythm-guitar harmony is voiced as three-note gestures, those 78 notes represent 26 chord attacks.
- Those gestures change from 0.5 beat to 2.8 beats.
- The smallest remaining same-track gap after Mode A is 0.03 beat; no overlap is created.

That makes the long rhythm-guitar sustains the main human-listening risk. The question is not whether they are structurally legal—they are—but whether they sound naturally like a guitarist letting a chord ring or whether they blur the riff identity.

## Focused A/B listening points

Approximate times assume 123 BPM.

### 0:00–0:08 — Intro, bars 1–4
The clearest first test. Each bar begins with a rhythm-guitar chord that changes from 0.5 beat in A to 2.8 beats in B.

Listen for:
- Does B sound fuller and more like a held guitar chord?
- Or does B erase too much rhythmic space and make the intro drag?
- Does the sustained chord mask the next gesture?

### 0:08–0:22 — Verse 1
Large 2.8-beat rhythm-guitar sustains recur around:
- ~0:07.8
- ~0:11.7
- ~0:15.6
- ~0:19.5
- ~0:21.5

Listen for whether the longer ring helps the verse breathe or makes the guitar accompaniment too continuous.

### 0:23–0:38 — Chorus 1
This section contains both strong sustain and deliberate shortening.

Important spots:
- ~0:23.4, ~0:27.3, ~0:31.2, ~0:35.1, ~0:37.1: large 0.5 → 2.8 beat chord sustains.
- ~0:26.8: a chord is slightly shortened from 0.5 → 0.47 beat.
- ~0:34.6: a chord is sharply shortened from 0.5 → 0.22 beat.

Listen for whether B preserves punch and separation through those short attacks while allowing neighboring chords to ring.

### 0:39–0:54 — Verse 2
Large sustains recur at approximately:
- ~0:39.0
- ~0:42.9
- ~0:46.8
- ~0:50.7
- ~0:52.7

This is useful for deciding whether the Mode A behavior still feels musical after repetition rather than only sounding good in the opening.

### 0:55–1:06 — Chorus 2
The same tension returns between long ring and short punctuation.

A particularly useful short-hit check:
- ~1:02.0: chord shortened from 0.5 → 0.22 beat.

Listen for whether the contrast between ringing chords and short hits feels intentional.

### 1:13–end — Outro
Around ~1:13.7, another chord is shortened from 0.5 → 0.22 beat.

This is the best ending check:
- Does Mode A help the outro feel resolved?
- Or does the longer sustain elsewhere make the ending lose contrast?

## Decision rule

Do not add strum timing, bass sustain, random timing, continuous control, or any other performance variable yet.

Mode A should move forward only if B sounds:
1. more connected and more guitar-like than A,
2. without blurring riff boundaries,
3. without filling intentional space,
4. without weakening short rhythmic attacks,
5. without making the harmony guitar feel like a pad rather than a guitarist.

If the lead improvement is good but the rhythm-guitar sustain is too long, the next repair should be narrowly limited to the HARMONY duration policy rather than discarding Mode A or changing other performance dimensions.
