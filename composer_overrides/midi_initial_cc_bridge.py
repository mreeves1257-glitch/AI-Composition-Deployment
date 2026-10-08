"""Transfer explicitly specified, instrument-native initial MIDI controls.

Only reads 'midi_routing' metadata, written by the existing output_handoff from
the target instrument's midi_mapping. Does not infer or fabricate CCs from
articulation labels, change notes/timing, or replace recorded instruments.

This module is separate from the preserved Output Core source.
"""
from __future__ import annotations

import json
from typing import Iterable


class MidiControlContractError(ValueError):
    """An instrument explicitly asked for a malformed controller message."""


def append_initial_cc(
    note_events: list[tuple[int, int, bytes]],
    metadata: Iterable[tuple[str, str]],
    track_id: str,
    channel: int = 0,
) -> list[tuple[int, int, bytes]]:
    """Insert MIDI CC at tick zero, before Note On, for this exact track.

    A MIDI CC is (B0 + channel) <controller 0..127> <value 0..127>.
    The Output Core assigns MIDI channels to tracks. Preserve that channel
    for every inserted instrument control, including the combined MIDI file.

    Existing note-off order (0) and note-on order (1) are unchanged.
    Controller priority (-1) ensures SFZ controls are initialized first.
    """
    if isinstance(channel, bool) or not isinstance(channel, int) or not 0 <= channel <= 15:
        raise MidiControlContractError("INVALID_MIDI_CHANNEL")
    routing_values = [v for k, v in metadata if k == "midi_routing"]
    if not routing_values:
        return list(note_events)
    if len(routing_values) != 1:
        raise MidiControlContractError("MULTIPLE_MIDI_ROUTING_RECORDS")
    try:
        routing = json.loads(routing_values[0])
    except (ValueError, TypeError) as exc:
        raise MidiControlContractError("INVALID_MIDI_ROUTING_JSON") from exc
    if not isinstance(routing, dict):
        raise MidiControlContractError("MIDI_ROUTING_MUST_BE_OBJECT")
    selected = routing.get(str(track_id), {})
    if not isinstance(selected, dict):
        raise MidiControlContractError("TRACK_MIDI_ROUTING_MUST_BE_OBJECT")
    cc = selected.get("initial_cc", {})
    if cc is None:
        return list(note_events)
    if not isinstance(cc, dict):
        raise MidiControlContractError("INITIAL_CC_MUST_BE_OBJECT")

    events = list(note_events)
    for controller, value in cc.items():
        # Reject booleans, floats, negatives, and values >127; do not silently
        # substitute a guessed or clamped control value.
        if isinstance(controller, bool) or not str(controller).isdigit():
            raise MidiControlContractError("INVALID_CC_NUMBER")
        number = int(controller)
        if (
            isinstance(value, bool) or not isinstance(value, int)
            or not 0 <= number <= 127 or not 0 <= value <= 127
        ):
            raise MidiControlContractError("INVALID_CC_VALUE_OR_NUMBER")
        events.append((0, -1, bytes((0xB0 | channel, number, value))))
    # Stable ordering preserves the target resource's explicit CC ordering for
    # initialization; never reorder different CCs by their numeric ID.
    return sorted(events, key=lambda event: (event[0], event[1]))
