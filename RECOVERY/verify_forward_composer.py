#!/usr/bin/env python3
"""Final forward-master functional verification. Run only on isolated rebuilt copy."""
import argparse, hashlib, importlib, json, os, sys, tempfile, wave
from pathlib import Path

def sha256_file(p,chunk=8*1024*1024):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(chunk),b""): h.update(b)
    return h.hexdigest()

def wav_check(p):
    p=Path(p)
    if not p.is_file(): raise AssertionError("WAV_MISSING:"+str(p))
    with wave.open(str(p),"rb") as w:
        frames=w.getnframes(); channels=w.getnchannels(); rate=w.getframerate(); width=w.getsampwidth()
        data=w.readframes(frames)
    if frames<=0 or channels not in (1,2) or rate<=0 or width<=0 or not any(data):
        raise AssertionError("WAV_INVALID_OR_SILENT:"+str(p))
    return {"path":str(p),"frames":frames,"channels":channels,"rate":rate,"sample_width":width,"sha256":sha256_file(p)}

def locate_registry(root):
    names=[
      "AI_Comp_Genre_Performance_Registry_002_WORKING_COMPLETE_2026-10-02_182810_CDT.json",
      "AI_Comp_Genre_Performance_Registry.json"
    ]
    for name in names:
        hits=list(root.rglob(name))
        if hits: return hits[0]
    hits=[p for p in root.rglob("*.json") if "Genre_Performance_Registry" in p.name]
    if not hits: raise SystemExit("GENRE_REGISTRY_NOT_FOUND")
    return hits[0]

def locate_runtime(root):
    hits=[p.parent for p in root.rglob("engine.py") if (p.parent/"output_handoff.py").is_file()]
    if not hits: raise SystemExit("RUNTIME_NOT_FOUND")
    return hits[0]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("working_copy",type=Path)
    ap.add_argument("output",type=Path)
    a=ap.parse_args()
    root=a.working_copy.resolve()
    runtime=locate_runtime(root)
    sys.path.insert(0,str(runtime))
    registry=locate_registry(root)
    profiles=json.loads(registry.read_text())["profiles"]
    if len(profiles)!=55: raise SystemExit(f"GENRE_COUNT_MISMATCH:{len(profiles)}")
    from engine import AICompositionEngine
    import output_handoff
    report={"genre_count":55,"registry":str(registry),"runtime":str(runtime),"tuning":{"440":[],"432":[]},"classical":{}}
    with tempfile.TemporaryDirectory() as tmp:
        tmp=Path(tmp)
        output_handoff.OUT=tmp/"outputs"
        engine=AICompositionEngine(history_path=tmp/"history.json")
        for tuning in (440,432):
            key=str(tuning)
            for genre in profiles:
                result=engine.run(genre,mode="quick",analyze_audio=False,tuning_reference_hz=tuning)
                if not result.get("audio_rendered"):
                    raise SystemExit(f"GENRE_RENDER_FAILED:{genre}:{tuning}:{result.get('reason')}")
                wav_path=result.get("audio_render",{}).get("wav_path")
                if not wav_path: raise SystemExit(f"WAV_PATH_MISSING:{genre}:{tuning}")
                report["tuning"][key].append({"genre":genre,"wav":wav_check(wav_path),
                    "reported_tuning":result.get("tuning_reference_hz")})
                if float(result.get("tuning_reference_hz",0))!=float(tuning):
                    raise SystemExit(f"TUNING_REPORT_MISMATCH:{genre}:{tuning}")
    # Classical is counted separately from the 55 genres.
    classical_tests=[p for p in root.rglob("test_*.py") if "classical" in p.name.lower()]
    report["classical"]["test_files"]=[str(p.relative_to(root)) for p in classical_tests]
    report["classical"]["expected_regression_count"]=43
    report["classical"]["status"]="REQUIRES_TEST_RUNNER_GATE"
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({"status":"55_GENRES_440_432_AUDIO_PASS","genres":55,
                      "renders":110,"classical_test_files":len(classical_tests),
                      "next_gate":"RUN_CLASSICAL_43_AND_FULL_PROJECT_REGRESSIONS"},indent=2))
if __name__=="__main__": main()
