"""Rock Core V3 performance candidate A: guitar durations only.

Applies the existing project-authored Rock electric-guitar duration policy to the
validated 40-bar V3 symbolic piece, with an added harmony-aware bar-boundary cap.

Mode A intentionally does NOT:
- strum/stagger chord onsets;
- apply bass sustain research;
- move drum onsets;
- change any pitch, velocity, event count, instrument identity or tempo;
- render audio.
"""
from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
import hashlib
import json
import math
from typing import Any

from rock_v3_core_development_executor import execute as build_piece
from rock_v3_core_performance_plan import build as build_performance_plan

SCHEMA="ROCK_V3_CORE_PERFORMANCE_A_001"
MODE="A_GUITAR_DURATION_ONLY"


class RockV3CorePerformanceAError(RuntimeError):
    pass


def _sha(value:Any)->str:
    return hashlib.sha256(
        json.dumps(value,sort_keys=True,separators=(",",":"),default=str).encode()
    ).hexdigest()


def _is_guitar(event:dict[str,Any])->bool:
    return str(event.get("instrument_id","")).lower()=="electric_guitar"


def _explicit_short(event:dict[str,Any])->bool:
    text=str(event.get("articulation","")).lower()
    return any(x in text for x in ("mute","staccato","chop","short","pizz"))


def _bar_end(start:float)->float:
    return (math.floor(start/4.0)+1)*4.0


def execute()->dict[str,Any]:
    source=build_piece()
    plan=build_performance_plan()
    mode=plan["candidate_modes"][MODE]
    if mode.get("apply_guitar_duration_policy") is not True:
        raise RockV3CorePerformanceAError("ROCK_MODE_A_GUITAR_DURATION_POLICY_DISABLED")
    if mode.get("apply_rhythm_guitar_strum_candidate") is not False:
        raise RockV3CorePerformanceAError("ROCK_MODE_A_STRUM_UNEXPECTEDLY_ENABLED")
    if mode.get("apply_bass_sustain_candidate") is not False:
        raise RockV3CorePerformanceAError("ROCK_MODE_A_BASS_SUSTAIN_UNEXPECTEDLY_ENABLED")

    rhythm_rules=plan["role_plans"]["HARMONY"]["duration_policy"]
    lead_rules=plan["role_plans"]["LEAD"]["duration_policy"]
    close_attack=float(rhythm_rules["close_attack_beats"])
    rapid=float(rhythm_rules["rapid_phrase_beats"])
    release_gap=float(rhythm_rules["release_gap_beats"])
    ring_fraction=float(rhythm_rules["ring_fraction"])
    max_ring=float(rhythm_rules["max_ringing_beats"])

    events=[deepcopy(e) for e in source["events"]]
    tracks:dict[str,list[int]]=defaultdict(list)
    for idx,event in enumerate(events):
        if _is_guitar(event) and str(event.get("track_id","")).upper() in ("HARMONY","LEAD"):
            tracks[str(event["track_id"]).upper()].append(idx)

    changed=[]
    gestures_by_track={}
    for track,indices in tracks.items():
        indices.sort(key=lambda i:(float(events[i]["start_beat"]),int(events[i].get("midi",0))))
        gestures:list[list[int]]=[]
        for idx in indices:
            start=float(events[idx]["start_beat"])
            if (
                not gestures
                or start-float(events[gestures[-1][0]]["start_beat"])>close_attack
            ):
                gestures.append([idx])
            else:
                gestures[-1].append(idx)
        gestures_by_track[track]=len(gestures)

        for pos,members in enumerate(gestures):
            first=float(events[members[0]]["start_beat"])
            next_onset=(
                float(events[gestures[pos+1][0]]["start_beat"])
                if pos+1<len(gestures) else None
            )
            if next_onset is None:
                continue
            spacing=next_onset-first
            if spacing<=0:
                raise RockV3CorePerformanceAError(
                    "ROCK_GUITAR_GESTURE_NONPOSITIVE_SPACING::"+track
                )

            for idx in members:
                event=events[idx]
                if _explicit_short(event):
                    continue
                start=float(event["start_beat"])
                original=float(event["duration_beats"])
                if original<=0:
                    raise RockV3CorePerformanceAError("ROCK_GUITAR_NONPOSITIVE_SOURCE_DURATION")

                if spacing<rapid:
                    next_gap=max(0.08,next_onset-start)
                    if track=="LEAD":
                        fraction=(
                            float(lead_rules["explicit_legato_connection_fraction"])
                            if "legato" in str(event.get("articulation","")).lower()
                            else float(lead_rules["rapid_phrase_connection_fraction"])
                        )
                        desired=max(original,min(next_gap*fraction,next_gap))
                    else:
                        desired=min(original,max(0.08,next_gap-0.03))
                else:
                    end=first+min(max_ring,spacing*ring_fraction)
                    end=min(end,next_onset-release_gap)
                    desired=max(original,max(0.08,end-start))

                # V3 harmony safety: without an explicit tie/continuation rule,
                # performance may not carry a note across the next bar's harmony.
                cap=max(0.08,_bar_end(start)-start-0.05)
                desired=min(desired,cap)

                if desired<=0:
                    raise RockV3CorePerformanceAError("ROCK_GUITAR_DURATION_CAP_NONPOSITIVE")
                new_duration=round(desired,6)
                if abs(new_duration-original)>1e-9:
                    changed.append({
                        "track_id":track,
                        "start_beat":start,
                        "midi":int(event["midi"]),
                        "before_duration_beats":original,
                        "after_duration_beats":new_duration,
                        "bar_end_cap":round(cap,6),
                    })
                    event["duration_beats"]=new_duration

    if not changed:
        raise RockV3CorePerformanceAError("ROCK_MODE_A_CHANGED_NO_GUITAR_DURATIONS")
    if not any(x["track_id"]=="HARMONY" for x in changed):
        raise RockV3CorePerformanceAError("ROCK_MODE_A_CHANGED_NO_RHYTHM_GUITAR_DURATIONS")
    if not any(x["track_id"]=="LEAD" for x in changed):
        raise RockV3CorePerformanceAError("ROCK_MODE_A_CHANGED_NO_LEAD_DURATIONS")

    events.sort(key=lambda x:(
        float(x["start_beat"]),str(x["track_id"]),int(x.get("midi") or 0)
    ))

    result={
        "schema":SCHEMA,
        "status":"PASS",
        "genre":"ROCK",
        "profile_id":"ROCK_CORE_V2",
        "performance_mode":MODE,
        "source_execution_sha256":source["execution_sha256"],
        "performance_plan_sha256":plan["performance_plan_sha256"],
        "bar_count":source["bar_count"],
        "tempo_bpm":source["tempo_bpm"],
        "events":events,
        "event_count":len(events),
        "guitar_gesture_counts":gestures_by_track,
        "changed_duration_count":len(changed),
        "changed_durations":changed,
        "onsets_changed":False,
        "pitches_changed":False,
        "velocities_changed":False,
        "event_count_changed":False,
        "instrument_ids_changed":False,
        "drum_events_changed":False,
        "bass_events_changed":False,
        "rhythm_guitar_strum_applied":False,
        "bass_sustain_candidate_applied":False,
        "random_jitter_used":False,
        "harmony_boundary_cap_applied":True,
        "audio_generated":False,
        "audio_authority":False,
        "finished_composition_authority":False,
        "live_runtime_authority":False,
        "reasoning_engine_used":False,
        "musical_quality_proven":False,
        "listening_approval":False,
        "render_allowed":False,
        "next_gate":"AUDIT_MODE_A__THEN_OPTIONAL_MODE_B_STRUM_A_B_PREP__NO_AUDIO_YET",
    }
    result["performance_execution_sha256"]=_sha({
        k:v for k,v in result.items() if k!="performance_execution_sha256"
    })
    return result
