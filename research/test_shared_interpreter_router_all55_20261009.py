"""All 55 shared interpreter links: live executable data-router, no synthetic performance."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "composer_overrides"))
from genre_styles.shared_interpreter_router import (
    CAPABILITY_IDS, InterpreterConnectionError, ORIGINAL_STAGE_ORDER,
    connect_all_genres, listed_genres, route_to_shared_interpreter,
)

links = connect_all_genres()
assert len(links) == 55 == len(listed_genres())
families = {r["family"] for r in links.values()}
assert len(families) == 13, families
ids = [r["genre_profile_id"] for r in links.values()]
assert len(ids) == len(set(ids)) == 55
for name, plan in links.items():
    assert plan["genre"] == name
    assert plan["link_state"] == "CONNECTED_STAGE_3_TO_4_DATA_ROUTER"
    assert plan["next_stage"] == "COMPOSE_SEPARATE_PARTS"
    assert plan["performance_stage"] == "PERFORM_MUSICALLY"
    assert plan["mixer_stage"] == "GENRE_MIX_THEN_STANDALONE_3D_MIX"
    assert plan["original_7_stages"] == list(ORIGINAL_STAGE_ORDER)
    assert len(plan["capability_requirements"]) == 22
    assert [c["id"] for c in plan["capability_requirements"]] == list(CAPABILITY_IDS)
    assert plan["source_sfzs_unchanged"] is True
    assert plan["musical_notes_authorized"] is False
    assert plan["live_genre_enabled"] is False
    assert plan["full_song_audio_verified"] is False
    assert "profile_id" in plan["genre_specific_musical_intentions"]
    assert plan["genre_specific_musical_intentions"]["profile_id"] == plan["genre_profile_id"]
    assert plan["selected_original_instrument_ids"] == []

def reject(fn):
    try: fn()
    except InterpreterConnectionError: return True
    raise AssertionError("EXPECTED_A_SAFETY_REJECTION")
assert reject(lambda: route_to_shared_interpreter("NoSuchGenre"))
assert reject(lambda: route_to_shared_interpreter("ROCK", runtime_profile={"profile_id":"FAKE"}))
assert reject(lambda: route_to_shared_interpreter("ROCK",original_stage3_result={"status":"NOT_READY"}))
assert reject(lambda: route_to_shared_interpreter("ROCK",original_stage3_result={"status":"PASS","meter":"3/4"}))
assert reject(lambda: route_to_shared_interpreter("ROCK",original_stage3_result={"status":"PASS","tempo_bpm":280}))
assert reject(lambda: route_to_shared_interpreter("ROCK",original_stage3_result={"status":"PASS","palette":["drums","drums"]}))
rock=route_to_shared_interpreter("ROCK",original_stage3_result={"status":"PASS","tempo_bpm":145,"meter":"4/4","palette":["electric_guitar","electric_bass","drums"]})
assert rock["selected_original_instrument_ids"] == ["electric_guitar","electric_bass","drums"]
assert rock["selected_meter"] == "4/4"
assert rock["live_genre_enabled"] is False
# 3/4 meters must survive for actual genres, not overwritten by other keyboard sources.
waltz=route_to_shared_interpreter("Jazz Waltz",original_stage3_result={"status":"PASS","meter":"3/4"})
assert waltz["selected_meter"]=="3/4",waltz
print("SHARED_INTERPRETER_55_EXPLICIT_RUNTIME_ROUTES_PASS",json.dumps({"genres":len(links),"families":len(families),"stage_3_to_4_links":len(links),"capability_links":len(links)*22,"original_seven_stages_preserved":True,"recorded_instruments_preserved":True,"all_artifact_generator_flags_protected":True,"negative_safety_tests":6,"rock_stage3_palette_forwarded":True,"jazz_waltz_3_4_preserved":True},sort_keys=True))
