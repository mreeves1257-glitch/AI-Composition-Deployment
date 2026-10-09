#!/usr/bin/env python3
"""Nonproduction proof: all 55 genres resolve to a single shared package.

Check original profiles, Stage 3 -> 4 MIDI event contract, and fail-closed behavior.
No actual sound renderer, live Composer/Plug, external GPL engine or source WAV.
"""
from __future__ import annotations
import json
from pathlib import Path
from composer_overrides.genre_styles import registry
from composer_overrides.genre_styles.shared_interpreter_router import (
    HandoffError, STAGE_NAMES, CAP_IDS, linked_genres, stage3_to_stage4,
)

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"composer_overrides"/"genre_styles"
def expect_error(callback, exact_message):
    try:
        callback()
    except HandoffError as exc:
        assert str(exc)==exact_message, (exact_message,str(exc))
        return
    raise AssertionError("DID_NOT_FAIL_CLOSED:"+exact_message)

index=json.loads((BASE/"index.json").read_text())
bindings=json.loads((BASE/"SHARED_INTERPRETER_ALL_55_LINKS_R1.json").read_text())
catalog=json.loads((BASE/"SHARED_INTERPRETER_EXTERNAL_BACKEND_CATALOG_R1.json").read_text())
assert bindings["genre_count"]==55 and bindings["family_count"]==13
assert len(bindings["links"])==len(linked_genres())==55
assert set(x["genre"] for x in bindings["links"])==set(linked_genres())
assert len({x["shared_router"] for x in bindings["links"]})==1
assert len({x["stage3_to4"] for x in bindings["links"]})==1
assert catalog["default_backend"].startswith("NONE")
assert all(not x["runtime_loaded"] for x in catalog["external_research_archives"])
profiles={}
for n in linked_genres():
    binding=next(x for x in bindings["links"] if x["genre"]==n)
    route=registry.get_shared_musical_interpreter_link(n)
    assert route["genre"]==n and route["shared_adapter_linked"] is True
    assert len(route["capability_ids"])==22 and tuple(route["capability_ids"])==CAP_IDS
    assert not route["score_backend_activated"] and not route["live_runtime_deployed"]
    assert route["interpreter_to_composer_boundary"]=="BETWEEN_ORIGINAL_STAGE_03_AND_04"
    assert route["original_profile_path"]==binding["profile_file"]
    assert index["genre_to_family_file"][n]==binding["profile_file"].split("genre_styles/",1)[1]
    assert route["stage4_owner"]=="COMPOSE_SEPARATE_PARTS" and route["stage5_owner"]=="PERFORM_MUSICALLY"
    assert len(route["meter_options"])>=1
    assert route["stage2_original_musical_definition"]["profile_id"]==route["profile_id"]
    family=json.loads((BASE/index["genre_to_family_file"][n]).read_text())
    assert family["profiles"][n]["seven_stage_plan"]["stage_order"]==list(STAGE_NAMES)
    assert all(not e["connection_activated"] for e in family["profiles"][n]["seven_stage_plan"]["stages"])
    assert family["profiles"][n]["seven_stage_plan"]["auto_apply"] is False
    profiles[n]=route
assert len(profiles)==55 and len({r["family"] for r in profiles.values()})==13
assert "3/4" in profiles["Jazz Waltz"]["meter_options"]
assert "3/4" in profiles["WALTZ"]["meter_options"]
assert "percussion absent" in profiles["PIANIST"]["stage2_original_musical_definition"]["percussion_behavior_if_applicable"]
assert "clave" in profiles["Salsa"]["stage2_original_musical_definition"]["percussion_behavior_if_applicable"].lower()
assert "swing" in profiles["Swing"]["stage2_original_musical_definition"]["groove_behavior"].lower()
# Isolated schema and mapping proofs. TEST_SOURCE is not a real installed SFZ.
examples={}
for g in ("ROCK","Swing","Jazz Waltz","Salsa","PIANIST"):
    r=profiles[g]
    role=r["stage3_original_roles"][0]
    meter=r["meter_options"][0]
    bpm=float(r["tempo_bpm_range"][0])
    selected=[{"track_id":role,"source_id":"ISOLATED_TEST_SOURCE_NOT_A_REAL_SFZ",
               "min_midi_note":50,"max_midi_note":83,"supported_articulations":["normal"]}]
    event=[{"track_id":role,"midi_note":60,"velocity":85,
            "start_beat":1.5,"duration_beats":0.75,"articulation":"normal"}]
    structure={"meter":meter,"tempo_bpm":bpm,"section":"INTRO"}
    score=registry.handoff_shared_interpreted_events(
        g,song_structure=structure,selected_instruments=selected,arranger_events=event)
    assert score["genre"]==g and len(score["stage4_composer_input_events"])==1
    assert score["stage4_composer_input_events"][0]["source_id"]=="ISOLATED_TEST_SOURCE_NOT_A_REAL_SFZ"
    assert not score["live_composer_connected"] and score["stage5_performance_required"]
    examples[g]={"role":role,"meter":meter,"one_note_validated":True}
    expect_error(lambda:stage3_to_stage4(
        g,song_structure=structure,selected_instruments=selected,
        arranger_events=[{**event[0],"track_id":"WRONG_ROLE"}]),
        "INTERPRETER_SELECTED_UNVERIFIED_PART")
    expect_error(lambda:stage3_to_stage4(
        g,song_structure=structure,selected_instruments=selected,
        arranger_events=[{**event[0],"midi_note":100}]),
        "MIDI_OUTSIDE_SELECTED_REAL_SAMPLE_RANGE")
    expect_error(lambda:stage3_to_stage4(
        g,song_structure=structure,selected_instruments=selected,
        arranger_events=[{**event[0],"articulation":"unverified-vibrato"}]),
        "ARTICULATION_NOT_SUPPORTED_BY_SELECTED_SOURCE")
    expect_error(lambda:stage3_to_stage4(
        g,song_structure=structure,selected_instruments=[{**selected[0],"source_id":""}],
        arranger_events=event), "UNVERIFIED_RESOURCE_ID")
expect_error(lambda:registry.get_shared_musical_interpreter_link("UNKNOWN GENRE"),
             "UNKNOWN_OR_UNFILED_GENRE")
summary={"status":"SHARED_INTERPRETER_ALL_55_REGISTRY_AND_TYPED_MIDI_HANDOFF_PASS",
         "original_genre_count":55,"family_count":13,"source_22_gate_references":55*22,
         "one_shared_router":True,"all_original_7_stages_intact":True,
         "external_runtimes_installed":False,"deployed_composer_modified":False,
         "real_audio_or_finished_song_verified":False,"example_stage4_midi_event_contracts":examples}
print("SHARED_INTERPRETER_ALL_55_LINKS_PASS",json.dumps(summary,sort_keys=True))
