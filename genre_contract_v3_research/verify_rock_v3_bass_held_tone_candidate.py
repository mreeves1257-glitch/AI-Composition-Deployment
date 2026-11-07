"""Verify Rock V3 held-tone bass candidate.

Requirements:
- source has 147 bass events;
- held-tone candidate keeps exactly 70 strong-beat bass events;
- removes all 77 off-beat bass re-attacks;
- no off-beat bass events remain;
- no overlap between held strong-beat notes;
- release gap before next strong beat remains >= 0.20 beat;
- strong-beat pitch/onset/velocity are unchanged;
- all non-BASS events are unchanged;
- intended mapping is growlybass_clean.sfz.
"""
from __future__ import annotations

from pathlib import Path
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
FORWARD=ROOT/"current_master_forward"
if str(FORWARD) not in sys.path:
    sys.path.insert(0,str(FORWARD))

from rock_v3_bass_offbeat_coherence_candidate import execute as execute_source
from rock_v3_bass_held_tone_candidate import execute as execute_candidate, RELEASE_GAP_BEATS

OUT=ROOT/"genre_contract_v3_research"/"ROCK_V3_BASS_HELD_TONE_CANDIDATE_VERIFY.json"
EPS=1e-9

class VerifyError(RuntimeError):
    pass

def _is_strong(start:float)->bool:
    return abs(start-round(start))<=EPS

def main()->None:
    source=execute_source()
    cand=execute_candidate()
    if source.get("status")!="PASS" or cand.get("status")!="PASS":
        raise VerifyError("SOURCE_OR_CANDIDATE_NOT_PASS")

    source_bass=[e for e in source["events"] if str(e.get("track_id","")).upper()=="BASS"]
    cand_bass=[e for e in cand["events"] if str(e.get("track_id","")).upper()=="BASS"]
    source_non=[e for e in source["events"] if str(e.get("track_id","")).upper()!="BASS"]
    cand_non=[e for e in cand["events"] if str(e.get("track_id","")).upper()!="BASS"]

    if len(source_bass)!=147:
        raise VerifyError(f"SOURCE_BASS_COUNT::{len(source_bass)}")
    if len(cand_bass)!=70:
        raise VerifyError(f"HELD_BASS_COUNT::{len(cand_bass)}")
    if cand["removed_offbeat_bass_event_count"]!=77:
        raise VerifyError("REMOVED_OFFBEAT_COUNT_DRIFT")
    if any(not _is_strong(float(e["start_beat"])) for e in cand_bass):
        raise VerifyError("OFFBEAT_BASS_REMAINS")

    if len(source_non)!=len(cand_non):
        raise VerifyError("NON_BASS_EVENT_COUNT_CHANGED")
    sort_key=lambda e:(
        float(e["start_beat"]),
        str(e.get("track_id","")),
        int(e.get("midi",0)),
        int(e.get("velocity",0)),
        float(e.get("duration_beats",0.0)),
        str(e.get("section","")),
        str(e.get("source_cell","")),
    )
    source_non=sorted(source_non,key=sort_key)
    cand_non=sorted(cand_non,key=sort_key)
    for a,b in zip(source_non,cand_non):
        for key in ("track_id","role","instrument_id","source_instrument_id","start_beat","duration_beats","midi","velocity","section","section_type","source_cell","chord_symbol"):
            if a.get(key)!=b.get(key):
                raise VerifyError("NON_BASS_MUTATION::"+key)

    source_strong=[e for e in source_bass if _is_strong(float(e["start_beat"]))]
    source_strong.sort(key=lambda e:(float(e["start_beat"]),int(e["midi"])))
    cand_bass.sort(key=lambda e:(float(e["start_beat"]),int(e["midi"])))
    if len(source_strong)!=len(cand_bass):
        raise VerifyError("STRONG_ALIGNMENT_COUNT_DRIFT")

    minimum_gap=None
    for i,(a,b) in enumerate(zip(source_strong,cand_bass)):
        for key in ("start_beat","midi","velocity","instrument_id","section","section_type","chord_symbol"):
            if a.get(key)!=b.get(key):
                raise VerifyError("STRONG_IDENTITY_MUTATION::"+key)
        if float(b["duration_beats"])<float(a["duration_beats"])-EPS:
            raise VerifyError("HELD_DURATION_SHORTENED")
        if float(b["duration_beats"])>1.50+EPS:
            raise VerifyError("MAX_HOLD_EXCEEDED")
        if i+1<len(cand_bass):
            nxt=float(cand_bass[i+1]["start_beat"])
            end=float(b["start_beat"])+float(b["duration_beats"])
            gap=nxt-end
            if minimum_gap is None or gap<minimum_gap:
                minimum_gap=gap
            if gap<RELEASE_GAP_BEATS-EPS:
                raise VerifyError(f"RELEASE_GAP_TOO_SMALL::{gap}")

    report={
        "schema":"ROCK_V3_BASS_HELD_TONE_CANDIDATE_VERIFY_001",
        "status":"PASS",
        "diagnostic_only":True,
        "source_execution_sha256":source["execution_sha256"],
        "candidate_execution_sha256":cand["execution_sha256"],
        "source_bass_event_count":147,
        "held_bass_event_count":70,
        "removed_offbeat_bass_event_count":77,
        "offbeat_bass_event_count_after":0,
        "strong_bass_overlap_count":0,
        "minimum_gap_to_next_strong_attack_beats":None if minimum_gap is None else round(minimum_gap,6),
        "max_hold_beats":1.50,
        "strong_beat_pitch_changed":False,
        "strong_beat_onset_changed":False,
        "strong_beat_velocity_changed":False,
        "non_bass_mutation_count":0,
        "intended_bass_mapping":"growlybass_clean.sfz",
        "audio_generated":False,
        "candidate_enabled":False,
        "canonical_policy_modified":False,
        "reasoning_engine_used":False,
        "listening_approval":False,
        "live_runtime_promoted":False,
        "next_gate":"BASS_ONLY_THREE_WAY_RENDER"
    }
    OUT.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))

if __name__=="__main__":
    main()
