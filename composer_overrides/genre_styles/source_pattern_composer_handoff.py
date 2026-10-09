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
