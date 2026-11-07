"""No-audio resource/capability preflight for Rock Core V3 Mode A.

Proves the performed 40-bar score resolves to the intended current resources and
target contexts. It deliberately does NOT promote resource presence to expressive
capability certification.

Mode A's only newly executed expressive behavior is guitar note-duration change.
The INTERNAL target registry currently has no per-resource verified performance-
capability certificate, and Shinyguitar remains production-fidelity not certified.
"""
from __future__ import annotations

from pathlib import Path
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
RUNTIME=ROOT/"composer"/"runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0,str(RUNTIME))

from genre_contract_v3_execution_bridge import snapshot_for
from rock_v3_core_performance_a import execute as perform_a
from instrument_separator import separate_events, verify_instrument_resolution
from instrument_program import InstrumentProgram
from target_program import TargetProgram
from genre_performance_capability_requirements import build as build_caps, validate as validate_caps
from production_resource_resolver import resolve_bindings


def main():
    performed=perform_a()
    if performed.get("status")!="PASS":
        raise RuntimeError("ROCK_MODE_A_NOT_READY_FOR_RESOURCE_PREFLIGHT")
    if performed.get("performance_mode")!="A_GUITAR_DURATION_ONLY":
        raise RuntimeError("ROCK_RESOURCE_PREFLIGHT_WRONG_PERFORMANCE_MODE")
    if performed.get("audio_generated") is not False:
        raise RuntimeError("ROCK_RESOURCE_PREFLIGHT_RECEIVED_AUDIO")

    separated=separate_events("ROCK",performed["events"])
    library=InstrumentProgram(RUNTIME/"instrument_library.json")
    instruments=library.resolve_events(separated["events"])
    if instruments.get("status")!="PASS":
        raise RuntimeError(
            "ROCK_MODE_A_INSTRUMENT_RESOLUTION_FAIL::"+
            json.dumps(instruments.get("missing",[]),sort_keys=True)
        )
    separator_resolution=verify_instrument_resolution(
        separated["manifest"],instruments
    )
    if separator_resolution.get("status")!="PASS":
        raise RuntimeError("ROCK_MODE_A_SEPARATOR_RESOLUTION_FAIL")

    profile=snapshot_for("ROCK")
    caps=build_caps(
        "ROCK",
        profile,
        separated["manifest"]["registrations"],
        separated["events"],
        {"ROCK":profile},
    )
    validate_caps(caps,separated["manifest"]["registrations"])

    cap_by_track={str(x["track_id"]):x for x in caps["entries"]}
    for track in ("HARMONY","LEAD"):
        if track not in cap_by_track:
            raise RuntimeError("ROCK_MODE_A_GUITAR_CAPABILITY_ENTRY_MISSING::"+track)
        controls=set(cap_by_track[track].get("required_continuous_controls") or [])
        if "NOTE_LENGTH_RESPONSE" not in controls:
            raise RuntimeError("ROCK_MODE_A_NOTE_LENGTH_RESPONSE_REQUIREMENT_MISSING::"+track)

    instruments=dict(
        instruments,
        performance_capability_requirements=caps,
        instrument_separator_resolution=separator_resolution,
    )
    target=TargetProgram(RUNTIME/"target_registry.json").resolve(
        "INTERNAL",instruments
    )
    if target.get("status")!="PASS":
        raise RuntimeError(
            "ROCK_MODE_A_TARGET_RESOURCE_RESOLUTION_FAIL::"+
            json.dumps(target.get("missing",[]),sort_keys=True)
        )
    if target.get("render_allowed") is not False:
        raise RuntimeError("ROCK_MODE_A_RESOURCE_PREFLIGHT_GRANTED_RENDER")
    if target.get("audio_backend_verified") is not False:
        raise RuntimeError("ROCK_MODE_A_RESOURCE_PREFLIGHT_CLAIMED_AUDIO_BACKEND")

    by_track={str(x["track_id"]):x for x in target["resolved_resources"]}
    for track in ("HARMONY","LEAD","BASS","KICK","SNARE","HAT"):
        if track not in by_track:
            raise RuntimeError("ROCK_MODE_A_TARGET_TRACK_MISSING::"+track)

    rhythm=by_track["HARMONY"]["resource"]
    lead=by_track["LEAD"]["resource"]
    if rhythm.get("resource_id")!="KARORYFER_SHINYGUITAR":
        raise RuntimeError("ROCK_MODE_A_RHYTHM_GUITAR_WRONG_RESOURCE")
    if lead.get("resource_id")!="KARORYFER_SHINYGUITAR":
        raise RuntimeError("ROCK_MODE_A_LEAD_GUITAR_WRONG_RESOURCE")
    if rhythm.get("preferred_mapping")!="Programs/composer_electric.sfz":
        raise RuntimeError("ROCK_MODE_A_RHYTHM_MAPPING_CHANGED")
    if lead.get("preferred_mapping")!="Programs/composer_electric.sfz":
        raise RuntimeError("ROCK_MODE_A_LEAD_MAPPING_CHANGED")
    if rhythm.get("production_fidelity_status")!="NOT_YET_CERTIFIED":
        raise RuntimeError("ROCK_MODE_A_RHYTHM_FIDELITY_STATUS_UNEXPECTED")
    if lead.get("production_fidelity_status")!="NOT_YET_CERTIFIED":
        raise RuntimeError("ROCK_MODE_A_LEAD_FIDELITY_STATUS_UNEXPECTED")
    if rhythm.get("fallback_policy")!="NO_SYNTHETIC_SUBSTITUTION":
        raise RuntimeError("ROCK_MODE_A_RHYTHM_FALLBACK_POLICY_CHANGED")
    if lead.get("fallback_policy")!="NO_SYNTHETIC_SUBSTITUTION":
        raise RuntimeError("ROCK_MODE_A_LEAD_FALLBACK_POLICY_CHANGED")

    # Target role routing must preserve the one-instrument/two-context design.
    requests=instruments.get("source_requests") or []
    guitar_roles={
        str(x.get("track_id")):x.get("role")
        for x in requests if x.get("instrument_id")=="electric_guitar"
    }
    if guitar_roles.get("HARMONY")!="RHYTHM_POWER_CHORDS":
        raise RuntimeError("ROCK_MODE_A_RHYTHM_TARGET_ROLE_WRONG")
    if guitar_roles.get("LEAD")!="LEAD_MELODY":
        raise RuntimeError("ROCK_MODE_A_LEAD_TARGET_ROLE_WRONG")

    # Mapping-file presence is proven after the pinned-resource acquisition step.
    disk=resolve_bindings(RUNTIME)
    required_keys=(
        "electric_guitar:RHYTHM_POWER_CHORDS",
        "electric_guitar:LEAD_MELODY",
        "electric_bass_guitar",
        "kick_drum_rock",
        "snare_drum",
        "hi_hat",
    )
    presence={key:disk.get(key) for key in required_keys}
    missing={
        key:value for key,value in presence.items()
        if not value or value.get("status")!="MAPPING_FOUND"
    }
    if missing:
        raise RuntimeError(
            "ROCK_MODE_A_RESOURCE_FILE_MISSING::"+
            json.dumps(missing,sort_keys=True)
        )

    # Resource bindings prove identity and file graph, not expressive response.
    for resource in (rhythm,lead):
        if "verified_performance_capabilities" in resource:
            raise RuntimeError(
                "ROCK_MODE_A_UNEXPECTED_TARGET_CAPABILITY_CERTIFICATE_PRESENT"
            )

    summary={
        "status":"PASS_WITH_CAPABILITY_CERTIFICATION_BLOCK",
        "diagnostic_only":True,
        "genre":"ROCK",
        "profile_id":"ROCK_CORE_V2",
        "performance_mode":"A_GUITAR_DURATION_ONLY",
        "bar_count":performed["bar_count"],
        "event_count":performed["event_count"],
        "resource_identity_resolution":"PASS",
        "resource_mapping_file_presence":"PASS",
        "instrument_separator_resolution":"PASS",
        "guitar_contexts":{
            "HARMONY":{
                "instrument_id":"electric_guitar",
                "target_role":"RHYTHM_POWER_CHORDS",
                "resource_id":rhythm["resource_id"],
                "mapping":rhythm["preferred_mapping"],
                "production_fidelity_status":rhythm["production_fidelity_status"],
            },
            "LEAD":{
                "instrument_id":"electric_guitar",
                "target_role":"LEAD_MELODY",
                "resource_id":lead["resource_id"],
                "mapping":lead["preferred_mapping"],
                "production_fidelity_status":lead["production_fidelity_status"],
            },
        },
        "mode_a_new_expressive_requirement":"NOTE_LENGTH_RESPONSE",
        "note_length_response_required_on_tracks":["HARMONY","LEAD"],
        "target_performance_capability_certificate_present":False,
        "target_capability_certification_status":"BLOCKED_NOT_YET_PROVEN",
        "production_fidelity_certification_status":"BLOCKED_NOT_YET_CERTIFIED",
        "render_allowed":False,
        "audio_generated":False,
        "audio_backend_verified":False,
        "finished_composition_authority":False,
        "live_runtime_promoted":False,
        "result":(
            "The 40-bar Rock Core Mode A score resolves to the intended Shinyguitar, "
            "Growlybass and Big Rusty resources with separate rhythm/lead guitar target "
            "contexts and all mapping files present. Resource identity is proven, but "
            "the target registry does not yet certify Shinyguitar NOTE_LENGTH_RESPONSE "
            "or production fidelity, so rendering/listening remains blocked."
        ),
        "next_gate":"VERIFY_SHINYGUITAR_MODE_A_NOTE_LENGTH_RESPONSE_WITH_ISOLATED_RESOURCE_TEST_BEFORE_COMPOSITION_AUDIO",
    }
    out=ROOT/"genre_contract_v3_research"/"ROCK_V3_CORE_PERFORMANCE_A_RESOURCE_PREFLIGHT.json"
    out.write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps(summary,indent=2))


if __name__=="__main__":
    main()
