"""Audit evidence-backed Rock V3 variant composition packages."""
from __future__ import annotations

from pathlib import Path
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
FORWARD=ROOT/"current_master_forward"
if str(FORWARD) not in sys.path:
    sys.path.insert(0,str(FORWARD))

from rock_v3_variant_package import audit_all, compile_package


def main():
    result=audit_all()
    if result.get("variant_count")!=9:
        raise RuntimeError("ROCK_VARIANT_COUNT_NOT_9")
    if result.get("structural_package_count")!=7:
        raise RuntimeError(
            "ROCK_STRUCTURAL_VARIANT_PACKAGE_COUNT_NOT_7::"+
            str(result.get("structural_package_count"))
        )
    if result.get("second_level_resolution_required_count")!=2:
        raise RuntimeError(
            "ROCK_UMBRELLA_VARIANT_COUNT_NOT_2::"+
            str(result.get("second_level_resolution_required_count"))
        )

    expected_structural={
        "Hard rock","Soft rock","Southern rock","Progressive rock",
        "Punk-related rock","Blues rock","Singer-songwriter rock",
    }
    expected_umbrella={"Classic rock","Alternative rock"}
    if set(result.get("structural_variants") or [])!=expected_structural:
        raise RuntimeError("ROCK_STRUCTURAL_VARIANT_SET_CHANGED")
    if set(result.get("umbrella_variants") or [])!=expected_umbrella:
        raise RuntimeError("ROCK_UMBRELLA_VARIANT_SET_CHANGED")

    for name,item in result["results"].items():
        for key in (
            "audio_authority","live_runtime_authority",
            "finished_composition_authority"
        ):
            if item.get(key) is not False:
                raise RuntimeError(f"ROCK_VARIANT_AUTHORITY_ESCALATION::{name}::{key}")

        if name in expected_structural:
            if item.get("status")!="PASS_STRUCTURAL_VARIANT_PACKAGE":
                raise RuntimeError("ROCK_STRUCTURAL_VARIANT_NOT_PASS::"+name)
            if item.get("single_composition_recipe_allowed") is not True:
                raise RuntimeError("ROCK_STRUCTURAL_VARIANT_RECIPE_NOT_ALLOWED::"+name)
            if item.get("form_execution_ready") is not False:
                raise RuntimeError("ROCK_FORM_EXECUTION_PREMATURELY_READY::"+name)
            if item.get("note_execution_ready") is not False:
                raise RuntimeError("ROCK_NOTE_EXECUTION_PREMATURELY_READY::"+name)
            if item.get("resource_execution_ready") is not False:
                raise RuntimeError("ROCK_RESOURCE_EXECUTION_PREMATURELY_READY::"+name)
            for field in (
                "form_strategy","groove_strategy","harmony_strategy",
                "texture_strategy","foreground_strategy","development_strategy"
            ):
                if not item.get(field):
                    raise RuntimeError(f"ROCK_VARIANT_STRATEGY_MISSING::{name}::{field}")
        else:
            if item.get("status")!="BLOCKED_SECOND_LEVEL_VARIANT_RESOLUTION_REQUIRED":
                raise RuntimeError("ROCK_UMBRELLA_VARIANT_NOT_BLOCKED::"+name)
            if item.get("single_composition_recipe_allowed") is not False:
                raise RuntimeError("ROCK_UMBRELLA_SINGLE_RECIPE_ALLOWED::"+name)
            if not item.get("required_child_resolution"):
                raise RuntimeError("ROCK_UMBRELLA_CHILD_RESOLUTION_MISSING::"+name)

    summary={
        "status":"PASS",
        "diagnostic_only":True,
        "genre":"ROCK",
        "variant_count":9,
        "structural_package_count":7,
        "umbrella_block_count":2,
        "structural_variants":sorted(expected_structural),
        "umbrella_variants":sorted(expected_umbrella),
        "audio_authority":False,
        "live_runtime_promoted":False,
        "finished_composition_authority":False,
        "finding":(
            "Rock V3 no longer treats all candidate labels as equally executable. "
            "Seven variants have typed structural composition packages; Classic rock "
            "and Alternative rock are blocked as umbrella labels pending child-style resolution."
        ),
        "next_gate":"BUILD_VARIANT_FORM_PLANS_WITHOUT_AUDIO",
    }
    out=ROOT/"genre_contract_v3_research"/"ROCK_V3_VARIANT_PACKAGE_AUDIT.json"
    out.write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps(summary,indent=2))


if __name__=="__main__":
    main()
