"""Rock Core V3 harmonic-development plan.

Research-only harmonic plan for the current ROCK_CORE_V2 family-baseline pilot.
It does not claim a universal Rock progression and does not use the old generic
four-chord progression engine.

Authority:
- current Rock V3 harmony model;
- the current project-authored Rock source seed (Em, C, G, D vocabulary);
- the 40-bar Rock Core form/development plans.

The plan develops order and arrival behavior using only the current seed's
harmonic vocabulary. No notes or audio are generated here.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

from genre_contract_v3_execution_bridge import contract_for
from genre_v3_source_pattern_bridge import load_seed
from rock_v3_core_form_plan import build as build_form
from rock_v3_core_development_plan import build as build_development

SCHEMA="ROCK_V3_CORE_HARMONY_PLAN_001"


class RockV3CoreHarmonyPlanError(RuntimeError):
    pass


def _sha(value:Any)->str:
    return hashlib.sha256(
        json.dumps(value,sort_keys=True,separators=(",",":"),default=str).encode()
    ).hexdigest()


# One research candidate for the broad Rock Core pilot. The progression material
# is restricted to the source seed vocabulary. Section order changes create
# verse/chorus contrast and later-section development without invoking a generic
# progression generator.
SECTION_CHORDS={
    "INTRO_1": ("Em","Em","C","D"),
    "VERSE_1": ("Em","C","G","D","Em","C","G","D"),
    "CHORUS_1": ("G","D","Em","C","G","D","C","D"),
    "VERSE_2": ("Em","C","G","D","Em","G","C","D"),
    "CHORUS_2": ("G","D","Em","C","C","G","D","Em"),
    "OUTRO_1": ("Em","C","D","Em"),
}


def build()->dict[str,Any]:
    contract=contract_for("ROCK")
    seed=load_seed("ROCK")
    form=build_form()
    development=build_development()

    harmony_model=(contract.get("musical_grammar") or {}).get("harmony_model")
    if not harmony_model:
        raise RockV3CoreHarmonyPlanError("ROCK_V3_HARMONY_AUTHORITY_MISSING")
    if harmony_model.get("authority")!="RESOLVED_ROCK_SUBGENRE":
        # The broad baseline is permitted only as a family-level candidate when
        # no variant cues exist. It still may not claim variant-specific authority.
        raise RockV3CoreHarmonyPlanError("ROCK_V3_HARMONY_AUTHORITY_CHANGED")

    source_symbols=[x.get("symbol") for x in seed.get("chords") or []]
    source_vocabulary={x for x in source_symbols if x}
    if source_vocabulary!={"Em","C","G","D"}:
        raise RockV3CoreHarmonyPlanError(
            "ROCK_SOURCE_HARMONY_VOCABULARY_CHANGED::"+
            json.dumps(sorted(source_vocabulary))
        )

    section_ids=[x["section_id"] for x in form["sections"]]
    if section_ids!=["INTRO_1","VERSE_1","CHORUS_1","VERSE_2","CHORUS_2","OUTRO_1"]:
        raise RockV3CoreHarmonyPlanError("ROCK_FORM_SECTION_ORDER_CHANGED")
    if set(section_ids)!=set(SECTION_CHORDS):
        raise RockV3CoreHarmonyPlanError("ROCK_HARMONY_SECTION_SET_MISMATCH")
    if development.get("form_plan_sha256")!=form.get("form_plan_sha256"):
        raise RockV3CoreHarmonyPlanError("ROCK_HARMONY_DEVELOPMENT_FORM_HASH_MISMATCH")

    bars=[]
    absolute=0
    for section in form["sections"]:
        section_id=section["section_id"]
        chords=SECTION_CHORDS[section_id]
        if len(chords)!=section["bars"]:
            raise RockV3CoreHarmonyPlanError(
                "ROCK_HARMONY_SECTION_LENGTH_MISMATCH::"+section_id
            )
        for local_bar,symbol in enumerate(chords):
            if symbol not in source_vocabulary:
                raise RockV3CoreHarmonyPlanError(
                    "ROCK_HARMONY_LEFT_SOURCE_VOCABULARY::"+symbol
                )
            bars.append({
                "bar":absolute,
                "section_id":section_id,
                "section_type":section["section_type"],
                "local_bar":local_bar,
                "chord_symbol":symbol,
                "source_vocabulary_member":True,
                "harmonic_plan_role":(
                    "FINAL_ARRIVAL" if absolute==39 else
                    "SECTION_BOUNDARY" if local_bar==len(chords)-1 else
                    "SECTION_MOTION"
                ),
            })
            absolute+=1

    if absolute!=40:
        raise RockV3CoreHarmonyPlanError("ROCK_HARMONY_NOT_40_BARS")
    if bars[-1]["chord_symbol"]!="Em":
        raise RockV3CoreHarmonyPlanError("ROCK_HARMONY_FINAL_NOT_HOME")

    verse1=SECTION_CHORDS["VERSE_1"]
    verse2=SECTION_CHORDS["VERSE_2"]
    chorus1=SECTION_CHORDS["CHORUS_1"]
    chorus2=SECTION_CHORDS["CHORUS_2"]
    if verse1==verse2:
        raise RockV3CoreHarmonyPlanError("ROCK_VERSE2_HARMONY_NOT_DEVELOPED")
    if chorus1==chorus2:
        raise RockV3CoreHarmonyPlanError("ROCK_CHORUS2_HARMONY_NOT_DEVELOPED")
    if verse1==chorus1:
        raise RockV3CoreHarmonyPlanError("ROCK_VERSE_CHORUS_HARMONY_NOT_CONTRASTED")

    result={
        "schema":SCHEMA,
        "status":"PASS",
        "genre":"ROCK",
        "profile_id":"ROCK_CORE_V2",
        "resolved_variant":None,
        "family_baseline_only":True,
        "variant_specific_harmony_claimed":False,
        "key_center_candidate":"E_MINOR_MODAL_TONAL_CENTER",
        "source_seed_id":seed["seed_id"],
        "source_chord_vocabulary":sorted(source_vocabulary),
        "source_chord_sequence":source_symbols,
        "bar_count":40,
        "sections":{
            key:list(value) for key,value in SECTION_CHORDS.items()
        },
        "bars":bars,
        "v3_harmony_authority":harmony_model,
        "old_generic_progression_engine_used":False,
        "generic_four_chord_engine_used":False,
        "new_chord_vocabulary_invented":False,
        "notes_generated":False,
        "audio_generated":False,
        "audio_authority":False,
        "finished_composition_authority":False,
        "live_runtime_authority":False,
        "reasoning_engine_used":False,
        "research_candidate_only":True,
        "musical_quality_proven":False,
        "listening_approval":False,
        "next_gate":"ROCK_CORE_EVENT_DEVELOPMENT_EXECUTOR",
    }
    result["harmony_plan_sha256"]=_sha(result)
    return result
