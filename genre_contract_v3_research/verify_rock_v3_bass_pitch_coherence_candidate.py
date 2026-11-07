"""Verify the Rock V3 bass pitch-coherence repair candidate.

No audio. No live enablement.

Expected behavior:
- preserve all onsets, velocities, event count and non-BASS roles;
- never extend BASS;
- for different-pitch attacks with spacing > 0.30 beat, previous note must
  release at least 0.25 beat before the new pitch;
- for ultra-close different-pitch attacks (<= 0.30 beat), later note must be
  pitch-locked to the prior tone rather than producing an overlapping pitch flip.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
FORWARD=ROOT/"current_master_forward"
if str(FORWARD) not in sys.path:
    sys.path.insert(0,str(FORWARD))

from rock_v3_strum_candidate_executor import execute as execute_source
from rock_v3_bass_pitch_coherence_candidate_executor import (
    execute as execute_candidate,
    RELEASE_GAP_BEATS,
    ULTRA_CLOSE_PITCH_LOCK_BEATS,
)

OUT=ROOT/"genre_contract_v3_research"/"ROCK_V3_BASS_PITCH_COHERENCE_CANDIDATE_VERIFY.json"


class VerifyError(RuntimeError):
    pass


def main()->None:
    source=execute_source()
    cand=execute_candidate()

    if source.get("status")!="PASS" or cand.get("status")!="PASS":
        raise VerifyError("SOURCE_OR_CANDIDATE_NOT_PASS")
    if source["event_count"]!=cand["event_count"]:
        raise VerifyError("EVENT_COUNT_CHANGED")

    source_bass=[
        e for e in source["events"]
        if str(e.get("track_id","")).upper()=="BASS"
    ]
    cand_bass=[
        e for e in cand["events"]
        if str(e.get("track_id","")).upper()=="BASS"
    ]
    if len(source_bass)!=len(cand_bass):
        raise VerifyError("BASS_COUNT_CHANGED")

    duration_changes=0
    pitch_changes=0
    non_bass_mutations=0
    onset_changes=0
    velocity_changes=0
    extension_count=0

    for before,after in zip(source["events"],cand["events"]):
        track=str(before.get("track_id","")).upper()

        if float(before["start_beat"])!=float(after["start_beat"]):
            onset_changes+=1
        if int(before["velocity"])!=int(after["velocity"]):
            velocity_changes+=1

        bdur=float(before["duration_beats"])
        adur=float(after["duration_beats"])
        bpitch=int(before["midi"])
        apitch=int(after["midi"])

        if abs(adur-bdur)>1e-9:
            duration_changes+=1
            if adur>bdur+1e-9:
                extension_count+=1
            if track!="BASS":
                non_bass_mutations+=1

        if apitch!=bpitch:
            pitch_changes+=1
            if track!="BASS":
                non_bass_mutations+=1

    if onset_changes:
        raise VerifyError("ONSET_CHANGED")
    if velocity_changes:
        raise VerifyError("VELOCITY_CHANGED")
    if extension_count:
        raise VerifyError("BASS_DURATION_EXTENDED")
    if non_bass_mutations:
        raise VerifyError("NON_BASS_MUTATION")
    if duration_changes!=cand["bass_duration_shortened_event_count"]:
        raise VerifyError("DURATION_CHANGE_COUNT_DRIFT")
    if pitch_changes!=cand["bass_pitch_locked_event_count"]:
        raise VerifyError("PITCH_LOCK_COUNT_DRIFT")

    duration_manifest=cand["duration_change_manifest"]
    pitch_manifest=cand["pitch_lock_manifest"]

    for x in duration_manifest:
        spacing=float(x["next_start_beat"])-float(x["start_beat"])
        if spacing<=ULTRA_CLOSE_PITCH_LOCK_BEATS+1e-9:
            raise VerifyError("ULTRA_CLOSE_EVENT_SHORTENED_INSTEAD_OF_LOCKED")
        if float(x["resulting_gap_beats"])<RELEASE_GAP_BEATS-1e-9:
            raise VerifyError("RELEASE_GAP_TOO_SMALL")
        if float(x["after_duration_beats"])>=float(x["before_duration_beats"])-1e-9:
            raise VerifyError("DURATION_NOT_SHORTENED")

    for x in pitch_manifest:
        spacing=float(x["spacing_from_prior_attack_beats"])
        if spacing>ULTRA_CLOSE_PITCH_LOCK_BEATS+1e-9:
            raise VerifyError("PITCH_LOCK_OUTSIDE_ULTRA_CLOSE_WINDOW")
        if int(x["before_midi"])==int(x["after_midi"]):
            raise VerifyError("PITCH_LOCK_DID_NOT_CHANGE_PITCH")

    remaining=[]
    for a,b in zip(cand_bass,cand_bass[1:]):
        if int(a["midi"])==int(b["midi"]):
            continue
        spacing=float(b["start_beat"])-float(a["start_beat"])
        a_end=float(a["start_beat"])+float(a["duration_beats"])
        gap=float(b["start_beat"])-a_end
        required=RELEASE_GAP_BEATS if spacing>ULTRA_CLOSE_PITCH_LOCK_BEATS else 0.0
        if gap<required-1e-9:
            remaining.append({
                "a_start":a["start_beat"],"a_midi":a["midi"],
                "b_start":b["start_beat"],"b_midi":b["midi"],
                "spacing":spacing,"gap":gap,"required":required
            })

    if remaining:
        raise VerifyError("DIFFERENT_PITCH_COHERENCE_VIOLATION_REMAINS")

    report={
        "schema":"ROCK_V3_BASS_PITCH_COHERENCE_CANDIDATE_VERIFY_001",
        "status":"PASS",
        "diagnostic_only":True,
        "source_execution_sha256":source["execution_sha256"],
        "candidate_execution_sha256":cand["execution_sha256"],
        "bass_event_count":len(cand_bass),
        "duration_shortened_event_count":duration_changes,
        "pitch_locked_event_count":pitch_changes,
        "duration_reduction_distribution":{
            str(k):v for k,v in sorted(Counter(
                round(float(x["duration_reduction_beats"]),6)
                for x in duration_manifest
            ).items())
        },
        "pitch_lock_spacing_distribution":{
            str(k):v for k,v in sorted(Counter(
                round(float(x["spacing_from_prior_attack_beats"]),6)
                for x in pitch_manifest
            ).items())
        },
        "release_gap_beats":RELEASE_GAP_BEATS,
        "ultra_close_pitch_lock_beats":ULTRA_CLOSE_PITCH_LOCK_BEATS,
        "remaining_different_pitch_coherence_violation_count":0,
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
        "next_gate":"CLEAN_MAPPING_BASS_WRITING_ARTICULATION_A_B"
    }
    OUT.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))


if __name__=="__main__":
    main()
