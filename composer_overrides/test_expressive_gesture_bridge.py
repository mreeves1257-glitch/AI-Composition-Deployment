"""Byte-level tests of the real Output Core + opt-in, source-mapped gestures."""
from __future__ import annotations

import json
import unittest
from fractions import Fraction

from AI_Comp_Executable_Output_Core_001 import (
    CompositionExecutionPackage, MidiAdapter, MusicalEvent, TimeSignature,
)
from expressive_gesture_bridge import PerformanceGestureError


def plan(*gestures, cap="SHINYGUITAR_RECORDED_LEAD_CC1_V1",
         resource="KARORYFER_SHINYGUITAR", program="Programs/composer-electric-lead.sfz"):
    return {
        "LEAD": {
            "capability_id": cap, "resource_id": resource,
            "preferred_mapping": program, "gestures": list(gestures),
        }
    }


def make_package(expression=None, lead_events=None, includes_initial_cc=True):
    if lead_events is None:
        lead_events = (
            MusicalEvent("L1", "LEAD", "electric_guitar", Fraction(0), Fraction(4), 64, 90),
        )
    notes = tuple(lead_events) + (
        MusicalEvent("B1", "BASS", "electric_bass_guitar", Fraction(0), Fraction(2), 40, 79),
    )
    metadata = []
    if includes_initial_cc:
        metadata.append(("midi_routing", json.dumps({"LEAD": {"initial_cc": {"1": 88}}})))
    if expression is not None:
        metadata.append(("expressive_gesture_plan", json.dumps(expression)))
    return CompositionExecutionPackage(
        "expressive-check", "No Genre Template", 120.0,
        TimeSignature(4, 4), 480, notes, tuple(metadata),
    )


def midi_bytes(expression=None, lead_events=None):
    return MidiAdapter().render(make_package(expression, lead_events), "fixture").payload


def decode_tracks(raw):
    assert raw[:4] == b"MThd"
    header_len = int.from_bytes(raw[4:8], "big")
    pos = 8 + header_len
    tracks = []
    while pos < len(raw):
        assert raw[pos:pos + 4] == b"MTrk"
        length = int.from_bytes(raw[pos + 4:pos + 8], "big")
        segment = raw[pos + 8:pos + 8 + length]
        pos += 8 + length
        cursor = 0
        tick = 0
        events = []
        while cursor < len(segment):
            dt = 0
            while True:
                b = segment[cursor]
                cursor += 1
                dt = (dt << 7) | (b & 0x7f)
                if not (b & 0x80):
                    break
            tick += dt
            kind = segment[cursor]
            cursor += 1
            if kind == 0xff:
                subtype = segment[cursor]
                cursor += 1
                n = 0
                while True:
                    v = segment[cursor]
                    cursor += 1
                    n = (n << 7) | (v & 0x7f)
                    if not (v & 0x80):
                        break
                cursor += n
                if subtype == 0x2f:
                    break
                continue
            n = 1 if (kind & 0xf0) in (0xc0, 0xd0) else 2
            data = tuple(segment[cursor:cursor + n])
            cursor += n
            events.append((tick, kind, data))
        tracks.append(events)
    return tracks


class ExpressiveBridgeTests(unittest.TestCase):
    def test_no_plan_does_not_change_midi(self):
        a = midi_bytes()
        b = midi_bytes({})
        self.assertEqual(a, b)

    def test_real_timed_midi_and_note_preservation(self):
        gestures = plan(
            {"at_beat": "0", "control": "vibrato_depth", "value": 0},
            {"at_beat": "1/2", "control": "vibrato_depth", "value": 88},
            {"at_beat": "7/2", "control": "vibrato_depth", "value": 0},
        )
        plain, expressive = decode_tracks(midi_bytes()), decode_tracks(midi_bytes(gestures))
        cc = [e for e in expressive[1] if e[1] & 0xf0 == 0xb0]
        self.assertEqual(cc, [
            (0, 0xb0, (1, 88)),          # existing SFZ initial control
            (0, 0xb0, (1, 0)),           # first note begins dry
            (240, 0xb0, (1, 88)),        # vibrato after half beat
            (1680, 0xb0, (1, 0)),        # natural fade before release
        ])
        self.assertEqual(
            [e for e in expressive[1] if e[1] & 0xf0 in (0x80, 0x90)],
            [e for e in plain[1] if e[1] & 0xf0 in (0x80, 0x90)],
        )
        self.assertEqual(expressive[2], plain[2])  # BASS: no controller leaks

    def test_genre_independent_and_opt_in(self):
        self.assertIn(b"\xb0\x01\x58", midi_bytes(plan(
            {"at_beat": "1", "control": "vibrato_depth", "value": 88}
        )))
        self.assertNotIn(b"\xb0\x01\x58", MidiAdapter().render(
            make_package(expression=None, includes_initial_cc=False), "fixture"
        ).payload)

    def test_wrong_sound_program_blocked(self):
        with self.assertRaisesRegex(PerformanceGestureError, "CAPABILITY_RESOURCE_MISMATCH"):
            midi_bytes(plan(
                {"at_beat": "1", "control": "vibrato_depth", "value": 88},
                program="Programs/composer-electric.sfz",
            ))

    def test_nonexistent_controller_or_patch_blocked(self):
        with self.assertRaisesRegex(PerformanceGestureError, "CONTROL_NOT_SUPPORTED"):
            midi_bytes(plan(
                {"at_beat": "1", "control": "korg_DNC_CC80", "value": 127},
            ))
        with self.assertRaisesRegex(PerformanceGestureError, "UNKNOWN_OR_UNREADABLE"):
            midi_bytes(plan(
                {"at_beat": "1", "control": "vibrato_depth", "value": 88},
                cap="ANY_YAMAHA_OR_KORG_VOICE",
            ))

    def test_negative_and_out_of_range_refused(self):
        for wrong in (-1, 128, True, "127", 88.2):
            with self.subTest(value=wrong), self.assertRaises(PerformanceGestureError):
                midi_bytes(plan({"at_beat": "1", "control": "vibrato_depth", "value": wrong}))
        for beat in ("-1/2", "NAN", "1/0"):
            with self.subTest(beat=beat), self.assertRaises(PerformanceGestureError):
                midi_bytes(plan({"at_beat": beat, "control": "vibrato_depth", "value": 88}))

    def test_polyphonic_overlap_refused(self):
        chords = (
            MusicalEvent("L1", "LEAD", "electric_guitar", Fraction(0), Fraction(2), 64, 90),
            MusicalEvent("L2", "LEAD", "electric_guitar", Fraction(0), Fraction(2), 67, 90),
        )
        with self.assertRaisesRegex(PerformanceGestureError, "ONE_SOUNDING_NOTE"):
            midi_bytes(plan({"at_beat": "1", "control": "vibrato_depth", "value": 88}), chords)

    def test_release_reset_and_duplicate_timing(self):
        self.assertIn(b"\xb0\x01\x00", midi_bytes(plan(
            {"at_beat": "4", "control": "vibrato_depth", "value": 0}
        )))
        with self.assertRaisesRegex(PerformanceGestureError, "ONE_SOUNDING_NOTE"):
            midi_bytes(plan({"at_beat": "5", "control": "vibrato_depth", "value": 88}))
        with self.assertRaisesRegex(PerformanceGestureError, "DUPLICATE_CONTROLLER"):
            midi_bytes(plan(
                {"at_beat": "1", "control": "vibrato_depth", "value": 88},
                {"at_beat": "1", "control": "vibrato_depth", "value": 0},
            ))

    def test_incompatible_midi_note_instrument_refused(self):
        not_guitar = (
            MusicalEvent("L1", "LEAD", "clarinet_bb", Fraction(0), Fraction(2), 64, 90),
        )
        with self.assertRaisesRegex(PerformanceGestureError, "CAPABILITY_INSTRUMENT_MISMATCH"):
            midi_bytes(plan({"at_beat": "1", "control": "vibrato_depth", "value": 88}), not_guitar)


if __name__ == "__main__":
    unittest.main(verbosity=2)
