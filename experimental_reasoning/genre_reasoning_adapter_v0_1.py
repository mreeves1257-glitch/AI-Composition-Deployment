"""Genre-profile adapter for Composer Musical Reasoning Engine v0.1.

This adapter does not define genres. It reads the existing Composer profile and
pre-generation compiler output, then supplies that authoritative context to the
isolated reasoning engine.
"""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys
from typing import Any, Mapping, Optional, Sequence

HERE = Path(__file__).resolve().parent
MASTER = HERE.parent / "current_master_forward"
if str(MASTER) not in sys.path:
    sys.path.insert(0, str(MASTER))

from genre_pre_generation_compiler import compile_generation_plan, compile_semantic_contract
from reasoning_engine_v0_1 import ComposerState, MusicalGoal, reason

ADAPTER_ID = "COMPOSER_GENRE_REASONING_ADAPTER_V0_1"


def _baseline_for_profile(profile: Mapping[str, Any]) -> tuple:
    meters = list(profile.get("meter_options") or ["4/4"])
    tempos = list(profile.get("tempo_bpm_range") or [120, 120])
    forms = list(profile.get("form_tendencies") or ["verse_chorus"])
    meter = str(meters[0])
    bpm = int(tempos[0])
    form = str(forms[0])
    return ("C", "major", meter, bpm, form, "roots")


def _profile_spatial_character(profile: Mapping[str, Any]) -> dict[str, str]:
    text = " ".join(
        str(profile.get(k) or "")
        for k in (
            "arrangement_transformation",
            "dynamic_behavior",
            "sound_effects_intent",
            "mix_prominence_intent",
            "production_mastering_intent",
        )
    ).lower()

    return {
        "spaciousness": (
            "BROAD"
            if any(w in text for w in ("broad spatial", "space", "spacious", "open", "depth", "ambient"))
            else "PROFILE_STANDARD"
        ),
        "dynamic_range": (
            "PRESERVE_WIDE"
            if any(w in text for w in ("wide", "dynamic range", "cresc", "diminu", "breathing"))
            else "PROFILE_STANDARD"
        ),
        "transient_emphasis": (
            "PRESERVE_PUNCH"
            if any(w in text for w in ("punch", "transient", "backbeat", "attack"))
            else "PROFILE_STANDARD"
        ),
    }


def reason_with_genre_profile(
    *,
    profile: Mapping[str, Any],
    state: ComposerState,
    goal: Optional[MusicalGoal] = None,
    creation_seed: int = 0,
) -> dict[str, Any]:
    """Return a reasoning packet grounded in one existing Composer genre profile."""
    profile_id = str(profile.get("profile_id") or "")
    if not profile_id:
        raise ValueError("GENRE_REASONING_PROFILE_ID_REQUIRED")
    if state.profile_id != profile_id:
        raise ValueError("GENRE_REASONING_STATE_PROFILE_MISMATCH")

    contract = compile_semantic_contract(dict(profile))
    generation_plan = compile_generation_plan(
        dict(profile),
        _baseline_for_profile(profile),
        creation_seed=creation_seed,
    )

    packet = reason(
        state=state,
        semantic_tags=contract["tags"],
        generation_plan=generation_plan,
        goal=goal,
    )

    packet["genre_profile_adapter"] = {
        "adapter_id": ADAPTER_ID,
        "profile_id": profile_id,
        "profile_status": profile.get("status"),
        "profile_family": profile.get("family"),
        "resolution_policy": profile.get("resolution_policy"),
        "profile_remains_authoritative": True,
        "semantic_tags": contract["tags"],
        "compiled_harmony_family": generation_plan["harmony_family"],
        "compiled_bass_behavior": generation_plan["bass_behavior"],
        "compiled_meter": generation_plan["meter"],
        "compiled_form": generation_plan["form"],
        "compiled_tempo_bpm": generation_plan["tempo_bpm"],
        "spatial_character": _profile_spatial_character(profile),
        "source_fields": {
            "groove_behavior": profile.get("groove_behavior"),
            "phrase_behavior": profile.get("phrase_behavior"),
            "harmony_behavior": profile.get("harmony_behavior"),
            "bass_behavior": profile.get("bass_behavior"),
            "instrument_role_behavior": profile.get("instrument_role_behavior"),
            "arrangement_transformation": profile.get("arrangement_transformation"),
            "dynamic_behavior": profile.get("dynamic_behavior"),
            "mix_prominence_intent": profile.get("mix_prominence_intent"),
            "production_mastering_intent": profile.get("production_mastering_intent"),
        },
    }
    return packet
