import unittest

from genre_contract_v3_research.classical_melody_validation import aggregate_validation


class ClassicalMelodyValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result=aggregate_validation(seeds=32)

    def test_research_only_and_shared_harmony(self):
        self.assertEqual(self.result["status"],"PASS")
        self.assertTrue(self.result["research_only"])
        self.assertFalse(self.result["live_runtime_modified"])
        self.assertTrue(self.result["neutral_harmony_shared"])

    def test_structural_melodic_integrity(self):
        for variant,data in self.result["variants"].items():
            means=data["means"]
            worst=data["worst_case"]
            self.assertEqual(means["bar_downbeat_chord_tone_pct"],100,variant)
            self.assertEqual(means["cadence_target_pct"],100,variant)
            self.assertGreaterEqual(means["motif_return_bucket_match_pct"],70,variant)
            self.assertGreaterEqual(means["large_leap_recovery_pct"],78,variant)
            self.assertLessEqual(worst["max_interval_semitones"],12,variant)

    def test_period_contrast_is_not_just_register(self):
        c=self.result["variants"]["CLASSICAL_PERIOD_TOPLINE"]["means"]
        r=self.result["variants"]["ROMANTIC_TONAL_TOPLINE"]["means"]
        self.assertLess(r["notes_per_qb"],c["notes_per_qb"]-0.3)
        self.assertGreater(r["mean_abs_interval"],c["mean_abs_interval"]+0.25)
        self.assertLess(r["step_pct"],c["step_pct"]-7)
        self.assertGreater(r["leap5_pct"],c["leap5_pct"]+5)
        self.assertGreater(r["mean_note_duration_qb"],c["mean_note_duration_qb"]+0.10)


if __name__=="__main__":
    unittest.main()
