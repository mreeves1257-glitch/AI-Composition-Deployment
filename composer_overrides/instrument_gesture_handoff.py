"""Route explicit performed-note gestures to the REAL resolved SFZ program.

This is a genre-independent output-handoff bridge. It reads only the existing
MusicalEvent articulation field and each track's resolved_resource from the
actual target module. It authorizes no controls unless a recognized explicit
note tag occurs AND the selected exact SFZ program matches a recorded, tested
capability.

It does not compose, infer genre playing, invent musical gestures, change
sample libraries or activate any of the 55 genre-family stages.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable


CAPABILITY_MANIFEST = Path(__file__).with_name("performance_capabilities.json")
EXPLICIT_TAGS = frozenset({"sustained_vibrato"})


class InstrumentGestureRoutingError(ValueError):
    """A note's requested articulation is not usable on its selected sound."""


def route_explicit_note_gestures(
    notes: Iterable[object],
    resolved_resources: Iterable[dict],
    original_metadata: Iterable[tuple[str, str]],
) -> tuple[tuple[str, str], ...]:
    """Return existing metadata verbatim unless an explicit expressive tag exists.

    Exact source/resource/program identity is verified from resolved_resources
    (not from a guessed genre or track name). MIDI data for a supported program
    is authored by the existing expressive_gesture_bridge, never here.
    """
    metadata = tuple(original_metadata)
    notes = tuple(notes)
    if not any(getattr(n, "articulation", None) in EXPLICIT_TAGS for n in notes):
        return metadata
    if any(key == "expressive_gesture_plan" for key, _ in metadata):
        raise InstrumentGestureRoutingError("EXPRESSIVE_METADATA_ALREADY_PRESENT")
    try:
        doc = json.loads(CAPABILITY_MANIFEST.read_text(encoding="utf-8"))
        if doc["schema_version"] != 1:
            raise InstrumentGestureRoutingError("UNRECOGNIZED_CAPABILITY_SCHEMA")
        entries = doc["entries"]
    except (OSError, KeyError, ValueError, TypeError) as exc:
        raise InstrumentGestureRoutingError("CAPABILITY_MANIFEST_UNAVAILABLE") from exc
    if not isinstance(entries, dict):
        raise InstrumentGestureRoutingError("CAPABILITY_MANIFEST_ENTRIES_INVALID")
    if not isinstance(resolved_resources, (tuple, list)):
        raise InstrumentGestureRoutingError("INVALID_RESOLVED_RESOURCES")

    by_track = {}
    for item in resolved_resources:
        if not isinstance(item, dict) or "track_id" not in item:
            raise InstrumentGestureRoutingError("MALFORMED_RESOLVED_RESOURCE")
        track = str(item["track_id"])
        if track in by_track:
            raise InstrumentGestureRoutingError("AMBIGUOUS_TRACK_RESOURCE:" + track)
        by_track[track] = item

    tagged_tracks = {str(note.track_id) for note in notes
                     if getattr(note, "articulation", None) in EXPLICIT_TAGS}
    selections = {}
    for track in sorted(tagged_tracks):
        item = by_track.get(track)
        if item is None:
            raise InstrumentGestureRoutingError("TRACK_RESOURCE_NOT_RESOLVED:" + track)
        resource = item.get("resource")
        if not isinstance(resource, dict) or resource.get("resource_type") != "SFZ_SAMPLE_LIBRARY":
            raise InstrumentGestureRoutingError("TRACK_REQUIRES_REAL_SFZ_RESOURCE:" + track)
        resource_id = resource.get("resource_id")
        preferred_mapping = resource.get("preferred_mapping")
        if not isinstance(resource_id, str) or not isinstance(preferred_mapping, str):
            raise InstrumentGestureRoutingError("TRACK_RESOURCE_IDENTITY_MISSING:" + track)

        track_notes = [n for n in notes if str(n.track_id) == track and
                       getattr(n, "midi_note", None) is not None]
        instrument_ids = {str(n.instrument_id) for n in track_notes}
        if len(instrument_ids) != 1:
            raise InstrumentGestureRoutingError("INCONSISTENT_TRACK_INSTRUMENT:" + track)
        requested_tag_set = {str(n.articulation) for n in track_notes
                             if getattr(n, "articulation", None) in EXPLICIT_TAGS}
        if requested_tag_set != {"sustained_vibrato"}:
            raise InstrumentGestureRoutingError("UNKNOWN_EXPRESSIVE_NOTE_TAG:" + track)

        candidates = [
            (name, entry) for name, entry in entries.items()
            if (entry.get("resource_id") == resource_id and
                entry.get("preferred_mapping") == preferred_mapping and
                instrument_ids.issubset(set(entry.get("instrument_ids", []))) and
                entry.get("note_mode") == "monophonic_expressive_gestures_only" and
                requested_tag_set.issubset(set(entry.get("gesture_templates", {}))))
        ]
        if len(candidates) != 1:
            raise InstrumentGestureRoutingError(
                "NO_UNIQUE_VERIFIED_ARTICULATION_MAPPING:" + track
            )
        capability_id, capability = candidates[0]
        # Check the chosen target item identifies the same actual instrument
        # as its notes, with an explicitly registered alias (if applicable).
        target_instrument = str(item.get("instrument_id", ""))
        if target_instrument not in capability["instrument_ids"]:
            raise InstrumentGestureRoutingError(
                "RESOLVED_INSTRUMENT_ID_MISMATCH:" + track
            )
        selections[track] = {
            "capability_id": capability_id,
            "resource_id": resource_id,
            "preferred_mapping": preferred_mapping,
            "gesture_source": "note_articulation",
        }
    if not selections:
        return metadata
    return metadata + (("expressive_gesture_plan", json.dumps(
        selections, sort_keys=True, separators=(",", ":")
    )),)
