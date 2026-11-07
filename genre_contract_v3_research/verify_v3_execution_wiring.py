"""Audit Genre Contract V3 source propagation without generating notes or audio.

Diagnostic only. The experimental reasoning engine is intentionally absent from
this branch. This audit proves which genre source reaches selection/execution
and exposes remaining legacy instrument-authority paths.
"""
from __future__ import annotations

from pathlib import Path
import importlib.util
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
FORWARD = ROOT / "current_master_forward"
if str(FORWARD) not in sys.path:
    sys.path.insert(0, str(FORWARD))

from genre_contract_v3_execution_bridge import (
    load_master,
    snapshot_for,
    execution_packet,
)
from genre_selector import GenreSelector

V3_PATH = ROOT / "genre_contract_v3_research" / "GENRE_CONTRACT_V3_ALL_55.json"
MENU_PATH = None
ADAPTER_PATH = FORWARD / "AI_Comp_Genre_Execution_Adapter_002_WORKING_2026-10-02_184019_CDT.py"


def _load_adapter():
    spec = importlib.util.spec_from_file_location("v3_diagnostic_adapter", ADAPTER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("ADAPTER_LOAD_FAILED")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    master = load_master()
    contracts = master["contracts"]
    if len(contracts) != 55:
        raise RuntimeError("V3_CONTRACT_COUNT_NOT_55")

    selector = GenreSelector(V3_PATH, MENU_PATH)
    if selector.registry_source != "GENRE_CONTRACT_V3_ALL_55":
        raise RuntimeError("SELECTOR_NOT_V3")

    adapter = _load_adapter()
    if set(adapter.profiles) != set(contracts):
        raise RuntimeError("ADAPTER_PROFILE_NAME_SET_MISMATCH")

    results = []
    selection_pass = 0
    execution_packet_pass = 0
    adapter_profile_pass = 0
    legacy_static_palette = 0
    controlled_component = 0
    classical_specialized = 0
    structured_sections_present = 0

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
        execution_packet_pass += 1
        structured_sections_present += sum(packet.get(field) is not None for field in required_structured)

        adapter_profile = adapter.profiles[name]
        source = adapter_profile.get("_genre_contract_v3_source") or {}
        if source.get("genre_name") != name:
            raise RuntimeError(f"ADAPTER_V3_SOURCE_FAIL::{name}")
        if adapter_profile.get("profile_id") != snapshot.get("profile_id"):
            raise RuntimeError(f"ADAPTER_PROFILE_FAIL::{name}")
        adapter_profile_pass += 1

        policy = snapshot.get("resolution_policy")
        if name == "Classical":
            authority = "SPECIALIZED_CLASSICAL_COMPOSITION_STATIC_ROSTER"
            template = "classical"
            parts = list(getattr(adapter, "PALETTES", {}).get("classical", []))
            classical_specialized += 1
        elif policy != "AUTOMATIC_BASELINE_ALLOWED":
            authority = "CONTROLLED_COMPONENT_INPUT"
            template = adapter.family_template(name)
            parts = []
            controlled_component += 1
        else:
            template = adapter.family_template(name)
            parts = adapter.resolve_genre_parts(name, template, adapter_profile)
            authority = "LEGACY_STATIC_PALETTE"
            legacy_static_palette += 1

        ensemble = contract.get("ensemble") or {}
        roster = ensemble.get("instrument_roster") or []
        results.append({
            "genre": name,
            "profile_id": snapshot.get("profile_id"),
            "resolution_policy": policy,
            "selector_source": selection.get("registry_source"),
            "execution_packet_source": packet.get("source"),
            "adapter_profile_source": source.get("master_path"),
            "instrument_authority": authority,
            "legacy_template": template,
            "legacy_palette_parts": parts,
            "v3_instrument_roster_count": len(roster),
            "v3_instrument_roster": roster,
            "v3_structured_sections_present": [
                field for field in required_structured if packet.get(field) is not None
            ],
        })

    adapter_source = ADAPTER_PATH.read_text()
    classical_source = (FORWARD / "classical_composition.py").read_text()
    communication_source = (FORWARD / "genre_communication_blueprint.py").read_text()

    summary = {
        "status": "PASS",
        "diagnostic_only": True,
        "reasoning_engine_in_test_path": False,
        "genre_contract_v3_count": len(contracts),
        "selector_v3_pass_count": selection_pass,
        "execution_packet_v3_pass_count": execution_packet_pass,
        "adapter_v3_profile_pass_count": adapter_profile_pass,
        "structured_section_instances_present": structured_sections_present,
        "instrument_authority_counts": {
            "LEGACY_STATIC_PALETTE": legacy_static_palette,
            "CONTROLLED_COMPONENT_INPUT": controlled_component,
            "SPECIALIZED_CLASSICAL_COMPOSITION_STATIC_ROSTER": classical_specialized,
        },
        "confirmed_remaining_gaps": {
            "static_palette_table_present": "PALETTES={" in adapter_source,
            "resolve_genre_parts_uses_static_palette": "PALETTES.get(tmpl" in adapter_source,
            "classical_special_case_present": "if name == 'Classical':" in adapter_source,
            "classical_fixed_plan_code_present": "CLASSICAL_EXECUTABLE_PLAN_1" in classical_source,
            "generic_blueprint_rejects_classical": "CLASSICAL_USES_EXISTING_SPECIALIZED_PATH" in communication_source,
        },
        "interpretation": (
            "V3 source propagation now passes on this diagnostic branch, but reading V3 "
            "does not yet mean executing V3. Automatic non-Classical instrument choice "
            "still comes from legacy static palettes, while Classical still uses its "
            "specialized fixed composition/roster path."
        ),
        "genres": results,
    }

    if selection_pass != 55 or execution_packet_pass != 55 or adapter_profile_pass != 55:
        raise RuntimeError("ALL_55_V3_PROPAGATION_NOT_PROVEN")
    if legacy_static_palette == 0:
        raise RuntimeError("EXPECTED_LEGACY_PALETTE_GAP_NOT_DETECTED")
    if not all(summary["confirmed_remaining_gaps"].values()):
        raise RuntimeError("EXPECTED_WIRING_GAP_NOT_DETECTED")

    out = ROOT / "genre_contract_v3_research" / "V3_EXECUTION_WIRING_AUDIT.json"
    out.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
