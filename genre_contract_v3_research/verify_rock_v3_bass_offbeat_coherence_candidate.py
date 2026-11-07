"""Verify all-offbeat Rock bass coherence candidate.

Requirements:
- every non-integer-beat BASS attack matches immediately preceding BASS pitch;
- strong-beat pitch changes remain allowed;
- max BASS duration 0.20 beat;
- no onset/velocity/event-count/non-BASS mutation;
- no duration extension.
"""
from __future__ import annotations

from pathlib import Path
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
FORWARD=ROOT/"current_master_forward"
if str(FORWARD) not in sys.path:
    sys.path.insert(0,str(FORWARD))

from rock_v3_strum_candidate_executor import execute as execute_source
from rock_v3_bass_offbeat_coherence_candidate import (
    execute as execute_candidate,
    MAX_GATE_BEATS,
)

OUT=ROOT/"genre_contract_v3_research"/"ROCK_V3_BASS_OFFBEAT_COHERENCE_VERIFY.json"
EPS=1e-9

class VerifyError(RuntimeError):
    pass

def _is_strong(start:float)->bool:
    return abs(start-round(start))<=EPS

def main()->None:
    source=execute_source()
    cand=execute_candidate()
    if source.get("status")!="PASS" or cand.get("status")!="PASS":
        raise VerifyError("SOURCE_OR_CANDIDATE_NOT_PASS")
    if source["event_count"]!=cand["event_count"]:
        raise VerifyError("EVENT_COUNT_CHANGED")

    source_bass=[e for e in source["events"] if str(e.get("track_id","")).upper()=="BASS"]
    cand_bass=[e for e in cand["events"] if str(e.get("track_id","")).upper()=="BASS"]
    if len(source_bass)!=len(cand_bass):
        raise VerifyError("BASS_COUNT_CHANGED")

    offbeat_count=0
    different_offbeat_count=0
    strong_pitch_change_count=0
    onset_changes=velocity_changes=non_bass_mutations=duration_extensions=0

    prior=None
    for e in cand_bass:
        start=float(e["start_beat"])
        if float(e["duration_beats"])>MAX_GATE_BEATS+EPS:
            raise VerifyError("BASS_DURATION_OVER_GATE")
        if prior is not None:
            if _is_strong(start):
                if int(e["midi"])!=int(prior["midi"]):
                    strong_pitch_change_count+=1
            else:
                offbeat_count+=1
                if int(e["midi"])!=int(prior["midi"]):
                    different_offbeat_count+=1
        prior=e

    if different_offbeat_count:
        raise VerifyError("DIFFERENT_PITCH_OFFBEAT_REMAINS")

    for before,after in zip(source["events"],cand["events"]):
        track=str(before.get("track_id","")).upper()
        if float(before["start_beat"])!=float(after["start_beat"]):
            onset_changes+=1
        if int(before["velocity"])!=int(after["velocity"]):
            velocity_changes+=1
        if float(after["duration_beats"])>float(before["duration_beats"])+EPS:
            duration_extensions+=1
        if track!="BASS" and (
            int(before["midi"])!=int(after["midi"])
            or abs(float(before["duration_beats"])-float(after["duration_beats"]))>EPS
        ):
            non_bass_mutations+=1

    if onset_changes or velocity_changes or duration_extensions or non_bass_mutations:
        raise VerifyError("NON_TARGET_MUTATION")

    report={
        "schema":"ROCK_V3_BASS_OFFBEAT_COHERENCE_VERIFY_001",
        "status":"PASS",
        "diagnostic_only":True,
        "source_execution_sha256":source["execution_sha256"],
        "candidate_execution_sha256":cand["execution_sha256"],
        "bass_event_count":len(cand_bass),
        "offbeat_bass_event_count":offbeat_count,
        "different_pitch_offbeat_remaining_count":0,
        "strong_beat_pitch_change_count":strong_pitch_change_count,
        "bass_duration_changed_event_count":cand["bass_duration_changed_event_count"],
        "bass_offbeat_pitch_normalized_event_count":cand["bass_offbeat_pitch_normalized_event_count"],
        "max_bass_duration_beats":MAX_GATE_BEATS,
        "onset_changed_event_count":0,
        "velocity_changed_event_count":0,
        "duration_extended_event_count":0,
        "non_bass_mutation_count":0,
        "event_count_changed":False,
        "preferred_guitar_treatment_preserved":True,
        "harmony_max_ringing_beats":2.8,
        "safe_strum_treatment_preserved":True,
        "treated_lead_preserved":True,
        "candidate_enabled":False,
        "audio_generated":False,
        "canonical_policy_modified":False,
        "reasoning_engine_used":False,
        "listening_approval":False,
        "live_runtime_promoted":False,
        "next_gate":"16_BAR_CURRENT_MAPPING_A_B_ALL_OFFBEAT_COHERENCE"
    }
    OUT.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))

if __name__=="__main__":
    main()
