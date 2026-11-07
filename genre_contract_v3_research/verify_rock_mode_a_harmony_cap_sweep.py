"""Symbolically verify Rock Mode A HARMONY sustain-cap candidates.

This is a no-audio, no-live-authority gate. It verifies that candidate caps only
reduce positive HARMONY duration extensions from canonical Mode A while preserving:
- all canonical HARMONY shortenings,
- pitch/onset/velocity/voicing/event identity,
- LEAD/BASS/DRUM events exactly,
- bar-boundary safety,
- vertical rhythm-guitar chord-duration coherence.

The canonical Mode A implementation is not modified.
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
FORWARD=ROOT/"current_master_forward"
if str(FORWARD) not in sys.path:
    sys.path.insert(0,str(FORWARD))

from rock_v3_core_development_executor import execute as execute_before
from rock_v3_core_performance_executor import execute as execute_after, MODE

SCHEMA="ROCK_MODE_A_HARMONY_CAP_SWEEP_SYMBOLIC_VERIFY_001"
CAPS=(1.4,2.0)


class HarmonyCapVerifyError(RuntimeError):
    pass


def _bar_end(start:float)->float:
    return (int(start//4)+1)*4.0


def _identity(e:dict)->tuple:
    return (
        str(e.get("track_id","")),
        str(e.get("role","")),
        str(e.get("instrument_id","")),
        str(e.get("source_instrument_id","")),
        float(e["start_beat"]),
        int(e["midi"]),
        int(e["velocity"]),
        str(e.get("section","")),
        str(e.get("section_type","")),
        str(e.get("source_cell","")),
        str(e.get("chord_symbol","")),
    )


def _candidate(before:list[dict],after:list[dict],cap:float)->list[dict]:
    out=[]
    for b,a in zip(before,after):
        if _identity(b)!=_identity(a):
            raise HarmonyCapVerifyError("CANONICAL_IDENTITY_DRIFT")
        e=dict(a)
        track=str(b.get("track_id","")).upper()
        original=float(b["duration_beats"])
        canonical=float(a["duration_beats"])
        if track=="HARMONY":
            if canonical>original:
                e["duration_beats"]=round(min(canonical,cap),6)
            else:
                # preserve canonical shortening exactly
                e["duration_beats"]=canonical
        else:
            # no other role is allowed to differ from canonical Mode A
            e["duration_beats"]=canonical
        out.append(e)
    return out


def _audit_candidate(before:list[dict],canonical:list[dict],candidate:list[dict],cap:float)->dict:
    if not (len(before)==len(canonical)==len(candidate)):
        raise HarmonyCapVerifyError("EVENT_COUNT_DRIFT")

    trimmed_note_events=0
    trimmed_gesture_keys=set()
    canonical_shortenings=0
    preserved_shortenings=0
    non_harmony_duration_mutations=0
    identity_mutations=0
    bar_crossings=0
    positive_extensions_above_cap=0

    vertical=defaultdict(list)

    for b,a,c in zip(before,canonical,candidate):
        if _identity(b)!=_identity(c):
            identity_mutations+=1

        track=str(b.get("track_id","")).upper()
        original=float(b["duration_beats"])
        canonical_d=float(a["duration_beats"])
        candidate_d=float(c["duration_beats"])

        if track!="HARMONY" and abs(candidate_d-canonical_d)>1e-9:
            non_harmony_duration_mutations+=1

        if track=="HARMONY":
            if canonical_d<original-1e-9:
                canonical_shortenings+=1
                if abs(candidate_d-canonical_d)<=1e-9:
                    preserved_shortenings+=1
            if candidate_d>cap+1e-9 and canonical_d>original+1e-9:
                positive_extensions_above_cap+=1
            if candidate_d<canonical_d-1e-9:
                # only a positive canonical extension may be trimmed
                if canonical_d<=original+1e-9:
                    raise HarmonyCapVerifyError("TRIMMED_NON_EXTENSION")
                trimmed_note_events+=1
                trimmed_gesture_keys.add((float(b["start_beat"]),str(b.get("section",""))))

            start=float(c["start_beat"])
            if start+candidate_d>_bar_end(start)+1e-9:
                bar_crossings+=1
            vertical[start].append(candidate_d)

    split_gestures=[
        {"start_beat":start,"durations":vals}
        for start,vals in vertical.items()
        if max(vals)-min(vals)>1e-9
    ]

    if identity_mutations:
        raise HarmonyCapVerifyError("IDENTITY_MUTATION")
    if non_harmony_duration_mutations:
        raise HarmonyCapVerifyError("NON_HARMONY_DURATION_MUTATION")
    if preserved_shortenings!=canonical_shortenings:
        raise HarmonyCapVerifyError("CANONICAL_SHORTENING_NOT_PRESERVED")
    if positive_extensions_above_cap:
        raise HarmonyCapVerifyError("CAP_NOT_ENFORCED")
    if bar_crossings:
        raise HarmonyCapVerifyError("BAR_BOUNDARY_CROSSING")
    if split_gestures:
        raise HarmonyCapVerifyError("VERTICAL_CHORD_DURATION_SPLIT")

    first8_note=0
    first8_gestures=set()
    for b,a,c in zip(before,canonical,candidate):
        if str(b.get("track_id","")).upper()!="HARMONY":
            continue
        if float(b["start_beat"])>=32:
            continue
        if float(c["duration_beats"])<float(a["duration_beats"])-1e-9:
            first8_note+=1
            first8_gestures.add((float(b["start_beat"]),str(b.get("section",""))))

    return {
        "cap_beats":cap,
        "trimmed_harmony_note_event_count":trimmed_note_events,
        "trimmed_harmony_vertical_gesture_count":len(trimmed_gesture_keys),
        "first_8_bars_trimmed_note_event_count":first8_note,
        "first_8_bars_trimmed_vertical_gesture_count":len(first8_gestures),
        "canonical_harmony_shortening_event_count":canonical_shortenings,
        "preserved_canonical_harmony_shortening_event_count":preserved_shortenings,
        "identity_mutation_count":0,
        "non_harmony_duration_mutation_count":0,
        "bar_boundary_crossing_count":0,
        "vertical_chord_duration_split_count":0,
        "positive_extension_above_cap_count":0,
    }


def main()->None:
    before=execute_before()
    canonical=execute_after(MODE)
    if before.get("status")!="PASS" or canonical.get("status")!="PASS":
        raise HarmonyCapVerifyError("SOURCE_NOT_PASS")

    before_events=before["events"]
    canonical_events=canonical["events"]
    results={}
    for cap in CAPS:
        cand=_candidate(before_events,canonical_events,cap)
        results[str(cap)]=_audit_candidate(before_events,canonical_events,cand,cap)

    # Expected counts from the already-recorded symbolic forecast.
    if results["1.4"]["trimmed_harmony_note_event_count"]!=117:
        raise HarmonyCapVerifyError("CAP_1_4_FULL_COUNT_DRIFT")
    if results["1.4"]["trimmed_harmony_vertical_gesture_count"]!=39:
        raise HarmonyCapVerifyError("CAP_1_4_GESTURE_COUNT_DRIFT")
    if results["1.4"]["first_8_bars_trimmed_note_event_count"]!=24:
        raise HarmonyCapVerifyError("CAP_1_4_FIRST8_NOTE_COUNT_DRIFT")
    if results["1.4"]["first_8_bars_trimmed_vertical_gesture_count"]!=8:
        raise HarmonyCapVerifyError("CAP_1_4_FIRST8_GESTURE_COUNT_DRIFT")

    if results["2.0"]["trimmed_harmony_note_event_count"]!=78:
        raise HarmonyCapVerifyError("CAP_2_0_FULL_COUNT_DRIFT")
    if results["2.0"]["trimmed_harmony_vertical_gesture_count"]!=26:
        raise HarmonyCapVerifyError("CAP_2_0_GESTURE_COUNT_DRIFT")
    if results["2.0"]["first_8_bars_trimmed_note_event_count"]!=18:
        raise HarmonyCapVerifyError("CAP_2_0_FIRST8_NOTE_COUNT_DRIFT")
    if results["2.0"]["first_8_bars_trimmed_vertical_gesture_count"]!=6:
        raise HarmonyCapVerifyError("CAP_2_0_FIRST8_GESTURE_COUNT_DRIFT")

    report={
        "schema":SCHEMA,
        "status":"PASS",
        "diagnostic_only":True,
        "genre":"ROCK",
        "profile_id":"ROCK_CORE_V2",
        "canonical_mode":MODE,
        "canonical_max_ringing_beats":2.8,
        "candidate_results":results,
        "unchanged_dimensions":[
            "pitch","onset","velocity","voicing","event_count","instrument_identity",
            "LEAD","BASS","KICK","SNARE","HAT","reasoning_engine"
        ],
        "canonical_policy_modified":False,
        "audio_generated":False,
        "production_fidelity_certified":False,
        "listening_approval":False,
        "live_runtime_promoted":False,
        "next_gate":"HUMAN_LISTENING_OF_RENDERED_HARMONY_CAP_SWEEP",
    }

    out=ROOT/"genre_contract_v3_research"/"ROCK_MODE_A_HARMONY_CAP_SWEEP_SYMBOLIC_VERIFY.json"
    out.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))


if __name__=="__main__":
    main()
