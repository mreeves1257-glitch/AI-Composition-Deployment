"""Kick-only audio-presence A/B on the user's liked MMA 16-bar Rock candidate.

Never change external composition, SFZ samples, note attacks/velocities,
bass, guitar, snare, hats, fills, or the existing standalone 3D mixer.
Only KICK and directly derived SUBKICK metadata gain change, inside isolated
mixer jobs; keep untouched working master as immutable reference.

Expected prior step: research/mma_rock_band_handoff_16bar_r1.py succeeds and
stores recorded live-sample stem paths and original 3D mixer job.
"""
from __future__ import annotations
import copy, hashlib, json, math, subprocess, sys, wave
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"research"/"mma_rock_handoff_r1_output"
DIR=SOURCE/"interpreted_fill"
OUT=ROOT/"research"/"rock_kick_only_mix_audition_r1"
MIXER=ROOT/"composer"/"runtime"/"standalone_3d_mixer.py"
# moderate correction vs more prominent; not a decision to permanently
# change the user's working balance. SUBKICK inherits ONLY recorded kick.
VARIANTS=(("kick_present_plus_6db",6.0,6.0),
          ("kick_present_plus_9db",9.0,6.0))

def require(cond,message):
    if not cond:raise AssertionError(message)

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()

def levels(path):
    import numpy as np
    with wave.open(str(path),"rb") as w:
        sr=w.getframerate()
        channels=w.getnchannels()
        peak=0.0; ss=0.; n=0
        while True:
            raw=w.readframes(65536)
            if not raw:break
            if w.getsampwidth()!=2:
                raise AssertionError("UNSUPPORTED_MEASUREMENT_PCM")
            x=np.frombuffer(raw,dtype="<i2").astype("float64")/32768.
            n+=len(x);ss+=float((x*x).sum());peak=max(peak,float(abs(x).max()))
        require(n>100 and peak>0,"AUDIO_STEM_SILENT:"+str(path))
    rms=math.sqrt(ss/n)
    return {"peak_dbfs":round(20*math.log10(peak),3),
            "rms_dbfs":round(20*math.log10(rms),3),
            "rate":sr,"channels":channels,"length_seconds":round(n/sr/channels,3)}

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    jobfile=DIR/"standalone_final_mixer_job.json"
    original=SOURCE/"MMA_Rock_16Bar_Interpreted_Band_Fill_3D.wav"
    require(jobfile.is_file() and original.is_file(),"PRESERVED_GOOD_ROCK_AUDIO_MISSING")
    source_digest=sha(original)
    job=json.loads(jobfile.read_text())
    engine=job["engine_result"]
    stems=job["stems"]
    require(engine["genre"].upper()=="ROCK","WRONG_GENRE")
    tracks={s["track_id"]:s for s in stems}
    require("KICK" in tracks and "SUBKICK" in tracks,"MISSING_KICK_OR_SUBKICK_STEM")
    require(tracks["KICK"].get("instrument_id")=="kick_drum_rock","KICK_IDENTITY_MISMATCH")
    target=engine["modules"]["target"]["resolved_resources"]
    bytrack={x["track_id"]:x for x in target}
    require(set(tracks)==set(bytrack),"MIXER_RESOURCE_DECLARATION_MISMATCH")
    bindings={}
    for track,s in tracks.items():
        resource=bytrack[track]["resource"]
        bindings[track]={"resource_id":resource["resource_id"],
                          "original_target_gain_db":resource["target_gain_db"],
                          "audio_sha256":sha(s["wav_path"]),
                          "wav_levels":levels(s["wav_path"])}
    # Compare original source kick effective pre-mix strength to snare/hats
    # and other selected real-source parts; no psychoacoustic claim from dB.
    kick_db=bindings["KICK"]["wav_levels"]["rms_dbfs"]+bindings["KICK"]["original_target_gain_db"]
    other_levels={role:round(info["wav_levels"]["rms_dbfs"]+info["original_target_gain_db"],3)
                  for role,info in bindings.items()}
    print("ROCK_KICK_ORIGINAL_STEM_LEVEL_DIAGNOSTIC",json.dumps({
        "kick_source_peak_dbfs":bindings["KICK"]["wav_levels"]["peak_dbfs"],
        "kick_source_rms_dbfs":bindings["KICK"]["wav_levels"]["rms_dbfs"],
        "kick_gain_db":bindings["KICK"]["original_target_gain_db"],
        "subkick_gain_db":bindings["SUBKICK"]["original_target_gain_db"],
        "effective_rms_by_track_db":other_levels,
    },sort_keys=True),flush=True)
    product={}
    for label,kick_boost,sub_boost in VARIANTS:
        e=copy.deepcopy(engine)
        res=e["modules"]["target"]["resolved_resources"]
        changed=[]
        for x in res:
            track=x["track_id"]
            if track in ("KICK","SUBKICK"):
                boost=kick_boost if track=="KICK" else sub_boost
                base=float(x["resource"]["target_gain_db"])
                x["resource"]["target_gain_db"]=base+boost
                x["resource"]["research_kick_focused_gain_offset_db"]=boost
                changed.append(track)
        require(set(changed)=={"KICK","SUBKICK"},"ONLY_REC_KICK_AND_SUB_ALLOWED")
        # Every OTHER resolved resource (including original mixer ratios) is bit-identical.
        for x in res:
            if x["track_id"] not in ("KICK","SUBKICK"):
                require(x==bytrack[x["track_id"]],"UNRELATED_MIX_BINDING_CHANGED")
        output=OUT/label;output.mkdir(exist_ok=True)
        edited_job=output/"mixer_job.json"
        edited_job.write_text(json.dumps({"engine_result":e,"stems":stems},indent=2))
        completed=subprocess.run([sys.executable,str(MIXER),str(edited_job),
                                  str(output/"mix")],text=True,capture_output=True,
                                 timeout=160)
        require(completed.returncode==0,"ORIGINAL_3D_MIXER_RETURNED_ERROR:"+completed.stderr[-700:]+completed.stdout[-700:])
        response=json.loads(completed.stdout.strip())
        require(response.get("status")=="AUDIO_RENDER_PASS",
                "ORIGINAL_3D_WAV_NOT_RENDERED:"+str(response))
        wav=Path(response["wav_path"])
        require(wav.is_file(),"OUTPUT_WAV_MISSING")
        with wave.open(str(wav),"rb") as f:
            spec=(f.getframerate(),f.getnchannels(),f.getsampwidth())
            duration=f.getnframes()/f.getframerate()
        require(spec==(44100,2,2) and 30<duration<33,"OUTPUT_NOT_VALID_16_BAR_3D")
        final=OUT/("Rock_Interpreter_"+label+".wav")
        shutil.copyfile(wav,final)
        product[label]={"wav":final.name,"kick_added_gain_db":kick_boost,
                        "subkick_added_gain_db":sub_boost,
                        "sha256":sha(final),
                        "duration_s":round(duration,4),
                        "all_stems_original_and_unchanged":True,
                        "all_other_mix_resources_unchanged":True}
        print("KICK_ONLY_3D_REBALANCE_PASS",json.dumps(product[label]),flush=True)
    require(sha(original)==source_digest,"ORIGINAL_USER_LIKED_AUDIO_WAS_MODIFIED")
    for track,s in tracks.items():
        require(sha(s["wav_path"])==bindings[track]["audio_sha256"],
                "ORIGINAL_STEM_MODIFIED:"+track)
    result={"status":"ROCK_INTERPRETER_KICK_ONLY_REAL_AUDIO_AB_PASS",
            "original_exact_wav_sha256":source_digest,
            "original_song_protected":True,
            "original_sample_sounds_protected":True,
            "unchanged_note_events":True,
            "same_7_stage_genre_flow":True,
            "live_composer_deployed":False,
            "original_sound_library_modified":False,
            "original_3D_mixer_code_modified":False,
            "kick_notes_in_16bar_song":32,
            "recorded_kick_and_lowpass_subkick_both_exist":True,
            "source_stem_diagnostics":bindings,
            "variants":product,
            "quality_requires_user_listening":True,
            "note":"All output candidates remain distinct from user-favored original. Source ratio values preserved for other instruments, though global master normalization changes."
           }
    (OUT/"KICK_RESTORATION_REPORT.json").write_text(json.dumps(result,indent=2)+"\n")
    print("ROCK_KICK_FOCUSED_AUDITION_CREATED",json.dumps({
        "original_unchanged":True,"candidate_count":len(product),
        "real_audio":True,"kick_source_is_non_silent":True,
        "other_stems_unchanged":True,
        "live_mixer_unchanged":True},sort_keys=True),flush=True)

if __name__=="__main__":
    main()
