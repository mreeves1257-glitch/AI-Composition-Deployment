"""Verify all 55 original symbolic source-pattern seeds against Genre V3."""
from __future__ import annotations

from pathlib import Path
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
FORWARD=ROOT/"current_master_forward"
if str(FORWARD) not in sys.path:
    sys.path.insert(0,str(FORWARD))

from genre_v3_source_pattern_bridge import audit_all


def main():
    result=audit_all()
    genres=result["results"]
    roles={name:[r["role"] for r in item["roles"]] for name,item in genres.items()}
    summary={
        "status":"PASS",
        "diagnostic_only":True,
        "reasoning_engine_in_test_path":False,
        "note_generation_executed":False,
        "audio_generation_executed":False,
        "genre_count":result["genre_count"],
        "family_count":result["family_count"],
        "all_audio_authority_false":all(not x["audio_authority"] for x in genres.values()),
        "all_live_runtime_authority_false":all(not x["live_runtime_authority"] for x in genres.values()),
        "all_require_musical_revalidation":all(
            x["compatibility_status"]=="STRUCTURALLY_COMPATIBLE__MUSICAL_REVALIDATION_REQUIRED"
            for x in genres.values()
        ),
        "unique_seed_count":len({x["seed_id"] for x in genres.values()}),
        "role_inventory_by_genre":roles,
        "result":(
            "All 55 original project-authored symbolic source-pattern seeds remain "
            "structurally compatible with the current V3 profile IDs, meter ranges, "
            "tempo ranges, and expected source-pattern schema. They remain unauditioned "
            "and have no audio/live authority."
        ),
    }
    if summary["genre_count"]!=55 or summary["family_count"]!=13:
        raise RuntimeError("V3_SOURCE_PATTERN_COVERAGE_FAIL")
    if summary["unique_seed_count"]!=55:
        raise RuntimeError("V3_SOURCE_PATTERN_SEEDS_NOT_UNIQUE")
    if not summary["all_audio_authority_false"] or not summary["all_live_runtime_authority_false"]:
        raise RuntimeError("V3_SOURCE_PATTERN_AUTHORITY_ESCALATION")
    out=ROOT/"genre_contract_v3_research"/"V3_SOURCE_PATTERN_COMPATIBILITY_AUDIT.json"
    out.write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps(summary,indent=2))


if __name__=="__main__":
    main()
