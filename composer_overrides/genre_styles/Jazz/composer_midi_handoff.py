"""Jazz family's strict, real Composer-MIDI gate before the original SFZ renderer.

All eight Jazz styles share transport/writer machinery; their musical decisions
and instrument assignments are always read from EACH original genre profile.
Never feed short symbolic source-preview scores into an audio render.
Never silently substitute Rock parts or General MIDI soundfonts.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ..genre_owned_midi_inlet import receive_genre_midi
from ..shared_interpreter_router import InterpreterConnectionError

JAZZ_GENRES=("Swing","Jazz Ballad","Big Band","Jazz Waltz",
             "Bebop","Cool Jazz","Dixieland","Jazz Fusion")


def jazz_midi_to_original_renderer_gate(*, engine_result:dict,
                                        execution_package,
                                        output_root:str|Path)->dict:
    """WRITE the original Composer's real score to MIDI, then route to Jazz.

    This runs *before* `execute_audio_render` calls the existing SFZ renderer.
    It is one additional code-level guard at the existing MIDI->Jazz boundary,
    not a new synthesis engine or a shared musical genre.
    """
    genre=engine_result.get("genre")
    if genre not in JAZZ_GENRES:
        raise InterpreterConnectionError("NOT_AN_EXISTING_JAZZ_GENRE")
    stage4=(engine_result.get("modules") or {}).get("theory") or {}
    events=stage4.get("events")
    if not isinstance(events,list) or not events:
        raise InterpreterConnectionError("JAZZ_COMPOSER_NO_REAL_STAGE4_NOTES")
    # Existing Original Output Core serializes actual accepted Composer events;
    # do not write a second hand-crafted pseudo MIDI score here.
    from AI_Comp_Executable_Output_Core_001 import (
        OutputManager, RenderRequest, OutputType, write_output_package)
    output_dir=Path(output_root).resolve()
    output_dir.mkdir(parents=True,exist_ok=True)
    issued=OutputManager().execute(
        execution_package,
        RenderRequest(request_id="JAZZ_MIDI_BEFORE_ORIGINAL_SFZ",
                      requested_outputs=(OutputType.MIDI,)),
    )
    paths=write_output_package(issued,output_dir)
    midi_path=Path(paths["MIDI"])
    source_before=hashlib.sha256(midi_path.read_bytes()).hexdigest()
    receipt=receive_genre_midi(
        midi_path,selected_genre=genre,
        composer_genre=genre,source_kind="COMPOSER")
    if receipt["status"]!="GENRE_SPECIFIC_MIDI_ARRIVED_AT_CORRECT_INTERPRETER_SLOT":
        raise InterpreterConnectionError("JAZZ_OWN_INTERPRETER_NEVER_RECEIVED_REAL_MIDI")
    if not receipt["original_source_midi_byte_identical"] or (
            receipt["actual_midi_sha256"]!=source_before):
        raise InterpreterConnectionError("JAZZ_ORIGINAL_COMPOSER_MIDI_CHANGED")
    if receipt["notes_received"]!=len(events):
        raise InterpreterConnectionError("JAZZ_ORIGINAL_COMPOSER_NOTE_LOSS")
    expected_tracks={str(x["track_id"]) for x in events}
    observed_tracks={x["track_id"] for x in receipt["individual_instrument_tracks"]}
    if observed_tracks!=expected_tracks:
        raise InterpreterConnectionError("JAZZ_COMPOSER_TO_MIDI_TRACK_LOSS")
    # Jazz Ballad already has individually pinned, real SFZ samples. Other
    # seven Jazz styles are NOT automatically certified to have complete
    # source audio just because they passed this one MIDI gate.
    proof={
        "status":"JAZZ_COMPOSER_MIDI_TO_OWN_GENRE_SLOT_PASS",
        "genre":genre,
        "original_composer_midi":str(midi_path),
        "original_midi_sha256":source_before,
        "notes_received":receipt["notes_received"],
        "roles_received":sorted(observed_tracks),
        "jazz_family_only":True,
        "actual_original_score_not_seven_bar_seed":True,
        "original_renderer_not_replaced":True,
        "live_activated":False,
        "instrument_audio_verified_by_this_gate":False,
        "genre_musical_rearrangement_performed_here":False,
        "next_stage":"ORIGINAL_SFZ_INSTRUMENT_STEMS",
    }
    (output_dir/"JAZZ_MIDI_HANDOFF_RECEIPT.json").write_text(
        json.dumps(proof,indent=2)+"\n")
    return proof
