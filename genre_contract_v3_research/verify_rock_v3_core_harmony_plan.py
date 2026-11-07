"""Audit the Rock Core V3 harmonic-development plan."""
from __future__ import annotations

from pathlib import Path
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
FORWARD=ROOT/"current_master_forward"
if str(FORWARD) not in sys.path:
    sys.path.insert(0,str(FORWARD))

from rock_v3_core_harmony_plan import build


def main():
    plan=build()
    if plan.get("status")!="PASS":
        raise RuntimeError("ROCK_HARMONY_PLAN_NOT_PASS")
    if plan.get("genre")!="ROCK" or plan.get("profile_id")!="ROCK_CORE_V2":
        raise RuntimeError("ROCK_HARMONY_IDENTITY_DRIFT")
    if plan.get("resolved_variant") is not None:
        raise RuntimeError("ROCK_HARMONY_SILENTLY_CLAIMED_VARIANT")
    if plan.get("family_baseline_only") is not True:
        raise RuntimeError("ROCK_HARMONY_NOT_FAMILY_BASELINE")
    if plan.get("variant_specific_harmony_claimed") is not False:
        raise RuntimeError("ROCK_HARMONY_FALSE_VARIANT_AUTHORITY")
    if plan.get("bar_count")!=40 or len(plan.get("bars") or [])!=40:
        raise RuntimeError("ROCK_HARMONY_NOT_40_BARS")

    vocabulary=set(plan.get("source_chord_vocabulary") or [])
    if vocabulary!={"Em","C","G","D"}:
        raise RuntimeError(
            "ROCK_HARMONY_SOURCE_VOCABULARY_CHANGED::"+
            json.dumps(sorted(vocabulary))
        )
    bar_symbols=[x["chord_symbol"] for x in plan["bars"]]
    if set(bar_symbols)-vocabulary:
        raise RuntimeError("ROCK_HARMONY_INVENTED_NEW_CHORD_VOCABULARY")
    if bar_symbols[-1]!="Em":
        raise RuntimeError("ROCK_HARMONY_FINAL_HOME_MISSING")

    sections=plan.get("sections") or {}
    expected_lengths={
        "INTRO_1":4,"VERSE_1":8,"CHORUS_1":8,
        "VERSE_2":8,"CHORUS_2":8,"OUTRO_1":4,
    }
    if set(sections)!=set(expected_lengths):
        raise RuntimeError("ROCK_HARMONY_SECTION_SET_DRIFT")
    for name,length in expected_lengths.items():
        if len(sections[name])!=length:
            raise RuntimeError("ROCK_HARMONY_SECTION_LENGTH_WRONG::"+name)

    if sections["VERSE_1"]==sections["VERSE_2"]:
        raise RuntimeError("ROCK_HARMONY_VERSES_LITERAL_COPY")
    if sections["CHORUS_1"]==sections["CHORUS_2"]:
        raise RuntimeError("ROCK_HARMONY_CHORUSES_LITERAL_COPY")
    if sections["VERSE_1"]==sections["CHORUS_1"]:
        raise RuntimeError("ROCK_HARMONY_VERSE_CHORUS_NO_CONTRAST")

    # Prove the whole piece is not one four-bar cell tiled ten times.
    four_bar_cells=[
        tuple(bar_symbols[i:i+4])
        for i in range(0,len(bar_symbols),4)
    ]
    if len(set(four_bar_cells))<4:
        raise RuntimeError(
            "ROCK_HARMONY_INSUFFICIENT_FOUR_BAR_DEVELOPMENT::"+
            json.dumps(four_bar_cells)
        )

    for key in (
        "old_generic_progression_engine_used",
        "generic_four_chord_engine_used",
        "new_chord_vocabulary_invented",
        "notes_generated","audio_generated","audio_authority",
        "finished_composition_authority","live_runtime_authority",
        "reasoning_engine_used","musical_quality_proven","listening_approval",
    ):
        if plan.get(key) is not False:
            raise RuntimeError("ROCK_HARMONY_PREMATURE_OR_GENERIC_FLAG::"+key)

    if not plan.get("v3_harmony_authority"):
        raise RuntimeError("ROCK_HARMONY_V3_AUTHORITY_MISSING")

    boundary_rows=[
        x for x in plan["bars"]
        if x["harmonic_plan_role"] in ("SECTION_BOUNDARY","FINAL_ARRIVAL")
    ]
    if len(boundary_rows)!=6:
        raise RuntimeError("ROCK_HARMONY_BOUNDARY_COUNT_WRONG")

    summary={
        "status":"PASS",
        "diagnostic_only":True,
        "genre":"ROCK",
        "profile_id":"ROCK_CORE_V2",
        "resolved_variant":None,
        "family_baseline_only":True,
        "bar_count":40,
        "source_chord_vocabulary":sorted(vocabulary),
        "unique_four_bar_harmonic_cells":len(set(four_bar_cells)),
        "verse2_differs_from_verse1":True,
        "chorus2_differs_from_chorus1":True,
        "verse_chorus_contrast_present":True,
        "final_chord":"Em",
        "generic_progression_engine_used":False,
        "new_chord_vocabulary_invented":False,
        "notes_generated":False,
        "audio_generated":False,
        "finished_composition_authority":False,
        "musical_quality_proven":False,
        "result":(
            "Rock Core now has a source-derived 40-bar harmonic candidate using only "
            "the current Rock seed vocabulary, with section-specific development and "
            "no generic progression engine. It remains a research plan, not approved music."
        ),
        "next_gate":"ROCK_CORE_EVENT_DEVELOPMENT_EXECUTOR",
        "harmony_plan_sha256":plan["harmony_plan_sha256"],
    }
    out=ROOT/"genre_contract_v3_research"/"ROCK_V3_CORE_HARMONY_PLAN_AUDIT.json"
    out.write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps(summary,indent=2))


if __name__=="__main__":
    main()
