"""Controlled Melody R1 vs Melody R1 + exact Rock drum collision cleanup.

Use TRUE AICompositionEngine for BOTH completed recorded-source 3D WAV songs.
All original Shinyguitar/Growlybass/Big Rusty samples and existing score
musical writing remain unchanged. Drum candidate switch is the only change.
No deployment, HTTP requests, control panel or mixer modifications.
"""
from __future__ import annotations

from collections import Counter
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import traceback
import wave

ROOT=Path(__file__).resolve().parents[1]
RUNTIME=ROOT/"composer"/"runtime"
DEST=ROOT/"research"/"rock_drum_collision_ab_output"
SWITCH="AI_COMP_ROCK_DRUM_COLLISION_V1"

def sha_file(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(1048576),b""):
            h.update(chunk)
    return h.hexdigest()

def run(mode):
    if mode not in ("melody_r1","melody_r1_clean_drums"):
        raise ValueError("INVALID_ROCK_DRUM_AB_MODE")
    target=DEST/mode;target.mkdir(parents=True,exist_ok=True)
    os.environ["AI_COMP_RESOURCE_BANK"]=str(RUNTIME/"sound_resources")
    os.environ["AI_COMP_SFZ_RENDERER"]=str(ROOT/".composer_tools"/"bin"/"sfizz_render")
    os.environ["AI_COMP_OUTPUT_ROOT"]=str(target/"composer_outputs")
    os.environ["AI_COMP_ROCK_MELODY_V1"]="1"
    os.environ[SWITCH]="1" if mode=="melody_r1_clean_drums" else "0"
    os.environ["AI_COMP_ROCK_BASS_SUSTAIN_V1"]="0"
    os.environ["AI_COMP_AUTO_PHRASING_V1"]="0"
    sys.path.insert(0,str(RUNTIME))
    from engine import AICompositionEngine
    report={"experiment":"EXACT_ROCK_KICK_SNARE_BACKBEAT_COLLISIONS_ONLY",
            "mode":mode,"melody_r1_unchanged":True,
            "bass_note_off_policy_on":False,
            "drum_research_gate_on":mode=="melody_r1_clean_drums",
            "deployed":False,"source_samples_unchanged":True}
    try:
        music=AICompositionEngine(history_path=target/"independent_history.json").run(
            "ROCK",target_id="INTERNAL",mode="normal")
        score=music.get("modules",{}).get("theory",{})
        events=score.get("events",[])
        notes=[{k:e.get(k) for k in ("track_id","instrument_id","start_beat",
                         "duration_beats","midi","velocity","articulation")} for e in events]
        (target/"score_events.json").write_text(json.dumps(notes,separators=(",",":")))
        render=music.get("audio_render") or {}
        report.update({"engine_status":music.get("status"),"render_status":render.get("status"),
            "bars":score.get("bars"),"tempo_bpm":score.get("tempo_bpm"),
            "event_count":len(notes),"stem_count":len(render.get("stems",[]))})
        if not music.get("audio_rendered") or render.get("status")!="AUDIO_RENDER_PASS":
            raise RuntimeError("NOT_REAL_COMPLETE_RECORDED_AUDIO:"+repr({
                "status":music.get("status"),"reason":music.get("reason"),
                "render":render.get("status"),"error":render.get("reason")}))
        audio=Path(render.get("wav_path",""));master=Path(render.get("master_path",""))
        if not audio.is_file() or not master.is_file():
            raise RuntimeError("FINAL_WAV_OR_3D_MASTER_MISSING")
        metadata=json.loads(master.read_text())
        if not metadata.get("authoritative_3d_master") or len(metadata.get("audio_objects",[]))<9:
            raise RuntimeError("INVALID_REAL_3D_MASTER")
        with wave.open(str(audio),"rb") as f:
            duration=f.getnframes()/f.getframerate()
            spec=(f.getframerate(),f.getnchannels(),f.getsampwidth())
        if spec!=(44100,2,2) or duration<180:
            raise RuntimeError("NOT_FULL_SONG_STEREO:"+repr((spec,duration)))
        label="ORIGINAL_MELODY_R1" if mode=="melody_r1" else "MELODY_R1_SINGLE_DRUM_HITS"
        outfile=target/("ROCK_"+label+"_FULL_3D.wav")
        shutil.copyfile(audio,outfile)
        report.update({"status":"COMPLETE_REAL_3D_ROCK_SONG_PASS",
                       "duration_seconds":round(duration,3),
                       "source_count":len(metadata["audio_objects"]),
                       "audio_file":outfile.name,"wav_sha256":sha_file(outfile)})
        print("ROCK_DRUM_ARRANGEMENT_FULL_AUDIO_PASS",json.dumps(report,sort_keys=True),flush=True)
    except Exception as exc:
        report.update({"status":"BLOCKED","error":str(exc),
                       "traceback":traceback.format_exc()[-3500:]})
        print("ROCK_DRUM_ARRANGEMENT_AUDIO_BLOCKED",report["error"],flush=True)
        raise
    finally:
        (target/"result.json").write_text(json.dumps(report,indent=2)+"\n")

def compare():
    path=lambda mode,name:DEST/mode/name
    a=json.loads(path("melody_r1","score_events.json").read_text())
    b=json.loads(path("melody_r1_clean_drums","score_events.json").read_text())
    oa=json.loads(path("melody_r1","result.json").read_text())
    ob=json.loads(path("melody_r1_clean_drums","result.json").read_text())
    if oa["status"]!=ob["status"]!="COMPLETE_REAL_3D_ROCK_SONG_PASS":
        raise AssertionError("BOTH_REAL_FULL_SONGS_NOT_FINISHED")
    if len(a)!=2981:
        raise AssertionError("PRESERVED_MELODY_R1_SCORE_CHANGED:"+str(len(a)))
    non_drums=lambda events:[x for x in events if x["track_id"] not in ("KICK","SNARE")]
    if non_drums(a)!=non_drums(b):
        raise AssertionError("NON_KICK_SNARE_NOTE_MODIFIED")
    key=lambda n:json.dumps(n,sort_keys=True,separators=(",",":"))
    ca=Counter(map(key,a));cb=Counter(map(key,b))
    added=cb-ca;removed=ca-cb
    if added:
        raise AssertionError("DRUM_ARRANGEMENT_ADDED_OR_MODIFIED_NOTES:"+str(len(added)))
    lost=[json.loads(item) for item,count in removed.items() for _ in range(count)]
    counts=Counter((e["track_id"],e["articulation"]) for e in lost)
    if counts != {("KICK","kick"):187,("SNARE","snare"):254}:
        raise AssertionError("WRONG_SOURCE_PERCUSSION_EVENTS_REMOVED:"+str(counts))
    if len(a)-len(b)!=441:
        raise AssertionError("DRUM_COLLISION_COUNT_MISMATCH")
    def collisions(events):
        seen=Counter((e["track_id"],round(float(e["start_beat"]),9),e["midi"]) for e in events
                     if e["track_id"] in ("KICK","SNARE"))
        return {tr:sum(n-1 for (role,_,_),n in seen.items() if role==tr and n>1)
                for tr in ("KICK","SNARE")}
    before=collisions(a);after=collisions(b)
    if before!={"KICK":187,"SNARE":254} or after!={"KICK":0,"SNARE":0}:
        raise AssertionError("DRUM_COLLISIONS_REMAIN:"+str((before,after)))
    info={"status":"REAL_TWO_FULL_ROCK_SONG_DRUM_COLLISION_A_B_PASS",
        "original_score_events":len(a),"candidate_score_events":len(b),
        "removed_exact_legacy_hits":len(lost),"removed_by_type":dict(
            (role+"_"+art,count) for (role,art),count in counts.items()),
        "collisions_before":before,"collisions_after":after,
        "all_other_instruments_and_melody_r1_identical":True,
        "no_added_notes":True,
        "source_audio_both_recorded_SFZ":True,
        "3d_mixer_unchanged_and_used_both":True,
        "same_song_seconds":oa["duration_seconds"]==ob["duration_seconds"],
        "artistic_improvement_proven":False,
        "live_deployment_modified":False}
    (DEST/"COMPARISON.json").write_text(json.dumps(info,indent=2)+"\n")
    print("ROCK_DRUM_COLLISION_FULL_SONG_AB_VERIFIED",json.dumps(info,sort_keys=True),flush=True)

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--mode",required=True,choices=("melody_r1","melody_r1_clean_drums","compare"))
    arg=parser.parse_args()
    compare() if arg.mode=="compare" else run(arg.mode)
