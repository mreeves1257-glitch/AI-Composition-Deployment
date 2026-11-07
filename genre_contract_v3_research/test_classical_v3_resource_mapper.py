from pathlib import Path
import json
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
from classical_v3_orchestration_binder import bind, validate as validate_orchestration
from classical_v3_resource_mapper import map_resources, validate as validate_resources
from instrument_separator import separate_events, verify_instrument_resolution
from instrument_program import InstrumentProgram


class ClassicalV3ResourceMapperTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = snapshot_for("Classical")
        cls.package = resolve_variant(
            cls.profile, "CLASSICAL_PERIOD_ORCHESTRAL")
        cls.instrument_program = InstrumentProgram(
            FORWARD / "instrument_library.json")
        cls.library_ids = set(cls.instrument_program.by_id)

    def _one(self, seed):
        structure = compile_plan(
            self.package, tempo_bpm=112, meter="4/4", mode="quick",
            seed=seed, tonic_pc=0, tonal_mode="major")
        self.assertEqual(validate_plan(structure)["status"], "PASS")

        notes = realize_notes(structure)
        self.assertEqual(validate_notes(notes, structure)["status"], "PASS")

        orchestration = bind(notes, structure, self.package)
        self.assertEqual(
            validate_orchestration(orchestration, notes, structure)["status"],
            "PASS",
        )

        mapped = map_resources(orchestration)
        mapping_summary = validate_resources(
            mapped, orchestration, self.library_ids)

        separated = separate_events("Classical", mapped["events"])
        resolved = self.instrument_program.resolve_events(
            separated["events"])
        self.assertEqual(resolved["status"], "PASS")
        resolution_summary = verify_instrument_resolution(
            separated["manifest"], resolved)
        return (
            structure, notes, orchestration, mapped, mapping_summary,
            separated, resolved, resolution_summary,
        )

    def test_seed_zero_reaches_existing_instrument_resolver_from_v3(self):
        _, _, _, mapped, summary, separated, resolved, verify = self._one(0)
        self.assertEqual(summary["status"], "PASS")
        self.assertEqual(summary["source_assignment_preservation_pct"], 100)
        self.assertEqual(summary["resource_library_presence_pct"], 100)
        self.assertEqual(summary["section_mapping_completion_pct"], 100)
        self.assertTrue(summary["instrument_resolver_ready"])
        self.assertFalse(summary["audio_generated"])
        self.assertEqual(verify["status"], "PASS")
        self.assertEqual(
            verify["expected_registration_count"],
            verify["resolved_registration_count"],
        )
        self.assertGreater(len(resolved["profiles"]), 0)
        self.assertGreater(
            separated["manifest"]["registration_count"], 0)
        for event in mapped["events"]:
            self.assertEqual(
                event["genre_contract_authority"], "GENRE_CONTRACT_V3")

    def test_multiple_seeds_resolve_without_missing_instruments(self):
        for seed in range(16):
            _, _, _, _, summary, _, resolved, verify = self._one(seed)
            self.assertEqual(summary["resource_library_presence_pct"], 100)
            self.assertEqual(resolved["status"], "PASS")
            self.assertEqual(verify["missing_registrations"], [])
            self.assertEqual(verify["extra_registrations"], [])

    def test_expected_classical_sections_survive_separator(self):
        _, _, _, _, _, separated, _, _ = self._one(2)
        roles = {
            r["role"] for r in separated["manifest"]["registrations"]
        }
        self.assertTrue(
            {"VIOLIN_I", "VIOLIN_II", "VIOLA", "CELLO"}
            .issubset(roles))
        self.assertTrue(
            roles & {"FLUTE", "OBOE", "CLARINET"})


if __name__ == "__main__":
    unittest.main()
