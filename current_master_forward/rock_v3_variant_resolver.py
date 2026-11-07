"""Rock V3 variant-resolution gate.

Broad ROCK_CORE_V2 is not a production subgenre. The Genre Contract V3 explicitly
requires a resolved Rock variant before variant-specific form, groove, harmony,
transition or foreground rules can be treated as a finished composition package.

This module validates variant identity only. It does not invent missing
variant-specific musical rules and it has no audio authority.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any

from genre_contract_v3_execution_bridge import contract_for, snapshot_for

SCHEMA="ROCK_V3_VARIANT_RESOLVER_001"


class RockV3VariantResolutionError(RuntimeError):
    pass


def _sha(value:Any)->str:
    return hashlib.sha256(
        json.dumps(value,sort_keys=True,separators=(",",":"),default=str).encode()
    ).hexdigest()


def candidate_variants()->list[str]:
    contract=contract_for("ROCK")
    vr=contract.get("variant_resolution") or {}
    candidates=list(vr.get("candidate_variants") or [])
    if not candidates:
        raise RockV3VariantResolutionError("ROCK_V3_CANDIDATE_VARIANTS_MISSING")
    if len(candidates)!=len(set(candidates)):
        raise RockV3VariantResolutionError("ROCK_V3_CANDIDATE_VARIANTS_DUPLICATED")
    return candidates


def resolve(variant_name:str|None=None, *, variant_cues_present:bool=False)->dict[str,Any]:
    contract=contract_for("ROCK")
    snapshot=snapshot_for("ROCK")
    vr=contract.get("variant_resolution") or {}
    candidates=candidate_variants()

    if vr.get("status")!="REQUIRED_BEFORE_PERCENTAGES":
        raise RockV3VariantResolutionError("ROCK_V3_VARIANT_STATUS_CHANGED")
    hard_rule=vr.get("hard_rule")
    if not hard_rule:
        raise RockV3VariantResolutionError("ROCK_V3_VARIANT_HARD_RULE_MISSING")

    if variant_name is None:
        if variant_cues_present:
            status="ROCK_VARIANT_REQUIRED_BY_AVAILABLE_CUES"
            family_baseline_music_allowed=False
            next_gate="RESOLVE_VARIANT_FROM_AVAILABLE_CUES"
        else:
            status="ROCK_CORE_BASELINE_ALLOWED__NO_VARIANT_CUES"
            family_baseline_music_allowed=True
            next_gate="FAMILY_BASELINE_FORM_AND_MUSICAL_VALIDATION"
        packet={
            "schema":SCHEMA,
            "status":status,
            "genre":"ROCK",
            "profile_id":snapshot.get("profile_id"),
            "selected_variant":None,
            "candidate_variants":candidates,
            "hard_rule":hard_rule,
            "variant_cues_present":bool(variant_cues_present),
            "family_baseline_music_allowed":family_baseline_music_allowed,
            "family_baseline_identity":"ROCK_CORE_V2",
            "family_baseline_must_not_claim_subgenre":True,
            "variant_specific_music_ready":False,
            "broad_rock_may_not_stand_in_for_variant_when_cues_available":True,
            "audio_authority":False,
            "live_runtime_authority":False,
            "reasoning_engine_used":False,
            "next_gate":next_gate,
        }
        packet["variant_packet_sha256"]=_sha(packet)
        return packet

    if variant_name not in candidates:
        raise RockV3VariantResolutionError(
            "ROCK_VARIANT_NOT_IN_V3_CANDIDATES::"+str(variant_name)
        )

    # Selection is recognized, but selection alone is not permission to fabricate
    # variant-specific tempo/groove/form/harmony rules. Those must be compiled from
    # evidence in a separate package.
    packet={
        "schema":SCHEMA,
        "status":"ROCK_VARIANT_SELECTED__MUSICAL_PACKAGE_RESEARCH_REQUIRED",
        "genre":"ROCK",
        "profile_id":snapshot.get("profile_id"),
        "selected_variant":variant_name,
        "candidate_variants":candidates,
        "hard_rule":hard_rule,
        "variant_specific_music_ready":False,
        "selection_is_identity_only":True,
        "variant_cues_present":True,
        "family_baseline_music_allowed":False,
        "family_baseline_must_not_claim_subgenre":True,
        "broad_rock_may_not_stand_in_for_variant_when_cues_available":True,
        "musical_grammar":deepcopy(contract.get("musical_grammar")),
        "audio_authority":False,
        "live_runtime_authority":False,
        "reasoning_engine_used":False,
        "next_gate":"BUILD_EVIDENCE_BACKED_ROCK_VARIANT_MUSICAL_PACKAGE",
    }
    packet["variant_packet_sha256"]=_sha(packet)
    return packet
