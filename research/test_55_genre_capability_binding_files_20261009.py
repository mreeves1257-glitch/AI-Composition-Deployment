"""Check all 55 independently identified genres reach all 22 common handlers."""
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1]
HOME=ROOT/"composer_overrides"/"genre_styles"
sys.path.insert(0,str(ROOT/"composer_overrides"))
from genre_styles.shared_interpreter_router import CAPABILITY_IDS,connect_all_genres
from genre_styles.shared_musical_grammar import compile_musical_plan
from genre_styles.shared_capability_execution import HANDLERS
index=json.loads((HOME/"index.json").read_text())
assert len(index["genre_to_family_file"])==55
assert len(index["family_memberships"])==13
assert tuple(HANDLERS)==CAPABILITY_IDS
seen=set()
for family,members in index["family_memberships"].items():
    directory=HOME/family
    bind=json.loads((directory/"GENRE_CAPABILITY_EXECUTION_BINDINGS_R1.json").read_text())
    assert bind["family"]==family and bind["genre_count"]==len(members)
    assert bind["shared_interpreter_only"] is True
    assert bind["original_stage_connections_activated"] is False
    assert bind["developer_mode_connected"] is True
    assert bind["exact_production_audio_verified"] is False
    assert {x["genre_name"] for x in bind["per_genre"]}==set(members)
    profile=json.loads((directory/"profile.json").read_text())
    assert set(profile["profiles"])==set(members)
    for item in bind["per_genre"]:
        genre=item["genre_name"]
        assert genre not in seen;seen.add(genre)
        assert item["profile_id"]==profile["profiles"][genre]["musical_definition"]["profile_id"]
        assert item["source_profile_file"]=="composer_overrides/genre_styles/"+family+"/profile.json"
        assert item["original_rules_pointer"]=="/profiles/"+genre.replace("~","~0").replace("/","~1")+"/musical_definition"
        assert item["original_stage_order_pointer"]=="/profiles/"+genre.replace("~","~0").replace("/","~1")+"/seven_stage_plan/stage_order"
        assert item["execution_capabilities"]=="CAP_01_TO_CAP_22_VIA_ONE_SHARED_DISPATCH"
        assert item["genre_specific_rules_source"]=="ORIGINAL_PROFILE_LOOKUP_NOT_COPIED"
        assert item["independently_verified_finished_music"] is False
        assert item["live_enabled"] is False
        source=profile["profiles"][genre]["musical_definition"]
        p=compile_musical_plan(genre,meter=source["meter_options"][0],
                               tempo_bpm=source["tempo_bpm_range"][0],bars=1)
        result=p["capability_execution"]
        assert result["genre_binding_validated"]
        assert result["genre_binding_file"]==family+"/GENRE_CAPABILITY_EXECUTION_BINDINGS_R1.json"
        assert result["genre"]==genre
        assert tuple(result["capabilities"])==CAPABILITY_IDS
        assert result["ready_for_live_deployment"] is False
assert len(seen)==55==len(connect_all_genres())
rock=HOME/"Rock"
for filename in ("rock_pinned_mma_interpreter.py","rock_strum_phrase_performance.py"):
    assert not (rock/filename).exists()
    assert (ROOT/"research"/"archived_rock_20261009"/"original"/filename).is_file()
print("55_GENRE_13_FAMILY_22_EXECUTABLE_CAPABILITY_BINDINGS_PASS",
      {"genres":55,"families":13,"capability_links":55*22,
       "rock_uses_same_interpreter":True,"live_verified":False})
