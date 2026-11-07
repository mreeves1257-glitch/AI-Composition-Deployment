import unittest

from genre_contract_v3_research.classical_voice_leading_validation import aggregate_validation


class ClassicalVoiceLeadingValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = aggregate_validation(seeds=32)

    def test_research_only(self):
        self.assertEqual(self.result["status"], "PASS")
        self.assertTrue(self.result["research_only"])
        self.assertFalse(self.result["live_runtime_modified"])
        self.assertEqual(self.result["voice_model"], "ABSTRACT_SATB")

    def test_voice_leading_integrity(self):
        for variant, data in self.result["variants"].items():
            means = data["means"]
            worst = data["worst_case"]
            self.assertEqual(means["voice_crossings"], 0, variant)
            self.assertEqual(means["parallel_perfect_5_8"], 0, variant)
            self.assertEqual(means["full_essential_coverage_pct"], 100, variant)
            self.assertEqual(means["bass_inversion_accuracy_pct"], 100, variant)
            self.assertEqual(means["doubled_leading_tone_event_pct"], 0, variant)
            self.assertLessEqual(worst["max_leap_semitones"], 12, variant)
            self.assertLessEqual(worst["p95_leap_semitones"], 7, variant)
            self.assertLessEqual(worst["mean_leap_semitones"], 2.5, variant)
            self.assertGreaterEqual(worst["minimum_common_tone_transition_pct"], 45, variant)

    def test_tendency_tone_resolution(self):
        classical = self.result["variants"]["CLASSICAL_PERIOD_TONAL"]["means"]
        romantic = self.result["variants"]["ROMANTIC_TONAL_EXPANDED"]["means"]
        self.assertGreaterEqual(classical["leading_tone_resolution_pct"], 95)
        self.assertGreaterEqual(classical["dominant_seventh_resolution_pct"], 65)
        self.assertGreaterEqual(romantic["leading_tone_resolution_pct"], 80)
        self.assertGreaterEqual(romantic["dominant_seventh_resolution_pct"], 75)


if __name__ == "__main__":
    unittest.main()
