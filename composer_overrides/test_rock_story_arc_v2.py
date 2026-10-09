"""Rock storyline V2: default-off, score integrity and song-form tests."""
import os
import unittest
from collections import defaultdict
from unittest.mock import patch

from rock_story_arc_v2 import compose_rock_story,SWITCH,BASELINE_SWITCH,_section,_shape


def score():
    chords=[("D",("D","F","A")),("Bb",("Bb","D","F")),
            ("F",("F","A","C")),("C",("C","E","G"))]
    ctx={"meter":{"numerator":4,"denominator":4},
         "harmony":{"chords":[{"root":chords[i%4][0],"notes":list(chords[i%4][1])} for i in range(127)]},
         "key":{"scale":["D","E","F","G","A","Bb","C"]}}
    events=[]
    for bar in range(127):
        root=[50,46,53,48][bar%4]
        events.extend({"track_id":"HARMONY","instrument_id":"electric_guitar",
                      "start_beat":bar*4,"duration_beats":1,
                      "midi":x,"velocity":77}
                      for x in (root+12,root+15,root+19))
        events.append({"track_id":"BASS","instrument_id":"electric_bass_guitar",
                      "start_beat":bar*4,"duration_beats":.6,"midi":root-12,"velocity":79})
        events.append({"track_id":"SNARE","instrument_id":"snare_drum",
                       "start_beat":bar*4+1,"duration_beats":.1,"midi":38,"velocity":99})
        if bar>=4 and bar%2==1:
            for j in range(5):
                events.append({"track_id":"LEAD","instrument_id":"lead_guitar",
                               "start_beat":4*bar+.65*j,"duration_beats":.4,
                               "midi":63+j,"velocity":82,"articulation":"genre_lead"})
    events.sort(key=lambda e:(float(e["start_beat"]),str(e["track_id"]),int(e.get("midi",0))))
    return events,ctx

class StoryV2Tests(unittest.TestCase):
    def setUp(self):
        self.events,self.ctx=score()

    def test_off_is_byte_equivalent(self):
        with patch.dict(os.environ,{},clear=True):
            self.assertEqual(compose_rock_story(self.events,self.ctx),self.events)
        with patch.dict(os.environ,{SWITCH:"0",BASELINE_SWITCH:"1"}):
            self.assertEqual(compose_rock_story(self.events,self.ctx),self.events)

    def test_cannot_activate_without_melody_r1(self):
        with patch.dict(os.environ,{SWITCH:"1",BASELINE_SWITCH:"0"}):
            self.assertEqual(compose_rock_story(self.events,self.ctx),self.events)

    def test_ignores_other_switch_values(self):
        for x in ("true","on","2","yes"):
            with self.subTest(x=x),patch.dict(os.environ,{SWITCH:x,BASELINE_SWITCH:"1"}):
                self.assertEqual(compose_rock_story(self.events,self.ctx),self.events)

    def test_no_unrelated_instrument_or_other_genre_changes(self):
        a=self.events
        with patch.dict(os.environ,{BASELINE_SWITCH:"1"}):
            b=compose_rock_story(a,self.ctx,active=True)
        x=[e for e in a if e["track_id"]!="LEAD"]
        y=[e for e in b if e["track_id"]!="LEAD"]
        self.assertEqual(x,y)
        self.assertEqual(a,score()[0])

    def test_no_new_lead_bars(self):
        with patch.dict(os.environ,{BASELINE_SWITCH:"1"}):
            out=compose_rock_story(self.events,self.ctx,active=True)
        bars=lambda ev:{int(e["start_beat"]//4) for e in ev if e["track_id"]=="LEAD"}
        self.assertEqual(bars(out),bars(self.events))
        self.assertLess(len([x for x in out if x["track_id"]=="LEAD"]),
                        len([x for x in self.events if x["track_id"]=="LEAD"]))

    def test_playable_register_no_overlap_or_offkey(self):
        with patch.dict(os.environ,{BASELINE_SWITCH:"1"}):
            out=compose_rock_story(self.events,self.ctx,active=True)
        scale={2,4,5,7,9,10,0}
        grouped=defaultdict(list)
        for e in out:
            if e["track_id"]=="LEAD":
                self.assertGreaterEqual(e["midi"],59)
                self.assertLessEqual(e["midi"],76)
                self.assertIn(e["midi"]%12,scale)
                self.assertGreater(e["duration_beats"],.1)
                self.assertLess(e["start_beat"]%4+e["duration_beats"],4.0001)
                grouped[int(e["start_beat"]//4)].append(e)
        for notes in grouped.values():
            notes.sort(key=lambda e:e["start_beat"])
            for a,b in zip(notes,notes[1:]):
                self.assertLess(a["start_beat"]+a["duration_beats"],b["start_beat"])

    def test_musical_sections_and_returning_hook(self):
        self.assertEqual(_section(12,127),"VERSE")
        self.assertEqual(_section(32,127),"HOOK")
        self.assertEqual(_section(64,127),"HOOK_RETURN")
        self.assertEqual(_section(76,127),"BRIDGE")
        self.assertEqual(_section(94,127),"FINAL_HOOK")
        self.assertEqual(_section(122,127),"OUTRO")
        self.assertEqual(_shape("HOOK",33),_shape("HOOK_RETURN",65))
        self.assertEqual(_shape("HOOK_RETURN",65),_shape("FINAL_HOOK",97))
        self.assertNotEqual(_shape("BRIDGE",75),_shape("HOOK",35))

    def test_deterministic(self):
        with patch.dict(os.environ,{BASELINE_SWITCH:"1"}):
            a=compose_rock_story(self.events,self.ctx,3,active=True)
            b=compose_rock_story(self.events,self.ctx,3,active=True)
        self.assertEqual(a,b)

    def test_no_context_not_guessed(self):
        with patch.dict(os.environ,{BASELINE_SWITCH:"1"}):
            self.assertEqual(compose_rock_story(self.events,{},active=True),self.events)

if __name__=="__main__":
    unittest.main(verbosity=2)
