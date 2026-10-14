#!/usr/bin/env python3
import argparse, hashlib, json, zipfile
from pathlib import Path

def sha256_file(p,chunk=8*1024*1024):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(chunk),b""): h.update(b)
    return h.hexdigest()

def inspect(p):
    with zipfile.ZipFile(p) as z:
        bad=z.testzip()
        rows=[]
        for i in z.infolist():
            rows.append({"name":i.filename,"bytes":i.file_size,"compressed_bytes":i.compress_size,"crc32":f"{i.CRC:08x}"})
        return {"file":p.name,"bytes":p.stat().st_size,"sha256":sha256_file(p),
                "zip_crc":"PASS" if bad is None else "FAIL:"+bad,"members":len(rows),"entries":rows}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("repair_dir",type=Path)
    ap.add_argument("output",type=Path)
    a=ap.parse_args()
    names=["AI_Composer_FORWARD_REPAIR_SOURCE_AND_TESTS_2026-10-14.zip",
           "Composer_440_432_Repair_Backup_2026-10-12.zip"]
    report={"mode":"READ_ONLY_NO_EXTRACTION_NO_MASTER_MUTATION","packages":[]}
    for n in names:
        p=a.repair_dir/n
        if not p.is_file(): raise SystemExit("MISSING_REPAIR_PACKAGE:"+str(p))
        item=inspect(p)
        if item["zip_crc"]!="PASS": raise SystemExit("REPAIR_ZIP_CRC_FAILED:"+n)
        report["packages"].append(item)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({"status":"PASS","packages":[{"file":x["file"],"members":x["members"],"sha256":x["sha256"]} for x in report["packages"]]},indent=2))

if __name__=="__main__": main()
