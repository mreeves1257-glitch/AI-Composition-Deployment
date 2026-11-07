"""Rock V3 diagnostic bass downbeat-coherence candidate.

User-directed musical correction:
1. Bass attack/downbeat is good.
2. Bass tail must not resonate far enough to read as an upbeat.
3. If a bass note occurs on the half-beat upbeat, it must not introduce a new
   pitch against the sustained/downbeat tone; same-tone upbeats are allowed.

Measured resource behavior at 123 BPM on exact Growlybass Vicious v1.002:
- half-beat upbeat offset: ~0.2439 s;
- 0.20-beat MIDI gate -> measured active end ~0.22 s;
- 0.25-beat MIDI gate -> measured active end ~0.24 s;
- 0.30-beat MIDI gate crosses the upbeat.
Therefore 0.20 beat is the longest tested gate with a 20 ms pre-upbeat margin.

This candidate:
- caps BASS duration at 0.20 beat;
- preserves onset, velocity, event count, section/chord identity;
- preserves all already-same-pitch half-beat upbeats;
- changes only different-pitch half-beat upbeats to the immediately preceding
  same-bar BASS pitch;
- leaves preferred guitars untouched:
  2.8 HARMONY sustain + safe strum + treated LEAD.

Diagnostic only. No live authority.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math
from typing import Any

from rock_v3_strum_candidate_executor import execute as execute_preferred_guitar

SCHEMA="ROCK_V3_BASS_DOWNBEAT_COHERENCE_CANDIDATE_001"
MAX_GATE_BEATS=0.20
EPS=1e-6


class BassDownbeatCoherenceError(RuntimeError):
    pass


def _sha(value:Any)->str:
    return hashlib.sha256(
        json.dumps(value,sort_keys=True,separators=(",",":"),default=str).encode()
    ).hexdigest()


def _is_half_beat_upbeat(start:float)->bool:
    frac=start-math.floor(start)
    return abs(frac-0.5)<=EPS


def execute()->dict[str,Any]:
    source=execute_preferred_guitar()
    if source.get("status")!="PASS":
        raise BassDownbeatCoherenceError("PREFERRED_GUITAR_SOURCE_NOT_PASS")

    result=[deepcopy(e) for e in source["events"]]
    bass_indices=[
        i for i,e in enumerate(result)
        if str(e.get("track_id","")).upper()=="BASS"
        and str(e.get("instrument_id",""))=="electric_bass_guitar"
    ]
    bass_indices.sort(key=lambda i:(float(result[i]["start_beat"]),int(result[i]["midi"])))
    if not bass_indices:
        raise BassDownbeatCoherenceError("NO_BASS_EVENTS")

    duration_changes=[]
    pitch_changes=[]
    same_pitch_upbeats=0
    different_pitch_upbeats=0

    # First apply measured downbeat damping cap.
    for i in bass_indices:
        e=result[i]
        original=float(e["duration_beats"])
        new=min(original,MAX_GATE_BEATS)
        if new<original-1e-9:
            e["pre_downbeat_damping_duration_beats"]=original
            e["duration_beats"]=round(new,6)
            e["bass_downbeat_gate_beats"]=MAX_GATE_BEATS
            duration_changes.append({
                "event_index":i,
                "section":str(e.get("section","UNKNOWN")),
                "start_beat":float(e["start_beat"]),
                "midi":int(e["midi"]),
                "before_duration_beats":original,
                "after_duration_beats":round(new,6),
            })

    # Then normalize only half-beat upbeat pitch changes.
    for pos,i in enumerate(bass_indices):
        e=result[i]
        start=float(e["start_beat"])
        if not _is_half_beat_upbeat(start):
            continue

        bar=int(start//4)
        prior_idx=None
        for back in range(pos-1,-1,-1):
            j=bass_indices[back]
            p=result[j]
            pstart=float(p["start_beat"])
            if int(pstart//4)==bar:
                prior_idx=j
                break
            if pstart < bar*4:
                break

        if prior_idx is None:
            continue

        prior=result[prior_idx]
        prior_pitch=int(prior["midi"])
        current_pitch=int(e["midi"])

        if current_pitch==prior_pitch:
            same_pitch_upbeats+=1
            continue

        different_pitch_upbeats+=1
        e["pre_upbeat_coherence_midi"]=current_pitch
        e["midi"]=prior_pitch
        e["bass_upbeat_pitch_rule"]="MATCH_PRECEDING_SAME_BAR_BASS_TONE"
        pitch_changes.append({
            "event_index":i,
            "section":str(e.get("section","UNKNOWN")),
            "start_beat":start,
            "bar_index":bar,
            "before_midi":current_pitch,
            "after_midi":prior_pitch,
            "preceding_bass_start_beat":float(prior["start_beat"]),
        })

    if different_pitch_upbeats!=3:
        raise BassDownbeatCoherenceError(
            f"EXPECTED_3_DIFFERENT_PITCH_UPBEATS::{different_pitch_upbeats}"
        )
    if len(pitch_changes)!=3:
        raise BassDownbeatCoherenceError(
            f"EXPECTED_3_PITCH_CHANGES::{len(pitch_changes)}"
        )
    if same_pitch_upbeats!=26:
        raise BassDownbeatCoherenceError(
            f"EXPECTED_26_SAME_PITCH_UPBEATS::{same_pitch_upbeats}"
        )

    if len(result)!=len(source["events"]):
        raise BassDownbeatCoherenceError("EVENT_COUNT_CHANGED")

    non_bass_mutations=0
    onset_changes=0
    velocity_changes=0
    instrument_changes=0

    for before,after in zip(source["events"],result):
        track=str(before.get("track_id","")).upper()
        if float(before["start_beat"])!=float(after["start_beat"]):
            onset_changes+=1
        if int(before["velocity"])!=int(after["velocity"]):
            velocity_changes+=1
        if str(before.get("instrument_id",""))!=str(after.get("instrument_id","")):
            instrument_changes+=1

        if track!="BASS":
            if (
                before.get("midi")!=after.get("midi")
                or abs(float(before["duration_beats"])-float(after["duration_beats"]))>1e-9
            ):
                non_bass_mutations+=1

    if onset_changes or velocity_changes or instrument_changes:
        raise BassDownbeatCoherenceError("NON_DURATION_OR_PITCH_IDENTITY_CHANGED")
    if non_bass_mutations:
        raise BassDownbeatCoherenceError("NON_BASS_MUTATION")

    packet={
        "schema":SCHEMA,
        "status":"PASS",
        "diagnostic_only":True,
        "genre":"ROCK",
        "profile_id":"ROCK_CORE_V2",
        "source_execution_sha256":source["execution_sha256"],
        "tempo_bpm":source["tempo_bpm"],
        "bar_count":source["bar_count"],
        "event_count":len(result),
        "events":result,
        "bass_event_count":len(bass_indices),
        "max_bass_gate_beats":MAX_GATE_BEATS,
        "bass_duration_changed_event_count":len(duration_changes),
        "bass_duration_change_manifest":duration_changes,
        "half_beat_upbeat_same_pitch_count":26,
        "half_beat_upbeat_pitch_change_source_count":3,
        "bass_upbeat_pitch_normalized_event_count":len(pitch_changes),
        "bass_upbeat_pitch_change_manifest":pitch_changes,
        "measured_resource_basis":{
            "resource_id":"KARORYFER_GROWLYBASS_V1_002",
            "mapping":"growlybass_vicious.sfz",
            "tempo_bpm":123.0,
            "upbeat_offset_seconds":0.24390243902439024,
            "selected_gate_beats":0.20,
            "selected_gate_active_end_seconds":0.22,
            "pre_upbeat_margin_seconds":0.02390243902439025,
            "decay_grid_artifact_id":13583455938
        },
        "preferred_guitar_treatment_preserved":True,
        "harmony_max_ringing_beats":2.8,
        "safe_strum_treatment_preserved":True,
        "treated_lead_preserved":True,
        "bass_sustain_extension_rejected":True,
        "registry_modified":False,
        "canonical_policy_modified":False,
        "candidate_enabled_live":False,
        "reasoning_engine_used":False,
        "audio_generated":False,
        "listening_approval":False,
        "live_runtime_promoted":False,
        "next_gate":"SYMBOLIC_DOWNBEAT_COHERENCE_VERIFY__THEN_AUDIO_A_B"
    }
    packet["execution_sha256"]=_sha({
        k:v for k,v in packet.items() if k!="execution_sha256"
    })
    return packet


if __name__=="__main__":
    print(json.dumps(execute(),indent=2))
