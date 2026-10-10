#!/usr/bin/env python3
"""Audit Jazz family source roles and record exact unresolved instrument needs.

No substitution, no live event activation, no edits to original genre formulas.
"""
import json
from pathlib import Path
from genre_styles.source_pattern_library import compile_original_source_seed
from genre_styles.source_pattern_resource_handoff import map_source_roles
JAZZ=("Swing","Jazz Ballad","Big Band","Jazz Waltz","Bebop","Cool Jazz","Dixieland","Jazz Fusion")

def main():
    registry=json.loads(Path("composer/runtime/target_registry.json").read_text())["targets"]["INTERNAL"]["instrument_bindings"]
    rows=[];needs={}
    for genre in JAZZ:
        plan=compile_original_source_seed(genre)
        mapping=map_source_roles(plan,target_bindings=registry)
        blocked=[]
        for role in mapping["roles"]:
            if role["status"]=="EXACT_PROGRAM_REFERENCE_ONLY":continue
            instrument=role["original_instrument_id"]
            blocked.append({"role":role["role"],"instrument":instrument,
                            "status":role["status"],"reason":role.get("reason")})
            needs.setdefault(instrument,[]).append({"genre":genre,"role":role["role"]})
        rows.append({"genre":genre,"total":mapping["roles_total"],
                     "exact_original_source_mappings":mapping["exact_registry_references"],
                     "blocked":blocked})
    report={"schema":"JAZZ_ORIGINAL_SOURCE_GAP_AUDIT_V1","read_only":True,
            "jazz_genres":rows,"unresolved_instrument_types":needs,
            "totals":{"genres":len(rows),"roles":sum(r["total"] for r in rows),
                      "exact":sum(r["exact_original_source_mappings"] for r in rows),
                      "blocked":sum(len(r["blocked"]) for r in rows)}}
    out=Path("jazz-original-source-audit");out.mkdir(exist_ok=True)
    (out/"jazz_original_instrument_gaps.json").write_text(json.dumps(report,indent=2)+"\n")
    print("JAZZ_ORIGINAL_INSTRUMENT_GAPS",json.dumps(report["totals"]),flush=True)
    for iid,occ in sorted(needs.items(),key=lambda x:-len(x[1])):
        print("MISSING_ORIGINAL_JAZZ_INSTRUMENT",iid,len(occ),flush=True)

if __name__=="__main__":main()
