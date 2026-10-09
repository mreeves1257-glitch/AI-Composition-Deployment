"""Verify new Rock score against ORIGINAL Instrument/Target/Performance/Output code.

This is NOT a substitute renderer, mock musical engine, or SFZ sample proof.
Actual Python module sources are extracted from original composer/runtime.b64.
Live Composer, Plug, Control Panel, 3D mixer and source recordings are untouched.
"""
from __future__ import annotations
import base64
from collections import Counter
import io
import json
from pathlib import Path
import sys
import tarfile
import tempfile

PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT/"composer_overrides"))
from genre_styles.shared_interpreter_router import listed_genres
from genre_styles.source_pattern_library import compile_original_source_seed
from genre_styles.source_pattern_composer_handoff import prepare_source_pattern_composer_handoff
from genre_styles.source_pattern_resource_handoff import (
    ORIGINAL_SOURCE_PROVENANCE,load_binding_file)

RUNTIME_FILES=("instrument_program.py","target_program.py","performance_executor.py",
               "output_handoff.py","AI_Comp_Executable_Output_Core_001.py",
               "instrument_library.json","target_registry.json")
EXPECTED_ROCK={
    "electric_bass_guitar":("KARORYFER_GROWLYBASS_V1_002","growlybass_clean.sfz"),
    "electric_guitar:RHYTHM_POWER_CHORDS":
        ("KARORYFER_SHINYGUITAR","Programs/composer-electric.sfz"),
    "kick_drum_rock":("KARORYFER_BIG_RUSTY_DRUMS","Programs/composer-kick-lite.sfz"),
    "snare_drum":("KARORYFER_BIG_RUSTY_DRUMS","Programs/composer-snare-lite.sfz"),
    "hi_hat":("KARORYFER_BIG_RUSTY_DRUMS","Programs/composer-hihat-lite.sfz")
}

def insist(ok,message):
    if not ok:raise AssertionError(message)

def fixture_from_original_pins():
    return {
        binding_id:{
            "resource_id":resource,
            "preferred_mapping":sfz,
            "resource_type":"SFZ_SAMPLE_LIBRARY",
            "fallback_policy":"NO_SYNTHETIC_SUBSTITUTION",
            "library":ORIGINAL_SOURCE_PROVENANCE[resource][0],
            "license":ORIGINAL_SOURCE_PROVENANCE[resource][1]
        }
        for binding_id,(resource,sfz) in EXPECTED_ROCK.items()
    }

def install_original_runtime_into(tmp):
    raw=base64.b64decode((PROJECT/"composer"/"runtime.b64").read_bytes())
    with tarfile.open(fileobj=io.BytesIO(raw),mode="r:gz") as t:
        members=t.getmembers()
        for name in RUNTIME_FILES:
            found=[m for m in members if m.isfile() and
                   (m.name==name or m.name.endswith("/"+name))]
            insist(len(found)==1,"BASELINE_RUNTIME_MISSING_OR_DUPLICATE:"+name)
            (tmp/name).write_bytes(t.extractfile(found[0]).read())

def verify_original_runtime_contract():
    with tempfile.TemporaryDirectory() as path:
        tmp=Path(path)
        install_original_runtime_into(tmp)
        sys.path.insert(0,str(tmp))
        from instrument_program import InstrumentProgram
        from target_program import TargetProgram
        from performance_executor import PerformanceExecutor
        from output_handoff import build_execution_package
        from AI_Comp_Executable_Output_Core_001 import (
            OutputManager, RenderRequest, OutputType, write_output_package)

        original_instrument_catalog=json.loads((tmp/"instrument_library.json").read_text())
        physical_ids={x["id"] for x in original_instrument_catalog["instruments"]}
        alias={
            "electric_bass":"electric_bass_guitar",
            "lead_guitar":"electric_guitar","flute":"concert_flute",
            "clarinet":"clarinet_bb","trumpet":"trumpet_c",
            "trombone":"tenor_trombone","conga":"conga_family",
        }  # Original InstrumentProgram.resolve_events aliases, not newly guessed ones.
        unsupported=[]
        for genre in listed_genres():
            seed=compile_original_source_seed(genre)
            for r in seed["roles"]:
                if alias.get(r["instrument_id"],r["instrument_id"]) not in physical_ids:
                    unsupported.append((genre,r["role"],r["instrument_id"]))
        ids=Counter(k for _,_,k in unsupported)
        insist(len(unsupported)==66,"PHYSICAL_INSTRUMENT_GAP_COUNT_DRIFT")
        insist(len(ids)==13,"UNKNOWN_PHYSICAL_INSTRUMENT_CLASSES_DRIFT")

        seed=compile_original_source_seed("ROCK")
        stage3={"status":"PASS","palette":["electric_guitar","electric_bass","drums"]}
        refs=fixture_from_original_pins()
        result=prepare_source_pattern_composer_handoff(
            seed,original_stage3_result=stage3,target_bindings=refs,
            existing_events=[{"track_id":"ORIGINAL_LEAD","instrument_id":"electric_guitar",
                              "midi":69,"start_beat":0}])
        insist(result["status"]=="CANDIDATE_STAGE4_EVENTS_READY_SOURCE_PREFLIGHT_PENDING",
               "CANDIDATE_SOURCE_REFERENCE_NOT_READY")
        insist(result["candidate_is_not_live_events"] and
               result["audio_render_authorized"] is False and
               result["production_enabled"] is False,
               "UNVERIFIED_SCORE_ACTIVATED")
        events=result["candidate_stage4_events"]
        insist(len(events)==102,"ROCK_SEVEN_BAR_EVENT_DRIFT")
        insist(result["missing_original_rock_tracks"]==
               ["LEAD","TOMS","CRASH","RIDE"],"ROCK_LEAD_AND_FILLS_LOSS_HIDDEN")
        guitar=[e for e in events if e["track_id"]=="HARMONY"]
        insist(len(guitar)>0 and
               {e["instrument_id"] for e in guitar}=={"electric_guitar"} and
               {e["expected_target_binding_id"] for e in guitar}==
               {"electric_guitar:RHYTHM_POWER_CHORDS"},
               "INSTRUMENT_ID_CONFUSED_WITH_TARGET_BINDING_ID")
        instrument=InstrumentProgram(tmp/"instrument_library.json")
        resolved=instrument.resolve_events(events)
        insist(resolved["status"]=="PASS","REAL_INSTRUMENT_RESOLVER_REJECTED_PROPOSAL")
        insist(len(resolved["profiles"])==5,"INSTRUMENT_ROLE_COUNT_CHANGED")
        target=TargetProgram(tmp/"target_registry.json")
        target.registry["targets"]["INTERNAL"]["instrument_bindings"].update(refs)
        selected=target.resolve("INTERNAL",resolved)
        insist(selected["status"]=="PASS","REAL_TARGET_RESOLVER_REJECTED_PROPOSAL")
        tracks={r["track_id"]:(r["instrument_id"],r["resource"]) for r in selected["resolved_resources"]}
        insist(set(tracks)=={"BASS","HARMONY","KICK","SNARE","HAT"},
               "TARGET_DROPPED_OR_ADDED_INSTRUMENT")
        insist(tracks["HARMONY"][0]=="electric_guitar" and
               tracks["HARMONY"][1]["preferred_mapping"]==
                 "Programs/composer-electric.sfz",
               "REAL_TARGET_RHYTHM_SFZ_LOOKUP_WRONG")
        for e in events:
            expected=tracks[e["track_id"]]
            insist(e["instrument_id"]==expected[0] and
                   e["preferred_mapping"]==expected[1]["preferred_mapping"],
                   "TARGET_PROGRAM_DIVERGES_FROM_SOURCE_PATTERN_PROPOSAL")
        # Prove the old identifier would fail the original physical catalogue.
        bad=[{**e,"instrument_id":"electric_guitar:RHYTHM_POWER_CHORDS"}
             if e["track_id"]=="HARMONY" else e for e in events]
        insist(instrument.resolve_events(bad)["status"]=="BLOCKED",
               "HISTORICAL_GUITAR_KEY_BUG_NOT_REPRODUCIBLE")
        theory={"authority":"THEORY_ONLY","genre_name":"ROCK"}
        played=PerformanceExecutor().execute(theory,resolved,selected,events)
        insist(played["events"]==events and not played["manipulation_performed"],
               "ACTUAL_PERFORMANCE_EXECUTOR_CHANGED_UNVERIFIED_EVENTS")
        package=build_execution_package({
             "genre":"ROCK","modules":{
               "theory":{"events":events,"meter":"4/4","tempo_bpm":123,
                         "composition_fingerprint":"ROCK_IDENTITY_CONTRACT"},
               "target":selected
              }})
        insist(len(package.events)==len(events),
               "ORIGINAL_MIDI_OUTPUT_CORE_DROPPED_NOTE_EVENTS")
        insist({e.track_id for e in package.events}==
               {"BASS","HARMONY","KICK","SNARE","HAT"},
               "ORIGINAL_OUTPUT_CORE_TRACK_ISOLATION_BROKEN")
        import struct
        with tempfile.TemporaryDirectory() as midi_folder:
            written=OutputManager().execute(package,RenderRequest(
                request_id="ROCK_STAGE4_ISOLATED_REAL_MIDI",
                requested_outputs=(OutputType.MIDI,)))
            paths=write_output_package(written,Path(midi_folder))
            raw=Path(paths["MIDI"]).read_bytes()
            insist(raw[:8]==b"MThd"+bytes((0,0,0,6)),
                   "ORIGINAL_EXECUTABLE_OUTPUT_CORE_DID_NOT_WRITE_MIDI")
            fmt,count,ppq=struct.unpack(">HHH",raw[8:14])
            insist(fmt==1 and count==len(tracks)+1 and ppq==480,
                   "STAGE4_SEPARATE_REAL_MIDI_TRACKS_NOT_PRESERVED")
            insist(raw.count(b"MTrk")==count,
                   "STAGE4_MIDI_FILE_TRACK_STRUCTURE_CORRUPT")
            insist(len(raw)>1000,"STAGE4_OUTPUT_MIDI_FILE_EMPTY")
        print("ORIGINAL_STAGE4_TO_OUTPUT_CORE_CONTRACT_PASS",json.dumps({
            "proposed_note_events":len(events),
            "real_instrument_resolver":"PASS",
            "real_target_resolver":"PASS",
            "real_performance_executor":"PASS",
            "original_output_core_package":"PASS",
            "real_type1_multitrack_midi_file_written":"PASS",
            "exact_recording_bank_references":5,
            "not_approved_for_audio":True,
            "missing_original_rock_tracks":result["missing_original_rock_tracks"],
            "all_55_unknown_physical_catalog_role_occurrences":len(unsupported),
            "distinct_unknown_physical_instrument_ids":dict(sorted(ids.items()))
        },sort_keys=True))
        return True

if __name__=="__main__":
    verify_original_runtime_contract()
