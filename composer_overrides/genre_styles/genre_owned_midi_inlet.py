"""Genre-specific MIDI input wiring over one reusable, non-musical transport.

One exact, preserved 55-genre registry; each named genre keeps its OWN slot,
original musical definition, meter, tempo and track identities. This reads
actual Type-1 MIDI and verifies its destination, not just a genre filename.

SEED_PREVIEW receives each genre's existing seven-bar symbolic MIDI sketch
and MUST NOT pretend its abbreviated roles are its original full ensemble.
COMPOSER receives the actual complete original full-track vocabulary.
This is a *connection boundary*, not an active musical performance interpreter,
instrument renderer, sample verification, new Composer engine, or 3D mixer.
"""
from __future__ import annotations
from collections import defaultdict, deque
import hashlib
import json
from pathlib import Path

from .shared_interpreter_router import route_to_shared_interpreter, InterpreterConnectionError
from .source_pattern_library import read_pack

ROOT=Path(__file__).resolve().parent

def check(ok:bool, code:str):
    if not ok:
        raise InterpreterConnectionError("GENRE_SPECIFIC_MIDI_INLET:"+code)

def receive_genre_midi(path: str|Path, *, selected_genre:str,
                       composer_genre:str, source_kind:str="SEED_PREVIEW")->dict:
    """Read immutable multitrack MIDI into EXACT selected genre's own slot."""
    check(selected_genre==composer_genre and bool(selected_genre),
          "SELECTED_GENRE_AND_MIDI_SOURCE_DIFFER")
    check(source_kind in ("SEED_PREVIEW","COMPOSER"),
          "UNSUPPORTED_ORIGIN")
    genre=selected_genre
    route=route_to_shared_interpreter(genre)
    family=route["family"]
    registry=json.loads((ROOT/"GENRE_INTERPRETER_REGISTRY_R1.json").read_text())
    entry=registry["per_genre"][genre]
    check(entry["profile_id"]==route["genre_profile_id"],
          "WRONG_INDIVIDUAL_GENRE_SLOT_PROFILE")
    slot_ref=Path(entry["slot_file"])
    check(slot_ref.parts[:3]==("composer_overrides","genre_styles",family),
          "INTERPRETER_NOT_IN_ITS_OWN_GENRE_FOLDER")
    slot=json.loads((ROOT/Path(*slot_ref.parts[2:])).read_text(encoding="utf-8"))
    check(slot["genre_name"]==genre and
          slot["source_profile_id"]==route["genre_profile_id"] and
          slot["activated_in_live_composer"] is False and
          slot["source_specific_note_score_approved_for_production"] is False,
          "INDIVIDUAL_GENRE_INTERPRETER_SLOT_DRIFT")
    profile=json.loads((ROOT/family/"profile.json").read_text())["profiles"][genre]
    definition=profile["musical_definition"]
    check(definition["profile_id"]==route["genre_profile_id"],
          "WRONG_ORIGINAL_GENRE_MUSICAL_DEFINITION")
    full={t["track_id"] for t in profile["individual_instrument_tracks"]}
    check(full and len(full)==len(profile["individual_instrument_tracks"]),
          "FULL_GENRE_TRACKS_NOT_UNIQUE")
    if source_kind=="SEED_PREVIEW":
        source,_=read_pack(genre)
        permitted={r["role"]:r["instrument_id"] for r in source["roles"]}
        expected_conductor="CONDUCTOR_"+genre
        note_origin="SEVEN_BAR_SOURCE_SEED_NOT_FULL_ARRANGEMENT"
    else:
        permitted={t["track_id"]:t.get("instrument_id")
                   for t in profile["individual_instrument_tracks"]}
        expected_conductor="Conductor"
        note_origin="ORIGINAL_COMPOSER_FULL_TRACK_IDENTITIES"
    check(permitted,"SELECTED_GENRE_HAS_NO_TRACKS")
    midi_path=Path(path)
    check(midi_path.is_file() and midi_path.stat().st_size>100,
          "ACTUAL_MIDI_NOT_FOUND")
    original=midi_path.read_bytes()
    import mido
    mf=mido.MidiFile(str(midi_path))
    check(mf.type==1 and mf.ticks_per_beat==480,"NOT_TYPE1_480PPQ")
    roles=[];found=set();tempo=[];meters=[];all_notes=0
    for track_index,track in enumerate(mf.tracks):
        names=[msg.name for msg in track if msg.type=="track_name"]
        check(len(names)==1,"REQUIRES_SINGLE_NAMED_TRACK")
        name=names[0]
        check(name not in found,"DUPLICATE_INSTRUMENT_ROLE")
        found.add(name)
        is_conductor=track_index==0
        check(name==expected_conductor if is_conductor else name in permitted,
              "TRACK_NOT_OWNED_BY_SELECTED_GENRE:"+name)
        tick=0;pending=defaultdict(deque);notes=0
        for msg in track:
            check(msg.time>=0,"NEGATIVE_MIDI_TICK")
            tick+=msg.time
            if msg.type=="set_tempo":
                check(is_conductor,"TEMPO_WRITTEN_IN_INSTRUMENT")
                tempo.append((tick,msg.tempo))
            elif msg.type=="time_signature":
                check(is_conductor,"METER_WRITTEN_IN_INSTRUMENT")
                meters.append((tick,msg.numerator,msg.denominator))
            elif msg.type=="note_on" and msg.velocity>0:
                check(not is_conductor,"NOTES_IN_CONDUCTOR")
                pending[(msg.channel,msg.note)].append(tick)
                notes+=1
            elif msg.type=="note_off" or (msg.type=="note_on" and msg.velocity==0):
                k=(msg.channel,msg.note)
                check(not is_conductor and bool(pending[k]),
                      "NOTE_OFF_WITHOUT_NOTE_ON")
                check(tick>pending[k].popleft(),"MIDI_ZERO_LENGTH_NOTE")
            elif msg.type=="program_change":
                check(False,"GENERIC_GM_PROGRAM_CHANGE_NOT_PERMITTED")
        check(not any(pending.values()),"INCOMPLETE_NOTE_PAIR")
        if not is_conductor:
            check(notes>0,"INSTRUMENT_TRACK_IS_SILENT:"+name)
            all_notes+=notes
            roles.append({"track_id":name,
                          "original_genre_role_or_instrument":permitted[name],
                          "note_on_count":notes,"midi_track_index":track_index,
                          "exact_separate_track_received":True})
    check(len(tempo)==1 and tempo[0][0]==0,"ONE_STARTING_TEMPO_REQUIRED")
    check(len(meters)==1 and meters[0][0]==0,"ONE_STARTING_METER_REQUIRED")
    bpm=60_000_000/tempo[0][1]
    meter=f"{meters[0][1]}/{meters[0][2]}"
    lo,hi=definition["tempo_bpm_range"]
    check(meter in definition["meter_options"] and lo-.005<=bpm<=hi+.005,
          "GENRE_METER_OR_TEMPO_WRONG")
    if source_kind=="SEED_PREVIEW":
        check(meter==source["meter"] and
              abs(bpm-source["tempo_bpm"])<.005,
              "SOURCE_PREVIEW_PROFILE_CLOCK_MISMATCH")
    check(all_notes>0,"GENRE_INTERPRETER_NO_MIDI_NOTES")
    check(midi_path.read_bytes()==original,"SOURCE_MIDI_CHANGED")
    return {
        "status":"GENRE_SPECIFIC_MIDI_ARRIVED_AT_CORRECT_INTERPRETER_SLOT",
        "selected_genre":genre,"family":family,
        "exact_own_profile_id":entry["profile_id"],
        "exact_own_interpreter_slot":entry["slot_file"],
        "individual_musical_backend":entry["backend_file"],
        "actual_midi_sha256":hashlib.sha256(original).hexdigest(),
        "source_kind":source_kind,"notes_origin":note_origin,
        "midi_tracks_received":len(roles),"notes_received":all_notes,
        "individual_instrument_tracks":roles,
        "full_original_track_count":len(full),
        "full_original_tracks_not_present_in_preview":
            sorted(full-{r["track_id"] for r in roles}) if source_kind=="SEED_PREVIEW" else [],
        "abbreviated_seed_is_not_full_instrument_ensemble":source_kind=="SEED_PREVIEW",
        "tempo_bpm":round(bpm,3),"meter":meter,
        "original_source_midi_byte_identical":True,
        "shared_transport_not_shared_genre_playing_style":True,
        "genre_style_rules_loaded_from_own_profile":True,
        "next_stage":"OWN_GENRE_MUSICAL_INTERPRETATION_AND_ORIGINAL_INSTRUMENT_BINDING",
        "genre_musical_performance_activated":False,
        "original_recorded_instruments_rendered":False,
        "complete_recorded_music_verified":False,
        "production_deployed":False,
    }
