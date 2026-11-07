"""Canonical read-only access to Genre Contract V3 for execution diagnostics.

This module does not generate music and does not invoke the experimental
reasoning engine. It exists to make the V3 master the single inspectable source
for genre identity during the no-reasoning diagnostic.

The legacy October registry remains in the repository as historical/fallback
evidence, but callers using this bridge can prove exactly which V3 contract was
loaded and can carry the complete contract downstream.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import hashlib
import json
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MASTER_PATH = ROOT / "genre_contract_v3_research" / "GENRE_CONTRACT_V3_ALL_55.json"


class GenreContractV3Error(RuntimeError):
    pass


def _sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()


def load_master() -> dict[str, Any]:
    data = json.loads(MASTER_PATH.read_text())
    contracts = data.get("contracts")
    if not isinstance(contracts, dict) or len(contracts) != 55:
        raise GenreContractV3Error("GENRE_CONTRACT_V3_MASTER_NOT_55")
    return data


def contract_for(genre_name: str) -> dict[str, Any]:
    data = load_master()
    try:
        contract = data["contracts"][genre_name]
    except KeyError as exc:
        raise GenreContractV3Error(f"GENRE_CONTRACT_V3_UNKNOWN::{genre_name}") from exc
    if contract.get("genre_name") != genre_name:
        raise GenreContractV3Error("GENRE_CONTRACT_V3_NAME_MISMATCH")
    return deepcopy(contract)


def snapshot_for(genre_name: str) -> dict[str, Any]:
    contract = contract_for(genre_name)
    snapshot = deepcopy(contract.get("current_profile_snapshot") or {})
    if not snapshot.get("profile_id"):
        raise GenreContractV3Error("GENRE_CONTRACT_V3_PROFILE_ID_MISSING")
    snapshot["_genre_contract_v3_source"] = {
        "genre_name": genre_name,
        "contract_schema": contract.get("contract_schema"),
        "source_profile_id": contract.get("source_profile_id"),
        "research_status": contract.get("research_status"),
        "approved_for_runtime": contract.get("approved_for_runtime"),
        "contract_sha256": _sha(contract),
        "master_path": str(MASTER_PATH.relative_to(ROOT)),
    }
    # Carry the complete V3 intelligence as structured data. Legacy fields remain
    # present for older modules, but no V3 section is silently discarded here.
    snapshot["_genre_contract_v3"] = {
        key: deepcopy(contract.get(key))
        for key in (
            "comparison",
            "musical_grammar",
            "ensemble",
            "performance",
            "production",
            "evidence",
            "validation",
            "safeguards",
            "variant_resolution",
            "quantitative_evidence_status",
        )
        if key in contract
    }
    return snapshot


def all_snapshots() -> dict[str, dict[str, Any]]:
    data = load_master()
    return {name: snapshot_for(name) for name in data["contracts"]}


def execution_packet(genre_name: str) -> dict[str, Any]:
    contract = contract_for(genre_name)
    snapshot = snapshot_for(genre_name)
    packet = {
        "source": "GENRE_CONTRACT_V3_ALL_55",
        "genre_name": genre_name,
        "profile_id": snapshot["profile_id"],
        "snapshot": snapshot,
        "musical_grammar": deepcopy(contract.get("musical_grammar")),
        "ensemble": deepcopy(contract.get("ensemble")),
        "performance": deepcopy(contract.get("performance")),
        "production": deepcopy(contract.get("production")),
        "safeguards": deepcopy(contract.get("safeguards")),
        "variant_resolution": deepcopy(contract.get("variant_resolution")),
        "approved_for_runtime": contract.get("approved_for_runtime"),
        "research_status": contract.get("research_status"),
    }
    packet["packet_sha256"] = _sha(packet)
    return packet
