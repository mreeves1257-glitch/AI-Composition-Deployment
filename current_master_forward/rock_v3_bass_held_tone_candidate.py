"""Rock V3 diagnostic held-tone bass candidate.

Purpose:
Add bass body/sustain without reintroducing the unwanted upbeat behavior.

Source baseline:
- all-offbeat coherence candidate is accepted for pitch/rhythm behavior;
- every off-beat/subdivision bass pitch is coherent;
- current short-gate Vicious render is human-preferred bass-only.

Held-tone candidate:
- remove all non-integer-beat BASS re-attacks;
- keep only strong integer-beat BASS attacks;
- preserve strong-beat pitch, velocity, section, and instrument identity;
- sustain each strong-beat note toward the next strong-beat attack;
- duration target = min(78% of next-strong spacing, 1.50 beats,
  next-strong spacing minus 0.20-beat release gap);
- no overlaps and no off-beat events remain;
- intended render mapping is sustain-capable growlybass_clean.sfz.

Diagnostic only. No live authority.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any

from rock_v3_bass_offbeat_coherence_candidate import execute as execute_corrected

SCHEMA="ROCK_V3_BASS_HELD_TONE_CANDIDATE_001"
SPACING_FRACTION=0.78
MAX_HOLD_BEATS=1.50
RELEASE_GAP_BEATS=0.20
MIN_HOLD_BEATS=0.60
EPS=1e-9


class HeldToneError(RuntimeError):
    pass


def _sha(value:Any)->str:
    return hashlib.sha256(
        json.dumps(value,sort_keys=True,separators=(",",":"),default=str).encode()
    ).hexdigest()


def _is_strong(start:float)->bool:
    return abs(start-round(start))<=EPS


def execute()->dict[str,Any]:
    source=execute_corrected()
    if source.get("status")!="PASS":
        raise HeldToneError("SOURCE_NOT_PASS")

    non_bass=[deepcopy(e) for e in source["events"] if str(e.get("track_id","")).upper()!="BASS"]
    all_bass=[
        deepcopy(e) for e in source["events"]
        if str(e.get("track_id","")).upper()=="BASS"
    ]
    all_bass.sort(key=lambda e:(float(e["start_beat"]),int(e["midi"])))

    strong=[e for e in all_bass if _is_strong(float(e["start_beat"]))]
    offbeat=[e for e in all_bass if not _is_strong(float(e["start_beat"]))]

    if len(all_bass)!=147:
        raise HeldToneError(f"BASS_COUNT_DRIFT::{len(all_bass)}")
    if len(strong)!=70:
        raise HeldToneError(f"STRONG_BASS_COUNT_DRIFT::{len(strong)}")
    if len(offbeat)!=77:
        raise HeldToneError(f"OFFBEAT_BASS_COUNT_DRIFT::{len(offbeat)}")

    hold_manifest=[]
    for i,e in enumerate(strong):
        start=float(e["start_beat"])
        original=float(e["duration_beats"])

        if i+1 < len(strong):
            nxt=float(strong[i+1]["start_beat"])
            spacing=nxt-start
            target=min(
                MAX_HOLD_BEATS,
                spacing*SPACING_FRACTION,
                max(0.0,spacing-RELEASE_GAP_BEATS),
            )
            target=max(MIN_HOLD_BEATS,target)
            if target>spacing-RELEASE_GAP_BEATS+EPS:
                target=max(0.08,spacing-RELEASE_GAP_BEATS)
        else:
            spacing=None
            target=1.0

        target=round(max(original,target),6)
        e["pre_held_tone_duration_beats"]=original
        e["duration_beats"]=target
        e["bass_held_tone_mode"]="STRONG_BEAT_HELD_NO_OFFBEAT_REATTACK"
        e["bass_held_tone_intended_mapping"]="growlybass_clean.sfz"

        hold_manifest.append({
            "strong_event_index":i,
            "section":str(e.get("section","UNKNOWN")),
            "start_beat":start,
            "midi":int(e["midi"]),
            "original_duration_beats":original,
            "held_duration_beats":target,
            "next_strong_spacing_beats":None if spacing is None else round(spacing,6),
            "release_gap_beats":None if spacing is None else round(spacing-target,6),
        })

    # Recombine and sort by musical time. Non-BASS roles are untouched.
    result=non_bass+strong
    result.sort(key=lambda e:(
        float(e["start_beat"]),
        str(e.get("track_id","")),
        int(e.get("midi",0)),
    ))

    # Verify no offbeat BASS event survived.
    held_bass=[e for e in result if str(e.get("track_id","")).upper()=="BASS"]
    if any(not _is_strong(float(e["start_beat"])) for e in held_bass):
        raise HeldToneError("OFFBEAT_BASS_EVENT_REMAINS")

    overlaps=0
    min_gap=None
    for a,b in zip(held_bass,held_bass[1:]):
        end=float(a["start_beat"])+float(a["duration_beats"])
        gap=float(b["start_beat"])-end
        if min_gap is None or gap<min_gap:
            min_gap=gap
        if gap<-EPS:
            overlaps+=1

    if overlaps:
        raise HeldToneError("STRONG_BASS_OVERLAP")

    packet={
        "schema":SCHEMA,
        "status":"PASS",
        "diagnostic_only":True,
        "genre":"ROCK",
        "profile_id":"ROCK_CORE_V2",
        "source_execution_sha256":source["execution_sha256"],
        "tempo_bpm":source["tempo_bpm"],
        "bar_count":source["bar_count"],
        "events":result,
        "event_count":len(result),
        "source_bass_event_count":len(all_bass),
        "held_bass_event_count":len(held_bass),
        "removed_offbeat_bass_event_count":len(offbeat),
        "strong_bass_event_count":len(strong),
        "hold_manifest":hold_manifest,
        "spacing_fraction":SPACING_FRACTION,
        "max_hold_beats":MAX_HOLD_BEATS,
        "release_gap_beats":RELEASE_GAP_BEATS,
        "minimum_resulting_gap_to_next_strong_beat":None if min_gap is None else round(min_gap,6),
        "offbeat_bass_event_count_after":0,
        "strong_bass_overlap_count":0,
        "strong_beat_pitch_changed":False,
        "strong_beat_onset_changed":False,
        "strong_beat_velocity_changed":False,
        "non_bass_changed":False,
        "intended_bass_mapping":"growlybass_clean.sfz",
        "current_vicious_mapping_not_used_for_true_sustain":True,
        "preferred_guitar_treatment_preserved_symbolically":True,
        "reasoning_engine_used":False,
        "audio_generated":False,
        "candidate_enabled_live":False,
        "canonical_policy_modified":False,
        "listening_approval":False,
        "live_runtime_promoted":False,
        "next_gate":"BASS_ONLY_THREE_WAY_RENDER__VICIOUS_CORRECTED_SHORT_VS_CLEAN_CORRECTED_SHORT_VS_CLEAN_HELD_TONE"
    }
    packet["execution_sha256"]=_sha({
        k:v for k,v in packet.items() if k!="execution_sha256"
    })
    return packet


if __name__=="__main__":
    print(json.dumps(execute(),indent=2))
