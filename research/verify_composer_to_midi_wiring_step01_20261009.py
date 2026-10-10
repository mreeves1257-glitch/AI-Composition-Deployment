"""Wiring checkpoint 01: ORIGINAL Composer -> actual Standard MIDI file.

No interpreter (shared or otherwise) executes in this step.  This consumes
the preserved original Composer's Rock event output, serializes it with the
original MIDI output core, and validates a real multitrack MIDI file.
Production, instrument banks, genre backends, and standalone 3D stay untouched.
"""
from __future__ import annotations
import base64
from collections import Counter
import importlib.util
import io
import json
from pathlib import Path
import sys
import tarfile
import tempfile

PROJECT=Path(__file__).resolve().parents[1]
ARCHIVE=PROJECT/"composer"/"runtime.b64"

def check(ok,reason):
    if not ok:
        raise AssertionError(reason)

def extract_original_runtime(dest):
    raw=base64.b64decode(ARCHIVE.read_bytes(),validate=True)
    with tarfile.open(fileobj=io.BytesIO(raw),mode="r:gz") as tar:
        for m in tar:
            if not m.isfile():
                continue
            rel=Path(m.name)
            check(not rel.is_absolute() and ".." not in rel.parts,
                  "UNSAFE_PRESERVED_RUNTIME_ARCHIVE_PATH")
            check(dest.joinpath(rel).resolve().is_relative_to(dest.resolve()),
                  "ARCHIVE_PATH_ESCAPE")
            path=dest/rel
            path.parent.mkdir(parents=True,exist_ok=True)
            with tar.extractfile(m) as source:
                path.write_bytes(source.read())
    needed=[
        "AI_Comp_Genre_Execution_Adapter_002_WORKING_2026-10-02_184019_CDT.py",
        "output_handoff.py",
        "AI_Comp_Executable_Output_Core_001.py",
    ]
    for f in needed:
        check((dest/f).is_file(),"ORIGINAL_COMPOSER_MODULE_MISSING:"+f)

def main():
    with tempfile.TemporaryDirectory(prefix="composer-midi-first-link-") as td:
        root=Path(td)
        extract_original_runtime(root)
        sys.path.insert(0,str(root))
        adapter_source=root/"AI_Comp_Genre_Execution_Adapter_002_WORKING_2026-10-02_184019_CDT.py"
        spec=importlib.util.spec_from_file_location("original_unmodified_composer_adapter",adapter_source)
        adapter=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(adapter)
        composed=adapter.GenreExecutionAdapter().resolve(
            "ROCK",mode="normal",creation_seed=0)
        check(composed.get("status")=="PASS",
              "ORIGINAL_COMPOSER_DID_NOT_GENERATE_MUSIC:"+str(composed.get("status")))
        events=composed.get("events")
        check(isinstance(events,list) and len(events)>0,
              "ORIGINAL_COMPOSER_HAS_NO_NOTE_EVENTS")
        check(all(type(e.get("midi")) is int and 0<=e["midi"]<=127 and
                  e.get("start_beat") is not None and
                  float(e.get("duration_beats",0))>0 and
                  isinstance(e.get("track_id"),str)
                  for e in events),
              "COMPOSER_EVENT_MIDI_CONTRACT_INVALID")
        from output_handoff import build_execution_package
        from AI_Comp_Executable_Output_Core_001 import (
            OutputManager,RenderRequest,OutputType,write_output_package)
        theory={
            "events":events,
            "meter":composed["meter"],
            "tempo_bpm":composed["tempo_bpm"],
            "composition_fingerprint":"ORIGINAL_COMPOSER_ROCK_TO_MIDI_FIRST_CONNECTION"
        }
        packet=build_execution_package({
            "genre":"ROCK",
            "modules":{
                "theory":theory,
                "target":{"resolved_resources":[]}
            }
        })
        check(len(packet.events)==len(events),
              "MIDI_HANDOFF_DROPPED_COMPOSER_EVENTS")
        output=OutputManager().execute(
            packet,RenderRequest(
                request_id="WIRING_STEP01_COMPOSER_MIDI_ORIGINAL",
                requested_outputs=(OutputType.MIDI,)))
        paths=write_output_package(output,root/"midi_output")
        midi_path=Path(paths["MIDI"])
        check(midi_path.is_file() and midi_path.stat().st_size>128,
              "ORIGINAL_MIDI_FILE_NOT_WRITTEN")
        import mido
        mf=mido.MidiFile(midi_path)
        check(mf.type==1 and mf.ticks_per_beat==480,
              "COMPOSER_MIDI_NOT_TYPE_1_480PPQ")
        notes=[m for t in mf.tracks for m in t if m.type=="note_on" and m.velocity>0]
        check(len(notes)==len(events),
              "SERIALIZED_MIDI_NOTES_DO_NOT_MATCH_COMPOSER")
        check(len(mf.tracks)>2,"COMPOSER_MIDI_MISSING_INSTRUMENT_TRACKS")
        track_details=[
            {"index":i,"track_names":[m.name for m in t if m.type=="track_name"],
             "note_ons":sum(m.type=="note_on" and m.velocity>0 for m in t)}
            for i,t in enumerate(mf.tracks)]
        print("STEP01_COMPOSER_TO_MIDI_PASS",json.dumps({
            "composer":"ORIGINAL_PRESERVED_RUNTIME",
            "genre":"ROCK",
            "composer_note_events":len(events),
            "midi_note_ons":len(notes),
            "midi_format":mf.type,
            "midi_tracks":len(mf.tracks),
            "midi_track_details":track_details,
            "midi_ppq":mf.ticks_per_beat,
            "composer_tempo_bpm":composed["tempo_bpm"],
            "genre_interpreter_called":False,
            "production_changed":False,
            "next_unconnected_link":"MIDI_TO_SPECIFIC_GENRE_INTERPRETER"
        },sort_keys=True))

if __name__=="__main__":
    main()
