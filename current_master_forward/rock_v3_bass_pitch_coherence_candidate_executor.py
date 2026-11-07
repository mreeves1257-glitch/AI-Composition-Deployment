"""Rock V3 diagnostic bass pitch-coherence repair.

Source:
- current preferred diagnostic guitar treatment (2.8 HARMONY sustain + safe strum);
- original Rock BASS pitches/onsets/velocities.

Repair rule:
- preserve every bass onset, pitch, velocity, and event;
- same-pitch succession is left alone;
- before a later BASS attack of a DIFFERENT pitch, cap the earlier note so it
  releases with enough acoustic space before the new pitch attacks;
- if the different-pitch attack is ultra-close (<= 0.30 beat), keep the later
  event on the same pitch instead of creating a pitch flip inside the ringing tail;
- never extend any note and never move an onset.

This is an articulation/pitch-coherence repair, not a sustain enhancement.
Diagnostic only. No live authority.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any

from rock_v3_strum_candidate_executor import execute as execute_preferred_guitar

SCHEMA="ROCK_V3_BASS_PITCH_COHERENCE_CANDIDATE_001"
MODE="RELEASE_AND_LOCK_CLOSE_DIFFERENT_PITCH_ATTACKS"
RELEASE_GAP_BEATS=0.25
ULTRA_CLOSE_PITCH_LOCK_BEATS=0.30


class BassPitchCoherenceError(RuntimeError):
    pass


def _sha(value:Any)->str:
    return hashlib.sha256(
        json.dumps(value,sort_keys=True,separators=(",",":"),default=str).encode()
    ).hexdigest()


def execute()->dict[str,Any]:
    source=execute_preferred_guitar()
    if source.get("status")!="PASS":
        raise BassPitchCoherenceError("SOURCE_NOT_PASS")

    result=[deepcopy(e) for e in source["events"]]
    bass_indices=[
        i for i,e in enumerate(result)
        if str(e.get("track_id","")).upper()=="BASS"
        and str(e.get("instrument_id",""))=="electric_bass_guitar"
    ]
    bass_indices.sort(key=lambda i:(float(result[i]["start_beat"]),int(result[i]["midi"])))
    if not bass_indices:
        raise BassPitchCoherenceError("NO_BASS_EVENTS")

    changes=[]
    pitch_locks=[]
    same_pitch_pairs=0
    different_pitch_pairs=0

    # Work sequentially on the mutable bass events so an ultra-close pitch lock
    # becomes the pitch reference for the following pair.
    for pos,i in enumerate(bass_indices[:-1]):
        j=bass_indices[pos+1]
        current=result[i]
        nxt=result[j]

        start=float(current["start_beat"])
        duration=float(current["duration_beats"])
        end=start+duration
        next_start=float(nxt["start_beat"])
        spacing=next_start-start

        if int(current["midi"])==int(nxt["midi"]):
            same_pitch_pairs+=1
            continue

        different_pitch_pairs+=1

        # There is not enough acoustic time for a clean pitch change this close.
        # Preserve the later attack but keep the ringing bass on one tone.
        if spacing<=ULTRA_CLOSE_PITCH_LOCK_BEATS+1e-9:
            old_pitch=int(nxt["midi"])
            new_pitch=int(current["midi"])
            nxt["pre_pitch_coherence_midi"]=old_pitch
            nxt["midi"]=new_pitch
            nxt["bass_pitch_coherence_mode"]=MODE
            nxt["bass_pitch_lock_reason"]="ULTRA_CLOSE_DIFFERENT_PITCH_ATTACK"
            nxt["bass_pitch_lock_spacing_beats"]=round(spacing,6)
            pitch_locks.append({
                "event_index":j,
                "section":str(nxt.get("section","UNKNOWN")),
                "start_beat":next_start,
                "before_midi":old_pitch,
                "after_midi":new_pitch,
                "spacing_from_prior_attack_beats":round(spacing,6),
            })
            continue

        # For a real pitch change, clear enough space for the old tone's release.
        latest_end=next_start-RELEASE_GAP_BEATS
        if end<=latest_end+1e-9:
            continue

        new_duration=round(max(0.08,latest_end-start),6)
        if new_duration>=duration-1e-9:
            continue
        if new_duration<=0:
            raise BassPitchCoherenceError("NONPOSITIVE_REPAIRED_DURATION")

        current["pre_pitch_coherence_duration_beats"]=duration
        current["duration_beats"]=new_duration
        current["bass_pitch_coherence_mode"]=MODE
        current["bass_release_gap_beats"]=RELEASE_GAP_BEATS

        changes.append({
            "event_index":i,
            "section":str(current.get("section","UNKNOWN")),
            "start_beat":start,
            "midi":int(current["midi"]),
            "next_start_beat":next_start,
            "next_midi":int(nxt["midi"]),
            "before_duration_beats":duration,
            "after_duration_beats":new_duration,
            "duration_reduction_beats":round(duration-new_duration,6),
            "resulting_gap_beats":round(next_start-(start+new_duration),6),
        })

    if len(result)!=len(source["events"]):
        raise BassPitchCoherenceError("EVENT_COUNT_CHANGED")

    identity_fields=(
        "track_id","role","instrument_id","source_instrument_id",
        "start_beat","velocity","section","section_type",
        "source_cell","chord_symbol",
    )
    changed_duration_count=0
    changed_pitch_count=0
    non_bass_changes=0
    remaining_different_pitch_overlap=0

    for before,after in zip(source["events"],result):
        for field in identity_fields:
            if before.get(field)!=after.get(field):
                raise BassPitchCoherenceError("IDENTITY_MUTATION::"+field)
        track=str(before.get("track_id","")).upper()
        if abs(float(before["duration_beats"])-float(after["duration_beats"]))>1e-9:
            changed_duration_count+=1
            if track!="BASS":
                non_bass_changes+=1
        if int(before["midi"])!=int(after["midi"]):
            changed_pitch_count+=1
            if track!="BASS":
                non_bass_changes+=1

    if non_bass_changes:
        raise BassPitchCoherenceError("NON_BASS_MUTATION")
    if changed_duration_count!=len(changes):
        raise BassPitchCoherenceError("DURATION_CHANGE_COUNT_MISMATCH")
    if changed_pitch_count!=len(pitch_locks):
        raise BassPitchCoherenceError("PITCH_LOCK_COUNT_MISMATCH")

    repaired_bass=[result[i] for i in bass_indices]
    for a,b in zip(repaired_bass,repaired_bass[1:]):
        if int(a["midi"])==int(b["midi"]):
            continue
        a_end=float(a["start_beat"])+float(a["duration_beats"])
        b_start=float(b["start_beat"])
        spacing=b_start-float(a["start_beat"])
        required_gap=(RELEASE_GAP_BEATS if spacing>ULTRA_CLOSE_PITCH_LOCK_BEATS else 0.0)
        if a_end>b_start-required_gap+1e-9:
            remaining_different_pitch_overlap+=1

    if remaining_different_pitch_overlap:
        raise BassPitchCoherenceError("DIFFERENT_PITCH_OVERLAP_REMAINS")

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
        "same_pitch_adjacent_pair_count":same_pitch_pairs,
        "different_pitch_adjacent_pair_count":different_pitch_pairs,
        "bass_duration_shortened_event_count":len(changes),
        "bass_pitch_locked_event_count":len(pitch_locks),
        "duration_change_manifest":changes,
        "pitch_lock_manifest":pitch_locks,
        "release_gap_beats":RELEASE_GAP_BEATS,
        "ultra_close_pitch_lock_beats":ULTRA_CLOSE_PITCH_LOCK_BEATS,
        "remaining_different_pitch_overlap_count":0,
        "bass_pitch_changed":bool(pitch_locks),
        "bass_onset_changed":False,
        "bass_velocity_changed":False,
        "event_count_changed":False,
        "bass_duration_extended":False,
        "guitar_changed":False,
        "lead_changed":False,
        "drums_changed":False,
        "preferred_guitar_treatment_preserved":True,
        "harmony_max_ringing_beats":2.8,
        "safe_strum_treatment_preserved":True,
        "reasoning_engine_used":False,
        "audio_generated":False,
        "candidate_enabled_live":False,
        "canonical_policy_modified":False,
        "listening_approval":False,
        "live_runtime_promoted":False,
        "next_gate":"SYMBOLIC_VERIFY_PITCH_COHERENCE_REPAIR_THEN_AUDIO_A_B"
    }
    packet["execution_sha256"]=_sha({
        k:v for k,v in packet.items() if k!="execution_sha256"
    })
    return packet


if __name__=="__main__":
    print(json.dumps(execute(),indent=2))
