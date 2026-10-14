#!/usr/bin/env python3
"""Package a new forward Composer master only after all gates pass."""
import argparse, hashlib, json, zipfile
from pathlib import Path

def sha256_file(p,chunk=8*1024*1024):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(chunk),b""): h.update(b)
    return h.hexdigest()

def require(path, predicate, label):
    if not path.is_file(): raise SystemExit("MISSING_GATE:"+label+":"+str(path))
    data=json.loads(path.read_text())
    if not predicate(data): raise SystemExit("GATE_FAILED:"+label)
    return data

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("working_copy",type=Path)
    ap.add_argument("verification_dir",type=Path)
    ap.add_argument("output_dir",type=Path)
    ap.add_argument("--name",default="AI_Composer_FORWARD_MASTER_55_GENRES_440_432_TUNING_2026-10-14_R3.zip")
    a=ap.parse_args()
    root=a.working_copy.resolve(); v=a.verification_dir.resolve()
    require(v/"FORWARD_FUNCTIONAL_VERIFICATION.json",
        lambda d:d.get("genre_count")==55 and len(d.get("tuning",{}).get("440",[]))==55
        and len(d.get("tuning",{}).get("432",[]))==55,"55_GENRES_440_432")
    require(v/"REGRESSION_VERIFICATION.json",
        lambda d:d.get("status")=="PASS" and d.get("classical",{}).get("tests_run")==43
        and d.get("classical",{}).get("status")=="PASS","CLASSICAL_43_AND_REGRESSIONS")
    applied=require(v/"APPLIED_REPAIR_MAP.json",
        lambda d:isinstance(d.get("applied"),list) and len(d["applied"])>0,"REPAIR_OVERLAYS")
    a.output_dir.mkdir(parents=True,exist_ok=True)
    certification={
      "status":"PASS",
      "master_policy":"Forward-only; built from isolated verified production source; no prior master modified.",
      "genre_count":55,
      "finished_audio_440":55,
      "finished_audio_432":55,
      "classical_regression_tests":43,
      "repair_overlays":len(applied["applied"]),
      "source_working_copy":str(root),
      "note":"Shinyguitar and Big Rusty Drums are replacement libraries used in this forward lineage, not the lost original Composer instrument resources."
    }
    cert=root/"FORWARD_MASTER_CERTIFICATION_2026-10-14.json"
    cert.write_text(json.dumps(certification,indent=2)+"\n")
    out=a.output_dir/a.name
    files=sorted(p for p in root.rglob("*") if p.is_file())
    with zipfile.ZipFile(out,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
        for p in files: z.write(p,p.relative_to(root).as_posix())
    with zipfile.ZipFile(out) as z:
        bad=z.testzip(); members=len(z.infolist())
        if bad is not None: raise SystemExit("PACKAGED_ZIP_CRC_FAILED:"+bad)
    report={"status":"PASS","filename":out.name,"bytes":out.stat().st_size,
            "sha256":sha256_file(out),"members":members,"genre_count":55,
            "classical_tests":43,"zip_crc":"PASS","prior_masters_modified":False}
    (a.output_dir/(out.name+"_VERIFICATION.json")).write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
if __name__=="__main__": main()
