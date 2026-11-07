"""Rock Core V3 performance executor — Mode A: guitar duration only.

Canonical Mode A implementation for the diagnostic branch.

Reuses the project-authored Rock guitar-duration policy against the 40-bar
V3-developed symbolic candidate, with stricter V3 safeguards:
- no lead phrase stretching across bars;
- no guitar sustain past a bar/harmony boundary without an explicit tie;
- vertical rhythm-guitar chord members remain one coherent gesture.

Mode A changes duration only for electric-guitar events. It never changes pitch,
onset, velocity, track, instrument, event count, drums, bass, tempo or audio.
"""
from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
import hashlib
import json
from typing import Any

from rock_v3_core_development_executor import execute as execute_developed
from rock_v3_core_performance_plan import build as build_plan

SCHEMA="ROCK_V3_CORE_PERFORMANCE_EXECUTION_001"
MODE="A_GUITAR_DURATION_ONLY"


class RockV3CorePerformanceExecutorError(RuntimeError):
    pass


def _sha(value:Any)->str:
    return hashlib.sha256(
        json.dumps(value,sort_keys=True,separators=(",",":"),default=str).encode()
    ).hexdigest()


def _electric_guitar(event:dict[str,Any])->bool:
    return str(event.get("instrument_id",""))=="electric_guitar"


def _bar_end(start:float)->float:
    return (int(start//4)+1)*4.0


def execute(mode:str=MODE)->dict[str,Any]:
    if mode!=MODE:
        raise RockV3CorePerformanceExecutorError(
            "ROCK_PERFORMANCE_MODE_NOT_ENABLED::"+str(mode)
        )

    source=execute_developed()
    plan=build_plan()
    if source.get("status")!="PASS" or plan.get("status")!="PASS":
        raise RockV3CorePerformanceExecutorError("ROCK_PERFORMANCE_INPUT_NOT_READY")
    if plan.get("recommended_first_symbolic_performance_mode")!=MODE:
        raise RockV3CorePerformanceExecutorError("ROCK_PERFORMANCE_MODE_A_NOT_RECOMMENDED")
    if plan.get("symbolic_execution_sha256")!=source.get("execution_sha256"):
        raise RockV3CorePerformanceExecutorError("ROCK_PERFORMANCE_SOURCE_HASH_MISMATCH")

    mode_spec=(plan.get("candidate_modes") or {}).get(MODE) or {}
    if mode_spec.get("apply_guitar_duration_policy") is not True:
        raise RockV3CorePerformanceExecutorError("ROCK_MODE_A_DURATION_POLICY_DISABLED")
    if mode_spec.get("apply_rhythm_guitar_strum_candidate") is not False:
        raise RockV3CorePerformanceExecutorError("ROCK_MODE_A_STRUM_MUST_BE_DISABLED")
    if mode_spec.get("apply_bass_sustain_candidate") is not False:
        raise RockV3CorePerformanceExecutorError("ROCK_MODE_A_BASS_SUSTAIN_MUST_BE_DISABLED")

    harmony_policy=plan["role_plans"]["HARMONY"]["duration_policy"]
    lead_policy=plan["role_plans"]["LEAD"]["duration_policy"]
    rules={
        "close_attack_beats":float(harmony_policy["close_attack_beats"]),
        "rapid_phrase_beats":float(harmony_policy["rapid_phrase_beats"]),
        "release_gap_beats":float(harmony_policy["release_gap_beats"]),
        "ring_fraction":float(harmony_policy["ring_fraction"]),
        "max_ringing_beats":float(harmony_policy["max_ringing_beats"]),
        "lead_connection_fraction":float(lead_policy["rapid_phrase_connection_fraction"]),
        "legato_connection_fraction":float(lead_policy["explicit_legato_connection_fraction"]),
    }

    result=[deepcopy(e) for e in source["events"]]
    tracks:dict[str,list[int]]=defaultdict(list)
    for index,event in enumerate(result):
        if _electric_guitar(event) and str(event.get("track_id","")).upper() in ("HARMONY","LEAD"):
            tracks[str(event.get("track_id","")).upper()].append(index)

    duration_changes=[]
    gesture_count=0

    for track,indices in tracks.items():
        indices.sort(key=lambda i:(float(result[i]["start_beat"]),int(result[i].get("midi",0))))
        gestures:list[list[int]]=[]
        for index in indices:
            start=float(result[index]["start_beat"])
            if (
                not gestures
                or start-float(result[gestures[-1][0]]["start_beat"])
                    > rules["close_attack_beats"]
            ):
                gestures.append([index])
            else:
                gestures[-1].append(index)

        gesture_count+=len(gestures)
        for pos,members in enumerate(gestures):
            first=float(result[members[0]]["start_beat"])
            next_onset=(
                float(result[gestures[pos+1][0]]["start_beat"])
                if pos+1<len(gestures) else None
            )

            # A lead event in another bar is a new phrase window, not permission
            # to stretch the current phrase through an intentional response gap.
            if (
                track=="LEAD"
                and next_onset is not None
                and int(first//4)!=int(next_onset//4)
            ):
                next_onset=None

            for index in members:
                event=result[index]
                start=float(event["start_beat"])
                original=float(event["duration_beats"])
                technique=str(event.get("articulation","")).lower()
                explicit_short=any(
                    word in technique
                    for word in ("mute","staccato","chop","short","pizz")
                )
                explicit_legato="legato" in technique
                if original<=0 or explicit_short or next_onset is None:
                    continue

                spacing=next_onset-first
                if spacing<=0:
                    continue

                candidate=original
                if spacing<rules["rapid_phrase_beats"]:
                    next_gap=max(0.08,next_onset-start)
                    if explicit_legato:
                        candidate=max(
                            original,
                            min(next_gap*rules["legato_connection_fraction"],next_gap),
                        )
                    elif track=="LEAD":
                        candidate=max(
                            original,
                            min(next_gap*rules["lead_connection_fraction"],next_gap),
                        )
                    else:
                        candidate=min(original,max(0.08,next_gap-0.03))
                else:
                    end=first+min(
                        rules["max_ringing_beats"],
                        spacing*rules["ring_fraction"],
                    )
                    end=min(end,next_onset-rules["release_gap_beats"])
                    candidate=max(original,max(0.08,end-start))

                # V3 harmony safety: no cross-bar sustain without an explicit tie.
                max_inside_bar=max(0.01,_bar_end(start)-start)
                candidate=min(candidate,max_inside_bar)
                if candidate<=0:
                    raise RockV3CorePerformanceExecutorError(
                        "ROCK_MODE_A_NONPOSITIVE_DURATION"
                    )

                new_duration=round(candidate,6)
                if abs(new_duration-original)>1e-9:
                    event["pre_performance_duration_beats"]=original
                    event["duration_beats"]=new_duration
                    event["performance_execution_mode"]=MODE
                    event["duration_realization_source"]="PROJECT_INSTRUMENT_PERFORMANCE_V1__V3_HARMONY_SAFETY_CAP"
                    duration_changes.append({
                        "event_index":index,
                        "track_id":track,
                        "start_beat":start,
                        "midi":int(event["midi"]),
                        "before":original,
                        "after":new_duration,
                        "bar_boundary_cap":_bar_end(start),
                    })

    identity_fields=(
        "track_id","role","instrument_id","source_instrument_id",
        "start_beat","midi","velocity","section","section_type",
        "source_cell","chord_symbol",
    )
    if len(result)!=len(source["events"]):
        raise RockV3CorePerformanceExecutorError("ROCK_MODE_A_EVENT_COUNT_CHANGED")
    for before,after in zip(source["events"],result):
        for field in identity_fields:
            if before.get(field)!=after.get(field):
                raise RockV3CorePerformanceExecutorError(
                    "ROCK_MODE_A_IDENTITY_MUTATION::"+field
                )

    for event in result:
        start=float(event["start_beat"])
        end=start+float(event["duration_beats"])
        if end>_bar_end(start)+1e-9:
            raise RockV3CorePerformanceExecutorError(
                "ROCK_MODE_A_CROSSED_HARMONY_BAR_BOUNDARY"
            )

    changed_tracks={x["track_id"] for x in duration_changes}
    if not {"HARMONY","LEAD"}.issubset(changed_tracks):
        raise RockV3CorePerformanceExecutorError(
            "ROCK_MODE_A_DID_NOT_CHANGE_BOTH_GUITAR_ROLES"
        )

    packet={
        "schema":SCHEMA,
        "status":"PASS",
        "genre":"ROCK",
        "profile_id":"ROCK_CORE_V2",
        "resolved_variant":None,
        "family_baseline_only":True,
        "mode":MODE,
        "bar_count":source["bar_count"],
        "tempo_bpm":source["tempo_bpm"],
        "meter":source["meter"],
        "source_execution_sha256":source["execution_sha256"],
        "performance_plan_sha256":plan["performance_plan_sha256"],
        "events":result,
        "event_count":len(result),
        "guitar_gesture_count":gesture_count,
        "duration_changed_event_count":len(duration_changes),
        "duration_change_manifest":duration_changes,
        "pitch_changed":False,
        "onset_changed":False,
        "velocity_changed":False,
        "track_changed":False,
        "instrument_changed":False,
        "event_count_changed":False,
        "drums_changed":False,
        "bass_changed":False,
        "random_jitter_used":False,
        "shared_groove_numeric_offsets_applied":False,
        "strum_candidate_applied":False,
        "bass_sustain_candidate_applied":False,
        "continuous_control_applied":False,
        "target_articulation_switching_applied":False,
        "harmony_bar_boundary_crossing_allowed":False,
        "performance_realization_applied":True,
        "performance_realization_scope":"GUITAR_DURATION_ONLY",
        "audio_generated":False,
        "audio_authority":False,
        "render_allowed":False,
        "finished_composition_authority":False,
        "live_runtime_authority":False,
        "reasoning_engine_used":False,
        "musical_quality_proven":False,
        "listening_approval":False,
        "research_candidate_only":True,
        "next_gate":"ROCK_MODE_A_TARGET_CAPABILITY_AND_RESOURCE_PREFLIGHT__NO_AUDIO",
    }
    packet["execution_sha256"]=_sha({
        k:v for k,v in packet.items() if k!="execution_sha256"
    })
    return packet
