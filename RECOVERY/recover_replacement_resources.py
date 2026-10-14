#!/usr/bin/env python3
import argparse, hashlib, json, shutil, zipfile
from pathlib import Path

SHINY=("Karoryfer.Shinyguitar.v1.002.zip",368411844,"23cf4030cbf9ce9e2c84d7cbb1c022fbca124bfff0ad118a14eda7cf6c921d7b")
RUSTY=("Big_Rusty_Drums_1100.zip",619600370,"d4a9990acd19376d91ce446dae415c81428728b5adebb6a88eddbb3a6aac8744")

def sha256_file(p,chunk=8*1024*1024):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(chunk),b""): h.update(b)
    return h.hexdigest()

def extract_named(artifact,target_name,out):
    with zipfile.ZipFile(artifact) as z:
        matches=[n for n in z.namelist() if Path(n).name==target_name]
        if len(matches)!=1: raise SystemExit(f"EXPECTED_ONE:{artifact}:{target_name}:{matches}")
        with z.open(matches[0]) as r, out.open("wb") as w: shutil.copyfileobj(r,w,1024*1024)

def extract_bin(artifact,out):
    with zipfile.ZipFile(artifact) as z:
        matches=[n for n in z.namelist() if n.endswith(".bin")]
        if len(matches)!=1: raise SystemExit(f"EXPECTED_ONE_BIN:{artifact}:{matches}")
        with z.open(matches[0]) as r, out.open("wb") as w: shutil.copyfileobj(r,w,1024*1024)

def verify_zip(p,expected_bytes,expected_sha):
    if p.stat().st_size!=expected_bytes: raise SystemExit("SIZE_MISMATCH:"+str(p))
    sha=sha256_file(p)
    if sha!=expected_sha: raise SystemExit("SHA_MISMATCH:"+str(p))
    with zipfile.ZipFile(p) as z:
        bad=z.testzip()
        if bad is not None: raise SystemExit("CRC_FAIL:"+str(p)+":"+bad)
        return {"file":str(p),"bytes":p.stat().st_size,"sha256":sha,"members":len(z.infolist()),"crc":"PASS"}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("artifacts_dir",type=Path)
    ap.add_argument("output_dir",type=Path)
    a=ap.parse_args(); a.output_dir.mkdir(parents=True,exist_ok=True)

    shiny=a.output_dir/SHINY[0]
    extract_named(a.artifacts_dir/"Shinyguitar_recovery_artifact.zip",SHINY[0],shiny)

    parts=[]
    for i in range(3):
        p=a.output_dir/f"Big_Rusty_Drums_1100.zip.part.{i:03d}.bin"
        extract_bin(a.artifacts_dir/f"Big_Rusty_part_{i:03d}_artifact.zip",p)
        parts.append(p)
    rusty=a.output_dir/RUSTY[0]
    with rusty.open("wb") as w:
        for p in parts:
            with p.open("rb") as r:
                for b in iter(lambda:r.read(8*1024*1024),b""): w.write(b)

    report={
      "clarification":"These are manufacturer-original release ZIPs used as replacement libraries in the Composer; they are not the lost original Composer instrument resources.",
      "shinyguitar":verify_zip(shiny,SHINY[1],SHINY[2]),
      "big_rusty_drums":verify_zip(rusty,RUSTY[1],RUSTY[2]),
      "status":"PASS"
    }
    (a.output_dir/"REPLACEMENT_RESOURCE_RECOVERY_VERIFICATION.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))

if __name__=="__main__": main()
