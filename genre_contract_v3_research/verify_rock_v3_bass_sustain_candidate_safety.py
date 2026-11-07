"""Symbolic safety analysis for the disabled Rock V3 bass sustain candidate.

Uses the current preferred diagnostic Rock guitar context as source:
Mode A 2.8-beat HARMONY sustain + safe strum candidate. The strum executor does
not modify BASS, so this is equivalent to the current bass writing while fixing
the already-approved guitar treatment around it.

No audio. No live enablement. No canonical mutation.

Candidate:
- next_attack_min_beats = 0.80
- next_attack_max_beats = 2.50
- spacing_fraction = 0.78
- max_sustain_beats = 1.50
- minimum_extension_beats = 0.14

Rules used for this safety simulation:
- extend only; never shorten a bass note;
- do nothing outside the spacing window;
- do not cross the next bass attack;
- do not cross the current 4/4 bar/harmony boundary;
- require at least minimum_extension_beats to make a change;
- preserve pitch, onset, velocity, event count, and every non-BASS role.
"""
from __future__ import annotations

from pathlib import Path
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
FORWARD=ROOT/"current_master_forward"
if str(FORWARD) not in sys.path:
    sys.path.insert(0,str(FORWARD))

from rock_v3_strum_candidate_executor import execute as execute_preferred_guitar

NEXT_MIN=0.80
NEXT_MAX=2.50
SPACING_FRACTION=0.78
MAX_SUSTAIN=1.50
MIN_EXTENSION=0.14
RELEASE_GAP=0.0

class BassSafetyError(RuntimeError):
    pass


def _bar_end(start:float)->float:
    return (int(start//4)+1)*4.0


def main()->None:
    score=execute_preferred_guitar()
    if score.get("status")!="PASS":
        raise BassSafetyError("PREFERRED_GUITAR_SOURCE_NOT_PASS")

    bass=[
        e for e in score["events"]
        if str(e.get("track_id","")).upper()=="BASS"
        and str(e.get("instrument_id",""))=="electric_bass_guitar"
    ]
    bass=sorted(bass,key=lambda e:(float(e["start_beat"]),int(e["midi"])))
    if not bass:
        raise BassSafetyError("NO_BASS_EVENTS")

    changes=[]
    untouched_outside_window=0
    untouched_extension_too_small=0
    untouched_no_room=0
    overlap_count=0
    bar_crossing_count=0
    negative_or_zero_duration_count=0
    min_gap_after=None
    max_extension=0.0
    min_extension=None
    section_counts={}
    spacing_counts={"below_min":0,"inside_window":0,"above_max":0,"no_next":0}

    for i,e in enumerate(bass):
        start=float(e["start_beat"])
        original=float(e["duration_beats"])
        if original<=0:
            negative_or_zero_duration_count+=1

        if i+1>=len(bass):
            spacing_counts["no_next"]+=1
            continue

        nxt=float(bass[i+1]["start_beat"])
        spacing=nxt-start
        if spacing<NEXT_MIN-1e-9:
            spacing_counts["below_min"]+=1
            untouched_outside_window+=1
            continue
        if spacing>NEXT_MAX+1e-9:
            spacing_counts["above_max"]+=1
            untouched_outside_window+=1
            continue

        spacing_counts["inside_window"]+=1
        target=min(
            MAX_SUSTAIN,
            spacing*SPACING_FRACTION,
            max(0.0,nxt-start-RELEASE_GAP),
            max(0.0,_bar_end(start)-start),
        )
        target=max(original,target)  # never shorten
        extension=target-original

        if extension<MIN_EXTENSION-1e-9:
            if extension<=1e-9:
                untouched_no_room+=1
            else:
                untouched_extension_too_small+=1
            continue

        new_duration=round(target,6)
        end=start+new_duration
        gap=nxt-end

        if end>nxt+1e-9:
            overlap_count+=1
        if end>_bar_end(start)+1e-9:
            bar_crossing_count+=1

        if min_gap_after is None or gap<min_gap_after:
            min_gap_after=gap
        max_extension=max(max_extension,extension)
        if min_extension is None or extension<min_extension:
            min_extension=extension

        section=str(e.get("section","UNKNOWN"))
        section_counts[section]=section_counts.get(section,0)+1

        changes.append({
            "event_index_in_bass":i,
            "section":section,
            "start_beat":start,
            "midi":int(e["midi"]),
            "original_duration_beats":original,
            "next_attack_spacing_beats":round(spacing,6),
            "candidate_duration_beats":new_duration,
            "extension_beats":round(extension,6),
            "gap_to_next_attack_beats":round(gap,6),
            "bar_end_beat":_bar_end(start),
        })

    if negative_or_zero_duration_count:
        raise BassSafetyError("BAD_SOURCE_DURATION")
    if overlap_count:
        raise BassSafetyError("CANDIDATE_OVERLAP")
    if bar_crossing_count:
        raise BassSafetyError("CANDIDATE_BAR_CROSSING")

    report={
        "schema":"ROCK_V3_BASS_SUSTAIN_CANDIDATE_SAFETY_001",
        "status":"PASS",
        "diagnostic_only":True,
        "source":"ROCK_BASS_SUSTAIN_V1_RESEARCH_DISABLED_DEFAULT",
        "source_preferred_guitar_execution_sha256":score["execution_sha256"],
        "candidate":{
            "next_attack_min_beats":NEXT_MIN,
            "next_attack_max_beats":NEXT_MAX,
            "spacing_fraction":SPACING_FRACTION,
            "max_sustain_beats":MAX_SUSTAIN,
            "minimum_extension_beats":MIN_EXTENSION,
            "release_gap_beats":RELEASE_GAP,
            "extend_only":True,
            "bar_boundary_cap":True,
            "next_attack_cap":True
        },
        "bass_event_count":len(bass),
        "spacing_classification":spacing_counts,
        "changed_bass_event_count":len(changes),
        "unchanged_outside_spacing_window_count":untouched_outside_window,
        "unchanged_extension_too_small_count":untouched_extension_too_small,
        "unchanged_no_room_count":untouched_no_room,
        "section_change_counts":dict(sorted(section_counts.items())),
        "minimum_applied_extension_beats":None if min_extension is None else round(min_extension,6),
        "maximum_applied_extension_beats":round(max_extension,6),
        "minimum_gap_to_next_attack_after_extension_beats":None if min_gap_after is None else round(min_gap_after,6),
        "next_attack_overlap_count":0,
        "bar_boundary_crossing_count":0,
        "pitch_changed":False,
        "onset_changed":False,
        "velocity_changed":False,
        "event_count_changed":False,
        "guitar_changed_by_bass_candidate":False,
        "lead_changed_by_bass_candidate":False,
        "drums_changed":False,
        "reasoning_engine_used":False,
        "audio_generated":False,
        "candidate_enabled":False,
        "canonical_policy_modified":False,
        "live_runtime_promoted":False,
        "changes":changes,
        "next_gate":"BUILD_BASS_SUSTAIN_SYMBOLIC_EXECUTOR_IF_CHANGE_SET_IS_NONEMPTY_AND_STRUCTURALLY_BOUNDED"
    }

    out=ROOT/"genre_contract_v3_research"/"ROCK_V3_BASS_SUSTAIN_CANDIDATE_SAFETY.json"
    out.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))


if __name__=="__main__":
    main()
