"""Read-only diagnosis: why CREATE NEW MUSIC may repeat the same score.

Unpacks the project's original runtime, prints the seed/history call path, and
compares Rock compositions at distinct deterministic creation seeds.
No renderer, web request, song deployment, or production mutation occurs.
"""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"research"))
from verify_composer_to_midi_wiring_step01_20261009 import extract_original_runtime

def relevant_source(root,filename,terms,context=2):
    p=root/filename
    if not p.is_file():
        print("MISSING",filename);return
    lines=p.read_text().splitlines()
    seen=set()
    for i,line in enumerate(lines):
        if any(t in line for t in terms):
            for j in range(max(0,i-context),min(len(lines),i+context+1)):
                seen.add(j)
    print("ORIGINAL_SOURCE",filename,"MATCHES",len(seen))
    for i in sorted(seen)[:185]:
        print(f"{filename}:{i+1}: {lines[i][:200]}")

def checksum(result):
    notes=result.get("events",[])
    fields=[
      {k:n.get(k) for k in ("track_id","instrument_id","midi","start_beat",
                            "duration_beats","velocity","articulation")}
      for n in notes]
    return hashlib.sha256(json.dumps(fields,sort_keys=True,default=str).encode()).hexdigest()

def main():
    with tempfile.TemporaryDirectory(prefix="original-composer-seed-check-") as td:
        target=Path(td)
        extract_original_runtime(target)
        relevant_source(target,"engine.py",
                        ("creation_seed","history","def run(","get_creation","fingerprint"))
        relevant_source(target,"input_gateway.py",
                        ("compose_request","result=AICompositionEngine","request_id","creation_seed"))
        relevant_source(target,
                        "AI_Comp_Genre_Execution_Adapter_002_WORKING_2026-10-02_184019_CDT.py",
                        ("creation_seed","def resolve(","def generate_events("),0)
        sys.path.insert(0,str(target))
        src=target/"AI_Comp_Genre_Execution_Adapter_002_WORKING_2026-10-02_184019_CDT.py"
        spec=importlib.util.spec_from_file_location("original_reproducibility_adapter",src)
        a=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(a)
        records=[]
        for seed in (0,0,1,2):
            result=a.GenreExecutionAdapter().resolve("ROCK",mode="normal",creation_seed=seed)
            assert result["status"]=="PASS",str(result.get("status"))
            rec={
                "seed":seed,"events":len(result["events"]),
                "score_sha256":checksum(result),
                "tempo":result.get("tempo_bpm"),
                "bars":result.get("bars"),
                "theory_request":{k:result.get("theory_request",{}).get(k)
                     for k in ("tonic","mode","bars","roman_progression")}
            }
            records.append(rec)
        same=records[0]["score_sha256"]==records[1]["score_sha256"]
        difference=records[0]["score_sha256"]!=records[2]["score_sha256"]
        print("SEED_COMPARISON",json.dumps({
          "same_seed_repeats_exact_score":same,
          "different_seeds_change_score":difference,
          "records":records
        },sort_keys=True))
        assert same,"SAME_SEED_NONDETERMINISTIC_UNEXPECTED"
        assert difference,"DIFFERENT_SEEDS_DID_NOT_CHANGE_SONG"
if __name__=="__main__":
    main()
