"""Prove one executable symbolic genre grammar; no verified audio is claimed."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"composer_overrides"))
from genre_styles.shared_interpreter_router import connect_all_genres,InterpreterConnectionError
from genre_styles.shared_musical_grammar import compile_musical_plan

class SharedGrammarTests(unittest.TestCase):
    def test_every_genre_uses_its_own_source_rules(self):
        routes=connect_all_genres()
        self.assertEqual(len(routes),55)
        for name,route in routes.items():
            d=route["genre_specific_musical_intentions"]
            with self.subTest(genre=name):
                p=compile_musical_plan(name,meter=d["meter_options"][0],
                    tempo_bpm=d["tempo_bpm_range"][0],bars=8)
                self.assertEqual(p["genre_profile_id"],route["genre_profile_id"])
                self.assertEqual(p["genre_rules"],d)
                self.assertEqual(p["original_7_stages"],route["original_7_stages"])
                self.assertEqual(len(p["capability_status"]),22)
                self.assertFalse(p["midi_authorized"])
                self.assertFalse(p["recorded_audio_authorized"])
                self.assertEqual(p["symbolic_note_events"],[])
    def test_root_and_chord_type_and_section_variants(self):
        x=compile_musical_plan("ROCK",meter="4/4",tempo_bpm=145,bars=2,
            sections=[{"name":"V","bars":1,"variation_by_role":{"HARMONY":"A"}},
                      {"name":"C","bars":1,"variation_by_role":{"HARMONY":"B"}}],
            chords=[{"bar":0,"symbol":"C"},{"bar":1,"symbol":"Dm"}],
            roles=[{"role":"HARMONY","instrument_id":"electric_guitar",
                    "playable_midi_range":[40,90]}],
            patterns=[{"role":"HARMONY","kind":"CHORD_RELATIVE",
                "retrigger":"STOP_AT_CHORD","variations":{
                 "A":[{"beat":0,"duration":2,"degree":3,"octave":4,"velocity":81}],
                 "B":[{"beat":0,"duration":2,"degree":3,"octave":4,"velocity":96}]}}])
        self.assertEqual([e["midi"] for e in x["symbolic_note_events"]],[64,65])
        self.assertEqual([e["velocity"] for e in x["symbolic_note_events"]],[81,96])
        self.assertEqual([e["variation"] for e in x["symbolic_note_events"]],["A","B"])
        self.assertFalse(x["midi_authorized"])
    def test_midbar_chord_and_hold_stop(self):
        args=dict(genre="ROCK",meter="4/4",tempo_bpm=120,bars=1,
            sections=[{"name":"V","bars":1,"variation_by_role":{"LEAD":"A"}}],
            chords=[{"bar":0,"beat":0,"symbol":"C"},{"bar":0,"beat":2,"symbol":"G7"}],
            roles=[{"role":"LEAD","instrument_id":"electric_guitar",
                    "playable_midi_range":[40,90]}],
            patterns=[{"role":"LEAD","kind":"CHORD_RELATIVE","retrigger":"STOP_AT_CHORD",
                       "variations":{"A":[{"beat":1,"duration":3,"degree":3,
                                             "octave":4,"velocity":89},
                                            {"beat":3,"duration":1,"degree":3,
                                             "octave":4,"velocity":89}]}}])
        p=compile_musical_plan(**args)
        self.assertEqual([n["midi"] for n in p["symbolic_note_events"]],[64,71])
        self.assertEqual(p["symbolic_note_events"][0]["duration_beats"],"1")
        args["patterns"][0]["retrigger"]="HOLD_THROUGH_CHORD"
        q=compile_musical_plan(**args)
        self.assertEqual(q["symbolic_note_events"][0]["duration_beats"],"3")
    def test_no_rock_fallback_or_auto_drums(self):
        for genre,meter,tempo in [("WALTZ","3/4",90),("PIANIST","6/8",90),
                                  ("Jazz Waltz","3/4",90),("Salsa","4/4",160)]:
            p=compile_musical_plan(genre,meter=meter,tempo_bpm=tempo,bars=8)
            self.assertNotEqual(p["genre_profile_id"],"ROCK_CORE_V2")
            self.assertEqual(p["symbolic_note_events"],[])
    def test_invalid_requests_fail_closed(self):
        base=dict(genre="ROCK",meter="4/4",tempo_bpm=120,bars=2)
        for bad in ({"meter":"3/4"},{"tempo_bpm":320},
                    {"sections":[{"name":"BAD","bars":3}]},
                    {"chords":[{"bar":2,"symbol":"C"}]},
                    {"chords":[{"bar":0,"symbol":"H"}]},
                    {"roles":[{"role":"BASS","instrument_id":"bass",
                               "playable_midi_range":[80,20]}]}):
            with self.subTest(bad=bad),self.assertRaises(InterpreterConnectionError):
                compile_musical_plan(**(base|bad))
        with self.assertRaises(InterpreterConnectionError):
            compile_musical_plan("Jazz Ballad",tempo_bpm=60,bars=2)
        with self.assertRaises(InterpreterConnectionError):
            compile_musical_plan("NO_SUCH_GENRE",meter="4/4",tempo_bpm=110)
if __name__=="__main__":unittest.main(verbosity=2)
