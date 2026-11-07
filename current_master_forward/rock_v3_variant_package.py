"""Typed Rock V3 variant composition-package compiler.

Consumes the evidence-backed Rock variant research matrix. It does not create
notes, choose audio resources, or silently collapse umbrella labels into one
recipe.

Seven variants currently have enough evidence for a structured composition
candidate package. Classic rock and Alternative rock remain blocked until a
child style is resolved.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import hashlib
import json
from typing import Any

from genre_contract_v3_execution_bridge import ROOT as REPO, snapshot_for
from rock_v3_variant_resolver import resolve as resolve_variant

SCHEMA="ROCK_V3_VARIANT_COMPOSITION_PACKAGE_001"
MATRIX_PATH=REPO/"genre_contract_v3_research"/"ROCK_V3_VARIANT_RESEARCH_MATRIX_2026-11-07.json"


class RockV3VariantPackageError(RuntimeError):
    pass


def _sha(value:Any)->str:
    return hashlib.sha256(
        json.dumps(value,sort_keys=True,separators=(",",":"),default=str).encode()
    ).hexdigest()


def load_matrix()->dict[str,Any]:
    if not MATRIX_PATH.is_file():
        raise RockV3VariantPackageError("ROCK_VARIANT_RESEARCH_MATRIX_MISSING")
    data=json.loads(MATRIX_PATH.read_text())
    if data.get("schema")!="ROCK_V3_VARIANT_RESEARCH_MATRIX_001":
        raise RockV3VariantPackageError("ROCK_VARIANT_RESEARCH_MATRIX_SCHEMA_CHANGED")
    if data.get("profile_id")!="ROCK_CORE_V2":
        raise RockV3VariantPackageError("ROCK_VARIANT_RESEARCH_MATRIX_PROFILE_CHANGED")
    return data


def compile_package(variant_name:str)->dict[str,Any]:
    selection=resolve_variant(variant_name)
    matrix=load_matrix()
    row=(matrix.get("variants") or {}).get(variant_name)
    if row is None:
        raise RockV3VariantPackageError("ROCK_VARIANT_MATRIX_ROW_MISSING::"+variant_name)

    if row.get("classification","").startswith("UMBRELLA_"):
        packet={
            "schema":SCHEMA,
            "status":"BLOCKED_SECOND_LEVEL_VARIANT_RESOLUTION_REQUIRED",
            "genre":"ROCK",
            "profile_id":"ROCK_CORE_V2",
            "selected_variant":variant_name,
            "classification":row.get("classification"),
            "reason":row.get("reason"),
            "required_child_resolution":deepcopy(row.get("required_child_resolution") or []),
            "single_composition_recipe_allowed":False,
            "form_execution_ready":False,
            "note_execution_ready":False,
            "audio_authority":False,
            "live_runtime_authority":False,
            "finished_composition_authority":False,
            "reasoning_engine_used":False,
            "source_matrix":str(MATRIX_PATH.relative_to(REPO)),
            "next_gate":"RESOLVE_ROCK_CHILD_STYLE_BEFORE_FORM_OR_NOTES",
        }
        packet["package_sha256"]=_sha(packet)
        return packet

    if row.get("machine_package_status")!="RESEARCH_SUFFICIENT_FOR_STRUCTURAL_CANDIDATE__LISTENING_PENDING":
        raise RockV3VariantPackageError(
            "ROCK_VARIANT_NOT_STRUCTURAL_CANDIDATE::"+variant_name
        )

    required=(
        "form_strategy","groove_strategy","harmony_strategy","texture_strategy",
        "foreground_strategy","development_strategy","sources",
    )
    missing=[key for key in required if not row.get(key)]
    if missing:
        raise RockV3VariantPackageError(
            "ROCK_VARIANT_PACKAGE_FIELD_MISSING::"+variant_name+"::"+",".join(missing)
        )

    snapshot=snapshot_for("ROCK")
    packet={
        "schema":SCHEMA,
        "status":"PASS_STRUCTURAL_VARIANT_PACKAGE",
        "genre":"ROCK",
        "profile_id":snapshot.get("profile_id"),
        "selected_variant":variant_name,
        "classification":row.get("classification"),
        "evidence_confidence":row.get("evidence_confidence"),
        "scope_note":row.get("scope_note"),
        "form_strategy":deepcopy(row["form_strategy"]),
        "groove_strategy":deepcopy(row["groove_strategy"]),
        "harmony_strategy":deepcopy(row["harmony_strategy"]),
        "texture_strategy":deepcopy(row["texture_strategy"]),
        "foreground_strategy":deepcopy(row["foreground_strategy"]),
        "development_strategy":deepcopy(row["development_strategy"]),
        "evidence_source_ids":list(row["sources"]),
        "broad_rock_profile_id":"ROCK_CORE_V2",
        "broad_rock_tempo_range":deepcopy(snapshot.get("tempo_bpm_range")),
        "broad_rock_meter_options":deepcopy(snapshot.get("meter_options")),
        "selection_packet_sha256":selection.get("variant_packet_sha256"),
        "single_composition_recipe_allowed":True,
        "form_execution_ready":False,
        "note_execution_ready":False,
        "resource_execution_ready":False,
        "audio_authority":False,
        "live_runtime_authority":False,
        "finished_composition_authority":False,
        "reasoning_engine_used":False,
        "source_matrix":str(MATRIX_PATH.relative_to(REPO)),
        "next_gate":"BUILD_VARIANT_FORM_PLAN_AND_TRANSFORMATION_RULES",
    }
    packet["package_sha256"]=_sha(packet)
    return packet


def audit_all()->dict[str,Any]:
    matrix=load_matrix()
    results={name:compile_package(name) for name in matrix["variants"]}
    pass_names=[
        name for name,item in results.items()
        if item["status"]=="PASS_STRUCTURAL_VARIANT_PACKAGE"
    ]
    blocked_names=[
        name for name,item in results.items()
        if item["status"]=="BLOCKED_SECOND_LEVEL_VARIANT_RESOLUTION_REQUIRED"
    ]
    return {
        "status":"PASS",
        "genre":"ROCK",
        "variant_count":len(results),
        "structural_package_count":len(pass_names),
        "second_level_resolution_required_count":len(blocked_names),
        "structural_variants":pass_names,
        "umbrella_variants":blocked_names,
        "results":results,
    }
