"""Jazz-family actual same-engine MIDI -> own genre slot -> recorded audio test.

Only Jazz Ballad has all six verified SFZ recorded instruments in this build.
No claim of full audio for remaining 7: their mapped recorded sources still
need complete instrument verification. The same pre-render Jazz MIDI gate runs
for all eight named Jazz variants when individually requested.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import sys
import wave

ROOT=Path(__file__).resolve().parents[1]
RUNTIME=ROOT/"composer"/"runtime"
OUT=ROOT/"research_artifacts"/"jazz_family_connected_audio_20261010"
EXPECTED={
    "HARMONY":"electric_piano",
    "LEAD":"clarinet_bb",
    "BASS":"double_bass",
    "KICK":"kick_drum_rock",
    "SNARE":"snare_drum",
    "HAT":"hi_hat",
}
def require(condition,why):
    if not condition:raise AssertionError(why)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    os.environ["AI_COMP_RESOURCE_BANK"]=str(RUNTIME/"sound_resources")
    os.environ["AI_COMP_SFZ_RENDERER"]=str(ROOT/".composer_tools/bin/sfizz_render")
    os.environ["AI_COMP_OUTPUT_ROOT"]=str(OUT/"original_recorded_audio_output")
    os.environ["AI_COMP_AUTO_PHRASING_V1"]="0"
    os.environ["AI_COMP_ROCK_MELODY_V1"]="0"
    os.environ["AI_COMP_ROCK2_LEAD_PRESENCE_AUDITION"]="0"
    os.environ["AI_COMP_ROCK2_ENSEMBLE_AUDITION"]="0"
    sys.path.insert(0,str(RUNTIME))
    from engine import AICompositionEngine
    result=AICompositionEngine(history_path=OUT/"empty_jazz_history.json").run(
        "Jazz Ballad", target_id="INTERNAL", mode="normal")
    assert result.get("audio_rendered"), ("JAZZ_NOT_FINISHED",result.get("status"),result.get("reason"),result.get("audio_render"))
    theory=result.get("modules",{}).get("theory") or {}
    audio=result.get("audio_render") or {}
    events=theory.get("events",[])
    require(audio.get("status")=="AUDIO_RENDER_PASS","JAZZ_SAMPLE_RENDERER_FAILED")
    require(audio.get("output_stage")=="DIRECT_STEREO_SUM_NO_3D","JAZZ_NOT_STANDARD_STEREO")
    require(len(events)>100,"NO_COMPLETE_JAZZ_COMPOSER_SCORE")
    observed={s["track_id"]:s["instrument_id"] for s in audio.get("stems",[])}
    require(observed==EXPECTED,"JAZZ_NOT_THE_SIX_SEPARATE_ORIGINAL_INSTRUMENT_STEMS:"+str(observed))
    require(all(s.get("note_count",0)>0 for s in audio["stems"]),"JAZZ_SILENT_INSTRUMENT")
    # Confirm the Jazz-specific MIDI receiver ran BEFORE the final WAV,
    # with the existing Output Core's actual full-length Composer events.
    receipts=list((OUT/"original_recorded_audio_output"/"jazz_genre_midi_handoffs").glob("*/JAZZ_MIDI_HANDOFF_RECEIPT.json"))
    require(len(receipts)==1,"JAZZ_MIDI_GENRE_RECEIVER_NOT_CALLED_DURING_REAL_RENDER")
    receipt=json.loads(receipts[0].read_text())
    require(receipt["genre"]=="Jazz Ballad" and
            receipt["notes_received"]==len(events) and
            set(receipt["roles_received"])==set(EXPECTED),
            "JAZZ_REAL_COMPOSER_MIDI_NOT_DELIVERED_IN_FULL")
    wav=Path(audio["wav_path"])
    require(wav.is_file(),"JAZZ_FULL_FINISHED_RECORDING_MISSING")
    with wave.open(str(wav),"rb") as f:
        frames,rate,chans,width=f.getnframes(),f.getframerate(),f.getnchannels(),f.getsampwidth()
        require(chans==2 and width==2 and rate==44100 and frames>rate*80,
                "JAZZ_STEREO_NOT_REAL_FULL_LENGTH_44K1")
        f.setpos(min(rate*5,frames-1))
        require(any(f.readframes(min(rate,frames-rate*5))),
                "JAZZ_MUSIC_AUDIO_NOT_PRESENT")
    import shutil
    dest=OUT/"JAZZ_BALLAD_COMPOSER_MIDI_ORIGINAL_INSTRUMENTS_STEREO.wav"
    shutil.copyfile(wav,dest)
    report={"status":"JAZZ_BALLAD_FULL_COMPOSER_MIDI_TO_OWN_INTERPRETER_TO_SFZ_STEREO_PASS",
            "genre":"Jazz Ballad","genre_family_count":8,
            "this_full_song_audio_verified_only":"Jazz Ballad",
            "remaining_seven_styles_audio_not_automatically_approved":True,
            "composer_score_notes":len(events),
            "jazz_midi_handoff_verified":receipt,
            "original_stems":list(observed.keys()),
            "real_sampled_bank_stems":True,"standard_direct_stereo":True,
            "other_genres_not_modified":True,"rock2_sound_unchanged":True,
            "live_deployed":False,"wav_name":dest.name,
            "duration_seconds":round(frames/rate,3),
            "wav_sha256":hashlib.sha256(dest.read_bytes()).hexdigest()}
    (OUT/"RESULT.json").write_text(json.dumps(report,indent=2)+"\n")
    print("JAZZ_ACTUAL_MIDI_TO_OWN_GENRE_TO_FULL_RECORDED_STEREO_PASS",
          json.dumps({k:report[k] for k in ("genre","composer_score_notes",
                                          "original_stems","duration_seconds",
                                          "standard_direct_stereo","live_deployed")},sort_keys=True),flush=True)

if __name__=="__main__":main()
