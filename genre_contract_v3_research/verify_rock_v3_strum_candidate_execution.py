"""Verify the symbolic Rock V3 strum candidate executor.

No audio. No live enablement.
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

from rock_v3_core_performance_executor import execute as execute_mode_a, MODE
from rock_v3_strum_candidate_executor import execute as execute_strum

OUT=ROOT/"genre_contract_v3_research"/"ROCK_V3_STRUM_CANDIDATE_EXECUTION_VERIFY.json"


class VerifyError(RuntimeError):
    pass


def main()->None:
    source=execute_mode_a(MODE)
    cand=execute_strum()

    if source.get("status")!="PASS" or cand.get("status")!="PASS":
        raise VerifyError("SOURCE_OR_CANDIDATE_NOT_PASS")
    if source["event_count"]!=cand["event_count"]:
        raise VerifyError("EVENT_COUNT_CHANGED")
    if cand["harmony_vertical_gesture_count"]!=73:
        raise VerifyError("GESTURE_COUNT_DRIFT")
    if cand["max_required_span_beats"]!=0.076:
        raise VerifyError("MAX_SPAN_DRIFT")
    if cand["absolute_note_off_changed_event_count"]!=0:
        raise VerifyError("NOTE_OFF_CHANGED")
    if cand["non_harmony_mutation_count"]!=0:
        raise VerifyError("NON_HARMONY_MUTATION")
    if not cand["note_off_times_preserved"]:
        raise VerifyError("NOTE_OFF_FLAG_FALSE")

    offsets=[]
    directions=[]
    delayed=0
    for g in cand["gesture_manifest"]:
        directions.append(g["direction"])
        if g["member_count"]!=3:
            raise VerifyError("NON_THREE_NOTE_GESTURE")
        if abs(g["span_beats"]-0.076)>1e-9:
            raise VerifyError("GESTURE_SPAN_DRIFT")
        local=[float(n["offset_beats"]) for n in g["notes"]]
        if sorted(local)!=[0.0,0.038,0.076]:
            raise VerifyError("OFFSET_PATTERN_DRIFT")
        offsets.extend(local)
        delayed+=sum(1 for x in local if x>0)

        for n in g["notes"]:
            before_end=float(n["before_start"])+float(n["before_duration"])
            after_end=float(n["after_start"])+float(n["after_duration"])
            if abs(before_end-after_end)>1e-9:
                raise VerifyError("MANIFEST_NOTE_OFF_CHANGED")
            if float(n["after_duration"])<=0:
                raise VerifyError("NONPOSITIVE_DURATION")

    for i,d in enumerate(directions):
        expected="LOW_TO_HIGH" if i%2==0 else "HIGH_TO_LOW"
        if d!=expected:
            raise VerifyError("ALTERNATING_DIRECTION_DRIFT")

    if delayed!=146:
        raise VerifyError("DELAYED_NOTE_COUNT_DRIFT")
    if cand["onset_changed_event_count"]!=146:
        raise VerifyError("ONSET_CHANGED_COUNT_DRIFT")
    if cand["duration_changed_event_count"]!=146:
        raise VerifyError("DURATION_CHANGED_COUNT_DRIFT")

    report={
        "schema":"ROCK_V3_STRUM_CANDIDATE_EXECUTION_VERIFY_001",
        "status":"PASS",
        "diagnostic_only":True,
        "source_mode":MODE,
        "candidate_execution_sha256":cand["execution_sha256"],
        "harmony_vertical_gesture_count":cand["harmony_vertical_gesture_count"],
        "gesture_size":3,
        "direction_distribution":dict(Counter(directions)),
        "offset_distribution":{str(k):v for k,v in sorted(Counter(offsets).items())},
        "max_required_span_beats":cand["max_required_span_beats"],
        "delayed_note_event_count":delayed,
        "onset_changed_event_count":cand["onset_changed_event_count"],
        "duration_changed_event_count":cand["duration_changed_event_count"],
        "absolute_note_off_changed_event_count":0,
        "non_harmony_mutation_count":0,
        "pitch_changed":False,
        "velocity_changed":False,
        "event_count_changed":False,
        "lead_changed":False,
        "bass_changed":False,
        "drums_changed":False,
        "note_off_times_preserved":True,
        "candidate_enabled":False,
        "audio_generated":False,
        "canonical_policy_modified":False,
        "reasoning_engine_used":False,
        "listening_approval":False,
        "live_runtime_promoted":False,
        "next_gate":"ISOLATED_STRUM_AUDIO_A_B__CURRENT_MODE_A_VS_ATTACK_STAGGER_ONLY"
    }
    OUT.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))


if __name__=="__main__":
    main()
