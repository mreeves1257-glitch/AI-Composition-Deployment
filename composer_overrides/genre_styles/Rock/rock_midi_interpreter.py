"""Rock's OWN inbound MIDI interpreter: Composer MIDI -> exact Rock roles.

This module is an isolated development receiver, not a generic/shared musical
interpreter.  It consumes the original Composer's Type-1 MIDI, verifies Rock's
genre/clock/track identities, and returns separate recorded-program handoffs.

No notes are altered, no original recordings are touched, and nothing is
routed to the renderer, mixer or live Composer until a later verified step.
"""
from __future__ import annotations

from collections import defaultdict, deque
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parent
EXPECTED_GENRE="ROCK"

class RockMidiHandoffError(ValueError):
    pass

def require(ok:bool, reason:str)->None:
    if not ok:
        raise RockMidiHandoffError(reason)

def _read_json(filename:str)->dict:
    path=ROOT/filename
    require(path.is_file(),"MISSING_ORIGINAL_ROCK_FILE:"+filename)
    return json.loads(path.read_text(encoding="utf-8"))

def receive_composer_midi(midi_path:str|Path, *, genre:str="ROCK")->dict[str,Any]:
    """Read REAL pre-interpreter Composer MIDI and bind every event to Rock.

    Explicitly *does not* convert the Composer's notes into a different score;
    later genre performance rules and sampled-audio checks have separate gates.
    """
    require(genre==EXPECTED_GENRE,"NOT_THE_ROCK_GENRE_INTERPRETER")
    slot=_read_json("INTERPRETER_ROCK_R1.json")
    profile=_read_json("profile.json")["profiles"][EXPECTED_GENRE]
    refs=_read_json("SOURCE_RESOURCE_BINDINGS_R1.json")
    require(slot["genre_name"]==EXPECTED_GENRE
            and slot["source_profile_id"]==profile["musical_definition"]["profile_id"],
            "ROCK_SOURCE_PROFILE_ID_MISMATCH")
    require(slot["activated_in_live_composer"] is False
            and slot["source_specific_note_score_approved_for_production"] is False,
            "ROCK_PRODUCTION_GATE_UNEXPECTEDLY_ENABLED")
    inbound=slot.get("composer_midi_inbound",{})
    require(inbound.get("entrypoint")==
            "genre_styles.Rock.rock_midi_interpreter.receive_composer_midi"
            and inbound.get("shared_interpreter_used") is False
            and inbound.get("live_deployed") is False,
            "ROCK_OWN_INTERPRETER_MIDI_CONNECTION_NOT_REGISTERED")
    tracks=profile["individual_instrument_tracks"]
    mapping=refs["full_genre_track_sound_maps"][EXPECTED_GENRE]
    require(mapping["profile_id"]==slot["source_profile_id"],
            "ROCK_SFZ_MAP_PROFILE_MISMATCH")
    mapped=mapping["full_genre_tracks"]
    require(len(tracks)==len(mapped),"ROCK_FULL_TRACK_IDENTITY_COUNT_DRIFT")
    owned={a["track_id"]:a for a in tracks}
    bindings={x["track_id"]:x for x in mapped}
    require(len(owned)==len(tracks) and len(bindings)==len(mapped)
            and set(owned)==set(bindings),"ROCK_DUPLICATE_OR_MISSING_FULL_TRACK_IDS")
    for track_id, original in owned.items():
        record=bindings[track_id]
        require(original["instrument_id"]==record["original_instrument_id"]
                and record["independent_audio_stem_required"] is True
                and bool(record.get("registry_binding_id"))
                and bool(record.get("resource_id"))
                and bool(record.get("sfz_path")),
                "ROCK_ORIGINAL_RECORDED_PROGRAM_IDENTITY_UNRESOLVED:"+track_id)
    p=Path(midi_path)
    require(p.is_file() and p.stat().st_size>128,"COMPOSER_MIDI_NOT_FOUND")
    original_bytes=p.read_bytes()
    import mido
    midi=mido.MidiFile(p)
    require(midi.type==1 and midi.ticks_per_beat==480,
            "ROCK_REQUIRES_ORIGINAL_TYPE1_480PPQ_MIDI")
    conductor=0
    part_outputs=[]
    seen=set()
    tempos=[]
    timesigs=[]
    all_notes=0
    for index, track in enumerate(midi.tracks):
        names=[m.name for m in track if m.type=="track_name"]
        require(len(names)==1,"MIDI_TRACK_NEEDS_EXACTLY_ONE_NAME:"+str(index))
        name=names[0]
        require(name=="Conductor" or name in owned,
                "MIDI_TRACK_NOT_SUPPORTED_BY_ROCK:"+str(name))
        require(name not in seen,"DUPLICATE_MIDI_TRACK:"+name)
        seen.add(name)
        ticks=0
        pending=defaultdict(deque)
        count=0
        channel_events=0
        other_events=0
        for msg in track:
            ticks+=msg.time
            require(ticks>=0,"NEGATIVE_MIDI_POSITION")
            if msg.type=="set_tempo":
                tempos.append((ticks,msg.tempo))
            if msg.type=="time_signature":
                timesigs.append((ticks,msg.numerator,msg.denominator))
            if msg.type=="note_on" and msg.velocity>0:
                require(name!="Conductor","CONDUCTOR_HAS_NOTE_EVENTS")
                pending[(msg.channel,msg.note)].append(ticks)
                count+=1
            elif msg.type=="note_off" or (msg.type=="note_on" and msg.velocity==0):
                require(name!="Conductor","CONDUCTOR_HAS_NOTE_EVENTS")
                key=(msg.channel,msg.note)
                require(bool(pending[key]),"UNMATCHED_MIDI_NOTE_OFF:"+name)
                start=pending[key].popleft()
                require(ticks>start,"ZERO_OR_NEGATIVE_MIDI_NOTE_DURATION:"+name)
            elif not msg.is_meta:
                channel_events+=1
            else:
                other_events+=1
        require(not any(pending.values()),"MIDI_NOTE_ON_WITHOUT_NOTE_OFF:"+name)
        if name=="Conductor":
            conductor+=1
            require(index==0,"CONDUCTOR_NOT_FIRST_TRACK")
            continue
        require(count>0,"ROCK_INSTRUMENT_TRACK_HAS_NO_NOTES:"+name)
        record=bindings[name]
        part_outputs.append({
            "track_id":name,
            "instrument_id":record["original_instrument_id"],
            "recorded_program_binding_id":record["registry_binding_id"],
            "resource_id":record["resource_id"],
            "sfz_program":record["sfz_path"],
            "midi_track_index":index,
            "note_on_count":count,
            "non_note_channel_messages":channel_events,
            "same_original_midi_bytes":True,
            "source_program_reference_only":True,
        })
        all_notes+=count
    require(conductor==1,"ORIGINAL_CONDUCTOR_TRACK_MISSING")
    require(all_notes>0 and len(part_outputs)>0,"NO_ROCK_MIDI_PARTS")
    require(tempos and tempos[0][0]==0,"INITIAL_MIDI_TEMPO_REQUIRED")
    require(not any(at>0 for at,_ in tempos),"UNEXPECTED_MIDI_TEMPO_CHANGE")
    tempo_us=tempos[0][1]
    require(all(val==tempo_us for _,val in tempos),"CONFLICTING_MIDI_TEMPO_EVENTS")
    bpm=60_000_000/tempo_us
    lo,hi=profile["musical_definition"]["tempo_bpm_range"]
    require(lo-0.001<=bpm<=hi+0.001,"ROCK_TEMPO_OUTSIDE_GENRE_PROFILE")
    require(timesigs and timesigs[0][0]==0,"INITIAL_MIDI_METER_REQUIRED")
    require(not any(at>0 for at,_,_ in timesigs),"UNEXPECTED_MIDI_METER_CHANGE")
    require(all((n,d)==(4,4) for _,n,d in timesigs),"ROCK_WRONG_MIDI_METER")
    require(hashlib.sha256(p.read_bytes()).digest()==hashlib.sha256(original_bytes).digest(),
            "ORIGINAL_COMPOSER_MIDI_MUTATED")
    return {
        "status":"ROCK_OWN_INTERPRETER_RECEIVED_COMPOSER_MIDI",
        "genre":EXPECTED_GENRE,
        "genre_profile_id":slot["source_profile_id"],
        "specific_genre_interpreter":"genre_styles.Rock.rock_midi_interpreter",
        "source_midi_sha256":hashlib.sha256(original_bytes).hexdigest(),
        "midi_format":midi.type,
        "midi_ppq":midi.ticks_per_beat,
        "tempo_bpm":round(bpm,3),
        "meter":"4/4",
        "original_midi_track_count":len(midi.tracks),
        "note_on_count":all_notes,
        "received_rock_roles":part_outputs,
        "unwritten_rock_roles":[x for x in owned if x not in seen],
        "inbound_original_notes_unchanged":True,
        "received_as_separate_instrument_roles":True,
        "musical_rearrangement_or_phrase_rules_applied":False,
        "sample_graph_or_sfzs_checked":False,
        "instrument_renderer_connected":False,
        "production_enabled":False,
        "output_next_stage":"EXISTING_INSTRUMENT_RENDERER_AFTER_APPROVAL",
    }
