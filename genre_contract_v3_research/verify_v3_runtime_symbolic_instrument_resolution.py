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
            fg=result.get("genre_v3_foreground_authority") or {}
            if fg.get("source_pattern_can_supply_finished_foreground") is not False:
                raise RuntimeError("FOREGROUND_AUTHORITY_GUARD_MISSING::"+name)
            foreground_registry=result.get("foreground_executor_registry_status") or {}
            composition_registry=result.get("composition_executor_registry_status") or {}
            if name=="ROCK":
                if result.get("foreground_notes_generated") is not True:
                    raise RuntimeError("ROCK_DEVELOPED_FOREGROUND_NOT_ACTIVE")
                if result.get("composition_notes_generated") is not True:
                    raise RuntimeError("ROCK_DEVELOPED_COMPOSITION_NOT_ACTIVE")
                if result.get("performance_realization_applied") is not False:
                    raise RuntimeError("ROCK_PERFORMANCE_REALIZATION_PREMATURE")
                if result.get("foreground_execution_status")!="GENRE_SPECIFIC_COMPOSITION_RESEARCH_CANDIDATE__STRUCTURAL_PASS":
                    raise RuntimeError("ROCK_COMPOSITION_RUNTIME_STATUS_WRONG::"+str(result.get("foreground_execution_status")))
                if composition_registry.get("registered") is not True or composition_registry.get("eligible") is not True:
                    raise RuntimeError("ROCK_COMPOSITION_EXECUTOR_NOT_ACTIVE")
                if composition_registry.get("scope")!="FAMILY_BASELINE_ONLY_WHEN_NO_VARIANT_CUES":
                    raise RuntimeError("ROCK_COMPOSITION_EXECUTOR_SCOPE_WRONG")
                candidate=result.get("composition_candidate_execution") or {}
                if candidate.get("bar_count")!=40:
                    raise RuntimeError("ROCK_RUNTIME_COMPOSITION_NOT_40_BARS")
                if candidate.get("event_count")!=897:
                    raise RuntimeError("ROCK_RUNTIME_COMPOSITION_EVENT_COUNT_WRONG::"+str(candidate.get("event_count")))
                if candidate.get("rhythm_guitar_vertical_voicing_used") is not True:
                    raise RuntimeError("ROCK_RUNTIME_VERTICAL_GUITAR_FLAG_MISSING")
                if candidate.get("minimum_harmony_attack_pitch_count")!=3:
                    raise RuntimeError("ROCK_RUNTIME_HARMONY_MINIMUM_VOICING_WRONG")
                if candidate.get("performance_realization_applied") is not False:
                    raise RuntimeError("ROCK_RUNTIME_CANDIDATE_PERFORMANCE_ALREADY_APPLIED")
                if result.get("foreground_candidate_execution") is not None:
                    raise RuntimeError("ROCK_OLD_SEVEN_BAR_FOREGROUND_CANDIDATE_STILL_EXECUTED")
                if foreground_registry.get("registered") is not True:
                    raise RuntimeError("ROCK_FOREGROUND_REGISTRY_PROVENANCE_MISSING")
            else:
                if result.get("composition_notes_generated") is not False:
                    raise RuntimeError("UNREGISTERED_COMPOSITION_NOTES_WERE_FABRICATED::"+name)
                if composition_registry.get("registered") is not False:
                    raise RuntimeError("UNEXPECTED_COMPOSITION_EXECUTOR_REGISTERED::"+name)
                if result.get("foreground_notes_generated") is not False:
                    raise RuntimeError("UNREGISTERED_FOREGROUND_NOTES_WERE_FABRICATED::"+name)
                if result.get("foreground_execution_status") != "STRUCTURED_FOREGROUND_AUTHORITY_PRESENT__NOTE_EXECUTION_NOT_COMPILED":
                    raise RuntimeError("FOREGROUND_EXECUTION_STATUS_UNEXPECTED::"+name+"::"+str(result.get("foreground_execution_status")))
                if foreground_registry.get("registered") is not False:
                    raise RuntimeError("UNEXPECTED_FOREGROUND_EXECUTOR_REGISTERED::"+name)
            theory=result["theory_package"]
            if theory.get("legacy_note_generator_used") is not False:
                raise RuntimeError("LEGACY_NOTE_GENERATOR_STILL_USED::"+name)
            authority=theory.get("genre_v3_instrument_authority") or {}
            if authority.get("authority")!="V3_GOVERNED_SOURCE_PATTERN_ROLES":
                raise RuntimeError("SOURCE_ROLE_AUTHORITY_NOT_ACTIVE::"+name)
            expected_template=(
                "v3_developed_composition_candidate"
                if name=="ROCK"
                else "v3_symbolic_source_pattern"
            )
            if theory.get("execution_template")!=expected_template:
                raise RuntimeError(
                    "V3_EXECUTION_TEMPLATE_WRONG::"+name+"::"+
                    str(theory.get("execution_template"))
                )
            if name=="ROCK":
                if theory.get("bars")!=40:
                    raise RuntimeError("ROCK_THEORY_PACKAGE_NOT_40_BARS")
                if len(theory.get("events") or [])!=897:
                    raise RuntimeError("ROCK_THEORY_EVENT_COUNT_NOT_897")
                if theory.get("form")!="ROCK_CORE_V3_40_BAR_DEVELOPED_SYMBOLIC_CANDIDATE":
                    raise RuntimeError("ROCK_THEORY_FORM_ID_WRONG")
                harmony_attacks={}
                for event in theory["events"]:
                    if event.get("track_id")=="HARMONY":
                        harmony_attacks.setdefault(round(float(event["start_beat"]),6),[]).append(event)
                if len(harmony_attacks)!=73:
                    raise RuntimeError("ROCK_RUNTIME_HARMONY_ATTACK_COUNT_NOT_73::"+str(len(harmony_attacks)))
                if min(len(v) for v in harmony_attacks.values())!=3 or max(len(v) for v in harmony_attacks.values())!=3:
                    raise RuntimeError("ROCK_RUNTIME_HARMONY_ATTACK_NOT_THREE_NOTE_VOICING")
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
                "foreground_notes_generated":result.get("foreground_notes_generated"),
                "composition_notes_generated":result.get("composition_notes_generated"),
                "performance_realization_applied":result.get("performance_realization_applied"),
                "composition_executor_registered":bool((result.get("composition_executor_registry_status") or {}).get("registered")),
                "foreground_executor_registered":bool((result.get("foreground_executor_registry_status") or {}).get("registered")),
                "bar_count":theory.get("bars"),
                "execution_template":theory.get("execution_template"),
                "lead_event_count":sum(1 for e in theory["events"] if e.get("track_id")=="LEAD"),
                "rhythm_guitar_attack_count":(
                    len({round(float(e["start_beat"]),6) for e in theory["events"] if e.get("track_id")=="HARMONY"})
                    if name=="ROCK" else 0
                ),
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
        "registered_composition_candidate_count":sum(
            1 for row in rows.values() if row["composition_executor_registered"]
        ),
        "registered_foreground_registry_count":sum(
            1 for row in rows.values() if row["foreground_executor_registered"]
        ),
        "foreground_blocked_source_pattern_count":sum(
            1 for row in rows.values()
            if row["foreground_execution_status"]=="STRUCTURED_FOREGROUND_AUTHORITY_PRESENT__NOTE_EXECUTION_NOT_COMPILED"
        ),
        "rock_developed_composition_candidate_active":(
            rows["ROCK"]["composition_notes_generated"] is True
            and rows["ROCK"]["composition_executor_registered"] is True
            and rows["ROCK"]["bar_count"]==40
            and rows["ROCK"]["event_count"]==897
            and rows["ROCK"]["rhythm_guitar_attack_count"]==73
            and rows["ROCK"]["performance_realization_applied"] is False
            and rows["ROCK"]["finished_composition_authority"] is False
        ),
        "result":(
            "The reconstructed Composer accepted V3-governed symbolic events for "
            "all 40 automatic genres without explicit V3 formations and resolved every "
            "selected event instrument into the current instrument library. The seven "
            "automatic genres with explicit researched V3 formations stop safely before "
            "the generic legacy melody generator. Brush-snare and hand-drum remain "
            "canonical resource-required identities. Rendering remains blocked, and "
            "Rock alone now uses its registered 40-bar developed symbolic composition candidate "
            "(897 events, including vertical rhythm-guitar voicings); the other 39 source-pattern "
            "genres remain accompaniment-only. Rock performance realization is still blocked, and "
            "no source-pattern package has finished-composition authority or rendering permission."
        ),
        "genres":rows,
        "explicit_formation_safe_stops":explicit_rows,
        "next_gate":"ROCK_CORE_PERFORMANCE_REALIZATION_PLAN__OTHER_GENRES_FOREGROUND_EXECUTORS",
    }
    out=ROOT/"genre_contract_v3_research"/"V3_RUNTIME_SYMBOLIC_INSTRUMENT_RESOLUTION_AUDIT.json"
    out.write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps(summary,indent=2))


if __name__=="__main__":
    main()
