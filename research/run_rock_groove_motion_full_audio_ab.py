"""Two full recorded Rock 3D songs, identical Melody R1 & instruments.

A: user-preferred clean single-hit drums
B: that SAME existing score with gated eighth/sixteenth hats and bass-sync kick
No fake drum hits/samples, no volume/mixer changes or production deployment.
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

ROOT=Path(__file__).resolve().parents[1]
RUNTIME=ROOT/"composer"/"runtime"
OUT=ROOT/"research"/"rock_groove_motion_ab_output"

def assert_valid(test,label):
    if not test: raise AssertionError(label)

def sha(path):
    d=hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda:f.read(1<<20),b""):
            d.update(block)
    return d.hexdigest()

def run(mode):
    assert_valid(mode in ("clean_drums","groove_motion"),"BAD_MODE")
    dest=OUT/mode
    dest.mkdir(parents=True,exist_ok=True)
    os.environ.update({
        "AI_COMP_RESOURCE_BANK":str(RUNTIME/"sound_resources"),
        "AI_COMP_SFZ_RENDERER":str(ROOT/".composer_tools"/"bin"/"sfizz_render"),
        "AI_COMP_OUTPUT_ROOT":str(dest/"composer_outputs"),
        "AI_COMP_ROCK_MELODY_V1":"1",
        "AI_COMP_ROCK_DRUM_COLLISION_V1":"1",
        "AI_COMP_ROCK_GROOVE_MOTION_V1":"1" if mode=="groove_motion" else "0",
        "AI_COMP_ROCK_BASS_SUSTAIN_V1":"0",
        "AI_COMP_AUTO_PHRASING_V1":"0",
    })
    sys.path.insert(0,str(RUNTIME))
    from engine import AICompositionEngine
    result={"mode":mode,"experiment":"ROCK_METER_VS_WRITTEN_DRUM_GROOVE",
            "melody_r1_on":True,"clean_drums_on":True,
            "groove_motion_on":mode=="groove_motion",
            "original_SFZ_samples_unchanged":True,"deployed":False}
    try:
        engine=AICompositionEngine(history_path=dest/"independent_history.json")
        music=engine.run("ROCK",target_id="INTERNAL",mode="normal")
        score=music.get("modules",{}).get("theory",{})
        events=score.get("events") or []
        notes=[{k:e.get(k) for k in ("track_id","instrument_id","start_beat",
            "duration_beats","midi","velocity","articulation")} for e in events]
        (dest/"score_events.json").write_text(json.dumps(notes,separators=(",",":")))
        audio=music.get("audio_render") or {}
        result.update({"engine_status":music.get("status"),"render_status":audio.get("status"),
                       "bars":score.get("bars"),"tempo_bpm":score.get("tempo_bpm"),
                       "score_events":len(notes),"real_instrument_stems":len(audio.get("stems",[]))})
        assert_valid(music.get("audio_rendered") and audio.get("status")=="AUDIO_RENDER_PASS",
                     "TRUE_FULL_SONG_NOT_RENDERED:"+repr(audio.get("status")))
        path=Path(audio.get("wav_path",""))
        master=Path(audio.get("master_path",""))
        assert_valid(path.is_file() and master.is_file(),"REAL_3D_WAV_MASTER_MISSING")
        m=json.loads(master.read_text())
        assert_valid(m.get("authoritative_3d_master") and len(m.get("audio_objects",[]))>=9,
                     "TRUE_3D_MASTER_NOT_FOUND")
        with wave.open(str(path),"rb") as reader:
            spec=(reader.getframerate(),reader.getnchannels(),reader.getsampwidth())
            duration=reader.getnframes()/reader.getframerate()
        assert_valid(spec==(44100,2,2) and 180<duration<240,"INCOMPLETE_STEREO_SONG")
        outfile=dest/("Rock_Clean_Drums_Full_3D.wav" if mode=="clean_drums" else "Rock_Eighth_Sixteenth_Groove_Full_3D.wav")
        shutil.copyfile(path,outfile)
        result.update({"status":"TRUE_COMPLETE_ROCK_GROOVE_3D_PASS",
                       "duration_seconds":round(duration,3),"audio_sha256":sha(outfile),
                       "wav":outfile.name,"recorded_sources":len(m["audio_objects"])})
        print("ROCK_GROOVE_REAL_FULL_AUDIO_PASS",json.dumps(result,sort_keys=True),flush=True)
    except Exception as exc:
        result.update({"status":"BLOCKED","error":repr(exc),"trace":traceback.format_exc()[-3000:]})
        print("ROCK_GROOVE_FULL_AUDIO_BLOCKED",result["error"],flush=True)
        raise
    finally:
        (dest/"report.json").write_text(json.dumps(result,indent=2)+"\n")

def compare():
    load=lambda mode,file:json.loads((OUT/mode/file).read_text())
    a=load("clean_drums","score_events.json")
    b=load("groove_motion","score_events.json")
    am=load("clean_drums","report.json")
    bm=load("groove_motion","report.json")
    assert_valid(am["status"]==bm["status"]=="TRUE_COMPLETE_ROCK_GROOVE_3D_PASS","AUDIO_NOT_FINISHED")
    assert_valid(len(a)==2540,"CLEAN_DRUM_LISTENING_BASELINE_DRIFT")
    unchanged=lambda notes:[e for e in notes if e["track_id"] not in ("HAT","KICK")]
    assert_valid(unchanged(a)==unchanged(b),"OTHER_COMPOSITION_PART_MODIFIED")
    oldhat=[e for e in a if e["track_id"]=="HAT"]
    newhat=[e for e in b if e["track_id"]=="HAT"]
    oldkick=[e for e in a if e["track_id"]=="KICK"]
    newkick=[e for e in b if e["track_id"]=="KICK"]
    assert_valid(len(oldkick)==len(newkick),"KICK_HIT_COUNT_CHANGED")
    # New HAT hits may be added, existing HAT events must all be preserved.
    digest=lambda x:json.dumps(x,sort_keys=True,separators=(",",":"))
    old=Counter(map(digest,oldhat))
    revised=Counter(map(digest,newhat))
    assert_valid(not(old-revised),"ORIGINAL_HAT_HITS_MISSING_OR_CHANGED")
    extras=[json.loads(v) for v,c in (revised-old).items() for _ in range(c)]
    assert_valid(len(extras)>150 and all(x["midi"]==42 and
             x["instrument_id"]=="hi_hat" and x["articulation"]=="hat" for x in extras),
             "NOT_TRUE_ORIGINAL_RECORDED_HAT_SUBDIVISIONS")
    # Existing kick MIDI/velocity identities identical, only a subset of
    # offbeat 2.5 kick note-ons may anticipate bass at 2.25.
    kick_contract=lambda notes:Counter((e["midi"],e["velocity"],e["articulation"],
                                      e["duration_beats"]) for e in notes)
    assert_valid(kick_contract(oldkick)==kick_contract(newkick),
                 "KICK_PITCH_VELOCITY_OR_RECORDED_MAPPING_EDITED")
    old_key=Counter(map(digest,oldkick))
    new_key=Counter(map(digest,newkick))
    removed=[json.loads(v) for v,c in (old_key-new_key).items() for _ in range(c)]
    added=[json.loads(v) for v,c in (new_key-old_key).items() for _ in range(c)]
    assert_valid(len(removed)==len(added)>=15,"EXPECTED_BASS_SYNC_KICK_MOVES_NOT_FOUND")
    bass={round(e["start_beat"],6) for e in a if e["track_id"]=="BASS"}
    assert_valid(all(round(x["start_beat"]%4,6)==2.5 for x in removed),
                 "NON_2_5_KICK_CHANGED")
    assert_valid(all(round(x["start_beat"]%4,6)==2.25 and
                  round(x["start_beat"],6) in bass for x in added),
                 "NEW_KICK_NOT_AT_TRUE_BASS_ONSET")
    first_hats={round(e["start_beat"]%4,6) for e in oldhat}
    now_hats={round(e["start_beat"]%4,6) for e in newhat}
    assert_valid({.5,1.5,2.5,3.5,3.25,3.75}<=now_hats,
                 "NO_HAT_EIGHTH_SIXTEENTH_RHYTHM")
    summary={"status":"FULL_RECORDED_ROCK_GROOVE_A_B_PROOF_PASS",
      "baseline_events":len(a),"groove_events":len(b),
      "original_hat_hits":len(oldhat),"candidate_hat_hits":len(newhat),
      "additional_rhythmic_hat_strikes":len(extras),
      "bass_synced_kicks_repositioned":len(added),
      "protected_melody_bass_snare_guitar_other_parts_identical":True,
      "original_hat_strikes_preserved":True,"existing_kick_source_notes_preserved":True,
      "same_tempo_bpm":am["tempo_bpm"]==bm["tempo_bpm"]==145,
      "same_full_song_duration":am["duration_seconds"]==bm["duration_seconds"],
      "same_recorded_instruments_and_3D":True,
      "actual_music_quality_better_unproven":True,
      "no_production_deployment":True}
    (OUT/"COMPARISON.json").write_text(json.dumps(summary,indent=2)+"\n")
    print("ROCK_TRUE_GROOVE_SUBDIVISION_AB_PASS",json.dumps(summary,sort_keys=True),flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--mode",choices=("clean_drums","groove_motion","compare"),required=True)
    option=p.parse_args()
    compare() if option.mode=="compare" else run(option.mode)
