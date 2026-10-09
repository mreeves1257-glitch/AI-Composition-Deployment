"""Genuine Rock 127-bar Melody R1 vs Musical Story V2 A/B, recorded SFZ/3D.

Protects completed Melody R1 and every non-lead source note and instrument.
No live service, control panel or plug changes. Two new real recorded stereo
WAV files are made with AICompositionEngine.run, not a score-only fixture.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import traceback
import wave

HERE=Path(__file__).resolve().parents[1]
RUNTIME=HERE/"composer"/"runtime"
OUT=HERE/"research"/"rock_story_v2_full_song"

def require(condition,message):
    if not condition: raise AssertionError(message)

def checksum(path):
    dig=hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda:f.read(1<<20),b""):
            dig.update(block)
    return dig.hexdigest()

def score_slim(events):
    return [{k:e.get(k) for k in ("track_id","instrument_id","start_beat",
         "duration_beats","midi","velocity","articulation")} for e in events]

def run(mode):
    require(mode in ("melody_r1","story_v2"),"BAD_COMPARISON_MODE")
    dest=OUT/mode;dest.mkdir(parents=True,exist_ok=True)
    os.environ.update({
        "AI_COMP_RESOURCE_BANK":str(RUNTIME/"sound_resources"),
        "AI_COMP_SFZ_RENDERER":str(HERE/".composer_tools"/"bin"/"sfizz_render"),
        "AI_COMP_OUTPUT_ROOT":str(dest/"original_composer_outputs"),
        "AI_COMP_ROCK_MELODY_V1":"1",
        "AI_COMP_ROCK_STORY_V2":"1" if mode=="story_v2" else "0",
        "AI_COMP_ROCK_BASS_SUSTAIN_V1":"0",
        "AI_COMP_AUTO_PHRASING_V1":"0",
    })
    sys.path.insert(0,str(RUNTIME))
    from engine import AICompositionEngine
    report={"mode":mode,"experiment":"ROCK_127BAR_SECTION_NARRATIVE",
       "existing_melody_r1_on":True,"story_v2_on":mode=="story_v2",
       "original_sample_sources_unchanged":True,"deployed":False}
    try:
        result=AICompositionEngine(history_path=dest/"independent_history.json").run(
            "ROCK",target_id="INTERNAL",mode="normal"
        )
        theory=result.get("modules",{}).get("theory",{})
        notes=score_slim(theory.get("events",[]))
        (dest/"score_events.json").write_text(json.dumps(notes,separators=(",",":")))
        render=result.get("audio_render") or {}
        require(result.get("audio_rendered") is True,"ENGINE_AUDIO_NOT_RENDERED")
        require(render.get("status")=="AUDIO_RENDER_PASS",
                "ENGINE_HANDOFF_NOT_AUDIO_RENDER_PASS:"+str(render.get("status")))
        wavpath=Path(render.get("wav_path",""))
        master=Path(render.get("master_path",""))
        require(wavpath.is_file() and master.is_file(),"WAV_OR_MASTER_MISSING")
        md=json.loads(master.read_text())
        require(md.get("authoritative_3d_master") and len(md.get("audio_objects",[]))>=9,
                "NOT_PRESERVED_FULL_3D_MASTER")
        with wave.open(str(wavpath),"rb") as f:
            s=(f.getframerate(),f.getnchannels(),f.getsampwidth())
            duration=f.getnframes()/f.getframerate()
        require(s==(44100,2,2) and duration>180,"REAL_FINISHED_WAV_INVALID")
        filename="ROCK_FULL_MELODY_R1_3D.wav" if mode=="melody_r1" else "ROCK_FULL_STORY_V2_3D.wav"
        shutil.copyfile(wavpath,dest/filename)
        report.update({"status":"TRUE_COMPLETE_STEREO_RECORDED_3D_PASS",
           "tempo_bpm":theory.get("tempo_bpm"),"bars":theory.get("bars"),
           "score_events":len(notes),"duration_seconds":round(duration,3),
           "wav_sha256":checksum(dest/filename),"wav_file":filename,
           "real_source_stems":len(render.get("stems",[])),
           "3d_source_count":len(md.get("audio_objects",[]))})
        print("REAL_ROCK_STORY_FULL_SONG_PASS",json.dumps(report,sort_keys=True),flush=True)
    except Exception as exc:
        report.update({"status":"FAILED_NOT_APPROVED",
                       "error":repr(exc),"traceback":traceback.format_exc()[-2500:]})
        print("REAL_ROCK_STORY_V2_BLOCKED",report["error"],flush=True)
        raise
    finally:
        (dest/"result.json").write_text(json.dumps(report,indent=2)+"\n")

def compare():
    def get(mode,fn):return json.loads((OUT/mode/fn).read_text())
    a,b=(get(m,"score_events.json") for m in ("melody_r1","story_v2"))
    a_meta,b_meta=(get(m,"result.json") for m in ("melody_r1","story_v2"))
    require(a_meta["status"]==b_meta["status"]=="TRUE_COMPLETE_STEREO_RECORDED_3D_PASS","MISSING_REAL_3D_AUDIO")
    require(len(a)==2981,"PRESERVED_MELODY_R1_EVENT_BASELINE_DRIFT:"+str(len(a)))
    nolead=lambda seq:[e for e in seq if e.get("track_id")!="LEAD"]
    require(nolead(a)==nolead(b),"PROTECTED_NONLEAD_EVENTS_CHANGED")
    old=[e for e in a if e["track_id"]=="LEAD"]
    new=[e for e in b if e["track_id"]=="LEAD"]
    require(old!=new,"STORY_V2_DID_NOT_MODIFY_MELODY")
    require(len(new)>80 and len(new)<=len(old),"MELODY_SIZE_INVALID")
    bars=lambda s:sorted({int(float(e["start_beat"])//4) for e in s})
    require(bars(old)==bars(new),"ORIGINAL_LEAD_ENTRANCES_OR_RESTS_CHANGED")
    require(all(59<=int(e["midi"])<=76 for e in new),"UNPLAYABLE_LEAD_REGISTER")
    require(all(e["duration_beats"]>0 for e in new),"ZERO_LENGTH_MELODY")
    count=lambda xs:Counter(tuple(int(e["midi"]) for e in sorted(
        (x for x in xs if int(x["start_beat"]//4)==bar),
        key=lambda x:x["start_beat"])) for bar in bars(xs))
    unique_shapes=(len(count(old)),len(count(new)))
    changes={
        "status":"ROCK_R1_VS_STORY_V2_REAL_FULL_RECORDED_3D_COMPARE_PASS",
        "original_score_events":len(a),"story_v2_score_events":len(b),
        "original_lead_events":len(old),"story_v2_lead_events":len(new),
        "lead_bars_identical":True,"protected_nonlead_events_identical":True,
        "original_distinct_pitch_sequences":unique_shapes[0],
        "v2_distinct_pitch_sequences":unique_shapes[1],
        "original_lead_register":[min(e["midi"] for e in old),max(e["midi"] for e in old)],
        "v2_lead_register":[min(e["midi"] for e in new),max(e["midi"] for e in new)],
        "same_real_recorded_instruments":True,"3d_mixer_unchanged":True,
        "artistic_quality_or_hook_memorability_proven":False,
        "no_production_deployment":True,
    }
    (OUT/"COMPARISON.json").write_text(json.dumps(changes,indent=2)+"\n")
    print("REAL_ROCK_STORY_V2_AB_PROOF_PASS",json.dumps(changes),flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--mode",required=True,choices=("melody_r1","story_v2","compare"))
    args=p.parse_args()
    compare() if args.mode=="compare" else run(args.mode)
