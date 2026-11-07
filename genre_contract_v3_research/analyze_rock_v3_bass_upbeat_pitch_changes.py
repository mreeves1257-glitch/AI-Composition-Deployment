"""Analyze Rock V3 bass pitch changes on eighth-note upbeats.

User musical rule:
- If bass sustains across an upbeat, the sustained tone must remain the same pitch.
- A different-pitch upbeat must not be masked or smeared by the prior downbeat tail.
- If an upcoming upbeat changes pitch, the prior note must decay before that upbeat
  unless the upbeat itself is rewritten in a separate, explicitly approved test.

This script is read-only and symbolic. It does not mutate bass notes.
"""
from __future__ import annotations

from pathlib import Path
import json
import math
import sys

ROOT=Path(__file__).resolve().parents[1]
FORWARD=ROOT/"current_master_forward"
if str(FORWARD) not in sys.path:
    sys.path.insert(0,str(FORWARD))

from rock_v3_strum_candidate_executor import execute as execute_preferred_guitar

SCHEMA="ROCK_V3_BASS_UPBEAT_PITCH_ANALYSIS_001"
EPS=1e-6


def _is_half_beat_upbeat(start:float)->bool:
    frac=start-math.floor(start)
    return abs(frac-0.5)<=EPS


def main()->None:
    score=execute_preferred_guitar()
    if score.get("status")!="PASS":
        raise RuntimeError("SOURCE_NOT_PASS")

    bass=sorted(
        [
            e for e in score["events"]
            if str(e.get("track_id","")).upper()=="BASS"
            and str(e.get("instrument_id",""))=="electric_bass_guitar"
        ],
        key=lambda e:(float(e["start_beat"]),int(e["midi"]))
    )

    events=[]
    upbeat_events=[]
    different_pitch_upbeats=[]
    same_pitch_upbeats=[]
    preceding_tail_crosses_different_pitch_upbeat=[]

    for i,e in enumerate(bass):
        start=float(e["start_beat"])
        dur=float(e["duration_beats"])
        midi=int(e["midi"])
        row={
            "index":i,
            "section":str(e.get("section","UNKNOWN")),
            "start_beat":start,
            "bar_index":int(start//4),
            "beat_in_bar":round(start%4,6),
            "midi":midi,
            "duration_beats":dur,
            "end_beat":round(start+dur,6),
            "is_half_beat_upbeat":_is_half_beat_upbeat(start),
        }
        events.append(row)

        if not row["is_half_beat_upbeat"]:
            continue

        prior=None
        for j in range(i-1,-1,-1):
            p=bass[j]
            if int(float(p["start_beat"])//4)==row["bar_index"]:
                prior=p
                break
            if float(p["start_beat"]) < row["bar_index"]*4:
                break

        if prior is None:
            row2=dict(row)
            row2["prior_note"]=None
            upbeat_events.append(row2)
            continue

        pstart=float(prior["start_beat"])
        pdur=float(prior["duration_beats"])
        pmidi=int(prior["midi"])
        pend=pstart+pdur
        same=(pmidi==midi)

        row2=dict(row)
        row2["prior_note"]={
            "start_beat":pstart,
            "midi":pmidi,
            "duration_beats":pdur,
            "end_beat":round(pend,6),
        }
        row2["same_pitch_as_prior"]=same
        row2["prior_note_reaches_upbeat"]=pend>=start-EPS
        upbeat_events.append(row2)

        if same:
            same_pitch_upbeats.append(row2)
        else:
            different_pitch_upbeats.append(row2)
            if pend>=start-EPS:
                preceding_tail_crosses_different_pitch_upbeat.append(row2)

    report={
        "schema":SCHEMA,
        "status":"PASS",
        "diagnostic_only":True,
        "tempo_bpm":score["tempo_bpm"],
        "bar_count":score["bar_count"],
        "bass_event_count":len(bass),
        "half_beat_upbeat_event_count":len(upbeat_events),
        "same_pitch_upbeat_event_count":len(same_pitch_upbeats),
        "different_pitch_upbeat_event_count":len(different_pitch_upbeats),
        "different_pitch_upbeats_with_prior_tail_reaching_upbeat_count":len(
            preceding_tail_crosses_different_pitch_upbeat
        ),
        "user_rule":{
            "sustain_across_upbeat_requires_same_pitch":True,
            "different_pitch_upbeat_requires_prior_note_to_decay_before_upbeat":True,
            "upbeat_pitch_rewrite_authorized":False
        },
        "different_pitch_upbeats":different_pitch_upbeats,
        "same_pitch_upbeats":same_pitch_upbeats,
        "events":events,
        "canonical_policy_modified":False,
        "audio_generated":False,
        "reasoning_engine_used":False,
        "live_runtime_promoted":False,
        "next_gate":"COMBINE_DECAY_GRID_WITH_DIFFERENT_PITCH_UPBEAT_GUARD"
    }

    out=ROOT/"genre_contract_v3_research"/"ROCK_V3_BASS_UPBEAT_PITCH_ANALYSIS.json"
    out.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))


if __name__=="__main__":
    main()
