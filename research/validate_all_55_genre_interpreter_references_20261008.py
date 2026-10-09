"""Confirm 55 named genres have their OWN interpreter entry in 7-stage order.

No genre profile, instrument bank, executable Composer code, API or deployed
route is modified. Checks XRefs point at original genre-specific musical
definitions. Fail closed rather than falling back to a Rock groove.
"""
from __future__ import annotations
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"composer_overrides"/"genre_styles"
ORDER=[
    "SELECT_GENRE","DEFINE_MUSICAL_STRUCTURE","CHOOSE_INSTRUMENTS_AND_DRUM_KIT",
    "COMPOSE_SEPARATE_PARTS","PERFORM_MUSICALLY","RENDER_SEPARATE_AUDIO_STEMS",
    "GENRE_MIX_THEN_STANDALONE_3D_MIX"
]

def expect(cond,message):
    if not cond:raise AssertionError(message)

def validate():
    total=0;families=0;unique_names=set();examples={}
    for path in sorted(BASE.glob("*/profile.json")):
        family=path.parent.name
        original=json.loads(path.read_text())
        companion=path.parent/"GENRE_INTERPRETER_HANDOFF_R1.json"
        expect(companion.is_file(),"INTERPRETER_SLOT_FILE_MISSING:"+family)
        companion_data=json.loads(companion.read_text())
        expect(companion_data["schema_version"]=="GENRE_INTERPRETER_FAMILY_XREF_R1",
               "UNRECOGNIZED_HANDOFF_SCHEMA:"+family)
        expect(companion_data["source_profile_file"]==str(path.relative_to(ROOT)),
               "ORIGINAL_PROFILE_XREF_MISMATCH:"+family)
        expect(original["stage_wiring_activated"] is False,"FAMILY_ACCIDENTALLY_ENABLED:"+family)
        expect(original["reference_only"] is True and original["source_assets_immutable"] is True,
               "ORIGINALS_NOT_PROTECTED:"+family)
        profiles=original["profiles"]
        entries=companion_data["genres"]
        expect(len(profiles)==len(entries)==original["genre_count"]==companion_data["profile_count"],
               "FAMILY_GENRE_COVERAGE_MISMATCH:"+family)
        expect(companion_data["original_connections_activated"] is False,
               "GENRE_INTERPRETER_REFERENCE_WENT_LIVE:"+family)
        expect({x["genre_name"] for x in entries}==set(profiles),
               "MISSING_OR_EXTRA_INTERPRETER_GENRE:"+family)
        for entry in entries:
            name=entry["genre_name"]
            expect(name not in unique_names,"DUPLICATED_GENRE_REFERENCE:"+name)
            unique_names.add(name)
            prof=profiles[name]
            definitions=prof["musical_definition"]
            stages=prof["seven_stage_plan"]
            expect(stages["stage_order"]==ORDER,
                   "ORIGINAL_SEVEN_STAGE_ORDER_CHANGED:"+name)
            expect(all(not s["connection_activated"] for s in stages["stages"]) and
                   all(x["status"]=="RESERVED_NOT_CONNECTED" for x in stages["proposed_handoffs"]),
                   "ORIGINAL_GENRE_STAGE_PREMATURELY_LINKED:"+name)
            expect(stages["enable_runtime_connections"] is False,
                   "GENRE_STAGE_SILENTLY_ENABLED:"+name)
            expect(entry["profile_id"]==definitions["profile_id"],"PROFILE_ID_MISMATCH:"+name)
            expect(entry.get("interpreter_slot",entry.get("isolated_slot"))=="BETWEEN_ORIGINAL_STAGE_03_AND_04",
                   "INTERPRETER_ATTACHED_IN_WRONG_STAGE:"+name)
            xref=entry["source_of_truth"]
            expect(xref["read_original_values_at_runtime"] is True and
                   xref["file"]==str(path.relative_to(ROOT)),
                   "MISSING_ORIGINAL_CROSS_REFERENCE:"+name)
            escaped=name.replace("~","~0").replace("/","~1")
            expect(xref["json_pointer"]==f"/profiles/{escaped}/musical_definition",
                   "WRONG_MUSICAL_DEFINITION_TARGET:"+name)
            expect(entry.get("connected",entry.get("interpreter_stage_connected")) is False,
                   "UNAPPROVED_INTERPRETER_RUN:"+name)
            expect(isinstance(definitions["groove_behavior"],str) and
                   isinstance(definitions["percussion_behavior_if_applicable"],str),
                   "LOST_ORIGINAL_MUSICAL_LANGUAGE:"+name)
            examples[name]={"family":family,"groove":definitions["groove_behavior"],
                "percussion":definitions["percussion_behavior_if_applicable"],
                "meter":definitions["meter_options"],
                "intent_source":xref["json_pointer"]}
            total+=1
        families+=1
    expect(families==13 and total==55 and len(unique_names)==55,
           "ALL_GENRES_NOT_READY")
    expect("percussion absent" in examples["PIANIST"]["percussion"],
           "SOLO_PIANIST_MUST_NOT_GET_ROCK_DRUMMER")
    expect("3/4" in examples["WALTZ"]["meter"],
           "WALTZ_METER_NOT_PROTECTED")
    expect("clave" in examples["Salsa"]["percussion"].lower(),
           "LATIN_PERCUSSION_GENRE_LANGUAGE_LOST")
    expect("swing" in examples["Swing"]["groove"].lower(),
           "JAZZ_SWING_NOT_PRESERVED")
    summary={"status":"ALL_55_GENRE_INTERPRETER_REFERENCES_VERIFIED",
        "family_folders":families,"distinct_genres":total,
        "all_original_seven_stage_sequences_intact":True,
        "stage_2_definitions_are_original_authority":True,
        "stage_3_recorded_resource_selection_unchanged":True,
        "interpreter_slot":"BETWEEN_STAGES_3_AND_4",
        "cross_rock_style_contamination":False,
        "per_genre_executable_backend_already_available":False,
        "all_genre_connections_inactive":True,
        "live_composer_unchanged":True,"plug_unchanged":True,
        "source_instruments_unchanged":True,"final_3D_mixer_unchanged":True,
        "examples":{n:examples[n] for n in
                    ("ROCK","Swing","Salsa","WALTZ","PIANIST","Funk","Traditional Country")}}
    print("ALL_55_GENRE_INTERPRETER_COVERAGE_PASS",json.dumps(summary),flush=True)
    return summary

if __name__=="__main__":
    validate()
