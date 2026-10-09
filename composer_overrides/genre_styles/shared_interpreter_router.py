"""One shared, genre-specific musical interpreter entry point for all 55 genres.

This router wires the existing genre index, independent original musical
definitions, 22 capability requirements and typed Stage-3-to-4 handoff.
External arranger engines are independent MIDI-data PRODUCERS, not imported
GPL libraries or automatic stand-ins for the existing Composer.

The router does not enable production services, generate a finished song, or
render original recorded sounds. It can validate and pass independently
generated, source-aware per-track note events to the existing Stage 4.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Mapping, Sequence

HERE = Path(__file__).resolve().parent

STAGE_NAMES = (
    "SELECT_GENRE",
    "DEFINE_MUSICAL_STRUCTURE",
    "CHOOSE_INSTRUMENTS_AND_DRUM_KIT",
    "COMPOSE_SEPARATE_PARTS",
    "PERFORM_MUSICALLY",
    "RENDER_SEPARATE_AUDIO_STEMS",
    "GENRE_MIX_THEN_STANDALONE_3D_MIX",
)
CAP_IDS = tuple(f"CAP_{i:02d}" for i in range(1, 23))
INTERPRETER_BOUNDARY = "BETWEEN_ORIGINAL_STAGE_03_AND_04"


class HandoffError(ValueError):
    """A genre, part or selected original sound resource is not verified."""


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _check(cond: bool, reason: str) -> None:
    if not cond:
        raise HandoffError(reason)


def linked_genres() -> tuple[str, ...]:
    """The existing original index, NOT a second invented list of genres."""
    source = _json(HERE / "index.json")
    _check(source.get("profile_count") == 55, "GENRE_INDEX_COUNT_CHANGED")
    _check(source.get("automatic_application_enabled") is False, "LIVE_ACTIVATION_UNAPPROVED")
    return tuple(source["genre_to_family_file"])


def resolve(genre: str) -> dict:
    """Get ONE shared adapter for any saved genre without changing its style."""
    index = _json(HERE / "index.json")
    mapping = index["genre_to_family_file"]
    _check(isinstance(genre, str) and genre in mapping, "UNKNOWN_OR_UNFILED_GENRE")
    profile_file = mapping[genre]
    _check(profile_file.count("/") == 1 and profile_file.endswith("/profile.json"),
           "UNSAFE_FAMILY_PATH")
    family = profile_file.split("/")[0]
    profile = _json(HERE / profile_file)
    handoff = _json(HERE / family / "GENRE_INTERPRETER_HANDOFF_R1.json")
    procedure = _json(HERE / family / "GENRE_22_CAPABILITY_PROCEDURE_R1.json")
    master = _json(HERE / "GENRE_22_CAPABILITY_PROCEDURE_MASTER_R1.json")
    p = profile["profiles"][genre]
    original_stages = p["seven_stage_plan"]
    _check(original_stages["stage_order"] == list(STAGE_NAMES), "ORIGINAL_SEVEN_STAGES_CHANGED")
    _check(original_stages["stage_count"] == 7 and
           not original_stages["enable_runtime_connections"],
           "PRODUCTION_STAGE_NOT_REFERENCE_SAFE")
    _check(not profile["stage_wiring_activated"] and profile["source_assets_immutable"],
           "SOURCE_PROTECTION_CHANGED")
    matching = [entry for entry in handoff["genres"] if entry["genre_name"] == genre]
    _check(len(matching) == 1 and
           matching[0]["profile_id"] == p["musical_definition"]["profile_id"] and
           matching[0].get("interpreter_stage_connected", matching[0].get("connected")) is False,
           "GENRE_INTERPRETER_HANDOFF_MISMATCH")
    gates = [entry for entry in procedure["genre_records"] if entry["genre_name"] == genre]
    _check(len(gates) == 1 and tuple(gates[0]["capability_ids"]) == CAP_IDS,
           "GENRE_22_CAPABILITY_LINK_MISMATCH")
    _check([gate["id"] for gate in master["capabilities"]] == list(CAP_IDS),
           "MASTER_22_CAPABILITY_SET_CHANGED")
    _check(not procedure["activation_allowed"] and not master["automatic_activation"],
           "CAPABILITY_ACTIVATION_UNAPPROVED")
    definition = p["musical_definition"]
    roles = tuple(s["track_id"] for s in p["individual_instrument_tracks"])
    _check(len(set(roles)) == len(roles), "DUPLICATE_TRACK_ROLE")
    return {
        "genre": genre,
        "family": family,
        "profile_id": definition["profile_id"],
        "original_profile_path": "composer_overrides/genre_styles/" + profile_file,
        "stage2_original_musical_definition": definition,
        "stage3_original_roles": roles,
        "meter_options": tuple(definition["meter_options"]),
        "tempo_bpm_range": tuple(definition["tempo_bpm_range"]),
        "interpreter_to_composer_boundary": INTERPRETER_BOUNDARY,
        "stage4_owner": "COMPOSE_SEPARATE_PARTS",
        "stage5_owner": "PERFORM_MUSICALLY",
        "capability_ids": CAP_IDS,
        "genre_specific_grammar_required": True,
        "shared_adapter_linked": True,
        "score_backend_activated": False,
        "live_runtime_deployed": False,
        "verified_completed_audio": False,
    }


def _finite_num(value: object, reason: str) -> float:
    _check(type(value) in (float, int) and math.isfinite(value), reason)
    return float(value)


def stage3_to_stage4(
    genre: str,
    *,
    song_structure: Mapping[str, object],
    selected_instruments: Sequence[Mapping[str, object]],
    arranger_events: Sequence[Mapping[str, object]],
) -> dict:
    """Validate separate upstream MIDI-derived events for THIS genre and source.

    This is a real executable bridge for trusted, caller-provided typed events;
    it does NOT automatically run any unverified external arranger software.
    No fallback synthesizers, fake instruments, guitar default, or GM drum maps.
    """
    route = resolve(genre)
    _check(isinstance(song_structure, Mapping), "MISSING_STAGE2_SONG_STRUCTURE")
    _check(isinstance(selected_instruments, (tuple, list)) and
           isinstance(arranger_events, (tuple, list)), "INVALID_PART_EVENT_INPUT")
    meter = song_structure.get("meter")
    tempo = _finite_num(song_structure.get("tempo_bpm"), "INVALID_TEMPO")
    _check(isinstance(meter, str) and meter in route["meter_options"],
           "METER_NOT_AUTHORIZED_BY_GENRE")
    lo, hi = route["tempo_bpm_range"]
    _check(float(lo) <= tempo <= float(hi), "TEMPO_OUTSIDE_GENRE_PROFILE_RANGE")
    _check(isinstance(song_structure.get("section"), str) and
           bool(song_structure["section"].strip()), "MISSING_SONG_SECTION")
    # Explicit stage-3 verified bindings, NOT original profile's guessed roles.
    sources = {}
    for resource in selected_instruments:
        _check(isinstance(resource, Mapping), "INVALID_STAGE3_INSTRUMENT")
        role = resource.get("track_id")
        _check(isinstance(role, str) and role in route["stage3_original_roles"] and
               role not in sources, "UNAUTHORIZED_OR_DUPLICATE_TRACK_ROLE")
        _check(isinstance(resource.get("source_id"), str) and
               bool(resource["source_id"].strip()), "UNVERIFIED_RESOURCE_ID")
        min_note = resource.get("min_midi_note")
        max_note = resource.get("max_midi_note")
        _check(type(min_note) is int and type(max_note) is int and
               0 <= min_note <= max_note <= 127, "UNVERIFIED_RESOURCE_NOTE_RANGE")
        sources[role] = dict(resource)
    _check(bool(sources), "NO_VERIFIED_SELECTED_INSTRUMENTS")
    notes = []
    for event in arranger_events:
        _check(isinstance(event, Mapping), "INVALID_INTERPRETED_EVENT")
        role = event.get("track_id")
        _check(role in sources, "INTERPRETER_SELECTED_UNVERIFIED_PART")
        pitch = event.get("midi_note")
        velocity = event.get("velocity")
        _check(type(pitch) is int and 0 <= pitch <= 127, "INVALID_MIDI_PITCH")
        _check(type(velocity) is int and 1 <= velocity <= 127, "INVALID_VELOCITY")
        source = sources[role]
        _check(source["min_midi_note"] <= pitch <= source["max_midi_note"],
               "MIDI_OUTSIDE_SELECTED_REAL_SAMPLE_RANGE")
        start = _finite_num(event.get("start_beat"), "INVALID_EVENT_START")
        duration = _finite_num(event.get("duration_beats"), "INVALID_EVENT_DURATION")
        _check(start >= 0 and duration > 0, "NONPOSITIVE_OR_NEGATIVE_EVENT")
        # Only allow explicit source-backed playing techniques, never assume
        # all MIDI CC/key-switches are supported by every recorded instrument.
        gesture = event.get("articulation", "normal")
        supported = source.get("supported_articulations", ("normal",))
        _check(isinstance(gesture, str) and gesture in supported,
               "ARTICULATION_NOT_SUPPORTED_BY_SELECTED_SOURCE")
        notes.append({
            "track_id": role, "source_id": source["source_id"],
            "midi_note": pitch, "velocity": velocity,
            "start_beat": start, "duration_beats": duration,
            "articulation": gesture,
        })
    notes.sort(key=lambda n: (n["start_beat"], n["track_id"], n["midi_note"]))
    return {
        "schema_version": "SHARED_GENRE_INTERPRETER_STAGE3_TO4_R1",
        "status": "VALIDATED_PRE_STAGE4_NOTE_EVENTS_NOT_FINAL_AUDIO",
        "genre": route["genre"], "profile_id": route["profile_id"],
        "musical_structure": dict(song_structure),
        "stage4_composer_input_events": notes,
        "resolved_resource_bindings": [
            {"track_id": role, "source_id": record["source_id"]}
            for role, record in sources.items()
        ],
        "stage5_performance_required": True,
        "stage6_recorded_stem_renderer_required": True,
        "stage7_independent_3d_mixer_required": True,
        "live_composer_connected": False,
        "source_files_modified": False,
    }
