"""Audit Genre V3 foreground authority without generating notes or audio."""
from __future__ import annotations

from pathlib import Path
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
FORWARD=ROOT/"current_master_forward"
if str(FORWARD) not in sys.path:
    sys.path.insert(0,str(FORWARD))

from genre_v3_foreground_authority import audit_all


def main():
    result=audit_all()
    rows=result["results"]

    if result["genre_count"]!=55:
        raise RuntimeError("FOREGROUND_AUTHORITY_NOT_55")
    if result["automatic_nonclassical_count"]!=47:
        raise RuntimeError(
            "EXPECTED_47_AUTOMATIC_NONCLASSICAL::"+
            str(result["automatic_nonclassical_count"])
        )
    if result["controlled_or_user_count"]!=7:
        raise RuntimeError(
            "EXPECTED_7_CONTROLLED_OR_USER::"+
            str(result["controlled_or_user_count"])
        )
    if result["automatic_foreground_note_execution_ready_count"]!=0:
        raise RuntimeError("FOREGROUND_EXECUTION_WAS_FABRICATED")
    if result["source_pattern_finished_foreground_count"]!=0:
        raise RuntimeError("SOURCE_PATTERN_WRONGLY_PROMOTED_TO_FOREGROUND")
    if result["classical_execution_status"]!="SEPARATE_CLASSICAL_V3_MELODY_PATH":
        raise RuntimeError("CLASSICAL_FOREGROUND_PATH_MISCLASSIFIED")

    for name,item in rows.items():
        for key in (
            "melody_model","phrase_model","development_model",
            "role_handoff_rules","foreground_window_rules"
        ):
            if not item.get(key):
                raise RuntimeError(f"FOREGROUND_RULE_MISSING::{name}::{key}")
        if item.get("source_pattern_explicit_foreground_role_count")!=0:
            raise RuntimeError("SOURCE_PATTERN_FOREGROUND_ROLE_COUNT_CHANGED::"+name)
        if item.get("source_pattern_can_supply_finished_foreground") is not False:
            raise RuntimeError("SOURCE_PATTERN_FOREGROUND_GUARD_MISSING::"+name)
        if item.get("audio_authority") is not False:
            raise RuntimeError("FOREGROUND_AUTHORITY_AUDIO_ESCALATION::"+name)
        if item.get("reasoning_engine_used") is not False:
            raise RuntimeError("REASONING_ENGINE_ENTERED_FOREGROUND_AUDIT::"+name)

    summary={
        "status":"PASS",
        "diagnostic_only":True,
        "reasoning_engine_used":False,
        "audio_generated":False,
        "genre_count":55,
        "automatic_nonclassical_count":47,
        "controlled_or_user_count":7,
        "classical_count":1,
        "structured_foreground_rules_present_count":55,
        "source_pattern_explicit_foreground_role_count":0,
        "automatic_machine_executable_foreground_count":0,
        "source_pattern_finished_composition_eligible_count":0,
        "finding":(
            "All 55 V3 contracts contain melody/phrase/development/foreground-handoff "
            "rules, but the recovered source-pattern layer contains zero explicit "
            "foreground roles. Non-Classical automatic genres therefore still require "
            "a separate foreground/melody executor before audio or finished-composition "
            "promotion."
        ),
        "classical_status":"SEPARATE_CLASSICAL_V3_MELODY_PATH",
        "promotion_block":"SOURCE_PATTERN_ACCOMPANIMENT_MAY_NOT_BE_RENDERED_AS_FINISHED_COMPOSITION",
        "next_gate":"COMPILE_GENRE_SPECIFIC_FOREGROUND_EXECUTION_WITHOUT_GENERIC_MELODY",
    }
    out=ROOT/"genre_contract_v3_research"/"V3_FOREGROUND_AUTHORITY_AUDIT.json"
    out.write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps(summary,indent=2))


if __name__=="__main__":
    main()
