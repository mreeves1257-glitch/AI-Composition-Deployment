from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
FORWARD = ROOT / "current_master_forward"
if str(FORWARD) not in sys.path:
    sys.path.insert(0, str(FORWARD))

from genre_contract_v3_execution_bridge import snapshot_for
from classical_v3_variant_package import resolve as resolve_variant
from classical_v3_structural_compiler import compile_plan, validate_plan
from classical_composition import build_classical_setup


class ClassicalV3StructuralCompilerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = snapshot_for("Classical")
        cls.package = resolve_variant(
            cls.profile, "CLASSICAL_PERIOD_ORCHESTRAL")

    def test_quick_plan_rejects_old_failure_shape(self):
        plan = compile_plan(
            self.package, tempo_bpm=112, meter="4/4", mode="quick", seed=0)
        summary = validate_plan(plan)
        self.assertEqual(summary["status"], "PASS")
        self.assertEqual(summary["bar_count"], 24)
        self.assertGreaterEqual(len(summary["phrase_lengths"]), 3)
        self.assertGreaterEqual(len(summary["cadence_types"]), 3)
        self.assertLessEqual(summary["single_event_bar_percent"], 10)
        self.assertLessEqual(summary["maximum_harmony_duration_qb"], 2.0)
        self.assertEqual(summary["simultaneous_support_minimum_voices"], 3)
        self.assertTrue(summary["foreground_melody_required_every_bar"])
        self.assertFalse(summary["audio_generated"])

    def test_multiple_seeds_are_structurally_valid(self):
        for seed in range(32):
            plan = compile_plan(
                self.package, tempo_bpm=112, meter="4/4",
                mode="quick", seed=seed)
            summary = validate_plan(plan)
            self.assertEqual(summary["status"], "PASS")

    def test_normal_plan_is_not_fixed_eight_bar_form(self):
        plan = compile_plan(
            self.package, tempo_bpm=112, meter="4/4", mode="normal", seed=7)
        summary = validate_plan(plan)
        self.assertGreater(summary["bar_count"], 24)
        self.assertGreaterEqual(len(summary["phrase_lengths"]), 4)
        self.assertNotEqual(summary["phrase_lengths"], [8])

    def test_specialized_classical_path_binds_v3_structure_without_legacy_notes(self):
        setup = build_classical_setup(
            self.profile,
            mode="quick",
            creation_seed=0,
            v3_variant_package=self.package,
            v3_piece_intent={
                "intent_id":"TEST_CLASSICAL_PERIOD_ALLEGRO_MODERATO",
                "tempo_bpm":112,
                "meter":"4/4",
                "diagnostic_only":True,
            },
        )
        self.assertEqual(setup["status"], "PASS")
        self.assertFalse(setup["legacy_classical_generator_executed"])
        self.assertGreater(len(setup["events"]), 0)
        self.assertTrue(setup["v3_symbolic_diagnostic_only"])
        self.assertFalse(setup["audio_authority"])
        self.assertFalse(setup["legacy_note_generator_used"])
        self.assertEqual(setup["classical_v3_structural_validation"]["status"], "PASS")
        self.assertEqual(setup["classical_v3_structural_plan"]["schema"], "CLASSICAL_V3_STRUCTURAL_PLAN_001")
        self.assertEqual(setup["classical_v3_abstract_note_validation"]["status"], "PASS")
        self.assertEqual(
            setup["classical_v3_abstract_note_validation"]["melody_with_three_voice_support_overlap_pct"],
            100,
        )
        self.assertEqual(
            setup["classical_v3_canonical_orchestration_validation"]["status"],
            "PASS",
        )
        self.assertEqual(
            setup["genre_v3_instrument_authority"]["authority"],
            "CLASSICAL_V3_VARIANT_CANONICAL_ORCHESTRATION",
        )

    def test_requires_explicit_supported_meter_and_tempo(self):
        with self.assertRaises(ValueError):
            compile_plan(self.package, tempo_bpm=30, meter="4/4")
        with self.assertRaises(ValueError):
            compile_plan(self.package, tempo_bpm=112, meter="3/4")


if __name__ == "__main__":
    unittest.main()
