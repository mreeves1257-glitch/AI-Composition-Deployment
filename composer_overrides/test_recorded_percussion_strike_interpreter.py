"""Contract tests for original recorded drum layers, no new samples."""
from __future__ import annotations

import json
import unittest
from fractions import Fraction
from pathlib import Path

from AI_Comp_Executable_Output_Core_001 import MusicalEvent
from recorded_percussion_strike_interpreter import (
    UnsupportedPercussionGesture, interpret_recorded_percussion,
    load_map,
)


ROOT = Path(__file__).resolve().parent
BANK_ID = "KARORYFER_BIG_RUSTY_DRUMS"


def sound_binding(program="Programs/composer-snare-lite.sfz", instrument="snare_drum",track="SNARE"):
    return [{
        "track_id":track,"instrument_id":instrument,
        "resource":{
            "resource_type":"SFZ_SAMPLE_LIBRARY",
            "resource_id":BANK_ID,"preferred_mapping":program,
        }
    }]


def note(*,art=None,dynamic=None,velocity=90,instrument="snare_drum",pitch=38,track="SNARE"):
    return MusicalEvent(
        "STROKE1",track,instrument,Fraction(0),Fraction(1,8),
        pitch,velocity,articulation=art,dynamic=dynamic,
    )


class RecordedPercussionContractTests(unittest.TestCase):
    def test_original_musical_notes_remain_byte_equivalent_when_disabled(self):
        original=note(art="ghost_note")
        self.assertEqual(
            interpret_recorded_percussion([original],sound_binding()),(original,)
        )
        self.assertIs(interpret_recorded_percussion([original],sound_binding())[0],original)

    def test_ghost_note_chooses_existing_soft_snare_recording_layer(self):
        original=note(art="ghost_note")
        result=interpret_recorded_percussion([original],sound_binding(),enabled=True)[0]
        self.assertEqual(result.velocity,16)  # actual 1..31 source layer
        self.assertEqual(original.velocity,90)  # no source mutation
        self.assertEqual((result.midi_note,result.start_beats,result.duration_beats),
                         (original.midi_note,original.start_beats,original.duration_beats))

    def test_accents_and_force_use_existing_velocity_layers(self):
        for tag,lo,hi in (
            ("soft_hit",32,63),
            ("accent_hit",64,95),
            ("strong_hit",96,127),
        ):
            with self.subTest(tag=tag):
                selected=interpret_recorded_percussion(
                    [note(art=tag)],sound_binding(),enabled=True
                )[0].velocity
                self.assertGreaterEqual(selected,lo)
                self.assertLessEqual(selected,hi)

    def test_hihat_uses_eight_actual_recorded_dynamic_layers(self):
        original=note(instrument="hi_hat",track="HAT",pitch=42,art="ghost_note")
        resource=sound_binding("Programs/composer-hihat-lite.sfz","hi_hat","HAT")
        a=interpret_recorded_percussion((original,),resource,enabled=True)[0]
        self.assertEqual(a.velocity,8)
        strong=interpret_recorded_percussion((
            note(instrument="hi_hat",track="HAT",pitch=42,art="strong_hit"),
        ),resource,enabled=True)[0]
        self.assertEqual(strong.velocity,119)

    def test_supported_dynamics_without_manual_articulations(self):
        p=note(dynamic="pp")
        q=interpret_recorded_percussion([p],sound_binding(),enabled=True)[0]
        self.assertGreaterEqual(q.velocity,1)
        self.assertLessEqual(q.velocity,31)
        unchanged=note(art="already_composed_technique",dynamic="ff")
        self.assertIs(
            interpret_recorded_percussion([unchanged],sound_binding(),enabled=True)[0],
            unchanged,
        )

    def test_unsupported_instrument_or_mapping_is_not_silently_played(self):
        with self.assertRaisesRegex(UnsupportedPercussionGesture,"UNVERIFIED_INSTRUMENT"):
            interpret_recorded_percussion(
                [note(art="ghost_note")],
                sound_binding("Programs/another-snare.sfz"),
                enabled=True,
            )
        with self.assertRaisesRegex(UnsupportedPercussionGesture,"UNVERIFIED_INSTRUMENT"):
            interpret_recorded_percussion(
                [note(art="ghost_note")],
                sound_binding(instrument="piano"),
                enabled=True,
            )
        with self.assertRaisesRegex(UnsupportedPercussionGesture,"UNVERIFIED_INSTRUMENT"):
            interpret_recorded_percussion(
                [note(art="ghost_note",pitch=36)],sound_binding(),enabled=True,
            )

    def test_ordinary_historical_rock_and_jazz_articulation_codes_untouched(self):
        for existing in ("rock_kick","rock_backbeat","ride_timekeeping","tom_fill","legato"):
            with self.subTest(existing=existing):
                n=note(art=existing)
                self.assertIs(
                    interpret_recorded_percussion((n,),sound_binding(),enabled=True)[0],n,
                )

    def test_source_manifest_matches_actual_existing_sfz_heredocs(self):
        data=load_map()
        source=(ROOT.parents[1]/"build_current_composer.sh").read_text()
        self.assertEqual(len(data["programs"]),5)
        self.assertEqual(data["activated_genres"],[])
        self.assertFalse(data["automatic_application_enabled"])
        for name,p in data["programs"].items():
            with self.subTest(program=name):
                stem=Path(p["preferred_mapping"]).name
                begin=f'cat > "$BANK/KARORYFER_BIG_RUSTY_DRUMS/Programs/{stem}" <<\'SFZ\''
                self.assertIn(begin,source)
                excerpt=source.split(begin,1)[1].split("\nSFZ",1)[0]
                self.assertIn("seq_length=4",excerpt)
                self.assertIn("seq_position=2",excerpt)
                self.assertIn("seq_position=3",excerpt)
                self.assertIn("seq_position=4",excerpt)
                expected=1
                for start,end in p["velocity_layer_ranges"]:
                    self.assertEqual(start,expected)
                    self.assertLessEqual(start,end)
                    expected=end+1
                self.assertEqual(expected,128)
                self.assertEqual(p["round_robin_count"],4)


if __name__=="__main__":
    unittest.main(verbosity=2)
