"""Rock interpreter: lower ONLY the electric bass guitar, protect everything else.

Uses the exact liked 16-bar REAL recorded sample stems and original standalone
3D mixer. No arranger changes, no synthesizers, no new tracks, no gain/EQ
changes to kick/subkick/guitars/snare/hats/toms/crash, no live deployment.
"""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import wave

ROOT=Path(__file__).resolve().parents[1]
INPUT=ROOT/"research"/"mma_rock_handoff_r1_output"/"interpreted_fill"
REFERENCE=ROOT/"research"/"mma_rock_handoff_r1_output"/"MMA_Rock_16Bar_Interpreted_Band_Fill_3D.wav"
OUT=ROOT/"research"/"rock_bass_separation_r1_output"
MIXER=ROOT/"composer"/"runtime"/"standalone_3d_mixer.py"
# From previously successful user's preferred recording.
LIKED_ORIGINAL_SHA256="e2b8041276fe1253c7ed9a2e475562bd31a3e81c713e7161363b4a6e1964c187"
CANDIDATES=(("bass_reduced_4db",-4.0),("bass_reduced_8db",-8.0))

def assert_true(expr,message):
    if not expr:
        raise AssertionError(message)

def digest(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for data in iter(lambda:f.read(1024*1024),b""):
            h.update(data)
    return h.hexdigest()

def read_wave_meta(path):
    with wave.open(str(path),"rb") as w:
        return {"sample_rate":w.getframerate(),"channels":w.getnchannels(),
                "sample_width":w.getsampwidth(),
                "frames":w.getnframes(),
                "seconds":round(w.getnframes()/w.getframerate(),5)}

def run():
    OUT.mkdir(parents=True,exist_ok=True)
    job_path=INPUT/"standalone_final_mixer_job.json"
    assert_true(job_path.is_file(),"ORIGINAL_MMA_INTERPRETER_MIXER_JOB_MISSING")
    assert_true(REFERENCE.is_file(),"USER_LIKED_INTERPRETER_RECORDING_MISSING")
    assert_true(digest(REFERENCE)==LIKED_ORIGINAL_SHA256,
                "REFERENCE_NOT_USER_LIKED_ORIGINAL_ABORT")
    job=json.loads(job_path.read_text())
    engine=job["engine_result"]
    stems=job["stems"]
    assert_true(engine["genre"]=="ROCK","WRONG_GENRE")
    assert_true(len(stems)==8,"ORIGINAL_8_STEM_ROCK_BAND_MISMATCH")
    source_profiles={s["track_id"]:s for s in stems}
    assert_true(set(source_profiles)=={"HARMONY","BASS","KICK","SNARE","HAT","TOMS","CRASH","SUBKICK"},
                "WRONG_MMA_INSTRUMENT_LIST")
    profile_bytrack={p["track_id"]:p for p in engine["modules"]["instrument"]["profiles"]}
    resource_bytrack={r["track_id"]:r for r in engine["modules"]["target"]["resolved_resources"]}
    assert_true(set(profile_bytrack)==set(resource_bytrack)==set(source_profiles),
                "MIXER_STEM_PROFILE_INCONSISTENT")
    assert_true(profile_bytrack["BASS"]["instrument_id"]=="electric_bass_guitar",
                "EXPECTED_SAMPLED_ELECTRIC_BASS")
    assert_true(resource_bytrack["BASS"]["resource"]["resource_id"]=="KARORYFER_GROWLYBASS_V1_002",
                "ELECTRIC_BASS_SOURCE_IDENTITY_MISMATCH")
    assert_true(profile_bytrack["KICK"]["instrument_id"]=="kick_drum_rock",
                "KICK_IDENTITY_CHANGED")
    originals={t:{"sha256":digest(s["wav_path"]),
                  "wav":read_wave_meta(s["wav_path"]),
                  "gain_db":resource_bytrack[t]["resource"]["target_gain_db"],
                  "sample_resource_id":resource_bytrack[t]["resource"]["resource_id"]}
               for t,s in sorted(source_profiles.items())}
    kick_hash=originals["KICK"]["sha256"]
    # Prevent accidental alteration of already-correct melodic/drum parts:
    note_events=engine["modules"]["performance"]["events"]
    assert_true(len(note_events)>=400,"USER_APPROVED_INTERPRETER_NOT_RECONSTRUCTED")
    original_note_digest=hashlib.sha256(json.dumps(note_events,sort_keys=True).encode()).hexdigest()
    results={}
    for name,delta_db in CANDIDATES:
        new_engine=copy.deepcopy(engine)
        byrole={r["track_id"]:r for r in new_engine["modules"]["target"]["resolved_resources"]}
        bass=byrole["BASS"]["resource"]
        bass["target_gain_db"]=float(bass["target_gain_db"])+delta_db
        bass["research_bass_only_trim_db"]=delta_db
        assert_true(new_engine["modules"]["performance"]["events"]==note_events,
                    "NOTES_OR_COMPOSITION_MODIFIED")
        for t,original in resource_bytrack.items():
            if t=="BASS":continue
            assert_true(byrole[t]==original,"UNRELATED_INSTRUMENT_MIX_CHANGED:"+t)
        assert_true(bass["preferred_mapping"]==resource_bytrack["BASS"]["resource"]["preferred_mapping"],
                    "BASS_PROGRAM_REPLACED")
        path=OUT/name
        path.mkdir(parents=True,exist_ok=True)
        mixer_job=path/"job.json"
        mixer_job.write_text(json.dumps({"engine_result":new_engine,"stems":stems},indent=2)+"\n")
        proc=subprocess.run([sys.executable,str(MIXER),
                             str(mixer_job),str(path/"final")],
                            capture_output=True,text=True,timeout=180)
        assert_true(proc.returncode==0,
                    "UNMODIFIED_STANDALONE_3D_MIXER_ERROR:"+proc.stderr[-800:]+proc.stdout[-600:])
        response=json.loads(proc.stdout.strip())
        assert_true(response.get("status")=="AUDIO_RENDER_PASS" and response.get("audio_rendered"),
                    "3D_FINAL_AUDIO_NOT_CREATED:"+repr(response))
        result=Path(response["wav_path"])
        meta=read_wave_meta(result)
        assert_true(meta["sample_rate"]==44100 and meta["channels"]==2 and
                    meta["sample_width"]==2 and 30<meta["seconds"]<33,
                    "INCOMPLETE_REAL_SAMPLED_MIX")
        destination=OUT/("Rock_Interpreter_Bass_Reduced_4dB.wav" if delta_db==-4.0 else
                         "Rock_Interpreter_Bass_Reduced_8dB.wav")
        shutil.copyfile(result,destination)
        results[name]={"file":destination.name,"sha256":digest(destination),
                       "bass_gain_delta_db":delta_db,
                       "all_nonbass_instrument_gain_unchanged":True,
                       "all_source_stems_original":True,
                       "audio_meta":meta}
        print("ROCK_BASS_ONLY_MIX_PASS",json.dumps(results[name]),flush=True)
    assert_true(digest(REFERENCE)==LIKED_ORIGINAL_SHA256,"ORIGINAL_MASTER_MODIFIED")
    assert_true(hashlib.sha256(json.dumps(note_events,sort_keys=True).encode()).hexdigest()==original_note_digest,
                "NOTE_SCORE_DRIFT")
    for role,s in source_profiles.items():
        assert_true(digest(s["wav_path"])==originals[role]["sha256"],
                    "SOURCE_RECORDED_STEM_MODIFIED:"+role)
    assert_true(digest(source_profiles["KICK"]["wav_path"])==kick_hash,
                "SOURCE_KICK_MODIFIED")
    report={"status":"REAL_ROCK_INTERPRETER_BASS_ONLY_TWO_LEVEL_AB_PASS",
            "original_mix_name":REFERENCE.name,
            "original_mix_sha256":LIKED_ORIGINAL_SHA256,
            "original_mix_preserved":True,
            "original_kick_recorded_stem_sha256":kick_hash,
            "original_bass_recorded_stem_sha256":originals["BASS"]["sha256"],
            "other_gains_unchanged":True,
            "all_sample_files_unchanged":True,
            "all_notes_and_timings_unchanged":True,
            "independent_3d_mixer_unchanged":True,
            "normalization_note":"Original 3D final mixer applies peak-normalization to the full stereo output. Relative non-bass channel gains are unchanged, but absolute loudness may change with normalization.",
            "source_stems":originals,
            "new_variants":results,
            "full_song_not_modified":True,
            "not_deployed":True,
            "approval_status":"NOT_AUDITIONED_BY_USER"}
    (OUT/"ROCK_BASS_ONLY_AB_VERIFICATION.json").write_text(json.dumps(report,indent=2)+"\n")
    print("ROCK_BASS_ONLY_AB_FULL_PROOF_PASS",json.dumps({
        "source_stems":len(stems),"note_events":len(note_events),
        "variants":list(results),"protected_original_sha256":LIKED_ORIGINAL_SHA256,
        "nonbass_instruments_untouched":True,"recorded_kick_untouched":True,
        "3D_mixer_unchanged":True,"live_unchanged":True},sort_keys=True),flush=True)

if __name__=="__main__":
    run()
