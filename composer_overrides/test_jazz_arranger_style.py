"""Offline regressions for the isolated Jazz Ballad arranger layer."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from jazz_arranger_style import arrange_jazz_ballad, section_for_bar, CLARINET_RANGE, BASS_RANGE
from jazz_balance_contract import apply_jazz_ballad_balance
from genre_development_patch import build_jazz_progression


def fake_score(bars=48):
    pitches = [
        (0, 4, 7, 11), (9, 0, 4, 7), (2, 5, 9, 0), (7, 11, 2, 5),
        (5, 9, 0, 4), (4, 7, 11, 2),
    ]
    progression = [pitches[(bar * 3 + bar // 8) % len(pitches)] for bar in range(bars)]
    ctx = {
        "meter": {"numerator": 4, "denominator": 4},
        "key": {"scale_pitch_classes": [0, 2, 4, 5, 7, 9, 11]},
        "harmony": {"chords": [{"pitch_classes": list(p)} for p in progression]},
    }
    events = []
    for bar in range(bars):
        for note in (60, 64, 67, 71):
            events.append({"track_id": "HARMONY", "instrument_id": "electric_piano",
                           "midi": note, "start_beat": bar * 4,
                           "duration_beats": 1.5, "velocity": 68})
        for beat in (0.0, 2.0):
            events.extend([
                {"track_id": "BASS", "instrument_id": "double_bass",
                 "midi": 70, "start_beat": 4 * bar + beat,
                 "duration_beats": 0.7, "velocity": 79},
                {"track_id": "LEAD", "instrument_id": "clarinet_bb",
                 "midi": 95, "start_beat": 4 * bar + beat,
                 "duration_beats": 0.2, "velocity": 80},
                {"track_id": "SNARE", "instrument_id": "snare_drum",
                 "midi": 38, "start_beat": 4 * bar + beat,
                 "duration_beats": 0.1, "velocity": 66},
            ])
    return ctx, events


class JazzArrangerTests(unittest.TestCase):
    def test_real_sample_ranges_and_piano_preserved(self):
        ctx, original = fake_score()
        a = arrange_jazz_ballad(original, ctx, 8)
        track = lambda events, role: [e for e in events if e["track_id"] == role]
        self.assertEqual(track(a, "HARMONY"), track(original, "HARMONY"))
        self.assertEqual(len(track(a, "LEAD")), len(track(original, "LEAD")))
        self.assertEqual(len(track(a, "BASS")), len(track(original, "BASS")))
        self.assertTrue(all(CLARINET_RANGE[0] <= e["midi"] <= CLARINET_RANGE[1]
                            for e in track(a, "LEAD")))
        self.assertTrue(all(BASS_RANGE[0] <= e["midi"] <= BASS_RANGE[1]
                            for e in track(a, "BASS")))
        self.assertGreater(len({e["midi"] for e in track(a, "LEAD")}), 4)
        self.assertLess(len(track(a, "SNARE")), len(track(original, "SNARE")) // 2)

    def test_harmonic_bass_movement(self):
        ctx, original = fake_score()
        a = arrange_jazz_ballad(original, ctx, 0)
        bass = [e for e in a if e["track_id"] == "BASS"]
        for bar in range(48):
            first = [e for e in bass if int(e["start_beat"] // 4) == bar][0]
            self.assertEqual(first["midi"] % 12,
                             ctx["harmony"]["chords"][bar]["pitch_classes"][0])

    def test_sections_have_intro_and_ending(self):
        self.assertEqual(section_for_bar(0, 64), "INTRO")
        self.assertEqual(section_for_bar(9, 64), "MAIN_A")
        self.assertEqual(section_for_bar(20, 64), "MAIN_B")
        self.assertEqual(section_for_bar(60, 64), "ENDING")

    def test_balance_scope(self):
        original = {"genre": "ROCK", "modules": {}}
        self.assertIs(apply_jazz_ballad_balance(original), original)
        original = {"genre": "Swing", "modules": {}}
        self.assertIs(apply_jazz_ballad_balance(original), original)
        profiles = [{"track_id": track, "instrument_id": iid} for track, iid in (
            ("LEAD", "clarinet_bb"), ("BASS", "double_bass"), ("HARMONY", "electric_piano"),
            ("SNARE", "snare_drum"),
        )]
        resources = [{"track_id": p["track_id"], "resource": {"target_gain_db": -6.0}}
                     for p in profiles]
        score = {"genre": "Jazz Ballad",
                 "modules": {"instrument": {"profiles": profiles},
                             "target": {"resolved_resources": resources}}}
        result = apply_jazz_ballad_balance(score)
        self.assertIsNot(result, score)
        self.assertEqual(resources[0]["resource"]["target_gain_db"], -6.0)
        self.assertGreater(result["modules"]["target"]["resolved_resources"][0]
                           ["resource"]["target_gain_db"], -6.0)

    def test_chord_motion_is_not_four_bar_static(self):
        profile = {"resolution_policy": "AUTOMATIC_BASELINE_ALLOWED",
                   "profile_id": "JAZZ_BALLAD_V1"}
        seq = build_jazz_progression("Jazz Ballad", profile, "major", 96, 19)
        self.assertEqual(seq[-1], "I")
        self.assertEqual(len(seq), 96)
        self.assertTrue(all(len(set(seq[i:i + 4])) > 1 for i in range(93)))
        self.assertGreater(len(set(tuple(seq[i:i + 8])
                                   for i in range(0, 88, 8))), 2)

    def test_arranger_does_not_change_input(self):
        ctx, events = fake_score(24)
        snapshot = [dict(e) for e in events]
        arranged = arrange_jazz_ballad(events, ctx, 0)
        self.assertEqual(events, snapshot)
        self.assertEqual(arranged, arrange_jazz_ballad(events, ctx, 0))


if __name__ == "__main__":
    unittest.main()
