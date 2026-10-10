"""Inspect actual original Swing event and resource routing WITHOUT altering sounds."""
import json,importlib.util,sys
from pathlib import Path
sys.path.insert(0,"composer/runtime")
from genre_styles.genre_run_settings import load_genre_configuration
from instrument_program import InstrumentProgram
p=Path("composer/runtime/AI_Comp_Genre_Execution_Adapter_002_WORKING_2026-10-02_184019_CDT.py")
spec=importlib.util.spec_from_file_location("swing_adaptor_real",p)
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
r=mod.GenreExecutionAdapter().resolve("Swing",mode="normal",creation_seed=20261010)
d={"status":r.get("status"),"reason":r.get("reason"),"palette":r.get("palette"),
"execution_template":r.get("execution_template"),"genre_profile":load_genre_configuration("Swing"),
"result_fields":list(r.keys()),"events_count":len(r.get("events",[]))}
from collections import Counter,defaultdict
d["instruments"]=dict(Counter((str(x.get("track_id")),str(x.get("instrument_id"))) for x in r.get("events",[])))
d["sample_notes"]=list(r.get("events",[]))[:7]
instr=InstrumentProgram(Path("composer/runtime/instrument_library.json")).resolve_events(r.get("events",[]))
d["instrument_resolution"]={k:v for k,v in instr.items() if k not in ("source_requests","profiles")}
d["source_requests"]=instr.get("source_requests")
print("SWING_ORIGINAL_ENGINE_SOURCE_AUDIT",json.dumps(d,default=str)[:12000],flush=True)
