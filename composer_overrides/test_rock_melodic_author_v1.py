"""Regression tests: only isolated, opt-in Rock melody composition changes."""
from __future__ import annotations
import os
import unittest
from unittest.mock import patch

from rock_melodic_author_v1 import FEATURE,compose_rock_melody,NOTE_PC

def score():
    return ([{"track_id":"BASS","instrument_id":"electric_bass_guitar","start_beat":i*4,
              "duration_beats":.6,"midi":36+i%3,"velocity":85}
             for i in range(16)]
            +[{"track_id":"HARMONY","instrument_id":"electric_guitar","start_beat":i*4,
               "duration_beats":1.2,"midi":60+i%3,"velocity":77}
              for i in range(16)]
            +[{"track_id":"LEAD","instrument_id":"lead_guitar",
               "start_beat":i*4+j*4/6,"duration_beats":.34,
               "midi":60+(j%6),"velocity":80,"articulation":"genre_lead"}
              for i in (5,7,11,13,15) for j in range(6)])

def ctx():
    root=["C","F","G","A"]
    chords=[{"root":root[i%4],"notes":{
        "C":["C","E","G"],"F":["F","A","C"],"G":["G","B","D"],"A":["A","C","E"],
    }[root[i%4]]} for i in range(16)]
    return {"meter":{"numerator":4,"denominator":4},
            "harmony":{"chords":chords},
            "key":{"scale":["C","D","E","F","G","A","B"]}}

class TestMelodicAuthor(unittest.TestCase):
    def test_default_is_original_score(self):
        with patch.dict(os.environ,{},clear=True):
            self.assertEqual(compose_rock_melody(score(),ctx()),score())
        with patch.dict(os.environ,{FEATURE:"false"}):
            self.assertEqual(compose_rock_melody(score(),ctx()),score())

    def test_only_literal_opt_in(self):
        with patch.dict(os.environ,{FEATURE:"1"}):
            self.assertNotEqual(compose_rock_melody(score(),ctx()),score())

    def test_preserves_every_nonlead_event_exactly(self):
        original=score()
        changed=compose_rock_melody(original,ctx(),active=True)
        before=[e for e in original if e["track_id"]!="LEAD"]
        after=[e for e in changed if e["track_id"]!="LEAD"]
        self.assertEqual(sorted(before,key=lambda x:(x["track_id"],x["start_beat"])),
                         sorted(after,key=lambda x:(x["track_id"],x["start_beat"])))

    def test_no_new_lead_bars(self):
        orig=score()
        changed=compose_rock_melody(orig,ctx(),active=True)
        bars=lambda ev:{int(e["start_beat"]//4) for e in ev if e["track_id"]=="LEAD"}
        self.assertEqual(bars(changed),bars(orig))

    def test_not_fixed_six_note_rolls(self):
        original=score()
        changed=compose_rock_melody(original,ctx(),active=True)
        before=[e for e in original if e["track_id"]=="LEAD"]
        after=[e for e in changed if e["track_id"]=="LEAD"]
        self.assertLess(len(after),len(before))
        self.assertGreater(len({e["midi"] for e in after}),3)
        self.assertGreater(len({round(e["start_beat"]%4,2) for e in after}),4)
        self.assertGreater(len({round(e["duration_beats"],2) for e in after}),3)

    def test_chord_tones_on_anchor_and_resolution(self):
        output=compose_rock_melody(score(),ctx(),active=True)
        by_bar={}
        for x in output:
            if x["track_id"]=="LEAD":by_bar.setdefault(int(x["start_beat"]//4),[]).append(x)
        for bar,notes in by_bar.items():
            notes.sort(key=lambda e:e["start_beat"])
            tones={NOTE_PC[n] for n in ctx()["harmony"]["chords"][bar]["notes"]}
            self.assertIn(notes[0]["midi"]%12,tones)
            self.assertIn(notes[-1]["midi"]%12,tones)

    def test_all_notes_playable_and_no_overlap_in_bar(self):
        output=compose_rock_melody(score(),ctx(),active=True)
        for e in output:
            if e["track_id"]!="LEAD":continue
            self.assertGreaterEqual(e["midi"],59)
            self.assertLessEqual(e["midi"],76)
            self.assertGreater(e["duration_beats"],0)
            self.assertLess(e["start_beat"]%4+e["duration_beats"],4.001)
        bybar={}
        for e in output:
            if e["track_id"]=="LEAD":bybar.setdefault(int(e["start_beat"]//4),[]).append(e)
        for notes in bybar.values():
            notes.sort(key=lambda e:e["start_beat"])
            for a,b in zip(notes,notes[1:]):
                self.assertLess(a["start_beat"]+a["duration_beats"],b["start_beat"])

    def test_repeatable_same_seed_not_mutating(self):
        orig=score()
        one=compose_rock_melody(orig,ctx(),2,active=True)
        two=compose_rock_melody(orig,ctx(),2,active=True)
        self.assertEqual(one,two)
        self.assertEqual(orig,score())

    def test_unsupported_or_missing_harmony_is_noop(self):
        original=score()
        bad=[{},{"meter":{"numerator":3,"denominator":4}},
             {"meter":{"numerator":4,"denominator":4},
              "key":{"scale":["C"]},"harmony":{"chords":[]}}]
        for context in bad:
            self.assertEqual(compose_rock_melody(original,context,active=True),original)

if __name__=="__main__":
    unittest.main(verbosity=2)
