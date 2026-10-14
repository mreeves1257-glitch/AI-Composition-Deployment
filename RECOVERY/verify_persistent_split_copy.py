#!/usr/bin/env python3
"""Verify a materialized persistent split-master copy reproduces the exact master hash."""
import argparse, hashlib, json
from pathlib import Path

def sha256_file(p,chunk=8*1024*1024):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(chunk),b""): h.update(b)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("manifest",type=Path)
    ap.add_argument("parts_dir",type=Path)
    ap.add_argument("output",type=Path)
    a=ap.parse_args()
    m=json.loads(a.manifest.read_text())
    expected_sha=m["archive_sha256"]; expected_bytes=m["archive_bytes"]
    full=hashlib.sha256(); total=0; checks=[]
    for row in sorted(m["parts"],key=lambda x:x["sequence"]):
        p=a.parts_dir/row["name"]
        if not p.is_file(): raise SystemExit("MISSING_SAVED_PART:"+str(p))
        size=p.stat().st_size; sha=sha256_file(p)
        if size!=row["bytes"] or sha!=row["sha256"]:
            raise SystemExit("SAVED_PART_MISMATCH:"+p.name)
        with p.open("rb") as f:
            for b in iter(lambda:f.read(8*1024*1024),b""):
                full.update(b); total+=len(b)
        checks.append({"name":p.name,"bytes":size,"sha256":sha,"status":"PASS"})
    actual_sha=full.hexdigest()
    if total!=expected_bytes or actual_sha!=expected_sha:
        raise SystemExit("PERSISTENT_REASSEMBLY_MISMATCH")
    report={"status":"PASS","persistent_copy_reassembly":"PASS",
            "archive_bytes":total,"archive_sha256":actual_sha,"parts":checks}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({"status":"PASS","bytes":total,"sha256":actual_sha,"parts":len(checks)},indent=2))
if __name__=="__main__": main()
