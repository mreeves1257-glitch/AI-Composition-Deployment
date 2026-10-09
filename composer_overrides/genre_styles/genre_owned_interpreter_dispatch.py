"""Strict genre-owned Stage-3->4 musical interpretation dispatcher (non-live).

Unlike prior generic musical router, the selected genre determines the actual
EXECUTABLE musical decision backend. Existing shared MIDI/SFZ/3D tech stays
shared; no stage 8 and no fallback to Rock, generic drums, or fake instruments.
Only explicitly implemented individual genre backends accept MIDI research
inputs. This module DOES NOT replace original Composer theory['events'].
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from .external_style_midi_reader import StyleMidiInterfaceError,require

ROOT=Path(__file__).resolve().parent

def dispatch_stage3_to4_genre_owned(genre: str, *, source_midi_path: str|Path,
                                    original_stage3_result: dict[str,Any]) -> dict:
    config=json.loads((ROOT/"GENRE_INTERPRETER_REGISTRY_R1.json").read_text())
    entries=config["per_genre"]
    require(isinstance(genre,str) and genre in entries,
            "UNKNOWN_GENRE_NO_GENERIC_FALLBACK")
    entry=entries[genre]
    slot=json.loads((ROOT.parent.parent.parent/entry["slot_file"]).read_text())
    require(slot["genre_name"]==genre and
            slot["source_profile_id"]==entry["profile_id"],
            "GENRE_PROFILE_SOURCE_AUTHORITY_CHANGED")
    require(slot["activated_in_live_composer"] is False and
            slot["source_specific_note_score_approved_for_production"] is False,
            "UNAPPROVED_INTERPRETER_EXECUTION_IN_LIVE_COMPOSER")
    stage3=original_stage3_result
    require(isinstance(stage3,dict) and stage3.get("status")=="PASS" and
            isinstance(stage3.get("palette"),list) and stage3["palette"],
            "ORIGINAL_STAGE3_RESOURCES_NOT_SELECTED")
    if slot["backend_file"] is None:
        return {"status":"BLOCKED_GENRE_OWNED_BACKEND_NOT_YET_IMPLEMENTED",
                "genre":genre,"profile_id":entry["profile_id"],
                "musical_event_count":0,"production_enabled":False,
                "audio_render_authorized":False}
    if genre=="ROCK":
        from .shared_interpreter_router import route_to_shared_interpreter
        from .Rock.rock_pinned_mma_interpreter import compile_pinned_mma_rock_score
        require(stage3.get("tempo_bpm")==145 and stage3.get("meter")=="4/4",
                "ROCK_INSTRUMENT_CLOCK_NOT_145_4_4")
        shared=route_to_shared_interpreter(
            genre,original_stage3_result=stage3)
        raw=compile_pinned_mma_rock_score(source_midi_path,shared)
        notes=raw["notes"]
        meter=raw["meter"];tempo=raw["tempo_bpm"]
        status="GENRE_OWNED_ROCK_PINNED_SOURCE_SCORE_READY_NOT_DEPLOYED"
    elif genre=="Jazz Waltz":
        from .Jazz.jazz_waltz_genre_interpreter import interpret_genre
        require(stage3.get("meter")=="3/4" and stage3.get("tempo_bpm")==156,
                "JAZZ_WALTZ_STAGE3_CLOCK_MISMATCH")
        raw=interpret_genre(source_midi_path,selected_genre=genre)
        notes=raw["actual_music_events"];meter=raw["meter"];tempo=raw["tempo_bpm"]
        status="GENRE_OWNED_JAZZ_WALTZ_SYMBOLIC_NOT_MAPPED_TO_SFZ"
    elif genre=="Salsa":
        from .Latin.salsa_genre_interpreter import interpret_genre
        require(stage3.get("meter")=="4/4" and stage3.get("tempo_bpm")==190,
                "SALSA_STAGE3_CLOCK_MISMATCH")
        raw=interpret_genre(source_midi_path,selected_genre=genre)
        notes=raw["actual_music_events"];meter=raw["meter"];tempo=raw["tempo_bpm"]
        status="GENRE_OWNED_SALSA_SYMBOLIC_NOT_MAPPED_TO_SFZ"
    else:
        raise StyleMidiInterfaceError("GENRE_BACKEND_MODULE_UNRECOGNIZED_NO_FALLBACK:"+genre)
    require(notes and slot["source_profile_id"]==raw["profile_id"]
            if genre!="ROCK" else bool(notes) and slot["source_profile_id"]=="ROCK_CORE_V2",
            "GENRE_OWNED_INTERPRETATION_OUTPUT_INVALID")
    return {
      "status":status,"genre":genre,"profile_id":slot["source_profile_id"],
      "interpreter_file":slot["backend_file"],
      "owned_stage_boundary":"BETWEEN_ORIGINAL_STAGE3_AND_STAGE4",
      "stage3_clock_verified":{"meter":meter,"tempo_bpm":tempo},
      "musical_event_count":len(notes),
      "stage4_candidate_events":notes,
      "old_authoritative_composer_events_untouched":True,
      "midi_processing_shared":True,
      "sampled_recording_program_verified":False,
      "audio_render_authorized":False,
      "production_enabled":False,
      "real_genre_audition_approved":False,
    }
