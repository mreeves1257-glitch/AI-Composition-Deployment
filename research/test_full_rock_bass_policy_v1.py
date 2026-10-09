"""Full generated Rock score gate proof: original notes vs feature-gated BASS only.

Does not render final song or activate any service. Requires the original
Composer build, original recorded registry, and Rock adapter inside runtime.
"""
from __future__ import annotations
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent/"composer"/"runtime"
sys.path.insert(0,str(ROOT))
from rock_bass_sustain_policy_v1 import SWITCH

def require(condition, message):
    if not condition:
        raise AssertionError(message)

def build_result():
    src=ROOT/"AI_Comp_Genre_Execution_Adapter_002_WORKING_2026-10-02_184019_CDT.py"
    spec=importlib.util.spec_from_file_location("isolated_rock_adapter",src)
    require(spec and spec.loader,"ORIGINAL_ROCK_ADAPTER_MISSING")
    obj=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    profiles=json.loads((ROOT/"AI_Comp_Genre_Performance_Registry_002_WORKING_COMPLETE_2026-10-02_182810_CDT.json").read_text())
    return obj,profiles["profiles"]["ROCK"]

def run():
    adapter,profile=build_result()
    with patch.dict(os.environ,{SWITCH:"0"}):
        off=adapter.build_setup("ROCK",profile,"normal",0)
    with patch.dict(os.environ,{SWITCH:"1"}):
        on=adapter.build_setup("ROCK",profile,"normal",0)
    require(off.get("status")==on.get("status")=="PASS","GENRE_EXECUTION_FAILED")
    require(off["tempo_bpm"]==on["tempo_bpm"]==145,"TEMPO_CHANGED")
    require(off["bars"]==on["bars"],"FORM_CHANGED")
    original=off["events"];candidate=on["events"]
    require(len(original)==len(candidate)>1000,"SCORE_EVENT_COUNT_CHANGED")
    changes=[]
    for i,(a,b) in enumerate(zip(original,candidate)):
        if a==b:
            continue
        differences={k for k in set(a)|set(b) if a.get(k)!=b.get(k)}
        require(differences=={"duration_beats"},"UNRELATED_FIELD_CHANGED:"+str(i)+":"+repr(differences))
        require(str(a.get("track_id","")).upper()=="BASS","UNRELATED_INSTRUMENT_CHANGED:"+str(i))
        require(a.get("instrument_id") in ("electric_bass","electric_bass_guitar"),"UNAPPROVED_BASS")
        require(float(b["duration_beats"])>float(a["duration_beats"]),"NOTE_SHORTENED")
        changes.append({"index":i,"start_beat":a["start_beat"],
                        "before":a["duration_beats"],"after":b["duration_beats"]})
    require(len(changes)>=8,"GATE_DOES_NOT_REACH_COMPOSER_EVENTS")
    # Strictly ensure no note, track, rhythm or velocity was edited.
    stripped=lambda events:[{k:v for k,v in e.items() if k!="duration_beats"} for e in events]
    require(stripped(original)==stripped(candidate),"PITCH_ONSET_OR_ROLE_CHANGED")
    # Native score snapshots prove programmatic identity in the same build.
    def digest(data):
        return hashlib.sha256(json.dumps(data,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
    report={"status":"PASS","genre":"ROCK",
        "original_mode":"FEATURE_OFF_CANONICAL",
        "candidate_mode":"FEATURE_ON_RESEARCH_ONLY",
        "enabled_env_var":SWITCH,"normal_mode_seed":0,
        "tempo_bpm":off["tempo_bpm"],"bars":off["bars"],
        "total_events":len(original),"bass_extension_count":len(changes),
        "unchanged_non_bass_notes":True,
        "original_sha256":digest(original),"candidate_sha256":digest(candidate),
        "sample_changed_bass_events":changes[:20],
        "deployed":False,"full_song_audio_proven":False,
    }
    output=HERE/"rock_bass_policy_proof_2026-10-08.json"
    output.write_text(json.dumps(report,indent=2)+"\n")
    print("ROCK_FULL_SCORE_FEATURE_GATED_SUSTAIN_PASS",json.dumps(report),flush=True)

if __name__=="__main__":
    run()
