"""Isolated 7-bar Rock genre-owned score -> ORIGINAL Composer -> genuine recorded stems.

Research audio only, not live music. Respects source handoff flag
production_enabled=False. This independent test does NOT promote a candidate
to normal composition events, publish any mix as complete Rock music or run
the standalone 3D mixer. It uses original preserved physical/target/performance
and Output Core, installed original SFZ and sample bytes, and sfizz renderer.

Requires a successful original build_current_composer.sh in GitHub Actions.
"""
from __future__ import annotations

from dataclasses import replace
from collections import Counter
from pathlib import Path
from contextlib import contextmanager
import hashlib
import json
import os
import sys
import wave
import zipfile

ROOT=Path(__file__).resolve().parents[1]
RT=ROOT/"composer"/"runtime"
OUT=ROOT/"research_artifacts"/"rock_original_source_stems"
sys.path.insert(0,str(RT))
from genre_styles.source_pattern_library import compile_original_source_seed
from genre_styles.source_pattern_composer_handoff import prepare_source_pattern_composer_handoff
from instrument_program import InstrumentProgram
from target_program import TargetProgram
from performance_executor import PerformanceExecutor
from output_handoff import build_execution_package
from AI_Comp_Executable_Output_Core_001 import MidiAdapter
from sfz_renderer_adapter import preflight,render_midi,validate_sfz_samples

EXPECTED={
    "BASS":("electric_bass_guitar","KARORYFER_GROWLYBASS_V1_002","growlybass_clean.sfz"),
    "HARMONY":("electric_guitar","KARORYFER_SHINYGUITAR","Programs/composer-electric.sfz"),
    "KICK":("kick_drum_rock","KARORYFER_BIG_RUSTY_DRUMS","Programs/composer-kick-lite.sfz"),
    "SNARE":("snare_drum","KARORYFER_BIG_RUSTY_DRUMS","Programs/composer-snare-lite.sfz"),
    "HAT":("hi_hat","KARORYFER_BIG_RUSTY_DRUMS","Programs/composer-hihat-lite.sfz"),
}
AUDIT_ONLY=True

def require(ok,code):
    if not ok:raise AssertionError(code)

def build_and_audit():
    assert AUDIT_ONLY
    OUT.mkdir(parents=True,exist_ok=True)
    renderer=ROOT/".composer_tools"/"bin"/"sfizz_render"
    bank=RT/"sound_resources"
    require(renderer.is_file(),"ORIGINAL_SFIZZ_RENDERER_MISSING")
    require(bank.is_dir(),"ORIGINAL_SFZ_BANK_NOT_INSTALLED")
    os.environ["AI_COMP_SFZ_RENDERER"]=str(renderer)
    os.environ["AI_COMP_RESOURCE_BANK"]=str(bank)
    seed=compile_original_source_seed("ROCK")
    original_pallette={"status":"PASS","palette":["electric_guitar","electric_bass","drums"]}
    registry=json.loads((RT/"target_registry.json").read_text())
    actual_bindings=registry["targets"]["INTERNAL"]["instrument_bindings"]
    proposal=prepare_source_pattern_composer_handoff(
       seed,original_stage3_result=original_pallette,
       existing_events=[{"track_id":"OLD_SCORE","instrument_id":"electric_guitar",
                         "start_beat":0,"midi":72}],target_bindings=actual_bindings)
    require(proposal["status"]=="CANDIDATE_STAGE4_EVENTS_READY_SOURCE_PREFLIGHT_PENDING",
            "GATED_ROCK_SOURCE_PROPOSAL_NOT_READY")
    require(proposal["candidate_is_not_live_events"] and
            not proposal["audio_render_authorized"] and
            not proposal["production_enabled"],
            "PROPOSAL_MUST_REMAIN_NONPRODUCTION")
    events=proposal["candidate_stage4_events"]
    require(len(events)==102,"ROCK_ORIGINAL_SEED_CHANGED")
    require(set(e["track_id"] for e in events)==set(EXPECTED),
            "ROCK_FIVE_SOURCE_PARTS_CHANGED")
    instrument=InstrumentProgram(RT/"instrument_library.json")
    physical=instrument.resolve_events(events)
    require(physical["status"]=="PASS","ORIGINAL_INSTRUMENT_STAGE_BLOCKED")
    target=TargetProgram(RT/"target_registry.json")
    resolved=target.resolve("INTERNAL",physical)
    require(resolved["status"]=="PASS","ORIGINAL_TARGET_STAGE_BLOCKED")
    PerformanceExecutor().execute(
        {"authority":"THEORY_ONLY","genre_name":"ROCK"},physical,resolved,events)
    program_by_track={r["track_id"]:r["resource"] for r in resolved["resolved_resources"]}
    require(set(program_by_track)==set(EXPECTED),"TARGET_RESOURCE_TRACK_DRIFT")
    checked={}
    for role,(instrument_id,resource_id,mapping) in EXPECTED.items():
        found=program_by_track[role]
        require(found["resource_id"]==resource_id and
                found["preferred_mapping"]==mapping,
                "TARGET_RESOURCE_SFZ_SUBSTITUTION:"+role)
        # Public sample banks are not included in Git source archive. This is
        # the first TRUE per-test installed SFZ plus recursive sample-byte check.
        ready=preflight(found)
        require(ready["status"]=="SFZ_RENDER_READY" and
                ready["sample_references"]>0,
                "ORIGINAL_SAMPLE_GRAPH_MISSING:"+role)
        checked[role]={
            "resource_id":resource_id,"preferred_mapping":mapping,
            "sample_references":ready["sample_references"],
            "unique_samples":ready["unique_samples"],
            "sfz_files_validated":ready["sfz_files_validated"],
        }
        print("SOURCE_RECORDED_SAMPLE_GRAPH_PRESENT",role,checked[role],flush=True)

    pkg=build_execution_package({
        "genre":"ROCK","modules":{
           "theory":{
                "events":events,"meter":seed["meter"],
                "tempo_bpm":seed["tempo_bpm"],
                "composition_fingerprint":"ROCK_SEVEN_BAR_RESEARCH_SOURCE_ONLY",
           },
           "target":resolved,
        },
    })
    require(len(pkg.events)==102,"ORIGINAL_OUTPUT_CORE_NOTE_LOSS")
    manifest={
       "source":"ORIGINAL_55_GENRE_AUTHORED_ROCK_SOURCE_SEED",
       "schema":"AI_COMP_ROCK_ORIGINAL_FIVE_STEM_RECORDED_AUDIO_RESEARCH_V1",
       "one_shared_interpreter_only":True,
       "baseline_hard_copy_unchanged":True,
       "original_composer_events_unchanged":True,
       "song_is_complete":False,
       "original_rock_parts_absent":["LEAD","TOMS","CRASH","RIDE"],
       "stage7_3d_final_mix_activated":False,
       "plug_or_control_panel_touched":False,
       "production_deployment_performed":False,
       "not_auditioned_for_musical_realism":True,
       "genre":"ROCK","tempo_bpm":seed["tempo_bpm"],"meter":seed["meter"],
       "note_events":len(pkg.events),
       "individual_instrument_stems":[],
       "source_recordings":{"banks":checked},
    }
    midi_adapter=MidiAdapter()
    for role in EXPECTED:
        notes=[e for e in pkg.events if e.track_id==role]
        require(len(notes)==sum(e["track_id"]==role for e in events),
                "LOST_SOURCE_ROLE_NOTES:"+role)
        p=replace(pkg,events=tuple(notes))
        midi=OUT/(role.lower()+"-recorded-source.mid")
        midi.write_bytes(midi_adapter.render(p,"ROCK_REAL_SFZ_SEVEN_BAR_SOURCE").payload)
        wav=OUT/(role.lower()+"-recorded-source.wav")
        report=render_midi(program_by_track[role],midi,wav,sample_rate=44100)
        require(report["status"]=="AUDIO_RENDER_PASS" and
                report["rms_linear"]>0 and report["peak_linear"]>0,
                "REAL_RECORDED_STEM_SILENT:"+role)
        with wave.open(str(wav),"rb") as w:
            sec=w.getnframes()/w.getframerate()
        require(sec>=8 and sec<40,"UNEXPECTED_SOURCE_SEED_AUDIO_DURATION:"+role)
        manifest["individual_instrument_stems"].append({
            "role":role,"note_count":len(notes),"sfz_source":report["sfz_path"],
            "wav_file":wav.name,"midi_file":midi.name,
            "duration_seconds":round(sec,4),"peak_dbfs":round(report["peak_dbfs"],4),
            "rms_dbfs":round(report["rms_dbfs"],4),
            "wav_sha256":hashlib.sha256(wav.read_bytes()).hexdigest(),
            "midi_sha256":hashlib.sha256(midi.read_bytes()).hexdigest(),
            "recorded_sample_graph_preflight":True,
        })
        print("ROCK_ORIGINAL_SEED_REAL_RECORDED_AUDIO_STEM_PASS",
              role,"notes",len(notes),"duration_s",round(sec,2),
              "rms_dbfs",round(report["rms_dbfs"],3),flush=True)

    (OUT/"PROOF_MANIFEST.json").write_text(json.dumps(manifest,indent=2)+"\n")
    (OUT/"README.txt").write_text(
        "ROCK: 5 seven-bar separate REAL RECORDED SOURCE instrument tracks.\n"
        "Proof of Composer note-to-SFZ recordings, NOT complete Rock music.\n"
        "No lead guitar, toms, ride, crash; no mastering, no Stage7 3D mixer.\n"
        "Do not treat an unapproved 7-bar practice score as new live music.\n"
        "Recorded samples and actual MIDI are source-authentic; no synthesis.\n"
        "Original hard copy, live Composer, Plug, and phone stay unchanged.\n")
    zip_path=OUT.parent/"ROCK_5_REAL_RECORDED_SOURCE_STEMS_2026-10-09.zip"
    with zipfile.ZipFile(zip_path,"w",compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted(OUT.iterdir()):
            z.write(p,p.name)
    require(zip_path.stat().st_size>1000,"EMPTY_AUDIO_ARCHIVE")
    print("ROCK_FIVE_SOURCE_REAL_SFZ_AUDIO_PROOF_PASS",json.dumps({
        "recording_stems":len(manifest["individual_instrument_stems"]),
        "source_sample_refs":{r:d["sample_references"] for r,d in checked.items()},
        "zip_bytes":zip_path.stat().st_size,
        "live_new_interpreter_activated":False,
        "musical_quality_verified":False,
        "standalone_mixer_active":False,
    }),flush=True)

if __name__=="__main__":
    build_and_audit()
