"""ONE SHARED INTERPRETER — existing Rock MMA note-language backend, exact pinned source.

Project-written translation and typed Rock fill logic extracted from original
2026-10-08 successful proof, source preserved unchanged. MMA itself stays an
external separately licensed program, never copied into the Composer.
This is a selected Stage-3->4 score backend, not a second shared engine.
"""
from __future__ import annotations
import collections, copy, hashlib, json
from pathlib import Path

TEMPO=145
BARS=16
PPQ=480
PINNED_USER_LIKED_MMA_SHA256="7253c3715299018dc540bdbaf29883bfbd7615ab7e5d943bde45f8d1b19555fe"
ROLES={
    "HARMONY":("electric_guitar:RHYTHM_POWER_CHORDS","electric_guitar","RHYTHM_POWER_CHORDS",0),
    "BASS":("electric_bass_guitar","electric_bass_guitar","BASS",1),
    "KICK":("kick_drum_rock","kick_drum_rock","KICK_PULSE",2),
    "SNARE":("snare_drum","snare_drum","SNARE_BACKBEAT",3),
    "HAT":("hi_hat","hi_hat","HI_HAT",4),
    "TOMS":("tom_tom","tom_tom","TOM_FILL",5),
    "CRASH":("crash_cymbal","crash_cymbal","CRASH_ACCENT",6),
}
# These are not interchangeable General MIDI instruments. Open hat is an
# explicitly acknowledged closed-hat approximation in the current kit.
# Tambourine 54 has NO matching selected Rock role: omitted, counted.
GM_DRUM={
    36:("KICK",36,"exact_recorded_kick"),
    38:("SNARE",38,"exact_recorded_snare"),
    46:("HAT",42,"open_hat_to_available_closed_hat_APPROXIMATION"),
}
NAME_ROUTES={"Bass":"BASS","Chord-Clean":"HARMONY"}
# Named high-level instruction language, distinct from note-level MIDI.
INTENTS=(
    {"kind":"SECTION_CHANGE","at_bar":8,"from":"VERSE","to":"CHORUS"},
    {"kind":"SIXTEENTH_SNARE_ROLL","bar":7,"start":2.50,"until":3.25,
     "intensities":[42,55,70,85]},
    {"kind":"DESCENDING_TOM_FILL","bar":7,"beats":[3.50,3.75],
     "pitches":[47,43],"intensities":[88,100]},
    {"kind":"CHORUS_CRASH_ARRIVAL","bar":8,"beat":0.0,"velocity":98},
    {"kind":"SECTION_CHANGE","at_bar":16,"from":"CHORUS","to":"END"},
    {"kind":"SIXTEENTH_SNARE_ROLL","bar":15,"start":2.50,"until":3.25,
     "intensities":[40,57,72,88]},
    {"kind":"DESCENDING_TOM_FILL","bar":15,"beats":[3.50,3.75],
     "pitches":[47,43],"intensities":[89,101]},
)


def need(value,message):
    if not value:raise AssertionError(message)


def note_event(track,midi,velocity,start,duration,art="interpreted_midi_note"):
    need(track in ROLES,"UNKNOWN_SOURCE_TRACK")
    need(0<=midi<=127 and 1<=velocity<=127 and duration>0 and start>=0 and start<64,
         "UNPLAYABLE_NOTE_FROM_INTERPRETER")
    return {"track_id":track,
            "instrument_id":ROLES[track][1],
            "start_beat":round(start,6),
            "duration_beats":round(min(duration,64-start),6),
            "midi":int(midi),"velocity":int(velocity),"articulation":art}

def split_external_midi(midifile):
    import mido
    mf=mido.MidiFile(midifile)
    need(mf.type==1,"MMA_IS_NOT_MULTITRACK_MIDI")
    need(mf.ticks_per_beat>0,"MMA_BAD_RESOLUTION")
    mapping_report=collections.Counter()
    unsupported=collections.Counter()
    ignored=collections.Counter()
    parts=collections.defaultdict(list)
    for tr in mf.tracks:
        names=[m.name for m in tr if m.type=="track_name"]
        name=names[-1] if names else ""
        enabled=name=="Drum" or name in NAME_ROUTES
        absolute=0
        voices=collections.defaultdict(collections.deque)
        for msg in tr:
            absolute+=msg.time
            if msg.type not in ("note_on","note_off"):
                continue
            ison=msg.type=="note_on" and msg.velocity>0
            isoff=msg.type=="note_off" or (msg.type=="note_on" and msg.velocity==0)
            key=(getattr(msg,"channel",0),int(msg.note))
            if ison:
                voices[key].append((absolute,int(msg.velocity)))
            elif isoff and voices[key]:
                tick,velocity=voices[key].popleft()
                beat=tick/mf.ticks_per_beat
                duration=(absolute-tick)/mf.ticks_per_beat
                if not 0<=beat<64 or duration<=0:continue
                if name=="Drum":
                    if key[0]!=9:
                        raise AssertionError("EXTERNAL_DRUM_NOT_ON_GM_CHANNEL_10")
                    mapping=GM_DRUM.get(int(msg.note))
                    if mapping is None:
                        unsupported[msg.note]+=1
                        continue
                    track,pitch,policy=mapping
                    mapping_report[policy]+=1
                    parts[track].append(note_event(track,pitch,velocity,beat,
                        min(duration,.13),"mma_gm_drum_interpreted"))
                elif name in NAME_ROUTES:
                    track=NAME_ROUTES[name]
                    mapping_report["separate_"+track]+=1
                    parts[track].append(note_event(track,int(msg.note),velocity,beat,
                        max(.10,min(duration,1.15)),"mma_chord_or_bass"))
                else:
                    ignored[name]+=1
    need(all(parts.get(track) for track in ("HARMONY","BASS","KICK","SNARE","HAT")),
         "MMA_REQUIRED_BAND_PART_MISSING")
    need(set(unsupported).issubset({54}),"UNSUPPORTED_MMA_DRUM_KIT_NOT_DOCUMENTED:"+str(unsupported))
    for notes in parts.values():
        notes.sort(key=lambda e:(e["start_beat"],e["midi"]))
    return dict(parts),dict(mapping_report),dict(unsupported),dict(ignored)

def compile_transition_intents(baseline):
    """Local typed intent -> executable recorded-source note compiler.

    All external MMA notes pass through untouched except conflicting snare
    strokes in the intended short fill window; the custom roll and tom series
    are *not* claimed as native Yamaha/Korg/MMA automatic arrangement.
    """
    parts=copy.deepcopy(baseline)
    trace=[]
    for i,intent in enumerate(INTENTS):
        kind=intent["kind"]
        if kind=="SECTION_CHANGE":
            trace.append({"index":i,"intent":kind,"musical_target_bar":intent["at_bar"],
                          "emitted_notes":0,"cross_part_boundary":True})
            continue
        bar=intent["bar"]
        need(bar in (7,8,15),"UNAUTHORIZED_ARRANGEMENT_SECTION")
        added=[]
        if kind=="SIXTEENTH_SNARE_ROLL":
            start=bar*4+intent["start"]
            need(round(intent["until"]-intent["start"],6)==.75 and len(intent["intensities"])==4,
                 "NOT_A_FOUR_STROKE_SIXTEENTH_ROLL")
            # Avoid overlapping the source backbeat exactly under the roll.
            old=parts["SNARE"]
            parts["SNARE"]=[e for e in old if not (start-.0001<=e["start_beat"]<=start+.75+.0001)]
            for j,vel in enumerate(intent["intensities"]):
                added.append(note_event("SNARE",38,vel,start+j*.25,.09,"interpreted_snare_16th_roll"))
        elif kind=="DESCENDING_TOM_FILL":
            need(list(intent["pitches"])==[47,43],"UNAUTHORIZED_TOM_MAPPING")
            for beat,pitch,vel in zip(intent["beats"],intent["pitches"],intent["intensities"]):
                added.append(note_event("TOMS",pitch,vel,bar*4+beat,.1,"interpreted_tom_descent"))
        elif kind=="CHORUS_CRASH_ARRIVAL":
            need(bar==8 and intent["beat"]==0.0,"CHORUS_ARRIVAL_NOT_ALIGNED")
            added.append(note_event("CRASH",49,intent["velocity"],bar*4,.20,"interpreted_section_crash"))
            need(any(abs(e["start_beat"]-(bar*4))<.05 for e in parts["BASS"]),
                 "BASS_NOT_CONNECTED_TO_CHORUS_ARRIVAL")
            need(any(abs(e["start_beat"]-(bar*4))<.05 for e in parts["HARMONY"]),
                 "GUITAR_NOT_CONNECTED_TO_CHORUS_ARRIVAL")
        else:raise AssertionError("UNRECOGNIZED_MUSICAL_INTENT")
        for event in added:parts.setdefault(event["track_id"],[]).append(event)
        trace.append({"index":i,"intent":kind,"section_bar":bar,
                      "emitted_notes":len(added),"output_tracks":sorted({x["track_id"] for x in added}),
                      "note_onsets":[e["start_beat"] for e in added]})
    for events in parts.values():events.sort(key=lambda e:(e["start_beat"],e["midi"]))
    need(len([e for e in parts.get("TOMS",[])])==4,"TOM_FILL_NOT_INTERPRETED")
    need(len(parts.get("CRASH",[]))==1,"CHORUS_NOT_ACCENTED")
    return parts,trace


def compile_pinned_mma_rock_score(midi_path, shared_handoff):
    """Materialize the user's actual original interpretation as Stage-4 note events.

    Exact existing source MIDI and exact Rock sample instrument IDs required.
    No generic fallback, no external song remix, no voice or audio change.
    """
    midi_path=Path(midi_path)
    need(midi_path.is_file(),"ORIGINAL_ROCK_MIDI_NOT_FOUND")
    h=hashlib.sha256(midi_path.read_bytes()).hexdigest()
    need(h==PINNED_USER_LIKED_MMA_SHA256,"MMA_PINNED_USER_LIKED_INPUT_MISMATCH")
    need(shared_handoff["schema"]=="AI_COMP_SHARED_INTERPRETER_BOUNDARY_R1" and
         shared_handoff["genre"]=="ROCK","ROCK_ONLY_MATCHING_HANDOFF_REQUIRED")
    need(shared_handoff["genre_profile_id"]=="ROCK_CORE_V2","ROCK_PROFILE_MISMATCH")
    need(shared_handoff["stage_3_to_4"]=="MUSICAL_INTERPRETER_AND_SOURCE_SPECIFIC_BRIDGE","WRONG_HANDOFF_STAGE")
    need(shared_handoff["arranger_backend_state"]=="MUSICAL_EVENT_GENERATOR_NOT_ENABLED_OR_VERIFIED","UNAPPROVED_LIVE_BACKEND")
    need(shared_handoff["selected_meter"] in (None,"4/4"),"PINNED_ROCK_IS_4_4_ONLY")
    note_groups, remap, missing, ignored=split_external_midi(midi_path)
    filled, trace=compile_transition_intents(note_groups)
    events=[dict(e) for track in ROLES for e in filled.get(track,[])]
    events.sort(key=lambda e:(e["start_beat"],list(ROLES).index(e["track_id"]),e["midi"]))
    need(len(events)==420,"ORIGINAL_420_NOTES_MUST_BE_IDENTICAL")
    need(set(e["track_id"] for e in events)=={"HARMONY","BASS","KICK","SNARE","HAT","TOMS","CRASH"},"ORIGINAL_SEVEN_TRACKS_MISSING")
    need(all(0<=e["start_beat"]<64 for e in events),"BAD_SCORE_BARS")
    return {
        "status":"PINNED_MMA_ROCK_SCORE_INTERPRETED",
        "interpreter_engine":"SHARED_GENRE_INTERPRETER_R1",
        "genre":"ROCK","source_midi_sha256":h,
        "score_id":"MMA_25.05.0_ORIGINAL_ROCK_16BAR_PINNED",
        "source_musical_interpreter":"INDEPENDENT_MMA_25.05.0_SEPARATELY_LICENSED",
        "backend_name":"ROCK_MMA_20261008_PROJECT_OWNED_SCORE_TRANSLATOR",
        "source_instrument_mapping":{k:{"binding_id":v[0],"instrument_id":v[1],"role":v[2]} for k,v in ROLES.items()},
        "tempo_bpm":TEMPO,"meter":"4/4","bars":BARS,
        "note_count":len(events),"notes":events,
        "intent_trace":trace,
        "midi_translation_evidence":remap,
        "unsupported_mma_drum_notes":missing,
        "unselected_extra_mma_tracks":ignored,
        "output_to":"ORIGINAL_COMPOSE_SEPARATE_PARTS",
        "performance_stage":"ORIGINAL_PERFORM_MUSICALLY",
        "only_backend_verified_for_this_genre":True,
        "does_not_activate_all_55":True,"live_deployed":False,
        "finished_audio_not_proven_by_this_function":True,
    }
