"""Verify the symbolic Rock V3 bass sustain candidate executor.

No audio. No live enablement. The approved diagnostic guitar treatment
(2.8-beat HARMONY sustain + safe strum + treated LEAD) must remain unchanged.
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

from rock_v3_strum_candidate_executor import execute as execute_preferred_guitar
from rock_v3_bass_sustain_candidate_executor import execute as execute_bass

OUT=ROOT/"genre_contract_v3_research"/"ROCK_V3_BASS_SUSTAIN_CANDIDATE_EXECUTION_VERIFY.json"


class VerifyError(RuntimeError):
    pass


def _bar_end(start:float)->float:
    return (int(start//4)+1)*4.0


def main()->None:
    source=execute_preferred_guitar()
    cand=execute_bass()

    if source.get("status")!="PASS" or cand.get("status")!="PASS":
        raise VerifyError("SOURCE_OR_CANDIDATE_NOT_PASS")
    if source["event_count"]!=cand["event_count"]:
        raise VerifyError("EVENT_COUNT_CHANGED")
    if cand["bass_event_count"]!=147:
        raise VerifyError("BASS_EVENT_COUNT_DRIFT")
    if cand["bass_duration_changed_event_count"]!=58:
        raise VerifyError("BASS_CHANGE_COUNT_DRIFT")

    changed=0
    non_bass_changes=0
    onset_changes=0
    pitch_changes=0
    velocity_changes=0
    instrument_changes=0
    overlap_count=0
    bar_crossing_count=0
    extension_values=[]
    section_counts=Counter()
    min_gap=None

    source_bass=[]
    cand_bass=[]

    for before,after in zip(source["events"],cand["events"]):
        track=str(before.get("track_id","")).upper()
        bdur=float(before["duration_beats"])
        adur=float(after["duration_beats"])

        if float(before["start_beat"])!=float(after["start_beat"]):
            onset_changes+=1
        if int(before["midi"])!=int(after["midi"]):
            pitch_changes+=1
        if int(before["velocity"])!=int(after["velocity"]):
            velocity_changes+=1
        if str(before.get("instrument_id",""))!=str(after.get("instrument_id","")):
            instrument_changes+=1

        if abs(adur-bdur)>1e-9:
            changed+=1
            if track!="BASS":
                non_bass_changes+=1

        if track=="BASS":
            source_bass.append(before)
            cand_bass.append(after)

    if onset_changes or pitch_changes or velocity_changes or instrument_changes:
        raise VerifyError("IDENTITY_DIMENSION_CHANGED")
    if non_bass_changes:
        raise VerifyError("NON_BASS_DURATION_CHANGED")
    if changed!=58:
        raise VerifyError("TOTAL_CHANGED_DURATION_COUNT_DRIFT")

    for i,(before,after) in enumerate(zip(source_bass,cand_bass)):
        start=float(after["start_beat"])
        dur=float(after["duration_beats"])
        if start+dur>_bar_end(start)+1e-9:
            bar_crossing_count+=1

        if i+1<len(cand_bass):
            nxt=float(cand_bass[i+1]["start_beat"])
            if start+dur>nxt+1e-9:
                overlap_count+=1
            gap=nxt-(start+dur)
            if min_gap is None or gap<min_gap:
                min_gap=gap

        ext=float(after["duration_beats"])-float(before["duration_beats"])
        if ext>1e-9:
            extension_values.append(round(ext,6))
            section_counts[str(after.get("section","UNKNOWN"))]+=1
            if ext<0.14-1e-9:
                raise VerifyError("APPLIED_EXTENSION_BELOW_MINIMUM")
            if float(after["duration_beats"])>1.50+1e-9:
                raise VerifyError("MAX_SUSTAIN_EXCEEDED")

    if overlap_count:
        raise VerifyError("NEXT_BASS_ATTACK_OVERLAP")
    if bar_crossing_count:
        raise VerifyError("BAR_BOUNDARY_CROSSING")
    if len(extension_values)!=58:
        raise VerifyError("EXTENSION_VALUE_COUNT_DRIFT")

    report={
        "schema":"ROCK_V3_BASS_SUSTAIN_CANDIDATE_EXECUTION_VERIFY_001",
        "status":"PASS",
        "diagnostic_only":True,
        "candidate_execution_sha256":cand["execution_sha256"],
        "source_execution_sha256":source["execution_sha256"],
        "bass_event_count":cand["bass_event_count"],
        "bass_duration_changed_event_count":cand["bass_duration_changed_event_count"],
        "extension_distribution":{str(k):v for k,v in sorted(Counter(extension_values).items())},
        "section_change_counts":dict(sorted(section_counts.items())),
        "minimum_applied_extension_beats":min(extension_values),
        "maximum_applied_extension_beats":max(extension_values),
        "minimum_gap_to_next_bass_attack_beats":None if min_gap is None else round(min_gap,6),
        "next_bass_attack_overlap_count":0,
        "bar_boundary_crossing_count":0,
        "onset_changed_event_count":0,
        "pitch_changed_event_count":0,
        "velocity_changed_event_count":0,
        "instrument_changed_event_count":0,
        "non_bass_duration_changed_event_count":0,
        "preferred_guitar_treatment_preserved":True,
        "harmony_max_ringing_beats":2.8,
        "safe_strum_treatment_preserved":True,
        "treated_lead_preserved":True,
        "drums_changed":False,
        "candidate_enabled":False,
        "audio_generated":False,
        "canonical_policy_modified":False,
        "reasoning_engine_used":False,
        "listening_approval":False,
        "live_runtime_promoted":False,
        "next_gate":"ISOLATED_BASS_SUSTAIN_AUDIO_A_B_WITH_APPROVED_GUITAR_CONTEXT_FIXED"
    }
    OUT.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))


if __name__=="__main__":
    main()
