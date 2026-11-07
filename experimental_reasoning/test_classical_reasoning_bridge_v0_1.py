"""Self-tests for the Classical reasoning bridge v0.1."""
from __future__ import annotations

import json
from pathlib import Path

from classical_reasoning_bridge_v0_1 import build_classical_reasoning_report
from reasoning_engine_v0_1 import validate

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "current_master_forward" / "genre_registry_WORKING_GENRE_COMPLETE_2026-10-02_182810_CDT.json"


def _profile():
    data = json.loads(REGISTRY.read_text())
    return data["detailed_or_new_profiles"]["Classical"]


def test_classical_bridge_preserves_native_form_and_does_not_invent_kick():
    report = build_classical_reasoning_report(profile=_profile(), creation_seed=0, mode="quick")
    assert report["status"] == "PASS"
    assert report["source_classical_plan_preserved"] is True
    assert report["live_composer_modified"] is False
    assert report["kick_present"] is False
    assert report["section_count"] == 4
    assert [x["classical_section"] for x in report["sections"]] == ["A", "B", "A_RETURN", "CODA"]
    assert [x["formal_function"] for x in report["sections"]] == ["statement", "contrast", "return", "coda"]


def test_classical_contrast_return_and_coda_have_distinct_reasoning():
    report = build_classical_reasoning_report(profile=_profile(), creation_seed=0, mode="quick")
    by_name = {x["classical_section"]: x["reasoning_packet"] for x in report["sections"]}
    for packet in by_name.values():
        validate(packet)

    a = by_name["A"]["decisions"]
    b = by_name["B"]["decisions"]
    ret = by_name["A_RETURN"]["decisions"]
    coda = by_name["CODA"]["decisions"]

    assert a["kick_character"]["status"] == "NOT_ACTIVE"
    assert a["low_end_interaction"]["status"] == "NOT_APPLICABLE"
    assert b["contrast"]["required"] is True
    assert b["section_function"] == "CONTRAST"
    assert ret["section_function"] == "RETURN"
    assert ret["musical_memory"]["status"] == "PASS"
    assert coda["section_function"] == "CODA"
    assert coda["transition"]["mode"] == "RESOLVE_OR_THIN"
    assert "RECEDING" in coda["spatial_choreography"]["target_scene"]["intimacy"]


def test_classical_keeps_full_orchestra_identity_available_to_reasoning():
    report = build_classical_reasoning_report(profile=_profile(), creation_seed=0, mode="quick")
    instruments = set(report["distinct_instruments"])
    assert report["orchestral_player_count"] >= 16
    assert {"violin", "viola", "cello", "double_bass", "concert_flute", "oboe", "clarinet_bb",
            "bassoon", "horn_f", "trumpet_c", "tenor_trombone", "bass_tuba", "timpani"} <= instruments


if __name__ == "__main__":
    tests = [
        test_classical_bridge_preserves_native_form_and_does_not_invent_kick,
        test_classical_contrast_return_and_coda_have_distinct_reasoning,
        test_classical_keeps_full_orchestra_identity_available_to_reasoning,
    ]
    for fn in tests:
        fn()
    print(f"PASS: {len(tests)} Classical reasoning-bridge v0.1 tests")
