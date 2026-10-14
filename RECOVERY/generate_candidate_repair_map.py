#!/usr/bin/env python3
"""Generate a candidate repair overlay map only. Does not write into the Composer."""
import argparse, json, zipfile
from pathlib import Path

PACKAGES=["AI_Composer_FORWARD_REPAIR_SOURCE_AND_TESTS_2026-10-14.zip",
          "Composer_440_432_Repair_Backup_2026-10-12.zip"]

def file_index(root):
    idx={}
    for p in root.rglob("*"):
        if p.is_file():
            idx.setdefault(p.name,[]).append(p.relative_to(root).as_posix())
    return idx

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("working_copy",type=Path)
    ap.add_argument("repair_dir",type=Path)
    ap.add_argument("output",type=Path)
    a=ap.parse_args()
    idx=file_index(a.working_copy)
    candidates=[]; unresolved=[]
    for pkg in PACKAGES:
        p=a.repair_dir/pkg
        if not p.is_file(): raise SystemExit("MISSING_PACKAGE:"+str(p))
        with zipfile.ZipFile(p) as z:
            for info in z.infolist():
                if info.is_dir(): continue
                member=info.filename
                base=Path(member).name
                matches=idx.get(base,[])
                if len(matches)==1:
                    candidates.append({"package":pkg,"member":member,"candidate_target":matches[0],"match_reason":"UNIQUE_BASENAME_ONLY"})
                else:
                    unresolved.append({"package":pkg,"member":member,"basename":base,"candidate_targets":matches})
    doc={"reviewed":False,"forward_only":True,
         "warning":"CANDIDATE ONLY. No overlay may be applied until every row is reviewed against the repair records and intended forward changes.",
         "candidates":candidates,"unresolved":unresolved}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(doc,indent=2)+"\n")
    print(json.dumps({"status":"CANDIDATE_MAP_ONLY","unique_candidates":len(candidates),"unresolved":len(unresolved)},indent=2))
if __name__=="__main__": main()
