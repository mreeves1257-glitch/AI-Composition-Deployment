#!/usr/bin/env python3
import argparse, hashlib, json
from pathlib import Path

def sha256_file(p,chunk=8*1024*1024):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(chunk),b""): h.update(b)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("archive",type=Path)
    ap.add_argument("output_dir",type=Path)
    ap.add_argument("--chunk-bytes",type=int,default=350*1024*1024)
    a=ap.parse_args()
    if not a.archive.is_file(): raise SystemExit("ARCHIVE_NOT_FOUND")
    if a.chunk_bytes >= 512*1024*1024: raise SystemExit("CHUNK_SIZE_MUST_BE_BELOW_512_MIB")
    a.output_dir.mkdir(parents=True,exist_ok=True)
    full_sha=sha256_file(a.archive)
    parts=[]
    with a.archive.open("rb") as r:
        seq=1
        while True:
            data=r.read(a.chunk_bytes)
            if not data: break
            p=a.output_dir/f"{a.archive.name}.{seq:03d}"
            p.write_bytes(data)
            parts.append({"sequence":seq,"name":p.name,"bytes":p.stat().st_size,"sha256":sha256_file(p)})
            seq+=1
    recon=hashlib.sha256()
    total=0
    for x in parts:
        p=a.output_dir/x["name"]
        with p.open("rb") as f:
            for b in iter(lambda:f.read(8*1024*1024),b""):
                recon.update(b); total+=len(b)
    if recon.hexdigest()!=full_sha or total!=a.archive.stat().st_size:
        raise SystemExit("SPLIT_REASSEMBLY_VERIFY_FAILED")
    manifest={"format":"AI_COMPOSER_FORWARD_MASTER_SPLIT_V1","source_archive":a.archive.name,
              "archive_bytes":a.archive.stat().st_size,"archive_sha256":full_sha,
              "chunk_bytes":a.chunk_bytes,"parts":parts,"reassembly_verification":"PASS"}
    (a.output_dir/(a.archive.name+"_SPLIT_MANIFEST.json")).write_text(json.dumps(manifest,indent=2)+"\n")
    print(json.dumps({"status":"PASS","parts":len(parts),"archive_sha256":full_sha},indent=2))

if __name__=="__main__": main()
