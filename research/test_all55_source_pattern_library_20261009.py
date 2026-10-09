"""Full original 55-genre source-pattern authoring and score-compilation proof."""
from pathlib import Path
from fractions import Fraction
from collections import defaultdict
import hashlib,sys,unittest,json
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"composer_overrides"))
from genre_styles.shared_interpreter_router import (
    connect_all_genres,InterpreterConnectionError,CAPABILITY_IDS)
from genre_styles.source_pattern_library import (compile_original_source_seed,
    read_pack,SECTION_NAMES,VARIATIONS)
from genre_styles.shared_musical_grammar import compile_musical_plan
class GenreSourcePatternTests(unittest.TestCase):
 def test_every_genre_has_distinct_usable_source_musical_output(self):
    original=connect_all_genres()
    self.assertEqual(len(original),55)
    count=0
    family_counts=defaultdict(int)
    music_fingerprints=defaultdict(list)
    for name,route in original.items():
        with self.subTest(genre=name):
            data,ref=read_pack(name)
            p=compile_original_source_seed(name)
            notes=p["symbolic_note_events"]
            self.assertTrue(notes,name)
            self.assertEqual(p["genre_profile_id"],ref["genre_profile_id"])
            self.assertEqual(p["genre_rules"],ref["genre_specific_musical_intentions"])
            self.assertEqual(p["source_pattern_contract"]["genre_specific_seed"],name)
            self.assertEqual(p["source_pattern_contract"]["played_section_sequence"],list(SECTION_NAMES))
            self.assertEqual({n["section"] for n in notes},set(SECTION_NAMES))
            self.assertEqual({n["role"] for n in notes},{r["role"] for r in data["roles"]})
            self.assertEqual(len(p["capability_status"]),22)
            self.assertEqual(tuple(p["capability_execution"]["capabilities"]),CAPABILITY_IDS)
            self.assertFalse(p["midi_authorized"])
            self.assertFalse(p["recorded_audio_authorized"])
            self.assertFalse(p["capability_execution"]["ready_for_live_deployment"])
            self.assertFalse(p["source_pattern_contract"]["production_enabled"])
            for n in notes:
                self.assertEqual(n["status"],"SYMBOLIC_ONLY")
                self.assertLess(Fraction(n["start_beat"]),Fraction(p["bars"])*Fraction(p["quarter_beats_per_bar"]))
                self.assertGreater(Fraction(n["duration_beats"]),0)
                if n["pattern_kind"]=="DRUM_ABSOLUTE":
                    self.assertEqual(n["source_note_mapping"],"UNVERIFIED_RECORDED_PROGRAM")
            fingerprint=hashlib.sha256(json.dumps([
                [x["start_beat"],x["midi"],x["role"],x["velocity"],x["section"]]
                for x in notes],sort_keys=True).encode()).hexdigest()
            music_fingerprints[fingerprint].append(name)
            count+=len(notes);family_counts[ref["family"]]+=1
    self.assertEqual(len(family_counts),13)
    self.assertEqual(sum(family_counts.values()),55)
    self.assertEqual(len(music_fingerprints),55,
                     [x for x in music_fingerprints.values() if len(x)>1])
    self.assertGreater(count,1000)
    print("ALL_55_GENRES_ORIGINAL_SOURCE_PATTERN_NOTES_PASS",
          json.dumps({"genres":55,"families":13,"unique_note_fingerprints":len(music_fingerprints),
                      "produced_seven_bar_symbolic_notes":count,
                      "source_sample_audio_approved":False}))
 def test_rock_swing_salsa_waltz_and_pianist_distinctions(self):
    rock=compile_original_source_seed("ROCK")
    swing=compile_original_source_seed("Swing")
    salsa=compile_original_source_seed("Salsa")
    waltz=compile_original_source_seed("WALTZ")
    solo=compile_original_source_seed("PIANIST")
    self.assertEqual(rock["meter"],"4/4")
    self.assertEqual(swing["meter"],"4/4")
    self.assertEqual(salsa["meter"],"4/4")
    self.assertEqual(waltz["meter"],"3/4")
    self.assertIn(solo["meter"],("4/4","3/4","6/8"))
    role=lambda p:{n["role"] for n in p["symbolic_note_events"]}
    self.assertTrue({"KICK","SNARE","HAT"}.issubset(role(rock)))
    self.assertIn("RIDE",role(swing))
    self.assertTrue({"CONGA","CLAVE","SHAKER"}.issubset(role(salsa)))
    self.assertFalse({"KICK","SNARE","HAT","CONGA","CLAVE"}.intersection(role(waltz)))
    self.assertEqual(role(solo),{"LEFT_HAND","RIGHT_HAND"})
    self.assertTrue(all(n["pattern_kind"]=="CHORD_RELATIVE"
                        for n in solo["symbolic_note_events"]))
    def percussion(p):return [(x["start_beat"],x["role"]) for x in p["symbolic_note_events"]
                            if x["pattern_kind"]=="DRUM_ABSOLUTE"]
    self.assertNotEqual(percussion(rock),percussion(salsa))
    self.assertNotEqual(percussion(swing),percussion(salsa))
 def test_missing_instrument_or_corrupt_provenance_fails_closed(self):
    self.assertRaises(InterpreterConnectionError,read_pack,"Missing Genre")
    p,ref=read_pack("ROCK")
    self.assertRaises(InterpreterConnectionError,compile_musical_plan,
        "Jazz Waltz",meter="4/4",tempo_bpm=130,bars=7,sections=p["sections"],
        chords=p["chords"],roles=p["roles"],patterns=p["patterns"])
    self.assertRaises(InterpreterConnectionError,compile_musical_plan,
        "ROCK",meter="4/4",tempo_bpm=120,bars=7,sections=p["sections"],
        chords=p["chords"],roles=p["roles"],patterns=p["patterns"],
        original_stage3_result={"status":"PASS","meter":"4/4","tempo_bpm":120,
                                "palette":["piano"]})
    source=ROOT/"composer_overrides"/"genre_styles"/"Rock"
    self.assertFalse((source/"rock_pinned_mma_interpreter.py").exists())
    self.assertTrue((ROOT/"research"/"archived_rock_20261009"/"original"/"rock_pinned_mma_interpreter.py").is_file())
if __name__=="__main__":unittest.main(verbosity=2)
