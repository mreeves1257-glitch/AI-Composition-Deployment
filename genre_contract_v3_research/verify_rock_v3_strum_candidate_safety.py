"""Symbolic safety analysis for the disabled Rock V3 strum candidate.

No audio is generated and the candidate remains disabled.

The analysis asks whether the current research parameters can be applied as a
pure onset-stagger to the current 40-bar Mode A HARMONY score while keeping
note durations unchanged.

Candidate parameters:
- note_gap_beats = 0.038
- max_strum_span_beats = 0.14
- alternate_direction = True
- preserve pitch/velocity/event count

This verifier does not mutate canonical files.
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
FORWARD=ROOT/"current_master_forward"
if str(FORWARD) not in sys.path:
    sys.path.insert(0,str(FORWARD))

from rock_v3_core_performance_executor import execute as execute_mode_a, MODE

NOTE_GAP=0.038
MAX_SPAN=0.14
MAX_CLUSTER_GAP=0.047

class StrumSafetyError(RuntimeError):
    pass


def _bar_end(start:float)->float:
    return (int(start//4)+1)*4.0


def main()->None:
    score=execute_mode_a(MODE)
    if score.get("status")!="PASS":
        raise StrumSafetyError("MODE_A_SOURCE_NOT_PASS")

    harmony=[
        e for e in score["events"]
        if str(e.get("track_id","")).upper()=="HARMONY"
        and str(e.get("instrument_id",""))=="electric_guitar"
    ]
    if not harmony:
        raise StrumSafetyError("NO_HARMONY_EVENTS")

    by_onset=defaultdict(list)
    for e in harmony:
        by_onset[float(e["start_beat"])].append(e)

    gestures=[]
    for onset in sorted(by_onset):
        members=sorted(by_onset[onset],key=lambda e:int(e["midi"]))
        span=(len(members)-1)*NOTE_GAP
        gestures.append((onset,members,span))

    onset_list=[g[0] for g in gestures]
    next_onset={onset:(onset_list[i+1] if i+1<len(onset_list) else None)
                for i,onset in enumerate(onset_list)}

    result={
        "schema":"ROCK_V3_STRUM_CANDIDATE_SAFETY_001",
        "status":"PASS",
        "diagnostic_only":True,
        "candidate":{
            "max_cluster_gap_beats":MAX_CLUSTER_GAP,
            "note_gap_beats":NOTE_GAP,
            "max_strum_span_beats":MAX_SPAN,
            "alternate_direction":True,
            "preserve_pitch_velocity_count":True
        },
        "mode_a_source_sha256":score["execution_sha256"],
        "harmony_note_event_count":len(harmony),
        "vertical_gesture_count":len(gestures),
        "gesture_size_distribution":{},
        "max_required_span_beats":0.0,
        "gesture_span_exceeds_candidate_max_count":0,
        "unchanged_duration_simulation":{
            "bar_boundary_crossing_note_count":0,
            "next_gesture_overlap_note_count":0,
            "gestures_with_any_overlap_count":0,
            "minimum_resulting_gap_beats":None,
            "overlap_examples":[]
        },
        "preserve_original_note_off_simulation":{
            "nonpositive_duration_note_count":0,
            "minimum_resulting_duration_beats":None,
            "duration_adjusted_note_count":0,
            "maximum_mechanical_duration_reduction_beats":0.0
        },
        "audio_generated":False,
        "candidate_enabled":False,
        "canonical_policy_modified":False,
        "reasoning_engine_used":False,
        "listening_approval":False,
        "live_runtime_promoted":False
    }

    size_counts=defaultdict(int)
    min_gap=None
    overlap_gestures=set()
    min_preserved_duration=None
    adjusted_count=0
    nonpositive=0
    max_reduction=0.0

    for gi,(onset,members,span) in enumerate(gestures):
        size_counts[str(len(members))]+=1
        result["max_required_span_beats"]=max(result["max_required_span_beats"],span)
        if span>MAX_SPAN+1e-9:
            result["gesture_span_exceeds_candidate_max_count"]+=1

        direction_up=(gi%2==0)
        ordered=members if direction_up else list(reversed(members))
        nxt=next_onset[onset]

        for idx,e in enumerate(ordered):
            offset=idx*NOTE_GAP
            new_start=onset+offset
            original_duration=float(e["duration_beats"])
            new_end=new_start+original_duration

            if new_end>_bar_end(onset)+1e-9:
                result["unchanged_duration_simulation"]["bar_boundary_crossing_note_count"]+=1

            if nxt is not None:
                gap=nxt-new_end
                if min_gap is None or gap<min_gap:
                    min_gap=gap
                if gap<0:
                    result["unchanged_duration_simulation"]["next_gesture_overlap_note_count"]+=1
                    overlap_gestures.add(onset)
                    if len(result["unchanged_duration_simulation"]["overlap_examples"])<12:
                        result["unchanged_duration_simulation"]["overlap_examples"].append({
                            "gesture_onset":onset,
                            "next_gesture_onset":nxt,
                            "midi":int(e["midi"]),
                            "offset_beats":round(offset,6),
                            "duration_beats":original_duration,
                            "resulting_overlap_beats":round(-gap,6)
                        })

            # Alternative mechanical treatment: preserve original note-off time,
            # so a delayed string attack shortens only by its onset offset.
            preserved_duration=original_duration-offset
            if offset>0:
                adjusted_count+=1
                max_reduction=max(max_reduction,offset)
            if min_preserved_duration is None or preserved_duration<min_preserved_duration:
                min_preserved_duration=preserved_duration
            if preserved_duration<=0:
                nonpositive+=1

    result["gesture_size_distribution"]=dict(sorted(size_counts.items(),key=lambda kv:int(kv[0])))
    result["unchanged_duration_simulation"]["gestures_with_any_overlap_count"]=len(overlap_gestures)
    result["unchanged_duration_simulation"]["minimum_resulting_gap_beats"]=(
        None if min_gap is None else round(min_gap,6)
    )
    result["preserve_original_note_off_simulation"]["nonpositive_duration_note_count"]=nonpositive
    result["preserve_original_note_off_simulation"]["minimum_resulting_duration_beats"]=(
        None if min_preserved_duration is None else round(min_preserved_duration,6)
    )
    result["preserve_original_note_off_simulation"]["duration_adjusted_note_count"]=adjusted_count
    result["preserve_original_note_off_simulation"]["maximum_mechanical_duration_reduction_beats"]=round(max_reduction,6)

    unchanged_safe=(
        result["gesture_span_exceeds_candidate_max_count"]==0
        and result["unchanged_duration_simulation"]["bar_boundary_crossing_note_count"]==0
        and result["unchanged_duration_simulation"]["next_gesture_overlap_note_count"]==0
    )
    noteoff_safe=(
        result["gesture_span_exceeds_candidate_max_count"]==0
        and nonpositive==0
    )

    result["pure_onset_stagger_with_unchanged_duration_safe"]=unchanged_safe
    result["onset_stagger_with_original_note_off_preserved_safe"]=noteoff_safe

    if unchanged_safe:
        result["next_gate"]="BUILD_SYMBOLIC_STRUM_EXECUTOR_WITH_UNCHANGED_DURATIONS__NO_AUDIO"
    elif noteoff_safe:
        result["next_gate"]="PURE_ONSET_STAGGER_NOT_SAFE__REVIEW_NOTE_OFF_PRESERVING_MECHANICAL_COMPENSATION_BEFORE_IMPLEMENTATION"
    else:
        result["next_gate"]="REJECT_CURRENT_STRUM_PARAMETERS_BEFORE_IMPLEMENTATION"

    out=ROOT/"genre_contract_v3_research"/"ROCK_V3_STRUM_CANDIDATE_SAFETY.json"
    out.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))


if __name__=="__main__":
    main()
