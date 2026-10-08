"""Regression tests for real MIDI encoding of explicitly requested controls."""
from __future__ import annotations

import json
import unittest
from fractions import Fraction

from AI_Comp_Executable_Output_Core_001 import (
    CompositionExecutionPackage, MidiAdapter, MusicalEvent, TimeSignature,
)
from midi_initial_cc_bridge import append_initial_cc, MidiControlContractError


def make_package(routes=None):
    meta = () if routes is None else (("midi_routing", json.dumps(routes)),)
    events = (
        MusicalEvent("E1", "LEAD", "electric_guitar", Fraction(0), Fraction(1), 64, 90),
        MusicalEvent("E2", "BASS", "electric_bass_guitar", Fraction(0), Fraction(1), 40, 80),
    )
    return CompositionExecutionPackage("test", "Test", 120.0, TimeSignature(4, 4),
                                       480, events, meta)


def midi_bytes(routes=None):
    return MidiAdapter().render(make_package(routes), "test-fingerprint").payload


class ExplicitControlBridgeTests(unittest.TestCase):
    def test_native_lead_controls_before_first_note(self):
        # These exact CC values are already declared in Rock's target program.
        raw = midi_bytes({"LEAD": {"initial_cc": {"1": 88, "103": 85, "104": 90}}})
        first_cc = raw.index(bytes((0xB0, 1, 88)))
        first_note = raw.index(bytes((0x90, 64, 90)))
        self.assertLess(first_cc, first_note)
        self.assertIn(bytes((0xB0, 103, 85)), raw)
        self.assertIn(bytes((0xB0, 104, 90)), raw)
        self.assertEqual(raw.count(bytes((0xB0, 1, 88))), 1)
        self.assertIn(bytes((0x90, 40, 80)), raw)

    def test_no_midi_controls_not_requested(self):
        self.assertEqual(
            midi_bytes(),
            midi_bytes({"LEAD": {"initial_cc": {}}, "BASS": {"percussion": False}}),
        )

    def test_only_specific_track_receives_controls(self):
        raw = midi_bytes({"BASS": {"initial_cc": {"7": 35}}})
        self.assertNotIn(bytes((0xB0, 1, 88)), raw)
        self.assertIn(bytes((0xB1, 7, 35)), raw)

    def test_preserves_track_midi_channel(self):
        controls = append_initial_cc([], (("midi_routing", json.dumps(
            {"LEAD": {"initial_cc": {"1": 88}}})),), "LEAD", 3)
        self.assertEqual(controls, [(0, -1, bytes((0xB3, 1, 88)))])

    def test_invalid_cc_refused_not_clamped(self):
        for bad in ({"131": 2}, {"1": 200}, {"1": -1}, {"1": True}):
            with self.subTest(bad=bad), self.assertRaises(MidiControlContractError):
                append_initial_cc([], (("midi_routing", json.dumps(
                    {"LEAD": {"initial_cc": bad}}
                )),), "LEAD")

    def test_existing_onsets_and_pitch_untouched(self):
        plain = midi_bytes()
        controlled = midi_bytes({"LEAD": {"initial_cc": {"1": 88}}})
        self.assertIn(bytes((0x90, 64, 90)), plain)
        self.assertIn(bytes((0x90, 64, 90)), controlled)
        self.assertIn(bytes((0x80, 64, 0)), controlled)
        self.assertIn(bytes((0x90, 40, 80)), controlled)


if __name__ == "__main__":
    unittest.main(verbosity=2)
