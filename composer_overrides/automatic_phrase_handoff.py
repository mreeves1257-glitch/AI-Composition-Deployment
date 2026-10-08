"""Connect conservative phrase decisions to the proven MIDI interpreter.

No user-facing controls. The Composer-only gate (AI_COMP_AUTO_PHRASING_V1=1)
is OFF by default and has no effect on production without explicit enablement.
Genre family stage routes remain inactive.

An independently authored note articulation always takes precedence. Each
automatically eligible track is checked against the actual TARGET-selected SFZ
program, not genre or name guesswork. Unsupported/missing sound resources
remain unchanged rather than silently pretending to vibrate.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Iterable

from instrument_gesture_handoff import route_explicit_note_gestures
from phrase_expression_decisions import decide_phrase_end_vibrato

CAPABILITIES = Path(__file__).with_name("performance_capabilities.json")


class AutomaticPhraseRoutingError(ValueError):
    pass


def _has_auto_permission() -> bool:
    return os.environ.get("AI_COMP_AUTO_PHRASING_V1", "") == "1"


def route_performance_intentions(
    notes: Iterable[object],
    resolved_resources: Iterable[dict],
    original_metadata: Iterable[tuple[str, str]],
) -> tuple[tuple[str, str], ...]:
    notes = tuple(notes)
    resolved_resources = tuple(resolved_resources)
    base = route_explicit_note_gestures(notes, resolved_resources, original_metadata)
    if not _has_auto_permission():
        return base
    try:
        caps = json.loads(CAPABILITIES.read_text(encoding="utf-8"))
        if caps["schema_version"] != 1 or not isinstance(caps["entries"], dict):
            raise AutomaticPhraseRoutingError("INVALID_AUTO_CAPABILITY_SCHEMA")
    except (OSError, KeyError, TypeError, ValueError) as exc:
        raise AutomaticPhraseRoutingError("AUTO_CAPABILITY_MANIFEST_MISSING") from exc

    existing = [value for key, value in base if key == "expressive_gesture_plan"]
    if len(existing) > 1:
        raise AutomaticPhraseRoutingError("DUPLICATE_GESTURE_PLANS")
    try:
        plans = json.loads(existing[0]) if existing else {}
    except (TypeError, ValueError) as exc:
        raise AutomaticPhraseRoutingError("INVALID_EXISTING_GESTURE_PLAN") from exc
    if not isinstance(plans, dict):
        raise AutomaticPhraseRoutingError("EXISTING_GESTURE_PLAN_NOT_OBJECT")
    plans = dict(plans)

    eligible_notes_by_track = {}
    for note in notes:
        if getattr(note, "midi_note", None) is not None:
            eligible_notes_by_track.setdefault(str(note.track_id), []).append(note)

    # Build an exact source lookup rather than treating a MIDI/instrument name
    # as proof of the selected sound or an authorization for expressive CCs.
    by_track = {}
    for item in resolved_resources:
        if not isinstance(item, dict) or "track_id" not in item:
            raise AutomaticPhraseRoutingError("MALFORMED_TARGET_RESOURCE")
        track = str(item["track_id"])
        if track in by_track:
            raise AutomaticPhraseRoutingError("DUPLICATE_TARGET_TRACK:" + track)
        by_track[track] = item

    changed = False
    for track, track_notes in sorted(eligible_notes_by_track.items()):
        if track in plans:  # explicit instruction wins, no added gestures
            continue
        target = by_track.get(track)
        if not isinstance(target, dict):
            continue
        resource = target.get("resource")
        if not isinstance(resource, dict) or resource.get("resource_type") != "SFZ_SAMPLE_LIBRARY":
            continue
        instrument_ids = {str(n.instrument_id) for n in track_notes}
        if len(instrument_ids) != 1 or str(target.get("instrument_id", "")) not in instrument_ids:
            continue
        choices = [
            (name, cap) for name, cap in caps["entries"].items()
            if resource.get("resource_id") == cap.get("resource_id")
            and resource.get("preferred_mapping") == cap.get("preferred_mapping")
            and instrument_ids.issubset(set(cap.get("instrument_ids", [])))
            and cap.get("note_mode") == "monophonic_expressive_gestures_only"
        ]
        if len(choices) != 1:
            continue
        capability_id, capability = choices[0]
        gestures = decide_phrase_end_vibrato(track_notes, capability, ppq=480)
        if not gestures:
            continue
        plans[track] = {
            "capability_id": capability_id,
            "resource_id": capability["resource_id"],
            "preferred_mapping": capability["preferred_mapping"],
            "gestures": gestures,
        }
        changed = True
    if not changed:
        return base
    if existing:
        # The existing explicit plan must be unique and preserved by content.
        other = tuple((key, val) for key, val in base if key != "expressive_gesture_plan")
    else:
        other = base
    return other + (("expressive_gesture_plan", json.dumps(
        plans, sort_keys=True, separators=(",", ":")
    )),)
