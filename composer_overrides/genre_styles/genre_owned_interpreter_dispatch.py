"""Strict Stage 3→4 genre-owned interpretation; rehearsal only, never production.

Every original genre has its own authored seven-section musical pattern and
profile in its established family folder. The 52 genres without a dedicated
external MIDI translator now execute those OWN score seeds via the existing
shared score compiler. Rock, Jazz Waltz and Salsa keep their separate,
unmodified MMA-derived interpreter backends. No genre inherits Rock notes.
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
EXTERNAL_BACKENDS = {"ROCK", "Jazz Waltz", "Salsa"}


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
        if genre == "ROCK":
            from .Rock.rock_pinned_mma_interpreter import compile_pinned_mma_rock_score
            require(backend ==
                "composer_overrides/genre_styles/Rock/rock_pinned_mma_interpreter.py",
                "ROCK_RECOVERED_INTERPRETER_CHANGED")
            require(stage3.get("tempo_bpm") == 145 and
                    stage3.get("meter") == "4/4",
                    "ROCK_INSTRUMENT_CLOCK_NOT_145_4_4")
            raw = compile_pinned_mma_rock_score(source_midi_path, route)
            notes = raw["notes"]
            meter = raw["meter"]
            tempo = raw["tempo_bpm"]
            status = "GENRE_OWNED_ROCK_PINNED_SOURCE_SCORE_READY_NOT_DEPLOYED"
        elif genre == "Jazz Waltz":
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
                (genre == "ROCK" or slot["source_profile_id"] == raw["profile_id"]),
                "GENRE_OWNED_INTERPRETATION_OUTPUT_INVALID")
        source_type = "GENRE_SPECIFIC_PINNED_OR_EXTERNAL_MMA_MIDI"

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
