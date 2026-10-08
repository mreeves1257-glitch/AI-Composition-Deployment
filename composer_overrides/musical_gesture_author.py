"""Translate named musical-note intent into target-program expressive controls.

An opt-in, genre-neutral preparatory layer. It never creates notes, guesses
instrument articulations, or silently reassigns a different sound bank.
Only explicit note articulation 'sustained_vibrato' is supported in V1, on a
capability that declares that gesture and its timing.
"""
from __future__ import annotations

from fractions import Fraction
from typing import Iterable


class GestureAuthorError(ValueError):
    """A source instrument cannot safely perform the requested note gesture."""


def _as_fraction(value: object) -> Fraction:
    try:
        return Fraction(str(value))
    except (TypeError, ValueError, ZeroDivisionError) as exc:
        raise GestureAuthorError("INVALID_MUSICAL_EVENT_BEATS") from exc


def author_from_note_articulations(
    notes: Iterable[object], capability: dict, *, ppq: int
) -> list[dict]:
    """Return source-native named MIDI gestures, not raw MIDI or genre logic.

    The exact source capability manifest provides the supported vocabulary,
    modulation value and timing fractions. A note without a recognized explicit
    articulation is unchanged, not given generic randomness or vibrato.
    """
    if isinstance(ppq, bool) or not isinstance(ppq, int) or ppq <= 0:
        raise GestureAuthorError("INVALID_GESTURE_AUTHOR_PPQ")
    template = capability.get("gesture_templates", {}).get("sustained_vibrato")
    if not isinstance(template, dict) or template.get("control") != "vibrato_depth":
        raise GestureAuthorError("INSTRUMENT_HAS_NO_AUTHORABLE_VIBRATO")
    minimum = _as_fraction(template["minimum_note_beats"])
    delay = _as_fraction(template["delay_fraction_of_note"])
    end_gap = _as_fraction(template["release_fraction_of_note"])
    if not (minimum > 0 and 0 < delay < 1 and 0 < end_gap < 1 and delay+end_gap < 1):
        raise GestureAuthorError("INVALID_INSTRUMENT_GESTURE_TEMPLATE")
    on_value = template["on_value"]
    if isinstance(on_value, bool) or not isinstance(on_value, int):
        raise GestureAuthorError("INVALID_INSTRUMENT_ON_VALUE")
    note_info = []
    for note in notes:
        if getattr(note, "midi_note", None) is None:
            continue
        start = _as_fraction(note.start_beats)
        duration = _as_fraction(note.duration_beats)
        if start < 0 or duration <= 0:
            raise GestureAuthorError("INVALID_NOTE_DURATION_OR_START")
        note_info.append((start, start+duration, str(getattr(note,"articulation",None) or ""),note))
    note_info.sort(key=lambda item:item[0])
    gestures=[]
    active = [r for r in note_info if r[2] == "sustained_vibrato"]
    if not active:
        return []
    # MIDI CC1 is channel-wide. Reject any potentially sounding overlapping
    # notes, not only overlaps at command-event timestamps.
    for (_,prev_end,_,_), (next_start,_,_,_) in zip(note_info,note_info[1:]):
        if prev_end > next_start:
            raise GestureAuthorError("CHANNEL_POLYPHONY_NOT_SUPPORTED_FOR_VIBRATO")
    for start,end,art,_ in active:
        duration=end-start
        if duration < minimum:
            raise GestureAuthorError("NOTE_TOO_SHORT_FOR_SUSTAINED_VIBRATO")
        # Quantize to MIDI-tick grid and avoid identical tick collisions.
        ticks=sorted({
            round(float(start*ppq)),
            round(float((start+duration*delay)*ppq)),
            round(float((end-duration*end_gap)*ppq)),
        })
        if len(ticks)!=3:
            raise GestureAuthorError("NOTE_TOO_SHORT_FOR_GESTURE_RESOLUTION")
        # The explicit off/on/off pattern is a physical intention: enter
        # the note with no LFO, introduce delayed vibrato, then settle.
        for tick,value in zip(ticks,(0,on_value,0)):
            gestures.append({
                "at_beat":str(Fraction(tick,ppq)),
                "control":template["control"],
                "value":value,
            })
    return gestures
