"""SALSA genre's own rhythmic, chord and clave interpretation backend.

Consumes separate official MMA 'Salsa' output using project-owned MIDI
translation. Retains the actual GM Latin percussion IDs as SYMBOLIC roles;
does NOT remap maracas, claves, cowbells, guiro to a Rock drum bank.
"""
from __future__ import annotations
from collections import Counter
from ..external_style_midi_reader import read_arranger_style_midi,require

GENRE="Salsa"
PROFILE="SALSA_V1"
STYLE="Salsa"
BPM=190
METER=(4,4)
ROUTES={
  "Bass":("SYNCOPATED_SALSA_BASS","electric_bass"),
  "Chord":("MONTUNO_SOURCE_CHORD","electric_piano"),
  "Drum":("LATIN_PERCUSSION_MULTIROLE_UNVERIFIED",None)
}
GM_LATIN={
  56:"COWBELL",61:"LOW_BONGO",68:"LOW_AGOGO",69:"CABASA",
  73:"SHORT_GUIRO",74:"LONG_GUIRO",75:"CLAVES",
}

def interpret_genre(midi_path, *, selected_genre="Salsa"):
    require(selected_genre==GENRE,"SALSA_INTERPRETER_CROSS_GENRE_FORBIDDEN")
    parsed=read_arranger_style_midi(midi_path,meter=METER,
           tempo_bpm=BPM,required_tracks=tuple(ROUTES))
    events=[]
    perc=Counter()
    bars=Counter()
    clave_hits=[]
    for n in parsed["events"]:
        name=n["source_track"]
        require(name in ROUTES,"NON_SALSA_SOURCE_TRACK:"+name)
        role,physical=ROUTES[name]
        bar=int(n["start_beat"]//4)
        beat=round(n["start_beat"]%4,6)
        if name=="Drum":
            require(n["channel"]==9,"LATIN_DRUM_NOT_GM_CHANNEL_TEN")
            key=n["source_midi_note"]
            require(key in GM_LATIN,"UNKNOWN_OR_UNAPPROVED_LATIN_GM_KEY:"+str(key))
            role=GM_LATIN[key]
            perc[role]+=1
            if role=="CLAVES":clave_hits.append((bar,beat))
        else:
            require(n["channel"]!=9,"LATIN_BASS_CHORD_MUST_NOT_BE_DRUM_CHANNEL")
        bars[bar]+=1
        events.append({**n,"genre":GENRE,"profile_id":PROFILE,
           "stage4_role":role,"proposed_physical_instrument_id":physical,
           "source_bar":bar,"beat_within_bar":beat,
           "clave_cycle_bar_index":bar%2,
           "real_SFZ_sample_program_verified":False,
           "stage4_status":"INTERPRETED_SOURCE_NOTE_NOT_AUTHORIZED_FOR_AUDIO"})
    require(len(bars)==8 and max(bars)==7,
            "SALSA_STYLE_NOT_EIGHT_BAR_4_4")
    # Presence on more than one measure ensures a real rhythmic line, not
    # simply printed metadata labeled 'clave'. The exact 2-3/3-2 orientation
    # is NOT inferred without verifying the source pattern/entry phase.
    require(len(clave_hits)>4 and len({b%2 for b,_ in clave_hits})==2,
            "SALSA_CLAVE_SOURCE_RHYTHM_MISSING")
    require(perc["CLAVES"]>0 and perc["COWBELL"]>0 and
            any(e["stage4_role"]=="SYNCOPATED_SALSA_BASS" for e in events),
            "SALSA_SPECIFIC_GROOVE_AND_BASS_MISSING")
    return {"status":"SALSA_GENRE_SOURCE_MIDI_INTERPRETED",
       "genre":GENRE,"profile_id":PROFILE,"musical_program":STYLE,
       "meter":"4/4","tempo_bpm":BPM,"bars":8,
       "source_sha256":parsed["source_sha256"],
       "actual_music_events":events,"event_count":len(events),
       "source_track_roles":sorted(ROUTES),
       "latin_percussion_roles":dict(perc),
       "two_bar_clave_periodicity_observed":True,
       "exact_2_3_vs_3_2_clave_orientation_verified":False,
       "conga_and_trumpet_sources_present":False,
       "distinct_style_language_executed":True,
       "native_recorded_programs_mapped":False,
       "audio_render_authorized":False,"production_enabled":False,
       "live_composer_events_replaced":False}
