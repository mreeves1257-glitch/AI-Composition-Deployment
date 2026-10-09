"""One runtime gateway for all 55 original genres: no duplicate arranger engines.

This module connects the original Stage-3 -> Stage-4 musical interpreter slot to
source-of-truth genre definitions, the 22 capability requirements and selected
instruments. It does NOT synthesize notes or silently activate unfinished genre
backends. All source files remain read-only.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parent
ORIGINAL_STAGE_ORDER = (
    "SELECT_GENRE", "DEFINE_MUSICAL_STRUCTURE",
    "CHOOSE_INSTRUMENTS_AND_DRUM_KIT", "COMPOSE_SEPARATE_PARTS",
    "PERFORM_MUSICALLY", "RENDER_SEPARATE_AUDIO_STEMS",
    "GENRE_MIX_THEN_STANDALONE_3D_MIX",
)
CAPABILITY_IDS = tuple("CAP_%02d" % n for n in range(1, 23))


class InterpreterConnectionError(ValueError):
    """Prevent use of a mismatched genre, source file or musical instrument."""


def _read_json(path: Path) -> dict:
    if not path.is_file():
        raise InterpreterConnectionError("MISSING_SOURCE:" + str(path))
    return json.loads(path.read_text(encoding="utf-8"))


def listed_genres() -> tuple[str, ...]:
    """All canonical genre names; no hard-coded extra/duplicated genre registry."""
    idx = _read_json(ROOT / "index.json")
    names = idx["genre_to_family_file"]
    if len(names) != 55 or idx["profile_count"] != 55:
        raise InterpreterConnectionError("GENRE_INDEX_NOT_EXACT_55")
    if len(idx["family_memberships"]) != 13:
        raise InterpreterConnectionError("GENRE_FAMILIES_NOT_EXACT_13")
    return tuple(names)


def _validate_profile(genre: str, profile: dict, handoff: dict, procedure: dict,
                      index: dict, procedure_master: dict) -> dict:
    definition = profile["musical_definition"]
    if profile["genre"] != genre or definition["profile_id"] != handoff["profile_id"]:
        raise InterpreterConnectionError("GENRE_PROFILE_ID_MISMATCH:" + genre)
    if procedure["profile_id"] != definition["profile_id"]:
        raise InterpreterConnectionError("CAPABILITY_GENRE_ID_MISMATCH:" + genre)
    if procedure["capability_ids"] != list(CAPABILITY_IDS):
        raise InterpreterConnectionError("22_CAPABILITIES_MISSING:" + genre)
    if procedure_master["capability_count"] != 22:
        raise InterpreterConnectionError("CAPABILITY_MASTER_NOT_22")
    if tuple(profile["seven_stage_plan"]["stage_order"]) != ORIGINAL_STAGE_ORDER:
        raise InterpreterConnectionError("ORIGINAL_SEVEN_STAGES_CHANGED:" + genre)
    if (profile["seven_stage_plan"]["enable_runtime_connections"] or
            handoff.get("interpreter_stage_connected", False)):
        raise InterpreterConnectionError("PREEXISTING_STAGE_FLAGS_CHANGED:" + genre)
    if not isinstance(definition.get("meter_options"), list) or not definition["meter_options"]:
        raise InterpreterConnectionError("METER_NOT_DEFINED:" + genre)
    expected = index["genre_to_family_file"][genre]
    if expected != f'{profile["family_name"]}/profile.json':
        # family_name may be a display label; index path remains authoritative.
        pass
    if handoff["source_of_truth"]["file"] != "composer_overrides/genre_styles/" + expected:
        raise InterpreterConnectionError("MUSICAL_DEFINITION_SOURCE_MISMATCH:" + genre)
    if handoff["source_of_truth"]["json_pointer"] != (
        "/profiles/" + genre.replace("~", "~0").replace("/", "~1") +
        "/musical_definition"
    ):
        raise InterpreterConnectionError("MUSICAL_DEFINITION_POINTER_MISMATCH:" + genre)
    return definition


def route_to_shared_interpreter(
    genre: str,
    *,
    runtime_profile: Mapping[str, Any] | None = None,
    original_stage3_result: Mapping[str, Any] | None = None,
) -> dict:
    """Make a typed, traceable COMMON composer-facing Stage-3→4 handoff.

    This is executable routing, but musical backends are intentionally NOT
    enabled until note output + exact original SFZ performance are verified.
    """
    idx = _read_json(ROOT / "index.json")
    filepath = idx["genre_to_family_file"].get(genre)
    if not filepath:
        raise InterpreterConnectionError("UNKNOWN_GENRE:" + str(genre))
    family = Path(filepath).parent.name
    original = _read_json(ROOT / filepath)
    p = original["profiles"][genre]
    handoff_root = _read_json(ROOT / family / "GENRE_INTERPRETER_HANDOFF_R1.json")
    capability_root = _read_json(ROOT / family / "GENRE_22_CAPABILITY_PROCEDURE_R1.json")
    procedure_master = _read_json(ROOT / "GENRE_22_CAPABILITY_PROCEDURE_MASTER_R1.json")
    try:
        handoff = next(x for x in handoff_root["genres"] if x["genre_name"] == genre)
        procedure = next(x for x in capability_root["genre_records"] if x["genre_name"] == genre)
    except StopIteration as exc:
        raise InterpreterConnectionError("MISSING_FAMILY_HANDOFF:" + genre) from exc
    musical = _validate_profile(genre, p, handoff, procedure, idx, procedure_master)
    if runtime_profile is not None and runtime_profile.get("profile_id") != musical["profile_id"]:
        raise InterpreterConnectionError("RUNTIME_PROFILE_ID_MISMATCH:" + genre)
    stage3 = original_stage3_result or {}
    if original_stage3_result is not None and stage3.get("status") != "PASS":
        raise InterpreterConnectionError("ORIGINAL_STAGE3_NOT_READY:" + genre)
    selected_instruments = list(stage3.get("palette", []))
    if len(selected_instruments) != len(set(selected_instruments)):
        raise InterpreterConnectionError("DUPLICATED_SELECTED_INSTRUMENTS:" + genre)
    if not all(isinstance(x, str) and x.strip() for x in selected_instruments):
        raise InterpreterConnectionError("INVALID_SELECTED_INSTRUMENT_ID:" + genre)
    actual_meter = stage3.get("meter")
    if actual_meter is not None and actual_meter not in musical["meter_options"]:
        raise InterpreterConnectionError("SELECTED_METER_OUTSIDE_ORIGINAL_GENRE:" + genre)
    tempo = stage3.get("tempo_bpm")
    if tempo is not None:
        lo, hi = musical["tempo_bpm_range"]
        if not lo <= tempo <= hi:
            raise InterpreterConnectionError("SELECTED_TEMPO_OUTSIDE_ORIGINAL_GENRE:" + genre)

    # The original definitions remain the single source of truth; no new
    # hypothetical recorded resources, performance claims, or generated notes.
    goal_fields = ("profile_id", "tempo_bpm_range", "meter_options",
                   "form_tendencies", "groove_behavior", "phrase_behavior",
                   "harmony_behavior", "bass_behavior",
                   "percussion_behavior_if_applicable",
                   "instrument_role_behavior", "ensemble_player_behavior",
                   "articulation_behavior", "timing_humanization_behavior",
                   "arrangement_transformation", "continuous_performance_control")
    selected = {field: musical.get(field) for field in goal_fields}
    rules = [
        {"id": item["id"],
         "requirement": item["implementation_requirement"],
         "applicability": item["applicability_rule"],
         "status": "UNVERIFIED" if item["applicability_rule"] == "ALL_GENRES" else "PENDING_SELECTED_INSTRUMENT_CAPABILITY_CHECK"}
        for item in procedure_master["capabilities"]
    ]
    if tuple(item["id"] for item in rules) != CAPABILITY_IDS:
        raise InterpreterConnectionError("INVALID_CAPABILITY_REGISTER")
    return {
        "schema": "AI_COMP_SHARED_INTERPRETER_BOUNDARY_R1",
        "link_state": "CONNECTED_STAGE_3_TO_4_DATA_ROUTER",
        "arranger_backend_state": "MUSICAL_EVENT_GENERATOR_NOT_ENABLED_OR_VERIFIED",
        "genre": genre,
        "family": family,
        "genre_profile_id": musical["profile_id"],
        "genre_specific_musical_intentions": selected,
        "source_path": "composer_overrides/genre_styles/" + filepath,
        "selected_original_instrument_ids": selected_instruments,
        "selected_meter": actual_meter,
        "selected_tempo_bpm": tempo,
        "selected_song_section": stage3.get("section_id"),
        "stage_3_to_4": "MUSICAL_INTERPRETER_AND_SOURCE_SPECIFIC_BRIDGE",
        "next_stage": "COMPOSE_SEPARATE_PARTS",
        "performance_stage": "PERFORM_MUSICALLY",
        "mixer_stage": "GENRE_MIX_THEN_STANDALONE_3D_MIX",
        "original_7_stages": list(ORIGINAL_STAGE_ORDER),
        "capability_requirements": rules,
        "musical_notes_authorized": False,
        "source_sfzs_unchanged": True,
        "full_song_audio_verified": False,
        "live_genre_enabled": False,
    }


def connect_all_genres() -> dict:
    """Exercise ONE shared gateway with all 55 actual individual genre definitions."""
    routes = {}
    for name in listed_genres():
        routes[name] = route_to_shared_interpreter(name)
    if len(routes) != 55 or len({r["genre_profile_id"] for r in routes.values()}) != 55:
        raise InterpreterConnectionError("NOT_55_UNIQUE_ROUTES")
    return routes

def compile_selected_musical_interpreter(
    genre: str,
    *,
    original_mma_midi_path: str | Path,
    original_stage3_result: Mapping[str, Any] | None = None,
) -> dict:
    """Run a VERIFIED style-specific note-producing backend through ONE router.

    Rock pinned original is the first musical compiler. All other genres are
    data-linked but intentionally fail closed until their own playing language
    is separately proven; there is never a universal Rock fallback.
    """
    route = route_to_shared_interpreter(
        genre, original_stage3_result=original_stage3_result
    )
    if genre != "ROCK":
        raise InterpreterConnectionError(
            "NO_VERIFIED_SCORE_BACKEND_FOR_GENRE:" + genre
        )
    from .Rock.rock_pinned_mma_interpreter import compile_pinned_mma_rock_score
    return compile_pinned_mma_rock_score(original_mma_midi_path, route)
