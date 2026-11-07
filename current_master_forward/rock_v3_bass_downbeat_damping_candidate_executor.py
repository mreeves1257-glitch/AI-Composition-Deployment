"""Rock V3 diagnostic bass downbeat-damping + upbeat-tone guard.

Directly implements the human listening diagnosis:
- bass attack/downbeat is good;
- bass resonance carries too far toward the upbeat;
- if bass continues into an upbeat, it should stay on the same tone.

Measured resource evidence on exact Growlybass v1.002 / growlybass_vicious.sfz:
- at 123 BPM, a 0.20-beat MIDI gate has measured acoustic active-end
  ~0.451 beat after attack, before the 0.50-beat upbeat;
- 0.30-beat and longer gates cross the half-beat upbeat.

Candidate behavior:
1. cap ordinary BASS MIDI gate to 0.20 beat (never extend);
2. preserve every BASS onset, velocity, event count and instrument;
3. on half-beat upbeat attacks only, if pitch differs from the preceding BASS
   tone, lock that upbeat to the preceding pitch;
4. preserve same-pitch upbeats unchanged;
5. final sustained arrival is excluded from damping.

Diagnostic only. No live authority.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any

from rock_v3_strum_candidate_executor import execute as execute_preferred_guitar

SCHEMA="ROCK_V3_BASS_DOWNBEAT_DAMPING_CANDIDATE_001"
MODE="GATE_0P20_BEAT_PLUS_DIFFERENT_PITCH_UPBEAT_GUARD"
GATE_BEATS=0.20
UPBEAT_FRACTION=0.50
FINAL_BAR_INDEX=39


class BassDownbeatDampingError(RuntimeError):
    pass


def _sha(value:Any)->str:
    return hashlib.sha256(
        json.dumps(value,sort_keys=True,separators=(",",":"),default=str).encode()
    ).hexdigest()


def _is_half_beat_upbeat(start:float)->bool:
    local=start%4.0
    frac=local-int(local)
    return abs(frac-UPBEAT_FRACTION)<=1e-9


def execute()->dict[str,Any]:
    source=execute_preferred_guitar()
    if source.get("status")!="PASS":
        raise BassDownbeatDampingError("SOURCE_NOT_PASS")

    result=[deepcopy(e) for e in source["events"]]
    bass_indices=[
        i for i,e in enumerate(result)
        if str(e.get("track_id","")).upper()=="BASS"
        and str(e.get("instrument_id",""))=="electric_bass_guitar"
    ]
    bass_indices.sort(key=lambda i:(float(result[i]["start_beat"]),int(result[i]["midi"])))
    if not bass_indices:
        raise BassDownbeatDampingError("NO_BASS_EVENTS")

    duration_changes=[]
    pitch_locks=[]

    # First, shorten ordinary bass gates so the measured acoustic tail clears
    # the next half-beat upbeat. Preserve the final sustained arrival.
    for i in bass_indices:
        e=result[i]
        start=float(e["start_beat"])
        bar_index=int(start//4)
        original=float(e["duration_beats"])
        if bar_index==FINAL_BAR_INDEX:
            continue
        if original>GATE_BEATS+1e-9:
            e["pre_downbeat_damping_duration_beats"]=original
            e["duration_beats"]=GATE_BEATS
            e["bass_downbeat_damping_mode"]=MODE
            e["bass_gate_beats"]=GATE_BEATS
            duration_changes.append({
                "event_index":i,
                "section":str(e.get("section","UNKNOWN")),
                "start_beat":start,
                "midi":int(e["midi"]),
                "before_duration_beats":original,
                "after_duration_beats":GATE_BEATS,
                "duration_reduction_beats":round(original-GATE_BEATS,6),
            })

    # Then enforce same-tone behavior only on half-beat upbeat attacks.
    previous_bass_index=None
    for i in bass_indices:
        e=result[i]
        start=float(e["start_beat"])
        if previous_bass_index is not None and _is_half_beat_upbeat(start):
            prev=result[previous_bass_index]
            if int(e["midi"])!=int(prev["midi"]):
                old=int(e["midi"])
                new=int(prev["midi"])
                e["pre_upbeat_guard_midi"]=old
                e["midi"]=new
                e["bass_upbeat_pitch_guard"]=True
                e["bass_upbeat_pitch_guard_source_midi"]=new
                pitch_locks.append({
                    "event_index":i,
                    "section":str(e.get("section","UNKNOWN")),
                    "start_beat":start,
                    "before_midi":old,
                    "after_midi":new,
                    "prior_start_beat":float(prev["start_beat"]),
                    "prior_midi":int(prev["midi"]),
                })
        previous_bass_index=i

    if len(result)!=len(source["events"]):
        raise BassDownbeatDampingError("EVENT_COUNT_CHANGED")

    duration_changed=0
    pitch_changed=0
    non_bass_mutation=0
    onset_changed=0
    velocity_changed=0

    for before,after in zip(source["events"],result):
        track=str(before.get("track_id","")).upper()
        if float(before["start_beat"])!=float(after["start_beat"]):
            onset_changed+=1
        if int(before["velocity"])!=int(after["velocity"]):
            velocity_changed+=1

        if abs(float(before["duration_beats"])-float(after["duration_beats"]))>1e-9:
            duration_changed+=1
            if float(after["duration_beats"])>float(before["duration_beats"])+1e-9:
                raise BassDownbeatDampingError("DURATION_EXTENDED")
            if track!="BASS":
                non_bass_mutation+=1

        if int(before["midi"])!=int(after["midi"]):
            pitch_changed+=1
            if track!="BASS":
                non_bass_mutation+=1

    if onset_changed:
        raise BassDownbeatDampingError("ONSET_CHANGED")
    if velocity_changed:
        raise BassDownbeatDampingError("VELOCITY_CHANGED")
    if non_bass_mutation:
        raise BassDownbeatDampingError("NON_BASS_MUTATION")
    if duration_changed!=len(duration_changes):
        raise BassDownbeatDampingError("DURATION_CHANGE_COUNT_MISMATCH")
    if pitch_changed!=len(pitch_locks):
        raise BassDownbeatDampingError("PITCH_LOCK_COUNT_MISMATCH")

    packet={
        "schema":SCHEMA,
        "status":"PASS",
        "diagnostic_only":True,
        "genre":"ROCK",
        "profile_id":"ROCK_CORE_V2",
        "mode":MODE,
        "source_execution_sha256":source["execution_sha256"],
        "bar_count":source["bar_count"],
        "tempo_bpm":source["tempo_bpm"],
        "meter":source["meter"],
        "events":result,
        "event_count":len(result),
        "bass_event_count":len(bass_indices),
        "gate_beats":GATE_BEATS,
        "bass_duration_shortened_event_count":len(duration_changes),
        "different_pitch_half_beat_upbeat_lock_count":len(pitch_locks),
        "duration_change_manifest":duration_changes,
        "pitch_lock_manifest":pitch_locks,
        "final_sustained_arrival_exempt":True,
        "bass_onset_changed":False,
        "bass_velocity_changed":False,
        "event_count_changed":False,
        "duration_extended":False,
        "guitar_changed":False,
        "lead_changed":False,
        "drums_changed":False,
        "preferred_guitar_treatment_preserved":True,
        "harmony_max_ringing_beats":2.8,
        "safe_strum_treatment_preserved":True,
        "resource_assumption":{
            "resource_id":"KARORYFER_GROWLYBASS_V1_002",
            "mapping":"growlybass_vicious.sfz",
            "measured_gate_beats":0.20,
            "measured_active_end_beats":0.451,
            "crosses_half_beat_upbeat":False
        },
        "reasoning_engine_used":False,
        "audio_generated":False,
        "candidate_enabled_live":False,
        "canonical_policy_modified":False,
        "listening_approval":False,
        "live_runtime_promoted":False,
        "next_gate":"SYMBOLIC_VERIFY_THEN_CURRENT_MAPPING_LISTENING_A_B"
    }
    packet["execution_sha256"]=_sha({
        k:v for k,v in packet.items() if k!="execution_sha256"
    })
    return packet


if __name__=="__main__":
    print(json.dumps(execute(),indent=2))
