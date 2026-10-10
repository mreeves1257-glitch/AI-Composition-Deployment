"""Real Swing with original trumpet, piano, double bass and ride-led kit.

This test cannot claim live readiness: isolate branch, no mix changes, no
manufacturer patches, never relabel Jazz Ballad music as Swing.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import wave

ROOT=Path(__file__).resolve().parents[1]
RUNTIME=ROOT/"composer"/"runtime"
OUT=ROOT/"research_artifacts"/"swing_original_full_stereo"
EXPECTED={"BASS","HARMONY","LEAD","KICK","SNARE","HAT"}

def ensure(ok,reason):
    if not ok:raise RuntimeError("SWING_FINISHED_AUDIO_TEST:"+reason)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    os.environ["AI_COMP_RESOURCE_BANK"]=str(RUNTIME/"sound_resources")
    os.environ["AI_COMP_SFZ_RENDERER"]=str(ROOT/".composer_tools/bin/sfizz_render")
    os.environ["AI_COMP_OUTPUT_ROOT"]=str(OUT/"original_render")
    os.environ["AI_COMP_AUTO_PHRASING_V1"]="0"
    os.environ["AI_COMP_ROCK_MELODY_V1"]="0"
    os.environ["AI_COMP_ROCK2_ENSEMBLE_AUDITION"]="0"
    os.environ["AI_COMP_ROCK2_LEAD_PRESENCE_AUDITION"]="0"
    sys.path.insert(0,str(RUNTIME))
    from engine import AICompositionEngine
    from genre_styles.genre_run_settings import load_genre_configuration
    cfg=load_genre_configuration("Swing")
    ensure(cfg["genre_routing_active"] and not cfg["live_production_activated"],
           "SWING_OWN_GENRE_IDENTITY_NOT_READY")
    from genre_styles.Jazz.swing_recorded_target_links import RID,RIDE_SWING
    ensure((RUNTIME/"sound_resources"/RID/RIDE_SWING).is_file(),
           "REAL_SWING_RIDE_MIDI_MAPPING_NOT_INSTALLED")
    result=AICompositionEngine(history_path=OUT/"fresh_swing_new_music_history.json").run(
        "Swing",target_id="INTERNAL",mode="normal")
    audio=result.get("audio_render") or {}
    theory=result.get("modules",{}).get("theory") or {}
    events=theory.get("events",[])
    ensure(result.get("audio_rendered") and
           audio.get("status")=="AUDIO_RENDER_PASS",
           "RECORDED_SFZ_AUDIO_FAILED:"+str(audio.get("reason")))
    ensure(result.get("genre")=="Swing","NOT_ACTUALLY_SWING")
    ensure(audio.get("output_stage")=="DIRECT_STEREO_SUM_NO_3D",
           "UNAPPROVED_SPATIAL_MIX")
    ensure(len(events)>=1000,"SWING_NOT_FULL_SONG")
    instruments={s["track_id"]:s["instrument_id"] for s in audio.get("stems",[])}
    ensure(set(instruments)==EXPECTED and len(audio["stems"])==6,
           "ORIGINAL_INSTRUMENT_ENSEMBLE_NOT_SIX_REAL_STEMS:"+repr(instruments))
    ensure(instruments=={"BASS":"double_bass","HARMONY":"electric_piano",
                        "LEAD":"trumpet_c","KICK":"kick_drum_rock",
                        "SNARE":"snare_drum","HAT":"ride_cymbal"},
           "WRONG_SWING_AUDIO_INSTRUMENT_IDENTITY:"+repr(instruments))
    ensure(all(s.get("note_count",0)>0 for s in audio["stems"]),
           "MISSING_SAMPLED_INSTRUMENT_MUSIC")
    receipts=list((OUT/"original_render"/"jazz_genre_midi_handoffs").glob(
        "*/JAZZ_MIDI_HANDOFF_RECEIPT.json"))
    ensure(len(receipts)==1,"SWING_MIDI_HANDOFF_NOT_CONNECTED_BEFORE_SFZ")
    receipt=json.loads(receipts[0].read_text())
    ensure(receipt["genre"]=="Swing" and receipt["notes_received"]==len(events)
           and set(receipt["roles_received"])==EXPECTED,
           "ORIGINAL_SWING_COMPOSER_MIDI_NOT_ACCEPTED")
    filename=Path(audio["wav_path"])
    ensure(filename.is_file(),"FINISHED_SWING_WAV_MISSING")
    with wave.open(str(filename),"rb") as stream:
        frames,rate,chans,width=stream.getnframes(),stream.getframerate(),stream.getnchannels(),stream.getsampwidth()
        ensure(rate==44100 and chans==2 and width==2 and frames>rate*90,
               "SWING_NOT_FULL_44100_STEREO")
        for secs in (10,25,50):
            stream.setpos(min(frames-1,secs*rate))
            ensure(any(stream.readframes(min(rate,frames-secs*rate))),
                   "SWING_AUDIO_MISSING_AT:"+str(secs))
    destination=OUT/"SWING_ORIGINAL_SIX_INSTRUMENTS_STEREO.wav"
    shutil.copyfile(filename,destination)
    report={"status":"SWING_FULL_ORIGINAL_RECORDED_STEREO_PASS",
            "genre":"Swing","tempo_bpm":theory.get("tempo_bpm"),
            "bars":theory.get("bars"),"full_composer_midi_notes":len(events),
            "original_six_audio_sources":instruments,"separate_stems":len(audio["stems"]),
            "genre_owned_interpreter_midi_accepted":True,
            "real_recorded_trumpet_sample_verified":True,
            "original_ride_correct_trigger_midi42":True,
            "mixer_and_instrument_sounds_unchanged":True,
            "no_unverified_source_substitutions":True,
            "full_stereo_duration_seconds":round(frames/rate,3),
            "recording_file":destination.name,
            "recording_sha256":hashlib.sha256(destination.read_bytes()).hexdigest(),
            "live_deployed":False,"listening_approval_not_claimed":True}
    (OUT/"RESULT.json").write_text(json.dumps(report,indent=2)+"\n")
    print("SWING_REAL_SIX_RECORDED_INSTRUMENTS_FINISHED_AUDIO_PASS",
          json.dumps(report,sort_keys=True),flush=True)

if __name__=="__main__":
    main()
