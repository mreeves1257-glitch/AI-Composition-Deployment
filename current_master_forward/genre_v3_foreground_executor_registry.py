"""Registry for genre-specific V3 foreground executors.

There is deliberately no generic melody fallback. A genre appears here only
after it has a separate structurally validated foreground implementation.

Current status:
- ROCK: research candidate from rock_v3_foreground_pilot
- all other non-Classical genres: unregistered / foreground execution blocked
- Classical: separate dedicated V3 composition path
"""
from __future__ import annotations

import importlib
from typing import Any

SCHEMA="GENRE_V3_FOREGROUND_EXECUTOR_REGISTRY_001"

EXECUTORS={
    "ROCK":{
        "module":"rock_v3_foreground_pilot",
        "function":"realize",
        "profile_id":"ROCK_CORE_V2",
        "status":"STRUCTURAL_RESEARCH_CANDIDATE__NO_AUDIO_APPROVAL",
        "audio_authority":False,
        "live_runtime_authority":False,
    },
}


class GenreV3ForegroundExecutorRegistryError(RuntimeError):
    pass


def status_for(genre_name:str)->dict[str,Any]:
    spec=EXECUTORS.get(genre_name)
    if spec is None:
        return {
            "status":"NO_GENRE_SPECIFIC_FOREGROUND_EXECUTOR",
            "genre":genre_name,
            "registered":False,
            "audio_authority":False,
            "live_runtime_authority":False,
        }
    return {
        "status":"PASS",
        "genre":genre_name,
        "registered":True,
        **dict(spec),
    }


def execute(genre_name:str)->dict[str,Any]:
    spec=EXECUTORS.get(genre_name)
    if spec is None:
        raise GenreV3ForegroundExecutorRegistryError(
            "GENRE_SPECIFIC_FOREGROUND_EXECUTOR_NOT_REGISTERED::"+genre_name
        )
    module=importlib.import_module(spec["module"])
    fn=getattr(module,spec["function"],None)
    if not callable(fn):
        raise GenreV3ForegroundExecutorRegistryError(
            "FOREGROUND_EXECUTOR_ENTRYPOINT_MISSING::"+genre_name
        )
    result=fn()
    if result.get("status")!="PASS":
        raise GenreV3ForegroundExecutorRegistryError(
            "FOREGROUND_EXECUTOR_NOT_PASS::"+genre_name
        )
    if result.get("profile_id")!=spec["profile_id"]:
        raise GenreV3ForegroundExecutorRegistryError(
            "FOREGROUND_EXECUTOR_PROFILE_ID_MISMATCH::"+genre_name
        )
    if result.get("audio_authority") is not False:
        raise GenreV3ForegroundExecutorRegistryError(
            "FOREGROUND_EXECUTOR_AUDIO_AUTHORITY_ESCALATION::"+genre_name
        )
    if result.get("live_runtime_authority") is not False:
        raise GenreV3ForegroundExecutorRegistryError(
            "FOREGROUND_EXECUTOR_LIVE_AUTHORITY_ESCALATION::"+genre_name
        )
    return result
