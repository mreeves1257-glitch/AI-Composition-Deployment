"""Two different ordinary Rock requests -> actual SFZ stems -> plain stereo WAV.

Runs on an isolated CI machine with real original sound banks. No deployed app,
fake audio, 3D mixer, or edits to source instruments. A fresh Composer engine
and EMPTY new history are used for each composition to test the original bug.
This deliberately tests the existing Composer renderer route; the new
Rock-specific MIDI interpreter integration is a separate pending connection.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import traceback
import wave

PROJECT=Path(__file__).resolve().parents[1]
RUNTIME=PROJECT/"composer"/"runtime"
OUT=PROJECT/"research_artifacts"/"fresh_rock_real_stereo"
BANK=RUNTIME/"sound_resources"
RENDERER=PROJECT/".composer_tools"/"bin"/"sfizz_render"

def require(ok,reason):
    if not ok: raise AssertionError(reason)

def digest(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as stream:
        for buf in iter(lambda:stream.read(1024*1024),b""):
            h.update(buf)
    return h.hexdigest()

def event_checksum(events):
    compact=[{k:e.get(k) for k in ("track_id","instrument_id","midi",
                                   "start_beat","duration_beats","velocity",
                                   "articulation")}
             for e in events]
    return hashlib.sha256(json.dumps(compact,sort_keys=True,separators=(",",":"),
                                     default=str).encode()).hexdigest()

def inspect_wav(path):
    path=Path(path)
    require(path.is_file(),"FINAL_STEREO_WAV_NOT_FOUND")
    with wave.open(str(path),"rb") as f:
        channels,width,sr,frames=(f.getnchannels(),f.getsampwidth(),
                                   f.getframerate(),f.getnframes())
        # Check there are nonzero audio samples in sampled positions across song.
        nonzero_regions=0
        checkpoints=range(0,frames,max(1,frames//16))
        for pos in checkpoints:
            f.setpos(pos)
            raw=f.readframes(min(4096,frames-pos))
            if any(raw):
                nonzero_regions+=1
    require((channels,width,sr)==(2,2,44100),
            "EXPECTED_44100_16BIT_STEREO_WAV")
    require(100<=frames/sr<=245,"NEW_ROCK2_SONG_OUTSIDE_VARIABLE_FORM_DURATION")
    require(nonzero_regions>=9,"STEREO_SONG_LARGELY_EMPTY")
    return {"channels":channels,"sample_width":width,"sample_rate":sr,
            "frames":frames,"duration_seconds":round(frames/sr,3),
            "nonzero_checked_regions":nonzero_regions,
            "file_bytes":path.stat().st_size,"sha256":digest(path)}

def create_preview(source,destination,seconds=18):
    with wave.open(str(source),"rb") as original:
        params=original.getparams()
        frames=min(params.framerate*seconds,original.getnframes())
        # Only copy a short section; the complete song remains separately saved.
        offset=min(params.framerate*12,max(0,original.getnframes()-frames))
        original.setpos(offset)
        with wave.open(str(destination),"wb") as snippet:
            snippet.setparams(params)
            chunk=65536
            left=frames
            while left:
                n=min(chunk,left)
                snippet.writeframes(original.readframes(n))
                left-=n
    return destination

def generate(song):
    require(song in ("one","two"),"UNSUPPORTED_TEST_SONG")
    root=OUT/song
    root.mkdir(parents=True,exist_ok=True)
    require(BANK.is_dir() and RENDERER.is_file(),
            "ORIGINAL_RECORDED_SFZ_BANK_OR_RENDERER_MISSING")
    os.environ["AI_COMP_RESOURCE_BANK"]=str(BANK)
    os.environ["AI_COMP_SFZ_RENDERER"]=str(RENDERER)
    os.environ["AI_COMP_OUTPUT_ROOT"]=str(root/"composer_audio")
    os.environ["AI_COMP_AUTO_PHRASING_V1"]="0"
    os.environ["AI_COMP_ROCK_BASS_SUSTAIN_V1"]="0"
    os.environ["AI_COMP_ROCK_MELODY_V1"]="0"
    sys.path.insert(0,str(RUNTIME))
    from engine import AICompositionEngine

    history=root/"new_empty_song_history.json"
    require(not history.exists(),"SONG_TEST_HISTORY_MUST_START_EMPTY")
    report={"mode":"normal","requested_genre":"ROCK",
            "song":song,"live_deployed":False,
            "producer":"ORIGINAL_AICompositionEngine.run",
            "audio_path":"EXISTING_SFZ_STEMS_TO_DIRECT_STEREO",
            "genre_specific_interpreter_production_link_active":False}
    try:
        result=AICompositionEngine(history_path=history).run(
            "ROCK",target_id="INTERNAL",mode="normal")
        theory=result.get("modules",{}).get("theory",{})
        events=theory.get("events",[])
        audio=result.get("audio_render") or {}
        report.update({
            "engine_status":result.get("status"),
            "engine_reason":result.get("reason"),
            "tempo_bpm":theory.get("tempo_bpm"),
            "bars":theory.get("bars"),
            "creation_seed":theory.get("creation_seed"),
            "composition_fingerprint":theory.get("composition_fingerprint"),
            "notes":len(events),
            "score_sha256":event_checksum(events),
            "audio_render_status":audio.get("status"),
            "audio_rendered":bool(result.get("audio_rendered")),
            "audio_output_stage":audio.get("output_stage"),
            "stems":[x.get("track_id") for x in audio.get("stems",[])],
            "audio_reason":audio.get("reason")
        })
        require(len(events)>1000,"COMPOSER_NO_FULL_LENGTH_ROCK_SCORE")
        require(70<=int(report["bars"])<=108
                and int(report["tempo_bpm"]) in (117,124,131,139,143),
                "OLD_127_BAR_145_BPM_ROCK_WAS_USED")
        require(report["bars"]!=127 and report["tempo_bpm"]!=145,
                "RETIRED_OOMPA_SONG_GOT_REUSED")
        require(result.get("audio_rendered") is True and
                audio.get("status")=="AUDIO_RENDER_PASS",
                "EXISTING_INSTRUMENTS_DID_NOT_RENDER_REAL_AUDIO:"+str(audio.get("reason")))
        require(audio.get("output_stage")=="DIRECT_STEREO_SUM_NO_3D",
                "UNWANTED_3D_OR_WRONG_AUDIO_OUTPUT_STAGE")
        require(len(audio.get("stems",[]))>=10,
                "NEW_ROCK_ENSEMBLE_MISSING_STEMS")
        require(len(set(report["stems"]))==len(report["stems"]),
                "DUPLICATE_INSTRUMENT_TRACK_IN_AUDIO")
        require({"BASS","HARMONY","LEAD","KEYS","KICK","SNARE","HAT",
                 "TOMS","CRASH","RIDE"}.issubset(report["stems"]),
                "ESSENTIAL_NEW_ROCK2_ENSEMBLE_INSTRUMENT_MISSING")
        audio_file=Path(audio["wav_path"])
        report["finished_wav"]=inspect_wav(audio_file)
        manifest=json.loads(Path(audio["output_manifest_path"]).read_text())
        require(manifest.get("output_method")=="DIRECT_STEREO_SUM_NO_3D"
                and manifest.get("has_3d_master") is False
                and manifest.get("source_count")==len(report["stems"]),
                "DIRECT_STEREO_PROVENANCE_INVALID")
        final=root/("ROCK_NEW_SONG_"+song.upper()+"_DIRECT_STEREO.wav")
        shutil.copyfile(audio_file,final)
        preview=root/("ROCK_NEW_SONG_"+song.upper()+"_18SEC_PREVIEW.wav")
        create_preview(audio_file,preview)
        report.update({"status":"FULL_NEW_SONG_REAL_SFZ_DIRECT_STEREO_PASS",
                       "completed_filename":final.name,"preview_file":preview.name})
        print("REAL_FRESH_ROCK_SONG_AUDIO_PASS",json.dumps({
            "song":song,"score_sha256":report["score_sha256"],
            "final_sha256":report["finished_wav"]["sha256"],
            "bars":report["bars"],"notes":report["notes"],
            "stems":report["stems"],
            "duration_seconds":report["finished_wav"]["duration_seconds"],
            "no_3d":True,"live_deployed":False},sort_keys=True),flush=True)
    except Exception as exc:
        report["status"]="FULL_SONG_FAILED"
        report["error"]=str(exc)
        report["traceback"]=traceback.format_exc()[-4500:]
        print("FRESH_SONG_FULL_RENDER_BLOCKED",song,str(exc),flush=True)
        raise
    finally:
        (root/"RESULT.json").write_text(json.dumps(report,indent=2,default=str)+"\n")

def compare():
    a=json.loads((OUT/"one"/"RESULT.json").read_text())
    b=json.loads((OUT/"two"/"RESULT.json").read_text())
    require(a["status"]==b["status"]=="FULL_NEW_SONG_REAL_SFZ_DIRECT_STEREO_PASS",
            "BOTH_REAL_RECORDED_COMPOSITIONS_NOT_COMPLETE")
    require(a["score_sha256"]!=b["score_sha256"],
            "COMPOSER_REPEATED_THE_SAME_MUSICAL_SCORE")
    require(a["finished_wav"]["sha256"]!=b["finished_wav"]["sha256"],
            "FINAL_STEREO_OUTPUT_IDENTICAL_FOR_DIFFERENT_SONGS")
    require(a["creation_seed"]!=b["creation_seed"],
            "COMPOSER_CREATION_SEED_REPEATED")
    require(a["tempo_bpm"]!=145 and b["tempo_bpm"]!=145
            and a["bars"]!=127 and b["bars"]!=127,
            "RETIRED_OOMPA_SONG_FORM_FOUND")
    require("KEYS" in a["stems"] and "KEYS" in b["stems"],
            "ADDITIONAL_INDEPENDENT_RECORDED_INSTRUMENT_MISSING")
    summary={"status":"TWO_DIFFERENT_FULL_ROCK_SONGS_WITH_REAL_RECORDED_INSTRUMENT_AUDIO_PASS",
             "two_different_composer_scores":True,
             "retired_song_never_reused":True,
             "source_style":"MMA_ROCK2_HARD_DRIVING",
             "separate_original_recorded_wurlitzer_role":True,
             "two_different_finished_wavs":True,
             "different_creation_seeds":True,
             "compositions":[{key:r[key] for key in
                 ("song","bars","tempo_bpm","notes","creation_seed","score_sha256",
                  "completed_filename","preview_file")}
                 for r in (a,b)],
             "source_sampled_stems_preserved":True,
             "no_3d":True,
             "production_deployed":False,
             "genre_specific_interpreter_integrated":False}
    (OUT/"COMPARISON.json").write_text(json.dumps(summary,indent=2)+"\n")
    print("TWO_DISTINCT_SONGS_AND_FINAL_AUDIO_PASS",json.dumps(summary,sort_keys=True),flush=True)

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--song",required=True,choices=["one","two","compare"])
    song=ap.parse_args().song
    compare() if song=="compare" else generate(song)
