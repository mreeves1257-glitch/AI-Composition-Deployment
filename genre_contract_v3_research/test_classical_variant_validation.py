import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "genre_contract_v3_research"))

import classical_variant_validation as cvv


class ClassicalVariantValidationTests(unittest.TestCase):
    def setUp(self):
        self.result = cvv.build_validation(seed=0, mode="quick")
        self.classical = self.result["variants"]["CLASSICAL_PERIOD_BASELINE"]
        self.romantic = self.result["variants"]["LATE_ROMANTIC_EXPANDED"]

    def test_same_plan_for_both_variants(self):
        self.assertEqual(self.classical["plan_sha256"], self.romantic["plan_sha256"])
        self.assertEqual(self.result["plan_sha256"], self.classical["plan_sha256"])

    def test_classical_period_foreground_balance(self):
        fg = self.classical["foreground_bar_percent"]
        self.assertGreater(fg.get("STRINGS", 0), fg.get("WOODWINDS", 0))
        self.assertEqual(fg.get("BRASS", 0), 0)
        self.assertGreater(fg.get("WOODWINDS", 0), 0)

    def test_late_romantic_allows_real_brass_foreground(self):
        fg = self.romantic["foreground_bar_percent"]
        self.assertGreater(fg.get("STRINGS", 0), 0)
        self.assertGreater(fg.get("WOODWINDS", 0), 0)
        self.assertGreater(fg.get("BRASS", 0), 0)
        self.assertGreater(self.romantic["brass_foreground_bars"], 0)

    def test_activity_windows_track_evidence_targets(self):
        # Quick mode has 28 bars, so one bar is about 3.57 percentage points.
        tolerance = 3.6
        for summary in (self.classical, self.romantic):
            for family, target in summary["activity_target_percent"].items():
                observed = summary["active_bar_percent"].get(family, 0)
                self.assertLessEqual(
                    abs(observed - target),
                    tolerance,
                    msg=f"{summary['variant_id']} {family}: {observed} vs {target}",
                )

    def test_late_romantic_brass_is_more_active(self):
        ca = self.classical["active_bar_percent"].get("BRASS", 0)
        ro = self.romantic["active_bar_percent"].get("BRASS", 0)
        self.assertGreater(ro, ca)

    def test_no_gain_based_solution(self):
        self.assertFalse(self.classical["gain_fields_present"])
        self.assertFalse(self.romantic["gain_fields_present"])

    def test_research_only(self):
        self.assertTrue(self.result["research_only"])
        self.assertFalse(self.result["live_runtime_modified"])


if __name__ == "__main__":
    unittest.main()
