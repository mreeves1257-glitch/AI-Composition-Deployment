"""Read-only regression audit for preserved genre execution adapter.

Usage: python composer_overrides/audit_legacy_execution.py /path/to/preserved_adapter.py
The preserved adapter and registry must be colocated. No create_new, history writes,
deployment, or composer modification. The adapter import may create an output dir.
"""
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

def run(adapter_path):
    adapter_path=Path(adapter_path).resolve()
    spec=importlib.util.spec_from_file_location("preserved_genre_adapter",adapter_path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    outcomes=Counter()
    examples={}
    for genre in module.profiles:
        result=module.build_setup(genre,module.profiles[genre],mode="quick",creation_seed=0)
        status=result.get("status","UNKNOWN")
        outcomes[status]+=1
        if status=="PASS":
            actual=len(set(event["instrument_id"] for event in result["events"]))
            examples[genre]={"instrument_types":actual,"events":len(result["events"]),
                             "palette":result["palette"]}
        else:
            examples[genre]={"status":status}
    return {"registered_genres":len(module.profiles),"status_counts":dict(outcomes),
            "genre_results":examples}

if __name__=="__main__":
    if len(sys.argv)!=2: raise SystemExit("Provide preserved adapter file path")
    print(json.dumps(run(sys.argv[1]),indent=2,sort_keys=True))
