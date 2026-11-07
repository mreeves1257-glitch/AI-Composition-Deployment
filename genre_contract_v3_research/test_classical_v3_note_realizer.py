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
from classical_v3_note_realizer import realize, validate


class ClassicalV3NoteRealizerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = snapshot_for("Classical")
        cls.package = resolve_variant(
            cls.profile, "CLASSICAL_PERIOD_ORCHESTRAL")

    def _one(self, seed):
        structural = compile_plan(
            self.package,
            tempo_bpm=112,
            meter="4/4",
            mode="quick",
            seed=seed,
            tonic_pc=0,
            tonal_mode="major",
        )
        self.assertEqual(validate_plan(structural)["status"], "PASS")
        plan = realize(structural)
        summary = validate(plan, structural)
        return structural, plan, summary

    def test_seed_zero_rejects_previous_failure_shape(self):
        _, plan, summary = self._one(0)
        self.assertEqual(summary["status"], "PASS")
        self.assertEqual(summary["support_harmony_attack_pass_pct"], 100)
        self.assertEqual(summary["structural_melody_chord_tone_pct"], 100)
        self.assertEqual(summary["cadence_target_pct"], 100)
        self.assertEqual(
            summary["melody_with_three_voice_support_overlap_pct"], 100)
        self.assertGreaterEqual(
            summary["melody_notes_per_quarterbeat"], 1.6)
        self.assertLessEqual(
            summary["melody_notes_per_quarterbeat"], 2.7)
        self.assertLessEqual(summary["melody_max_duration_qb"], 1.0)
        self.assertGreaterEqual(summary["melody_distinct_duration_count"], 2)
        self.assertGreaterEqual(summary["melody_distinct_onset_gap_count"], 2)
        self.assertFalse(summary["audio_generated"])
        self.assertFalse(summary["instrumentation_bound"])
        roles = {n["role"] for n in plan["notes"]}
        self.assertEqual(
            roles,
            {"SUPPORT_BASS","SUPPORT_TENOR","SUPPORT_ALTO","MELODY"},
        )

    def test_multiple_seeds_pass_vertical_harmony_and_texture(self):
        for seed in range(32):
            _, _, summary = self._one(seed)
            self.assertEqual(summary["support_harmony_attack_pass_pct"], 100)
            self.assertEqual(summary["structural_melody_chord_tone_pct"], 100)
            self.assertEqual(summary["cadence_target_pct"], 100)
            self.assertEqual(
                summary["melody_with_three_voice_support_overlap_pct"], 100)
            self.assertGreaterEqual(summary["melody_step_motion_pct"], 35)

    def test_no_instrument_or_audio_authority(self):
        _, plan, summary = self._one(3)
        self.assertFalse(plan["instrumentation_bound"])
        self.assertFalse(plan["audio_approved"])
        self.assertFalse(summary["audio_generated"])
        for note in plan["notes"]:
            self.assertNotIn("instrument_id", note)
            self.assertNotIn("track_id", note)


if __name__ == "__main__":
    unittest.main()
