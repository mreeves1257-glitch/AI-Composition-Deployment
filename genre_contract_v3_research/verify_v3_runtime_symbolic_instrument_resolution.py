"""Run the reconstructed Composer through V3 symbolic instrument resolution.

This is an integration test, not an audio test. It expects the modules in
current_master_forward to have been synchronized into composer/runtime first.
"""
from __future__ import annotations

from pathlib import Path
import json
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
RUNTIME=ROOT/"composer"/"runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0,str(RUNTIME))

from engine import AICompositionEngine
from genre_contract_v3_execution_bridge import load_master, snapshot_for
from genre_v3_instrument_authority import resolve as resolve_explicit
from genre_v3_source_pattern_bridge import resolve_source_roles


def eligible_genres():
    master=load_master()
    out=[]
    for name in master["contracts"]:
        snap=snapshot_for(name)
        if snap.get("resolution_policy")!="AUTOMATIC_BASELINE_ALLOWED":
            continue
        if name=="Classical":
            continue
        if resolve_explicit(name,snap).get("status")=="PASS":
            continue
        if resolve_source_roles(name).get("status")=="PASS":
            out.append(name)
    return out

def explicit_formation_genres():
    master=load_master()
    out=[]
    for name in master["contracts"]:
        if name=="Classical":
            continue
        snap=snapshot_for(name)
        if snap.get("resolution_policy")!="AUTOMATIC_BASELINE_ALLOWED":
            continue
        if resolve_explicit(name,snap).get("status")=="PASS":
            out.append(name)
    return out


def main():
    genres=eligible_genres()
    if len(genres)!=40:
        raise RuntimeError("EXPECTED_40_RUNTIME_SYMBOLIC_GENRES__GOT_"+str(len(genres)))
    explicit_genres=explicit_formation_genres()
    if len(explicit_genres)!=7:
        raise RuntimeError("EXPECTED_7_EXPLICIT_FORMATION_GENRES__GOT_"+str(len(explicit_genres)))

    rows={}
    explicit_rows={}
    with tempfile.TemporaryDirectory() as tmp:
        engine=AICompositionEngine(history_path=Path(tmp)/"history.json")
        if getattr(engine.theory,"profile_source",None)!="GENRE_CONTRACT_V3_ALL_55":
            raise RuntimeError("RUNTIME_ADAPTER_DID_NOT_DEFAULT_TO_V3")

        for name in genres:
            result=engine.run(name,mode="quick",audio_backend="PRESERVED")
            if result.get("status")!="V3_SYMBOLIC_INSTRUMENT_RESOLUTION_PASS":
                raise RuntimeError(
                    "RUNTIME_SYMBOLIC_RESOLUTION_FAIL::"+name+"::"+
                    json.dumps({
                        "status":result.get("status"),
                        "stage":result.get("stage"),
                        "reason":result.get("reason"),
                        "missing":result.get("missing"),
                    },sort_keys=True)
                )
            if result.get("audio_rendered") is not False:
                raise RuntimeError("RUNTIME_SYMBOLIC_AUDIO_ESCALATION::"+name)
            if result.get("finished_composition_authority") is not False:
                raise RuntimeError("SOURCE_PATTERN_WRONGLY_PROMOTED_TO_FINISHED_COMPOSITION::"+name)
            if result.get("source_pattern_finished_composition_eligible") is not False:
                raise RuntimeError("SOURCE_PATTERN_WRONGLY_MARKED_FINISHED_ELIGIBLE::"+name)
            if result.get("foreground_notes_generated") is not False:
                raise RuntimeError("FOREGROUND_NOTES_WERE_FABRICATED::"+name)
            if result.get("foreground_execution_status") != "STRUCTURED_FOREGROUND_AUTHORITY_PRESENT__NOTE_EXECUTION_NOT_COMPILED":
                raise RuntimeError("FOREGROUND_EXECUTION_STATUS_UNEXPECTED::"+name+"::"+str(result.get("foreground_execution_status")))
            fg=result.get("genre_v3_foreground_authority") or {}
            if fg.get("source_pattern_can_supply_finished_foreground") is not False:
                raise RuntimeError("FOREGROUND_AUTHORITY_GUARD_MISSING::"+name)
            theory=result["theory_package"]
            if theory.get("legacy_note_generator_used") is not False:
                raise RuntimeError("LEGACY_NOTE_GENERATOR_STILL_USED::"+name)
            authority=theory.get("genre_v3_instrument_authority") or {}
            if authority.get("authority")!="V3_GOVERNED_SOURCE_PATTERN_ROLES":
                raise RuntimeError("SOURCE_ROLE_AUTHORITY_NOT_ACTIVE::"+name)
            if theory.get("execution_template")!="v3_symbolic_source_pattern":
                raise RuntimeError("SOURCE_PATTERN_EXECUTION_TEMPLATE_NOT_ACTIVE::"+name)
            if not theory.get("events"):
                raise RuntimeError("RUNTIME_SYMBOLIC_EVENTS_EMPTY::"+name)

            package=result["instrument_package"]
            resolution=package.get("instrument_separator_resolution") or {}
            if resolution.get("status")!="PASS":
                raise RuntimeError("RUNTIME_INSTRUMENT_SEPARATOR_RESOLUTION_FAIL::"+name)
            if resolution.get("missing_registrations"):
                raise RuntimeError("RUNTIME_INSTRUMENT_REGISTRATION_MISSING::"+name)

            source_ids=sorted({e["instrument_id"] for e in theory["events"]})
            resolved_ids=sorted({
                p.get("instrument_id")
                for p in package.get("profiles",[])
                if p.get("instrument_id")
            })
            unresolved=[iid for iid in source_ids if iid not in resolved_ids]
            if unresolved:
                raise RuntimeError(
                    "RUNTIME_CURRENT_INSTRUMENT_PROFILE_MISSING::"+
                    name+"::"+",".join(unresolved)
                )

            rows[name]={
                "event_count":len(theory["events"]),
                "selected_instrument_ids":source_ids,
                "resolved_instrument_ids":resolved_ids,
                "registration_count":resolution.get("resolved_registration_count"),
                "tempo_bpm":theory.get("tempo_bpm"),
                "meter":theory.get("meter"),
                "legacy_note_generator_used":theory.get("legacy_note_generator_used"),
                "audio_rendered":result.get("audio_rendered"),
                "foreground_execution_status":result.get("foreground_execution_status"),
                "finished_composition_authority":result.get("finished_composition_authority"),
            }

        # A researched formation is not permission to synthesize generic music.
        # These seven genres must stop before the old family melody generator.
        for name in explicit_genres:
            result=engine.run(name,mode="quick",audio_backend="PRESERVED")
            if result.get("status")!="BLOCKED" or result.get("stage")!="THEORY":
                raise RuntimeError("EXPLICIT_FORMATION_DID_NOT_STOP_AT_THEORY::"+name)
            if result.get("reason")!="V3_EXPLICIT_FORMATION_COMPOSITION_PENDING":
                raise RuntimeError(
                    "EXPLICIT_FORMATION_BLOCK_REASON_WRONG::"+name+"::"+
                    str(result.get("reason"))
                )
            theory=result.get("theory_package") or {}
            if theory.get("legacy_note_generator_used") is not False:
                raise RuntimeError("EXPLICIT_FORMATION_USED_GENERIC_NOTE_GENERATOR::"+name)
            if theory.get("events")!=[]:
                raise RuntimeError("EXPLICIT_FORMATION_GENERATED_UNAPPROVED_EVENTS::"+name)
            if theory.get("finished_composition_authority") is not False:
                raise RuntimeError("EXPLICIT_FORMATION_PROMOTED_TO_FINISHED_COMPOSITION::"+name)
            explicit_rows[name]={
                "status":theory.get("status"),
                "palette":theory.get("palette"),
                "legacy_note_generator_used":theory.get("legacy_note_generator_used"),
                "finished_composition_authority":theory.get("finished_composition_authority"),
                "promotion_block":theory.get("promotion_block"),
            }

    summary={
        "status":"PASS",
        "diagnostic_only":True,
        "source_pattern_genre_count":len(rows),
        "explicit_formation_safe_stop_count":len(explicit_rows),
        "genre_count":len(rows)+len(explicit_rows),
        "genre_profile_source":"GENRE_CONTRACT_V3_ALL_55",
        "reasoning_engine_used":False,
        "audio_rendered":False,
        "live_runtime_promoted":False,
        "all_legacy_note_generator_bypassed":all(
            row["legacy_note_generator_used"] is False for row in rows.values()
        ),
        "all_finished_composition_authority_false":all(
            row["finished_composition_authority"] is False for row in rows.values()
        ),
        "all_foreground_execution_blocked":all(
            row["foreground_execution_status"]=="STRUCTURED_FOREGROUND_AUTHORITY_PRESENT__NOTE_EXECUTION_NOT_COMPILED"
            for row in rows.values()
        ),
        "result":(
            "The reconstructed Composer accepted V3-governed symbolic events for "
            "all 40 automatic genres without explicit V3 formations and resolved every "
            "selected event instrument into the current instrument library. The seven "
            "automatic genres with explicit researched V3 formations stop safely before "
            "the generic legacy melody generator. Brush-snare and hand-drum remain "
            "canonical resource-required identities. Rendering remains blocked, and "
            "accompaniment-only packages cannot be promoted without a foreground executor."
        ),
        "genres":rows,
        "explicit_formation_safe_stops":explicit_rows,
        "next_gate":"GENRE_SPECIFIC_FORM_AND_MUSICAL_BEHAVIOR_REVALIDATION_BEFORE_AUDIO",
    }
    out=ROOT/"genre_contract_v3_research"/"V3_RUNTIME_SYMBOLIC_INSTRUMENT_RESOLUTION_AUDIT.json"
    out.write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps(summary,indent=2))


if __name__=="__main__":
    main()
