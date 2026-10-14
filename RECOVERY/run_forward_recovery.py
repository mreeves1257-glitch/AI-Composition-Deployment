#!/usr/bin/env python3
"""Forward-only AI Composer recovery orchestrator.
Never edits source chunks or existing masters. Every build happens in a new output tree.
This script intentionally stops before overlay if the repair-map file has not been reviewed.
"""
import argparse, json, shutil, subprocess, sys, zipfile
from pathlib import Path

BASE="AI_Composer_PRODUCTION_MASTER_55_GENRES_FORWARD_2026-10-12.zip"
R1="AI_Composer_FORWARD_REPAIR_SOURCE_AND_TESTS_2026-10-14.zip"
R2="Composer_440_432_Repair_Backup_2026-10-12.zip"

def run(*cmd):
    print("+"," ".join(map(str,cmd)),flush=True)
    subprocess.run([str(x) for x in cmd],check=True)

def extract_clean(src,dst):
    if dst.exists(): shutil.rmtree(dst)
    dst.mkdir(parents=True)
    with zipfile.ZipFile(src) as z:
        bad=z.testzip()
        if bad is not None: raise SystemExit("CRC_FAIL:"+bad)
        z.extractall(dst)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--production-parts",type=Path,required=True)
    ap.add_argument("--resource-artifacts",type=Path,required=True)
    ap.add_argument("--repair-dir",type=Path,required=True)
    ap.add_argument("--work",type=Path,required=True)
    ap.add_argument("--repair-map",type=Path,required=True,
                    help="Reviewed JSON mapping of repair-package members to target paths. Must explicitly approve every overlay.")
    a=ap.parse_args()
    root=Path(__file__).resolve().parent
    a.work.mkdir(parents=True,exist_ok=True)

    # 1. Verify/reassemble production source.
    run(sys.executable,root/"reassemble_production_master.py",a.production_parts,a.work/"production")
    production=a.work/"production"/BASE

    # 2. Recover and independently verify replacement libraries.
    run(sys.executable,root/"recover_replacement_resources.py",a.resource_artifacts,a.work/"resources")

    # 3. Audit repair packages before applying anything.
    run(sys.executable,root/"audit_repair_packages.py",a.repair_dir,a.work/"repair_audit.json")

    # 4. Create isolated working extraction. Never mutate production ZIP.
    isolated=a.work/"isolated_forward_working_copy"
    extract_clean(production,isolated)

    # 5. Apply only an explicitly reviewed repair map.
    mapping=json.loads(a.repair_map.read_text())
    if mapping.get("reviewed") is not True or mapping.get("forward_only") is not True:
        raise SystemExit("REPAIR_MAP_NOT_REVIEWED")
    packages={R1:a.repair_dir/R1,R2:a.repair_dir/R2}
    applied=[]
    for row in mapping.get("overlays",[]):
        pkg=row["package"]; member=row["member"]; target=row["target"]
        if pkg not in packages: raise SystemExit("UNKNOWN_REPAIR_PACKAGE:"+pkg)
        if Path(target).is_absolute() or ".." in Path(target).parts: raise SystemExit("UNSAFE_TARGET:"+target)
        with zipfile.ZipFile(packages[pkg]) as z:
            if member not in z.namelist(): raise SystemExit("MISSING_REPAIR_MEMBER:"+member)
            dest=isolated/target; dest.parent.mkdir(parents=True,exist_ok=True)
            with z.open(member) as r, dest.open("wb") as w: shutil.copyfileobj(r,w,1024*1024)
        applied.append({"package":pkg,"member":member,"target":target})
    (a.work/"APPLIED_REPAIR_MAP.json").write_text(json.dumps({"applied":applied},indent=2)+"\n")

    print(json.dumps({
      "status":"OVERLAYS_APPLIED_TO_ISOLATED_COPY",
      "source_master_unchanged":True,
      "next_required_gate":"RUN_PROJECT_TESTS_AND_55_GENRE_AUDIO_VERIFICATION_BEFORE_PACKAGING",
      "working_copy":str(isolated)
    },indent=2))

if __name__=="__main__": main()
