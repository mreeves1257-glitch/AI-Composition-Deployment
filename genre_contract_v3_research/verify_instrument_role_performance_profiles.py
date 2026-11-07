"""Verify reusable instrument-role performance profiles against approved evidence.

This is a structural guard. It does not render audio and does not promote live.
"""
from __future__ import annotations

from pathlib import Path
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
FORWARD=ROOT/"current_master_forward"
if str(FORWARD) not in sys.path:
    sys.path.insert(0,str(FORWARD))

from instrument_role_performance_profiles import resolve, registry_snapshot

OUT=ROOT/"genre_contract_v3_research"/"INSTRUMENT_ROLE_PERFORMANCE_PROFILES_VERIFY.json"


class VerifyError(RuntimeError):
    pass


def main()->None:
    registry=registry_snapshot()
    if registry.get("status")!="DIAGNOSTIC_APPROVED_PROFILES__NOT_LIVE_RUNTIME_AUTHORITY":
        raise VerifyError("WRONG_REGISTRY_STATUS")
    if registry.get("reasoning_engine_used") is not False:
        raise VerifyError("REASONING_ENGINE_MUST_BE_FALSE")
    if registry.get("live_runtime_authority") is not False:
        raise VerifyError("LIVE_AUTHORITY_MUST_BE_FALSE")

    harmony=resolve("ROCK","ROCK_CORE_V2","HARMONY")
    lead=resolve("ROCK","ROCK_CORE_V2","LEAD")
    bass=resolve("ROCK","ROCK_CORE_V2","BASS")

    # Human-approved guitar treatment.
    hd=harmony["duration_policy"]
    ha=harmony["attack_policy"]
    if float(hd["max_ringing_beats"])!=2.8:
        raise VerifyError("HARMONY_RING_DRIFT")
    if ha["mode"]!="SAFE_NOTE_OFF_PRESERVING_STRUM":
        raise VerifyError("HARMONY_STRUM_MODE_DRIFT")
    if float(ha["note_gap_beats"])!=0.038:
        raise VerifyError("HARMONY_STRUM_GAP_DRIFT")
    if ha["absolute_note_off_preserved"] is not True:
        raise VerifyError("HARMONY_NOTE_OFF_GUARD_MISSING")
    if lead["timing_policy"]["random_jitter"] is not False:
        raise VerifyError("LEAD_RANDOM_JITTER_ENABLED")

    # Human-approved Bass D treatment.
    if bass["human_listening_status"]!="APPROVED_DIAGNOSTIC":
        raise VerifyError("BASS_NOT_APPROVED_DIAGNOSTIC")
    ep=bass["event_policy"]
    if ep["strong_beat_attacks_only"] is not True:
        raise VerifyError("BASS_STRONG_BEAT_RULE_DRIFT")
    if ep["offbeat_reattacks_allowed"] is not False:
        raise VerifyError("BASS_OFFBEAT_REATTACK_ENABLED")
    if ep["offbeat_pitch_changes_allowed"] is not False:
        raise VerifyError("BASS_OFFBEAT_PITCH_CHANGE_ENABLED")

    body=bass["body_layer"]
    attack=bass["attack_layer"]
    if body["mapping"]!="growlybass_clean.sfz":
        raise VerifyError("BASS_BODY_MAPPING_DRIFT")
    if float(body["max_hold_beats"])!=1.50:
        raise VerifyError("BASS_MAX_HOLD_DRIFT")
    if float(body["release_gap_beats"])!=0.20:
        raise VerifyError("BASS_RELEASE_GAP_DRIFT")
    if attack["mapping"]!="growlybass_vicious.sfz":
        raise VerifyError("BASS_ATTACK_MAPPING_DRIFT")
    if float(attack["gate_beats"])!=0.20:
        raise VerifyError("BASS_ATTACK_GATE_DRIFT")
    if float(attack["mix_gain_db"])!=-9.0:
        raise VerifyError("BASS_ATTACK_GAIN_DRIFT")
    if not (
        attack["same_onset_as_body"]
        and attack["same_pitch_as_body"]
        and attack["same_velocity_as_body"]
        and attack["creates_new_rhythmic_attack"] is False
    ):
        raise VerifyError("BASS_ATTACK_IDENTITY_RULE_DRIFT")

    # Check decision evidence.
    decision_path=ROOT/"genre_contract_v3_research"/"ROCK_V3_BASS_ATTACK_HYBRID_HUMAN_DECISION_2026-11-07.json"
    decision=json.loads(decision_path.read_text())
    if decision.get("user_judgment")!="D_PREFERRED":
        raise VerifyError("BASS_D_DECISION_NOT_PRESENT")
    pref=decision["preferred_bass_treatment"]
    expected={
        "held_mapping":"growlybass_clean.sfz",
        "attack_mapping":"growlybass_vicious.sfz",
        "attack_layer_gain_db":-9.0,
        "attack_gate_beats":0.20,
        "strong_beat_only":True,
        "offbeat_reattacks":False,
        "different_pitch_offbeats":0,
        "same_pitch_same_onset_attack_layer":True,
    }
    for key,value in expected.items():
        if pref.get(key)!=value:
            raise VerifyError("BASS_DECISION_MISMATCH::"+key)

    # Check target resource bindings exist and prohibit fallback.
    target=json.loads((FORWARD/"target_registry.json").read_text())
    bindings=target["targets"]["INTERNAL"]["instrument_bindings"]
    bbind=bindings["electric_bass_guitar"]
    if bbind["resource_id"]!="KARORYFER_GROWLYBASS_V1_002":
        raise VerifyError("BASS_RESOURCE_ID_DRIFT")
    if bbind["fallback_policy"]!="NO_SYNTHETIC_SUBSTITUTION":
        raise VerifyError("BASS_FALLBACK_POLICY_DRIFT")
    if "growlybass_clean.sfz" not in bbind["available_mappings"]:
        raise VerifyError("CLEAN_MAPPING_NOT_AVAILABLE")
    if "growlybass_vicious.sfz" not in bbind["available_mappings"]:
        raise VerifyError("VICIOUS_MAPPING_NOT_AVAILABLE")

    for key in ("electric_guitar:RHYTHM_POWER_CHORDS","electric_guitar:LEAD_MELODY"):
        bind=bindings[key]
        if bind["resource_id"]!="KARORYFER_SHINYGUITAR":
            raise VerifyError("GUITAR_RESOURCE_DRIFT::"+key)
        if bind["preferred_mapping"]!="Programs/composer_electric.sfz":
            raise VerifyError("GUITAR_MAPPING_DRIFT::"+key)
        if bind["fallback_policy"]!="NO_SYNTHETIC_SUBSTITUTION":
            raise VerifyError("GUITAR_FALLBACK_DRIFT::"+key)

    report={
        "schema":"INSTRUMENT_ROLE_PERFORMANCE_PROFILES_VERIFY_001",
        "status":"PASS",
        "diagnostic_only":True,
        "registry_sha256":registry["registry_sha256"],
        "verified_profiles":[
            harmony["profile_id"],
            lead["profile_id"],
            bass["profile_id"],
        ],
        "rock_harmony_max_ringing_beats":2.8,
        "rock_harmony_safe_strum":True,
        "rock_lead_treated":True,
        "rock_bass_human_preference":"D",
        "rock_bass_body_mapping":"growlybass_clean.sfz",
        "rock_bass_attack_mapping":"growlybass_vicious.sfz",
        "rock_bass_attack_gain_db":-9.0,
        "rock_bass_offbeat_reattacks":False,
        "target_bindings_verified":True,
        "synthetic_fallback_allowed":False,
        "reasoning_engine_used":False,
        "canonical_policy_modified":False,
        "live_runtime_promoted":False,
        "audio_generated":False,
        "next_gate":"BUILD_APPROVED_ROCK_PERFORMANCE_PACKAGE_FROM_ROLE_PROFILES"
    }
    OUT.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))


if __name__=="__main__":
    main()
