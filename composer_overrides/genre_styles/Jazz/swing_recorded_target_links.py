"""Activate exact original recorded Swing target bindings in ISOLATED audition.

Uses existing approved Jazz Ballad double bass and piano, project-verified
recorded Big Rusty kick/snare/ride, and new pinned unmodified VSCO trumpet.
No gain/mix/attack/decay or recorded source edits, no Rock/Jazz Ballad changes.
The original swing instrument table calls its timekeeper HAT but instruments
resolve that role to ride_cymbal. The note stays MIDI 42; a SEPARATE Swing SFZ
triggers the original ride cymbal sample with that unchanged note.
"""
from __future__ import annotations
from copy import deepcopy
from pathlib import Path
import json
import os
import tempfile

from . import swing_recorded_trumpet as trumpet

ROOT=Path(__file__).resolve().parents[2]
BANK=ROOT/"sound_resources"
TARGET=ROOT/"target_registry.json"
SOURCE=Path(__file__).resolve().with_name("profile.json")
RID="KARORYFER_BIG_RUSTY_DRUMS"
RIDE_SOURCE="Programs/composer-ride-lite.sfz"
RIDE_SWING="Programs/composer-swing-ride-note42.sfz"

def need(condition,why):
    if not condition:raise RuntimeError("SWING_SOURCE_CONNECTION:"+why)

def install_original_ride_alias():
    source=BANK/RID/RIDE_SOURCE
    need(source.is_file(),"MISSING_ORIGINAL_RIDE_SFZ")
    raw=source.read_text(encoding="utf-8")
    from_="<global> key=51 "
    need(raw.count(from_)==1,"ORIGINAL_RIDE_TRIGGER_AMBIGUOUS")
    # This is not altering a sample or global percussion behavior. It is a
    # genre-only MIDI key crosswalk: original Swing HAT (note42) -> ride WAV.
    mapped=raw.replace(from_,"<global> key=42 ",1)
    dest=BANK/RID/RIDE_SWING
    need(not dest.exists() or dest.read_text()==mapped,
         "EXISTING_SOURCE_MAPPING_WOULD_BE_REPLACED")
    dest.write_text(mapped)
    return dest

def source_binding(source, mapping, *, library=None, license=None):
    copy=deepcopy(source)
    copy["preferred_mapping"]=mapping
    if library is not None:copy["library"]=library
    if license is not None:copy["license"]=license
    return copy

def install():
    from sfz_renderer_adapter import validate_sfz_samples,render_midi
    from production_resource_policy import require_recorded_sample_resource
    from target_program import TargetProgram
    from instrument_program import InstrumentProgram
    registry=json.loads(TARGET.read_text())
    bindings=registry["targets"]["INTERNAL"]["instrument_bindings"]
    name="Swing"
    p=json.loads(SOURCE.read_text())["profiles"][name]
    actual=[x["track_id"] for x in p["individual_instrument_tracks"]]
    need(actual==["DOUBLE_BASS","ELECTRIC_PIANO","TRUMPET","KICK","SNARE","HAT"],
         "AUTHORITATIVE_SWING_INSTRUMENT_ROLES_CHANGED")
    expected={
        "double_bass":("JAZZ_MEATBASS_PINNED","Programs/jazz-pizzicato.sfz"),
        "electric_piano":("GREG_SULLIVAN_E_PIANOS","Wurlitzer EP200/composer-wurlitzer.sfz"),
        "kick_drum_rock":(RID,"Programs/composer-kick-lite.sfz"),
        "snare_drum":(RID,"Programs/composer-snare-lite.sfz"),
        "ride_cymbal":(RID,RIDE_SOURCE),
    }
    for instrument,(resource,path) in expected.items():
        c=bindings.get(instrument)
        need(isinstance(c,dict) and c.get("resource_id")==resource
             and c.get("preferred_mapping")==path,
             "ORIGINAL_INSTRUMENT_BANK_CHANGED:"+instrument)
        require_recorded_sample_resource(c)
        need((BANK/resource/path).is_file(),
             "ORIGINAL_SAMPLE_PROGRAM_NOT_INSTALLED:"+instrument)
    # Source-sample graph and note-zone recording verification already proved
    # by trumpet.preflight(), against all 10 native upstream WAV recordings.
    need((BANK/trumpet.BANK_ID/trumpet.SFZ).is_file(),
         "RECORDED_TRUMPET_NOT_PREFLIGHTED")
    native_trumpet={
        "resource_id":trumpet.BANK_ID,
        "resource_type":"SFZ_SAMPLE_LIBRARY",
        "preferred_mapping":trumpet.SFZ,
        "library":"VSCO 2 Community Edition / original trumpet",
        "license":"CC0-1.0",
        "renderer_requirement":"SFZ_COMPATIBLE_SAMPLE_RENDERER",
        "fallback_policy":"NO_SYNTHETIC_SUBSTITUTION",
        "target_gain_db":-6.0,
        "attribution":"Versilian Studios CC0 / VSCO2 Community Edition",
    }
    require_recorded_sample_resource(native_trumpet)
    install_original_ride_alias()
    original_ride=bindings["ride_cymbal"]
    swing_ride=source_binding(original_ride,RIDE_SWING)
    verify=[
        ("trumpet_c:trumpet",native_trumpet,10),
        ("ride_cymbal:drums_ride",swing_ride,12),
        ("kick_drum_rock:drums_ride",bindings["kick_drum_rock"],16),
        ("snare_drum:drums_ride",bindings["snare_drum"],16)
    ]
    staged=deepcopy(registry)
    candidates=staged["targets"]["INTERNAL"]["instrument_bindings"]
    for key,data,regions in verify:
        require_recorded_sample_resource(data)
        previous=candidates.get(key)
        need(previous is None or previous==data,
             "WOULD_OVERWRITE_EXISTING_OR_OTHER_GENRE_BINDING:"+key)
        report=validate_sfz_samples(BANK/data["resource_id"]/data["preferred_mapping"])
        need(report["sample_references"]==regions,
             "REAL_ORIGINAL_SAMPLE_GRAPH_MISSING:"+key+":"+str(report.get("sample_references")))
        candidates[key]=deepcopy(data)
    # Underlying original Swing normal-mode instrument behavior must resolve
    # all separate parts before target data is permitted to be updated.
    import importlib.util
    a=ROOT/"AI_Comp_Genre_Execution_Adapter_002_WORKING_2026-10-02_184019_CDT.py"
    spec=importlib.util.spec_from_file_location("swing_original_adapter_source",a)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    score=module.GenreExecutionAdapter().resolve("Swing",mode="normal",creation_seed=20261010)
    need(score["status"]=="PASS","SWING_MUSIC_NOT_CREATED")
    events=score["events"]
    ids={e["instrument_id"] for e in events}
    need(ids=={"double_bass","electric_piano","trumpet","drums_ride"},
         "SWING_ACTUAL_COMPOSER_INSTRUMENT_IDENTITY_CHANGED:"+str(ids))
    trumpet_notes=[e["midi"] for e in events if e["instrument_id"]=="trumpet"]
    need(trumpet_notes and min(trumpet_notes)>=60 and max(trumpet_notes)<=83,
         "SWING_MIDI_OUTSIDE_GENUINE_TRUMPET_SAMPLE_RANGE:"+repr((min(trumpet_notes),max(trumpet_notes))))
    parts=InstrumentProgram(ROOT/"instrument_library.json").resolve_events(events)
    need(parts["status"]=="PASS","SWING_INSTRUMENT_PROGRAM_NOT_RESOLVED")
    exact={x["track_id"]:x["instrument_id"] for x in parts["source_requests"]}
    need(exact=={"BASS":"double_bass","HARMONY":"electric_piano",
                "LEAD":"trumpet_c","KICK":"kick_drum_rock",
                "SNARE":"snare_drum","HAT":"ride_cymbal"},
         "SWING_ORIGINAL_RESOLVER_ROLE_DRIFT:"+str(exact))
    target=TargetProgram(TARGET)
    target.registry=staged
    stage=target.resolve("INTERNAL",parts)
    need(stage["status"]=="PASS","SWING_SFZ_TARGET_ROUTING_FAILED:"+repr(stage.get("missing")))
    matched={row["track_id"]:row["resource"] for row in stage["resolved_resources"]}
    need(set(matched)==set(exact),"SWING_SIX_PARTS_NOT_BOUND")
    need(matched["LEAD"]["resource_id"]==trumpet.BANK_ID
         and matched["HAT"]["preferred_mapping"]==RIDE_SWING
         and matched["BASS"]["resource_id"]=="JAZZ_MEATBASS_PINNED",
         "SWING_WRONG_JAZZ_VOICES")
    # Three drum instrument ids and Swing-only trumpet must not be used by
    # Jazz Ballad. Add only distinct context-qualified keys + trumpet_c.
    for k in bindings:
        if k not in ("trumpet_c:trumpet","ride_cymbal:drums_ride",
                     "kick_drum_rock:drums_ride","snare_drum:drums_ride"):
            need(bindings[k]==candidates[k],"SOME_OTHER_GENRE_SETTING_CHANGED:"+k)
    TARGET.write_text(json.dumps(staged,indent=2)+"\n")
    report={"status":"SWING_6_ORIGINAL_RECORDED_SOURCE_TARGETS_CONNECTED",
            "source":"ORIGINAL_SFZ_AND_NEW_PINNED_VSCO_TRUMPET",
            "swing_own_full_music_events":len(events),
            "six_independent_original_roles":sorted(exact),
            "genre_ride_midi_42_maps_to_original_ride_recording":True,
            "swing_trumpet_note_range":[min(trumpet_notes),max(trumpet_notes)],
            "recorded_target_resources":{k:{"resource_id":v["resource_id"],
                "mapping":v["preferred_mapping"]} for k,v in matched.items()},
            "original_genres_and_mixes_unchanged":True,
            "no_manufacturer_or_synthetic_fallback":True,
            "live_production_deployed":False}
    dest=ROOT/"output"/"swing_original_sample_target_links.json"
    dest.parent.mkdir(exist_ok=True)
    dest.write_text(json.dumps(report,indent=2)+"\n")
    print("SWING_SIX_SEPARATE_REAL_RECORDED_TARGETS_PASS",
          json.dumps(report,sort_keys=True),flush=True)
    return report

if __name__=="__main__":
    install()
