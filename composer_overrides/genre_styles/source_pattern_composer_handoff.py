"""One safe Stage4 composition handoff from independent genre source patterns.

Assembles actual note-event dictionaries in the existing Composer event shape.
Never silently replaces its original events, renders unknown programs, inserts
generic instrument substitutes or claims audio approval. Selected sources are
required before a complete candidate exists. Original 7 stage layout stands.
"""
from __future__ import annotations
from fractions import Fraction
from typing import Any,Mapping,Sequence
from .source_pattern_resource_handoff import map_source_roles
from .shared_interpreter_router import InterpreterConnectionError

HANDOFF_VERSION="AI_COMP_SOURCE_PATTERN_STAGE4_PROPOSAL_V1"

def require(flag: bool, msg: str) -> None:
    if not flag: raise InterpreterConnectionError(msg)

def prepare_source_pattern_composer_handoff(
    seed_plan: Mapping[str,Any], *,
    original_stage3_result: Mapping[str,Any]|None=None,
    existing_events: Sequence[Mapping[str,Any]]=(),
    target_bindings: Mapping[str,Any]|None=None,
) -> dict:
    """Prepare an independently inspectable, genre-authored Stage4 note score.

    Candidate audio activation requires a separate source file/note zone/stem
    verification and user audition. This function NEVER enables that itself.
    """
    source=seed_plan.get("source_pattern_contract",{})
    genre=seed_plan.get("genre")
    require(source.get("genre_specific_seed")==genre and
            source.get("production_enabled") is False and
            seed_plan.get("recorded_audio_authorized") is False and
            seed_plan.get("midi_authorized") is False,
            "SOURCE_PATTERN_SCORE_NOT_AUTHORIZED")
    mapping=map_source_roles(seed_plan,stage3=original_stage3_result,
                              target_bindings=target_bindings)
    symbolic=seed_plan.get("symbolic_note_events",[])
    require(bool(symbolic),"SOURCE_PATTERN_SCORE_EMPTY")
    original_events=list(existing_events)
    original_event_ids={(e.get("track_id"),e.get("instrument_id"),
                         str(e.get("start_beat")),int(e.get("midi",-1)))
                        for e in original_events}
    # Never allow preview notes to sneak into unchanged legacy event list.
    mapped={x["role"]:x for x in mapping["roles"]
            if x["status"]=="EXACT_PROGRAM_REFERENCE_ONLY"}
    candidate=[]
    if mapping["source_program_identification_complete"]:
        for i,n in enumerate(symbolic):
            role=n["role"]
            require(role in mapped,"SOURCE_PATTERN_ROLE_NOT_MAPPED:"+role)
            m=mapped[role]
            note=n["midi"]
            if n["pattern_kind"]=="DRUM_ABSOLUTE":
                require(note in m["percussion_allowed_midi_notes"],
                        "UNSUPPORTED_RECORDED_DRUM_NOTE")
            start=Fraction(n["start_beat"])
            duration=Fraction(n["duration_beats"])
            require(0<=start and duration>0 and type(note)==int and 0<=note<=127,
                    "INVALID_STAGE4_SCORE_NOTE")
            candidate.append({
                "track_id":role,
                # Existing InstrumentProgram accepts the physical instrument
                # ID (electric_guitar), NOT the resource-registry key
                # (electric_guitar:RHYTHM_POWER_CHORDS). That second key
                # belongs to TargetProgram, which derives it from track role.
                "instrument_id":m["original_instrument_id"],
                "expected_target_binding_id":m["binding_id"],
                "start_beat":float(start),
                "duration_beats":float(duration),
                "midi":note,
                "velocity":n["velocity"],
                "articulation":"authored_genre_pattern_not_auditioned",
                "source_pattern_section":n["section"],
                "source_pattern_variation":n["variation"],
                "source_pattern_kind":n["pattern_kind"],
                "resource_id":m["resource_id"],
                "preferred_mapping":m["preferred_mapping"],
                "composer_stage":"COMPOSE_SEPARATE_PARTS",
                "audit_status":"PROPOSED_NOT_APPROVED",
            })
        candidate.sort(key=lambda e:(e["start_beat"],e["track_id"],e["midi"]))
        require(len(candidate)==len(symbolic),"PARTIAL_INSTRUMENT_OUTPUT_FORBIDDEN")
    outcome=("CANDIDATE_STAGE4_EVENTS_READY_SOURCE_PREFLIGHT_PENDING"
             if candidate else "BLOCKED_INCOMPLETE_EXACT_INSTRUMENT_MAPPING")
    # Rock's actual recorded baseline has additional LEAD/TOMS/CRASH/RIDE
    # tracks. The first seven-bar source seed is deliberately incomplete;
    # never mislabel the five instrument parts as a complete Rock score.
    old_rock_tracks=("BASS","HARMONY","KICK","SNARE","HAT",
                     "LEAD","TOMS","CRASH","RIDE")
    missing_rock_tracks=(
        [role for role in old_rock_tracks
         if role not in {r["role"] for r in mapping["roles"]}]
        if genre=="ROCK" else [])
    # Composer's actual event list is preserved unchanged; this is a separate
    # candidate which the existing render path must not pick up implicitly.
    return {
       "schema":HANDOFF_VERSION,"genre":genre,
       "genre_profile_id":seed_plan["genre_profile_id"],
       "stage_3_to_4":seed_plan["stage_3_to_4"],
       "routing":mapping,"status":outcome,
       "candidate_stage4_events":candidate,
       "candidate_event_count":len(candidate),
       "candidate_contains_all_original_rock_parts":(
           not missing_rock_tracks if genre=="ROCK" else None),
       "missing_original_rock_tracks":missing_rock_tracks,
       "arrangement_scope":"SEVEN_BAR_SEED_NOT_COMPLETE_SONG",
       "requested_note_count":len(symbolic),
       "original_events_count":len(original_events),
       "existing_composer_events_unchanged":True,
       "candidate_is_not_live_events":True,
       "source_sfzs_preflight_passed":False,
       "original_sample_note_ranges_verified":False,
       "individual_stems_verified":False,
       "full_song_verified":False,
       "audio_render_authorized":False,
       "original_composer_is_authoritative_for_audio":True,
       "production_enabled":False
    }


def prepare_external_midi_composer_handoff(
    interpreter: Mapping[str,Any], *,
    original_genre_profile: Mapping[str,Any],
    recorded_full_track_map: Mapping[str,Any],
    original_stage3_result: Mapping[str,Any],
    existing_events: Sequence[Mapping[str,Any]]=(),
) -> dict:
    """Match external arranger MIDI to EXISTING original Stage-4 track IDs.

    Only a referenced original recorded-SFZ instrument is allowed to become
    an *unapproved isolated candidate*. Sources without an exact recorded
    program, unselected instruments, and unsupported kit roles remain blocked.
    Never route this partial proposal to the original Composer, render partial
    audio, change an arranger style or substitute an original instrument.
    """
    genre = interpreter.get("genre")
    require(genre == "Jazz Waltz" and
            interpreter.get("source_type") == "GENRE_SPECIFIC_EXTERNAL_MMA_MIDI",
            "EXTERNAL_MIDI_ORIGINAL_GENRE_NOT_ENABLED_FOR_HANDOFF")
    require(interpreter.get("audio_render_authorized") is False and
            interpreter.get("production_enabled") is False and
            interpreter.get("old_authoritative_composer_events_untouched") is True,
            "EXTERNAL_MIDI_UNAUTHORIZED_LIVE_INPUT")
    require(original_genre_profile.get("genre") == genre and
            recorded_full_track_map.get("genre") == genre and
            original_genre_profile["musical_definition"]["profile_id"] ==
            recorded_full_track_map["profile_id"] ==
            interpreter["profile_id"], "EXTERNAL_MIDI_ORIGINAL_PROFILE_MISMATCH")
    require(original_stage3_result.get("status") == "PASS" and
            original_stage3_result.get("palette") ==
            original_genre_profile.get("original_composer_instrument_palette"),
            "EXTERNAL_MIDI_STAGE3_ORIGINAL_PALETTE_MISMATCH")
    tracks = original_genre_profile["individual_instrument_tracks"]
    assigned = recorded_full_track_map["full_genre_tracks"]
    require(len(tracks) == len(assigned) and
            all(t["track_id"] == s["track_id"] and
                t.get("instrument_id") == s.get("original_instrument_id") and
                t.get("original_palette_group") == s.get("original_palette_group")
                for t,s in zip(tracks,assigned)),
            "EXTERNAL_MIDI_ORIGINAL_TRACK_OR_PALETTE_CHANGED")
    by_id = {t["track_id"]: t for t in assigned}
    require(len(by_id) == len(assigned), "ORIGINAL_TRACK_IDS_NOT_UNIQUE")
    by_instrument = {}
    for t in assigned:
        if t.get("original_instrument_id"):
            by_instrument.setdefault(t["original_instrument_id"],[]).append(t)
    # MIDI channel ten uses kit semantics. Treat symbols as *musical*
    # descriptions only; they are NOT SFZ sample or velocity map evidence.
    percussion_roles = {"SNARE":"SNARE","HI_HAT":"HAT"}
    received = interpreter["stage4_candidate_events"]
    require(received and len(received) == interpreter["musical_event_count"],
            "EXTERNAL_MIDI_INTERPRETED_NOTE_COUNT_DRIFT")
    candidates, blocked = [], []
    present_original_tracks = set()
    for note in received:
        require(note.get("genre") == genre and
                note.get("profile_id") == interpreter["profile_id"] and
                note.get("stage4_status") ==
                "INTERPRETED_SOURCE_NOTE_NOT_AUTHORIZED_FOR_AUDIO" and
                note.get("real_SFZ_sample_program_verified") is False,
                "EXTERNAL_SOURCE_NOTE_OR_AUDIO_AUTHORITY_CHANGED")
        channel, pitch, velocity = (note["channel"],note["source_midi_note"],
                                    note["velocity"])
        start,duration = note["start_beat"],note["duration_beats"]
        require(type(channel) is int and 0 <= channel <= 15 and
                type(pitch) is int and 0 <= pitch <= 127 and
                type(velocity) is int and 1 <= velocity <= 127 and
                isinstance(start,(int,float)) and
                isinstance(duration,(int,float)) and
                0 <= start and 0 < duration,
                "EXTERNAL_MIDI_NOTE_VALUES_INVALID")
        if channel == 9:
            track = by_id.get(percussion_roles.get(note["stage4_role"],""))
            allowed = track is not None and track.get("original_palette_group") == "brush_drums"
            reason = "" if allowed else "MMA_PERCUSSION_NOT_AN_ORIGINAL_TRACK"
        else:
            matches = by_instrument.get(note["proposed_physical_instrument_id"],[])
            track = matches[0] if len(matches) == 1 else None
            allowed = track is not None
            reason = "" if allowed else "MMA_INSTRUMENT_NOT_IN_ORIGINAL_SELECTED_TRACKS"
        if not allowed:
            blocked.append({"source_track":note["source_track"],
                "stage4_role":note["stage4_role"],"midi":pitch,"reason":reason})
            continue
        name = track["track_id"]
        present_original_tracks.add(name)
        if not (track.get("mapping_state") ==
                "RECORDED_PROGRAM_IDENTITY_REFERENCE_NOT_NEW_ROUTE_AUDIO_VERIFIED" and
                bool(track.get("resource_id")) and
                bool(track.get("registry_binding_id")) and
                bool(track.get("sfz_path")) and
                track.get("preflight_verified_for_this_genre") is False):
            blocked.append({"source_track":note["source_track"],
                "track_id":name,"midi":pitch,
                "reason":"ORIGINAL_TRACK_EXACT_RECORDED_PROGRAM_NOT_VERIFIED"})
            continue
        candidates.append({
            "track_id":name,
            "instrument_id":track["original_instrument_id"],
            "expected_target_binding_id":track["registry_binding_id"],
            "resource_id":track["resource_id"],
            "preferred_mapping":track["sfz_path"],
            "start_beat":float(start),
            "duration_beats":float(duration),
            "midi":pitch,
            "velocity":velocity,
            "source_midi_track":note["source_track"],
            "source_midi_channel":channel,
            "composer_stage":"COMPOSE_SEPARATE_PARTS",
            "audit_status":"REHEARSAL_REFERENCE_ONLY_ORIGINAL_SFZ_NOT_PREFLIGHTED",
        })
    candidates.sort(key=lambda n:(n["start_beat"],n["track_id"],n["midi"]))
    require(len(received) == len(candidates) + len(blocked),
            "EXTERNAL_MIDI_SILENT_NOTE_DISCARD")
    missing_original = sorted(set(by_id)-present_original_tracks)
    reasons = sorted({item["reason"] for item in blocked})
    original_event_count = len(existing_events)
    return {
        "schema":"AI_COMP_EXTERNAL_MIDI_STAGE4_REFERENCE_HANDOFF_V1",
        "genre":genre,
        "genre_profile_id":interpreter["profile_id"],
        "status":"BLOCKED_PARTIAL_MIDI_TO_ORIGINAL_RECORDED_TRACK_REFERENCES",
        "candidate_stage4_events":candidates,
        "candidate_event_count":len(candidates),
        "received_external_midi_note_count":len(received),
        "blocked_note_count":len(blocked),
        "blocked_note_reasons":reasons,
        "blocked_note_details":blocked,
        "unfilled_original_genre_tracks":missing_original,
        "recorded_program_reference_tracks":sorted({n["track_id"] for n in candidates}),
        "original_events_count":original_event_count,
        "existing_composer_events_unchanged":True,
        "candidate_is_not_live_events":True,
        "full_arrangement_ready":False,
        "individual_stems_verified":False,
        "source_sfzs_preflight_passed":False,
        "recorded_audio_authorized":False,
        "audio_render_authorized":False,
        "production_enabled":False,
    }
