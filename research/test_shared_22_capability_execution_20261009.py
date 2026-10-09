"""Proof of 22 real shared callable handlers with safe source/live failure gates."""
from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"composer_overrides"))
from genre_styles.shared_capability_execution import (HANDLERS,evaluate_22_capabilities)
from genre_styles.shared_interpreter_router import (
    CAPABILITY_IDS,connect_all_genres,InterpreterConnectionError)
from genre_styles.shared_musical_grammar import compile_musical_plan

def rock_plan():
    return compile_musical_plan(
        "ROCK",meter="4/4",tempo_bpm=120,bars=2,
        sections=[{"name":"A","bars":2,"variation_by_role":{"HARMONY":"intro"}}],
        chords=[{"bar":0,"symbol":"C"},{"bar":1,"symbol":"G7"}],
        roles=[{"role":"HARMONY","instrument_id":"electric_guitar",
                "playable_midi_range":[40,90]}],
        patterns=[{"role":"HARMONY","kind":"CHORD_RELATIVE",
          "retrigger":"STOP_AT_CHORD",
          "variations":{"intro":[{"beat":0,"duration":1,"degree":1,
                                   "octave":4,"velocity":84}]}}])
MANIFEST={
"HARMONY":{
  "instrument_id":"electric_guitar",
  "resource_id":"TEST_SAMPLE_RECORDING",
  "source_type":"SFZ_SAMPLE_LIBRARY",
  "program":"fixture.sfz",
  "source_verified":True,
  "open_string_midi":[40,45,50,55,59,64],
  "verified_articulations":{
    "vibrato_depth":{"type":"CC","controller":1}},
  "verified_cc":[1],
  "source_sha256":"INDEPENDENT_CHECKSUM_FIXTURE_ONLY",
  "stem_id":"HARMONY",
  "sample_lifetime":{"note_off_action":"RELEASE_ENVELOPE","loop_validated":False},
  "verified_drum_note_map":{"36":36},
  "verified_round_robin_variants":3,
  "mpe_verified":True
}}

class SharedCapabilityTests(unittest.TestCase):
    def test_all_55_have_22_real_handlers(self):
        self.assertEqual(tuple(HANDLERS),CAPABILITY_IDS)
        routes=connect_all_genres()
        self.assertEqual(len(routes),55)
        for name,ref in routes.items():
            meter=ref["genre_specific_musical_intentions"]["meter_options"][0]
            tempo=ref["genre_specific_musical_intentions"]["tempo_bpm_range"][0]
            plan=compile_musical_plan(name,meter=meter,tempo_bpm=tempo,bars=1)
            o=plan["capability_execution"]
            with self.subTest(genre=name):
                self.assertEqual(o["genre"],name)
                self.assertEqual(o["capability_count"],22)
                self.assertEqual(tuple(o["capabilities"]),CAPABILITY_IDS)
                self.assertTrue(o["all_handlers_connected"])
                self.assertFalse(o["audio_verified"])
                self.assertFalse(o["ready_for_live_deployment"])
                self.assertTrue(all(c["handler"] and c["state"] and
                                    c["live_verified"] is False
                                    for c in o["capabilities"].values()))
                self.assertEqual(plan["source_path"],ref["source_path"])
    def test_rock_and_jazz_both_use_same_capability_handlers(self):
        rock=compile_musical_plan("ROCK",meter="4/4",tempo_bpm=120,bars=1)
        jazz=compile_musical_plan("Jazz Ballad",meter="4/4",tempo_bpm=60,bars=1)
        self.assertEqual(tuple(rock["capability_execution"]["capabilities"]),
                         tuple(jazz["capability_execution"]["capabilities"]))
        self.assertNotEqual(rock["genre_rules"],jazz["genre_rules"])
    def test_note_fsm_and_timed_messages_without_audio(self):
        plan=rock_plan()
        result=plan["capability_execution"]["capabilities"]
        self.assertEqual(result["CAP_11"]["state"],"SYMBOLIC_EXECUTABLE")
        self.assertEqual(len(result["CAP_11"]["artifact"]["events"]),4)
        self.assertEqual(result["CAP_15"]["state"],"SYMBOLIC_MIDI_MESSAGES_READY")
        msg=result["CAP_15"]["artifact"]["messages"]
        self.assertEqual([x["type"] for x in msg],
                         ["note_on","note_off","note_on","note_off"])
        self.assertEqual(result["CAP_16"]["state"],"BLOCKED_RESOURCE_EVIDENCE")
        self.assertFalse(plan["recorded_audio_authorized"])
    def test_verified_instrument_maps_are_used_not_invented(self):
        plan=rock_plan()
        a=evaluate_22_capabilities(plan,resources=MANIFEST,
            requests={
              "guitar_strums":[{
                "role":"HARMONY","direction":"DOWN",
                "strings":[{"string":0,"fret":0,"midi":40},
                           {"string":1,"fret":2,"midi":47}]}],
              "articulations":[{"role":"HARMONY","gesture":"vibrato_depth"}],
              "phrase_shapes":[{"role":"HARMONY","start_beat":0,
                               "duration_beats":2,"start_level":75,"end_level":90}],
              "midi_controls":[{"role":"HARMONY","beat":"1/2",
                                "controller":1,"value":88}],
              "drum_strikes":[{"role":"HARMONY","source_note":36,
                               "beat":1,"velocity":85}],
              "per_note_controls":[{"role":"HARMONY","note_id":1,"channel":2}]
            })["capabilities"]
        for k in ("CAP_12","CAP_13","CAP_14","CAP_15","CAP_16",
                  "CAP_17","CAP_18","CAP_19","CAP_20"):
            self.assertNotIn(a[k]["state"],("CONNECTED_INPUT_PENDING",
                "BLOCKED_SAMPLE_LIFETIME","BLOCKED_RESOURCE_EVIDENCE"))
        self.assertEqual(a["CAP_12"]["artifact"][0]["string_order"],[0,1])
        self.assertEqual(a["CAP_18"]["artifact"][0]["destination_note"],36)
        self.assertEqual(a["CAP_15"]["artifact"]["messages"][1]["type"],"control_change")
        self.assertFalse(a["CAP_20"]["live_verified"])
    def test_fail_closed_on_unverified_samples_and_controls(self):
        plan=rock_plan()
        for requests in (
            {"midi_controls":[{"role":"HARMONY","beat":0,
                               "controller":74,"value":99}]},
            {"articulations":[{"role":"HARMONY","gesture":"imaginary_slide"}]},
            {"guitar_strums":[{"role":"HARMONY","direction":"DOWN",
                              "strings":[{"string":0,"fret":3,"midi":40}]}]},
            {"drum_strikes":[{"role":"HARMONY","source_note":54,
                              "beat":0,"velocity":50}]},
            {"per_note_controls":[{"role":"HARMONY","note_id":1,"channel":2},
                                  {"role":"HARMONY","note_id":2,"channel":2}]}
        ):
            with self.subTest(requests=requests),self.assertRaises(InterpreterConnectionError):
                evaluate_22_capabilities(plan,resources=MANIFEST,requests=requests)
        with self.assertRaises(InterpreterConnectionError):
            evaluate_22_capabilities(plan,resources={"HARMONY":dict(
                MANIFEST["HARMONY"],source_verified=False)},requests={
                "articulations":[{"role":"HARMONY","gesture":"vibrato_depth"}]})
    def test_audio_and_live_receipts_are_not_self_verifying(self):
        plan=rock_plan()
        assertplan=evaluate_22_capabilities(plan,resources=MANIFEST,requests={
            "audio_evidence":{"source_identity":"receipt","render_report":"receipt",
              "stem_integrity":"receipt","master_integrity":"receipt",
              "genre_listening_review":"receipt"},
            "live_handoff":{"composer_job_id":"fixture",
                "plug_delivery_receipt":"fixture",
                "control_panel_audio_receipt":"fixture",
                "phone_playback_confirmation":"fixture"},
        })
        a=assertplan["capabilities"]
        self.assertEqual(a["CAP_21"]["state"],"SUBMITTED_FOR_INDEPENDENT_AUDIT")
        self.assertEqual(a["CAP_22"]["state"],"SUBMITTED_FOR_LIVE_AUDIT")
        self.assertFalse(assertplan["ready_for_live_deployment"])
    def test_cross_genre_substitution_fails(self):
        plan=rock_plan()
        plan["genre"]="Swing"
        with self.assertRaises(InterpreterConnectionError):
            evaluate_22_capabilities(plan)
if __name__=="__main__":unittest.main(verbosity=2)
