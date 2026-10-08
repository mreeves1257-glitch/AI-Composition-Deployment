"""Genre-neutral automatic phrase selection and exact Composer output checks.

These tests DO NOT ask for full-song playback or modify the live Composer.
They enable the internal auto-phrase switch only inside the test context.
"""
from __future__ import annotations

import json
import os
import unittest
from dataclasses import replace
from fractions import Fraction
from unittest.mock import patch

from AI_Comp_Executable_Output_Core_001 import MusicalEvent, MidiAdapter
from output_handoff import build_execution_package
from test_instrument_gesture_handoff import engine_result, independently_authored_midi_plan
from phrase_expression_decisions import decide_phrase_end_vibrato


def instrument_capability():
    from pathlib import Path
    return json.loads((Path(__file__).with_name("performance_capabilities.json")).read_text())[
        "entries"]["SHINYGUITAR_RECORDED_LEAD_CC1_V1"]


def note(start,duration,pitch=60,articulation=None,track="SOLO",instrument="lead_guitar"):
    return MusicalEvent(
        "N"+str(start)+"-"+str(pitch), track, instrument,
        Fraction(str(start)),Fraction(str(duration)),pitch,100,
        articulation=articulation,
    )


class AutomaticPhrasePolicyTest(unittest.TestCase):
    def setUp(self):
        self.cap = instrument_capability()

    def test_sustained_phrase_ending_uses_existing_instrument_template(self):
        notes=(note(0,"1/2"),note("1/2","1/2"),note(1,4))
        gestures=decide_phrase_end_vibrato(notes,self.cap,ppq=480)
        self.assertEqual(gestures,[
            {"at_beat":"1","control":"vibrato_depth","value":0},
            {"at_beat":"2","control":"vibrato_depth","value":88},
            {"at_beat":"9/2","control":"vibrato_depth","value":0},
        ])
        self.assertEqual(notes[-1].articulation,None) # virtual, original unchanged

    def test_no_gesture_for_short_or_connected_notes(self):
        self.assertEqual(decide_phrase_end_vibrato(
            (note(0,"1/2"),note("1/2","1/2")),self.cap,ppq=480),[])
        self.assertEqual(decide_phrase_end_vibrato(
            (note(0,2),note(2,1)),self.cap,ppq=480),[])

    def test_long_note_before_real_rest_and_nonfinal_note(self):
        notes=(note(0,2),note("5/2",1),note("7/2",2))
        gestures=decide_phrase_end_vibrato(notes,self.cap,ppq=480)
        self.assertEqual([x["at_beat"] for x in gestures],
                         ["0","1/2","7/4","7/2","4","21/4"])
        self.assertEqual(len(gestures),6)

    def test_manual_articulations_take_precedence(self):
        for tag in ("staccato","legato","sustained_vibrato"):
            self.assertEqual(decide_phrase_end_vibrato(
                (note(0,4,articulation=tag),),self.cap,ppq=480),[])

    def test_chords_or_overlap_skip_channel_wide_vibrato(self):
        self.assertEqual(decide_phrase_end_vibrato(
            (note(0,4,60),note(1,4,64)),self.cap,ppq=480),[])
        self.assertEqual(decide_phrase_end_vibrato(
            (note(0,3,60),note(2,2,60)),self.cap,ppq=480),[])

    def test_unmapped_instrument_has_no_inferred_controls(self):
        wrong=dict(self.cap,note_mode="polyphonic")
        self.assertEqual(decide_phrase_end_vibrato((note(0,4),),wrong,ppq=480),[])
        wrong=dict(self.cap,gesture_templates={})
        self.assertEqual(decide_phrase_end_vibrato((note(0,4),),wrong,ppq=480),[])

    def test_repeatable_and_bounded(self):
        notes=tuple(note(i*4,2) for i in range(40))
        a=decide_phrase_end_vibrato(notes,self.cap,ppq=480)
        b=decide_phrase_end_vibrato(notes,self.cap,ppq=480)
        self.assertEqual(a,b)
        self.assertEqual(len(a),48) # last 16 eligible phrase endings only

    def test_auto_gate_off_is_byte_identical_to_existing_no_tag_composer(self):
        source=engine_result(None)
        with patch.dict(os.environ,{"AI_COMP_AUTO_PHRASING_V1":"0"}):
            original=build_execution_package(source)
            self.assertNotIn("expressive_gesture_plan",dict(original.metadata))
            original_midi=MidiAdapter().render(original,"fixed").payload
        with patch.dict(os.environ,{"AI_COMP_AUTO_PHRASING_V1":"absent"}):
            other=build_execution_package(source)
            self.assertEqual(MidiAdapter().render(other,"fixed").payload,original_midi)

    def test_auto_gate_on_resolves_real_sample_and_equals_manual_commands(self):
        source=engine_result(None)
        with patch.dict(os.environ,{"AI_COMP_AUTO_PHRASING_V1":"1"}):
            automatic=build_execution_package(source)
        with patch.dict(os.environ,{"AI_COMP_AUTO_PHRASING_V1":"0"}):
            ordinary=build_execution_package(source)
        meta=dict(automatic.metadata)
        self.assertIn("expressive_gesture_plan",meta)
        plan=json.loads(meta["expressive_gesture_plan"])
        self.assertEqual(plan["SOLO"]["gestures"],independently_authored_midi_plan()["SOLO"]["gestures"])
        self.assertEqual(source["modules"]["theory"]["events"][0]["articulation"],None)
        manual=replace(ordinary,metadata=ordinary.metadata+((
            "expressive_gesture_plan",json.dumps(independently_authored_midi_plan())
        ),))
        self.assertEqual(
            MidiAdapter().render(automatic,"same").payload,
            MidiAdapter().render(manual,"same").payload,
        )

    def test_auto_does_not_modify_unsupported_or_other_instruments(self):
        source=engine_result(None,resource_id="UNKNOWN_RESOURCE",program="none.sfz")
        with patch.dict(os.environ,{"AI_COMP_AUTO_PHRASING_V1":"1"}):
            pkg=build_execution_package(source)
        self.assertNotIn("expressive_gesture_plan",dict(pkg.metadata))
        source=engine_result(None,instrument="piano",resource_id="UNKNOWN",program="piano.sfz")
        with patch.dict(os.environ,{"AI_COMP_AUTO_PHRASING_V1":"1"}):
            pkg=build_execution_package(source)
        self.assertNotIn("expressive_gesture_plan",dict(pkg.metadata))

    def test_auto_avoids_existing_manual_and_polyphonic_guitar(self):
        source=engine_result("sustained_vibrato")
        with patch.dict(os.environ,{"AI_COMP_AUTO_PHRASING_V1":"1"}):
            pkg=build_execution_package(source)
        self.assertEqual(json.loads(dict(pkg.metadata)["expressive_gesture_plan"])["SOLO"]["gesture_source"],"note_articulation")
        source=engine_result(None,overlap=True)
        with patch.dict(os.environ,{"AI_COMP_AUTO_PHRASING_V1":"1"}):
            pkg=build_execution_package(source)
        self.assertNotIn("expressive_gesture_plan",dict(pkg.metadata))


if __name__=="__main__":
    unittest.main(verbosity=2)
