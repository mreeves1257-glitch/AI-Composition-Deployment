"""Regression tests: Rock melody R1 cannot alter sounds, roles or other genres."""
import collections
import copy
import os
import unittest
from unittest.mock import patch

from rock_melodic_development_v1 import SWITCH, compose_rock_melody


def fake_music(bars=24):
    ev=[]
    # Existing triads Dm / F / Eb / Bb, bass note roots (the note values
    # are score samples only; no synthetic audio or fake performance proof).
    chords=((62,65,69),(65,69,72),(63,67,70),(70,74,77))
    for bar in range(bars):
        chord=chords[bar%4]
        for pc in chord:
            ev.append(dict(track_id="HARMONY",instrument_id="electric_guitar",
                start_beat=4*bar+0.032*(pc-chord[0]),duration_beats=1.1,
                midi=pc,velocity=65,articulation="genre_harmony"))
        ev.append(dict(track_id="BASS",instrument_id="electric_bass_guitar",
            start_beat=4*bar,duration_beats=.48,midi=chord[0]-24,
            velocity=75,articulation="genre_bass"))
        ev.append(dict(track_id="SNARE",instrument_id="snare_drum",
            start_beat=4*bar+1,duration_beats=.1,midi=38,
            velocity=88,articulation="snare"))
        if bar%2==1 and bar>3:
            for j in range(6):
                ev.append(dict(track_id="LEAD",instrument_id="lead_guitar",
                    start_beat=4*bar+j*2/3,duration_beats=.35,
                    midi=[62,64,65,67,69,70][j],
                    velocity=75,articulation="genre_lead"))
    return ev


class RockMelodyTests(unittest.TestCase):
    def setUp(self):
        self.events=fake_music()

    def test_default_absent_and_false_preserve_every_note(self):
        with patch.dict(os.environ,{},clear=True):
            self.assertEqual(compose_rock_melody(self.events,"ROCK"),self.events)
        with patch.dict(os.environ,{SWITCH:"0"}):
            self.assertEqual(compose_rock_melody(self.events,"ROCK"),self.events)
        with patch.dict(os.environ,{SWITCH:"true"}):
            self.assertEqual(compose_rock_melody(self.events,"ROCK"),self.events)

    def test_rock_only(self):
        for style in ("Jazz Ballad","FUNK","Country","Rockabilly",""):
            with self.subTest(style=style):
                self.assertEqual(compose_rock_melody(self.events,style,flag=True),self.events)

    def test_every_nonlead_event_is_bit_identical(self):
        result=compose_rock_melody(self.events,"ROCK",flag=True)
        original=[e for e in self.events if e["track_id"]!="LEAD"]
        current=[e for e in result if e["track_id"]!="LEAD"]
        self.assertEqual(original,current)

    def test_no_new_track_source_or_extra_lead_note(self):
        before=collections.Counter(e["track_id"] for e in self.events)
        after=collections.Counter(e["track_id"] for e in compose_rock_melody(self.events,"ROCK",flag=True))
        self.assertEqual(set(before),set(after))
        self.assertLess(after["LEAD"],before["LEAD"])
        self.assertGreater(after["LEAD"],0)

    def test_lead_is_chord_grounded_and_register_bounded(self):
        events=compose_rock_melody(self.events,"ROCK",flag=True)
        bybar=collections.defaultdict(set)
        for e in self.events:
            if e["track_id"]=="HARMONY" and e["start_beat"]%4<.6:
                bybar[int(e["start_beat"]//4)].add(e["midi"]%12)
        leads=[e for e in events if e["track_id"]=="LEAD"]
        self.assertTrue(all(60<=e["midi"]<=78 for e in leads))
        self.assertTrue(all(e["midi"]%12 in bybar[int(e["start_beat"]//4)] for e in leads))
        self.assertGreater(len({e["midi"] for e in leads}),4)
        self.assertGreater(len({e["start_beat"]%4 for e in leads}),5)
        self.assertTrue(all(e["duration_beats"]>0 and e["velocity"]>0 for e in leads))

    def test_original_music_is_not_modified_in_place(self):
        original=copy.deepcopy(self.events)
        changed=compose_rock_melody(self.events,"ROCK",flag=True)
        self.assertEqual(self.events,original)
        changed[0]["midi"]=1
        self.assertEqual(self.events[0],original[0])

    def test_audit_is_deterministic_and_explicit_off_overrides_env(self):
        a=compose_rock_melody(self.events,"ROCK",flag=True)
        b=compose_rock_melody(self.events,"ROCK",flag=True)
        self.assertEqual(a,b)
        with patch.dict(os.environ,{SWITCH:"1"}):
            self.assertEqual(compose_rock_melody(self.events,"ROCK",flag=False),self.events)

    def test_non_four_four_keeps_existing_events(self):
        self.assertEqual(compose_rock_melody(self.events,"ROCK",flag=True,beats_per_bar=3),self.events)


if __name__=="__main__":
    unittest.main(verbosity=2)
