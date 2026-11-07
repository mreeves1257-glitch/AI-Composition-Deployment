"""Rock V3 diagnostic bass sustain candidate executor.

Source is the current preferred diagnostic guitar treatment:
- Mode A HARMONY duration policy with 2.8-beat max;
- safe note-off-preserving HARMONY strum attack;
- treated LEAD unchanged.

This executor changes only BASS note durations under the disabled
ROCK_BASS_SUSTAIN_V1_RESEARCH_DISABLED_DEFAULT policy.

Candidate rules:
- next attack spacing must be 0.80..2.50 beats;
- target duration is min(0.78 * spacing, 1.50 beats);
- never shorten;
- require at least +0.14 beat extension;
- never cross next BASS attack;
- never cross current bar/harmony boundary;
- preserve pitch, onset, velocity, event count, and all non-BASS roles.

Diagnostic only. No audio or live authority.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any

from rock_v3_strum_candidate_executor import execute as execute_preferred_guitar

SCHEMA="ROCK_V3_BASS_SUSTAIN_CANDIDATE_EXECUTION_001"
MODE="BASS_SUSTAIN_SPACING_BOUNDED"
NEXT_MIN=0.80
NEXT_MAX=2.50
SPACING_FRACTION=0.78
MAX_SUSTAIN=1.50
MIN_EXTENSION=0.14


class RockV3BassSustainCandidateError(RuntimeError):
    pass


def _sha(value:Any)->str:
    return hashlib.sha256(
        json.dumps(value,sort_keys=True,separators=(",",":"),default=str).encode()
    ).hexdigest()


def _bar_end(start:float)->float:
    return (int(start//4)+1)*4.0


def execute()->dict[str,Any]:
    source=execute_preferred_guitar()
    if source.get("status")!="PASS":
        raise RockV3BassSustainCandidateError("PREFERRED_GUITAR_SOURCE_NOT_PASS")

    result=[deepcopy(e) for e in source["events"]]

    bass_indices=[
        i for i,e in enumerate(result)
        if str(e.get("track_id","")).upper()=="BASS"
        and str(e.get("instrument_id",""))=="electric_bass_guitar"
    ]
    bass_indices.sort(key=lambda i:(float(result[i]["start_beat"]),int(result[i]["midi"])))
    if not bass_indices:
        raise RockV3BassSustainCandidateError("NO_BASS_EVENTS")

    changes=[]

    for pos,i in enumerate(bass_indices):
        if pos+1>=len(bass_indices):
            continue

        e=result[i]
        nxt=result[bass_indices[pos+1]]
        start=float(e["start_beat"])
        next_start=float(nxt["start_beat"])
        spacing=next_start-start
        original=float(e["duration_beats"])

        if spacing<NEXT_MIN-1e-9 or spacing>NEXT_MAX+1e-9:
            continue

        target=min(
            MAX_SUSTAIN,
            spacing*SPACING_FRACTION,
            next_start-start,
            _bar_end(start)-start,
        )
        target=max(original,target)
        extension=target-original
        if extension<MIN_EXTENSION-1e-9:
            continue

        new_duration=round(target,6)
        if start+new_duration>next_start+1e-9:
            raise RockV3BassSustainCandidateError("NEXT_BASS_ATTACK_CROSSED")
        if start+new_duration>_bar_end(start)+1e-9:
            raise RockV3BassSustainCandidateError("BAR_BOUNDARY_CROSSED")

        e["pre_bass_sustain_duration_beats"]=original
        e["duration_beats"]=new_duration
        e["bass_sustain_execution_mode"]=MODE
        e["bass_sustain_source"]="ROCK_BASS_SUSTAIN_V1_RESEARCH_DISABLED_DEFAULT"
        e["bass_sustain_spacing_beats"]=round(spacing,6)
        e["bass_sustain_extension_beats"]=round(extension,6)

        changes.append({
            "event_index":i,
            "section":str(e.get("section","UNKNOWN")),
            "start_beat":start,
            "midi":int(e["midi"]),
            "before":original,
            "after":new_duration,
            "extension_beats":round(extension,6),
            "next_attack_spacing_beats":round(spacing,6),
            "gap_to_next_attack_beats":round(next_start-(start+new_duration),6),
            "bar_end_beat":_bar_end(start),
        })

    if len(result)!=len(source["events"]):
        raise RockV3BassSustainCandidateError("EVENT_COUNT_CHANGED")

    identity_fields=(
        "track_id","role","instrument_id","source_instrument_id",
        "start_beat","midi","velocity","section","section_type",
        "source_cell","chord_symbol",
    )
    changed_duration_count=0
    non_bass_mutation_count=0
    pitch_changed=onset_changed=velocity_changed=instrument_changed=False

    for before,after in zip(source["events"],result):
        for field in identity_fields:
            if before.get(field)!=after.get(field):
                raise RockV3BassSustainCandidateError("IDENTITY_MUTATION::"+field)

        bdur=float(before["duration_beats"])
        adur=float(after["duration_beats"])
        if abs(adur-bdur)>1e-9:
            changed_duration_count+=1
            if str(before.get("track_id","")).upper()!="BASS":
                non_bass_mutation_count+=1

    if non_bass_mutation_count:
        raise RockV3BassSustainCandidateError("NON_BASS_DURATION_MUTATION")

    if changed_duration_count!=len(changes):
        raise RockV3BassSustainCandidateError("CHANGE_MANIFEST_COUNT_MISMATCH")

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
        "bass_duration_changed_event_count":len(changes),
        "bass_duration_change_manifest":changes,
        "candidate":{
            "next_attack_min_beats":NEXT_MIN,
            "next_attack_max_beats":NEXT_MAX,
            "spacing_fraction":SPACING_FRACTION,
            "max_sustain_beats":MAX_SUSTAIN,
            "minimum_extension_beats":MIN_EXTENSION,
            "extend_only":True,
            "next_attack_cap":True,
            "bar_boundary_cap":True,
        },
        "pitch_changed":pitch_changed,
        "onset_changed":onset_changed,
        "velocity_changed":velocity_changed,
        "instrument_changed":instrument_changed,
        "event_count_changed":False,
        "guitar_changed_by_bass_candidate":False,
        "lead_changed_by_bass_candidate":False,
        "drums_changed":False,
        "preferred_guitar_treatment_preserved":True,
        "harmony_max_ringing_beats":2.8,
        "safe_strum_treatment_preserved":True,
        "reasoning_engine_used":False,
        "audio_generated":False,
        "audio_authority":False,
        "candidate_enabled_live":False,
        "canonical_policy_modified":False,
        "listening_approval":False,
        "live_runtime_promoted":False,
        "research_candidate_only":True,
        "next_gate":"SYMBOLIC_BASS_SUSTAIN_EXECUTION_VERIFICATION__NO_AUDIO",
    }
    packet["execution_sha256"]=_sha({
        k:v for k,v in packet.items() if k!="execution_sha256"
    })
    return packet


if __name__=="__main__":
    print(json.dumps(execute(),indent=2))
