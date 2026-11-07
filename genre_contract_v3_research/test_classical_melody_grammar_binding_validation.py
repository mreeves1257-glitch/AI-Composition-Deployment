import unittest

from genre_contract_v3_research.classical_melody_grammar_binding_validation import aggregate_validation


class ClassicalMelodyGrammarBindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result=aggregate_validation(seeds=32)

    def test_research_only(self):
        self.assertEqual(self.result["status"],"PASS")
        self.assertTrue(self.result["research_only"])
        self.assertFalse(self.result["live_runtime_modified"])
        self.assertFalse(self.result["orchestration_enabled"])

    def test_harmonic_binding_integrity(self):
        for variant,data in self.result["variants"].items():
            means=data["means"]
            worst=data["worst_case"]
            self.assertEqual(means["structural_chord_tone_pct"],100,variant)
            self.assertEqual(means["cadence_chord_tone_pct"],100,variant)
            self.assertGreaterEqual(means["motif_return_bucket_match_pct"],75,variant)
            self.assertLessEqual(worst["max_interval_semitones"],12,variant)

    def test_nonchord_resolution_and_period_contrast(self):
        c=self.result["variants"]["CLASSICAL_PERIOD_TOPLINE"]["means"]
        r=self.result["variants"]["ROMANTIC_TONAL_TOPLINE"]["means"]
        self.assertGreaterEqual(c["nonchord_step_resolution_pct"],70)
        self.assertGreaterEqual(r["nonchord_step_resolution_pct"],60)
        self.assertGreaterEqual(c["large_leap_recovery_pct"],80)
        self.assertGreaterEqual(r["large_leap_recovery_pct"],75)
        self.assertLess(r["notes_per_qb"],c["notes_per_qb"]-0.3)
        self.assertGreater(r["mean_abs_interval"],c["mean_abs_interval"]+0.25)
        self.assertLess(r["step_pct"],c["step_pct"]-5)
        self.assertGreater(r["leap5_pct"],c["leap5_pct"]+5)


if __name__=="__main__":
    unittest.main()
