"""Rock V3 form planner.

Plans variant-valid section/bar structure only. It never creates notes and never
silently selects a form.

- Five Rock variants expose explicit research-candidate form choices.
- Blues rock requires a form submode before a detailed blueprint.
- Progressive rock requires a custom section/meter plan.
- Classic rock and Alternative rock remain blocked at second-level resolution.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import hashlib
import json
import re
from typing import Any

from genre_contract_v3_execution_bridge import ROOT as REPO
from rock_v3_variant_package import compile_package

SCHEMA="ROCK_V3_FORM_PLAN_001"
FORM_PATH=REPO/"genre_contract_v3_research"/"ROCK_V3_FORM_CANDIDATES_2026-11-07.json"
METER_RE=re.compile(r"^([1-9][0-9]?)/(2|4|8|16)$")


class RockV3FormPlannerError(RuntimeError):
    pass


def _sha(value:Any)->str:
    return hashlib.sha256(
        json.dumps(value,sort_keys=True,separators=(",",":"),default=str).encode()
    ).hexdigest()


def load_forms()->dict[str,Any]:
    if not FORM_PATH.is_file():
        raise RockV3FormPlannerError("ROCK_FORM_CANDIDATE_FILE_MISSING")
    data=json.loads(FORM_PATH.read_text())
    if data.get("schema")!="ROCK_V3_FORM_CANDIDATES_001":
        raise RockV3FormPlannerError("ROCK_FORM_CANDIDATE_SCHEMA_CHANGED")
    return data


def available_forms(variant_name:str)->dict[str,Any]:
    package=compile_package(variant_name)
    forms=load_forms()
    row=(forms.get("variants") or {}).get(variant_name)
    if row is None:
        raise RockV3FormPlannerError("ROCK_FORM_VARIANT_ROW_MISSING::"+variant_name)
    return {
        "variant":variant_name,
        "variant_package_status":package["status"],
        "form_status":row["status"],
        "form_ids":[x["form_id"] for x in row.get("candidates") or []],
        "required_form_submodes":deepcopy(row.get("required_form_submodes") or []),
        "required_inputs":deepcopy(row.get("required_inputs") or []),
        "reason":row.get("reason"),
    }


def _layout(sections:list[dict[str,Any]])->tuple[list[dict[str,Any]],int]:
    cursor=0
    out=[]
    for index,section in enumerate(sections):
        bars=section.get("bars")
        if type(bars) is not int or bars<=0:
            raise RockV3FormPlannerError("ROCK_FORM_SECTION_BARS_INVALID")
        item=deepcopy(section)
        item["section_index"]=index
        item["start_bar"]=cursor
        item["end_bar_exclusive"]=cursor+bars
        cursor+=bars
        out.append(item)
    return out,cursor


def _base_packet(
    variant_name:str,
    status:str,
    *,
    reason:str|None=None,
    next_gate:str,
)->dict[str,Any]:
    packet={
        "schema":SCHEMA,
        "status":status,
        "genre":"ROCK",
        "selected_variant":variant_name,
        "reason":reason,
        "form_selected":False,
        "planned_sections":[],
        "planned_bar_count":0,
        "source_seed_prototype_bar_count":7,
        "prototype_bar_copy_as_finished_music_allowed":False,
        "new_material_requires_variant_transformation_rules":True,
        "note_events_generated":False,
        "note_execution_ready":False,
        "audio_authority":False,
        "live_runtime_authority":False,
        "finished_composition_authority":False,
        "reasoning_engine_used":False,
        "next_gate":next_gate,
    }
    packet["form_plan_sha256"]=_sha(packet)
    return packet


def plan(
    variant_name:str,
    *,
    form_id:str|None=None,
    form_submode:str|None=None,
    custom_sections:list[dict[str,Any]]|None=None,
)->dict[str,Any]:
    package=compile_package(variant_name)
    forms=load_forms()
    row=(forms.get("variants") or {}).get(variant_name)
    if row is None:
        raise RockV3FormPlannerError("ROCK_FORM_VARIANT_ROW_MISSING::"+variant_name)
    state=row["status"]

    if state=="SECOND_LEVEL_VARIANT_REQUIRED":
        return _base_packet(
            variant_name,
            "BLOCKED_SECOND_LEVEL_VARIANT_RESOLUTION_REQUIRED",
            reason="Broad umbrella label has no single Rock form authority.",
            next_gate="RESOLVE_CHILD_STYLE_BEFORE_FORM",
        )

    if state=="FORM_SUBMODE_REQUIRED":
        allowed=list(row.get("required_form_submodes") or [])
        if form_submode is None:
            packet=_base_packet(
                variant_name,
                "FORM_SUBMODE_REQUIRED",
                reason=row.get("reason"),
                next_gate="SELECT_BLUES_ROCK_FORM_SUBMODE",
            )
            packet["required_form_submodes"]=allowed
            packet["form_plan_sha256"]=_sha({k:v for k,v in packet.items() if k!="form_plan_sha256"})
            return packet
        if form_submode not in allowed:
            raise RockV3FormPlannerError(
                "ROCK_FORM_SUBMODE_NOT_ALLOWED::"+variant_name+"::"+str(form_submode)
            )
        packet=_base_packet(
            variant_name,
            "FORM_SUBMODE_SELECTED__DETAILED_BLUEPRINT_REQUIRED",
            reason=row.get("reason"),
            next_gate="BUILD_SELECTED_BLUES_ROCK_SUBMODE_BLUEPRINT",
        )
        packet["selected_form_submode"]=form_submode
        packet["form_plan_sha256"]=_sha({k:v for k,v in packet.items() if k!="form_plan_sha256"})
        return packet

    if state=="CUSTOM_SECTION_AND_METER_PLAN_REQUIRED":
        if custom_sections is None:
            packet=_base_packet(
                variant_name,
                "CUSTOM_SECTION_AND_METER_PLAN_REQUIRED",
                reason=row.get("reason"),
                next_gate="SUPPLY_PROGRESSIVE_SECTION_AND_METER_PLAN",
            )
            packet["required_inputs"]=deepcopy(row.get("required_inputs") or [])
            packet["form_plan_sha256"]=_sha({k:v for k,v in packet.items() if k!="form_plan_sha256"})
            return packet

        if not isinstance(custom_sections,list) or not custom_sections:
            raise RockV3FormPlannerError("PROGRESSIVE_CUSTOM_SECTIONS_INVALID")
        normalized=[]
        for index,section in enumerate(custom_sections):
            if not isinstance(section,dict):
                raise RockV3FormPlannerError("PROGRESSIVE_CUSTOM_SECTION_NOT_OBJECT")
            name=str(section.get("name") or "").strip()
            role=str(section.get("role") or "").strip()
            meter=str(section.get("meter") or "").strip()
            bars=section.get("bars")
            if not name or not role or type(bars) is not int or bars<=0:
                raise RockV3FormPlannerError("PROGRESSIVE_CUSTOM_SECTION_FIELD_INVALID")
            match=METER_RE.fullmatch(meter)
            if match is None:
                raise RockV3FormPlannerError("PROGRESSIVE_CUSTOM_METER_INVALID::"+meter)
            normalized.append({
                "name":name,
                "bars":bars,
                "meter":meter,
                "role":role,
                "prototype_family":section.get("prototype_family","NEW_PROGRESSIVE_MATERIAL"),
            })
        laid,total=_layout(normalized)
        packet={
            "schema":SCHEMA,
            "status":"PASS_CUSTOM_FORM_PLAN",
            "genre":"ROCK",
            "selected_variant":variant_name,
            "form_selected":True,
            "selected_form_id":"CUSTOM_PROGRESSIVE_PLAN",
            "planned_sections":laid,
            "planned_bar_count":total,
            "source_seed_prototype_bar_count":7,
            "prototype_bar_copy_as_finished_music_allowed":False,
            "new_material_requires_variant_transformation_rules":True,
            "note_events_generated":False,
            "note_execution_ready":False,
            "audio_authority":False,
            "live_runtime_authority":False,
            "finished_composition_authority":False,
            "reasoning_engine_used":False,
            "next_gate":"COMPILE_PROGRESSIVE_SECTION_TRANSFORMATION_AND_METER_EXECUTION",
        }
        packet["form_plan_sha256"]=_sha(packet)
        return packet

    if state!="FORM_CHOICE_REQUIRED":
        raise RockV3FormPlannerError("ROCK_FORM_STATE_UNKNOWN::"+state)

    candidates=list(row.get("candidates") or [])
    ids=[x["form_id"] for x in candidates]
    if form_id is None:
        packet=_base_packet(
            variant_name,
            "FORM_CHOICE_REQUIRED",
            reason="Variant has multiple valid research-candidate forms; no silent default is allowed.",
            next_gate="SELECT_EXPLICIT_ROCK_FORM_CANDIDATE",
        )
        packet["candidate_form_ids"]=ids
        packet["form_plan_sha256"]=_sha({k:v for k,v in packet.items() if k!="form_plan_sha256"})
        return packet

    if form_id not in ids:
        raise RockV3FormPlannerError(
            "ROCK_FORM_ID_NOT_ALLOWED::"+variant_name+"::"+str(form_id)
        )
    candidate=next(x for x in candidates if x["form_id"]==form_id)
    laid,total=_layout(candidate["sections"])
    if total!=candidate.get("total_bars"):
        raise RockV3FormPlannerError("ROCK_FORM_TOTAL_BAR_MISMATCH::"+form_id)
    if total<=7:
        raise RockV3FormPlannerError("ROCK_FORM_DID_NOT_EXPAND_BEYOND_PROTOTYPE")

    packet={
        "schema":SCHEMA,
        "status":"PASS_FORM_PLAN",
        "genre":"ROCK",
        "selected_variant":variant_name,
        "variant_package_sha256":package.get("package_sha256"),
        "form_selected":True,
        "selected_form_id":form_id,
        "planned_sections":laid,
        "planned_bar_count":total,
        "source_seed_prototype_bar_count":7,
        "new_material_required":deepcopy(candidate.get("new_material_required") or []),
        "prototype_bar_copy_as_finished_music_allowed":False,
        "new_material_requires_variant_transformation_rules":True,
        "note_events_generated":False,
        "note_execution_ready":False,
        "audio_authority":False,
        "live_runtime_authority":False,
        "finished_composition_authority":False,
        "reasoning_engine_used":False,
        "source_form_file":str(FORM_PATH.relative_to(REPO)),
        "next_gate":"BUILD_SECTION_TRANSFORMATION_RULES_THEN_EXPAND_NOTES",
    }
    packet["form_plan_sha256"]=_sha(packet)
    return packet
