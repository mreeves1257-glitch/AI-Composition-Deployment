#!/usr/bin/env python3
"""Audit all genre-owned source roles against actual installed recorded-source IDs.

Read-only: does not activate candidates, change any genre, or synthesize replacements.
"""
import json
from collections import Counter
from pathlib import Path
from genre_styles.shared_interpreter_router import connect_all_genres
from genre_styles.source_pattern_library import compile_original_source_seed
from genre_styles.source_pattern_resource_handoff import map_source_roles

def main():
    registry=json.loads(Path("composer/runtime/target_registry.json").read_text())["targets"]["INTERNAL"]["instrument_bindings"]
    genres=connect_all_genres()
    report={"schema":"AI_COMP_55_GENRE_RECORDED_SOURCE_AUDIT_V1",
            "diagnostic_only":True,"live_audio_authorized":False,"genres":[]}
    status_count=Counter()
    for genre in genres:
        plan=compile_original_source_seed(genre)
        result=map_source_roles(plan,target_bindings=registry)
        statuses=Counter(r["status"] for r in result["roles"])
        status_count.update(statuses)
        report["genres"].append({
            "genre":genre,"roles_total":result["roles_total"],
            "exact_original_programs":result["exact_registry_references"],
            "blocked_roles":result["unresolved_roles"],
            "roles":[{"role":r["role"],"instrument":r["original_instrument_id"],
                      "status":r["status"],"binding_id":r.get("binding_id"),
                      "reason":r.get("reason")} for r in result["roles"]]})
    report["totals"]={"genres":len(genres),"roles":sum(g["roles_total"] for g in report["genres"]),
                      "status_counts":dict(sorted(status_count.items()))}
    if report["totals"]["genres"]!=55 or report["totals"]["roles"]!=234:
        raise RuntimeError("GENRE_SOURCE_INVENTORY_DRIFT")
    path=Path("rock-diagnostic-audio/ALL_55_GENRES_RECORDED_SOURCE_AUDIT.json")
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,indent=2)+"\n")
    print("ALL_55_GENRE_SOURCE_AUDIT",json.dumps(report["totals"]),flush=True)

if __name__=="__main__":main()
