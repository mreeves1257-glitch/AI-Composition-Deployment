#!/usr/bin/env python3
"""Validate all 55 non-active genre 22-capability references against original profiles."""
import json
from pathlib import Path
B=Path(__file__).resolve().parents[1]/"composer_overrides/genre_styles"
load=lambda p:json.loads(p.read_text())
families={"Afrobeats_AfroLatin":3,"Classical_Acoustic":3,"Country_Bluegrass":7,"Electronic_Dance":9,"Hybrid_Custom":5,"Indie_Alternative":1,"Jazz":8,"Latin":7,"New_Age_Spiritual":2,"R_and_B_Soul_Funk_Disco":6,"Reggaeton":1,"Rock":1,"Trip_Hop":2}
stages=["SELECT_GENRE","DEFINE_MUSICAL_STRUCTURE","CHOOSE_INSTRUMENTS_AND_DRUM_KIT","COMPOSE_SEPARATE_PARTS","PERFORM_MUSICALLY","RENDER_SEPARATE_AUDIO_STEMS","GENRE_MIX_THEN_STANDALONE_3D_MIX"]
ids=[f"CAP_{i:02}" for i in range(1,23)]
def check(t,msg):assert t,msg
m=load(B/"GENRE_22_CAPABILITY_PROCEDURE_MASTER_R1.json")
check(m["capability_count"]==22 and [c["id"] for c in m["capabilities"]]==ids,"MASTER_MISSING_CAPABILITIES")
check(m["original_stages"]==stages and not m["automatic_activation"],"MASTER_INVALID")
check({p.parent.name for p in B.glob("*/GENRE_22_CAPABILITY_PROCEDURE_R1.json")}==set(families),"FAMILY_FILES_MISSING_OR_EXTRA")
total=0
for family,n in families.items():
    profile=load(B/family/"profile.json")
    old=load(B/family/"GENRE_INTERPRETER_HANDOFF_R1.json")
    add=load(B/family/"GENRE_22_CAPABILITY_PROCEDURE_R1.json")
    check(add["family"]==family and add["genres_count"]==n,"FAMILY_HEADER:"+family)
    check(not add["activation_allowed"],"MUST_REMAIN_INACTIVE:"+family)
    check(len(profile["profiles"])==len(old["genres"])==len(add["genre_records"])==n,"FAMILY_COUNT:"+family)
    oldmap={x["genre_name"]:x for x in old["genres"]}
    seen=set()
    for e in add["genre_records"]:
        name=e["genre_name"]
        check(name not in seen and name in oldmap and name in profile["profiles"],"GENRE_REFERENCE:"+family+"/"+name)
        seen.add(name)
        p=profile["profiles"][name]
        o=oldmap[name]
        check(e["profile_id"]==o["profile_id"]==p["musical_definition"]["profile_id"],"PROFILE_ID:"+family+"/"+name)
        check(e["source_of_truth"]==o["source_of_truth"],"SOURCE_XREF:"+family+"/"+name)
        check(e["capability_ids"]==ids,"22_COVERAGE:"+family+"/"+name)
        check(e["original_seven_stage_count"]==7 and p["seven_stage_plan"]["stage_order"]==stages,"SEVEN_STAGE_ORDER:"+family+"/"+name)
        check(not p["seven_stage_plan"]["enable_runtime_connections"] and not o["interpreter_stage_connected"],"UNAUTHORIZED_ACTIVATION:"+family+"/"+name)
        check("CONDITIONAL" in e["applicability_at_runtime"],"ALL_INSTRUMENTS_ASSUMED:"+family+"/"+name)
        check(e["capability_implementation_verification"]=="NOT_VERIFIED_OR_ACTIVATED_BY_THIS_PROCEDURAL_REFERENCE","MISLEADING_COMPLETION:"+family+"/"+name)
        total+=1
check(total==55,"TOTAL_55_INVALID")
print("ALL_55_22_COMPONENT_PROCEDURE_XREF_PASS",json.dumps({"families":len(families),"genre_count":total,"capabilities_each":22,"reference_checks":total*22,"original_seven_stages_preserved":True,"no_genre_activated":True}))
