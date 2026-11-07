"""Rock Core V3 structural form plan.

Expands the one-bar symbolic source cells into a family-baseline song FORM PLAN.
It does not expand notes and has no audio authority.

Evidence used:
- ROCK_CORE_V2 permits the broad family baseline when no subgenre cues exist.
- Broad Rock profile: verse/chorus tendency and 4- or 8-bar phrase behavior.
- Original source-pattern cells: INTRO, VERSE_A, VERSE_RESPONSE, FILL,
  CHORUS_B, CHORUS_RESPONSE, ENDING.
- Foreground pilot: lead/riff ownership alternates by source cell.

Important: repeated source cells are structural placeholders only. Literal
note-for-note repetition may not be promoted to final music; a development pass
must transform foreground/riff/harmony/detail before event expansion is eligible
for listening.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any

from genre_contract_v3_execution_bridge import contract_for, snapshot_for
from genre_v3_source_pattern_bridge import load_seed
from rock_v3_variant_resolver import resolve as resolve_rock_variant
from rock_v3_foreground_pilot import SECTION_PLAN

SCHEMA="ROCK_V3_CORE_FORM_PLAN_001"


class RockV3CoreFormPlanError(RuntimeError):
    pass


def _sha(value:Any)->str:
    return hashlib.sha256(
        json.dumps(value,sort_keys=True,separators=(",",":"),default=str).encode()
    ).hexdigest()


# Research form candidate based only on the broad family rules and available
# source-cell vocabulary. It is not a universal Rock form.
FORM_BLOCKS=(
    {
        "section_id":"INTRO_1",
        "section_type":"INTRO",
        "bars":4,
        "cells":("INTRO","INTRO","VERSE_A","FILL"),
    },
    {
        "section_id":"VERSE_1",
        "section_type":"VERSE",
        "bars":8,
        "cells":(
            "VERSE_A","VERSE_RESPONSE","VERSE_A","VERSE_RESPONSE",
            "VERSE_A","VERSE_RESPONSE","VERSE_A","FILL",
        ),
    },
    {
        "section_id":"CHORUS_1",
        "section_type":"CHORUS",
        "bars":8,
        "cells":(
            "CHORUS_B","CHORUS_RESPONSE","CHORUS_B","CHORUS_RESPONSE",
            "CHORUS_B","CHORUS_RESPONSE","CHORUS_B","FILL",
        ),
    },
    {
        "section_id":"VERSE_2",
        "section_type":"VERSE",
        "bars":8,
        "cells":(
            "VERSE_A","VERSE_RESPONSE","VERSE_A","VERSE_RESPONSE",
            "VERSE_A","VERSE_RESPONSE","VERSE_A","FILL",
        ),
    },
    {
        "section_id":"CHORUS_2",
        "section_type":"CHORUS",
        "bars":8,
        "cells":(
            "CHORUS_B","CHORUS_RESPONSE","CHORUS_B","CHORUS_RESPONSE",
            "CHORUS_B","CHORUS_RESPONSE","CHORUS_B","FILL",
        ),
    },
    {
        "section_id":"OUTRO_1",
        "section_type":"OUTRO",
        "bars":4,
        "cells":("CHORUS_B","CHORUS_RESPONSE","ENDING","ENDING"),
    },
)


def build()->dict[str,Any]:
    contract=contract_for("ROCK")
    snapshot=snapshot_for("ROCK")
    seed=load_seed("ROCK")
    gate=resolve_rock_variant(None,variant_cues_present=False)

    if snapshot.get("profile_id")!="ROCK_CORE_V2":
        raise RockV3CoreFormPlanError("ROCK_CORE_PROFILE_ID_DRIFT")
    if gate.get("status")!="ROCK_CORE_BASELINE_ALLOWED__NO_VARIANT_CUES":
        raise RockV3CoreFormPlanError("ROCK_CORE_BASELINE_FORM_GATE_BLOCKED")
    if gate.get("family_baseline_music_allowed") is not True:
        raise RockV3CoreFormPlanError("ROCK_CORE_BASELINE_NOT_ALLOWED")
    if gate.get("family_baseline_must_not_claim_subgenre") is not True:
        raise RockV3CoreFormPlanError("ROCK_CORE_SUBGENRE_GUARD_MISSING")

    snapshot_forms=set(snapshot.get("form_tendencies") or [])
    if "verse_chorus" not in snapshot_forms:
        raise RockV3CoreFormPlanError("ROCK_CORE_VERSE_CHORUS_NOT_ALLOWED")

    phrase_text=str(snapshot.get("phrase_behavior") or "")
    if "4-" not in phrase_text and "4" not in phrase_text:
        raise RockV3CoreFormPlanError("ROCK_CORE_FOUR_BAR_PHRASE_EVIDENCE_MISSING")
    if "8-bar" not in phrase_text and "8" not in phrase_text:
        raise RockV3CoreFormPlanError("ROCK_CORE_EIGHT_BAR_PHRASE_EVIDENCE_MISSING")

    seed_sections={x["name"] for x in seed.get("sections") or []}
    required_cells={
        "INTRO","VERSE_A","VERSE_RESPONSE","FILL",
        "CHORUS_B","CHORUS_RESPONSE","ENDING",
    }
    if seed_sections!=required_cells:
        raise RockV3CoreFormPlanError(
            "ROCK_SOURCE_CELL_VOCABULARY_CHANGED::"+
            json.dumps(sorted(seed_sections))
        )

    bars=[]
    absolute_bar=0
    for block in FORM_BLOCKS:
        cells=block["cells"]
        if len(cells)!=block["bars"]:
            raise RockV3CoreFormPlanError(
                "ROCK_FORM_BLOCK_CELL_COUNT_MISMATCH::"+block["section_id"]
            )
        if block["bars"] not in (4,8):
            raise RockV3CoreFormPlanError(
                "ROCK_FORM_BLOCK_NOT_4_OR_8_BARS::"+block["section_id"]
            )
        for local_bar,cell in enumerate(cells):
            if cell not in required_cells:
                raise RockV3CoreFormPlanError("ROCK_FORM_UNKNOWN_SOURCE_CELL::"+cell)
            fg=SECTION_PLAN[cell]
            bars.append({
                "bar":absolute_bar,
                "section_id":block["section_id"],
                "section_type":block["section_type"],
                "local_bar":local_bar,
                "phrase_index":local_bar//4,
                "source_cell":cell,
                "foreground_owner":fg["owner"],
                "foreground_motif_candidate":fg["motif"],
                "boundary_fill":cell=="FILL",
                "development_transform_required":True,
            })
            absolute_bar+=1

    if absolute_bar!=40:
        raise RockV3CoreFormPlanError("ROCK_CORE_FORM_NOT_40_BARS")

    section_lengths=[b["bars"] for b in FORM_BLOCKS]
    if section_lengths!=[4,8,8,8,8,4]:
        raise RockV3CoreFormPlanError("ROCK_CORE_FORM_SECTION_LENGTH_DRIFT")

    form_model=(contract.get("musical_grammar") or {}).get("form_model")
    development_model=(contract.get("musical_grammar") or {}).get("development_model")
    transition_model=(contract.get("musical_grammar") or {}).get("transition_model")

    result={
        "schema":SCHEMA,
        "status":"PASS",
        "genre":"ROCK",
        "profile_id":"ROCK_CORE_V2",
        "resolved_variant":None,
        "family_baseline_identity":"ROCK_CORE_V2",
        "family_baseline_must_not_claim_subgenre":True,
        "variant_cues_present":False,
        "meter":seed["meter"],
        "tempo_bpm":seed["tempo_bpm"],
        "bar_count":40,
        "section_count":len(FORM_BLOCKS),
        "section_lengths":section_lengths,
        "sections":[
            {
                "section_id":b["section_id"],
                "section_type":b["section_type"],
                "bars":b["bars"],
                "cells":list(b["cells"]),
            }
            for b in FORM_BLOCKS
        ],
        "bars":bars,
        "source_seed_id":seed["seed_id"],
        "source_cell_vocabulary":sorted(required_cells),
        "form_authority":deepcopy(form_model),
        "transition_authority":deepcopy(transition_model),
        "development_authority":deepcopy(development_model),
        "literal_source_cell_reuse_allowed_for_final_music":False,
        "development_transform_required_before_event_expansion":True,
        "harmony_development_required_before_listening":True,
        "foreground_development_required_before_listening":True,
        "transition_realization_required_before_listening":True,
        "note_events_generated":False,
        "audio_authority":False,
        "audio_generated":False,
        "finished_composition_authority":False,
        "live_runtime_authority":False,
        "reasoning_engine_used":False,
        "research_candidate_only":True,
        "next_gate":"ROCK_CORE_DEVELOPMENT_PLAN_THEN_EVENT_EXPANSION",
    }
    result["form_plan_sha256"]=_sha(result)
    return result
