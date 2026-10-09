#!/usr/bin/env python3
"""Read-only uniform 55-genre connection integrity test. Does not activate music."""
import json,sys
from pathlib import Path
B=Path(__file__).resolve().parents[1]/"composer_overrides"/"genre_styles"
sys.path.insert(0,str(B.parent))
from genre_styles.shared_interpreter_router import connect_all_genres,ORIGINAL_STAGE_ORDER,CAPABILITY_IDS
load=lambda p:json.loads(p.read_text(encoding="utf-8"))
index=load(B/"index.json")
master=load(B/"GENRE_22_CAPABILITY_PROCEDURE_MASTER_R1.json")
template=load(B/"Jazz"/"GENRE_INTERPRETER_HANDOFF_R1.json")
family_fields=list(template); genre_fields=list(template["genres"][0])
source_fields=list(template["genres"][0]["source_of_truth"])
families={}; names=set()
for d in sorted(B.iterdir()):
    if not (d/"profile.json").is_file():continue
    family=d.name;p=load(d/"profile.json")
    h=load(d/"GENRE_INTERPRETER_HANDOFF_R1.json")
    c=load(d/"GENRE_22_CAPABILITY_PROCEDURE_R1.json")
    assert list(h)==family_fields and h["family_name"]==h["family_directory"]==family
    assert h["source_profile_file"]=="composer_overrides/genre_styles/"+family+"/profile.json"
    assert h["original_stage_count"]==7 and h["original_connections_activated"] is False
    assert c["capability_count"]==master["capability_count"]==22 and c["activation_allowed"] is False
    bycap={x["genre_name"]:x for x in c["genre_records"]}
    assert len(bycap)==len(h["genres"])==len(p["profiles"])==h["profile_count"]
    assert {x["genre_name"] for x in h["genres"]}==set(bycap)==set(p["profiles"])
    for x in h["genres"]:
        name=x["genre_name"]; assert name not in names; names.add(name)
        assert list(x)==genre_fields and list(x["source_of_truth"])==source_fields
        pointer="/profiles/"+name.replace("~","~0").replace("/","~1")
        assert x["source_of_truth"]==bycap[name]["source_of_truth"]=={
            "file":h["source_profile_file"],"json_pointer":pointer+"/musical_definition",
            "stage_pointer":pointer+"/seven_stage_plan","read_original_values_at_runtime":True}
        assert x["profile_id"]==p["profiles"][name]["musical_definition"]["profile_id"]==bycap[name]["profile_id"]
        assert p["profiles"][name]["seven_stage_plan"]["stage_order"]==list(ORIGINAL_STAGE_ORDER)
        assert p["profiles"][name]["seven_stage_plan"]["enable_runtime_connections"] is False
        assert x["isolated_slot"]=="BETWEEN_ORIGINAL_STAGE_03_AND_04"
        assert x["accepts_form_and_meter_from"]=="ORIGINAL_STAGE_02_DEFINE_MUSICAL_STRUCTURE"
        assert x["accepts_resource_bindings_from"]=="ORIGINAL_STAGE_03_CHOOSE_INSTRUMENTS_AND_DRUM_KIT"
        assert x["passes_validated_role_plan_to"]=="ORIGINAL_STAGE_04_COMPOSE_SEPARATE_PARTS"
        assert x["expression_owned_by"]=="ORIGINAL_STAGE_05_PERFORM_MUSICALLY"
        assert x["authoring_policy"]=="GENRE_SPECIFIC_ONLY_NO_ROCK_FALLBACK"
        assert x["typed_interpreter_backend"]=="UNSELECTED_PENDING_DISTINCT_GENRE_AUDITION"
        assert x["interpreter_stage_connected"] is False and x["renderer_connected"] is False
        assert bycap[name]["capability_ids"]==list(CAPABILITY_IDS)
        assert index["genre_to_family_file"][name]==family+"/profile.json"
    families[family]=len(h["genres"])
assert len(families)==13 and len(names)==sum(families.values())==55
routes=connect_all_genres()
assert set(routes)==names and all(x["live_genre_enabled"] is False for x in routes.values())
print("UNIFORM_GENRE_CONNECTIONS_PASS: 13 families, 55 genres, 7 stages, 1210 capability references, one shared data router; no live enablement")
