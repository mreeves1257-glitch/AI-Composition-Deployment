"""End-to-end isolated Step01 -> Step02: original Composer MIDI into Rock ONLY.

The exact original Composer/MIDI writer is exercised again; its written Type 1
MIDI is then *read* by Rock's own input module. No other interpreter,
recording bank, 3D mixer, production URL, or other genre is touched.
"""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT/"research"))
sys.path.insert(0,str(PROJECT/"composer_overrides"))
from verify_composer_to_midi_wiring_step01_20261009 import extract_original_runtime,check
from genre_styles.Rock.rock_midi_interpreter import (
    receive_composer_midi,RockMidiHandoffError)

def make_original_composer_midi(root):
    extract_original_runtime(root)
    sys.path.insert(0,str(root))
    original=root/"AI_Comp_Genre_Execution_Adapter_002_WORKING_2026-10-02_184019_CDT.py"
    spec=importlib.util.spec_from_file_location("real_original_rock_composer",original)
    adapter=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter)
    result=adapter.GenreExecutionAdapter().resolve("ROCK",mode="normal",creation_seed=0)
    check(result["status"]=="PASS","COMPOSER_ORIGINAL_ROCK_NOT_READY")
    from output_handoff import build_execution_package
    from AI_Comp_Executable_Output_Core_001 import (
        OutputManager,RenderRequest,OutputType,write_output_package)
    packet=build_execution_package({
        "genre":"ROCK","modules":{
            "theory":{
                "events":result["events"],
                "meter":result["meter"],
                "tempo_bpm":result["tempo_bpm"],
                "composition_fingerprint":"ROCK_ORIGINAL_MIDI_TO_OWN_GENRE_INTERPRETER"
            },
            "target":{"resolved_resources":[]}
        }
    })
    check(len(packet.events)==len(result["events"]),
          "COMPOSER_SCORE_NOT_PRESERVED_BEFORE_GENRE_RECEIVER")
    output=OutputManager().execute(packet,RenderRequest(
        request_id="WIRING_STEP02_ROCK_ONLY",requested_outputs=(OutputType.MIDI,)))
    paths=write_output_package(output,root/"original_composer_midi")
    return result,Path(paths["MIDI"])

def main():
    with tempfile.TemporaryDirectory(prefix="midi-into-rock-interpreter-") as folder:
        root=Path(folder)
        original,source=make_original_composer_midi(root)
        before=source.read_bytes()
        handoff=receive_composer_midi(source,genre="ROCK")
        check(handoff["status"]=="ROCK_OWN_INTERPRETER_RECEIVED_COMPOSER_MIDI",
              "ROCK_SPECIFIC_MIDI_RECEIVER_NOT_CALLED")
        check(handoff["note_on_count"]==len(original["events"]),
              "COMPOSER_TO_ROCK_MIDI_NOTE_LOSS")
        check(source.read_bytes()==before,"COMPOSER_MIDI_MUTATED_BY_ROCK")
        original_tracks={e["track_id"] for e in original["events"]}
        received={e["track_id"] for e in handoff["received_rock_roles"]}
        check(received==original_tracks,"ROCK_TRACKS_LOST_OR_SUBSTITUTED")
        check(handoff["inbound_original_notes_unchanged"] is True
              and handoff["production_enabled"] is False
              and handoff["instrument_renderer_connected"] is False,
              "NO_PREMATURE_RENDER_OR_PRODUCTION_ALLOWED")
        expected={
            "BASS":("electric_bass_guitar","KARORYFER_GROWLYBASS_V1_002"),
            "HARMONY":("electric_guitar","KARORYFER_SHINYGUITAR"),
            "LEAD":("electric_guitar","KARORYFER_SHINYGUITAR"),
            "KICK":("kick_drum_rock","KARORYFER_BIG_RUSTY_DRUMS"),
            "SNARE":("snare_drum","KARORYFER_BIG_RUSTY_DRUMS"),
            "HAT":("hi_hat","KARORYFER_BIG_RUSTY_DRUMS"),
        }
        check(received==set(expected),"UNEXPECTED_ORIGINAL_ROCK_MIDI_TRACKS")
        for role in handoff["received_rock_roles"]:
            check((role["instrument_id"],role["resource_id"])==expected[role["track_id"]],
                  "INCORRECT_ORIGINAL_RECORDED_INSTRUMENT:"+role["track_id"])
        # Reject MIDI that belongs to another genre: NO general shared interpreter.
        try:
            receive_composer_midi(source,genre="Jazz Ballad")
        except RockMidiHandoffError as e:
            check(str(e)=="NOT_THE_ROCK_GENRE_INTERPRETER",
                  "BAD_OTHER_GENRE_BLOCK_REASON")
        else:
            raise AssertionError("CROSS_GENRE_MIDI_INCORRECTLY_ACCEPTED")

        # Make an independent temporary copy with a wrongly named instrument.
        # The original Composer file must remain byte-for-byte untouched.
        import mido
        changed=root/"unknown_instrument_reject.mid"
        mf=mido.MidiFile(source)
        named=[m for t in mf.tracks for m in t if m.type=="track_name"]
        check(any(m.name=="BASS" for m in named),"ORIGINAL_BASS_TRACK_MISSING")
        next(m for m in named if m.name=="BASS").name="PIANO"
        mf.save(changed)
        try:
            receive_composer_midi(changed)
        except RockMidiHandoffError as e:
            check("MIDI_TRACK_NOT_SUPPORTED_BY_ROCK" in str(e),
                  "UNKNOWN_INSTRUMENT_FAILED_FOR_WRONG_REASON")
        else:
            raise AssertionError("UNKNOWN_MIDI_ROLE_SILENTLY_ACCEPTED")
        print("STEP02_MIDI_TO_INDIVIDUAL_ROCK_INTERPRETER_PASS",json.dumps({
            "original_composer_events":len(original["events"]),
            "rock_notes_received":handoff["note_on_count"],
            "midi_track_count":handoff["original_midi_track_count"],
            "rock_instrument_roles":[r["track_id"] for r in handoff["received_rock_roles"]],
            "unplayed_optional_rock_roles":handoff["unwritten_rock_roles"],
            "original_midi_sha256":handoff["source_midi_sha256"],
            "specific_interpreter":handoff["specific_genre_interpreter"],
            "other_genre_blocked":True,
            "unknown_instrument_blocked":True,
            "original_midi_unchanged":True,
            "original_recording_resources_unchanged":True,
            "next_unconnected_link":"ROCK_INTERPRETER_TO_ORIGINAL_INSTRUMENT_RENDERER",
            "live_deployed":False
        },sort_keys=True))

if __name__=="__main__":
    main()
