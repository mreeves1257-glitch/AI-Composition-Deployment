"""Audit the Rock Core V3 40-bar structural form plan."""
from __future__ import annotations

from pathlib import Path
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
FORWARD=ROOT/"current_master_forward"
if str(FORWARD) not in sys.path:
    sys.path.insert(0,str(FORWARD))

from rock_v3_core_form_plan import build


def main():
    plan=build()
    if plan.get("status")!="PASS":
        raise RuntimeError("ROCK_CORE_FORM_PLAN_NOT_PASS")
    if plan.get("profile_id")!="ROCK_CORE_V2":
        raise RuntimeError("ROCK_CORE_FORM_PROFILE_DRIFT")
    if plan.get("resolved_variant") is not None:
        raise RuntimeError("ROCK_CORE_FORM_SILENTLY_CLAIMED_VARIANT")
    if plan.get("family_baseline_must_not_claim_subgenre") is not True:
        raise RuntimeError("ROCK_CORE_FORM_SUBGENRE_GUARD_MISSING")
    if plan.get("bar_count")!=40:
        raise RuntimeError("ROCK_CORE_FORM_BAR_COUNT_WRONG")
    if plan.get("section_lengths")!=[4,8,8,8,8,4]:
        raise RuntimeError("ROCK_CORE_FORM_SECTION_LENGTHS_WRONG")
    if plan.get("note_events_generated") is not False:
        raise RuntimeError("ROCK_CORE_FORM_PREMATURE_NOTE_GENERATION")
    if plan.get("audio_generated") is not False or plan.get("audio_authority") is not False:
        raise RuntimeError("ROCK_CORE_FORM_AUDIO_ESCALATION")
    if plan.get("finished_composition_authority") is not False:
        raise RuntimeError("ROCK_CORE_FORM_PREMATURE_FINISHED_AUTHORITY")
    if plan.get("literal_source_cell_reuse_allowed_for_final_music") is not False:
        raise RuntimeError("ROCK_CORE_FORM_LITERAL_LOOP_PROMOTION_ALLOWED")
    for key in (
        "development_transform_required_before_event_expansion",
        "harmony_development_required_before_listening",
        "foreground_development_required_before_listening",
        "transition_realization_required_before_listening",
    ):
        if plan.get(key) is not True:
            raise RuntimeError("ROCK_CORE_FORM_REQUIRED_GATE_MISSING::"+key)

    bars=plan["bars"]
    if len(bars)!=40 or [x["bar"] for x in bars]!=list(range(40)):
        raise RuntimeError("ROCK_CORE_FORM_BAR_SEQUENCE_INVALID")

    by_section={}
    for row in bars:
        by_section.setdefault(row["section_id"],[]).append(row)

    expected_order=["INTRO_1","VERSE_1","CHORUS_1","VERSE_2","CHORUS_2","OUTRO_1"]
    if list(by_section)!=expected_order:
        raise RuntimeError("ROCK_CORE_FORM_SECTION_ORDER_INVALID")

    # Every intro/verse/chorus block ends with a structural transition cell.
    for section_id in ("INTRO_1","VERSE_1","CHORUS_1","VERSE_2","CHORUS_2"):
        rows=by_section[section_id]
        if rows[-1]["source_cell"]!="FILL":
            raise RuntimeError("ROCK_CORE_FORM_BOUNDARY_FILL_MISSING::"+section_id)
        if rows[-1]["boundary_fill"] is not True:
            raise RuntimeError("ROCK_CORE_FORM_BOUNDARY_FILL_FLAG_MISSING::"+section_id)

    if [x["source_cell"] for x in by_section["OUTRO_1"][-2:]]!=["ENDING","ENDING"]:
        raise RuntimeError("ROCK_CORE_FORM_ENDING_CELLS_MISSING")

    owners={x["foreground_owner"] for x in bars}
    if owners!={"LEAD_GUITAR","HARMONY_RIFF"}:
        raise RuntimeError("ROCK_CORE_FORM_FOREGROUND_HANDOFF_LOST")

    lead_bars=sum(x["foreground_owner"]=="LEAD_GUITAR" for x in bars)
    riff_bars=sum(x["foreground_owner"]=="HARMONY_RIFF" for x in bars)
    if lead_bars==0 or riff_bars==0:
        raise RuntimeError("ROCK_CORE_FORM_FOREGROUND_NOT_ALTERNATING")

    if not all(x["development_transform_required"] is True for x in bars):
        raise RuntimeError("ROCK_CORE_FORM_DEVELOPMENT_FLAG_NOT_PER_BAR")

    summary={
        "status":"PASS",
        "diagnostic_only":True,
        "genre":"ROCK",
        "profile_id":"ROCK_CORE_V2",
        "resolved_variant":None,
        "family_baseline_only":True,
        "bar_count":40,
        "section_lengths":plan["section_lengths"],
        "section_order":expected_order,
        "lead_foreground_bars":lead_bars,
        "riff_foreground_bars":riff_bars,
        "boundary_fill_sections":[
            x for x in expected_order if x!="OUTRO_1"
        ],
        "literal_cell_reuse_final_music_allowed":False,
        "note_events_generated":False,
        "audio_generated":False,
        "finished_composition_authority":False,
        "result":(
            "Rock Core now has a 40-bar structural verse/chorus form candidate "
            "built from the existing source-cell vocabulary and 4/8-bar family "
            "phrase rules. It remains a form plan only: repeated cells must be "
            "musically developed before event expansion or listening."
        ),
        "next_gate":"ROCK_CORE_DEVELOPMENT_PLAN_THEN_EVENT_EXPANSION",
        "form_plan_sha256":plan["form_plan_sha256"],
    }
    out=ROOT/"genre_contract_v3_research"/"ROCK_V3_CORE_FORM_PLAN_AUDIT.json"
    out.write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps(summary,indent=2))


if __name__=="__main__":
    main()
