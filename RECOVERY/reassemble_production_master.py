#!/usr/bin/env python3
import argparse, hashlib, json, zipfile
from pathlib import Path

SEGMENTS = [
("AI_Composer_FORWARD_WORKING_MASTER_55_GENRES_GENRE_PREGEN_HARD_COPY_2026-10-12.zip.001",367001600,"e2da268db837110ebbe9f0bc7b1c50f7eba06e4d446fe1e7cbe6f5f516a65d11"),
("AI_Composer_FORWARD_WORKING_MASTER_55_GENRES_GENRE_PREGEN_HARD_COPY_2026-10-12.zip.002",367001600,"9d02893797e36ae77cab15edad53aebee6502d58d540a5b0b18e1a2ecf1e0c8a"),
("AI_Composer_FORWARD_WORKING_MASTER_55_GENRES_GENRE_PREGEN_HARD_COPY_2026-10-12.zip.003",367001600,"334a214b033d0e42617601a094fb682349045be73d2c5ae3a680b3efe91c41b3"),
("AI_Composer_FORWARD_WORKING_MASTER_55_GENRES_GENRE_PREGEN_HARD_COPY_2026-10-12.zip.004",367001600,"de10b20e9cc18b421198bfa7518f0d5af42eaf650a6f76cfd49f4c056907b256"),
("AI_Composer_FORWARD_WORKING_MASTER_55_GENRES_GENRE_PREGEN_HARD_COPY_2026-10-12.zip.005",367001600,"ad5ea4cf58b4a71c345c7892c06b1eced232ded9d1473b963a89ff0dece26f9b"),
("AI_Composer_FORWARD_WORKING_MASTER_55_GENRES_GENRE_PREGEN_HARD_COPY_2026-10-12.zip.006",367001600,"597f9d142bdbad2a508e17882d84235f6ee317952451b0ec25fa22349397fa77"),
("AI_Composer_PRODUCTION_MASTER_55_GENRES_FORWARD_2026-10-12.zip.007",367001600,"8f9b0e17ff7b61ac3933293d94061ef9f2c6f42b6584051ccb305761ed22791f"),
("AI_Composer_PRODUCTION_MASTER_55_GENRES_FORWARD_2026-10-12.zip.008",367001600,"6b0646b3e945d152e5da7ee7dc221e44a8a79ca1ebce3d128cb6ad545a2a340f"),
("AI_Composer_PRODUCTION_MASTER_55_GENRES_FORWARD_2026-10-12.zip.009",367001600,"a97026d38778581a2c4570dcdadccfa30e78000a131e9a4846c0965dcba0bb16"),
("AI_Composer_PRODUCTION_MASTER_55_GENRES_FORWARD_2026-10-12.zip.010",176895962,"f0d47ef45913b32bcc19d020f4b6ed9ca4ee7bb4ea8aa6e8ecbf1043ff6d2055"),
]
TARGET="AI_Composer_PRODUCTION_MASTER_55_GENRES_FORWARD_2026-10-12.zip"
TARGET_BYTES=3479910362
TARGET_SHA="de328c5ee8de22b80771e7d6dc9c7391263f449e8a7183ed6d48433e527e961d"

def sha256_file(p,chunk=8*1024*1024):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(chunk),b""): h.update(b)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("parts_dir",type=Path)
    ap.add_argument("output_dir",type=Path)
    args=ap.parse_args()
    args.output_dir.mkdir(parents=True,exist_ok=True)
    report={"segments":[]}
    for name,size,sha in SEGMENTS:
        p=args.parts_dir/name
        if not p.is_file(): raise SystemExit("MISSING_SEGMENT:"+str(p))
        actual_size=p.stat().st_size
        actual_sha=sha256_file(p)
        ok=actual_size==size and actual_sha==sha
        report["segments"].append({"name":name,"bytes":actual_size,"sha256":actual_sha,"ok":ok})
        if not ok: raise SystemExit("SEGMENT_VERIFY_FAILED:"+name)
    out=args.output_dir/TARGET
    with out.open("wb") as w:
        for name,_,_ in SEGMENTS:
            with (args.parts_dir/name).open("rb") as r:
                for b in iter(lambda:r.read(8*1024*1024),b""): w.write(b)
    if out.stat().st_size!=TARGET_BYTES: raise SystemExit("FULL_SIZE_MISMATCH")
    full_sha=sha256_file(out)
    if full_sha!=TARGET_SHA: raise SystemExit("FULL_SHA256_MISMATCH")
    with zipfile.ZipFile(out) as z:
        bad=z.testzip()
        report["zip_members"]=len(z.infolist())
        report["zip_crc"]="PASS" if bad is None else "FAIL:"+bad
        if bad is not None: raise SystemExit("ZIP_CRC_FAILED:"+bad)
    report.update({"archive":str(out),"archive_bytes":out.stat().st_size,"archive_sha256":full_sha,"status":"PASS"})
    (args.output_dir/"PRODUCTION_MASTER_REASSEMBLY_VERIFICATION.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))

if __name__=="__main__": main()
