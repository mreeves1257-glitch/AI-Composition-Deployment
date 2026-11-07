"""No-audio Rock V3 target-resource context preflight.

Proves that the reconstructed Composer preserves one canonical electric-guitar
instrument identity while routing HARMONY and LEAD through distinct target
resource contexts.

No rendering is permitted by this test.
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
from target_program import TargetProgram
from production_resource_resolver import resolve_bindings


def main():
    with tempfile.TemporaryDirectory() as tmp:
        engine=AICompositionEngine(history_path=Path(tmp)/"history.json")
        result=engine.run("ROCK",mode="quick",audio_backend="PRESERVED")

    if result.get("status")!="V3_SYMBOLIC_INSTRUMENT_RESOLUTION_PASS":
        raise RuntimeError("ROCK_V3_RUNTIME_NOT_AT_SYMBOLIC_RESOLUTION_PASS")
    if result.get("foreground_notes_generated") is not True:
        raise RuntimeError("ROCK_V3_FOREGROUND_NOT_PRESENT")
    if result.get("finished_composition_authority") is not False:
        raise RuntimeError("ROCK_V3_FINISHED_COMPOSITION_AUTHORITY_ESCALATED")
    if result.get("audio_rendered") is not False:
        raise RuntimeError("ROCK_V3_AUDIO_RENDERED_DURING_RESOURCE_PREFLIGHT")

    package=result.get("instrument_package") or {}
    requests=package.get("source_requests") or []
    role_rows=[
        {
            "track_id":r.get("track_id"),
            "instrument_id":r.get("instrument_id"),
            "source_instrument_id":r.get("source_instrument_id"),
            "role":r.get("role"),
            "articulations":r.get("articulations"),
        }
        for r in requests
    ]

    guitar_roles={
        r.get("role")
        for r in requests
        if r.get("instrument_id")=="electric_guitar"
    }
    if guitar_roles!={"RHYTHM_POWER_CHORDS","LEAD_MELODY"}:
        raise RuntimeError(
            "ROCK_GUITAR_CONTEXT_ROLES_WRONG::"+
            json.dumps(sorted(x for x in guitar_roles if x))
        )

    target=TargetProgram(RUNTIME/"target_registry.json")
    resolved=target.resolve("INTERNAL",package)
    if resolved.get("status")!="PASS":
        raise RuntimeError(
            "ROCK_TARGET_RESOURCE_RESOLUTION_FAIL::"+
            json.dumps(resolved.get("missing",[]),sort_keys=True)
        )
    if resolved.get("render_allowed") is not False:
        raise RuntimeError("ROCK_RESOURCE_PREFLIGHT_GRANTED_RENDER_PERMISSION")
    if resolved.get("audio_backend_verified") is not False:
        raise RuntimeError("ROCK_RESOURCE_PREFLIGHT_CLAIMED_AUDIO_VERIFICATION")

    resources=resolved.get("resolved_resources") or []
    by_track={str(x.get("track_id")):x for x in resources}
    for track in ("HARMONY","LEAD","BASS","KICK","SNARE","HAT"):
        if track not in by_track:
            raise RuntimeError("ROCK_TARGET_RESOURCE_TRACK_MISSING::"+track)

    rhythm=by_track["HARMONY"]["resource"]
    lead=by_track["LEAD"]["resource"]
    if rhythm.get("resource_id")!="KARORYFER_SHINYGUITAR":
        raise RuntimeError("ROCK_RHYTHM_GUITAR_NOT_SHINYGUITAR")
    if lead.get("resource_id")!="KARORYFER_SHINYGUITAR":
        raise RuntimeError("ROCK_LEAD_GUITAR_NOT_SHINYGUITAR")
    if rhythm.get("preferred_mapping")!="Programs/composer_electric.sfz":
        raise RuntimeError("ROCK_RHYTHM_GUITAR_MAPPING_CHANGED")
    if lead.get("preferred_mapping")!="Programs/composer_electric.sfz":
        raise RuntimeError("ROCK_LEAD_GUITAR_MAPPING_CHANGED")
    if rhythm.get("target_gain_db")!=-5:
        raise RuntimeError("ROCK_RHYTHM_GUITAR_CONTEXT_GAIN_CHANGED")
    if lead.get("target_gain_db")!=-6:
        raise RuntimeError("ROCK_LEAD_GUITAR_CONTEXT_GAIN_CHANGED")
    if rhythm.get("fallback_policy")!="NO_SYNTHETIC_SUBSTITUTION":
        raise RuntimeError("ROCK_RHYTHM_GUITAR_FALLBACK_POLICY_CHANGED")
    if lead.get("fallback_policy")!="NO_SYNTHETIC_SUBSTITUTION":
        raise RuntimeError("ROCK_LEAD_GUITAR_FALLBACK_POLICY_CHANGED")

    expected_resources={
        "BASS":"KARORYFER_GROWLYBASS_V1_002",
        "KICK":"KARORYFER_BIG_RUSTY_DRUMS",
        "SNARE":"KARORYFER_BIG_RUSTY_DRUMS",
        "HAT":"KARORYFER_BIG_RUSTY_DRUMS",
    }
    for track,resource_id in expected_resources.items():
        if by_track[track]["resource"].get("resource_id")!=resource_id:
            raise RuntimeError("ROCK_RESOURCE_ID_CHANGED::"+track)

    # File-presence proof only. This does not render or certify musical fidelity.
    disk=resolve_bindings(RUNTIME)
    keys=(
        "electric_guitar:RHYTHM_POWER_CHORDS",
        "electric_guitar:LEAD_MELODY",
        "electric_bass_guitar",
        "kick_drum_rock",
        "snare_drum",
        "hi_hat",
    )
    presence={key:disk.get(key) for key in keys}
    missing_files={
        key:value for key,value in presence.items()
        if not value or value.get("status")!="MAPPING_FOUND"
    }
    if missing_files:
        raise RuntimeError(
            "ROCK_RESOURCE_MAPPING_FILE_MISSING::"+
            json.dumps(missing_files,sort_keys=True)
        )

    summary={
        "status":"PASS",
        "diagnostic_only":True,
        "genre":"ROCK",
        "audio_rendered":False,
        "render_allowed":False,
        "live_runtime_promoted":False,
        "foreground_notes_generated":True,
        "finished_composition_authority":False,
        "instrument_source_requests":role_rows,
        "guitar_contexts":{
            "HARMONY":{
                "instrument_id":"electric_guitar",
                "role":"RHYTHM_POWER_CHORDS",
                "resource_id":rhythm["resource_id"],
                "preferred_mapping":rhythm["preferred_mapping"],
                "target_gain_db":rhythm["target_gain_db"],
                "fallback_policy":rhythm["fallback_policy"],
            },
            "LEAD":{
                "instrument_id":"electric_guitar",
                "role":"LEAD_MELODY",
                "resource_id":lead["resource_id"],
                "preferred_mapping":lead["preferred_mapping"],
                "target_gain_db":lead["target_gain_db"],
                "fallback_policy":lead["fallback_policy"],
            },
        },
        "resource_mapping_file_presence":presence,
        "result":(
            "Rock rhythm and lead guitar retain one canonical electric_guitar identity "
            "but resolve through distinct RHYTHM_POWER_CHORDS and LEAD_MELODY target "
            "contexts, both pinned to Karoryfer Shinyguitar with no synthetic fallback. "
            "Bass and drum roles retain their pinned real-sample resources."
        ),
        "next_gate":"ROCK_VARIANT_AND_FORM_EXPANSION_BEFORE_ANY_AUDIO",
    }
    out=ROOT/"genre_contract_v3_research"/"ROCK_V3_TARGET_RESOURCE_CONTEXT_AUDIT.json"
    out.write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps(summary,indent=2))


if __name__=="__main__":
    main()
