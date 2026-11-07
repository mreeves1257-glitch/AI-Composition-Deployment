"""Audit Rock V3 bass pitch changes on off-beat/subdivision attacks.

User-directed musical rule:
- strong-beat/downbeat pitch changes may be valid;
- off-beat/subdivision bass attacks should not introduce a new pitch while the
  pulse tone is still carrying;
- off-beat/subdivision attack should repeat the most recent strong-beat tone or
  be omitted in a later candidate.

This audit is symbolic only.
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

from rock_v3_strum_candidate_executor import execute as execute_source
from rock_v3_bass_downbeat_coherence_candidate import execute as execute_halfbeat_candidate

OUT=ROOT/"genre_contract_v3_research"/"ROCK_V3_BASS_OFFBEAT_PITCH_CHANGE_AUDIT.json"
EPS=1e-9


def _is_strong_beat(start:float)->bool:
    return abs(start-round(start))<=EPS


def audit(events:list[dict],label:str)->dict:
    bass=[
        e for e in events
        if str(e.get("track_id","")).upper()=="BASS"
        and float(e["start_beat"])<64.0
    ]
    bass.sort(key=lambda e:(float(e["start_beat"]),int(e["midi"])))

    offbeats=[]
    different=[]
    prior=None
    for e in bass:
        start=float(e["start_beat"])
        if prior is not None and not _is_strong_beat(start):
            item={
                "start_beat":start,
                "bar_index":int(start//4),
                "local_beat":round(start%4,6),
                "midi":int(e["midi"]),
                "prior_start_beat":float(prior["start_beat"]),
                "prior_midi":int(prior["midi"]),
                "same_pitch_as_prior":int(e["midi"])==int(prior["midi"]),
                "section":str(e.get("section","UNKNOWN"))
            }
            offbeats.append(item)
            if not item["same_pitch_as_prior"]:
                different.append(item)
        prior=e

    return {
        "label":label,
        "bass_event_count":len(bass),
        "offbeat_event_count":len(offbeats),
        "different_pitch_offbeat_count":len(different),
        "different_pitch_offbeats":different,
        "all_offbeats":offbeats,
    }


def main()->None:
    source=execute_source()
    half=execute_halfbeat_candidate()
    if source.get("status")!="PASS" or half.get("status")!="PASS":
        raise RuntimeError("SOURCE_NOT_PASS")

    report={
        "schema":"ROCK_V3_BASS_OFFBEAT_PITCH_CHANGE_AUDIT_001",
        "status":"PASS",
        "diagnostic_only":True,
        "window_bars":16,
        "strong_beat_definition":"integer beat positions only",
        "source":audit(source["events"],"CURRENT_SOURCE"),
        "halfbeat_candidate":audit(half["events"],"HALFBEAT_ONLY_COHERENCE_CANDIDATE"),
        "user_rule":"Off-beat/subdivision bass attacks may not introduce a new pitch relative to the preceding bass tone.",
        "canonical_policy_modified":False,
        "audio_generated":False,
        "reasoning_engine_used":False,
        "live_runtime_promoted":False
    }
    OUT.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))


if __name__=="__main__":
    main()
