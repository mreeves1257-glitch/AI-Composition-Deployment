"""Opt-in interpreter event boundary; legacy genre event generation is untouched.

The interpreter supplies real note/percussion events for every declared part.
No notes are invented, no fixed palette is read, and no silent substitution occurs.
"""
from universal_arrangement_handoff import validate_interpreter_arrangement, ArrangementHandoffError

class InterpreterEventError(ValueError): pass

def validate_interpreter_events(genre, musical_plan, available_instruments):
    validated = validate_interpreter_arrangement(genre, musical_plan, available_instruments)
    events = musical_plan.get("events")
    if not isinstance(events, (list, tuple)) or not events:
        raise InterpreterEventError("INTERPRETER_EVENTS_REQUIRED")
    ids = {part["part_id"] for part in validated.instrument_roles}
    expected = {part["part_id"]: part["instrument_id"] for part in validated.instrument_roles}
    seen = set()
    checked = []
    for event in events:
        if not isinstance(event, dict):
            raise InterpreterEventError("EVENT_MUST_BE_OBJECT")
        part = event.get("track_id")
        if part not in ids:
            raise InterpreterEventError("UNDECLARED_PART: " + str(part))
        if event.get("instrument_id") != expected[part]:
            raise InterpreterEventError("INSTRUMENT_MISMATCH: " + str(part))
        for key in ("start_beat", "duration_beats", "midi", "velocity"):
            value = event.get(key)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise InterpreterEventError("INVALID_EVENT_FIELD: " + key)
        if event["start_beat"] < 0 or event["duration_beats"] <= 0:
            raise InterpreterEventError("INVALID_EVENT_TIMING")
        if not 0 <= event["midi"] <= 127 or not 0 <= event["velocity"] <= 127:
            raise InterpreterEventError("INVALID_MIDI_VALUE")
        seen.add(part)
        checked.append(dict(event))
    missing = ids - seen
    if missing:
        raise InterpreterEventError("SILENT_PARTS: " + ",".join(sorted(missing)))
    return checked

def execute_interpreter_events(genre, musical_plan, available_instruments, renderer, *, creation_seed):
    """Calls the supplied renderer only after complete event coverage validation."""
    events = validate_interpreter_events(genre, musical_plan, available_instruments)
    if not callable(renderer):
        raise InterpreterEventError("RENDERER_REQUIRED")
    return renderer(events, musical_plan=musical_plan, creation_seed=creation_seed)
