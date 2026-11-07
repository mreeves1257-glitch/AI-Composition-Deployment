"""Build one reusable Rock V3 approved-performance package.

This module composes already-validated/human-approved diagnostic behavior. It
does not invent a new musical treatment.

Included approved roles
-----------------------
HARMONY
- electric guitar duration treatment;
- 2.8-beat max ring;
- safe note-off-preserving strum.

LEAD
- treated melodic duration behavior.

BASS D
- strong-beat-only held body;
- Clean mapping for body;
- same-onset/same-pitch Vicious transient at -9 dB;
- transient gate 0.20 beat;
- no offbeat re-attacks.

Drums are deliberately NOT declared approved here. Their symbolic events remain
available in the score, but this package marks their performance/render status
as pending a separate controlled gate.

Diagnostic branch only. No live authority. No reasoning engine.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any

from instrument_role_performance_profiles import resolve
from rock_v3_bass_held_tone_candidate import execute as execute_held_score

SCHEMA="ROCK_V3_APPROVED_PERFORMANCE_PACKAGE_001"
GENRE="ROCK"
GENRE_PROFILE_ID="ROCK_CORE_V2"
EPS=1e-9


class RockV3ApprovedPerformancePackageError(RuntimeError):
    pass


def _sha(value:Any)->str:
    return hashlib.sha256(
        json.dumps(value,sort_keys=True,separators=(",",":"),default=str).encode()
    ).hexdigest()


def _is_integer_beat(value:float)->bool:
    return abs(value-round(value))<=EPS


def build()->dict[str,Any]:
    score=execute_held_score()
    if score.get("status")!="PASS":
        raise RockV3ApprovedPerformancePackageError("HELD_SCORE_NOT_PASS")

    harmony_profile=resolve(GENRE,GENRE_PROFILE_ID,"HARMONY")
    lead_profile=resolve(GENRE,GENRE_PROFILE_ID,"LEAD")
    bass_profile=resolve(GENRE,GENRE_PROFILE_ID,"BASS")

    events=[deepcopy(e) for e in score["events"]]
    harmony=[
        deepcopy(e) for e in events
        if str(e.get("track_id","")).upper()=="HARMONY"
    ]
    lead=[
        deepcopy(e) for e in events
        if str(e.get("track_id","")).upper()=="LEAD"
    ]
    bass=[
        deepcopy(e) for e in events
        if str(e.get("track_id","")).upper()=="BASS"
    ]

    if not harmony or not lead or not bass:
        raise RockV3ApprovedPerformancePackageError("APPROVED_ROLE_EVENTS_MISSING")

    # Confirm the score really contains the approved guitar strum treatment.
    strummed=[e for e in harmony if e.get("strum_execution_mode")]
    if not strummed:
        raise RockV3ApprovedPerformancePackageError("APPROVED_STRUM_NOT_PRESENT")
    if any(
        e.get("strum_execution_mode")!="HARMONY_ATTACK_STAGGER_NOTE_OFF_PRESERVED"
        for e in strummed
    ):
        raise RockV3ApprovedPerformancePackageError("STRUM_MODE_DRIFT")
    if any(e.get("note_off_preserved") is not True for e in strummed):
        raise RockV3ApprovedPerformancePackageError("STRUM_NOTE_OFF_GUARD_DRIFT")

    # Confirm held bass score contains no offbeat bass re-attacks.
    if any(not _is_integer_beat(float(e["start_beat"])) for e in bass):
        raise RockV3ApprovedPerformancePackageError("OFFBEAT_BASS_EVENT_PRESENT")

    body=bass_profile["body_layer"]
    attack=bass_profile["attack_layer"]

    # Build attack render events as a layer, not a new compositional rhythm.
    attack_events=[]
    for event in bass:
        a=deepcopy(event)
        original=float(a["duration_beats"])
        a["duration_beats"]=round(min(original,float(attack["gate_beats"])),6)
        a["performance_layer"]="BASS_ATTACK_TRANSIENT"
        a["performance_parent_profile_id"]=bass_profile["profile_id"]
        a["same_rhythmic_event_as_body"]=True
        attack_events.append(a)

    if len(attack_events)!=len(bass):
        raise RockV3ApprovedPerformancePackageError("ATTACK_LAYER_COUNT_DRIFT")
    for body_event,attack_event in zip(bass,attack_events):
        if (
            float(body_event["start_beat"])!=float(attack_event["start_beat"])
            or int(body_event["midi"])!=int(attack_event["midi"])
            or int(body_event["velocity"])!=int(attack_event["velocity"])
        ):
            raise RockV3ApprovedPerformancePackageError(
                "ATTACK_LAYER_IDENTITY_DRIFT"
            )

    render_layers={
        "HARMONY":{
            "track_role":"HARMONY",
            "profile_id":harmony_profile["profile_id"],
            "events":harmony,
            "resource_id":harmony_profile["resource_intent"]["resource_id"],
            "mapping":harmony_profile["resource_intent"]["mapping"],
            "mix_gain_db":-5.0,
            "approval_status":"HUMAN_APPROVED_DIAGNOSTIC",
        },
        "LEAD":{
            "track_role":"LEAD",
            "profile_id":lead_profile["profile_id"],
            "events":lead,
            "resource_id":lead_profile["resource_intent"]["resource_id"],
            "mapping":lead_profile["resource_intent"]["mapping"],
            "mix_gain_db":-6.0,
            "approval_status":"HUMAN_APPROVED_DIAGNOSTIC",
        },
        "BASS_BODY":{
            "track_role":"BASS",
            "profile_id":bass_profile["profile_id"],
            "events":bass,
            "resource_id":body["resource_id"],
            "mapping":body["mapping"],
            "mix_gain_db":0.0,
            "approval_status":"HUMAN_APPROVED_DIAGNOSTIC",
        },
        "BASS_ATTACK":{
            "track_role":"BASS",
            "profile_id":bass_profile["profile_id"],
            "events":attack_events,
            "resource_id":attack["resource_id"],
            "mapping":attack["mapping"],
            "mix_gain_db":float(attack["mix_gain_db"]),
            "gate_beats":float(attack["gate_beats"]),
            "same_rhythmic_events_as":"BASS_BODY",
            "approval_status":"HUMAN_APPROVED_DIAGNOSTIC",
        },
    }

    unresolved_roles={}
    for role in ("KICK","SNARE","HAT","PERCUSSION"):
        count=sum(
            1 for e in events
            if str(e.get("track_id","")).upper()==role
        )
        if count:
            unresolved_roles[role]={
                "symbolic_event_count":count,
                "performance_status":"PRESERVE_SYMBOLIC_SOURCE__NOT_INCLUDED_IN_APPROVED_RENDER_PACKAGE",
                "reason":"SEPARATE_CONTROLLED_ROLE_GATE_REQUIRED",
            }

    packet={
        "schema":SCHEMA,
        "status":"PASS",
        "diagnostic_only":True,
        "genre":GENRE,
        "genre_profile_id":GENRE_PROFILE_ID,
        "source_execution_sha256":score["execution_sha256"],
        "tempo_bpm":score["tempo_bpm"],
        "bar_count":score["bar_count"],
        "score_events":events,
        "score_event_count":len(events),
        "approved_role_profiles":{
            "HARMONY":{
                "profile_id":harmony_profile["profile_id"],
                "profile_sha256":harmony_profile["profile_sha256"],
            },
            "LEAD":{
                "profile_id":lead_profile["profile_id"],
                "profile_sha256":lead_profile["profile_sha256"],
            },
            "BASS":{
                "profile_id":bass_profile["profile_id"],
                "profile_sha256":bass_profile["profile_sha256"],
            },
        },
        "render_layers":render_layers,
        "approved_render_layer_order":[
            "BASS_BODY",
            "BASS_ATTACK",
            "HARMONY",
            "LEAD",
        ],
        "unresolved_roles":unresolved_roles,
        "bass_offbeat_reattack_count":0,
        "bass_attack_layer_creates_new_rhythm":False,
        "new_performance_variables_added":False,
        "reasoning_engine_used":False,
        "canonical_policy_modified":False,
        "live_runtime_authority":False,
        "audio_generated":False,
        "listening_approval_scope":"INDIVIDUAL_INCLUDED_ROLE_TREATMENTS_ONLY",
        "full_ensemble_listening_approval":False,
        "next_gate":"USE_THIS_PACKAGE_AS_SINGLE_SOURCE_FOR_APPROVED_ROCK_ROLE_RENDERING__DRUMS_SEPARATE",
    }
    packet["package_sha256"]=_sha({
        k:v for k,v in packet.items() if k!="package_sha256"
    })
    return packet


if __name__=="__main__":
    print(json.dumps(build(),indent=2))
