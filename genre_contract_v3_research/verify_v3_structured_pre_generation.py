"""Verify structured Genre Contract V3 survives pre-generation compilation.

No note generation, no audio generation, no reasoning engine.
"""
from __future__ import annotations

from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
FORWARD = ROOT / "current_master_forward"
if str(FORWARD) not in sys.path:
    sys.path.insert(0, str(FORWARD))

from genre_contract_v3_execution_bridge import load_master, snapshot_for
from genre_pre_generation_compiler import compile_generation_plan

SUPPORTED_METERS = ("4/4", "3/4", "2/4", "6/8")
SUPPORTED_FORMS = ("verse_chorus", "aba", "through_composed")


def _fallback_baseline(snapshot):
    meters = list(snapshot.get("meter_options") or [])
    meter = next((m for m in meters if m in SUPPORTED_METERS), "4/4")
    tempos = list(snapshot.get("tempo_bpm_range") or [100, 100])
    lo, hi = int(tempos[0]), int(tempos[-1])
    bpm = int(round((lo + hi) / 2))
    forms = list(snapshot.get("form_tendencies") or [])
    form = next((f for f in forms if f in SUPPORTED_FORMS), "through_composed")
    return ("C", "major", meter, bpm, form, "roots_fifths")


def main():
    master = load_master()
    results = []
    passes = 0
    hashes = set()

    for name in master["contracts"]:
        snapshot = snapshot_for(name)
        plan = compile_generation_plan(snapshot, _fallback_baseline(snapshot), creation_seed=0)
        structured = plan.get("structured_v3_contract") or {}
        if plan.get("source") != "GENRE_CONTRACT_V3_STRUCTURED_PRE_GENERATION":
            raise RuntimeError(f"PREGEN_SOURCE_NOT_V3::{name}")
        if structured.get("status") != "PASS":
            raise RuntimeError(f"STRUCTURED_V3_NOT_PASS::{name}")
        if structured.get("genre_name") != name:
            raise RuntimeError(f"STRUCTURED_V3_NAME_MISMATCH::{name}")
        if structured.get("profile_id") != snapshot.get("profile_id"):
            raise RuntimeError(f"STRUCTURED_V3_PROFILE_MISMATCH::{name}")
        sections = structured.get("sections") or {}
        for required in ("musical_grammar", "ensemble", "performance", "safeguards", "variant_resolution"):
            if required not in sections or sections[required] is None:
                raise RuntimeError(f"STRUCTURED_V3_SECTION_MISSING::{name}::{required}")
        if plan.get("semantic_tag_role") != "LEGACY_EXECUTION_FALLBACK":
            raise RuntimeError(f"LEGACY_TAG_ROLE_NOT_EXPLICIT::{name}")
        digest = plan.get("structured_v3_contract_sha256")
        if not digest:
            raise RuntimeError(f"STRUCTURED_V3_HASH_MISSING::{name}")
        hashes.add(digest)
        passes += 1
        results.append({
            "genre": name,
            "profile_id": snapshot.get("profile_id"),
            "pre_generation_source": plan.get("source"),
            "structured_sha256": digest,
            "structured_sections": sorted(sections),
            "legacy_semantic_tag_role": plan.get("semantic_tag_role"),
            "legacy_semantic_tags": plan.get("semantic_tags"),
            "tempo_bpm": plan.get("tempo_bpm"),
            "meter": plan.get("meter"),
            "form": plan.get("form"),
            "note_generation_executed": False,
        })

    if passes != 55:
        raise RuntimeError(f"EXPECTED_55_STRUCTURED_PREGEN_PASSES__GOT_{passes}")
    if len(hashes) != 55:
        raise RuntimeError("STRUCTURED_V3_HASH_COLLISION_OR_DUPLICATION")

    summary = {
        "status": "PASS",
        "diagnostic_only": True,
        "reasoning_engine_in_test_path": False,
        "note_generation_executed": False,
        "audio_generation_executed": False,
        "genre_count": 55,
        "structured_pre_generation_pass_count": passes,
        "unique_structured_contract_hash_count": len(hashes),
        "result": (
            "All 55 Genre Contract V3 payloads survive into pre-generation as structured "
            "authority. Legacy semantic tags remain present only as explicitly labeled "
            "execution fallback behavior."
        ),
        "next_gap": (
            "Teach event generation to execute structured V3 grammar instead of relying "
            "primarily on legacy family-template branches and semantic tags."
        ),
        "genres": results,
    }

    out = ROOT / "genre_contract_v3_research" / "V3_STRUCTURED_PREGEN_AUDIT.json"
    out.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
