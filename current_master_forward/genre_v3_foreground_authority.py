"""Genre Contract V3 foreground/melody authority.

This module does not invent melody notes. It compiles the existing V3 foreground
instructions into one explicit machine-readable handoff and states whether a
separate foreground executor is still required.

The recovered source-pattern libraries are accompaniment/groove seeds. They have
no explicit LEAD/MELODY/SOLO/HOOK/THEME/COUNTER/VOCAL roles and may not be
promoted as finished compositions without this separate foreground layer.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any

from genre_contract_v3_execution_bridge import contract_for, snapshot_for

AUTHORITY_ID = "GENRE_V3_FOREGROUND_AUTHORITY_001"
SOURCE_PATTERN_ACCOMPANIMENT_ROLES = (
    "BASS","BRUSH","CLAP","CLAVE","CONGA","CYMBAL","HAND_DRUM",
    "HARMONY","HAT","KICK","LEFT_HAND","RIDE","RIGHT_HAND","SHAKER","SNARE",
)
EXPLICIT_FOREGROUND_ROLE_TOKENS = (
    "LEAD","MELODY","SOLO","HOOK","THEME","COUNTER","VOCAL",
)


class GenreV3ForegroundAuthorityError(RuntimeError):
    pass


def _sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()


def compile_authority(genre_name: str) -> dict[str, Any]:
    contract = contract_for(genre_name)
    snapshot = snapshot_for(genre_name)
    grammar = contract.get("musical_grammar") or {}
    ensemble = contract.get("ensemble") or {}
    variant = contract.get("variant_resolution") or {}
    performance = contract.get("performance") or {}

    required_grammar = ("melody_model", "phrase_model", "development_model")
    missing_grammar = [key for key in required_grammar if not grammar.get(key)]
    if missing_grammar:
        raise GenreV3ForegroundAuthorityError(
            "V3_FOREGROUND_GRAMMAR_MISSING::" + genre_name + "::" +
            ",".join(missing_grammar)
        )

    role_handoff = list(ensemble.get("role_handoff_rules") or [])
    foreground_windows = list(ensemble.get("foreground_window_rules") or [])
    if not role_handoff:
        raise GenreV3ForegroundAuthorityError(
            "V3_FOREGROUND_ROLE_HANDOFF_MISSING::" + genre_name
        )
    if not foreground_windows:
        raise GenreV3ForegroundAuthorityError(
            "V3_FOREGROUND_WINDOW_RULES_MISSING::" + genre_name
        )

    policy = snapshot.get("resolution_policy")
    if genre_name == "Classical":
        execution_status = "SEPARATE_CLASSICAL_V3_MELODY_PATH"
        separate_executor_required = False
        note_execution_ready_here = False
    elif policy != "AUTOMATIC_BASELINE_ALLOWED":
        execution_status = "CONTROLLED_OR_USER_FOREGROUND_RESOLUTION_REQUIRED"
        separate_executor_required = True
        note_execution_ready_here = False
    else:
        execution_status = (
            "STRUCTURED_FOREGROUND_AUTHORITY_PRESENT__"
            "NOTE_EXECUTION_NOT_COMPILED"
        )
        separate_executor_required = True
        note_execution_ready_here = False

    candidate_melody = variant.get("candidate_melody_behavior")
    packet = {
        "status": "PASS",
        "authority_id": AUTHORITY_ID,
        "genre": genre_name,
        "profile_id": snapshot.get("profile_id"),
        "resolution_policy": policy,
        "execution_status": execution_status,
        "note_execution_ready_here": note_execution_ready_here,
        "separate_foreground_executor_required": separate_executor_required,
        "melody_model": deepcopy(grammar.get("melody_model")),
        "phrase_model": deepcopy(grammar.get("phrase_model")),
        "development_model": deepcopy(grammar.get("development_model")),
        "role_handoff_rules": deepcopy(role_handoff),
        "foreground_window_rules": deepcopy(foreground_windows),
        "candidate_melody_behavior": deepcopy(candidate_melody),
        "variant_resolution_status": variant.get("status"),
        "timing_humanization_behavior": snapshot.get("timing_humanization_behavior"),
        "instrument_role_behavior": snapshot.get("instrument_role_behavior"),
        "ensemble_player_behavior": snapshot.get("ensemble_player_behavior"),
        "performance": deepcopy(performance),
        "source_pattern_role_vocabulary": list(SOURCE_PATTERN_ACCOMPANIMENT_ROLES),
        "source_pattern_explicit_foreground_role_count": 0,
        "source_pattern_can_supply_finished_foreground": False,
        "source_pattern_classification": "ACCOMPANIMENT_GROOVE_SEED_ONLY",
        "promotion_block": (
            "DO_NOT_RENDER_SOURCE_PATTERN_AS_FINISHED_COMPOSITION_"
            "WITHOUT_RESOLVED_FOREGROUND_LAYER"
        ),
        "reasoning_engine_required": False,
        "reasoning_engine_used": False,
        "audio_authority": False,
        "live_runtime_authority": False,
        "contract_sha256": (
            snapshot.get("_genre_contract_v3_source") or {}
        ).get("contract_sha256"),
    }
    packet["foreground_authority_sha256"] = _sha(packet)
    return packet


def audit_all() -> dict[str, Any]:
    from genre_contract_v3_execution_bridge import load_master
    names = list(load_master()["contracts"])
    results = {name: compile_authority(name) for name in names}
    if len(results) != 55:
        raise GenreV3ForegroundAuthorityError("V3_FOREGROUND_AUDIT_NOT_55")

    automatic = [
        x for x in results.values()
        if x["resolution_policy"] == "AUTOMATIC_BASELINE_ALLOWED"
        and x["genre"] != "Classical"
    ]
    controlled = [
        x for x in results.values()
        if x["resolution_policy"] != "AUTOMATIC_BASELINE_ALLOWED"
    ]
    classical = results["Classical"]

    return {
        "status": "PASS",
        "genre_count": len(results),
        "automatic_nonclassical_count": len(automatic),
        "controlled_or_user_count": len(controlled),
        "classical_count": 1,
        "automatic_foreground_note_execution_ready_count": sum(
            bool(x["note_execution_ready_here"]) for x in automatic
        ),
        "source_pattern_finished_foreground_count": sum(
            bool(x["source_pattern_can_supply_finished_foreground"])
            for x in results.values()
        ),
        "classical_execution_status": classical["execution_status"],
        "results": results,
    }
