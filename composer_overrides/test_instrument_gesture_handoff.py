"""Isolated Composer output_handoff -> note gestures -> exact MIDI tests.

Uses the preserved Composer's ACTUAL build_execution_package and Output Core;
no genre activated, no new notes, no audio renderer or user-side test.
"""
from __future__ import annotations

import json
import unittest
from dataclasses import replace

from output_handoff import build_execution_package
from AI_Comp_Executable_Output_Core_001 import MidiAdapter
from instrument_gesture_handoff import InstrumentGestureRoutingError


def engine_result(articulation=None, *,
                  track="SOLO", program="Programs/composer-electric-lead.sfz",
                  instrument="lead_guitar", resource_id="KARORYFER_SHINYGUITAR",
                  target_instrument=None, overlap=False):
    events = [
        {"track_id": track, "instrument_id": instrument, "start_beat": 0,
         "duration_beats": 4, "midi": 60, "velocity": 100,
         "articulation": articulation, "drum": False}
    ]
    if overlap:
        events.append({
            "track_id":track,"instrument_id":instrument,"start_beat":1,
            "duration_beats":1,"midi":64,"velocity":90,"drum":False
        })
    resolved = [{
        "track_id": track, "instrument_id": target_instrument or instrument,
        "resource": {
            "resource_type": "SFZ_SAMPLE_LIBRARY",
            "resource_id": resource_id, "preferred_mapping": program,
            "midi_mapping": {"initial_cc": {"1": 0}}
        }
    }]
    return {
        "genre": "Independent Genre, Not Rock/Jazz",
        "modules": {
            "theory": {
                "meter": "4/4", "tempo_bpm": 120,
                "composition_fingerprint": "explicit-gesture-fixture",
                "events": events,
            },
            "target": {"resolved_resources": resolved},
        },
    }


def independently_authored_midi_plan():
    """Manual note-gesture reference: specifies exact timing, not note labels."""
    return {
        "SOLO": {
            "capability_id": "SHINYGUITAR_RECORDED_LEAD_CC1_V1",
            "resource_id": "KARORYFER_SHINYGUITAR",
            "preferred_mapping": "Programs/composer-electric-lead.sfz",
            "gestures": [
                {"at_beat": "0", "control": "vibrato_depth", "value": 0},
                {"at_beat": "1", "control": "vibrato_depth", "value": 88},
                {"at_beat": "7/2", "control": "vibrato_depth", "value": 0},
            ],
        },
    }


def midi_bytes(result):
    return MidiAdapter().render(
        build_execution_package(result), "source-fingerprint-fixture"
    ).payload


class InstrumentAwareComposerHandoffTests(unittest.TestCase):
    def test_authorized_instrument_note_produces_timed_midi(self):
        actual = engine_result("sustained_vibrato")
        pkg = build_execution_package(actual)
        metadata = dict(pkg.metadata)
        plan = json.loads(metadata["expressive_gesture_plan"])
        self.assertEqual(sorted(plan), ["SOLO"])
        self.assertEqual(plan["SOLO"]["capability_id"], "SHINYGUITAR_RECORDED_LEAD_CC1_V1")
        self.assertEqual(plan["SOLO"]["gesture_source"], "note_articulation")
        data = midi_bytes(actual)
        self.assertIn(bytes((0xB0, 1, 88)), data)  # timed CC1 on
        self.assertIn(bytes((0xB0, 1, 0)), data)   # note start/release CC1 off
        self.assertIn(bytes((0x90, 60, 100)), data)
        self.assertIn(bytes((0x80, 60, 0)), data)

    def test_without_explicit_articulation_original_behavior_byte_exact(self):
        baseline = engine_result()
        pkg = build_execution_package(baseline)
        self.assertNotIn("expressive_gesture_plan", dict(pkg.metadata))
        unchanged = midi_bytes(baseline)
        self.assertIn(bytes((0x90, 60, 100)), unchanged)
        self.assertNotIn(bytes((0xB0, 1, 88)), unchanged)

    def test_selected_program_not_just_instrument_label_controls_permission(self):
        with self.assertRaisesRegex(InstrumentGestureRoutingError, "NO_UNIQUE_VERIFIED"):
            build_execution_package(engine_result(
                "sustained_vibrato", program="Programs/composer-electric.sfz"
            ))
        with self.assertRaisesRegex(InstrumentGestureRoutingError, "NO_UNIQUE_VERIFIED"):
            build_execution_package(engine_result(
                "sustained_vibrato", resource_id="WRONG_SAMPLE_LIBRARY"
            ))

    def test_wrong_track_instrument_identity_rejected(self):
        with self.assertRaisesRegex(InstrumentGestureRoutingError, "NO_UNIQUE_VERIFIED"):
            build_execution_package(engine_result(
                "sustained_vibrato", instrument="clarinet_bb"
            ))
        with self.assertRaisesRegex(InstrumentGestureRoutingError, "RESOLVED_INSTRUMENT_ID_MISMATCH"):
            build_execution_package(engine_result(
                "sustained_vibrato", target_instrument="snare_drum"
            ))

    def test_missing_or_ambiguous_resolved_track_fails_closed(self):
        d=engine_result("sustained_vibrato")
        d["modules"]["target"]["resolved_resources"]=[]
        with self.assertRaisesRegex(InstrumentGestureRoutingError,"TRACK_RESOURCE_NOT_RESOLVED"):
            build_execution_package(d)
        d=engine_result("sustained_vibrato")
        d["modules"]["target"]["resolved_resources"].append(
            d["modules"]["target"]["resolved_resources"][0].copy()
        )
        with self.assertRaisesRegex(InstrumentGestureRoutingError,"AMBIGUOUS_TRACK_RESOURCE"):
            build_execution_package(d)

    def test_no_unauthorized_channel_wide_vibrato_on_chords(self):
        d=engine_result("sustained_vibrato",overlap=True)
        with self.assertRaisesRegex(ValueError,"CHANNEL_POLYPHONY"):
            midi_bytes(d)

    def test_unrelated_articulations_not_mistaken_for_native_vibrato(self):
        d=engine_result("legato")
        self.assertNotIn("expressive_gesture_plan",dict(build_execution_package(d).metadata))
        self.assertNotIn(bytes((0xB0,1,88)),midi_bytes(d))

    def test_non_guitar_expressive_tag_does_not_fake_a_sound(self):
        with self.assertRaisesRegex(InstrumentGestureRoutingError, "NO_UNIQUE_VERIFIED"):
            build_execution_package(engine_result(
                "sustained_vibrato", instrument="piano", resource_id="PIANO_BANK",
                program="piano.sfz",
            ))


    def test_note_annotation_and_identical_gestures_have_same_midi_events(self):
        tagged = build_execution_package(engine_result("sustained_vibrato"))
        untagged = build_execution_package(engine_result(None))
        manual = replace(untagged, metadata=untagged.metadata + (
            ("expressive_gesture_plan", json.dumps(independently_authored_midi_plan())),
        ))
        raw_auto = MidiAdapter().render(tagged,"same-fingerprint").payload
        raw_manual = MidiAdapter().render(manual,"same-fingerprint").payload
        if raw_auto != raw_manual:
            first = next((i for i,(a,b) in enumerate(zip(raw_auto,raw_manual)) if a!=b),
                         min(len(raw_auto),len(raw_manual)))
            print("ANNOTATION_MIDI_COMPARISON",{
                "auto_length":len(raw_auto),
                "manual_length":len(raw_manual),
                "first_diff_offset":first,
                "auto_near":raw_auto[max(0,first-10):first+35].hex(),
                "manual_near":raw_manual[max(0,first-10):first+35].hex(),
            },flush=True)
        self.assertEqual(raw_auto,raw_manual,"MIDI_SERIALIZATION_DIFF_FROM_NOTE_ANNOTATION")


if __name__ == "__main__":
    unittest.main(verbosity=2)
