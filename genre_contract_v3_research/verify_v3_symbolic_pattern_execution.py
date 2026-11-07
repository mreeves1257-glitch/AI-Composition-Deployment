"""Audit V3-governed symbolic event execution.

Expected hierarchy:
- controlled genres: not auto-executed here
- Classical: separate V3 structural path
- explicit V3 formation genres: their formation authority supersedes source-role fallback
- 35 automatic genres: symbolic source-pattern execution eligible
- 5 automatic genres: source-role mapping incomplete and must refuse symbolic execution
"""
from __future__ import annotations

from pathlib import Path
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
FORWARD=ROOT/"current_master_forward"
if str(FORWARD) not in sys.path:
    sys.path.insert(0,str(FORWARD))

from genre_contract_v3_execution_bridge import load_master, snapshot_for
from genre_v3_instrument_authority import resolve as resolve_explicit
from genre_v3_source_pattern_bridge import resolve_source_roles
from genre_v3_symbolic_pattern_executor import compile_seed, GenreV3SymbolicExecutionError


def main():
    master=load_master()
    compiled={}
    expected_refusals={}
    skipped={}
    event_total=0

    for name,contract in master["contracts"].items():
        snap=snapshot_for(name)
        policy=snap.get("resolution_policy")
        if policy!="AUTOMATIC_BASELINE_ALLOWED":
            skipped[name]="CONTROLLED_COMPONENT_INPUT"
            continue
        if name=="Classical":
            skipped[name]="SEPARATE_CLASSICAL_V3_STRUCTURAL_PATH"
            continue

        explicit=resolve_explicit(name,snap)
        if explicit.get("status")=="PASS":
            skipped[name]="EXPLICIT_V3_FORMATION_SUPERSEDES_SOURCE_ROLE_FALLBACK"
            continue

        roles=resolve_source_roles(name)
        if roles.get("status")=="PASS":
            result=compile_seed(name)
            if result.get("status")!="PASS":
                raise RuntimeError("SYMBOLIC_EXECUTION_NOT_PASS::"+name)
            if result.get("audio_generated") is not False:
                raise RuntimeError("SYMBOLIC_EXECUTION_AUDIO_ESCALATION::"+name)
            if result.get("live_runtime_authority") is not False:
                raise RuntimeError("SYMBOLIC_EXECUTION_LIVE_ESCALATION::"+name)
            if result.get("musical_audition_approved") is not False:
                raise RuntimeError("SYMBOLIC_EXECUTION_AUDITION_ESCALATION::"+name)
            event_roles={x["role"] for x in result["events"]}
            mapped_roles={x["role"] for x in roles["role_mappings"]}
            if event_roles!=mapped_roles:
                raise RuntimeError("SYMBOLIC_ROLE_COVERAGE_MISMATCH::"+name)
            sections={x["section"] for x in result["events"]}
            if len(sections)!=7:
                raise RuntimeError("SYMBOLIC_SECTION_COVERAGE_MISMATCH::"+name)
            event_total+=result["event_count"]
            compiled[name]={
                "event_count":result["event_count"],
                "meter":result["meter"],
                "tempo_bpm":result["tempo_bpm"],
                "roles":sorted(event_roles),
                "execution_sha256":result["execution_sha256"],
            }
        else:
            try:
                compile_seed(name)
            except GenreV3SymbolicExecutionError as exc:
                if not str(exc).startswith("SOURCE_ROLE_MAPPING_NOT_READY::"):
                    raise
            else:
                raise RuntimeError("INCOMPLETE_SOURCE_ROLE_MAPPING_DID_NOT_REFUSE::"+name)
            expected_refusals[name]=roles.get("unresolved",[])

    expected_refusal_names=set()
    if set(expected_refusals)!=expected_refusal_names:
        raise RuntimeError(
            "SYMBOLIC_REFUSAL_SET_UNEXPECTED::"+
            json.dumps(sorted(expected_refusals))
        )
    if len(compiled)!=40:
        raise RuntimeError("EXPECTED_40_SYMBOLIC_EXECUTABLE_GENRES__GOT_"+str(len(compiled)))
    if len(skipped)!=15:
        raise RuntimeError("EXPECTED_15_HIGHER_AUTHORITY_OR_CONTROLLED_SKIPS__GOT_"+str(len(skipped)))

    summary={
        "status":"PASS",
        "diagnostic_only":True,
        "reasoning_engine_in_test_path":False,
        "audio_generated":False,
        "live_runtime_modified":False,
        "genre_count":55,
        "symbolic_execution_pass_genres":len(compiled),
        "symbolic_execution_refused_genres":len(expected_refusals),
        "higher_authority_or_controlled_skips":len(skipped),
        "total_symbolic_events_compiled":event_total,
        "compiled":compiled,
        "refused":expected_refusals,
        "skipped":skipped,
        "result":(
            "All 40 automatic genres without explicit V3 formations now have a "
            "V3-governed, current-instrument-recognized symbolic event path. Brush-snare "
            "and hand-drum identities are preserved as resource-required canonical roles "
            "rather than unsafe substitutions. Seven explicit V3 formation genres, seven "
            "controlled genres and Classical remain on higher-authority/separate paths."
        ),
        "next_gate":(
            "Bind symbolic execution into the diagnostic Stage-3-to-4 handoff, then "
            "validate form expansion and genre-specific musical behavior before audio."
        ),
    }
    out=ROOT/"genre_contract_v3_research"/"V3_SYMBOLIC_PATTERN_EXECUTION_AUDIT.json"
    out.write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps(summary,indent=2))


if __name__=="__main__":
    main()
