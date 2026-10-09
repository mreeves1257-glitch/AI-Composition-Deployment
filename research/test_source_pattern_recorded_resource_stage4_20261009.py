"""Prove all 55 genre-owned source roles and guarded Stage4 Composer candidate events."""
import sys,unittest,json,copy
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/"composer_overrides"))
from genre_styles.shared_interpreter_router import (connect_all_genres,InterpreterConnectionError)
from genre_styles.source_pattern_library import compile_original_source_seed
from genre_styles.source_pattern_resource_handoff import (
 PINNED,CONTEXT_PINNED,ORIGINAL_SOURCE_PROVENANCE,load_binding_file,map_source_roles)
from genre_styles.source_pattern_composer_handoff import (
 prepare_source_pattern_composer_handoff)

def rock_fixture():
    defs=[
      ("electric_bass_guitar","KARORYFER_GROWLYBASS_V1_002","growlybass_clean.sfz"),
      ("electric_guitar:RHYTHM_POWER_CHORDS","KARORYFER_SHINYGUITAR","Programs/composer-electric.sfz"),
      ("kick_drum_rock","KARORYFER_BIG_RUSTY_DRUMS","Programs/composer-kick-lite.sfz"),
      ("snare_drum","KARORYFER_BIG_RUSTY_DRUMS","Programs/composer-snare-lite.sfz"),
      ("hi_hat","KARORYFER_BIG_RUSTY_DRUMS","Programs/composer-hihat-lite.sfz")]
    return {identity:{"resource_id":resource,"preferred_mapping":sfz,
             "resource_type":"SFZ_SAMPLE_LIBRARY",
             "fallback_policy":"NO_SYNTHETIC_SUBSTITUTION",
             "library":ORIGINAL_SOURCE_PROVENANCE[resource][0],
             "license":ORIGINAL_SOURCE_PROVENANCE[resource][1]}
        for identity,resource,sfz in defs}

class InstrumentToCompositionTests(unittest.TestCase):
 def test_all_55_genre_roles_are_mapped_or_explicitly_blocked(self):
    routes=connect_all_genres()
    self.assertEqual(len(routes),55)
    count=ready=blocked=0
    signatures=set()
    for genre in routes:
      with self.subTest(genre=genre):
        plan=compile_original_source_seed(genre)
        ref,link=load_binding_file(genre)
        self.assertEqual(ref["profile_id"],plan["genre_profile_id"])
        self.assertEqual(set(ref["role_bindings"]),
                         {x["role"] for x in plan["roles"]})
        self.assertEqual(link["genre"],genre) if "genre" in link else None
        result=prepare_source_pattern_composer_handoff(plan,
                     existing_events=[{"track_id":"OLD","instrument_id":"OLD",
                                       "start_beat":0,"midi":60,"velocity":90}],
                     target_bindings={})
        self.assertEqual(result["status"],"BLOCKED_INCOMPLETE_EXACT_INSTRUMENT_MAPPING")
        self.assertEqual(result["candidate_stage4_events"],[])
        self.assertEqual(result["original_events_count"],1)
        self.assertTrue(result["existing_composer_events_unchanged"])
        self.assertFalse(result["audio_render_authorized"])
        statuses={x["status"] for x in result["routing"]["roles"]}
        self.assertTrue(statuses.issubset({
            "BLOCKED_NO_INSTALLED_REGISTRY_BINDING",
            "BLOCKED_NO_AUTHORITATIVE_SOURCE_PROGRAM"}))
        count+=len(ref["role_bindings"])
        blocked+=sum(x["lookup_policy"]=="BLOCKED_UNVERIFIED"
                    for x in ref["role_bindings"].values())
        ready+=sum(x["lookup_policy"] in ("EXACT_ID","EXACT_CONTEXTUAL")
                    for x in ref["role_bindings"].values())
        signatures.add((genre,tuple(sorted(ref["role_bindings"]))))
    self.assertEqual(len(signatures),55)
    self.assertEqual(ready+blocked,count)
    self.assertEqual(count,234)
    self.assertEqual(ready,104)
    self.assertEqual(blocked,130)
 def test_rock_exact_original_recorded_program_pins_and_source_score(self):
    plan=compile_original_source_seed("ROCK")
    stage3={"status":"PASS","meter":"4/4","tempo_bpm":120,
            "palette":["electric_guitar","electric_bass","drums"]}
    original=[{"track_id":"LEGACY_BASS","instrument_id":"electric_bass_guitar",
               "start_beat":0,"midi":40,"velocity":91}]
    preserved=copy.deepcopy(original)
    mapping=map_source_roles(plan,stage3=stage3,target_bindings=rock_fixture())
    self.assertEqual(mapping["exact_registry_references"],5)
    self.assertEqual(mapping["unresolved_roles"],[])
    self.assertEqual(mapping["unsupported_percussion_notes"],[])
    self.assertTrue(mapping["source_program_identification_complete"])
    self.assertFalse(mapping["playback_preflight_complete"])
    proposal=prepare_source_pattern_composer_handoff(
       plan,original_stage3_result=stage3,existing_events=original,
       target_bindings=rock_fixture())
    self.assertEqual(original,preserved)
    self.assertEqual(proposal["status"],
        "CANDIDATE_STAGE4_EVENTS_READY_SOURCE_PREFLIGHT_PENDING")
    self.assertEqual(proposal["candidate_event_count"],len(plan["symbolic_note_events"]))
    self.assertGreater(proposal["candidate_event_count"],30)
    self.assertFalse(proposal["audio_render_authorized"])
    self.assertTrue(proposal["candidate_is_not_live_events"])
    byrole={}
    for item in proposal["candidate_stage4_events"]:
       byrole.setdefault(item["track_id"],set()).add(item["instrument_id"])
       self.assertEqual(item["composer_stage"],"COMPOSE_SEPARATE_PARTS")
       self.assertEqual(item["audit_status"],"PROPOSED_NOT_APPROVED")
       if item["track_id"]=="KICK":self.assertEqual(item["midi"],36)
       if item["track_id"]=="SNARE":self.assertEqual(item["midi"],38)
       if item["track_id"]=="HAT":self.assertEqual(item["midi"],42)
    self.assertEqual(byrole["HARMONY"],{"electric_guitar:RHYTHM_POWER_CHORDS"})
    self.assertEqual(byrole["BASS"],{"electric_bass_guitar"})
    self.assertEqual(byrole["KICK"],{"kick_drum_rock"})
 def test_invalid_source_and_unselected_instruments_block(self):
    plan=compile_original_source_seed("ROCK")
    bad=rock_fixture()
    bad["snare_drum"]["resource_id"]="FAKE_SYNTH"
    response=map_source_roles(plan,target_bindings=bad)
    self.assertIn("SNARE",response["unresolved_roles"])
    self.assertFalse(response["source_program_identification_complete"])
    wrong_license=rock_fixture()
    wrong_license["snare_drum"]["license"]="UNAUTHORIZED"
    license_result=map_source_roles(plan,target_bindings=wrong_license)
    self.assertIn("SNARE",license_result["unresolved_roles"])
    a=prepare_source_pattern_composer_handoff(plan,target_bindings=bad)
    self.assertEqual(a["candidate_stage4_events"],[])
    b=map_source_roles(plan,stage3={"status":"PASS","palette":["electric_guitar","drums"]},
                       target_bindings=rock_fixture())
    self.assertIn("BASS",b["unresolved_roles"])
    self.assertFalse(b["source_program_identification_complete"])
    for invalid in ({"status":"FAIL","palette":[]},
        {"status":"PASS","palette":["drums","drums"]}):
       with self.assertRaises(InterpreterConnectionError):
         map_source_roles(plan,stage3=invalid,target_bindings=rock_fixture())
 def test_specific_source_note_incompatible_instrument_is_not_faked(self):
    plan=compile_original_source_seed("Salsa")
    result=map_source_roles(plan,target_bindings=rock_fixture())
    self.assertFalse(result["source_program_identification_complete"])
    self.assertIn("CLAVE",result["unresolved_roles"])
    self.assertIn("SHAKER",result["unresolved_roles"])
    solo=compile_original_source_seed("PIANIST")
    pianist=prepare_source_pattern_composer_handoff(solo,target_bindings=rock_fixture())
    self.assertEqual(pianist["candidate_stage4_events"],[])
    self.assertEqual({x["original_instrument_id"] for x in pianist["routing"]["roles"]},{"piano"})
    self.assertFalse(pianist["audio_render_authorized"])
if __name__=="__main__":unittest.main(verbosity=2)
