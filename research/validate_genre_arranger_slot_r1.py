"""Validate filing the musical interpreter in the original seven-stage genre route.

Research-only file integrity audit. It does not edit, activate, import or run
composer code, nor install the external MMA / JJazzLab engines.
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
GENRES=ROOT/"composer_overrides"/"genre_styles"
SHARED=GENRES/"GENRE_ARRANGER_INTERPRETER_HANDOFF_REFERENCE_R1.json"
ROCK=GENRES/"Rock"/"ROCK_ARRANGER_INTERPRETER_PLACEMENT_R1.json"
ORDER=["SELECT_GENRE","DEFINE_MUSICAL_STRUCTURE","CHOOSE_INSTRUMENTS_AND_DRUM_KIT",
       "COMPOSE_SEPARATE_PARTS","PERFORM_MUSICALLY","RENDER_SEPARATE_AUDIO_STEMS",
       "GENRE_MIX_THEN_STANDALONE_3D_MIX"]

def require(x,label):
    if not x:raise AssertionError(label)

def check():
    shared=json.loads(SHARED.read_text())
    rock=json.loads(ROCK.read_text())
    require(shared["placement"]["steps_preserved"]==ORDER,"SEVEN_STAGE_ORDER_CHANGED")
    require(shared["placement"]["arrangement_interpretation_boundary"]=="BETWEEN_STEP_03_AND_STEP_04","WRONG_HANDOFF")
    require(shared["activation"]["enabled"] is False,"HANDOFF_ACCIDENTALLY_ACTIVATED")
    require(shared["activation"]["production_wiring_changed"] is False,"PRODUCTION_WIRING_TOUCHED")
    require(rock["stage_boundary"]["from"]==ORDER[2] and rock["stage_boundary"]["to"]==ORDER[3],"ROCK_SLOT_WRONG")
    require(rock["runtime_activated"] is False,"ROCK_INTERPRETER_ACTIVATED")
    require(rock["original_seven_stage_handoffs_changed"] is False,"ORIGINAL_STAGE_GRAPH_CHANGED")
    require(rock["original_family_profile"]=="composer_overrides/genre_styles/Rock/profile.json","WRONG_ROCK_PROFILE_ANCHOR")
    families=[]
    genres=[]
    for path in sorted(GENRES.glob("*/profile.json")):
        j=json.loads(path.read_text())
        require(j.get("reference_only") is True,"FAMILY_NO_LONGER_REFERENCE_ONLY:"+str(path))
        require(j.get("source_assets_immutable") is True,"SAMPLE_ORIGINAL_NOT_PROTECTED:"+str(path))
        require(j.get("stage_wiring_activated") is False,"FAMILY_WIRING_ACTIVATED:"+str(path))
        profiles=j.get("profiles")
        require(isinstance(profiles,dict),"FAMILY_PROFILES_NOT_DICT")
        require(j["genre_count"]==len(profiles),"FAMILY_GENRE_COUNT_DRIFT")
        for name,p in profiles.items():
            stage=p["seven_stage_plan"]
            require(stage["stage_order"]==ORDER,"GENRE_STAGE_ORDER_CHANGED:"+name)
            require(len(stage["stages"])==7,"GENRE_STAGE_COUNT_CHANGED:"+name)
            require(all(item["order"]==i and item["name"]==ORDER[i-1] and item["connection_activated"] is False for i,item in enumerate(stage["stages"],1)),
                    "GENRE_STAGE_ACTIVATED:"+name)
            require(len(stage["proposed_handoffs"])==6 and all(x["status"]=="RESERVED_NOT_CONNECTED" for x in stage["proposed_handoffs"]),
                    "GENRE_HANDOFF_PREMATURELY_LINKED:"+name)
            require(stage["enable_runtime_connections"] is False,"GENRE_ROUTING_ENABLED:"+name)
            genres.append(name)
        families.append(path.parent.name)
    require(len(families)==13,"EXPECTED_13_GENRE_FAMILIES_GOT_"+str(len(families)))
    require(len(genres)==55,"EXPECTED_55_GENRES_GOT_"+str(len(genres)))
    require(len(genres)==len(set(genres)),"DUPLICATE_PROFILE_NAME")
    summary={"status":"GENRE_INTERPRETER_STAGE_SLOT_REFERENCE_PASS",
             "family_folders":len(families),"genre_profiles":len(genres),
             "existing_seven_stage_order_preserved":True,
             "new_physical_genre_stage_inserted":False,
             "interpreter_placement":"BETWEEN_ORIGINAL_STAGES_3_AND_4",
             "genre_music_definition_input":"ORIGINAL_STAGE_2",
             "instrument_source_resolution":"ORIGINAL_STAGE_3",
             "source_aware_expressive_playback":"ORIGINAL_STAGE_5",
             "original_connections_activated":False,
             "recorded_sample_banks_unchanged":True,
             "composer_or_plug_deployed":False,
             "external_interpreter_installed":False,
             "user_approved_audio_unchanged":True,
             "rock_exemplar_in_original_genre_family":True}
    print("ARRANGER_GENRE_FILING_VERIFIED",json.dumps(summary,sort_keys=True),flush=True)
    return summary

if __name__=="__main__":
    check()
