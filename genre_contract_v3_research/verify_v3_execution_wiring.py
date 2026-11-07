"""Audit Genre Contract V3 source propagation without generating notes or audio.

Diagnostic only. The experimental reasoning engine is intentionally absent from
this branch. This audit dynamically proves V3 selection/packet propagation and
statically identifies remaining legacy execution authority in the old adapter.
"""
from __future__ import annotations

from pathlib import Path
import ast
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
FORWARD = ROOT / "current_master_forward"
if str(FORWARD) not in sys.path:
    sys.path.insert(0, str(FORWARD))

from genre_contract_v3_execution_bridge import load_master, snapshot_for, execution_packet
from genre_selector import GenreSelector
from genre_v3_instrument_authority import resolve as resolve_v3_instrument_authority
from genre_v3_source_pattern_bridge import resolve_source_roles
from classical_v3_variant_package import resolve as resolve_classical_v3_variant

V3_PATH = ROOT / "genre_contract_v3_research" / "GENRE_CONTRACT_V3_ALL_55.json"
ADAPTER_PATH = FORWARD / "AI_Comp_Genre_Execution_Adapter_002_WORKING_2026-10-02_184019_CDT.py"
CLASSICAL_PATH = FORWARD / "classical_composition.py"
BLUEPRINT_PATH = FORWARD / "genre_communication_blueprint.py"
PERFORMANCE_PATH = FORWARD / "genre_performance_realization.py"
INSTRUMENT_PATH = FORWARD / "instrument_program.py"
ENGINE_PATH = FORWARD / "engine.py"


def _literal_assignment(source: str, name: str):
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return ast.literal_eval(node.value)
    raise RuntimeError(f"STATIC_ASSIGNMENT_NOT_FOUND::{name}")


def main():
    master = load_master()
    contracts = master["contracts"]
    if len(contracts) != 55:
        raise RuntimeError("V3_CONTRACT_COUNT_NOT_55")

    selector = GenreSelector(V3_PATH, None)
    if selector.registry_source != "GENRE_CONTRACT_V3_ALL_55":
        raise RuntimeError("SELECTOR_NOT_V3")

    adapter_source = ADAPTER_PATH.read_text()
    classical_source = CLASSICAL_PATH.read_text()
    communication_source = BLUEPRINT_PATH.read_text()
    performance_source = PERFORMANCE_PATH.read_text()
    instrument_source = INSTRUMENT_PATH.read_text()
    engine_source = ENGINE_PATH.read_text()

    palettes = _literal_assignment(adapter_source, "PALETTES")
    bases = _literal_assignment(adapter_source, "BASE")

    adapter_v3_source_patch = (
        "from genre_contract_v3_execution_bridge import all_snapshots" in adapter_source
        and "profiles=all_snapshots()" in adapter_source
        and "v3_execution_packet(name)" in adapter_source
        and "def __init__(self, profile_registry_path=None, history_path=None)" in adapter_source
        and "self.profile_source='GENRE_CONTRACT_V3_ALL_55'" in adapter_source
        and "profile_registry_path=PROFILE_PATH" not in adapter_source
    )
    adapter_v3_roster_patch = (
        "from genre_v3_instrument_authority import resolve as resolve_v3_instrument_authority" in adapter_source
        and "resolve_genre_parts_with_authority" in adapter_source
        and "genre_v3_instrument_authority" in adapter_source
    )
    if not adapter_v3_source_patch:
        raise RuntimeError("ADAPTER_V3_SOURCE_PATCH_MISSING")
    if not adapter_v3_roster_patch:
        raise RuntimeError("ADAPTER_V3_ROSTER_PATCH_MISSING")

    results = []
    selection_pass = 0
    packet_pass = 0
    v3_explicit_roster = 0
    v3_source_pattern_roles = 0
    legacy_fallback = 0
    controlled_component = 0
    classical_specialized = 0
    structured_section_instances = 0

    required_structured = (
        "musical_grammar",
        "ensemble",
        "performance",
        "production",
        "safeguards",
        "variant_resolution",
    )

    for name, contract in contracts.items():
        snapshot = snapshot_for(name)
        selection = selector.select(name)
        if selection.get("registry_source") != "GENRE_CONTRACT_V3_ALL_55":
            raise RuntimeError(f"SELECTOR_SOURCE_FAIL::{name}")
        if selection["profile"].get("profile_id") != snapshot.get("profile_id"):
            raise RuntimeError(f"SELECTOR_PROFILE_FAIL::{name}")
        selection_pass += 1

        packet = execution_packet(name)
        if packet.get("source") != "GENRE_CONTRACT_V3_ALL_55":
            raise RuntimeError(f"PACKET_SOURCE_FAIL::{name}")
        if packet.get("profile_id") != snapshot.get("profile_id"):
            raise RuntimeError(f"PACKET_PROFILE_FAIL::{name}")
        for field in required_structured:
            if field not in packet:
                raise RuntimeError(f"PACKET_SECTION_MISSING::{name}::{field}")
        packet_pass += 1
        structured_section_instances += sum(packet.get(field) is not None for field in required_structured)

        policy = snapshot.get("resolution_policy")
        v3_instrument = resolve_v3_instrument_authority(name, snapshot)
        if name == "Classical":
            classical_package = resolve_classical_v3_variant(
                snapshot, "CLASSICAL_PERIOD_ORCHESTRAL")
            if classical_package.get("status") != "RESEARCH_PACKAGE_READY_FOR_STRUCTURAL_COMPILER__NOT_AUDIO_APPROVED":
                raise RuntimeError("CLASSICAL_V3_PACKAGE_NOT_RESOLVED")
            authority = "V3_CLASSICAL_SYMBOLIC_ORCHESTRATION_RUNTIME_DIAGNOSTIC"
            classical_specialized += 1
        elif policy != "AUTOMATIC_BASELINE_ALLOWED":
            authority = "CONTROLLED_COMPONENT_INPUT"
            controlled_component += 1
        elif v3_instrument.get("status") == "PASS":
            authority = "GENRE_CONTRACT_V3_EXPLICIT_ROSTER"
            v3_explicit_roster += 1
        else:
            source_roles = resolve_source_roles(name)
            if source_roles.get("status") == "PASS":
                authority = "V3_GOVERNED_SOURCE_PATTERN_ROLES"
                v3_source_pattern_roles += 1
            else:
                authority = "LEGACY_FAMILY_TEMPLATE_AND_STATIC_PALETTE_FALLBACK"
                legacy_fallback += 1

        ensemble = contract.get("ensemble") or {}
        roster = ensemble.get("instrument_roster") or []
        results.append({
            "genre": name,
            "profile_id": snapshot.get("profile_id"),
            "resolution_policy": policy,
            "selector_source": selection.get("registry_source"),
            "execution_packet_source": packet.get("source"),
            "contract_sha256": (snapshot.get("_genre_contract_v3_source") or {}).get("contract_sha256"),
            "instrument_authority_remaining": authority,
            "v3_instrument_authority_status": v3_instrument.get("status"),
            "v3_event_roles": v3_instrument.get("event_roles", []),
            "v3_instrument_roster_count": len(roster),
            "v3_instrument_roster": roster,
            "v3_structured_sections_present": [
                field for field in required_structured if packet.get(field) is not None
            ],
        })

    v3_downstream_guards = {
        "blueprint_embeds_full_v3_packet": "'genre_contract_v3_execution_packet': copy.deepcopy(v3_execution_packet)" in communication_source,
        "blueprint_validates_embedded_v3_packet": "GENRE_COMMUNICATION_BLUEPRINT_V3_PACKET_MISSING" in communication_source,
        "engine_revalidates_v3_packet_at_blueprint_boundary": "v3_execution_packet=v3_contract_packet" in engine_source,
    }

    remaining_gaps = {
        "adapter_v3_profile_source_patch_present": adapter_v3_source_patch,
        "adapter_constructor_defaults_to_v3": (
            "def __init__(self, profile_registry_path=None, history_path=None)" in adapter_source
            and "self.profile_source='GENRE_CONTRACT_V3_ALL_55'" in adapter_source
        ),
        "adapter_constructor_legacy_default_removed": "profile_registry_path=PROFILE_PATH" not in adapter_source,
        "adapter_v3_roster_patch_present": adapter_v3_roster_patch,
        "static_palette_table_still_present_as_fallback": bool(palettes),
        "static_family_baseline_table_still_present": bool(bases),
        "fallback_path_still_uses_static_palette": "PALETTES.get(tmpl" in adapter_source,
        "classical_special_case_present": "if name == 'Classical':" in adapter_source,
        "legacy_classical_fixed_plan_code_still_present": "CLASSICAL_EXECUTABLE_PLAN_1" in classical_source,
        "classical_v3_structural_compiler_bound": "from classical_v3_structural_compiler import compile_plan as compile_v3_structure" in classical_source,
        "classical_abstract_note_realizer_bound": "from classical_v3_note_realizer import realize as realize_v3_notes" in classical_source,
        "classical_v3_orchestration_binder_bound": "from classical_v3_orchestration_binder import bind as bind_v3_orchestration" in classical_source,
        "classical_v3_resource_mapper_bound": "from classical_v3_resource_mapper import map_resources as map_v3_resources" in classical_source,
        "classical_symbolic_runtime_diagnostic_bound": "'execution_template':'classical_v3_symbolic_orchestration'" in classical_source and "'v3_symbolic_diagnostic_only':True" in classical_source,
        "classical_legacy_execution_explicitly_false": "'legacy_classical_generator_executed':False" in classical_source,
        "generic_blueprint_rejects_classical": "CLASSICAL_USES_EXISTING_SPECIALIZED_PATH" in communication_source,
        "performance_realizer_bypasses_classical": "CLASSICAL_SPECIALIZED_PATH_UNCHANGED" in performance_source,
        "instrument_resolver_only_resolves_event_ids": "original = event['instrument_id']" in instrument_source,
    }

    summary = {
        "status": "PASS",
        "diagnostic_only": True,
        "reasoning_engine_in_test_path": False,
        "note_generation_executed": False,
        "audio_generation_executed": False,
        "genre_contract_v3_count": len(contracts),
        "selector_v3_pass_count": selection_pass,
        "execution_packet_v3_pass_count": packet_pass,
        "structured_section_instances_present": structured_section_instances,
        "legacy_static_palette_template_count": len(palettes),
        "legacy_family_baseline_template_count": len(bases),
        "remaining_execution_authority_counts": {
            "GENRE_CONTRACT_V3_EXPLICIT_ROSTER": v3_explicit_roster,
            "V3_GOVERNED_SOURCE_PATTERN_ROLES": v3_source_pattern_roles,
            "LEGACY_FAMILY_TEMPLATE_AND_STATIC_PALETTE_FALLBACK": legacy_fallback,
            "CONTROLLED_COMPONENT_INPUT": controlled_component,
            "V3_CLASSICAL_SYMBOLIC_ORCHESTRATION_RUNTIME_DIAGNOSTIC": classical_specialized,
        },
        "v3_downstream_guards": v3_downstream_guards,
        "confirmed_remaining_gaps": remaining_gaps,
        "interpretation": (
            "All 55 V3 contracts survive selection and execution-packet creation. "
            "Seven non-Classical automatic genres use explicit V3 formation authority "
            "and the remaining forty automatic genres use V3-governed source-pattern "
            "role authority. No automatic genre currently requires the legacy static "
            "palette as execution authority. Classical uses its validated V3 "
            "structure, abstract-note, canonical-orchestration and resource-mapping "
            "path and stops at symbolic runtime instrument resolution before audio."
        ),
        "genres": results,
    }

    if not all(v3_downstream_guards.values()):
        raise RuntimeError("V3_DOWNSTREAM_BLUEPRINT_GUARD_MISSING")
    if selection_pass != 55 or packet_pass != 55:
        raise RuntimeError("ALL_55_V3_PROPAGATION_NOT_PROVEN")
    if v3_explicit_roster != 7:
        raise RuntimeError(f"EXPECTED_7_V3_EXPLICIT_ROSTER_GENRES__GOT_{v3_explicit_roster}")
    if v3_source_pattern_roles != 40:
        raise RuntimeError(f"EXPECTED_40_V3_SOURCE_PATTERN_ROLE_GENRES__GOT_{v3_source_pattern_roles}")
    if legacy_fallback != 0:
        raise RuntimeError(f"EXPECTED_ZERO_AUTOMATIC_LEGACY_FALLBACKS__GOT_{legacy_fallback}")
    if controlled_component != 7 or classical_specialized != 1:
        raise RuntimeError("EXPECTED_CONTROLLED_OR_CLASSICAL_COUNTS_NOT_MET")
    positive_invariants = {
        "adapter_v3_profile_source_patch_present": remaining_gaps["adapter_v3_profile_source_patch_present"],
        "adapter_constructor_defaults_to_v3": remaining_gaps["adapter_constructor_defaults_to_v3"],
        "adapter_constructor_legacy_default_removed": remaining_gaps["adapter_constructor_legacy_default_removed"],
        "adapter_v3_roster_patch_present": remaining_gaps["adapter_v3_roster_patch_present"],
        "source_pattern_authority_bound": (
            "V3_GOVERNED_SOURCE_PATTERN_ROLES" in adapter_source
            and "genre_v3_symbolic_pattern_executor" in adapter_source
            and "legacy_note_generator_used':False" in adapter_source
        ),
        "classical_v3_structural_compiler_bound": remaining_gaps["classical_v3_structural_compiler_bound"],
        "classical_abstract_note_realizer_bound": remaining_gaps["classical_abstract_note_realizer_bound"],
        "classical_v3_orchestration_binder_bound": remaining_gaps["classical_v3_orchestration_binder_bound"],
        "classical_v3_resource_mapper_bound": remaining_gaps["classical_v3_resource_mapper_bound"],
        "classical_symbolic_runtime_diagnostic_bound": remaining_gaps["classical_symbolic_runtime_diagnostic_bound"],
        "classical_legacy_execution_explicitly_false": remaining_gaps["classical_legacy_execution_explicitly_false"],
        "engine_symbolic_resolution_stop_present": "V3_SYMBOLIC_INSTRUMENT_RESOLUTION_PASS" in engine_source,
        "instrument_resolver_only_resolves_event_ids": remaining_gaps["instrument_resolver_only_resolves_event_ids"],
    }
    summary["positive_invariants"] = positive_invariants
    if not all(positive_invariants.values()):
        raise RuntimeError(
            "V3_EXECUTION_POSITIVE_INVARIANT_MISSING::"+
            json.dumps({k:v for k,v in positive_invariants.items() if not v},sort_keys=True)
        )

    out = ROOT / "genre_contract_v3_research" / "V3_EXECUTION_WIRING_AUDIT.json"
    out.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
