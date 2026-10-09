"""Rock percussion collision policy exact-pair safety tests."""
import copy
import os
import unittest
from unittest.mock import patch

from rock_drum_collision_policy_v1 import SWITCH, resolve_rock_drum_collisions as clean

def e(track,inst,beat,midi,velocity,art):
    return {"track_id":track,"instrument_id":inst,"start_beat":beat,
            "duration_beats":0.1,"midi":midi,"velocity":velocity,
            "articulation":art}

def sample():
    return [
        e("KICK","kick_drum_rock",0,36,62,"kick"),
        e("KICK","kick_drum_rock",0,36,112,"rock_kick"),
        e("KICK","kick_drum_rock",.5,36,88,"kick"),  # unique groove accent
        e("SNARE","snare_drum",1,38,60,"snare"),
        e("SNARE","snare_drum",1,38,102,"rock_backbeat"),
        e("SNARE","snare_drum",3,38,108,"rock_backbeat"),
        e("LEAD","lead_guitar",1,70,80,"genre_lead"),
        e("HAT","hi_hat",1,42,81,"hihat"),
    ]

class RockCollisionTests(unittest.TestCase):
    def test_no_activation_default(self):
        x=sample()
        with patch.dict(os.environ,{},clear=True):
            self.assertEqual(clean(x,"ROCK"),x)
        for value in ("0","yes","true","2",""):
            with self.subTest(value=value),patch.dict(os.environ,{SWITCH:value}):
                self.assertEqual(clean(x,"ROCK"),x)

    def test_exact_enabled_reduces_only_approved_pair(self):
        x=sample()
        result=clean(x,"ROCK",enabled=True)
        self.assertEqual(len(result),len(x)-2)
        self.assertEqual(result,[x[i] for i in (1,2,4,5,6,7)])

    def test_other_genre_never_affected(self):
        for g in ("Jazz Ballad","Funk","ROCKABILLY","",None):
            with self.subTest(genre=g):
                self.assertEqual(clean(sample(),g,enabled=True),sample())

    def test_untouched_source_events_and_no_mutation(self):
        x=sample();original=copy.deepcopy(x)
        result=clean(x,"ROCK",enabled=True)
        self.assertEqual(x,original)
        self.assertNotEqual(id(result[0]),id(original[1]))
        self.assertEqual(result[0],original[1])
        result[0]["velocity"]=12
        self.assertEqual(x[1]["velocity"],112)

    def test_triple_hit_ambiguous_retained(self):
        x=sample()+[e("KICK","kick_drum_rock",0,36,90,"rock_kick")]
        result=clean(x,"ROCK",enabled=True)
        self.assertIn(x[0],result)
        self.assertIn(x[1],result)
        self.assertIn(x[-1],result)

    def test_different_pitch_is_not_collision(self):
        x=[e("KICK","kick_drum_rock",0,35,55,"kick"),
           e("KICK","kick_drum_rock",0,36,112,"rock_kick")]
        self.assertEqual(clean(x,"ROCK",enabled=True),x)

    def test_unknown_drum_role_does_not_collide(self):
        x=[e("KICK","kick_drum_rock",0,36,55,"flam"),
           e("KICK","kick_drum_rock",0,36,112,"rock_kick")]
        self.assertEqual(clean(x,"ROCK",enabled=True),x)

    def test_mismatched_library_cannot_collapse(self):
        x=[e("SNARE","snare_drum",1,38,60,"snare"),
           e("SNARE","synthetic_snare",1,38,102,"rock_backbeat")]
        self.assertEqual(clean(x,"ROCK",enabled=True),x)

    def test_other_tracks_never_edited(self):
        x=sample()+[
            e("BASS","electric_bass_guitar",0,45,100,"bass"),
            e("TOMS","tom_tom",1,47,90,"tom_fill")]
        y=clean(x,"ROCK",enabled=True)
        self.assertEqual([v for v in x if v["track_id"] not in ("KICK","SNARE")],
                         [v for v in y if v["track_id"] not in ("KICK","SNARE")])

    def test_multiple_pairs_separate_bars(self):
        x=[e("SNARE","snare_drum",4*n+1,38,62,"snare") for n in range(12)]
        x += [e("SNARE","snare_drum",4*n+1,38,105,"rock_backbeat") for n in range(12)]
        self.assertEqual(len(clean(x,"ROCK",enabled=True)),12)

    def test_flag_explicit_false_overrides_env(self):
        with patch.dict(os.environ,{SWITCH:"1"}):
            self.assertEqual(clean(sample(),"ROCK",enabled=False),sample())

if __name__=="__main__":
    unittest.main(verbosity=2)
