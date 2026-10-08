"""Translate EXPLICIT musical gestures into source-mapped, timed MIDI controls.

This is one independently testable output boundary, not a Yamaha/Korg clone,
an automatic 'humanize' effect or an activated genre route.

Input: CompositionExecutionPackage.metadata element
  ("expressive_gesture_plan", JSON object mapping track ids to:
     {"capability_id": "SHINYGUITAR_RECORDED_LEAD_CC1_V1",
      "resource_id": "KARORYFER_SHINYGUITAR",
      "preferred_mapping": "Programs/composer-electric-lead.sfz",
      "gestures": [{"at_beat": "0", "control": "vibrato_depth", "value": 0},
                   {"at_beat": "1/2", "control": "vibrato_depth", "value": 88}]})

No plan = absolutely no change. The only supported patch is whitelisted by
the committed capability manifest and validated against per-track instrument
identity. A vibrato_depth change acts on the selected MIDI CHANNEL, not one
note; overlapping notes are rejected rather than receiving unintended bends.
Actual audio response still requires separate sfizz testing and listening.
"""
from __future__ import annotations

import json
import math
from fractions import Fraction
from pathlib import Path
from typing import Iterable


MANIFEST = Path(__file__).with_name("performance_capabilities.json")
MAX_GESTURES_PER_TRACK = 256


class PerformanceGestureError(ValueError):
    """The requested MIDI message is unsupported by this exact target."""


def _fraction(value: object) -> Fraction:
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise PerformanceGestureError("GESTURE_BEAT_INVALID")
    if isinstance(value, float) and not math.isfinite(value):
        raise PerformanceGestureError("GESTURE_BEAT_NOT_FINITE")
    try:
        val = Fraction(str(value))
    except (ValueError, ZeroDivisionError, OverflowError) as exc:
        raise PerformanceGestureError("GESTURE_BEAT_INVALID") from exc
    if val < 0 or val > 100000:
        raise PerformanceGestureError("GESTURE_BEAT_OUT_OF_RANGE")
    return val


def _one_json_metadata(metadata: Iterable[tuple[str, str]], key: str) -> object | None:
    values = [value for name, value in metadata if name == key]
    if not values:
        return None
    if len(values) != 1:
        raise PerformanceGestureError("DUPLICATE_" + key.upper())
    try:
        return json.loads(values[0])
    except (TypeError, ValueError) as exc:
        raise PerformanceGestureError("INVALID_" + key.upper() + "_JSON") from exc


def _note_intervals(track_events: Iterable[object], ppq: int) -> list[tuple[int, int]]:
    intervals = []
    for note in track_events:
        if getattr(note, "midi_note", None) is None:
            continue
        onset = round(float(note.start_beats * ppq))
        finish = max(onset + 1, round(float((note.start_beats + note.duration_beats) * ppq)))
        intervals.append((onset, finish))
    return intervals


def append_expressive_gestures(
    midi_events: list[tuple[int, int, bytes]],
    metadata: Iterable[tuple[str, str]],
    track_id: str,
    channel: int,
    ppq: int,
    track_events: Iterable[object],
) -> list[tuple[int, int, bytes]]:
    """Add supported time-varying CCs before Note On/Off at their exact beat.

    Existing notes, durations, channels, tempo, initial MIDI controls and
    routing remain untouched. All requested controls must be explicitly
    authorized by the exact SFZ-program capability manifest.
    """
    plan = _one_json_metadata(metadata, "expressive_gesture_plan")
    if plan is None:
        return list(midi_events)
    if not isinstance(plan, dict):
        raise PerformanceGestureError("GESTURE_PLAN_MUST_BE_OBJECT")
    selection = plan.get(str(track_id))
    if selection is None:
        return list(midi_events)
    if not isinstance(selection, dict):
        raise PerformanceGestureError("GESTURE_TRACK_MUST_BE_OBJECT")
    if isinstance(channel, bool) or not isinstance(channel, int) or not 0 <= channel <= 15:
        raise PerformanceGestureError("INVALID_MIDI_CHANNEL")
    if isinstance(ppq, bool) or not isinstance(ppq, int) or ppq <= 0:
        raise PerformanceGestureError("INVALID_PPQ")
    cap_id = selection.get("capability_id")
    if not isinstance(cap_id, str):
        raise PerformanceGestureError("MISSING_INSTRUMENT_CAPABILITY")
    try:
        caps = json.loads(MANIFEST.read_text(encoding="utf-8"))
        cap = caps["entries"][cap_id]
    except (KeyError, TypeError, OSError, ValueError) as exc:
        raise PerformanceGestureError("UNKNOWN_OR_UNREADABLE_CAPABILITY") from exc
    if caps.get("schema_version") != 1:
        raise PerformanceGestureError("UNSUPPORTED_CAPABILITY_SCHEMA")
    for name in ("resource_id", "preferred_mapping"):
        if selection.get(name) != cap.get(name):
            raise PerformanceGestureError("CAPABILITY_RESOURCE_MISMATCH_" + name.upper())
    notes = list(track_events)
    instrument_ids = {note.instrument_id for note in notes if getattr(note, "midi_note", None) is not None}
    if not instrument_ids or not instrument_ids.issubset(set(cap["instrument_ids"])):
        raise PerformanceGestureError("CAPABILITY_INSTRUMENT_MISMATCH")
    if cap.get("note_mode") != "monophonic_expressive_gestures_only":
        raise PerformanceGestureError("UNSUPPORTED_CHANNEL_NOTE_MODE")
    gestures = selection.get("gestures", [])
    if not isinstance(gestures, list) or len(gestures) > MAX_GESTURES_PER_TRACK:
        raise PerformanceGestureError("INVALID_GESTURE_COLLECTION")
    intervals = _note_intervals(notes, ppq)
    result = list(midi_events)
    emitted = set()
    for g in gestures:
        if not isinstance(g, dict) or set(g) != {"at_beat", "control", "value"}:
            raise PerformanceGestureError("INVALID_GESTURE_FIELDS")
        control = cap["supported_controls"].get(g["control"])
        if control is None or control.get("message") != "control_change":
            raise PerformanceGestureError("CONTROL_NOT_SUPPORTED_BY_INSTRUMENT")
        tick = round(float(_fraction(g["at_beat"]) * ppq))
        value = g["value"]
        lower, upper = control["value_range"]
        if isinstance(value, bool) or not isinstance(value, int) or not lower <= value <= upper:
            raise PerformanceGestureError("CONTROL_VALUE_NOT_SUPPORTED")
        cc = control["controller"]
        if isinstance(cc, bool) or not isinstance(cc, int) or not 0 <= cc <= 127:
            raise PerformanceGestureError("INVALID_CAPABILITY_CC")
        sounding = sum(onset <= tick < end for onset, end in intervals)
        # A reset to zero is allowed exactly at a note end, so the LFO does
        # not persist into another phrase. Nonzero controls require one note.
        at_release = value == 0 and any(tick == end for _, end in intervals)
        if sounding != 1 and not (sounding == 0 and at_release):
            raise PerformanceGestureError("TIMED_CONTROL_REQUIRES_ONE_SOUNDING_NOTE")
        token = (tick, cc)
        if token in emitted:
            raise PerformanceGestureError("DUPLICATE_CONTROLLER_AT_TICK")
        emitted.add(token)
        result.append((tick, -1, bytes((0xB0 | channel, cc, value))))
    # Stable sort makes configured initial CC at tick 0 appear before a
    # deliberate gesture at tick 0; all controls precede note-on.
    return sorted(result, key=lambda event: (event[0], event[1]))
