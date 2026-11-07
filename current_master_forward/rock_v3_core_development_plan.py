"""Rock Core V3 development plan.

This module does not generate or mutate notes. It turns the 40-bar Rock Core form
plan into explicit per-section transformation requirements so repeated source
cells cannot be promoted as literal loops.

The plan is constrained to the current Rock V3 contract and current source-cell
vocabulary. It deliberately rejects the older generic full-length development
patch as execution authority.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any

from genre_contract_v3_execution_bridge import contract_for
from rock_v3_core_form_plan import build as build_form_plan

SCHEMA="ROCK_V3_CORE_DEVELOPMENT_PLAN_001"


class RockV3CoreDevelopmentPlanError(RuntimeError):
    pass


def _sha(value:Any)->str:
    return hashlib.sha256(
        json.dumps(value,sort_keys=True,separators=(",",":"),default=str).encode()
    ).hexdigest()


# Development intents are structural requirements, not literal MIDI edits.
# Every later executor must prove that a requested transform is realized in a
# genre-appropriate way rather than by generic octave flips or random jitter.
SECTION_DEVELOPMENT={
    "INTRO_1":{
        "energy":"ESTABLISH",
        "foreground_policy":"RHYTHM_RIFF_FIRST__SELECTIVE_LEAD_ENTRY",
        "required_transforms":[
            "LOWER_DENSITY_THAN_MAIN_SECTIONS",
            "BOUNDARY_FILL_IN_FINAL_BAR",
        ],
        "forbidden":["FULL_CHORUS_DENSITY","CONTINUOUS_LEAD"],
    },
    "VERSE_1":{
        "energy":"BASELINE",
        "foreground_policy":"CALL_RESPONSE",
        "required_transforms":[
            "ALTERNATE_LEAD_AND_RIFF_WINDOWS",
            "PRESERVE_RHYTHM_SECTION_CLARITY",
        ],
        "forbidden":["CONTINUOUS_LEAD","EVERY_GAP_FILLED"],
    },
    "CHORUS_1":{
        "energy":"LIFT_1",
        "foreground_policy":"LEAD_WITH_RIFF_RESPONSE",
        "required_transforms":[
            "GREATER_SECTION_CONTRAST_THAN_VERSE_1",
            "FOREGROUND_REGISTER_OR_CONTOUR_LIFT",
            "RHYTHM_GUITAR_YIELDS_DENSITY_IN_LEAD_WINDOWS",
        ],
        "forbidden":["VELOCITY_ONLY_LIFT","UNISON_ALL_PARTS"],
    },
    "VERSE_2":{
        "energy":"DEVELOPED_VERSE",
        "foreground_policy":"CALL_RESPONSE_VARIANT",
        "required_transforms":[
            "NOT_LITERAL_COPY_OF_VERSE_1",
            "MOTIF_TRANSFORMATION",
            "RHYTHMIC_OR_REGISTER_VARIATION",
            "PRESERVE_CORE_GROOVE_IDENTITY",
        ],
        "forbidden":["BAR_FOR_BAR_COPY_OF_VERSE_1","RANDOM_PITCH_REPLACEMENT"],
    },
    "CHORUS_2":{
        "energy":"LIFT_2",
        "foreground_policy":"REPRISE_WITH_DEVELOPMENT",
        "required_transforms":[
            "RECALL_CHORUS_1_IDENTITY",
            "NOT_LITERAL_COPY_OF_CHORUS_1",
            "MOTIF_REPRISE_WITH_VARIATION",
            "SECTION_LEVEL_DYNAMIC_OR_REGISTER_DEVELOPMENT",
        ],
        "forbidden":["BAR_FOR_BAR_COPY_OF_CHORUS_1","GENERIC_OCTAVE_FLIP"],
    },
    "OUTRO_1":{
        "energy":"RELEASE",
        "foreground_policy":"CADENTIAL_FOREGROUND",
        "required_transforms":[
            "ENDING_CELLS_GAIN_FINALITY",
            "REDUCE_OR_RESOLVE_DENSITY",
            "CLEAR_FINAL_ARRIVAL",
        ],
        "forbidden":["INFINITE_LOOP","ABRUPT_RANDOM_STOP"],
    },
}

ALLOWED_DEVELOPMENT_AXES=(
    "MOTIF_CONTOUR",
    "MOTIF_RHYTHM",
    "REGISTER_WITHIN_INSTRUMENT_RANGE",
    "RHYTHM_GUITAR_DENSITY",
    "BASS_PICKUP_OR_FILL_PLACEMENT",
    "SECTION_DYNAMIC_SHAPE",
    "ARTICULATION_ROLE",
    "INTENTIONAL_REST_SPACE",
    "BOUNDARY_FILL_BEHAVIOR",
    "HARMONIC_PROGRESSION_WITHIN_ROCK_AUTHORITY",
)

FORBIDDEN_GLOBAL_SHORTCUTS=(
    "GENERIC_OCTAVE_FLIP",
    "RANDOM_JITTER",
    "CROSS_GENRE_MELODY_COPY",
    "ARBITRARY_NEW_INSTRUMENT_ROLE",
    "VELOCITY_ONLY_SECTION_DEVELOPMENT",
    "LITERAL_ONE_BAR_LOOP_AS_FINISHED_MUSIC",
    "GENERIC_FOUR_CHORD_ENGINE_AS_ROCK_VARIANT_AUTHORITY",
)


def build()->dict[str,Any]:
    form=build_form_plan()
    contract=contract_for("ROCK")
    grammar=contract.get("musical_grammar") or {}

    for key in ("development_model","transition_model","phrase_model","melody_model"):
        if not grammar.get(key):
            raise RockV3CoreDevelopmentPlanError(
                "ROCK_V3_DEVELOPMENT_AUTHORITY_MISSING::"+key
            )

    section_ids=[x["section_id"] for x in form["sections"]]
    if set(section_ids)!=set(SECTION_DEVELOPMENT):
        raise RockV3CoreDevelopmentPlanError("ROCK_DEVELOPMENT_SECTION_SET_DRIFT")

    bars=[]
    occurrence_by_cell={}
    for row in form["bars"]:
        cell=row["source_cell"]
        occurrence=occurrence_by_cell.get(cell,0)
        occurrence_by_cell[cell]=occurrence+1
        spec=SECTION_DEVELOPMENT[row["section_id"]]

        # First occurrence may establish a cell. Every recurrence must be treated
        # as a developmental event, never as permission for literal copying.
        recurrence=occurrence>0
        bars.append({
            **deepcopy(row),
            "source_cell_occurrence":occurrence,
            "source_cell_recurrence":recurrence,
            "development_epoch":row["section_id"],
            "energy_intent":spec["energy"],
            "foreground_policy":spec["foreground_policy"],
            "section_required_transforms":list(spec["required_transforms"]),
            "section_forbidden_transforms":list(spec["forbidden"]),
            "recurrence_transform_required":recurrence,
            "literal_note_copy_permitted":False,
        })

    if not any(x["source_cell_recurrence"] for x in bars):
        raise RockV3CoreDevelopmentPlanError("ROCK_DEVELOPMENT_NO_RECURRENT_CELLS_DETECTED")
    if any(x["literal_note_copy_permitted"] for x in bars):
        raise RockV3CoreDevelopmentPlanError("ROCK_DEVELOPMENT_LITERAL_COPY_ALLOWED")

    result={
        "schema":SCHEMA,
        "status":"PASS",
        "genre":"ROCK",
        "profile_id":"ROCK_CORE_V2",
        "resolved_variant":None,
        "family_baseline_only":True,
        "form_plan_sha256":form["form_plan_sha256"],
        "bar_count":form["bar_count"],
        "sections":deepcopy(form["sections"]),
        "bars":bars,
        "section_development":deepcopy(SECTION_DEVELOPMENT),
        "allowed_development_axes":list(ALLOWED_DEVELOPMENT_AXES),
        "forbidden_global_shortcuts":list(FORBIDDEN_GLOBAL_SHORTCUTS),
        "v3_development_authority":deepcopy(grammar["development_model"]),
        "v3_transition_authority":deepcopy(grammar["transition_model"]),
        "v3_phrase_authority":deepcopy(grammar["phrase_model"]),
        "v3_melody_authority":deepcopy(grammar["melody_model"]),
        "old_genre_development_patch_execution_authority":False,
        "development_notes_generated":False,
        "event_expansion_ready":False,
        "audio_generated":False,
        "audio_authority":False,
        "finished_composition_authority":False,
        "live_runtime_authority":False,
        "reasoning_engine_used":False,
        "next_gate":"IMPLEMENT_ROCK_CORE_DEVELOPMENT_EXECUTOR_WITH_EXPLICIT_TESTS",
    }
    result["development_plan_sha256"]=_sha(result)
    return result
