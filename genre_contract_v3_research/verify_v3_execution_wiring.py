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
            authority = "SPECIALIZED_CLASSICAL_COMPOSITION_STATIC_PLAN_AND_ROSTER"
            classical_specialized += 1
        elif policy != "AUTOMATIC_BASELINE_ALLOWED":
            authority = "CONTROLLED_COMPONENT_INPUT"
            controlled_component += 1
        elif v3_instrument.get("status") == "PASS":
            authority = "GENRE_CONTRACT_V3_EXPLICIT_ROSTER"
            v3_explicit_roster += 1
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
        "adapter_v3_roster_patch_present": adapter_v3_roster_patch,
        "static_palette_table_still_present_as_fallback": bool(palettes),
        "static_family_baseline_table_still_present": bool(bases),
        "fallback_path_still_uses_static_palette": "PALETTES.get(tmpl" in adapter_source,
        "classical_special_case_present": "if name == 'Classical':" in adapter_source,
        "classical_fixed_plan_code_present": "CLASSICAL_EXECUTABLE_PLAN_1" in classical_source,
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
            "LEGACY_FAMILY_TEMPLATE_AND_STATIC_PALETTE_FALLBACK": legacy_fallback,
            "CONTROLLED_COMPONENT_INPUT": controlled_component,
            "SPECIALIZED_CLASSICAL_COMPOSITION_STATIC_PLAN_AND_ROSTER": classical_specialized,
        },
        "v3_downstream_guards": v3_downstream_guards,
        "confirmed_remaining_gaps": remaining_gaps,
        "interpretation": (
            "All 55 V3 contracts survive selection and execution-packet creation. "
            "Seven non-Classical automatic genres with explicit V3 formations now have "
            "V3 instrument-role authority. Forty automatic genres still require a "
            "clearly labeled legacy palette fallback because their V3 rosters are not "
            "yet explicit. Classical remains isolated in its specialized fixed plan and "
            "must next receive a resolved V3 variant/composition package."
        ),
        "genres": results,
    }

    if not all(v3_downstream_guards.values()):
        raise RuntimeError("V3_DOWNSTREAM_BLUEPRINT_GUARD_MISSING")
    if selection_pass != 55 or packet_pass != 55:
        raise RuntimeError("ALL_55_V3_PROPAGATION_NOT_PROVEN")
    if v3_explicit_roster != 7:
        raise RuntimeError(f"EXPECTED_7_V3_EXPLICIT_ROSTER_GENRES__GOT_{v3_explicit_roster}")
    if legacy_fallback != 40:
        raise RuntimeError(f"EXPECTED_40_LEGACY_FALLBACK_GENRES__GOT_{legacy_fallback}")
    if controlled_component != 7 or classical_specialized != 1:
        raise RuntimeError("EXPECTED_CONTROLLED_OR_CLASSICAL_COUNTS_NOT_MET")
    required_gap_truths = (
        "adapter_v3_profile_source_patch_present",
        "adapter_v3_roster_patch_present",
        "static_palette_table_still_present_as_fallback",
        "static_family_baseline_table_still_present",
        "fallback_path_still_uses_static_palette",
        "classical_special_case_present",
        "classical_fixed_plan_code_present",
        "generic_blueprint_rejects_classical",
        "performance_realizer_bypasses_classical",
        "instrument_resolver_only_resolves_event_ids",
    )
    if not all(remaining_gaps[key] for key in required_gap_truths):
        raise RuntimeError("EXPECTED_WIRING_GAP_NOT_DETECTED")

    out = ROOT / "genre_contract_v3_research" / "V3_EXECUTION_WIRING_AUDIT.json"
    out.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
