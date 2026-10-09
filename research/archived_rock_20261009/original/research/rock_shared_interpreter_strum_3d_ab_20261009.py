"""Render A/B from pinned MMA Rock via real shared 55-genre interpreter/real Karoryfer recorded sounds.

Only change the rhythm guitar's coordinated attack spacing; keep the user's
saved original score, the preferred research-only -8dB bass, seven other
recorded stem channels, and independent final 3D mixer unchanged.
"""
from __future__ import annotations
import collections
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import wave

ROOT=Path(__file__).resolve().parents[1]
RUNTIME=ROOT/"composer"/"runtime"
OUT=ROOT/"research"/"shared_rock_strum_audio_r1"
sys.path.insert(0,str(ROOT/"composer_overrides"))
sys.path.insert(0,str(RUNTIME))
from genre_styles.shared_interpreter_router import compile_selected_musical_interpreter
from genre_styles.Rock.rock_strum_phrase_performance import apply_guitar_attack_strum

PROTECTED_REFERENCE_SHA="e2b8041276fe1253c7ed9a2e475562bd31a3e81c713e7161363b4a6e1964c187"
PROTECTED_MINUS8_SHA="7cbc7f8eef52dbc48b3e7ba15612d46c62f2e67bc6f719d059c561fe46950393"

def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def expect(ok,msg):
    if not ok:raise AssertionError(msg)

def load_original_renderer():
    spec=importlib.util.spec_from_file_location("rock_original_sfizz_bridge",ROOT/"research"/"mma_rock_band_handoff_16bar_r1.py")
    obj=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj

def preferred_minus8(jobpath, outdir):
    original=json.loads(Path(jobpath).read_text())
    expect(len(original["stems"])==8,"NOT_EIGHT_REAL_RECORDED_STEMS")
    copyjob=copy.deepcopy(original)
    gains={x["track_id"]:x["resource"] for x in copyjob["engine_result"]["modules"]["target"]["resolved_resources"]}
    before=copy.deepcopy(gains)
    expect(gains["BASS"]["resource_id"]=="KARORYFER_GROWLYBASS_V1_002","NOT_ORIGINAL_GROWLYBASS")
    gains["BASS"]["target_gain_db"]=float(gains["BASS"]["target_gain_db"])-8.0
    for track in gains:
        if track!="BASS":expect(gains[track]==before[track],"OTHER_MIX_GAIN_CHANGED_"+track)
    outdir.mkdir(parents=True,exist_ok=True)
    job=outdir/"only_bass_reduced_8db_original_mixer_job.json"
    job.write_text(json.dumps(copyjob,indent=2)+"\n")
    proc=subprocess.run([sys.executable,str(RUNTIME/"standalone_3d_mixer.py"),str(job),str(outdir/"stereo")],capture_output=True,text=True,timeout=200)
    expect(proc.returncode==0,"EXISTING_STANDALONE_3D_MIXER_ERROR:"+proc.stderr[-1100:])
    result=json.loads(proc.stdout.strip())
    expect(result.get("status")=="AUDIO_RENDER_PASS" and result.get("audio_rendered"),"NO_REAL_STEREO")
    wav=Path(result["wav_path"])
    expect(wav.is_file(),"FINISHED_AUDIO_MISSING")
    return wav

def parts(sc):
    d=collections.defaultdict(list)
    for x in sc["notes"]:d[x["track_id"]].append(x)
    for v in d.values():v.sort(key=lambda n:(n["start_beat"],n["midi"]))
    return dict(d)

def render_version(bridge,sc,name):
    bridge.OUT=OUT/name
    report=bridge.render(parts(sc),"interpreted_fill")
    raw=bridge.OUT/"MMA_Rock_16Bar_Interpreted_Band_Fill_3D.wav"
    mixjob=bridge.OUT/"interpreted_fill"/"standalone_final_mixer_job.json"
    stereo=preferred_minus8(mixjob,bridge.OUT/"PREFERRED_BASS_MINUS8")
    dst=OUT/(name+"_BassMinus8_Original3D.wav")
    shutil.copyfile(stereo,dst)
    return {"raw_original_mix_sha256":digest(raw),"preferred_minus8_wav_sha256":digest(dst),
            "wav_path":str(dst),"report":report,
            "by_track":{p.stem.upper():digest(p) for p in (bridge.OUT/"interpreted_fill").glob("*.wav") if p.stem.upper() in ("HARMONY","BASS","KICK","SNARE","HAT","TOMS","CRASH")},
            "job":str(mixjob)}

def main():
    source=ROOT/"research"/"pinned_input"/"MMA_Rock_16Bar_Two_Sections.mid"
    expect(source.is_file(),"EXACT_OCT8_MMA_SCORE_NOT_AVAILABLE")
    bridge=load_original_renderer()
    stage3={"status":"PASS","palette":["electric_guitar","electric_bass","drums"],"meter":"4/4","tempo_bpm":145}
    original=compile_selected_musical_interpreter("ROCK",original_mma_midi_path=source,original_stage3_result=stage3)
    candidate,change=apply_guitar_attack_strum(original)
    assert len(original["notes"])==len(candidate["notes"])==420
    unchanged=lambda obj:sorted([n for n in obj["notes"] if n["track_id"]!="HARMONY"],key=lambda e:(e["track_id"],e["start_beat"],e["midi"]))
    expect(unchanged(original)==unchanged(candidate),"ANOTHER_INSTRUMENT_WAS_CHANGED")
    baseline=render_version(bridge,original,"REFERENCE_20261008_UNCHANGED")
    expect(baseline["raw_original_mix_sha256"]==PROTECTED_REFERENCE_SHA,
           "USER_APPROVED_ORIGINAL_MMA_AUDIO_DID_NOT_REPRODUCE:"+baseline["raw_original_mix_sha256"])
    expect(baseline["preferred_minus8_wav_sha256"]==PROTECTED_MINUS8_SHA,
           "USER_PREFERRED_MINUS8_ROCK_AUDIO_DID_NOT_REPRODUCE:"+baseline["preferred_minus8_wav_sha256"])
    change_audio=render_version(bridge,candidate,"GUITAR_ATTACK_STRUM_ONLY")
    expect(change_audio["raw_original_mix_sha256"]!=PROTECTED_REFERENCE_SHA,"GUITAR_PERFORMANCE_MAKES_NO_AUDIO_DIFFERENCE")
    expect(change_audio["preferred_minus8_wav_sha256"]!=PROTECTED_MINUS8_SHA,"GUITAR_8DB_A_B_WAS_IDENTICAL")
    for track in ("BASS","KICK","SNARE","HAT","TOMS","CRASH"):
        expect(baseline["by_track"][track]==change_audio["by_track"][track],"ORIGINAL_STEM_DRIFT_"+track)
    with wave.open(str(OUT/"GUITAR_ATTACK_STRUM_ONLY_BassMinus8_Original3D.wav"),"rb") as w:
        duration=round(w.getnframes()/w.getframerate(),3)
        expect(w.getnchannels()==2 and w.getframerate()==44100 and 29<duration<34,"BAD_NEW_AUDIO")
    result={"status":"SINGLE_VARIABLE_STRUM_ON_ORIGINAL_ROCK_PINNED_MMA_AUDIO_PASS",
            "original_mma_sha256":digest(source),"original_interpreted_sha256":PROTECTED_REFERENCE_SHA,
            "user_preferred_minus8_sha256":PROTECTED_MINUS8_SHA,"unchanged_original_master_verified":True,
            "new_candidate_sha256":change_audio["preferred_minus8_wav_sha256"],"original_420_note_pitches_and_velocities_unchanged":True,
            "all_six_non_guitar_recorded_stems_identical":True,"one_standalone_3d_mixer_unchanged":True,
            "bass_at_provisional_preferred_minus8_db":True,"source_sfzs_unchanged":True,"live_not_deployed":True,
            "musical_quality_requires_user_listening":True,"audition_duration_seconds":duration,
            "guitar_performance_change":change,
            "reference_audio_name":"REFERENCE_20261008_UNCHANGED_BassMinus8_Original3D.wav",
            "candidate_audio_name":"GUITAR_ATTACK_STRUM_ONLY_BassMinus8_Original3D.wav"}
    (OUT/"PROOF_AND_STRUM_AB_REPORT.json").write_text(json.dumps(result,indent=2)+"\n")
    print("PINNED_ROCK_SHARED_INTERPRETER_ORIGINAL_MIX_REPRODUCED",PROTECTED_REFERENCE_SHA,flush=True)
    print("PINNED_ROCK_SHARED_INTERPRETER_USER_MINUS8_WAV_REPRODUCED",PROTECTED_MINUS8_SHA,flush=True)
    print("SHARED_INTERPRETER_GUITAR_ATTACK_ONLY_REAL_AUDIO_AB_PASS",json.dumps({k:v for k,v in result.items() if k!="guitar_performance_change"},sort_keys=True),flush=True)

if __name__=="__main__": main()
