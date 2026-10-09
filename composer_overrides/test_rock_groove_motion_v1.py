"""Safeguards for Rock groove's actual drum-beat subdivisions and bass sync."""
import os
import unittest
from collections import Counter
from unittest.mock import patch
from rock_groove_motion_v1 import SWITCH, REQUIRED_GATE, apply_rock_groove


def event(track,instrument,beat,pitch,velocity,articulation):
    return {"track_id":track,"instrument_id":instrument,"start_beat":beat,
            "duration_beats":.06 if track=="HAT" else .1,
            "midi":pitch,"velocity":velocity,"articulation":articulation}


def one_phrase():
    events=[]
    for bar in range(8):
        start=4*bar
        events.extend(event("HAT","hi_hat",start+j,42,48,"hat") for j in range(4))
        events.extend((event("KICK","kick_drum_rock",start,36,112,"rock_kick"),
                       event("KICK","kick_drum_rock",start+2,36,112,"rock_kick"),
                       event("SNARE","snare_drum",start+1,38,102,"rock_backbeat"),
                       event("SNARE","snare_drum",start+3,38,108,"rock_backbeat")))
        if bar in (1,3,4,5):
            events.append(event("KICK","kick_drum_rock",start+2.5,36,90,"rock_kick"))
        events.append(event("BASS","electric_bass_guitar",start,42,75,"genre_bass"))
        events.append(event("BASS","electric_bass_guitar",start+(2.25 if bar==4 else 2),43,75,"genre_bass"))
        events.append(event("LEAD","lead_guitar",start,68,80,"genre_lead"))
    return sorted(events,key=lambda e:(e["start_beat"],e["track_id"],e["midi"]))

class RockGrooveV1Tests(unittest.TestCase):
    def setUp(self):
        self.orig=one_phrase()

    def test_opt_in_must_have_clean_drums(self):
        for flags in ({}, {SWITCH:"1"}, {REQUIRED_GATE:"1"},
                      {SWITCH:"true",REQUIRED_GATE:"1"}):
            with self.subTest(flags=flags),patch.dict(os.environ,flags,clear=True):
                self.assertEqual(apply_rock_groove(self.orig,"ROCK"),self.orig)

    def test_not_other_genres(self):
        with patch.dict(os.environ,{SWITCH:"1",REQUIRED_GATE:"1"}):
            for genre in ("Jazz Ballad","FUNK","Rockabilly",""):
                self.assertEqual(apply_rock_groove(self.orig,genre),self.orig)

    def test_creates_eighth_and_limited_sixteenth_movement(self):
        with patch.dict(os.environ,{REQUIRED_GATE:"1"}):
            out=apply_rock_groove(self.orig,"ROCK",enabled=True)
        hats=[e for e in out if e["track_id"]=="HAT"]
        beats={round(e["start_beat"],2) for e in hats}
        self.assertIn(.5,beats)
        self.assertIn(1.5,beats)
        self.assertIn(3.5,beats)
        self.assertIn(15.25,beats)
        self.assertIn(15.75,beats)
        self.assertGreater(len(hats),32)
        # Nobody hits the same HAT twice at the same time.
        self.assertEqual(len(beats),len(hats))

    def test_new_hats_remain_same_real_sample_and_are_quieter(self):
        with patch.dict(os.environ,{REQUIRED_GATE:"1"}):
            out=apply_rock_groove(self.orig,"ROCK",enabled=True)
        hats=[e for e in out if e["track_id"]=="HAT" and e["start_beat"]%1>0]
        self.assertTrue(hats)
        self.assertTrue(all(e["instrument_id"]=="hi_hat" and e["midi"]==42
                            and e["articulation"]=="hat" for e in hats))
        self.assertTrue(all(25<=e["velocity"]<48 for e in hats))

    def test_only_bass_anchored_existing_kick_moves(self):
        with patch.dict(os.environ,{REQUIRED_GATE:"1"}):
            out=apply_rock_groove(self.orig,"ROCK",enabled=True)
        orig=[e for e in self.orig if e["track_id"]=="KICK"]
        new=[e for e in out if e["track_id"]=="KICK"]
        before={round(e["start_beat"],2) for e in orig}
        after={round(e["start_beat"],2) for e in new}
        self.assertEqual(len(orig),len(new))
        self.assertIn(18.25,after)
        self.assertNotIn(18.5,after)
        self.assertTrue({6.5,14.5,22.5}<=after)
        self.assertTrue({0,2,4,6,8,10,12,14}<=after)
        # Other kick fields were not replaced.
        self.assertEqual(Counter((e["velocity"],e["midi"],e["articulation"]) for e in orig),
                         Counter((e["velocity"],e["midi"],e["articulation"]) for e in new))

    def test_non_drum_score_unmodified(self):
        with patch.dict(os.environ,{REQUIRED_GATE:"1"}):
            out=apply_rock_groove(self.orig,"ROCK",enabled=True)
        keep=lambda e:e["track_id"] not in ("KICK","HAT")
        self.assertEqual([e for e in self.orig if keep(e)],[e for e in out if keep(e)])

    def test_old_score_input_does_not_mutate(self):
        snapshot=[dict(e) for e in self.orig]
        with patch.dict(os.environ,{REQUIRED_GATE:"1"}):
            out=apply_rock_groove(self.orig,"ROCK",enabled=True)
        self.assertEqual(self.orig,snapshot)
        out[0]["velocity"]=1
        self.assertEqual(self.orig[0],snapshot[0])

    def test_existing_hat_onsets_not_doubled(self):
        ev=one_phrase()
        ev.append(event("HAT","hi_hat",.5,42,38,"hat"))
        with patch.dict(os.environ,{REQUIRED_GATE:"1"}):
            out=apply_rock_groove(ev,"ROCK",enabled=True)
        self.assertEqual(sum(x["track_id"]=="HAT" and x["start_beat"]==.5 for x in out),1)

    def test_deterministic(self):
        with patch.dict(os.environ,{REQUIRED_GATE:"1"}):
            self.assertEqual(apply_rock_groove(self.orig,"ROCK",enabled=True),
                             apply_rock_groove(self.orig,"ROCK",enabled=True))

if __name__=="__main__":
    unittest.main(verbosity=2)
