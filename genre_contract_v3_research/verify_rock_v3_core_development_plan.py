"""Audit the Rock Core V3 development plan before any note expansion."""
from __future__ import annotations

from pathlib import Path
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
FORWARD=ROOT/"current_master_forward"
if str(FORWARD) not in sys.path:
    sys.path.insert(0,str(FORWARD))

from rock_v3_core_development_plan import build


def main():
    plan=build()
    if plan.get("status")!="PASS":
        raise RuntimeError("ROCK_DEVELOPMENT_PLAN_NOT_PASS")
    if plan.get("genre")!="ROCK" or plan.get("profile_id")!="ROCK_CORE_V2":
        raise RuntimeError("ROCK_DEVELOPMENT_IDENTITY_DRIFT")
    if plan.get("resolved_variant") is not None:
        raise RuntimeError("ROCK_DEVELOPMENT_SILENTLY_CLAIMED_SUBGENRE")
    if plan.get("family_baseline_only") is not True:
        raise RuntimeError("ROCK_DEVELOPMENT_NOT_MARKED_FAMILY_BASELINE")
    if plan.get("bar_count")!=40 or len(plan.get("bars") or [])!=40:
        raise RuntimeError("ROCK_DEVELOPMENT_NOT_40_BARS")
    if len(plan.get("sections") or [])!=6:
        raise RuntimeError("ROCK_DEVELOPMENT_SECTION_COUNT_WRONG")

    # This is a plan only. Nothing downstream may mistake it for music/audio.
    for key in (
        "development_notes_generated","event_expansion_ready","audio_generated",
        "audio_authority","finished_composition_authority","live_runtime_authority",
        "reasoning_engine_used",
    ):
        if plan.get(key) is not False:
            raise RuntimeError("ROCK_DEVELOPMENT_PREMATURE_AUTHORITY::"+key)
    if plan.get("old_genre_development_patch_execution_authority") is not False:
        raise RuntimeError("OLD_GENERIC_DEVELOPMENT_PATCH_REACTIVATED")

    required_forbidden={
        "GENERIC_OCTAVE_FLIP",
        "RANDOM_JITTER",
        "CROSS_GENRE_MELODY_COPY",
        "ARBITRARY_NEW_INSTRUMENT_ROLE",
        "VELOCITY_ONLY_SECTION_DEVELOPMENT",
        "LITERAL_ONE_BAR_LOOP_AS_FINISHED_MUSIC",
        "GENERIC_FOUR_CHORD_ENGINE_AS_ROCK_VARIANT_AUTHORITY",
    }
    actual_forbidden=set(plan.get("forbidden_global_shortcuts") or [])
    if not required_forbidden.issubset(actual_forbidden):
        raise RuntimeError(
            "ROCK_DEVELOPMENT_FORBIDDEN_SHORTCUT_MISSING::"+
            json.dumps(sorted(required_forbidden-actual_forbidden))
        )

    required_axes={
        "MOTIF_CONTOUR","MOTIF_RHYTHM","REGISTER_WITHIN_INSTRUMENT_RANGE",
        "RHYTHM_GUITAR_DENSITY","BASS_PICKUP_OR_FILL_PLACEMENT",
        "SECTION_DYNAMIC_SHAPE","ARTICULATION_ROLE","INTENTIONAL_REST_SPACE",
        "BOUNDARY_FILL_BEHAVIOR","HARMONIC_PROGRESSION_WITHIN_ROCK_AUTHORITY",
    }
    actual_axes=set(plan.get("allowed_development_axes") or [])
    if not required_axes.issubset(actual_axes):
        raise RuntimeError(
            "ROCK_DEVELOPMENT_AXIS_MISSING::"+
            json.dumps(sorted(required_axes-actual_axes))
        )

    section_dev=plan.get("section_development") or {}
    expected_sections={
        "INTRO_1","VERSE_1","CHORUS_1","VERSE_2","CHORUS_2","OUTRO_1"
    }
    if set(section_dev)!=expected_sections:
        raise RuntimeError("ROCK_DEVELOPMENT_SECTION_POLICY_DRIFT")

    if "NOT_LITERAL_COPY_OF_VERSE_1" not in section_dev["VERSE_2"]["required_transforms"]:
        raise RuntimeError("ROCK_VERSE2_LITERAL_COPY_NOT_BLOCKED")
    if "NOT_LITERAL_COPY_OF_CHORUS_1" not in section_dev["CHORUS_2"]["required_transforms"]:
        raise RuntimeError("ROCK_CHORUS2_LITERAL_COPY_NOT_BLOCKED")
    if "MOTIF_TRANSFORMATION" not in section_dev["VERSE_2"]["required_transforms"]:
        raise RuntimeError("ROCK_VERSE2_MOTIF_DEVELOPMENT_MISSING")
    if "MOTIF_REPRISE_WITH_VARIATION" not in section_dev["CHORUS_2"]["required_transforms"]:
        raise RuntimeError("ROCK_CHORUS2_REPRISE_DEVELOPMENT_MISSING")
    if "VELOCITY_ONLY_LIFT" not in section_dev["CHORUS_1"]["forbidden"]:
        raise RuntimeError("ROCK_CHORUS1_VELOCITY_ONLY_LIFT_NOT_BLOCKED")
    if "GENERIC_OCTAVE_FLIP" not in section_dev["CHORUS_2"]["forbidden"]:
        raise RuntimeError("ROCK_CHORUS2_GENERIC_OCTAVE_FLIP_NOT_BLOCKED")

    bars=plan["bars"]
    recurrent=[x for x in bars if x.get("source_cell_recurrence")]
    initial=[x for x in bars if not x.get("source_cell_recurrence")]
    if not recurrent:
        raise RuntimeError("ROCK_DEVELOPMENT_RECURRENT_CELL_SET_EMPTY")
    if any(x.get("recurrence_transform_required") is not True for x in recurrent):
        raise RuntimeError("ROCK_DEVELOPMENT_RECURRENCE_TRANSFORM_NOT_REQUIRED")
    if any(x.get("literal_note_copy_permitted") is not False for x in bars):
        raise RuntimeError("ROCK_DEVELOPMENT_LITERAL_NOTE_COPY_ALLOWED")
    if any(x.get("development_epoch") not in expected_sections for x in bars):
        raise RuntimeError("ROCK_DEVELOPMENT_EPOCH_INVALID")

    owners={x.get("foreground_owner") for x in bars}
    if owners!={"LEAD_GUITAR","HARMONY_RIFF"}:
        raise RuntimeError("ROCK_DEVELOPMENT_FOREGROUND_HANDOFF_LOST")

    # V3 authority must be present rather than a free-floating custom plan.
    for key in (
        "v3_development_authority","v3_transition_authority",
        "v3_phrase_authority","v3_melody_authority",
    ):
        if not plan.get(key):
            raise RuntimeError("ROCK_DEVELOPMENT_V3_AUTHORITY_MISSING::"+key)

    summary={
        "status":"PASS",
        "diagnostic_only":True,
        "genre":"ROCK",
        "profile_id":"ROCK_CORE_V2",
        "resolved_variant":None,
        "family_baseline_only":True,
        "bar_count":40,
        "section_count":6,
        "initial_source_cell_occurrences":len(initial),
        "recurrent_source_cell_occurrences":len(recurrent),
        "all_recurrent_cells_require_transformation":True,
        "literal_note_copy_permitted":False,
        "old_generic_development_patch_authority":False,
        "forbidden_shortcuts":sorted(actual_forbidden),
        "allowed_development_axes":sorted(actual_axes),
        "foreground_owners":sorted(owners),
        "notes_generated":False,
        "audio_generated":False,
        "finished_composition_authority":False,
        "result":(
            "Rock Core now has a V3-governed 40-bar development plan that requires "
            "recurring source cells to transform and explicitly blocks the old generic "
            "octave/jitter/four-chord shortcuts. It remains a non-generative plan."
        ),
        "next_gate":"IMPLEMENT_ROCK_CORE_DEVELOPMENT_EXECUTOR_WITH_EXPLICIT_TESTS",
        "development_plan_sha256":plan["development_plan_sha256"],
    }
    out=ROOT/"genre_contract_v3_research"/"ROCK_V3_CORE_DEVELOPMENT_PLAN_AUDIT.json"
    out.write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps(summary,indent=2))


if __name__=="__main__":
    main()
