"""Conservative, instrument-aware AUTOMATIC phrase-end expression policy V1.

This decides *when* an expressive gesture would be appropriate; the existing
musical_gesture_author decides *how* that gesture maps into native MIDI. A
musical decision is not a random "humanize" value.

V1 works only on a source-verified monophonic sustained lead program with a
proven vibrato template. Never infers bends, slides, drum dynamics or alternate
sound-library articulations. Original composed note events are not modified.

Policy is intentionally gated at the Composer output handoff: development
verification may enable it explicitly, but the 55 genre-family stages and
ordinary deployed song playback are unchanged until a separate enablement.
"""
from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
from typing import Iterable

from musical_gesture_author import (
    GestureAuthorError,
    author_from_note_articulations,
)


class AutomaticPhrasingError(ValueError):
    """An automatic phrase would not be safe for the selected instrument."""


# Fixed, documented *heuristic*, not a proven model of human performance.
MIN_SUSTAIN_BEATS = Fraction(2, 1)
MIN_PHRASE_BREAK_BEATS = Fraction(1, 4)
MAX_AUTOMATED_PHRASE_ENDINGS = 16


def decide_phrase_end_vibrato(
    events: Iterable[object], capability: dict, *, ppq: int
) -> list[dict]:
    """Return well-bounded MIDI gesture intentions for eligible phrase endings.

    Eligibility rules:
    - source is the exact compatible monophonic lead SFZ capability
    - no note has ANY existing explicit articulation (composer/player intent wins)
    - no overlapping notes or simultaneous independent voices
    - sustained notes must last at least two beats
    - note must be the last one or followed by a real rest >= a quarter beat
    - no more than 16 phrase endings per track; deterministic, no randomness
    - when ineligible return [] and do not touch note pitches, rhythm, dynamics

    Only emits existing, tested 'sustained_vibrato' through the note gesture
    author. It does not copy or implement Yamaha or Korg proprietary systems.
    """
    if capability.get("note_mode") != "monophonic_expressive_gestures_only":
        return []
    if "sustained_vibrato" not in capability.get("gesture_templates", {}):
        return []
    if isinstance(ppq, bool) or not isinstance(ppq, int) or ppq <= 0:
        raise AutomaticPhrasingError("INVALID_MIDI_PPQ")
    notes = [e for e in events if getattr(e, "midi_note", None) is not None]
    if not notes:
        return []
    # Respect all existing authored articulations, even ones V1 doesn't
    # understand. Never overlay arbitrary automatic effects on manual intent.
    if any(getattr(e, "articulation", None) not in (None, "") for e in notes):
        return []
    try:
        spans = sorted(
            ((Fraction(str(e.start_beats)), Fraction(str(e.duration_beats)), e)
             for e in notes),
            key=lambda triple: (triple[0], triple[1]),
        )
    except (ValueError, TypeError, ZeroDivisionError) as exc:
        raise AutomaticPhrasingError("INVALID_NOTE_BEAT") from exc
    if any(start < 0 or duration <= 0 for start,duration,_ in spans):
        raise AutomaticPhrasingError("INVALID_NOTE_SPAN")
    if any(
        start + duration > next_start
        for (start, duration, _), (next_start, _, _) in zip(spans, spans[1:])
    ):
        return []  # A polyphonic or overlapping track cannot use channel CC1.
    candidates = []
    for index, (start, duration, event) in enumerate(spans):
        if duration < MIN_SUSTAIN_BEATS:
            continue
        next_start = spans[index + 1][0] if index + 1 < len(spans) else None
        if next_start is not None and (
            next_start - (start + duration) < MIN_PHRASE_BREAK_BEATS
        ):
            continue
        candidates.append(event)
    if not candidates:
        return []
    # Bound the time-varying channel messages to avoid unwanted CC floods;
    # preferentially preserve endings at the very end of the composed track.
    eligible_ids = {id(e) for e in candidates[-MAX_AUTOMATED_PHRASE_ENDINGS:]}
    virtual_events = [
        replace(e, articulation="sustained_vibrato") if id(e) in eligible_ids else e
        for _,_,e in spans
    ]
    try:
        return author_from_note_articulations(virtual_events, capability, ppq=ppq)
    except (GestureAuthorError, TypeError) as exc:
        raise AutomaticPhrasingError("PHRASE_GESTURE_AUTHOR_REJECTED:" + str(exc)) from exc
