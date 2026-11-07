"""Rock V3 diagnostic bass off-beat coherence candidate.

Human-directed rule:
- strong-beat bass pitch changes may be valid;
- any off-beat/subdivision bass attack must keep the immediately preceding
  bass pitch;
- bass resonance is capped at the measured 0.20-beat gate so the attack does
  not carry far enough to read as a separate upbeat.

Source:
- preferred diagnostic guitar treatment:
  2.8 HARMONY sustain + safe strum + treated LEAD.

This candidate:
1. caps BASS duration at 0.20 beat;
2. preserves every BASS onset, velocity, event count and instrument;
3. for every non-integer-beat BASS attack, matches its pitch to the immediately
   preceding BASS event;
4. allows pitch changes only on integer beat positions;
5. never adds notes, moves attacks, or extends duration.

Diagnostic only. No live authority.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math
from typing import Any

from rock_v3_strum_candidate_executor import execute as execute_preferred_guitar

SCHEMA="ROCK_V3_BASS_OFFBEAT_COHERENCE_CANDIDATE_001"
MAX_GATE_BEATS=0.20
EPS=1e-9


class BassOffbeatCoherenceError(RuntimeError):
    pass


def _sha(value:Any)->str:
    return hashlib.sha256(
        json.dumps(value,sort_keys=True,separators=(",",":"),default=str).encode()
    ).hexdigest()


def _is_strong_beat(start:float)->bool:
    return abs(start-round(start))<=EPS


def execute()->dict[str,Any]:
    source=execute_preferred_guitar()
    if source.get("status")!="PASS":
        raise BassOffbeatCoherenceError("SOURCE_NOT_PASS")

    result=[deepcopy(e) for e in source["events"]]
    bass_indices=[
        i for i,e in enumerate(result)
        if str(e.get("track_id","")).upper()=="BASS"
        and str(e.get("instrument_id",""))=="electric_bass_guitar"
    ]
    bass_indices.sort(key=lambda i:(float(result[i]["start_beat"]),int(result[i]["midi"])))
    if not bass_indices:
        raise BassOffbeatCoherenceError("NO_BASS_EVENTS")

    duration_changes=[]
    pitch_locks=[]
    offbeat_count=0
    already_same_pitch_offbeat_count=0

    # Damping gate first.
    for i in bass_indices:
        e=result[i]
        original=float(e["duration_beats"])
        new=min(original,MAX_GATE_BEATS)
        if new<original-EPS:
            e["pre_offbeat_coherence_duration_beats"]=original
            e["duration_beats"]=round(new,6)
            e["bass_gate_beats"]=MAX_GATE_BEATS
            e["bass_offbeat_coherence_mode"]="GATE_0P20_PLUS_ALL_OFFBEAT_SAME_TONE"
            duration_changes.append({
                "event_index":i,
                "section":str(e.get("section","UNKNOWN")),
                "start_beat":float(e["start_beat"]),
                "midi":int(e["midi"]),
                "before_duration_beats":original,
                "after_duration_beats":round(new,6),
            })

    # Any off-beat attack keeps the immediately preceding bass pitch.
    prior_index=None
    for i in bass_indices:
        e=result[i]
        start=float(e["start_beat"])
        if prior_index is not None and not _is_strong_beat(start):
            offbeat_count+=1
            prior=result[prior_index]
            prior_pitch=int(prior["midi"])
            current_pitch=int(e["midi"])

            if current_pitch==prior_pitch:
                already_same_pitch_offbeat_count+=1
            else:
                e["pre_offbeat_coherence_midi"]=current_pitch
                e["midi"]=prior_pitch
                e["bass_offbeat_pitch_rule"]="MATCH_IMMEDIATELY_PRECEDING_BASS_TONE"
                pitch_locks.append({
                    "event_index":i,
                    "section":str(e.get("section","UNKNOWN")),
                    "start_beat":start,
                    "bar_index":int(start//4),
                    "local_beat":round(start%4,6),
                    "before_midi":current_pitch,
                    "after_midi":prior_pitch,
                    "preceding_bass_start_beat":float(prior["start_beat"]),
                    "preceding_bass_midi":prior_pitch,
                })
        prior_index=i

    if len(result)!=len(source["events"]):
        raise BassOffbeatCoherenceError("EVENT_COUNT_CHANGED")

    onset_changes=velocity_changes=instrument_changes=non_bass_mutations=0
    duration_extensions=0

    for before,after in zip(source["events"],result):
        track=str(before.get("track_id","")).upper()
        if float(before["start_beat"])!=float(after["start_beat"]):
            onset_changes+=1
        if int(before["velocity"])!=int(after["velocity"]):
            velocity_changes+=1
        if str(before.get("instrument_id",""))!=str(after.get("instrument_id","")):
            instrument_changes+=1
        if float(after["duration_beats"])>float(before["duration_beats"])+EPS:
            duration_extensions+=1

        if track!="BASS" and (
            int(before["midi"])!=int(after["midi"])
            or abs(float(before["duration_beats"])-float(after["duration_beats"]))>EPS
        ):
            non_bass_mutations+=1

    if onset_changes or velocity_changes or instrument_changes:
        raise BassOffbeatCoherenceError("IDENTITY_CHANGED")
    if duration_extensions:
        raise BassOffbeatCoherenceError("DURATION_EXTENDED")
    if non_bass_mutations:
        raise BassOffbeatCoherenceError("NON_BASS_MUTATION")

    # Verify no different-pitch offbeats remain.
    repaired_bass=[result[i] for i in bass_indices]
    remaining=[]
    prior=None
    for e in repaired_bass:
        start=float(e["start_beat"])
        if prior is not None and not _is_strong_beat(start):
            if int(e["midi"])!=int(prior["midi"]):
                remaining.append({
                    "start_beat":start,
                    "midi":int(e["midi"]),
                    "prior_midi":int(prior["midi"]),
                })
        prior=e

    if remaining:
        raise BassOffbeatCoherenceError("DIFFERENT_PITCH_OFFBEAT_REMAINS")

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
        "offbeat_bass_event_count":offbeat_count,
        "already_same_pitch_offbeat_count":already_same_pitch_offbeat_count,
        "bass_offbeat_pitch_normalized_event_count":len(pitch_locks),
        "bass_duration_change_manifest":duration_changes,
        "bass_offbeat_pitch_change_manifest":pitch_locks,
        "different_pitch_offbeat_remaining_count":0,
        "pitch_change_allowed_only_on_strong_beats":True,
        "preferred_guitar_treatment_preserved":True,
        "harmony_max_ringing_beats":2.8,
        "safe_strum_treatment_preserved":True,
        "treated_lead_preserved":True,
        "bass_sustain_extension_rejected":True,
        "canonical_policy_modified":False,
        "candidate_enabled_live":False,
        "reasoning_engine_used":False,
        "audio_generated":False,
        "listening_approval":False,
        "live_runtime_promoted":False,
        "next_gate":"SYMBOLIC_OFFBEAT_COHERENCE_VERIFY_THEN_AUDIO_A_B"
    }
    packet["execution_sha256"]=_sha({
        k:v for k,v in packet.items() if k!="execution_sha256"
    })
    return packet


if __name__=="__main__":
    print(json.dumps(execute(),indent=2))
