"""Registry for genre-specific V3 composition executors.

There is no generic composition fallback here. A genre is registered only after
its full symbolic composition path has passed genre-specific structural audits.

Current entry:
- ROCK / ROCK_CORE_V2 family baseline, only when no subgenre cues are present.

Explicit Rock variant cues must bypass this family-baseline executor and resolve
through the Rock variant package/form system instead.
"""
from __future__ import annotations

import importlib
from typing import Any

SCHEMA="GENRE_V3_COMPOSITION_EXECUTOR_REGISTRY_001"

EXECUTORS={
    "ROCK":{
        "module":"rock_v3_core_development_executor",
        "function":"execute",
        "profile_id":"ROCK_CORE_V2",
        "scope":"FAMILY_BASELINE_ONLY_WHEN_NO_VARIANT_CUES",
        "status":"STRUCTURAL_SYMBOLIC_COMPOSITION_CANDIDATE__NO_PERFORMANCE_OR_AUDIO_APPROVAL",
        "audio_authority":False,
        "live_runtime_authority":False,
        "finished_composition_authority":False,
    },
}


class GenreV3CompositionExecutorRegistryError(RuntimeError):
    pass


def status_for(
    genre_name:str,
    *,
    variant_cues_present:bool=False,
)->dict[str,Any]:
    spec=EXECUTORS.get(genre_name)
    if spec is None:
        return {
            "status":"NO_GENRE_SPECIFIC_COMPOSITION_EXECUTOR",
            "genre":genre_name,
            "registered":False,
            "eligible":False,
            "variant_cues_present":bool(variant_cues_present),
            "audio_authority":False,
            "live_runtime_authority":False,
            "finished_composition_authority":False,
        }

    eligible=not bool(variant_cues_present)
    return {
        "status":(
            "PASS"
            if eligible
            else "REGISTERED_BUT_BLOCKED_BY_VARIANT_CUES"
        ),
        "genre":genre_name,
        "registered":True,
        "eligible":eligible,
        "variant_cues_present":bool(variant_cues_present),
        **dict(spec),
        "next_gate":(
            "EXECUTE_FAMILY_BASELINE_SYMBOLIC_COMPOSITION"
            if eligible
            else "RESOLVE_VARIANT_PACKAGE_AND_FORM"
        ),
    }


def execute(
    genre_name:str,
    *,
    variant_cues_present:bool=False,
)->dict[str,Any]:
    state=status_for(
        genre_name,
        variant_cues_present=variant_cues_present,
    )
    if not state.get("registered"):
        raise GenreV3CompositionExecutorRegistryError(
            "GENRE_SPECIFIC_COMPOSITION_EXECUTOR_NOT_REGISTERED::"+genre_name
        )
    if not state.get("eligible"):
        raise GenreV3CompositionExecutorRegistryError(
            "FAMILY_BASELINE_COMPOSITION_BLOCKED_BY_VARIANT_CUES::"+genre_name
        )

    spec=EXECUTORS[genre_name]
    module=importlib.import_module(spec["module"])
    fn=getattr(module,spec["function"],None)
    if not callable(fn):
        raise GenreV3CompositionExecutorRegistryError(
            "COMPOSITION_EXECUTOR_ENTRYPOINT_MISSING::"+genre_name
        )

    result=fn()
    if result.get("status")!="PASS":
        raise GenreV3CompositionExecutorRegistryError(
            "COMPOSITION_EXECUTOR_NOT_PASS::"+genre_name
        )
    if result.get("profile_id")!=spec["profile_id"]:
        raise GenreV3CompositionExecutorRegistryError(
            "COMPOSITION_EXECUTOR_PROFILE_MISMATCH::"+genre_name
        )
    if result.get("resolved_variant") is not None:
        raise GenreV3CompositionExecutorRegistryError(
            "FAMILY_BASELINE_EXECUTOR_CLAIMED_VARIANT::"+genre_name
        )
    if result.get("family_baseline_only") is not True:
        raise GenreV3CompositionExecutorRegistryError(
            "FAMILY_BASELINE_EXECUTOR_SCOPE_MISSING::"+genre_name
        )
    for key in (
        "audio_authority",
        "live_runtime_authority",
        "finished_composition_authority",
        "musical_quality_proven",
        "listening_approval",
        "performance_realization_applied",
        "render_allowed",
    ):
        if result.get(key) is not False:
            raise GenreV3CompositionExecutorRegistryError(
                "COMPOSITION_EXECUTOR_AUTHORITY_ESCALATION::"+
                genre_name+"::"+key
            )
    return result
