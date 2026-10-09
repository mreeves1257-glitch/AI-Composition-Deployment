"""JAZZ WALTZ specific musical interpreter, project-owned bridge.

Consumes *external separately licensed* MMA JazzWaltz MIDI (never MMA code).
Owns jazz 3/4 ensemble interpretation, not Rock/Salsa templates.
Outputs original genre-specific Stage4 SOURCE events with exact GATE; no sample
pretence and no live Composer event replacement.
"""
from __future__ import annotations
from collections import Counter
from ..external_style_midi_reader import read_arranger_style_midi,require

GENRE="Jazz Waltz"
PROFILE="JAZZ_WALTZ_V1"
STYLE="JazzWaltz"
BPM=156
METER=(3,4)
# Musical roles from the external JazzWaltz arranger output. These are
# ORIGINAL source-track roles, not assertions that native SFZ patches exist.
ROUTES={
  "Walk":("WALKING_DOUBLE_BASS","double_bass"),
  "Bass":("BASS_PULSE","double_bass"),
  "Chord-Guitar":("GUITAR_COMP","acoustic_guitar"),
  "Chord":("JAZZ_HARMONIC_COMP","electric_piano"),
  "Drum":("JAZZ_KIT_UNVERIFIED",None)
}
# General MIDI percussion symbols, NOT authorization to reuse Rock SFZ drums.
GM_RESEARCH={38:"SNARE",42:"HI_HAT",51:"RIDE_CYMBAL"}

def interpret_genre(midi_path, *, selected_genre="Jazz Waltz"):
    require(selected_genre==GENRE,"JAZZ_WALTZ_INTERPRETER_CROSS_GENRE_FORBIDDEN")
    parsed=read_arranger_style_midi(midi_path,meter=METER,
          tempo_bpm=BPM,required_tracks=tuple(ROUTES))
    result=[]
    percussion=Counter()
    for note in parsed["events"]:
        name=note["source_track"]
        require(name in ROUTES,"JAZZ_WALTZ_SOURCE_TRACK_NOT_RECOGNIZED:"+name)
        role,physical=ROUTES[name]
        # The eighth bar is still sixteenth notes in 3/4, not 4/4.
        bar=int(note["start_beat"]//3)
        subbeat=round(note["start_beat"]%3,6)
        if name=="Drum":
            require(note["channel"]==9,"JAZZ_DRUMS_NOT_MIDI_CHANNEL_TEN")
            perc=GM_RESEARCH.get(note["source_midi_note"])
            require(perc is not None,"UNKNOWN_JAZZ_WALTZ_PERCUSSION_ID")
            percussion[perc]+=1
            role=perc
        else:
            require(note["channel"]!=9,"JAZZ_MELODY_USING_PERCUSSION_CHANNEL")
        result.append({**note,"genre":GENRE,"profile_id":PROFILE,
           "stage4_role":role,"proposed_physical_instrument_id":physical,
           "source_bar":bar,"beat_within_bar":subbeat,
           "real_SFZ_sample_program_verified":False,
           "stage4_status":"INTERPRETED_SOURCE_NOTE_NOT_AUTHORIZED_FOR_AUDIO"})
    require(max(x["source_bar"] for x in result)==7 and
       all(x["beat_within_bar"]<3 for x in result),
       "JAZZ_WALTZ_BAR_STRUCTURE_INCORRECT")
    require(percussion["RIDE_CYMBAL"]>0 and
            any(x["stage4_role"]=="WALKING_DOUBLE_BASS" for x in result),
            "JAZZ_WALTZ_MUSICAL_LANGUAGE_NOT_PRESENT")
    return {"status":"JAZZ_WALTZ_GENRE_SOURCE_MIDI_INTERPRETED",
       "genre":GENRE,"profile_id":PROFILE,"musical_program":STYLE,
       "meter":"3/4","tempo_bpm":BPM,"bars":8,
       "source_sha256":parsed["source_sha256"],
       "actual_music_events":result,"event_count":len(result),
       "source_track_roles":sorted(ROUTES),
       "source_percussion_note_classes":dict(percussion),
       "jazz_3_4_walking_bass_and_ride_verified":True,
       "distinct_style_language_executed":True,
       "native_recorded_programs_mapped":False,
       "audio_render_authorized":False,"production_enabled":False,
       "live_composer_events_replaced":False}
