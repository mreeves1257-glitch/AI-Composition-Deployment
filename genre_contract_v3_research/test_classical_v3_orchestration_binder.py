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
from classical_v3_note_realizer import realize as realize_notes, validate as validate_notes
from classical_v3_orchestration_binder import bind, validate


class ClassicalV3OrchestrationBinderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = snapshot_for("Classical")
        cls.package = resolve_variant(
            cls.profile, "CLASSICAL_PERIOD_ORCHESTRAL")

    def _one(self, seed):
        structure = compile_plan(
            self.package, tempo_bpm=112, meter="4/4", mode="quick",
            seed=seed, tonic_pc=0, tonal_mode="major")
        self.assertEqual(validate_plan(structure)["status"], "PASS")
        note_plan = realize_notes(structure)
        self.assertEqual(validate_notes(note_plan, structure)["status"], "PASS")
        orchestration = bind(note_plan, structure, self.package)
        summary = validate(orchestration, note_plan, structure)
        return structure, note_plan, orchestration, summary

    def test_seed_zero_uses_v3_period_sections_without_note_loss(self):
        _, notes, orchestration, summary = self._one(0)
        self.assertEqual(summary["status"], "PASS")
        self.assertEqual(summary["source_note_assignment_pct"], 100)
        self.assertEqual(summary["range_valid_pct"], 100)
        self.assertEqual(
            len(orchestration["primary_assignments"]),
            len(notes["notes"]),
        )
        self.assertGreaterEqual(summary["foreground_unique_section_count"], 3)
        self.assertFalse(summary["brass_foreground_default"])
        self.assertFalse(summary["percussion_foreground_default"])
        self.assertEqual(summary["inactive_family_roles_used"], [])
        self.assertFalse(summary["resource_mapping_bound"])
        self.assertFalse(summary["audio_generated"])

    def test_multiple_seeds_preserve_foreground_handoffs_and_support(self):
        for seed in range(32):
            _, _, _, summary = self._one(seed)
            self.assertEqual(summary["source_note_assignment_pct"], 100)
            self.assertEqual(summary["range_valid_pct"], 100)
            self.assertEqual(
                summary["preferred_foreground_owner_phrase_pct"], 100)
            self.assertTrue(
                {"VIOLIN_II", "VIOLA", "CELLO"}.issubset(
                    set(summary["support_sections"])))
            self.assertGreaterEqual(
                summary["foreground_unique_section_count"], 3)

    def test_period_variant_does_not_activate_broad_family_extras(self):
        _, _, orchestration, _ = self._one(5)
        inactive = set(orchestration["intentionally_inactive_family_roles"])
        used = {
            a["section_id"] for a in orchestration["primary_assignments"]
        }
        self.assertTrue(
            {"TROMBONE_FAMILY","PERCUSSION","TUBA_VARIANT_DEPENDENT"}
            .issubset(inactive))
        self.assertFalse(used & inactive)


if __name__ == "__main__":
    unittest.main()
