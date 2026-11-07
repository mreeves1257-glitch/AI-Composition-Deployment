"""Audit the Rock Core V3 performance-realization plan."""
from __future__ import annotations

from pathlib import Path
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
FORWARD=ROOT/"current_master_forward"
if str(FORWARD) not in sys.path:
    sys.path.insert(0,str(FORWARD))

from rock_v3_core_performance_plan import build


def main():
    plan=build()
    if plan.get("status")!="PASS":
        raise RuntimeError("ROCK_PERFORMANCE_PLAN_NOT_PASS")
    if plan.get("genre")!="ROCK" or plan.get("profile_id")!="ROCK_CORE_V2":
        raise RuntimeError("ROCK_PERFORMANCE_PLAN_IDENTITY_DRIFT")
    if plan.get("resolved_variant") is not None:
        raise RuntimeError("ROCK_PERFORMANCE_PLAN_SILENTLY_CLAIMED_VARIANT")
    if plan.get("family_baseline_only") is not True:
        raise RuntimeError("ROCK_PERFORMANCE_PLAN_NOT_FAMILY_BASELINE")

    for key in (
        "reasoning_engine_used","notes_added","pitches_changed",
        "velocities_changed","drum_onsets_changed","audio_generated",
        "audio_authority","finished_composition_authority",
        "live_runtime_authority","listening_approval",
    ):
        if plan.get(key) is not False:
            raise RuntimeError("ROCK_PERFORMANCE_PLAN_PREMATURE_FLAG::"+key)

    authority=plan.get("v3_performance_authority") or {}
    for key in (
        "articulation_behavior","dynamic_behavior","timing_humanization_behavior",
        "continuous_performance_control","interaction_rules",
    ):
        if not authority.get(key):
            raise RuntimeError("ROCK_PERFORMANCE_V3_AUTHORITY_MISSING::"+key)
    if "no independent random jitter" not in authority["timing_humanization_behavior"]:
        raise RuntimeError("ROCK_PERFORMANCE_RANDOM_JITTER_GUARD_LOST")

    roles=plan.get("role_plans") or {}
    if set(roles)!={"HARMONY","LEAD","BASS","KICK","SNARE","HAT"}:
        raise RuntimeError(
            "ROCK_PERFORMANCE_ROLE_PLAN_SET_WRONG::"+json.dumps(sorted(roles))
        )

    rhythm=roles["HARMONY"]
    if rhythm["duration_policy"].get("v3_harmony_safety_cap")!="DO_NOT_CROSS_NEXT_BAR_HARMONY_CHANGE_WITHOUT_EXPLICIT_TIE":
        raise RuntimeError("RHYTHM_GUITAR_HARMONY_SAFETY_CAP_MISSING")
    strum=rhythm["attack_strum_candidate"]
    if strum.get("listening_approved") is not False or strum.get("default_enabled") is not False:
        raise RuntimeError("UNAPPROVED_STRUM_CANDIDATE_AUTO_ENABLED")
    if strum.get("note_gap_beats")!=0.038:
        raise RuntimeError("ROCK_STRUM_RESEARCH_VALUE_DRIFT")

    lead=roles["LEAD"]
    if lead["duration_policy"].get("v3_harmony_safety_cap")!="DO_NOT_CROSS_NEXT_BAR_HARMONY_CHANGE_WITHOUT_EXPLICIT_TIE":
        raise RuntimeError("LEAD_GUITAR_HARMONY_SAFETY_CAP_MISSING")
    if lead["timing_policy"].get("random_jitter") is not False:
        raise RuntimeError("LEAD_RANDOM_JITTER_ALLOWED")
    if "SUSTAIN_ACROSS_UNVERIFIED_HARMONY_CHANGE" not in lead.get("forbidden",[]):
        raise RuntimeError("LEAD_CROSS_HARMONY_SUSTAIN_NOT_FORBIDDEN")

    bass=roles["BASS"]
    sustain=bass["sustain_candidate"]
    if sustain.get("listening_approved") is not False or sustain.get("default_enabled") is not False:
        raise RuntimeError("UNAPPROVED_BASS_SUSTAIN_AUTO_ENABLED")

    for role in ("KICK","SNARE","HAT"):
        row=roles[role]
        if row.get("random_jitter") is not False:
            raise RuntimeError("DRUM_RANDOM_JITTER_ALLOWED::"+role)
        if row.get("new_hits_allowed") is not False:
            raise RuntimeError("PERFORMANCE_STAGE_NEW_DRUM_HITS_ALLOWED::"+role)

    shared=plan.get("shared_groove_policy") or {}
    if shared.get("random_independent_offsets_allowed") is not False:
        raise RuntimeError("SHARED_GROOVE_INDEPENDENT_RANDOM_OFFSETS_ALLOWED")
    if shared.get("current_candidate_action")!="KEEP_COMPOSITION_ONSETS_EXACT":
        raise RuntimeError("MODE_A_SHOULD_KEEP_COMPOSITION_ONSETS_EXACT")

    modes=plan.get("candidate_modes") or {}
    if set(modes)!={
        "A_GUITAR_DURATION_ONLY",
        "B_GUITAR_DURATION_PLUS_STRUM",
        "C_GUITAR_PLUS_STRUM_PLUS_BASS_SUSTAIN",
    }:
        raise RuntimeError("ROCK_PERFORMANCE_CANDIDATE_MODE_SET_CHANGED")
    a=modes["A_GUITAR_DURATION_ONLY"]
    if not (
        a.get("apply_guitar_duration_policy") is True
        and a.get("apply_rhythm_guitar_strum_candidate") is False
        and a.get("apply_bass_sustain_candidate") is False
    ):
        raise RuntimeError("ROCK_MODE_A_SCOPE_CHANGED")
    if plan.get("recommended_first_symbolic_performance_mode")!="A_GUITAR_DURATION_ONLY":
        raise RuntimeError("ROCK_MODE_A_NOT_FIRST_SYMBOLIC_CANDIDATE")

    summary={
        "status":"PASS",
        "diagnostic_only":True,
        "genre":"ROCK",
        "profile_id":"ROCK_CORE_V2",
        "recommended_mode":"A_GUITAR_DURATION_ONLY",
        "mode_a_changes":"GUITAR_NOTE_DURATIONS_ONLY",
        "strum_candidate_default_enabled":False,
        "bass_sustain_candidate_default_enabled":False,
        "random_jitter_allowed":False,
        "drum_onset_changes_allowed":False,
        "new_drum_hits_allowed":False,
        "harmony_change_duration_cap_required":True,
        "audio_generated":False,
        "finished_composition_authority":False,
        "listening_approval":False,
        "result":(
            "Rock Core performance planning is now explicit and staged. The first "
            "candidate may change only electric-guitar note durations, must stop at "
            "planned harmony changes, and leaves strum timing and bass sustain as "
            "separate unapproved research variables."
        ),
        "next_gate":"EXECUTE_AND_AUDIT_MODE_A_GUITAR_DURATION_ONLY",
        "performance_plan_sha256":plan["performance_plan_sha256"],
    }
    out=ROOT/"genre_contract_v3_research"/"ROCK_V3_CORE_PERFORMANCE_PLAN_AUDIT.json"
    out.write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps(summary,indent=2))


if __name__=="__main__":
    main()
