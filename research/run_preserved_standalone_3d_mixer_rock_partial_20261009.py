"""Isolated last-stage 3D mixer proof using 5 authentic Rock source stems.

Actual external original standalone_3d_mixer.py runs as a subprocess; neither
the physical recorded stems nor the original composer event authority is
altered. This is an INCOMPLETE development listening reference, NOT a finished
Rock composition, published original scene, phone/Plug delivery or approval.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import subprocess
import sys
import hashlib
import tempfile
import wave
import zipfile

PROJECT=Path(__file__).resolve().parents[1]
RT=PROJECT/"composer"/"runtime"
SOURCE=PROJECT/"research_artifacts"/"rock_original_source_stems"
OUTPUT=PROJECT/"research_artifacts"/"rock_partial_stage7_staging"
sys.path.insert(0,str(RT))
from genre_styles.source_pattern_library import compile_original_source_seed
from genre_styles.source_pattern_composer_handoff import prepare_source_pattern_composer_handoff
from instrument_program import InstrumentProgram
from target_program import TargetProgram
from performance_executor import PerformanceExecutor

EXPECTED={"BASS","HARMONY","KICK","SNARE","HAT"}

def check(p,m):
    if not p:raise AssertionError(m)

def main():
    proof=json.loads((SOURCE/"PROOF_MANIFEST.json").read_text())
    check(proof["song_is_complete"] is False,"REJECT_FALSE_FULL_SONG")
    check(len(proof["individual_instrument_stems"])==5,"FIVE_STEM_AUDIO_REQUIRED")
    check(sum(x["note_count"] for x in proof["individual_instrument_stems"])==102,
          "SOURCE_NOTE_COUNT_CHANGED")
    seed=compile_original_source_seed("ROCK")
    target=TargetProgram(RT/"target_registry.json")
    instrument=InstrumentProgram(RT/"instrument_library.json")
    plan=prepare_source_pattern_composer_handoff(
        seed,original_stage3_result={"status":"PASS","palette":["electric_guitar","electric_bass","drums"]},
        target_bindings=target.registry["targets"]["INTERNAL"]["instrument_bindings"])
    check(plan["status"]=="CANDIDATE_STAGE4_EVENTS_READY_SOURCE_PREFLIGHT_PENDING" and
          plan["production_enabled"] is False and
          plan["audio_render_authorized"] is False,
          "SOURCE_SCORE_CANNOT_BE_PROMOTED_TO_LIVE_AUDIO")
    events=plan["candidate_stage4_events"]
    inst=instrument.resolve_events(events)
    check(inst["status"]=="PASS","ORIGINAL_INSTRUMENT_RESOLVER_FAILURE")
    tgt=target.resolve("INTERNAL",inst)
    check(tgt["status"]=="PASS","ORIGINAL_TARGET_SOURCE_BLOCKED")
    perf=PerformanceExecutor().execute({"authority":"THEORY_ONLY","genre_name":"ROCK"},
                                        inst,tgt,events)
    check(set(r["track_id"] for r in tgt["resolved_resources"])==EXPECTED,
          "WRONG_RECORDING_ROLES")
    stems=[]
    for row in proof["individual_instrument_stems"]:
        wav=SOURCE/row["wav_file"]
        check(wav.is_file() and hashlib.sha256(wav.read_bytes()).hexdigest()==row["wav_sha256"],
              "RECORDED_STEM_CHANGED_OR_MISSING:"+row["role"])
        stems.append({"track_id":row["role"],"instrument_id":
                      next(r["instrument_id"] for r in tgt["resolved_resources"]
                           if r["track_id"]==row["role"]),
                      "wav_path":str(wav.resolve()),
                      "note_count":row["note_count"]})
    engine={
        "genre":"ROCK",
        "modules":{
             "theory":{"events":events,"composition_fingerprint":
                       "ROCK_SEVEN_BAR_RESEARCH_5_TRACK_PARTIAL"},
             "instrument":inst,"target":tgt,"performance":perf,
        }
    }
    OUTPUT.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="rock_five_stage7_") as temp:
        path=Path(temp)
        job=path/"partial_source_research_job.json"
        job.write_text(json.dumps({"engine_result":engine,"stems":stems}))
        # This is a separate Python PROCESS invoked after completed sample
        # rendering; do not use any in-engine short-cut, fake mix or new mixer.
        p=subprocess.run([sys.executable,str(RT/"standalone_3d_mixer.py"),
                          str(job),str(OUTPUT)],capture_output=True,text=True,
                          timeout=120,check=False)
        check(p.returncode==0,
              "ORIGINAL_STANDALONE_3D_FAILED:"+p.stdout[-800:]+p.stderr[-500:])
        response=json.loads(p.stdout.strip().splitlines()[-1])
        check(response["mixer_stage"]=="STANDALONE_3D_FINAL_STAGE" and
              response["status"]=="AUDIO_RENDER_PASS",
              "ORIGINAL_3D_STAGE_DID_NOT_RETURN_AUDIO")
        mixed=Path(response["wav_path"])
        with wave.open(str(mixed),"rb") as s:
            count=s.getnframes();rate=s.getframerate();channels=s.getnchannels()
        check(channels==2 and rate==44100 and count>400000,
              "STEREO_TEST_WAVEFORM_UNREADABLE")
        check(mixed.stat().st_size>1000,"STEREO_OUTPUT_EMPTY")
        staging=OUTPUT/"ROCK_5_TRACKS_3D_STAGING_NOT_FINISHED_SONG.wav"
        staging.write_bytes(mixed.read_bytes())
        diagnostic={
          "schema":"AI_COMP_INCOMPLETE_FIVE_TRACK_ROCK_STANDALONE_3D_RESEARCH_V1",
          "only_five_original_sampled_tracks":sorted(EXPECTED),
          "missing_expected_rock_arrangement":["LEAD","TOMS","CRASH","RIDE"],
          "is_not_full_arrangement":True,
          "not_authoritative_music_master":True,
          "not_user_auditioned":True,
          "no_production_plug_or_phone_deployment":True,
          "stereo_derivative_made_by_original_separate_3d_process":True,
          "stage7_process_path":"composer/runtime/standalone_3d_mixer.py",
          "real_recorded_stems_verified":True,
          "underlying_source_role_notes":102,
          "duration_seconds":round(count/rate,3),
          "sample_rate":rate,
          "stereo_channels":2,
          "sha256":hashlib.sha256(staging.read_bytes()).hexdigest(),
          "source_stem_sha256":{r["role"]:r["wav_sha256"]
                                 for r in proof["individual_instrument_stems"]},
          "spatial_scene_path":response.get("master_path"),
        }
        (OUTPUT/"STAGE7_DIAGNOSTIC_MANIFEST.json").write_text(json.dumps(diagnostic,indent=2)+"\n")
        (OUTPUT/"README.txt").write_text(
          "Five-source partial-rock listening reference, 7 bars, not a complete song.\n"
          "Real recorded SFZ bass, rhythm guitar, kick, snare, hat.\n"
          "Processed by preserved *separate standalone stage-seven 3D mixer*.\n"
          "Lead guitar, toms, ride, crash are missing; not connected to live Plug.\n"
          "No sample bank changes, no Composer score replacement.\n"
          "Reference for evaluating tone and mix, not an artistic acceptance test.\n")
        archive=OUTPUT.parent/"ROCK_5_TRACK_STANDALONE_3D_DIAGNOSTIC_2026-10-09.zip"
        with zipfile.ZipFile(archive,"w",compression=zipfile.ZIP_DEFLATED) as z:
            for f in sorted(OUTPUT.glob("*")):
                if f.is_file():z.write(f,f.name)
        print("ORIGINAL_STANDALONE_3D_PARTIAL_ROCK_PREVIEW_PASS",json.dumps({
          "original_independent_3d_process":True,
          "real_sfizz_recorded_stems":5,
          "stereo_duration_seconds":diagnostic["duration_seconds"],
          "archive_bytes":archive.stat().st_size,
          "full_rock_music":False,
          "production_activation":False,
        }),flush=True)

if __name__=="__main__":main()
