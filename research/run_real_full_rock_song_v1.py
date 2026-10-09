"""Research-only REAL full Rock song Composer -> recorded SFZ -> external 3D audio.

Uses unchanged AICompositionEngine.run() exactly as the real input_gateway.
Runs one feature-flag state per Python process for proper isolation and path
control. No simulated stems, no new samples, no publishing or deployment.
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
DEST=ROOT/"research"/"rock_complete_song_validation"
AUDIO_ROOT=RUNTIME/"sound_resources"
RENDERER=ROOT/".composer_tools"/"bin"/"sfizz_render"

def sha_file(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda:stream.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()

def validate_wav(path):
    p=Path(path).resolve()
    if not p.is_file():
        raise RuntimeError("COMPLETED_WAV_MISSING:"+str(p))
    with wave.open(str(p),"rb") as w:
        fields={"channels":w.getnchannels(),"sample_width_bytes":w.getsampwidth(),
                "sample_rate":w.getframerate(),"frames":w.getnframes()}
    if fields["channels"]!=2 or fields["sample_width_bytes"]!=2 or fields["sample_rate"]!=44100:
        raise RuntimeError("UNEXPECTED_FINAL_WAV_FORMAT:"+str(fields))
    fields["duration_seconds"]=round(fields["frames"]/fields["sample_rate"],3)
    if fields["duration_seconds"] < 170:
        raise RuntimeError("SONG_TOO_SHORT_NOT_A_COMPLETE_ROCK_COMPOSITION:"+str(fields))
    fields["size_bytes"]=p.stat().st_size
    fields["sha256"]=sha_file(p)
    return fields

def run(mode):
    if mode not in ("original","candidate"):
        raise ValueError("BAD_MODE")
    output=DEST/mode
    output.mkdir(parents=True,exist_ok=True)
    if not AUDIO_ROOT.is_dir() or not RENDERER.is_file():
        raise RuntimeError("ORIGINAL_COMPOSER_SFZ_RESOURCES_NOT_READY")
    # The imported Composer output_handoff computes its output root at IMPORT.
    os.environ["AI_COMP_RESOURCE_BANK"]=str(AUDIO_ROOT)
    os.environ["AI_COMP_SFZ_RENDERER"]=str(RENDERER)
    os.environ["AI_COMP_OUTPUT_ROOT"]=str(output/"composer_outputs")
    os.environ["AI_COMP_AUTO_PHRASING_V1"]="0"
    os.environ["AI_COMP_ROCK_BASS_SUSTAIN_V1"]="0" if mode=="original" else "1"
    sys.path.insert(0,str(RUNTIME))
    from engine import AICompositionEngine
    report={"run_type":"REAL_COMPLETE_ROCK_SONG_NO_DEPLOY","mode":mode,"flag_activated":mode=="candidate",
            "external_control_panel_changed":False,"plug_changed":False,"standalone_3d_source_changed":False}
    target=output/"result.json"
    try:
        # Independent new histories guarantee identical deterministic seed=0,
        # so ON/OFF differ only where their candidate performance rule changes.
        engine=AICompositionEngine(history_path=output/"independent_history.json")
        result=engine.run("ROCK",target_id="INTERNAL",mode="normal")
        theory=result.get("modules",{}).get("theory",{})
        events=theory.get("events",[])
        report.update({
            "engine_status":result.get("status"),
            "engine_reason":result.get("reason"),
            "genre":result.get("genre"),
            "tempo_bpm":theory.get("tempo_bpm"),
            "bars":theory.get("bars"),
            "score_event_count":len(events),
            "engine_audio_rendered":bool(result.get("audio_rendered")),
            "output_handoff":result.get("output_handoff"),
            "audio_resource_preflight":result.get("audio_resource_preflight"),
            "audio_render_status":result.get("audio_render",{}).get("status"),
            "audio_render_reason":result.get("audio_render",{}).get("reason"),
        })
        # Store the entire score in a small separate research file so an
        # after-run comparison can prove no other instruments changed.
        compact=[{
            "track_id":e.get("track_id"),"instrument_id":e.get("instrument_id"),
            "start_beat":e.get("start_beat"),"duration_beats":e.get("duration_beats"),
            "midi":e.get("midi"),"velocity":e.get("velocity"),
            "articulation":e.get("articulation"),
        } for e in events]
        (output/"composed_events.json").write_text(json.dumps(compact,separators=(",",":")))
        handoff=result.get("audio_render") or {}
        report["source_stems"]=[{
            "track_id":x.get("track_id"),"instrument_id":x.get("instrument_id"),
            "note_count":x.get("note_count"),
            "peak_dbfs":x.get("peak_dbfs"),
            "rms_dbfs":x.get("rms_dbfs"),
            "wav_sha256":sha_file(x["wav_path"]) if x.get("wav_path") and Path(x["wav_path"]).is_file() else None,
        } for x in handoff.get("stems",[])]
        if not result.get("audio_rendered") or handoff.get("status")!="AUDIO_RENDER_PASS":
            raise RuntimeError("TRUE_COMPOSER_NOT_AUDIO_RENDER_PASS:"+repr({
                "engine":result.get("status"),"reason":result.get("reason"),
                "handoff":result.get("output_handoff"),"render":handoff.get("status"),
                "render_reason":handoff.get("reason"),
                "preflight":result.get("audio_resource_preflight",{}).get("missing"),
            }))
        wav=Path(handoff.get("wav_path",""))
        report["final_wav"]=validate_wav(wav)
        master=Path(handoff.get("master_path",""))
        if not master.is_file():
            raise RuntimeError("3D_MASTER_NOT_GENERATED")
        j=json.loads(master.read_text())
        if not j.get("authoritative_3d_master") or j.get("status")!="PASS_PRODUCTION_RESOURCE":
            raise RuntimeError("BAD_3D_MASTER_PROVENANCE:"+str(j.get("status")))
        report["authoritative_master_id"]=j.get("master_id")
        report["source_count"]=len(j.get("audio_objects",[]))
        if report["source_count"]<7:
            raise RuntimeError("NOT_ENOUGH_REAL_RECORDED_SOURCES:"+str(report["source_count"]))
        # Copy only finished playback derivative to compact artifact, without
        # sending original recorded sample bank/source stems.
        destination=output/("ROCK_FULL_SONG_"+mode.upper()+"_3D.wav")
        shutil.copyfile(wav,destination)
        report["final_audio_copied_for_listening"]=destination.name
        report["status"]="FULL_SONG_REAL_COMPOSER_3D_AUDIO_PASS"
        print("TRUE_COMPLETE_ROCK_COMPOSER_AUDIO_PASS",json.dumps({
            "mode":mode,"status":report["status"],"tempo":report["tempo_bpm"],
            "bars":report["bars"],"events":report["score_event_count"],
            "stems":len(report["source_stems"]),"sources":report["source_count"],
            "duration_s":report["final_wav"]["duration_seconds"],
            "file":destination.name,
        }),flush=True)
    except Exception as exc:
        report["status"]="BLOCKED_NEEDS_CAUSE_ANALYSIS"
        report["error"]=f"{type(exc).__name__}: {exc}"
        report["traceback_tail"]=traceback.format_exc()[-4000:]
        print("TRUE_COMPLETE_ROCK_COMPOSER_AUDIO_BLOCKED",report["error"],flush=True)
        raise
    finally:
        target.write_text(json.dumps(report,indent=2,default=str)+"\n")

def compare():
    orig=json.loads((DEST/"original"/"result.json").read_text())
    cand=json.loads((DEST/"candidate"/"result.json").read_text())
    if orig.get("status")!="FULL_SONG_REAL_COMPOSER_3D_AUDIO_PASS" or cand.get("status")!=orig["status"]:
        raise RuntimeError("BOTH_FULL_SONGS_NOT_COMPLETE")
    a=json.loads((DEST/"original"/"composed_events.json").read_text())
    b=json.loads((DEST/"candidate"/"composed_events.json").read_text())
    if len(a)!=len(b):
        raise RuntimeError("EVENT_COUNT_CHANGED")
    edited=[]
    for i,(before,after) in enumerate(zip(a,b)):
        if before==after:
            continue
        differences={key for key in set(before)|set(after) if before.get(key)!=after.get(key)}
        if differences!={"duration_beats"} or before.get("track_id")!="BASS" or before.get("instrument_id") not in ("electric_bass","electric_bass_guitar") or float(after["duration_beats"])<=float(before["duration_beats"]):
            raise RuntimeError("NOT_BASS_ONLY_EDIT_AT:"+str(i)+":"+repr(differences))
        edited.append(i)
    if len(edited)<8:
        raise RuntimeError("EXPECTED_SUSTAIN_EXTENSIONS_MISSING")
    if orig["final_wav"]["duration_seconds"]<170 or cand["final_wav"]["duration_seconds"]<170:
        raise RuntimeError("BOTH_SONGS_NOT_FULL_LENGTH")
    summary={"status":"TWO_FULL_REAL_SONGS_WITH_ONLY_BASS_SCORE_RELEASE_DIFFERENCES_PASS",
            "source_event_count":len(a),"bass_note_extensions":len(edited),
            "all_other_composer_events_identical":True,
            "original_wav":orig["final_audio_copied_for_listening"],
            "candidate_wav":cand["final_audio_copied_for_listening"],
            "source_sfz_audio_both":True,"standalone_3d_mixer_both":True,
            "deployed":False,"musical_preference_proven":False}
    (DEST/"COMPARISON.json").write_text(json.dumps(summary,indent=2)+"\n")
    print("TRUE_TWO_FULL_SONGS_COMPARISON_PASS",json.dumps(summary),flush=True)

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--mode",required=True,choices=("original","candidate","compare"))
    args=ap.parse_args()
    if args.mode=="compare": compare()
    else:run(args.mode)
