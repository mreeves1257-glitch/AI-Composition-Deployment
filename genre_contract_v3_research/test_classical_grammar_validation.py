import unittest
from genre_contract_v3_research.classical_grammar_validation import aggregate_validation


class ClassicalGrammarValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = aggregate_validation(seeds=32)

    def test_research_only(self):
        self.assertEqual(self.result["status"], "PASS")
        self.assertTrue(self.result["research_only"])
        self.assertFalse(self.result["live_runtime_modified"])
        self.assertTrue(self.result["abstract_harmony_only"])

    def test_romantic_is_more_tonally_mobile_not_faster(self):
        c = self.result["variants"]["CLASSICAL_PERIOD_TONAL"]["means"]
        r = self.result["variants"]["ROMANTIC_TONAL_EXPANDED"]["means"]
        self.assertGreater(r["localkey_duration_pct"], c["localkey_duration_pct"] + 15)
        self.assertGreater(r["applied_pct"], c["applied_pct"])
        self.assertGreater(r["altered_pct"], c["altered_pct"])
        self.assertGreater(r["extended_pct"], c["extended_pct"])
        self.assertLess(abs(r["mean_harmony_qb"] - c["mean_harmony_qb"]), 0.30)

    def test_cadence_families_remain_corpus_shaped(self):
        targets = {
            "CLASSICAL_PERIOD_TONAL": {"PAC":47.35, "HC":35.70, "IAC":6.19, "EC":7.35, "DC":3.41},
            "ROMANTIC_TONAL_EXPANDED": {"PAC":38.43, "HC":34.49, "IAC":22.92, "PC":2.55, "EC":1.16, "DC":0.46},
        }
        for variant, expected in targets.items():
            counts = self.result["variants"][variant]["cadence_counts"]
            total = sum(counts.values())
            for cadence, target in expected.items():
                observed = 100.0 * counts.get(cadence, 0) / total
                tolerance = 5.0 if target >= 3 else 3.0
                self.assertLessEqual(
                    abs(observed - target), tolerance,
                    msg=f"{variant} {cadence}: observed={observed:.2f} target={target:.2f}"
                )


if __name__ == "__main__":
    unittest.main()
