"""Offline regressions for the isolated Jazz Ballad arranger layer."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from genre_styles.Jazz.jazz_arranger_style import arrange_jazz_ballad, section_for_bar, CLARINET_RANGE, BASS_RANGE
from genre_styles.Jazz.jazz_balance_contract import apply_jazz_ballad_balance
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

    def test_clarinet_has_own_line_different_from_original_piano(self):
        ctx, original = fake_score(48)
        arranged = arrange_jazz_ballad(original, ctx, 8)
        piano_before = [e for e in original if e["track_id"] == "HARMONY"]
        piano_after = [e for e in arranged if e["track_id"] == "HARMONY"]
        self.assertEqual(piano_after, piano_before, "Never change piano performance")
        clarinet = [e for e in arranged if e["track_id"] == "LEAD"]
        self.assertEqual(len(clarinet), 96, "Keep a complete separate clarinet line")
        self.assertTrue(all(e["instrument_id"] == "clarinet_bb" for e in clarinet))
        self.assertTrue(all(CLARINET_RANGE[0] <= e["midi"] <= CLARINET_RANGE[1]
                            for e in clarinet))
        self.assertTrue(any(abs(e["start_beat"] - round(e["start_beat"])) > 0.25
                            for e in clarinet),
                        "Clarinet entrance must be distinct from on-beat piano")
        # A jazz ballad melody may share chord tones, but should not simply
        # shadow the piano in both pitch and entrance at the same time.
        exact_doublings = 0
        for note in clarinet:
            if any(p["midi"] == note["midi"] and
                   abs(p["start_beat"] - note["start_beat"]) < 0.01
                   for p in piano_before):
                exact_doublings += 1
        self.assertLess(exact_doublings, len(clarinet) // 10)

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

    def _six_track_mix(self):
        ids = {
            "LEAD": "clarinet_bb", "BASS": "double_bass",
            "HARMONY": "electric_piano", "SNARE": "snare_drum",
            "HAT": "hi_hat", "KICK": "kick_drum_rock",
        }
        metrics = {
            "LEAD": (-38.2,-56.1), "BASS": (-18.0,-44.7),
            "HARMONY": (-16.5,-35.7), "SNARE": (-34.25,-50.3),
            "HAT": (-35.5,-62.6), "KICK": (-25.1,-49.5),
        }
        profiles = [{"track_id":k,"instrument_id":v} for k,v in ids.items()]
        resources = [{"track_id":k,"resource":{
            "target_gain_db":-6.0,"resource_id":"RECORDED_"+k,
            "preferred_mapping":k+".sfz",
        }} for k in ids]
        result = {"genre":"Jazz Ballad","modules":{
            "instrument":{"profiles":profiles},
            "target":{"resolved_resources":resources},
        }}
        stems = [{"track_id":k,"instrument_id":v,"note_count":50,
                  "peak_dbfs":metrics[k][0],"rms_dbfs":metrics[k][1]}
                 for k,v in ids.items()]
        return result,stems

    def test_equal_intensity_all_six_and_source_preservation(self):
        from genre_styles.Jazz.jazz_balance_contract import (
            JAZZ_INTENSITY_WEIGHTS,JAZZ_BALANCE_VERSION,
        )
        original,stems=self._six_track_mix()
        mixed=apply_jazz_ballad_balance(original,stems)
        self.assertEqual(mixed["jazz_mix_instruction"]["goal"],
                         "EQUAL_PERCEIVED_INTENSITY")
        self.assertEqual(mixed["jazz_mix_instruction"]["name"],JAZZ_BALANCE_VERSION)
        self.assertEqual(len(mixed["jazz_mix_instruction"]["adjusted_tracks"]),6)
        self.assertLessEqual(mixed["jazz_mix_instruction"]["post_mix_proxy_spread_db"],1.0)
        resources={x["track_id"]:x["resource"] for x in
                   mixed["modules"]["target"]["resolved_resources"]}
        self.assertEqual(original["modules"]["target"]["resolved_resources"][0]
                         ["resource"]["target_gain_db"],-6.0)
        self.assertEqual(resources["HARMONY"]["preferred_mapping"],"HARMONY.sfz")
        self.assertEqual(resources["LEAD"]["resource_id"],"RECORDED_LEAD")
        scores=[]
        for stem in stems:
            track=stem["track_id"]
            w_rms,w_peak=JAZZ_INTENSITY_WEIGHTS[track]
            intensity=w_rms*stem["rms_dbfs"]+w_peak*stem["peak_dbfs"]
            scores.append(intensity+resources[track]["target_gain_db"])
        self.assertLessEqual(max(scores)-min(scores),1.0)
        self.assertGreater(resources["LEAD"]["target_gain_db"],
                           resources["HARMONY"]["target_gain_db"])
        self.assertGreater(resources["BASS"]["target_gain_db"],
                           resources["HARMONY"]["target_gain_db"])

    def test_equal_intensity_never_changes_other_genres(self):
        score,stems=self._six_track_mix()
        for genre in ("ROCK","Swing","Big Band","Jazz Fusion"):
            data={**score,"genre":genre}
            self.assertIs(apply_jazz_ballad_balance(data,stems),data)
        self.assertIs(apply_jazz_ballad_balance(score),score)

    def test_equal_intensity_fails_missing_or_silent_instruments(self):
        score,stems=self._six_track_mix()
        with self.assertRaisesRegex(ValueError,"MISSING_TRACKS"):
            apply_jazz_ballad_balance(score,stems[:-1])
        with self.assertRaisesRegex(ValueError,"EMPTY_AUDIO_PART"):
            apply_jazz_ballad_balance(score,
                 [{**x,"note_count":0} if x["track_id"]=="LEAD" else x for x in stems])
        with self.assertRaisesRegex(ValueError,"NO_MEASURABLE_AUDIO"):
            apply_jazz_ballad_balance(score,
                 [{**x,"rms_dbfs":float("-inf")} if x["track_id"]=="BASS" else x
                  for x in stems])
        with self.assertRaisesRegex(ValueError,"WRONG_AUDIO_SOURCE"):
            apply_jazz_ballad_balance(score,
                 [{**x,"instrument_id":"electric_piano"} if x["track_id"]=="LEAD" else x
                  for x in stems])

    def test_equal_intensity_gain_limit_rejects_unfixable_recording(self):
        score,stems=self._six_track_mix()
        excessive=[{**x,"peak_dbfs":-140.0,"rms_dbfs":-170.0}
                   if x["track_id"]=="LEAD" else x for x in stems]
        with self.assertRaisesRegex(ValueError,"OUT_OF_RANGE"):
            apply_jazz_ballad_balance(score,excessive)

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
