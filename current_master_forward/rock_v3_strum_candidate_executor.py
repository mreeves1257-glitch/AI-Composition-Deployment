"""Rock V3 diagnostic strum candidate executor.

Applies the disabled ROCK_SHINYGUITAR_STRUM_ATTACK_TIMING_V1 candidate to the
current Mode A score without changing canonical policy or live authority.

Design:
- HARMONY electric-guitar vertical chords only.
- Three-note chord members are staggered by 0.038 beat per string.
- Strum direction alternates by gesture.
- First string keeps the original onset.
- Delayed strings shorten numerically only enough to preserve their original
  absolute note-off time. This keeps release timing unchanged and prevents the
  overlap/bar-crossing failures found by the pure-onset simulation.
- Pitch, velocity, event count, chord identity, section identity and all
  non-HARMONY roles remain unchanged.

Diagnostic only. No audio authority.
"""
from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
import hashlib
import json
from typing import Any

from rock_v3_core_performance_executor import execute as execute_mode_a, MODE

SCHEMA="ROCK_V3_STRUM_CANDIDATE_EXECUTION_001"
STRUM_MODE="HARMONY_ATTACK_STAGGER_NOTE_OFF_PRESERVED"
NOTE_GAP_BEATS=0.038
MAX_STRUM_SPAN_BEATS=0.14
MAX_CLUSTER_GAP_BEATS=0.047


class RockV3StrumCandidateError(RuntimeError):
    pass


def _sha(value:Any)->str:
    return hashlib.sha256(
        json.dumps(value,sort_keys=True,separators=(",",":"),default=str).encode()
    ).hexdigest()


def _bar_end(start:float)->float:
    return (int(start//4)+1)*4.0


def execute()->dict[str,Any]:
    source=execute_mode_a(MODE)
    if source.get("status")!="PASS":
        raise RockV3StrumCandidateError("MODE_A_SOURCE_NOT_PASS")

    result=[deepcopy(e) for e in source["events"]]

    groups:dict[float,list[int]]=defaultdict(list)
    for i,e in enumerate(result):
        if (
            str(e.get("track_id","")).upper()=="HARMONY"
            and str(e.get("instrument_id",""))=="electric_guitar"
        ):
            groups[float(e["start_beat"])].append(i)

    if not groups:
        raise RockV3StrumCandidateError("NO_HARMONY_GESTURES")

    gesture_manifest=[]
    changed_indices=set()

    for gesture_index,onset in enumerate(sorted(groups)):
        members=groups[onset]
        members.sort(key=lambda i:int(result[i]["midi"]))

        span=(len(members)-1)*NOTE_GAP_BEATS
        if span>MAX_STRUM_SPAN_BEATS+1e-9:
            raise RockV3StrumCandidateError("STRUM_SPAN_EXCEEDS_MAX")

        ordered=members if gesture_index%2==0 else list(reversed(members))
        direction="LOW_TO_HIGH" if gesture_index%2==0 else "HIGH_TO_LOW"

        note_changes=[]
        for order_index,i in enumerate(ordered):
            event=result[i]
            original_start=float(event["start_beat"])
            original_duration=float(event["duration_beats"])
            original_end=original_start+original_duration

            offset=round(order_index*NOTE_GAP_BEATS,6)
            new_start=round(original_start+offset,6)
            new_duration=round(original_end-new_start,6)

            if new_duration<=0:
                raise RockV3StrumCandidateError("NONPOSITIVE_DURATION_AFTER_STAGGER")
            if new_start+new_duration>_bar_end(original_start)+1e-9:
                raise RockV3StrumCandidateError("BAR_BOUNDARY_CROSSING_AFTER_STAGGER")
            if abs((new_start+new_duration)-original_end)>1e-9:
                raise RockV3StrumCandidateError("NOTE_OFF_NOT_PRESERVED")

            event["pre_strum_start_beat"]=original_start
            event["pre_strum_duration_beats"]=original_duration
            event["start_beat"]=new_start
            event["duration_beats"]=new_duration
            event["strum_attack_offset_beats"]=offset
            event["strum_execution_mode"]=STRUM_MODE
            event["strum_direction"]=direction
            event["note_off_preserved"]=True
            changed_indices.add(i)

            note_changes.append({
                "event_index":i,
                "midi":int(event["midi"]),
                "before_start":original_start,
                "after_start":new_start,
                "before_duration":original_duration,
                "after_duration":new_duration,
                "absolute_note_off":round(original_end,6),
                "offset_beats":offset,
            })

        gesture_manifest.append({
            "gesture_index":gesture_index,
            "original_onset":onset,
            "direction":direction,
            "member_count":len(members),
            "span_beats":round(span,6),
            "notes":note_changes,
        })

    if len(result)!=len(source["events"]):
        raise RockV3StrumCandidateError("EVENT_COUNT_CHANGED")

    identity_fields=(
        "track_id","role","instrument_id","source_instrument_id",
        "midi","velocity","section","section_type","source_cell","chord_symbol",
    )
    onset_changed=0
    duration_changed=0
    note_off_changed=0
    non_harmony_mutations=0

    for i,(before,after) in enumerate(zip(source["events"],result)):
        for field in identity_fields:
            if before.get(field)!=after.get(field):
                raise RockV3StrumCandidateError("IDENTITY_MUTATION::"+field)

        track=str(before.get("track_id","")).upper()
        bstart=float(before["start_beat"])
        astart=float(after["start_beat"])
        bdur=float(before["duration_beats"])
        adur=float(after["duration_beats"])

        if abs(astart-bstart)>1e-9:
            onset_changed+=1
        if abs(adur-bdur)>1e-9:
            duration_changed+=1
        if abs((astart+adur)-(bstart+bdur))>1e-9:
            note_off_changed+=1

        if track!="HARMONY" and (
            abs(astart-bstart)>1e-9 or abs(adur-bdur)>1e-9
        ):
            non_harmony_mutations+=1

    if note_off_changed:
        raise RockV3StrumCandidateError("NOTE_OFF_CHANGED")
    if non_harmony_mutations:
        raise RockV3StrumCandidateError("NON_HARMONY_MUTATION")

    packet={
        "schema":SCHEMA,
        "status":"PASS",
        "diagnostic_only":True,
        "genre":"ROCK",
        "profile_id":"ROCK_CORE_V2",
        "source_mode":MODE,
        "strum_mode":STRUM_MODE,
        "source_execution_sha256":source["execution_sha256"],
        "bar_count":source["bar_count"],
        "tempo_bpm":source["tempo_bpm"],
        "meter":source["meter"],
        "events":result,
        "event_count":len(result),
        "harmony_vertical_gesture_count":len(gesture_manifest),
        "gesture_manifest":gesture_manifest,
        "note_gap_beats":NOTE_GAP_BEATS,
        "max_required_span_beats":max(g["span_beats"] for g in gesture_manifest),
        "onset_changed_event_count":onset_changed,
        "duration_changed_event_count":duration_changed,
        "absolute_note_off_changed_event_count":note_off_changed,
        "non_harmony_mutation_count":non_harmony_mutations,
        "pitch_changed":False,
        "velocity_changed":False,
        "event_count_changed":False,
        "instrument_changed":False,
        "lead_changed":False,
        "bass_changed":False,
        "drums_changed":False,
        "note_off_times_preserved":True,
        "canonical_mode_a_policy_modified":False,
        "strum_candidate_enabled_in_live_runtime":False,
        "audio_generated":False,
        "audio_authority":False,
        "reasoning_engine_used":False,
        "listening_approval":False,
        "research_candidate_only":True,
        "next_gate":"SYMBOLIC_STRUM_EXECUTION_VERIFICATION__NO_AUDIO",
    }
    packet["execution_sha256"]=_sha({
        k:v for k,v in packet.items() if k!="execution_sha256"
    })
    return packet


if __name__=="__main__":
    print(json.dumps(execute(),indent=2))
