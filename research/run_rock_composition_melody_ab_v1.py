"""Full original-vs-ROCK_MELODY_V1 comparison using the REAL AICompositionEngine.

Compares unchanged approved SFZ instruments and the same 3D mixer. The ONLY
musical score differences permitted are on LEAD, where new melodic composition
is explicitly tested. Neither version activates the separate bass research.
Never publishes/deploys anything.
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

ROOT=Path(__file__).resolve().parent.parent
RUNTIME=ROOT/"composer"/"runtime"
DEST=ROOT/"research"/"rock_melody_ab_output"
SOUND_BANK=RUNTIME/"sound_resources"
RENDERER=ROOT/".composer_tools"/"bin"/"sfizz_render"

def sha_file(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for x in iter(lambda:f.read(1024*1024),b""):
            h.update(x)
    return h.hexdigest()

def run(mode):
    if mode not in ("original","melodic_v1"):
        raise ValueError("INVALID_MELODY_STUDY_MODE")
    target=DEST/mode
    target.mkdir(parents=True,exist_ok=True)
    os.environ["AI_COMP_RESOURCE_BANK"]=str(SOUND_BANK)
    os.environ["AI_COMP_SFZ_RENDERER"]=str(RENDERER)
    os.environ["AI_COMP_OUTPUT_ROOT"]=str(target/"composer_outputs")
    os.environ["AI_COMP_ROCK_BASS_SUSTAIN_V1"]="0" # protect original bass
    os.environ["AI_COMP_AUTO_PHRASING_V1"]="0"
    os.environ["AI_COMP_ROCK_MELODY_V1"]="1" if mode=="melodic_v1" else "0"
    sys.path.insert(0,str(RUNTIME))
    from engine import AICompositionEngine
    result={"experiment":"ROCK_MELODIC_COMPOSITION_ONLY","mode":mode,
            "melody_gate_on":mode=="melodic_v1","bass_policy_on":False,
            "deployed":False,"sample_libraries_modified":False}
    try:
        engine=AICompositionEngine(history_path=target/"independent_history.json")
        music=engine.run("ROCK",target_id="INTERNAL",mode="normal")
        score=music.get("modules",{}).get("theory",{})
        notes=[{k:e.get(k) for k in ("track_id","instrument_id","start_beat",
                "duration_beats","midi","velocity","articulation")}
               for e in score.get("events",[])]
        (target/"score_events.json").write_text(json.dumps(notes,separators=(",",":")))
        handoff=music.get("audio_render") or {}
        result.update({"engine_status":music.get("status"),
             "render_status":handoff.get("status"),
             "source_stem_count":len(handoff.get("stems",[])),
             "bars":score.get("bars"),
             "tempo_bpm":score.get("tempo_bpm"),
             "note_event_count":len(notes)})
        if not music.get("audio_rendered") or handoff.get("status")!="AUDIO_RENDER_PASS":
            raise RuntimeError("NO_FINISHED_AUDIO_FROM_TRUE_COMPOSER:"+repr(
              {"status":music.get("status"),"reason":music.get("reason"),
               "audio_status":handoff.get("status"),"render_reason":handoff.get("reason")}))
        path=Path(handoff.get("wav_path",""))
        master=Path(handoff.get("master_path",""))
        if not path.is_file() or not master.is_file():
            raise RuntimeError("MISSING_OUTPUT_WAV_OR_3D_MASTER")
        master_data=json.loads(master.read_text())
        if not master_data.get("authoritative_3d_master"):
            raise RuntimeError("MISSING_AUTHENTIC_3D_MASTER")
        with wave.open(str(path),"rb") as wav:
            channels=wav.getnchannels()
            rate=wav.getframerate()
            width=wav.getsampwidth()
            duration=wav.getnframes()/rate
        if channels!=2 or rate!=44100 or width!=2 or duration<175:
            raise RuntimeError("NOT_COMPLETE_ROCK_SONG:"+str(duration))
        output_name="ROCK_FULL_SONG_"+mode.upper()+"_3D.wav"
        shutil.copyfile(path,target/output_name)
        result.update({"status":"ACTUAL_FULL_SONG_RECORDED_3D_PASS",
                       "audio_duration_seconds":round(duration,3),
                       "wav_sha256":sha_file(target/output_name),
                       "output":output_name,
                       "master_id":master_data.get("master_id"),
                       "3d_source_count":len(master_data.get("audio_objects",[]))})
        print("ROCK_MELODIC_REAL_AUDIO_PASS",json.dumps(result,sort_keys=True),flush=True)
    except Exception as exc:
        result.update({"status":"BLOCKED","error":f"{type(exc).__name__}:{exc}",
                       "traceback":traceback.format_exc()[-3000:]})
        print("ROCK_MELODIC_REAL_AUDIO_BLOCKED",result["error"],flush=True)
        raise
    finally:
        (target/"result.json").write_text(json.dumps(result,indent=2)+"\n")

def compare():
    a=json.loads((DEST/"original"/"score_events.json").read_text())
    b=json.loads((DEST/"melodic_v1"/"score_events.json").read_text())
    originals={t:[e for e in a if e["track_id"]==t] for t in set(e["track_id"] for e in a)}
    candidates={t:[e for e in b if e["track_id"]==t] for t in set(e["track_id"] for e in b)}
    if set(originals)!=set(candidates):
        raise RuntimeError("INSTRUMENT_TRACK_ADDED_REMOVED")
    for track in originals:
        if track!="LEAD" and originals[track]!=candidates[track]:
            raise RuntimeError("UNAUTHORIZED_NONLEAD_SCORE_CHANGE:"+track)
    def score_metrics(notes):
        lead=[e for e in notes if e["track_id"]=="LEAD"]
        harmonic={}; chord_events=[e for e in notes if e["track_id"]=="HARMONY"]
        for e in chord_events:
            bar=int(e["start_beat"]//4)
            harmonic.setdefault(bar,set()).add(int(e["midi"])%12)
        matches=sum(1 for e in lead if int(e["midi"])%12 in harmonic.get(int(e["start_beat"]//4),set()))
        bars=sorted({int(e["start_beat"]//4) for e in lead})
        return {"lead_count":len(lead),"unique_lead_pitches":len({e["midi"] for e in lead}),
                "lead_bar_count":len(bars),
                "chord_tone_rate":round(matches/max(1,len(lead)),4),
                "unique_onset_positions":len({round(e["start_beat"]%4,2) for e in lead}),
                "unique_note_durations":len({round(e["duration_beats"],2) for e in lead}),
                "active_lead_bars":bars}
    original=score_metrics(a);after=score_metrics(b)
    if original["active_lead_bars"]!=after["active_lead_bars"]:
        raise RuntimeError("ORIGINAL_LEAD_RESTS_REMOVED_OR_NEW_BAR")
    if after["unique_lead_pitches"]<=original["unique_lead_pitches"]:
        raise RuntimeError("MELODY_STILL_SIX_FIXED_NOTES")
    if after["chord_tone_rate"]<=original["chord_tone_rate"]:
        raise RuntimeError("MELODY_NOT_MORE_CHORD_RESPONSIVE")
    for name in ("original","melodic_v1"):
        finished=json.loads((DEST/name/"result.json").read_text())
        if finished.get("status")!="ACTUAL_FULL_SONG_RECORDED_3D_PASS":
            raise RuntimeError("UNFINISHED_VARIANT:"+name)
    report={"status":"ROCK_COMPOSITION_A_B_FULL_REAL_AUDIO_PROOF_PASS",
            "baseline":original,"candidate":after,
            "nonlead_tracks_identical":True,
            "same_recorded_instruments":True,
            "same_3d_mixer":True,
            "music_subjectively_better_unproven":True,
            "live_deployment_changed":False}
    (DEST/"COMPARISON.json").write_text(json.dumps(report,indent=2)+"\n")
    print("ROCK_COMPOSITION_ACTUAL_FULL_MUSIC_COMPARE_PASS",json.dumps({
         "baseline_pitches":original["unique_lead_pitches"],
         "candidate_pitches":after["unique_lead_pitches"],
         "baseline_chord_tone_rate":original["chord_tone_rate"],
         "candidate_chord_tone_rate":after["chord_tone_rate"],
         "nonlead_tracks_identical":True}),flush=True)

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--mode",choices=("original","melodic_v1","compare"),required=True)
    args=parser.parse_args()
    compare() if args.mode=="compare" else run(args.mode)
