"""Verify the reusable approved Rock V3 performance package.

Structural only: no audio, no live promotion.
"""
from __future__ import annotations

from pathlib import Path
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
FORWARD=ROOT/"current_master_forward"
if str(FORWARD) not in sys.path:
    sys.path.insert(0,str(FORWARD))

from rock_v3_approved_performance_package import build

OUT=ROOT/"genre_contract_v3_research"/"ROCK_V3_APPROVED_PERFORMANCE_PACKAGE_VERIFY.json"
EPS=1e-9


class VerifyError(RuntimeError):
    pass


def _is_integer(value:float)->bool:
    return abs(value-round(value))<=EPS


def main()->None:
    package=build()
    if package.get("status")!="PASS":
        raise VerifyError("PACKAGE_NOT_PASS")
    if package.get("new_performance_variables_added") is not False:
        raise VerifyError("NEW_VARIABLES_ADDED")
    if package.get("reasoning_engine_used") is not False:
        raise VerifyError("REASONING_ENGINE_USED")
    if package.get("live_runtime_authority") is not False:
        raise VerifyError("LIVE_AUTHORITY_SET")

    layers=package["render_layers"]
    expected_order=["BASS_BODY","BASS_ATTACK","HARMONY","LEAD"]
    if package["approved_render_layer_order"]!=expected_order:
        raise VerifyError("LAYER_ORDER_DRIFT")

    body=layers["BASS_BODY"]
    attack=layers["BASS_ATTACK"]
    harmony=layers["HARMONY"]
    lead=layers["LEAD"]

    if body["mapping"]!="growlybass_clean.sfz":
        raise VerifyError("BASS_BODY_MAPPING_DRIFT")
    if attack["mapping"]!="growlybass_vicious.sfz":
        raise VerifyError("BASS_ATTACK_MAPPING_DRIFT")
    if float(attack["mix_gain_db"])!=-9.0:
        raise VerifyError("BASS_ATTACK_GAIN_DRIFT")
    if float(attack["gate_beats"])!=0.20:
        raise VerifyError("BASS_ATTACK_GATE_DRIFT")
    if harmony["mapping"]!="Programs/composer_electric.sfz":
        raise VerifyError("HARMONY_MAPPING_DRIFT")
    if lead["mapping"]!="Programs/composer_electric.sfz":
        raise VerifyError("LEAD_MAPPING_DRIFT")
    if float(harmony["mix_gain_db"])!=-5.0:
        raise VerifyError("HARMONY_GAIN_DRIFT")
    if float(lead["mix_gain_db"])!=-6.0:
        raise VerifyError("LEAD_GAIN_DRIFT")

    body_events=body["events"]
    attack_events=attack["events"]
    if not body_events or len(body_events)!=len(attack_events):
        raise VerifyError("BASS_LAYER_COUNT_DRIFT")
    if any(not _is_integer(float(e["start_beat"])) for e in body_events):
        raise VerifyError("OFFBEAT_BASS_BODY_EVENT")
    if any(not _is_integer(float(e["start_beat"])) for e in attack_events):
        raise VerifyError("OFFBEAT_BASS_ATTACK_EVENT")

    for b,a in zip(body_events,attack_events):
        if (
            float(b["start_beat"])!=float(a["start_beat"])
            or int(b["midi"])!=int(a["midi"])
            or int(b["velocity"])!=int(a["velocity"])
        ):
            raise VerifyError("BASS_ATTACK_NOT_SAME_EVENT")
        if float(a["duration_beats"])>0.20+EPS:
            raise VerifyError("BASS_ATTACK_TOO_LONG")
        if a.get("same_rhythmic_event_as_body") is not True:
            raise VerifyError("BASS_ATTACK_LAYER_MARKER_MISSING")

    # Guitar must carry the already-approved treatment.
    h_events=harmony["events"]
    if not h_events:
        raise VerifyError("NO_HARMONY_EVENTS")
    strummed=[e for e in h_events if e.get("strum_execution_mode")]
    if not strummed:
        raise VerifyError("NO_STRUMMED_HARMONY_EVENTS")
    if any(
        e.get("strum_execution_mode")!="HARMONY_ATTACK_STAGGER_NOTE_OFF_PRESERVED"
        for e in strummed
    ):
        raise VerifyError("STRUM_MODE_DRIFT")
    if any(e.get("note_off_preserved") is not True for e in strummed):
        raise VerifyError("STRUM_NOTE_OFF_DRIFT")

    if not lead["events"]:
        raise VerifyError("NO_LEAD_EVENTS")

    # Drums must not sneak into the approved render layer set.
    forbidden_layer_roles={"KICK","SNARE","HAT","PERCUSSION","DRUMS"}
    for name,layer in layers.items():
        if str(layer.get("track_role","")).upper() in forbidden_layer_roles:
            raise VerifyError("DRUM_LAYER_INCLUDED::"+name)

    unresolved=package.get("unresolved_roles") or {}
    if not any(role in unresolved for role in ("KICK","SNARE","HAT")):
        raise VerifyError("DRUMS_NOT_MARKED_SEPARATE")

    report={
        "schema":"ROCK_V3_APPROVED_PERFORMANCE_PACKAGE_VERIFY_001",
        "status":"PASS",
        "diagnostic_only":True,
        "package_sha256":package["package_sha256"],
        "score_event_count":package["score_event_count"],
        "approved_layer_order":expected_order,
        "approved_role_profile_ids":{
            role:data["profile_id"]
            for role,data in package["approved_role_profiles"].items()
        },
        "bass_body_event_count":len(body_events),
        "bass_attack_event_count":len(attack_events),
        "bass_offbeat_event_count":0,
        "bass_attack_creates_new_rhythm":False,
        "harmony_event_count":len(harmony["events"]),
        "lead_event_count":len(lead["events"]),
        "drums_in_approved_render_layers":False,
        "drums_marked_separate":True,
        "new_performance_variables_added":False,
        "reasoning_engine_used":False,
        "audio_generated":False,
        "canonical_policy_modified":False,
        "live_runtime_promoted":False,
        "next_gate":"REFERENCE_PACKAGE_FROM_ROCK_PERFORMANCE_PLAN_WITHOUT_CHANGING_MUSIC"
    }
    OUT.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))


if __name__=="__main__":
    main()
