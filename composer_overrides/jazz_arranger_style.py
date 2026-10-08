"""Independent Jazz Ballad arranger-style performance layer.

Inspired by the documented *concept* of arranger keyboards: a common chord
timeline, per-track patterns, register guards, sections and phrase alternates.
No manufacturer's style file, samples, program code or proprietary phrases
are copied. The existing chord-playing electric piano is preserved verbatim.
All other genres, Rock, the sample bank and the 3D mixer are untouched.
"""
from __future__ import annotations

from collections import defaultdict

VERSION = "JAZZ_BALLAD_ARRANGER_STYLE_R1"
BASS_RANGE = (35, 55)       # Jazz Meatbass SFZ's verified mapped MIDI range
CLARINET_RANGE = (60, 71)   # Jazz VSCO clarinet SFZ's verified mapped range
# These refer to the *composition's* eight-bar sections, not to an instrument.
SECTION_NAMES = ("INTRO", "MAIN_A", "MAIN_B", "BRIDGE", "MAIN_C", "ENDING")


def section_for_bar(bar: int, total_bars: int) -> str:
    if bar < 2:
        return "INTRO"
    if bar >= max(2, total_bars - 4):
        return "ENDING"
    return ("MAIN_A", "MAIN_B", "BRIDGE", "MAIN_C")[(max(0, bar - 2) // 16) % 4]


def _available(chord: dict, lo: int, hi: int) -> list[int]:
    pcs = chord.get("pitch_classes", [])
    if not pcs or not all(isinstance(pc, int) and not isinstance(pc, bool) for pc in pcs):
        return []
    allowed = {pc % 12 for pc in pcs}
    return [midi for midi in range(lo, hi + 1) if midi % 12 in allowed]


def _choose(candidates: list[int], target: int, previous: int | None,
            avoid_repeat: bool) -> int:
    if not candidates:
        raise ValueError("JAZZ_ARRANGER_NO_PLAYABLE_NOTE")
    return min(candidates, key=lambda n: (
        16 if avoid_repeat and previous == n and len(candidates) > 1 else 0,
        abs(n - target),
        max(0, abs(n - previous) - 5) if previous is not None else 0,
        n,
    ))


def arrange_jazz_ballad(events: list[dict], ctx: dict,
                        creation_seed: int = 0) -> list[dict]:
    """Adapt an existing Jazz Ballad score, never creating new instruments.

    Bass follows the actual chord's root/fifth and occasionally a third.
    Clarinet uses chord-tone anchors and gentle scale-based connective notes.
    Brush one-shots are spaced to prevent overlapping long recorded swishes.
    The piano, sound mappings and finished mix implementation are unchanged.
    """
    if not events:
        return events
    harmony = ctx.get("harmony", {})
    chords = harmony.get("chords", [])
    meter_def = ctx.get("meter", {})
    if not chords or not isinstance(meter_def, dict):
        return events
    meter = float(meter_def.get("numerator", 4)) * 4.0 / float(meter_def.get("denominator", 4))
    if meter <= 0:
        return events
    total_bars = len(chords)
    keyed = defaultdict(list)
    for index, event in enumerate(events):
        track = str(event.get("track_id", "")).upper()
        if track in ("BASS", "LEAD", "SNARE"):
            bar = min(total_bars - 1, max(0, int(float(event.get("start_beat", 0)) // meter)))
            keyed[(track, bar)].append((index, event))
    for entries in keyed.values():
        entries.sort(key=lambda pair: (float(pair[1].get("start_beat", 0)), pair[0]))

    modified = {}
    suppressed = set()
    previous_lead = None
    previous_bass = None
    previous_brush_beat = float("-inf")

    for bar in range(total_bars):
        chord = chords[bar]
        if not isinstance(chord, dict):
            continue
        chord_pcs = chord.get("pitch_classes", [])
        if not chord_pcs:
            continue
        bass_candidates = _available(chord, *BASS_RANGE)
        lead_candidates = _available(chord, *CLARINET_RANGE)
        if not bass_candidates or not lead_candidates:
            # Do not replace valid original events with arbitrary unsupported pitches.
            continue
        root_pc = int(chord_pcs[0]) % 12
        fifth_pc = int(chord_pcs[2]) % 12 if len(chord_pcs) > 2 else root_pc
        third_pc = int(chord_pcs[1]) % 12 if len(chord_pcs) > 1 else root_pc
        variation = (bar // 4 + int(creation_seed)) % 4
        section = section_for_bar(bar, total_bars)

        # The acoustic double bass must play in its installed SFZ note range.
        bass_entries = keyed.get(("BASS", bar), [])
        for position, (index, event) in enumerate(bass_entries):
            pc = (root_pc if position == 0 else
                  (fifth_pc if position % 3 == 1 else third_pc))
            specific = [note for note in bass_candidates if note % 12 == pc]
            if not specific:
                specific = bass_candidates
            destination = 42 + (variation - 1) * 2
            if position > 0 and previous_bass is not None:
                destination = previous_bass + ((2, 5, -2, 3)[variation])
            pitch = _choose(specific, destination, previous_bass, False)
            revised = dict(event)
            revised["midi"] = pitch
            modified[index] = revised
            previous_bass = pitch

        # A melody should develop in four-bar phrases but remain inside the
        # actually mapped clarinet recordings. Chord tones anchor strong beats.
        lead_entries = keyed.get(("LEAD", bar), [])
        for position, (index, event) in enumerate(lead_entries):
            beat = float(event.get("start_beat", 0)) % meter
            phrase = bar // 4
            contour = (0, 2, 4, 2, -1, -3, 1, 3)
            target = 65 + contour[(phrase + position + bar % 4 + int(creation_seed)) % 8]
            # Keep every on-beat melody anchor harmonically related.
            # Passing notes from the existing scale provide connective motion.
            candidates = lead_candidates
            if position > 0 and beat >= meter / 2:
                scale = ctx.get("key", {}).get("scale_pitch_classes", [])
                if scale and all(isinstance(pc, int) for pc in scale):
                    passing = [n for n in range(CLARINET_RANGE[0], CLARINET_RANGE[1] + 1)
                               if n % 12 in {pc % 12 for pc in scale}]
                    if passing and (phrase + variation) % 3 == 1:
                        candidates = passing
            pitch = _choose(candidates, target, previous_lead, True)
            revised = dict(event)
            revised["midi"] = pitch
            if isinstance(revised.get("velocity"), (int, float)):
                revised["velocity"] = min(127, max(1, int(round(revised["velocity"] * 1.10))))
            if isinstance(revised.get("duration_beats"), (int, float)):
                revised["duration_beats"] = max(0.55, float(revised["duration_beats"]))
            modified[index] = revised
            previous_lead = pitch

        # This SFZ is a recorded brush *stir*, not a short snare strike.
        # Multiple one-shot tails in close succession create a hissy wall.
        # Preserve intentional brushes, but never stack them every beat.
        for index, event in keyed.get(("SNARE", bar), []):
            beat = float(event.get("start_beat", 0))
            gap = 2.0 * meter if section in ("INTRO", "MAIN_A", "ENDING") else meter
            if beat - previous_brush_beat < gap:
                suppressed.add(index)
                continue
            if (bar + variation) % 2 == 0 and section == "INTRO":
                suppressed.add(index)
                continue
            previous_brush_beat = beat

    arranged = [modified.get(i, dict(event)) for i, event in enumerate(events)
                if i not in suppressed]
    arranged.sort(key=lambda e: (
        float(e.get("start_beat", 0.0)),
        str(e.get("track_id", "")),
        int(e.get("midi", 0) or 0),
    ))
    return arranged
