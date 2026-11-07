"""Verify Rock V3 bass downbeat-coherence candidate.

No audio. No live enablement.
"""
from __future__ import annotations

from pathlib import Path
import math
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
FORWARD=ROOT/"current_master_forward"
if str(FORWARD) not in sys.path:
    sys.path.insert(0,str(FORWARD))

from rock_v3_strum_candidate_executor import execute as execute_source
from rock_v3_bass_downbeat_coherence_candidate import execute as execute_candidate

OUT=ROOT/"genre_contract_v3_research"/"ROCK_V3_BASS_DOWNBEAT_COHERENCE_VERIFY.json"
EPS=1e-6


class VerifyError(RuntimeError):
    pass


def _is_half_beat_upbeat(start:float)->bool:
    frac=start-math.floor(start)
    return abs(frac-0.5)<=EPS


def main()->None:
    source=execute_source()
    cand=execute_candidate()

    if source.get("status")!="PASS" or cand.get("status")!="PASS":
        raise VerifyError("SOURCE_OR_CANDIDATE_NOT_PASS")
    if source["event_count"]!=cand["event_count"]:
        raise VerifyError("EVENT_COUNT_CHANGED")
    if cand["bass_upbeat_pitch_normalized_event_count"]!=3:
        raise VerifyError("PITCH_NORMALIZATION_COUNT_DRIFT")

    source_bass=[]
    cand_bass=[]
    non_bass_mutations=0
    onset_changes=0
    velocity_changes=0
    bass_duration_over_cap=0
    bass_pitch_changes=0

    for before,after in zip(source["events"],cand["events"]):
        track=str(before.get("track_id","")).upper()

        if float(before["start_beat"])!=float(after["start_beat"]):
            onset_changes+=1
        if int(before["velocity"])!=int(after["velocity"]):
            velocity_changes+=1

        if track=="BASS":
            source_bass.append(before)
            cand_bass.append(after)
            if float(after["duration_beats"])>0.20+1e-9:
                bass_duration_over_cap+=1
            if int(before["midi"])!=int(after["midi"]):
                bass_pitch_changes+=1
        else:
            if (
                int(before["midi"])!=int(after["midi"])
                or abs(float(before["duration_beats"])-float(after["duration_beats"]))>1e-9
            ):
                non_bass_mutations+=1

    if onset_changes:
        raise VerifyError("ONSET_CHANGED")
    if velocity_changes:
        raise VerifyError("VELOCITY_CHANGED")
    if non_bass_mutations:
        raise VerifyError("NON_BASS_MUTATION")
    if bass_duration_over_cap:
        raise VerifyError("BASS_DURATION_OVER_0_20")
    if bass_pitch_changes!=3:
        raise VerifyError("EXPECTED_EXACTLY_3_BASS_PITCH_CHANGES")

    pairs=list(zip(source_bass,cand_bass))
    pairs.sort(key=lambda pair:(float(pair[1]["start_beat"]),int(pair[1]["midi"])))

    upbeat_count=0
    same_pitch_upbeat_count=0
    different_pitch_upbeat_count=0
    upbeat_manifest=[]

    for pos,(before,after) in enumerate(pairs):
        start=float(after["start_beat"])
        if not _is_half_beat_upbeat(start):
            continue

        bar=int(start//4)
        prior=None
        for back in range(pos-1,-1,-1):
            prev=pairs[back][1]
            pstart=float(prev["start_beat"])
            if int(pstart//4)==bar:
                prior=prev
                break
            if pstart<bar*4:
                break

        if prior is None:
            continue

        upbeat_count+=1
        same=int(after["midi"])==int(prior["midi"])
        if same:
            same_pitch_upbeat_count+=1
        else:
            different_pitch_upbeat_count+=1

        upbeat_manifest.append({
            "start_beat":start,
            "bar_index":bar,
            "midi":int(after["midi"]),
            "preceding_same_bar_midi":int(prior["midi"]),
            "same_pitch":same,
        })

    if upbeat_count!=29:
        raise VerifyError(f"UPBEAT_COUNT_DRIFT::{upbeat_count}")
    if same_pitch_upbeat_count!=29:
        raise VerifyError(f"NOT_ALL_UPBEATS_SAME_PITCH::{same_pitch_upbeat_count}")
    if different_pitch_upbeat_count:
        raise VerifyError("DIFFERENT_PITCH_UPBEAT_REMAINS")

    report={
        "schema":"ROCK_V3_BASS_DOWNBEAT_COHERENCE_VERIFY_001",
        "status":"PASS",
        "diagnostic_only":True,
        "source_execution_sha256":source["execution_sha256"],
        "candidate_execution_sha256":cand["execution_sha256"],
        "bass_event_count":cand["bass_event_count"],
        "bass_duration_changed_event_count":cand["bass_duration_changed_event_count"],
        "maximum_bass_duration_beats":0.20,
        "bass_pitch_changed_event_count":3,
        "half_beat_upbeat_event_count":29,
        "same_pitch_half_beat_upbeat_count":29,
        "different_pitch_half_beat_upbeat_count":0,
        "onset_changed_event_count":0,
        "velocity_changed_event_count":0,
        "non_bass_mutation_count":0,
        "event_count_changed":False,
        "preferred_harmony_max_ringing_beats":2.8,
        "preferred_safe_strum_preserved":True,
        "treated_lead_preserved":True,
        "measured_vicious_gate_basis":{
            "gate_beats":0.20,
            "active_end_seconds":0.22,
            "half_beat_upbeat_seconds":0.24390243902439024,
            "pre_upbeat_margin_seconds":0.02390243902439025,
            "artifact_id":13583455938
        },
        "upbeat_manifest":upbeat_manifest,
        "candidate_enabled":False,
        "audio_generated":False,
        "canonical_policy_modified":False,
        "reasoning_engine_used":False,
        "listening_approval":False,
        "live_runtime_promoted":False,
        "next_gate":"DOWNBEAT_COHERENCE_AUDIO_A_B_WITH_VICIOUS_MAPPING_AND_APPROVED_GUITARS"
    }
    OUT.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))


if __name__=="__main__":
    main()
