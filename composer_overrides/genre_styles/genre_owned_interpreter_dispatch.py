"""Strict Stage 3→4 genre-owned interpretation; rehearsal only, never production.

Every original genre has its own authored seven-section musical pattern and
profile in its established family folder. Rock has now been reset to use its
own Rock-authored score, alongside 52 other genres using the same existing
compiler. Jazz Waltz and Salsa retain their distinct externally sourced MIDI
interpretation. The older pinned Rock interpreter is preserved but inactive.
No sample or SFZ playback is authorized by any of these outputs.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .external_style_midi_reader import StyleMidiInterfaceError, require
from .shared_interpreter_router import route_to_shared_interpreter

ROOT = Path(__file__).resolve().parent
AUTHORED_SEED_BACKEND = "composer_overrides/genre_styles/source_pattern_library.py"
EXTERNAL_BACKENDS = {"Jazz Waltz", "Salsa"}


def dispatch_stage3_to4_genre_owned(
    genre: str, *, source_midi_path: str | Path | None = None,
    original_stage3_result: dict[str, Any],
) -> dict:
    """Interpret the named genre's real source notes, without sound activation.

    The original Stage-3 selected meter and tempo govern timing. When a
    genre's authored seven-bar seed is incompatible with those selections,
    fail closed rather than silently remetering or performing in another style.
    """
    config = json.loads((ROOT / "GENRE_INTERPRETER_REGISTRY_R1.json").read_text())
    entries = config["per_genre"]
    require(isinstance(genre, str) and genre in entries,
            "UNKNOWN_GENRE_NO_GENERIC_FALLBACK")
    entry = entries[genre]
    slot = json.loads((ROOT.parent.parent / entry["slot_file"]).read_text())
    require(slot["genre_name"] == genre and
            slot["source_profile_id"] == entry["profile_id"],
            "GENRE_PROFILE_SOURCE_AUTHORITY_CHANGED")
    require(slot["activated_in_live_composer"] is False and
            slot["source_specific_note_score_approved_for_production"] is False,
            "UNAPPROVED_INTERPRETER_EXECUTION_IN_LIVE_COMPOSER")
    stage3 = original_stage3_result
    require(isinstance(stage3, dict) and stage3.get("status") == "PASS" and
            isinstance(stage3.get("palette"), list) and stage3["palette"] and
            all(isinstance(x, str) and x for x in stage3["palette"]),
            "ORIGINAL_STAGE3_RESOURCES_NOT_SELECTED")
    # Same exact existing shared Stage-3 input contract for every genre.
    route = route_to_shared_interpreter(genre, original_stage3_result=stage3)
    backend = slot.get("backend_file")
    require(backend is not None and backend == entry.get("backend_file", backend),
            "GENRE_OWNED_BACKEND_NOT_CONFIGURED")

    behavior = None
    if genre not in EXTERNAL_BACKENDS:
        # This is the established original per-genre authored pattern, not a
        # generic fallback and not a new eighth stage or another synthesis engine.
        require(backend == AUTHORED_SEED_BACKEND,
                "OTHER_GENRE_INTERPRETER_BACKEND_NOT_AUTHORIZED")
        require(source_midi_path is None,
                "GENRE_SEED_BACKEND_CANNOT_SILENTLY_IGNORE_EXTERNAL_MIDI")
        from .source_pattern_library import read_pack, compile_original_source_seed
        from .source_pattern_resource_handoff import load_binding_file

        seed, authoritative = read_pack(genre)
        require(seed["profile_id"] == slot["source_profile_id"] ==
                authoritative["genre_profile_id"], "GENRE_SEED_PROFILE_MISMATCH")
        require(stage3.get("meter") == seed["meter"],
                "GENRE_SELECTED_METER_DIFFERS_FROM_AUTHORED_SEED")
        tempo = stage3.get("tempo_bpm")
        require(type(tempo) is int, "GENRE_EXPLICIT_INTEGER_TEMPO_REQUIRED")
        planned = compile_original_source_seed(genre, selected_tempo_bpm=tempo)
        recorded_roles, source_ref = load_binding_file(genre)
        require(source_ref["genre_profile_id"] == slot["source_profile_id"],
                "GENRE_SOUND_MAP_WRONG_PROFILE")
        authored_roles = {x["role"]: x["instrument_id"] for x in seed["roles"]}
        declared_roles = recorded_roles["role_bindings"]
        require(set(declared_roles) == set(authored_roles) and
                all(declared_roles[k]["original_instrument_id"] == v
                    for k, v in authored_roles.items()),
                "GENRE_ROLE_TO_SOUND_MAPPING_MISMATCH")
        notes = planned["symbolic_note_events"]
        require(notes and all(n["status"] == "SYMBOLIC_ONLY" and
                n["role"] in authored_roles and
                n["instrument_id"] == authored_roles[n["role"]]
                for n in notes), "GENRE_SCORE_EVENT_ROLE_MISMATCH")
        meter = planned["meter"]
        tempo = planned["tempo_bpm"]
        status = "GENRE_OWNED_SOURCE_SCORE_INTERPRETED_SYMBOLIC_NOT_AUDIO_READY"
        behavior = {
            "source": "ORIGINAL_PER_GENRE_AUTHORED_SEVEN_SECTION_PATTERN",
            "genre": genre,
            "profile_id": slot["source_profile_id"],
            "musical_rules": planned["genre_rules"],
            "meter": meter, "tempo_bpm": tempo,
            "sections": planned["sections"],
            "chord_timeline": planned["chord_timeline"],
            "roles": planned["roles"],
            "source_seed": planned["source_pattern_contract"]["seed_id"],
            "capability_states": planned["capability_status"],
            "selected_stage3_palette": list(stage3["palette"]),
            "original_role_sound_mapping": {
                k: {"instrument_id": v, "reference_status":
                    declared_roles[k]["status"],
                    "stage3_selected": v in stage3["palette"]}
                for k, v in authored_roles.items()
            },
            "all_mapped_sample_files_audio_verified": False,
            "seven_bar_development_score_not_complete_song": True,
        }
        source_type = "ORIGINAL_GENRE_OWNED_SYMBOLIC_PATTERN"
    else:
        require(source_midi_path is not None,
                "ORIGINAL_EXTERNAL_GENRE_MIDI_SOURCE_REQUIRED")
        if genre == "Jazz Waltz":
            from .Jazz.jazz_waltz_genre_interpreter import interpret_genre
            require(backend ==
                "composer_overrides/genre_styles/Jazz/jazz_waltz_genre_interpreter.py",
                "JAZZ_WALTZ_SPECIALIZED_BACKEND_CHANGED")
            require(stage3.get("meter") == "3/4" and
                    stage3.get("tempo_bpm") == 156,
                    "JAZZ_WALTZ_STAGE3_CLOCK_MISMATCH")
            raw = interpret_genre(source_midi_path, selected_genre=genre)
            notes = raw["actual_music_events"]
            meter = raw["meter"]
            tempo = raw["tempo_bpm"]
            status = "GENRE_OWNED_JAZZ_WALTZ_SYMBOLIC_NOT_MAPPED_TO_SFZ"
        else:
            from .Latin.salsa_genre_interpreter import interpret_genre
            require(backend ==
                "composer_overrides/genre_styles/Latin/salsa_genre_interpreter.py",
                "SALSA_SPECIALIZED_BACKEND_CHANGED")
            require(stage3.get("meter") == "4/4" and
                    stage3.get("tempo_bpm") == 190,
                    "SALSA_STAGE3_CLOCK_MISMATCH")
            raw = interpret_genre(source_midi_path, selected_genre=genre)
            notes = raw["actual_music_events"]
            meter = raw["meter"]
            tempo = raw["tempo_bpm"]
            status = "GENRE_OWNED_SALSA_SYMBOLIC_NOT_MAPPED_TO_SFZ"
        require(bool(notes) and
                (slot["source_profile_id"] == raw["profile_id"]),
                "GENRE_OWNED_INTERPRETATION_OUTPUT_INVALID")
        source_type = "GENRE_SPECIFIC_EXTERNAL_MMA_MIDI"

    return {
        "status": status, "genre": genre,
        "profile_id": slot["source_profile_id"],
        "interpreter_file": backend,
        "source_type": source_type,
        "owned_stage_boundary": "BETWEEN_ORIGINAL_STAGE3_AND_STAGE4",
        "stage3_clock_verified": {"meter": meter, "tempo_bpm": tempo},
        "musical_event_count": len(notes),
        "stage4_candidate_events": notes,
        "genre_behavior": behavior,
        "old_authoritative_composer_events_untouched": True,
        "midi_processing_shared": True,
        "sampled_recording_program_verified": False,
        "audio_render_authorized": False,
        "production_enabled": False,
        "real_genre_audition_approved": False,
    }


def connect_selected_genre_components(
    genre: str, *, original_stage3_result: dict[str, Any],
    original_composer_events=(), target_bindings=None,
    source_midi_path: str | Path | None = None,
) -> dict[str, Any]:
    """Execute the EXISTING 55-genre component connections in rehearsal.

    Real genre profile -> Stage-3 selection -> owned interpreter -> own source
    notes -> exact original role-to-recording resolver -> original Composer
    Stage-4 *proposal* -> shared 22 Stage-5 capability handlers -> isolated
    stem/standalone mixer contracts. No new sound engine, no substituted bank,
    no mutations to original Composer events or source recordings.

    Stage-6/7 actual rendering and final mixing are NEVER invoked here.
    Unverified programs and external MMA-only score inputs fail closed.
    """
    from .shared_interpreter_router import (
        InterpreterConnectionError, ORIGINAL_STAGE_ORDER,
        route_to_shared_interpreter,
    )
    from .source_pattern_library import read_pack, compile_original_source_seed
    from .source_pattern_resource_handoff import map_source_roles
    from .source_pattern_composer_handoff import (
        prepare_source_pattern_composer_handoff,
    )

    def check(ok, reason):
        if not ok:
            raise InterpreterConnectionError(reason + ":" + genre)

    # The stored original genre profile, interpreter registry, musical seed,
    # role map and complete original instrument list MUST agree by identity.
    route = route_to_shared_interpreter(
        genre, original_stage3_result=original_stage3_result,
    )
    check(isinstance(original_stage3_result, dict) and
          original_stage3_result.get("status") == "PASS",
          "ORIGINAL_STAGE3_NOT_APPROVED")
    seed, seedref = read_pack(genre)
    check(seedref["genre_profile_id"] == route["genre_profile_id"] and
          original_stage3_result.get("meter") == seed["meter"],
          "GENRE_SOURCE_METER_OR_PROFILE_DRIFT")
    tempo = original_stage3_result.get("tempo_bpm")
    check(type(tempo) is int, "GENRE_STAGE3_TEMPO_NOT_AN_INTEGER")
    plan = compile_original_source_seed(genre, selected_tempo_bpm=tempo)
    check(plan["genre"] == genre and
          plan["source_pattern_contract"]["genre_specific_seed"] == genre and
          plan["source_pattern_contract"]["production_enabled"] is False,
          "GENRE_SCORE_NOT_OWNED")
    check(len(plan["capability_execution"]["capabilities"]) == 22 and
          plan["capability_execution"]["ready_for_live_deployment"] is False,
          "GENRE_22_CAPABILITY_CONTRACT_FAILED")

    maps_path = ROOT / route["family"] / "SOURCE_RESOURCE_BINDINGS_R1.json"
    maps = json.loads(maps_path.read_text(encoding="utf-8"))
    source_records = [x for x in maps["genres"] if x["genre"] == genre]
    full = maps["full_genre_track_sound_maps"].get(genre)
    check(len(source_records) == 1 and
          source_records[0]["profile_id"] == route["genre_profile_id"] and
          isinstance(full, dict) and
          full["profile_id"] == route["genre_profile_id"] and
          full["genre"] == genre and
          full.get("production_audio_enabled") is False,
          "GENRE_FULL_INSTRUMENT_MAP_WRONG_PROFILE")
    original = json.loads(
        (ROOT / route["family"] / "profile.json").read_text(encoding="utf-8")
    )["profiles"][genre]
    tracks = original["individual_instrument_tracks"]
    mapped_tracks = full["full_genre_tracks"]
    check(len(tracks) == len(mapped_tracks) and len(tracks) > 0 and
          len({x["track_id"] for x in mapped_tracks}) == len(tracks),
          "ORIGINAL_FULL_TRACK_COUNT_OR_ID_CHANGED")
    for a, b in zip(tracks, mapped_tracks):
        check(a["track_id"] == b["track_id"] and
              a.get("instrument_id") == b.get("original_instrument_id") and
              a.get("original_palette_group") == b.get("original_palette_group") and
              b["independent_audio_stem_required"] is True,
              "SOUND_MAP_TRACK_OR_INSTRUMENT_SUBSTITUTED")
        if b.get("resource_id"):
            check(b["mapping_state"] ==
                  "RECORDED_PROGRAM_IDENTITY_REFERENCE_NOT_NEW_ROUTE_AUDIO_VERIFIED" and
                  b.get("preflight_verified_for_this_genre") is False and
                  bool(b.get("sfz_path")) and
                  bool(b.get("registry_binding_id")),
                  "INVALID_SOUND_RESOURCE_REFERENCE")
        else:
            check(b["mapping_state"] ==
                  "BLOCKED_NO_EXACT_PROGRAM_OR_CONTEXTUAL_KIT_MAPPING" and
                  b.get("sfz_path") is None,
                  "UNVERIFIED_INSTRUMENT_NOT_BLOCKED")

    mapped = map_source_roles(
        plan, stage3=original_stage3_result,
        target_bindings=target_bindings,
    )
    originals = list(original_composer_events)
    # Two independently authored external-MMA style interpreters require their
    # OWN recorded MIDI and an eventual exact note/track-to-SFZ translation.
    # Don't pass their incompatible event dialect into the Composer renderer.
    if genre in EXTERNAL_BACKENDS and source_midi_path is None:
        interpreter = {
            "status": "BLOCKED_EXTERNAL_GENRE_MIDI_NOT_PROVIDED",
            "genre": genre, "profile_id":route["genre_profile_id"],
            "musical_event_count": 0,
            "stage4_candidate_events": [],
            "production_enabled": False,
            "audio_render_authorized": False,
        }
    else:
        interpreter = dispatch_stage3_to4_genre_owned(
            genre, source_midi_path=source_midi_path,
            original_stage3_result=original_stage3_result,
        )
        check(interpreter["genre"] == genre and
              interpreter["profile_id"] == route["genre_profile_id"] and
              interpreter["production_enabled"] is False,
              "WRONG_GENRE_INTERPRETER_EXECUTED")
    if genre in EXTERNAL_BACKENDS:
        proposal = {
            "status": "BLOCKED_EXTERNAL_STYLE_TO_ORIGINAL_COMPOSER_ROLE_TRANSLATION_PENDING",
            "candidate_stage4_events": [],
            "candidate_event_count": 0,
            "existing_composer_events_unchanged": True,
            "audio_render_authorized": False,
        }
    else:
        # This is the original Stage-4 shape and existing routing function;
        # incomplete source/program mappings produce NO partial instrument mix.
        proposal = prepare_source_pattern_composer_handoff(
            plan, original_stage3_result=original_stage3_result,
            existing_events=originals, target_bindings=target_bindings,
        )
        check(interpreter["musical_event_count"] ==
              len(plan["symbolic_note_events"]) and
              interpreter["stage4_candidate_events"] ==
              plan["symbolic_note_events"], "INTERPRETER_TO_STAGE4_SCORE_DRIFT")
    check(proposal["audio_render_authorized"] is False and
          proposal["existing_composer_events_unchanged"] is True,
          "ORIGINAL_COMPOSER_EVENTS_OVERWRITTEN")

    pinned_tracks = [x["track_id"] for x in mapped_tracks if x.get("resource_id")]
    blocked_tracks = [x["track_id"] for x in mapped_tracks if not x.get("resource_id")]
    source_missing = mapped["unresolved_roles"]
    blockers = []
    if interpreter["musical_event_count"] == 0:
        blockers.append("EXTERNAL_STYLE_MIDI_REQUIRED_FOR_" + genre)
    if genre in EXTERNAL_BACKENDS:
        blockers.append("EXTERNAL_STYLE_NOT_YET_TRANSLATED_INTO_ORIGINAL_COMPOSER_EVENT_DIALECT")
    if source_missing or mapped["unsupported_percussion_notes"]:
        blockers.append("UNRESOLVED_SOURCE_ROLE_PROGRAM_OR_NOTE_MAPPING")
    if blocked_tracks:
        blockers.append("FULL_ARRANGEMENT_TRACKS_REQUIRE_EXACT_SFZ_BINDING")
    if len(plan["roles"]) != len(mapped_tracks) or \
       {x["role"] for x in plan["roles"]} != {x["track_id"] for x in mapped_tracks}:
        blockers.append("SEVEN_BAR_SOURCE_SEED_DOES_NOT_COVER_ALL_FULL_SONG_TRACKS")
    blockers.extend((
        "FULL_LENGTH_GENRE_PERFORMANCE_NOT_AUDITIONED",
        "SFZ_NOTE_ZONES_AND_INDEPENDENT_RECORDED_STEMS_NOT_PREFLIGHTED",
        "STANDALONE_3D_MIX_AND_PLUG_PHONE_AUDIO_NOT_REVERIFIED",
    ))
    order = list(ORIGINAL_STAGE_ORDER)
    return {
        "schema": "AI_COMP_55_GENRE_COMPONENT_HANDOFF_REHEARSAL_R1",
        "genre": genre, "family": route["family"],
        "profile_id": route["genre_profile_id"],
        "original_seven_stage_order": order,
        "interpreter_inserted_between": ["CHOOSE_INSTRUMENTS_AND_DRUM_KIT",
                                          "COMPOSE_SEPARATE_PARTS"],
        "stage3_to_interpreter": {
            "status": interpreter["status"], "source": interpreter.get("source_type"),
            "musical_event_count": interpreter["musical_event_count"],
            "genre_exclusive": True,
        },
        "interpreter_to_original_stage4": {
            "status": proposal["status"],
            "candidate_event_count": proposal["candidate_event_count"],
            "original_event_count": len(originals),
            "candidate_only_not_active_composer_events": True,
        },
        "stage3_to_sound_mapping": {
            "mapped_symbolic_role_references": mapped["exact_registry_references"],
            "missing_or_rejected_symbolic_roles": list(source_missing),
            "unsupported_percussion_note_requests":
                list(mapped["unsupported_percussion_notes"]),
            "source_program_identification_complete":
                mapped["source_program_identification_complete"],
        },
        "stage4_to_stage5_performance": {
            "shared_22_capability_handlers_connected":
                plan["capability_execution"]["all_handlers_connected"],
            "handler_count": len(plan["capability_execution"]["capabilities"]),
            "performance_not_auditioned": True,
            "capability_report": plan["capability_execution"]["capabilities"],
        },
        "stage5_to_stage6_recorded_stems": {
            "required_original_separate_tracks": list(full["requested_separate_stems"]),
            "exact_recorded_program_reference_tracks": pinned_tracks,
            "blocked_exact_program_tracks": blocked_tracks,
            "sfz_sample_graph_and_note_zone_verified": False,
            "renderer_executed": False,
            "stem_wav_count": 0,
        },
        "stage6_to_stage7_independent_3d_mixer": {
            "source": "PRESERVED_ORIGINAL_STANDALONE_3D_MIXER",
            "status": "BLOCKED_UNTIL_VERIFIED_SEPARATE_WAV_STEMS_EXIST",
            "mixer_unchanged": True, "mixer_executed": False,
            "master_wav_created": False,
        },
        "original_event_list_unchanged": originals == list(original_composer_events),
        "live_composer_events_replaced": False,
        "audio_render_authorized": False,
        "live_deployment_authorized": False,
        "connection_blockers": blockers,
        "status": "COMPONENTS_LINKED_IN_REHEARSAL_NOT_END_TO_END_AUDIO_COMPLETE",
    }


def connect_all_55_component_checkpoints(*, target_bindings=None) -> dict:
    """Run the same disconnected/non-audio component handoff for all 55."""
    from .shared_interpreter_router import listed_genres
    from .source_pattern_library import read_pack

    connections = {}
    for genre in listed_genres():
        seed, _ = read_pack(genre)
        palette = list(dict.fromkeys(x["instrument_id"] for x in seed["roles"]))
        selected = {"status": "PASS", "palette": palette,
                    "meter": seed["meter"], "tempo_bpm": seed["tempo_bpm"]}
        connections[genre] = connect_selected_genre_components(
            genre, original_stage3_result=selected,
            target_bindings=target_bindings,
        )
    return connections
