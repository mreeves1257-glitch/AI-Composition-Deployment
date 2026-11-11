"""Resolve an existing percussion player's explicit stroke intent to recorded SFZ layers.

There is no new synthesis, sound source, vendor language, genre shortcut, or
randomized humanization. SFZ already chooses recorded velocity layers and
round-robin samples. This bridge just translates SUPPORTED musical dynamic
intent to exact velocity ranges of a selected existing patch.

The function is pure and is NOT connected to the active Composer by default.
Unsupported/unknown intents or sources are not fabricated. Ordinary notes and
their original velocities are preserved exactly.
"""
from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Iterable

MAP_PATH = Path(__file__).with_name("recorded_percussion_performance_map.json")
STROKE_TAGS = {"ghost_note":0.0, "soft_hit":0.25, "accent_hit":0.80, "strong_hit":1.0}
DYNAMICS = {"ppp":0.0, "pp":0.1, "p":0.25, "mp":0.40,
            "mf":0.6, "f":0.8, "ff":1.0}
MAX_NOTES = 20000


class UnsupportedPercussionGesture(ValueError):
    """The requested dynamic cannot be safely sent to the selected SFZ."""


def load_map(path: Path = MAP_PATH) -> dict:
    doc = json.loads(path.read_text(encoding="utf-8"))
    if doc["schema_version"] != 1 or doc["automatic_application_enabled"]:
        raise UnsupportedPercussionGesture("PERCUSSION_MAP_SCHEMA_OR_GATE_MISMATCH")
    return doc


def _selected_level(note) -> float | None:
    art = getattr(note, "articulation", None)
    dyn = getattr(note, "dynamic", None)
    if art in STROKE_TAGS:
        return STROKE_TAGS[art]
    # Recognized, intentional handwritten articulation always wins. Do not
    # override its chosen note velocity with a generic dynamic-level mapping.
    if art not in (None, ""):
        return None
    if isinstance(dyn, str) and dyn in DYNAMICS:
        return DYNAMICS[dyn]
    return None


def _choose_velocity(ranges: list[list[int]], level: float) -> int:
    if not 0 <= level <= 1:
        raise UnsupportedPercussionGesture("BAD_DYNAMIC_INTENSITY")
    if not ranges or any(len(item) != 2 for item in ranges):
        raise UnsupportedPercussionGesture("BAD_VELOCITY_LAYER_MAP")
    index = min(len(ranges)-1, max(0, round(level*(len(ranges)-1))))
    low, high = ranges[index]
    if not 1 <= low <= high <= 127:
        raise UnsupportedPercussionGesture("BAD_MIDI_VELOCITY_RANGE")
    return (low+high)//2


def interpret_recorded_percussion(
    notes: Iterable[object],
    resolved_resources: Iterable[dict],
    *,
    enabled: bool = False,
    manifest: dict | None = None,
) -> tuple[object, ...]:
    """Change ONLY velocity on notes with explicit supported playing intent.

    The sound program and instrument must match exactly. The source event
    objects and unresolved/ordinary musical events are not mutated.
    """
    notes = tuple(notes)
    if not enabled:
        return notes
    if len(notes) > MAX_NOTES:
        raise UnsupportedPercussionGesture("TOO_MANY_EVENTS")
    doc = manifest if manifest is not None else load_map()
    if doc.get("schema_version") != 1:
        raise UnsupportedPercussionGesture("UNVERIFIED_PERCUSSION_MAP")
    programs = doc.get("programs")
    if not isinstance(programs, dict):
        raise UnsupportedPercussionGesture("MISSING_PROGRAM_MAP")
    by_track = {}
    for item in resolved_resources:
        if not isinstance(item, dict) or "track_id" not in item:
            raise UnsupportedPercussionGesture("UNRESOLVED_TRACK_DATA")
        track = str(item["track_id"])
        if track in by_track:
            raise UnsupportedPercussionGesture("AMBIGUOUS_PERCUSSION_TRACK")
        by_track[track] = item
    output = []
    for note in notes:
        level = _selected_level(note)
        if level is None or getattr(note, "midi_note", None) is None:
            output.append(note)
            continue
        track = str(note.track_id)
        selected = by_track.get(track)
        if not isinstance(selected, dict):
            raise UnsupportedPercussionGesture("STROKE_HAS_NO_RESOLVED_INSTRUMENT")
        resource = selected.get("resource")
        if not isinstance(resource, dict) or resource.get("resource_type") != "SFZ_SAMPLE_LIBRARY":
            raise UnsupportedPercussionGesture("STROKE_NOT_RECORDED_SFZ")
        options = [
            p for p in programs.values()
            if (p["resource_id"] == resource.get("resource_id")
                and p["preferred_mapping"] == resource.get("preferred_mapping")
                and note.instrument_id in p["instrument_ids"]
                and selected.get("instrument_id") in p["instrument_ids"]
                and int(note.midi_note) in p["allowed_midi_notes"])
        ]
        if len(options) != 1:
            raise UnsupportedPercussionGesture("UNVERIFIED_INSTRUMENT_STROKE_MAPPING")
        velocity = _choose_velocity(options[0]["velocity_layer_ranges"],level)
        output.append(replace(note, velocity=velocity))
    return tuple(output)
