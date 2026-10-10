"""Active development routing for all 55 ORIGINAL genre settings.

This consumes each genre's own preserved tempo/meter/groove/role definitions.
It changes no instrument, velocity, timbre, gain, SFZ, groove, rhythm or mix.
All 55 can be SELECTED and routed to an independent genre MIDI slot.
Finished-audio permission requires separately established real sample/audio proof.
"""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

ROOT=Path(__file__).resolve().parent
SETTING="RUN_CONNECTION_SETTINGS_R1.json"
SCHEMA="AI_COMP_55_INDIVIDUAL_GENRE_RUNTIME_SETTINGS_R1"
ORDER=("COMPOSER","ORIGINAL_TYPE1_MIDI","OWN_GENRE_INTERPRETER",
       "ORIGINAL_RECORDED_SFZ","STANDARD_STEREO",
       "OPTIONAL_STANDALONE_3D_MIXER_LAST")
APPROVED_DEVELOPMENT_AUDIO=frozenset(("ROCK","Jazz Ballad"))
EXTERNAL_OWN_STYLE=frozenset(("Jazz Waltz","Salsa"))

class OriginalGenreSettingsError(ValueError):
    pass

def require(ok,reason):
    if not ok:raise OriginalGenreSettingsError(reason)

def _json(path):
    require(path.is_file(),"GENRE_FILE_MISSING:"+str(path))
    return json.loads(path.read_text(encoding="utf-8"))

def load_genre_configuration(genre:str)->dict:
    index=_json(ROOT/"index.json")
    filepath=index["genre_to_family_file"].get(genre)
    require(bool(filepath),"UNKNOWN_55_GENRE:"+repr(genre))
    family=Path(filepath).parent.name
    file=ROOT/family/SETTING
    settings=_json(file)
    require(settings["schema"]==SCHEMA and settings["family"]==family
            and tuple(settings["shared_route"])==ORDER
            and settings["common_transport_module"]==
               "genre_styles.genre_owned_midi_inlet.receive_genre_midi"
            and settings["authoritative_genre_profiles_unmodified"] is True
            and settings["original_mixes_and_dynamics_unmodified"] is True
            and settings["original_recorded_instrument_library_unmodified"] is True
            and settings["no_general_midi_fallback"] is True,
            "GENRE_SETTINGS_CHAIN_OR_PRESERVATION_FAILURE:"+genre)
    records=[p for p in settings["per_genre"] if p.get("genre")==genre]
    require(len(records)==1,"GENRE_MISSING_OR_DUPLICATE_SETTINGS:"+genre)
    item=records[0]
    from .shared_interpreter_router import route_to_shared_interpreter
    route=route_to_shared_interpreter(genre)
    original=_json(ROOT/filepath)["profiles"][genre]
    musical=original["musical_definition"]
    registered=_json(ROOT/"GENRE_INTERPRETER_REGISTRY_R1.json")["per_genre"][genre]
    refs=_json(ROOT/family/"SOURCE_RESOURCE_BINDINGS_R1.json")
    recorded=refs["full_genre_track_sound_maps"][genre]["full_genre_tracks"]
    safe=genre.replace("~","~0").replace("/","~1")
    require(item["profile_id"]==route["genre_profile_id"]==
            musical["profile_id"]==registered["profile_id"],
            "GENRE_PROFILE_ID_NOT_EXACT:"+genre)
    require(item["original_definition_file"]==
            "composer_overrides/genre_styles/"+filepath and
            item["original_definition_pointer"]==
            "/profiles/"+safe+"/musical_definition",
            "GENRE_DEFINITION_POINTER_WRONG:"+genre)
    require(item["genre_midi_interpreter_slot"]==registered["slot_file"]
            and item["genre_specific_interpreter_backend"]==registered["backend_file"]
            and item["genre_source_pattern_file"]==
            "composer_overrides/genre_styles/"+family+"/SOURCE_PATTERN_LIBRARY_R1.json",
            "GENRE_INTERPRETER_MISMATCH:"+genre)
    for k,orig in (("meter_options","meter_options"),
                   ("tempo_bpm_range","tempo_bpm_range"),
                   ("original_groove_behavior","groove_behavior"),
                   ("original_phrase_behavior","phrase_behavior"),
                   ("original_ensemble_behavior","ensemble_player_behavior")):
        require(item[k]==musical[orig],"GENRE_MUSICAL_IDENTITY_CHANGED:"+genre+":"+k)
    refs_saved=item["recorded_role_bindings"]
    require(len(refs_saved)==len(recorded)==len(original["individual_instrument_tracks"]),
            "GENRE_INSTRUMENT_COUNT_CHANGED:"+genre)
    exact=0
    for saved,real,defined in zip(refs_saved,recorded,original["individual_instrument_tracks"]):
        require((saved["track_id"],saved["original_instrument_id"],
                 saved["resource_id"],saved["sfz_program"])==
                (real["track_id"],real["original_instrument_id"],
                 real.get("resource_id"),real.get("sfz_path"))
                and saved["track_id"]==defined["track_id"]
                and saved["original_instrument_id"]==defined["instrument_id"],
                "INSTRUMENT_ORIGINAL_MAPPING_SUBSTITUTED:"+genre)
        if saved["resource_id"] is not None:
            exact+=1
            require(saved["sfz_program"] and
                    saved["sound_source_status"]=="EXACT_REFERENCE_NEEDS_RUNTIME_AUDIO_PREFLIGHT",
                    "SOURCE_PROGRAM_PATH_MISSING:"+genre)
        else:
            require(saved["sfz_program"] is None and
                    saved["sound_source_status"]=="BLOCKED_UNVERIFIED_RECORDED_SOURCE",
                    "UNVERIFIED_INSTRUMENT_NOT_BLOCKED:"+genre)
    state=item["status"]
    require(state["genre_identity_routing"]=="ACTIVE_IN_DEVELOPMENT"
            and state["midi_inlet"]=="ACTIVE_IN_DEVELOPMENT"
            and state["own_musical_profile"]=="ORIGINAL_DEFINITION_LOADED"
            and state["original_tempo_meter_groove"]=="PRESERVED"
            and state["original_mix_and_instrument_settings"]=="UNMODIFIED"
            and state["source_seven_bar_seed"]=="PRESERVED_NOT_PROMOTED_TO_FULL_SONG"
            and state["production_enabled"] is False
            and state["all_original_recorded_tracks_have_exact_bank_references"]==
                (exact==len(recorded)),
            "UNSAFE_GENRE_ACTIVATION_FLAGS:"+genre)
    verified=genre in APPROVED_DEVELOPMENT_AUDIO
    require((state["full_recorded_audio_development_proof"]==
             "VERIFIED_ISOLATED_FULL_STEREO")==verified,
            "UNVERIFIED_GENRE_MARKED_PLAYABLE:"+genre)
    if genre in EXTERNAL_OWN_STYLE:
        require("genre_styles/" in item["genre_specific_interpreter_backend"],
                "EXTERNAL_STYLE_INTERPRETER_MISSING:"+genre)
    return deepcopy({
        "genre":genre,"family":family,"profile_id":musical["profile_id"],
        "meter_options":musical["meter_options"],
        "tempo_bpm_range":musical["tempo_bpm_range"],
        "groove_behavior":musical["groove_behavior"],
        "phrase_behavior":musical["phrase_behavior"],
        "ensemble_behavior":musical["ensemble_player_behavior"],
        "all_original_instruments":refs_saved,
        "original_full_track_count":len(recorded),
        "exact_recorded_program_references":exact,
        "missing_recorded_programs":[x["track_id"] for x in refs_saved
                                     if x["resource_id"] is None],
        "original_own_interpreter":registered["slot_file"],
        "genre_routing_active":True,
        "midi_inlet_active":True,
        "full_recorded_audio_approved_in_isolated_development":verified,
        "live_production_activated":False,
        "source_sfz_preserved":True,"mix_and_performance_settings_unchanged":True,
        "next_stage":"OWN_GENRE_PERFORMANCE_AND_ORIGINAL_SFZ_VALIDATION",
    })

def all_genre_configurations()->dict:
    index=_json(ROOT/"index.json")
    names=tuple(index["genre_to_family_file"])
    require(index["profile_count"]==55 and len(names)==55
            and len(index["family_memberships"])==13,
            "GENRE_CATALOG_NOT_55_IN_13_FAMILIES")
    configurations={name:load_genre_configuration(name) for name in names}
    require(len(configurations)==55 and
            len({v["profile_id"] for v in configurations.values()})==55,
            "NOT_55_INDEPENDENT_PROFILES")
    return configurations

def selected_composer_configuration(genre:str, runtime_profile:dict,
                                    stage3:dict)->dict:
    """Invoke at the existing Composer genre-selection boundary, NO new stage."""
    info=load_genre_configuration(genre)
    require(runtime_profile.get("profile_id")==info["profile_id"],
            "COMPOSER_RUNTIME_PROFILE_CROSS_GENRE")
    require(stage3.get("status")=="PASS","COMPOSER_STAGE3_NOT_READY")
    meter=stage3.get("meter")
    if meter is not None:
        require(meter in info["meter_options"],"GENRE_METER_NOT_OWN_SETTING")
    tempo=stage3.get("tempo_bpm")
    if tempo is not None:
        lo,hi=info["tempo_bpm_range"]
        require(lo<=tempo<=hi,"GENRE_TEMPO_NOT_OWN_SETTING")
    return info
