"""Audit Rock V3 structural form planner."""
from __future__ import annotations

from pathlib import Path
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
FORWARD=ROOT/"current_master_forward"
if str(FORWARD) not in sys.path:
    sys.path.insert(0,str(FORWARD))

from rock_v3_form_planner import plan, available_forms


CHOICE_VARIANTS={
    "Hard rock","Soft rock","Southern rock",
    "Punk-related rock","Singer-songwriter rock",
}
UMBRELLA={"Classic rock","Alternative rock"}


def main():
    plans={}
    candidate_plan_count=0

    for name in CHOICE_VARIANTS:
        availability=available_forms(name)
        if availability["form_status"]!="FORM_CHOICE_REQUIRED":
            raise RuntimeError("ROCK_FORM_CHOICE_STATUS_WRONG::"+name)
        ids=availability.get("form_ids") or []
        if len(ids)<2:
            raise RuntimeError("ROCK_FORM_CANDIDATE_COUNT_TOO_SMALL::"+name)

        missing=plan(name)
        if missing.get("status")!="FORM_CHOICE_REQUIRED":
            raise RuntimeError("ROCK_FORM_SILENT_DEFAULT_OCCURRED::"+name)
        if missing.get("form_selected") is not False:
            raise RuntimeError("ROCK_FORM_MARKED_SELECTED_WITHOUT_CHOICE::"+name)

        rows=[]
        for form_id in ids:
            result=plan(name,form_id=form_id)
            if result.get("status")!="PASS_FORM_PLAN":
                raise RuntimeError("ROCK_FORM_PLAN_NOT_PASS::"+name+"::"+form_id)
            if result.get("form_selected") is not True:
                raise RuntimeError("ROCK_FORM_PLAN_NOT_SELECTED::"+name+"::"+form_id)
            if result.get("planned_bar_count",0)<=7:
                raise RuntimeError("ROCK_FORM_NOT_EXPANDED::"+name+"::"+form_id)
            if not result.get("planned_sections"):
                raise RuntimeError("ROCK_FORM_SECTIONS_EMPTY::"+name+"::"+form_id)
            if result.get("note_events_generated") is not False:
                raise RuntimeError("ROCK_FORM_GENERATED_NOTES::"+name+"::"+form_id)
            if result.get("note_execution_ready") is not False:
                raise RuntimeError("ROCK_FORM_NOTE_EXECUTION_PREMATURE::"+name+"::"+form_id)
            if result.get("prototype_bar_copy_as_finished_music_allowed") is not False:
                raise RuntimeError("ROCK_FORM_PROTOTYPE_COPY_ALLOWED::"+name+"::"+form_id)
            if result.get("new_material_requires_variant_transformation_rules") is not True:
                raise RuntimeError("ROCK_FORM_TRANSFORMATION_GUARD_MISSING::"+name+"::"+form_id)
            if result.get("audio_authority") is not False:
                raise RuntimeError("ROCK_FORM_AUDIO_ESCALATION::"+name+"::"+form_id)
            rows.append({
                "form_id":form_id,
                "bar_count":result["planned_bar_count"],
                "section_count":len(result["planned_sections"]),
                "new_material_required":result["new_material_required"],
                "form_plan_sha256":result["form_plan_sha256"],
            })
            candidate_plan_count+=1
        plans[name]=rows

    blues=plan("Blues rock")
    if blues.get("status")!="FORM_SUBMODE_REQUIRED":
        raise RuntimeError("BLUES_ROCK_FORM_SUBMODE_NOT_REQUIRED")
    if set(blues.get("required_form_submodes") or [])!={"BLUES_DERIVED_CYCLE","RIFF_SECTIONAL"}:
        raise RuntimeError("BLUES_ROCK_FORM_SUBMODE_SET_CHANGED")
    for mode in blues["required_form_submodes"]:
        selected=plan("Blues rock",form_submode=mode)
        if selected.get("status")!="FORM_SUBMODE_SELECTED__DETAILED_BLUEPRINT_REQUIRED":
            raise RuntimeError("BLUES_ROCK_FORM_SUBMODE_SELECTION_STATUS_WRONG::"+mode)
        if selected.get("note_events_generated") is not False:
            raise RuntimeError("BLUES_ROCK_SUBMODE_GENERATED_NOTES::"+mode)

    prog=plan("Progressive rock")
    if prog.get("status")!="CUSTOM_SECTION_AND_METER_PLAN_REQUIRED":
        raise RuntimeError("PROGRESSIVE_CUSTOM_PLAN_NOT_REQUIRED")
    custom=plan("Progressive rock",custom_sections=[
        {"name":"OPENING","bars":5,"meter":"7/8","role":"ASYMMETRIC_OPENING"},
        {"name":"THEME_A","bars":7,"meter":"4/4","role":"THEMATIC_STATEMENT"},
        {"name":"DEVELOPMENT","bars":6,"meter":"5/4","role":"DEVELOPMENT"},
        {"name":"RETURN","bars":7,"meter":"4/4","role":"THEMATIC_RETURN"},
    ])
    if custom.get("status")!="PASS_CUSTOM_FORM_PLAN":
        raise RuntimeError("PROGRESSIVE_CUSTOM_PLAN_NOT_PASS")
    if custom.get("planned_bar_count")!=25:
        raise RuntimeError("PROGRESSIVE_CUSTOM_PLAN_BAR_COUNT_WRONG")
    if custom.get("note_events_generated") is not False:
        raise RuntimeError("PROGRESSIVE_CUSTOM_PLAN_GENERATED_NOTES")

    for name in UMBRELLA:
        blocked=plan(name)
        if blocked.get("status")!="BLOCKED_SECOND_LEVEL_VARIANT_RESOLUTION_REQUIRED":
            raise RuntimeError("ROCK_UMBRELLA_FORM_NOT_BLOCKED::"+name)

    summary={
        "status":"PASS",
        "diagnostic_only":True,
        "genre":"ROCK",
        "choice_variant_count":len(CHOICE_VARIANTS),
        "candidate_form_plan_count":candidate_plan_count,
        "blues_rock_status":"FORM_SUBMODE_REQUIRED",
        "progressive_rock_status":"CUSTOM_SECTION_AND_METER_PLAN_REQUIRED",
        "umbrella_block_count":len(UMBRELLA),
        "note_events_generated":False,
        "audio_authority":False,
        "live_runtime_promoted":False,
        "finished_composition_authority":False,
        "plans":plans,
        "finding":(
            "Rock V3 now has an explicit no-default structural form layer. Five variants "
            "expose multiple candidate forms, Blues Rock requires a structural submode, "
            "Progressive Rock requires a custom section/meter plan, and Classic/Alternative "
            "remain blocked as umbrella labels."
        ),
        "next_gate":"COMPILE_VARIANT_SECTION_TRANSFORMATION_RULES_BEFORE_NOTE_EXPANSION",
    }
    out=ROOT/"genre_contract_v3_research"/"ROCK_V3_FORM_PLANNER_AUDIT.json"
    out.write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps(summary,indent=2))


if __name__=="__main__":
    main()
