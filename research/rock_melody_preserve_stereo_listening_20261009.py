"""One strictly controlled Rock melody listening A/B with actual recorded instruments.

Both variants use the SAME original Composer seed, SFZ programs, untouched
original nonlead notes, direct stereo output, and exactly the same mix gains.
Only experimental ROCK MELODY V1 on/off differs. No control-panel call,
production deployment, 3D mixer, sample replacement or invented stem audio.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import wave
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
RUNTIME=ROOT/"composer"/"runtime"
DEST=ROOT/"research_artifacts"/"rock_melody_listening_ab_20261009"
BANK=RUNTIME/"sound_resources"
RENDERER=ROOT/".composer_tools"/"bin"/"sfizz_render"
FIXED_A_B_SEED=117
PARTS={"BASS","HARMONY","LEAD","KICK","SNARE","HAT","CRASH","TOMS","RIDE","SUBKICK"}

def require(test,message):
    if not test: raise AssertionError(message)

def sha(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def check_wav(p):
    p=Path(p)
    require(p.is_file(),"COMPLETE_STEREO_WAV_MISSING")
    with wave.open(str(p),"rb") as w:
        channels,width,sr,frames=w.getnchannels(),w.getsampwidth(),w.getframerate(),w.getnframes()
        samples=w.readframes(2048)
    require((channels,width,sr)==(2,2,44100) and frames>=170*sr,
            "NOT_ORIGINAL_44K1_16BIT_FULL_LENGTH_STEREO")
    require(any(samples),"BEGINNING_OF_RECORDING_HAS_NO_AUDIO")
    return {"channels":channels,"width":width,"sample_rate":sr,
            "frames":frames,"duration":round(frames/sr,3),
            "size_bytes":p.stat().st_size,"sha256":sha(p)}

def run(mode):
    require(mode in ("baseline","melodic_v1"),"INVALID_COMPARISON_MODE")
    output=DEST/mode
    output.mkdir(parents=True,exist_ok=True)
    require(BANK.is_dir() and RENDERER.is_file(),"ORIGINAL_RECORDINGS_NOT_INSTALLED")
    os.environ["AI_COMP_RESOURCE_BANK"]=str(BANK)
    os.environ["AI_COMP_SFZ_RENDERER"]=str(RENDERER)
    os.environ["AI_COMP_OUTPUT_ROOT"]=str(output/"composer_outputs")
    os.environ["AI_COMP_AUTO_PHRASING_V1"]="0"
    os.environ["AI_COMP_ROCK_BASS_SUSTAIN_V1"]="0"
    os.environ["AI_COMP_ROCK_MELODY_V1"]="1" if mode=="melodic_v1" else "0"
    sys.path.insert(0,str(RUNTIME))
    from engine import AICompositionEngine
    history=output/"empty_history.json"
    require(not history.exists(),"A_B_HISTORY_ALREADY_EXISTS")
    report={
        "mode":mode,"composer":"ORIGINAL_AICompositionEngine",
        "controlled_seed_for_a_b":FIXED_A_B_SEED,
        "melody_candidate_enabled":mode=="melodic_v1",
        "everyday_fresh_song_default_is_preserved":True,
        "mix":"IDENTICAL_DIRECT_STEREO_SETTINGS",
        "independent_original_instrument_stems":True,
        "user_control_panel_modified":False,"deployed":False
    }
    try:
        # Normal new-song requests use fresh entropy, but A/B music studies
        # explicitly pin the entropy for comparing the same original piece.
        with patch("secrets.randbits",return_value=FIXED_A_B_SEED):
            result=AICompositionEngine(history_path=history).run(
                "ROCK",target_id="INTERNAL",mode="normal")
        theory=result.get("modules",{}).get("theory",{})
        events=theory.get("events",[])
        stems=(result.get("audio_render") or {}).get("stems",[])
        render=result.get("audio_render") or {}
        report.update({
            "engine_status":result.get("status"),
            "audio_render_status":render.get("status"),
            "audio_reason":render.get("reason"),
            "seed_used":theory.get("creation_seed"),
            "bars":theory.get("bars"),
            "tempo_bpm":theory.get("tempo_bpm"),
            "event_count":len(events),
            "tracks":sorted({str(e["track_id"]) for e in events}),
            "stems":{str(e["track_id"]):{
                "wav_sha256":sha(e["wav_path"]),
                "note_count":e.get("note_count")
            } for e in stems},
            "stereo_stage":render.get("output_stage")
        })
        require(theory.get("creation_seed")==FIXED_A_B_SEED,
                "CONTROLLED_A_B_SEED_WAS_NOT_USED")
        require(len(events)>1000,"COMPOSER_CREATED_NO_COMPLETE_SONG")
        require(result.get("audio_rendered") is True and
                render.get("status")=="AUDIO_RENDER_PASS",
                "RECORDED_INSTRUMENTS_FAILED_TO_RENDER:"+str(render.get("reason")))
        require(render.get("output_stage")=="DIRECT_STEREO_SUM_NO_3D",
                "A_B_MIX_PATH_WAS_CHANGED")
        require(PARTS.issubset(report["stems"]),"MISSING_INSTRUMENT_STEMS")
        # Save original musical events in full, for track-level equality checks.
        (output/"SCORE.json").write_text(json.dumps([
            {k:e.get(k) for k in ("track_id","instrument_id","start_beat",
                "duration_beats","midi","velocity","articulation")}
            for e in events],separators=(",",":")))
        src=Path(render["wav_path"])
        report["audio"]=check_wav(src)
        recording=output/("ROCK_"+mode.upper()+"_UNALTERED_STEREO.wav")
        shutil.copyfile(src,recording)
        report["recording_name"]=recording.name
        report["status"]="COMPLETE_SONG_REAL_INSTRUMENTS_PASS"
        print("ROCK_MELODY_LISTENING_AUDIO_PASS",json.dumps({
            "mode":mode,"score_events":len(events),
            "lead_events":sum(e["track_id"]=="LEAD" for e in events),
            "audio_sha256":report["audio"]["sha256"],
            "stems":len(stems),
            "duration_seconds":report["audio"]["duration"],
            "3d_mixer_used":False,"live_deployed":False
        },sort_keys=True),flush=True)
    finally:
        (output/"RESULT.json").write_text(json.dumps(report,indent=2)+"\n")

def compare():
    a=json.loads((DEST/"baseline"/"RESULT.json").read_text())
    b=json.loads((DEST/"melodic_v1"/"RESULT.json").read_text())
    require(a["status"]==b["status"]=="COMPLETE_SONG_REAL_INSTRUMENTS_PASS",
            "FULL_AUDIO_INCOMPLETE")
    first=json.loads((DEST/"baseline"/"SCORE.json").read_text())
    second=json.loads((DEST/"melodic_v1"/"SCORE.json").read_text())
    nonlead=lambda events:[e for e in events if e["track_id"]!="LEAD"]
    require(nonlead(first)==nonlead(second),
            "MUSICAL_INSTRUMENT_OTHER_THAN_LEAD_WAS_CHANGED")
    a_lead=[e for e in first if e["track_id"]=="LEAD"]
    b_lead=[e for e in second if e["track_id"]=="LEAD"]
    require(a_lead!=b_lead,"EXPERIMENT_DID_NOT_CHANGE_LEAD_MELODY")
    require(a["tracks"]==b["tracks"],"A_B_NOT_IDENTICAL_TRACK_LAYOUT")
    require(a["tempo_bpm"]==b["tempo_bpm"] and a["bars"]==b["bars"],
            "A_B_NOT_THE_SAME_TEMPO_AND_FORM")
    require(a["seed_used"]==b["seed_used"]==FIXED_A_B_SEED,
            "A_B_USED_DIFFERENT_SONGS")
    require(a["audio"]["sha256"]!=b["audio"]["sha256"],
            "DIFFERENT_MELODY_DID_NOT_CHANGE_FINISHED_SOUND")
    for track in a["stems"]:
        if track=="LEAD":
            require(a["stems"][track]["wav_sha256"]!=b["stems"][track]["wav_sha256"],
                    "LEAD_GUITAR_STEM_NOT_CHANGED")
        else:
            require(a["stems"][track]["wav_sha256"]==b["stems"][track]["wav_sha256"],
                    "INSTRUMENT_AUDIO_STEM_CHANGED_UNEXPECTEDLY:"+track)
    report={
        "status":"ISOLATED_ROCK_MELODY_A_B_REAL_RECORDINGS_VERIFIED",
        "same_song_same_seed":True,
        "same_mix_and_all_nonlead_audio_bit_identical":True,
        "same_sample_recordings":True,
        "distinct_lead_melody":True,
        "same_tempo_and_form":True,
        "3d_processing":False,
        "control_panel_modified":False,
        "production_deployed":False,
        "human_musical_preference_unverified":True,
        "baseline":{
            "lead_notes":len(a_lead),
            "lead_pitches":len({e["midi"] for e in a_lead}),
            "wav_sha256":a["audio"]["sha256"]
        },
        "melodic_candidate":{
            "lead_notes":len(b_lead),
            "lead_pitches":len({e["midi"] for e in b_lead}),
            "wav_sha256":b["audio"]["sha256"]
        }
    }
    (DEST/"A_B_COMPARISON.json").write_text(json.dumps(report,indent=2)+"\n")
    print("ROCK_MELODY_PRESERVED_STEREO_SEPARATION_PASS",
          json.dumps(report,sort_keys=True),flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--mode",required=True,choices=("baseline","melodic_v1","compare"))
    args=p.parse_args()
    compare() if args.mode=="compare" else run(args.mode)
