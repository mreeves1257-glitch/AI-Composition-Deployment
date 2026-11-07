"""Execute V3-governed original source-pattern seeds as symbolic events.

Diagnostic branch only.
- Uses current Genre Contract V3 as authority.
- Uses only the project's original authored source-pattern vocabulary.
- Requires complete current-instrument role resolution.
- Produces typed symbolic events, never audio.
- Does not invoke the experimental reasoning engine.
"""
from __future__ import annotations

from bisect import bisect_right
from fractions import Fraction
from pathlib import Path
import hashlib
import json
import re
from typing import Any

from genre_contract_v3_execution_bridge import snapshot_for
from genre_v3_source_pattern_bridge import load_seed, resolve_source_roles

SCHEMA = "GENRE_V3_SYMBOLIC_PATTERN_EXECUTION_001"
CHORD_RE = re.compile(
    r"^([A-G])([#b]?)(maj7|m7|sus4|dim|aug|m|7)?(?:/([A-G])([#b]?))?$"
)
ROOT_PC = {"C":0,"D":2,"E":4,"F":5,"G":7,"A":9,"B":11}
ACC = {"":0,"#":1,"b":-1}
SCALES = {
    "": (0,2,4,5,7,9,11),
    "7": (0,2,4,5,7,9,10),
    "maj7": (0,2,4,5,7,9,11),
    "m": (0,2,3,5,7,8,10),
    "m7": (0,2,3,5,7,9,10),
    "sus4": (0,2,5,5,7,9,10),
    "dim": (0,2,3,5,6,8,9),
    "aug": (0,2,4,5,8,9,11),
}


class GenreV3SymbolicExecutionError(RuntimeError):
    pass


def _sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()


def _fraction(value: Any, field: str) -> Fraction:
    if isinstance(value, bool):
        raise GenreV3SymbolicExecutionError("INVALID_" + field)
    try:
        out = Fraction(str(value))
    except (TypeError, ValueError, ZeroDivisionError) as exc:
        raise GenreV3SymbolicExecutionError("INVALID_" + field) from exc
    if out.denominator > 1920:
        raise GenreV3SymbolicExecutionError("UNSUPPORTED_" + field + "_GRID")
    return out


def _beats_per_bar(meter: str) -> Fraction:
    try:
        numerator, denominator = map(int, str(meter).split("/"))
    except Exception as exc:
        raise GenreV3SymbolicExecutionError("INVALID_METER") from exc
    if numerator <= 0 or denominator not in (2,4,8,16):
        raise GenreV3SymbolicExecutionError("INVALID_METER")
    return Fraction(numerator * 4, denominator)


def _parse_chord(symbol: str) -> dict[str, Any]:
    match = CHORD_RE.fullmatch(str(symbol))
    if match is None:
        raise GenreV3SymbolicExecutionError("UNSUPPORTED_CHORD_SYMBOL::" + str(symbol))
    root, accidental, quality, bass_root, bass_acc = match.groups()
    quality = quality or ""
    if quality not in SCALES:
        raise GenreV3SymbolicExecutionError("UNSUPPORTED_CHORD_QUALITY::" + quality)
    root_pc = (ROOT_PC[root] + ACC[accidental]) % 12
    slash_bass_pc = (
        None if bass_root is None
        else (ROOT_PC[bass_root] + ACC[bass_acc]) % 12
    )
    return {
        "symbol": symbol,
        "root_pc": root_pc,
        "quality": quality,
        "slash_bass_pc": slash_bass_pc,
    }


def _tempo(genre_name: str, seed: dict[str, Any], selected_tempo_bpm: int | None) -> int:
    snapshot = snapshot_for(genre_name)
    lo, hi = [int(x) for x in snapshot.get("tempo_bpm_range", [])[:2]]
    value = int(seed["tempo_bpm"] if selected_tempo_bpm is None else selected_tempo_bpm)
    if not lo <= value <= hi:
        raise GenreV3SymbolicExecutionError(
            f"SELECTED_TEMPO_OUTSIDE_V3::{genre_name}::{value}"
        )
    return value



def parse_chord(symbol: str) -> dict[str, Any]:
    """Public read-only chord parser for V3 symbolic scheduling layers."""
    return dict(_parse_chord(symbol))


def realize_variation_bar(
    genre_name: str,
    *,
    variation_by_role: dict[str, str],
    chord_symbol: str,
    destination_bar: int,
    section_name: str,
) -> list[dict[str, Any]]:
    """Realize one approved source-pattern variation set on one approved chord.

    This is the scheduling primitive used by higher-level form compilers.
    It never chooses a variation, chord, section, instrument, or form on its own.
    """
    if type(destination_bar) is not int or destination_bar < 0:
        raise GenreV3SymbolicExecutionError("INVALID_DESTINATION_BAR")
    if not isinstance(variation_by_role, dict) or not variation_by_role:
        raise GenreV3SymbolicExecutionError("VARIATION_BY_ROLE_REQUIRED")
    if not section_name:
        raise GenreV3SymbolicExecutionError("SECTION_NAME_REQUIRED")

    seed = load_seed(genre_name)
    role_authority = resolve_source_roles(genre_name)
    if role_authority.get("status") != "PASS":
        raise GenreV3SymbolicExecutionError(
            "SOURCE_ROLE_MAPPING_NOT_READY::" + genre_name
        )

    meter = seed["meter"]
    beats_per_bar = _beats_per_bar(meter)
    chord = _parse_chord(chord_symbol)
    mappings = {x["role"]: x for x in role_authority["role_mappings"]}
    source_roles = {x["role"]: x for x in seed["roles"]}
    patterns = {x["role"]: x for x in seed["patterns"]}

    if set(variation_by_role) != set(source_roles):
        raise GenreV3SymbolicExecutionError(
            "VARIATION_ROLE_SET_MISMATCH::" + genre_name
        )

    events = []
    bar_start = Fraction(destination_bar) * beats_per_bar
    bar_end = bar_start + beats_per_bar

    for role_name, source_role in source_roles.items():
        mapping = mappings[role_name]
        pattern = patterns[role_name]
        variation = variation_by_role[role_name]
        variations = pattern.get("variations") or {}
        if variation not in variations:
            raise GenreV3SymbolicExecutionError(
                f"UNKNOWN_SOURCE_VARIATION::{genre_name}::{role_name}::{variation}"
            )

        for note in variations[variation]:
            offset = _fraction(note.get("beat"), "PATTERN_BEAT")
            duration = _fraction(note.get("duration"), "PATTERN_DURATION")
            if not (0 <= offset < beats_per_bar and duration > 0):
                raise GenreV3SymbolicExecutionError("PATTERN_TIMING_INVALID")
            start = bar_start + offset
            end = start + duration

            if pattern["kind"] == "CHORD_RELATIVE":
                degree = note.get("degree")
                octave = note.get("octave")
                if type(degree) is not int or not 1 <= degree <= 7:
                    raise GenreV3SymbolicExecutionError("INVALID_CHORD_DEGREE")
                if type(octave) is not int or not -1 <= octave <= 9:
                    raise GenreV3SymbolicExecutionError("INVALID_NOTE_OCTAVE")
                midi = (
                    (octave + 1) * 12
                    + chord["root_pc"]
                    + SCALES[chord["quality"]][degree - 1]
                )
                if pattern["retrigger"] == "STOP_AT_CHORD":
                    end = min(end, bar_end)
            elif pattern["kind"] == "DRUM_ABSOLUTE":
                midi = note.get("midi")
                if type(midi) is not int or not 0 <= midi <= 127:
                    raise GenreV3SymbolicExecutionError("INVALID_DRUM_MIDI")
                end = min(end, bar_end)
            else:
                raise GenreV3SymbolicExecutionError(
                    "PATTERN_KIND_NOT_SUPPORTED_BY_V3_EXECUTOR"
                )

            if end <= start or end > bar_end:
                raise GenreV3SymbolicExecutionError("EVENT_DURATION_OUTSIDE_BAR")

            playable = source_role.get("playable_midi_range")
            if (
                isinstance(playable, list)
                and len(playable) == 2
                and not (int(playable[0]) <= midi <= int(playable[1]))
            ):
                raise GenreV3SymbolicExecutionError(
                    f"EVENT_OUTSIDE_SOURCE_ROLE_RANGE::{genre_name}::{role_name}"
                )

            velocity = note.get("velocity")
            if type(velocity) is not int or not 1 <= velocity <= 127:
                raise GenreV3SymbolicExecutionError("INVALID_VELOCITY")

            event = {
                "track_id": role_name,
                "role": role_name,
                "instrument_id": mapping["instrument_id"],
                "source_instrument_id": mapping["source_instrument_id"],
                "instrument_mapping_kind": mapping["mapping_kind"],
                "start_beat": float(start),
                "duration_beats": float(end - start),
                "midi": int(midi),
                "velocity": int(velocity),
                "section": section_name,
                "variation": variation,
                "source_seed_id": seed["seed_id"],
                "source_pattern_kind": pattern["kind"],
                "source_rule": "V3_GOVERNED_ORIGINAL_SYMBOLIC_SOURCE_PATTERN_SCHEDULED",
                "scheduled_chord_symbol": chord_symbol,
                "destination_bar": destination_bar,
                "symbolic_only": True,
            }
            if mapping.get("performance_intent"):
                event["performance_intent"] = mapping["performance_intent"]
            events.append(event)

    events.sort(key=lambda x: (x["start_beat"], x["track_id"], x["midi"]))
    if {x["role"] for x in events} != set(source_roles):
        raise GenreV3SymbolicExecutionError(
            "SCHEDULED_BAR_SILENT_ROLE::" + genre_name
        )
    return events


def compile_seed(
    genre_name: str,
    *,
    selected_tempo_bpm: int | None = None,
) -> dict[str, Any]:
    seed = load_seed(genre_name)
    role_authority = resolve_source_roles(genre_name)
    if role_authority.get("status") != "PASS":
        raise GenreV3SymbolicExecutionError(
            "SOURCE_ROLE_MAPPING_NOT_READY::" + genre_name
        )

    tempo_bpm = _tempo(genre_name, seed, selected_tempo_bpm)
    meter = seed["meter"]
    beats_per_bar = _beats_per_bar(meter)
    section_count = len(seed["sections"])
    total_beats = beats_per_bar * section_count

    mappings = {
        x["role"]: x for x in role_authority["role_mappings"]
    }
    source_roles = {
        x["role"]: x for x in seed["roles"]
    }

    chord_events = []
    for item in seed["chords"]:
        bar = int(item["bar"])
        offset = _fraction(item.get("beat", 0), "CHORD_BEAT")
        if not (0 <= bar < section_count and 0 <= offset < beats_per_bar):
            raise GenreV3SymbolicExecutionError("CHORD_OUTSIDE_SEED")
        chord = _parse_chord(item["symbol"])
        position = Fraction(bar) * beats_per_bar + offset
        chord.update({
            "bar": bar,
            "beat": str(offset),
            "position": position,
        })
        chord_events.append(chord)
    chord_events.sort(key=lambda x: x["position"])
    chord_times = [x["position"] for x in chord_events]
    if len(chord_times) != len(set(chord_times)):
        raise GenreV3SymbolicExecutionError("MULTIPLE_CHORDS_AT_ONE_POSITION")

    patterns = {x["role"]: x for x in seed["patterns"]}
    events = []

    for bar, section in enumerate(seed["sections"]):
        section_name = section["name"]
        variation_by_role = section["variation_by_role"]
        for role_name, source_role in source_roles.items():
            mapping = mappings[role_name]
            pattern = patterns[role_name]
            variation = variation_by_role[role_name]
            notes = pattern["variations"][variation]

            for note_index, note in enumerate(notes):
                offset = _fraction(note.get("beat"), "PATTERN_BEAT")
                duration = _fraction(note.get("duration"), "PATTERN_DURATION")
                if not (0 <= offset < beats_per_bar and duration > 0):
                    raise GenreV3SymbolicExecutionError("PATTERN_TIMING_INVALID")
                start = Fraction(bar) * beats_per_bar + offset
                end = start + duration

                if pattern["kind"] == "CHORD_RELATIVE":
                    chord_index = bisect_right(chord_times, start) - 1
                    if chord_index < 0:
                        raise GenreV3SymbolicExecutionError("NO_ACTIVE_CHORD")
                    chord = chord_events[chord_index]
                    degree = note.get("degree")
                    octave = note.get("octave")
                    if type(degree) is not int or not 1 <= degree <= 7:
                        raise GenreV3SymbolicExecutionError("INVALID_CHORD_DEGREE")
                    if type(octave) is not int or not -1 <= octave <= 9:
                        raise GenreV3SymbolicExecutionError("INVALID_NOTE_OCTAVE")
                    midi = (
                        (octave + 1) * 12
                        + chord["root_pc"]
                        + SCALES[chord["quality"]][degree - 1]
                    )
                    next_chord_index = bisect_right(chord_times, start)
                    if (
                        pattern["retrigger"] == "STOP_AT_CHORD"
                        and next_chord_index < len(chord_times)
                        and chord_times[next_chord_index] < end
                    ):
                        end = chord_times[next_chord_index]
                elif pattern["kind"] == "DRUM_ABSOLUTE":
                    midi = note.get("midi")
                    if type(midi) is not int or not 0 <= midi <= 127:
                        raise GenreV3SymbolicExecutionError("INVALID_DRUM_MIDI")
                else:
                    raise GenreV3SymbolicExecutionError(
                        "PATTERN_KIND_NOT_SUPPORTED_BY_V3_EXECUTOR"
                    )

                if end <= start or end > total_beats:
                    raise GenreV3SymbolicExecutionError("EVENT_DURATION_OUTSIDE_SEED")

                playable = source_role.get("playable_midi_range")
                if (
                    isinstance(playable, list)
                    and len(playable) == 2
                    and not (int(playable[0]) <= midi <= int(playable[1]))
                ):
                    raise GenreV3SymbolicExecutionError(
                        f"EVENT_OUTSIDE_SOURCE_ROLE_RANGE::{genre_name}::{role_name}"
                    )

                velocity = note.get("velocity")
                if type(velocity) is not int or not 1 <= velocity <= 127:
                    raise GenreV3SymbolicExecutionError("INVALID_VELOCITY")

                event = {
                    "track_id": role_name,
                    "role": role_name,
                    "instrument_id": mapping["instrument_id"],
                    "source_instrument_id": mapping["source_instrument_id"],
                    "instrument_mapping_kind": mapping["mapping_kind"],
                    "start_beat": float(start),
                    "duration_beats": float(end - start),
                    "midi": int(midi),
                    "velocity": int(velocity),
                    "section": section_name,
                    "variation": variation,
                    "source_seed_id": seed["seed_id"],
                    "source_pattern_kind": pattern["kind"],
                    "source_rule": "V3_GOVERNED_ORIGINAL_SYMBOLIC_SOURCE_PATTERN",
                    "symbolic_only": True,
                }
                if mapping.get("performance_intent"):
                    event["performance_intent"] = mapping["performance_intent"]
                events.append(event)

    events.sort(key=lambda x: (x["start_beat"], x["track_id"], x["midi"]))
    if not events:
        raise GenreV3SymbolicExecutionError("SYMBOLIC_EXECUTION_EMPTY")

    expected_roles = set(source_roles)
    actual_roles = {x["role"] for x in events}
    if actual_roles != expected_roles:
        raise GenreV3SymbolicExecutionError(
            "SYMBOLIC_EXECUTION_SILENT_ROLE::" + genre_name
        )
    expected_sections = {x["name"] for x in seed["sections"]}
    actual_sections = {x["section"] for x in events}
    if actual_sections != expected_sections:
        raise GenreV3SymbolicExecutionError(
            "SYMBOLIC_EXECUTION_SILENT_SECTION::" + genre_name
        )

    result = {
        "schema": SCHEMA,
        "status": "PASS",
        "genre": genre_name,
        "profile_id": seed["profile_id"],
        "source_pattern_file": seed["source_pattern_file"],
        "source_seed_id": seed["seed_id"],
        "meter": meter,
        "tempo_bpm": tempo_bpm,
        "bar_count": section_count,
        "beats_per_bar": float(beats_per_bar),
        "role_authority": role_authority,
        "chords": [
            {k: v for k, v in item.items() if k != "position"}
            for item in chord_events
        ],
        "events": events,
        "event_count": len(events),
        "audio_authority": False,
        "audio_generated": False,
        "live_runtime_authority": False,
        "musical_audition_approved": False,
        "reasoning_engine_used": False,
        "promotion_gate": (
            "STRUCTURAL_SYMBOLIC_PASS__THEN_GENRE_SPECIFIC_MUSICAL_REVALIDATION__"
            "THEN_LISTENING__NO_LIVE_PROMOTION_BY_THIS MODULE"
        ),
    }
    result["execution_sha256"] = _sha({
        k: v for k, v in result.items() if k != "execution_sha256"
    })
    return result
