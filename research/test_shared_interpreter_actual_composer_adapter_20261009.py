"""Isolated source replay of the actual runtime Composer Stage3→4 build adapter."""
from pathlib import Path
import importlib.util
import json
import shutil
import sys

root=Path("/tmp/original-composer-runtime")
assert (root/"AI_Comp_Genre_Execution_Adapter_002_WORKING_2026-10-02_184019_CDT.py").is_file()
shutil.copytree("composer_overrides/genre_styles",root/"genre_styles",dirs_exist_ok=True)
shutil.copyfile("composer_overrides/genre_development_patch.py",root/"genre_development_patch.py")
build=Path("build_current_composer.sh").read_text()
anchor='override=r"""'
start=build.index(anchor)+len(anchor)
stop=build.index('"""',start)
insertion=build[start:stop]
assert "shared_interpreter_handoff" in insertion
path=root/"AI_Comp_Genre_Execution_Adapter_002_WORKING_2026-10-02_184019_CDT.py"
path.write_text(path.read_text()+"\n"+insertion+"\n")
sys.path.insert(0,str(root.resolve()))
spec=importlib.util.spec_from_file_location("staged_unchanged_composer_plus_shared_interpreter",path)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
result=module.GenreExecutionAdapter().resolve("ROCK",mode="normal",creation_seed=0)
assert result.get("status")=="PASS",result.get("status")
route=result["shared_interpreter_handoff"]
assert route["genre"]=="ROCK"
assert route["link_state"]=="CONNECTED_STAGE_3_TO_4_DATA_ROUTER"
assert route["arranger_backend_state"]=="MUSICAL_EVENT_GENERATOR_NOT_ENABLED_OR_VERIFIED"
assert len(route["capability_requirements"])==22
assert len(result["events"])>0,"ORIGINAL_COMPOSER_OUTPUT_LOST"
assert all(not e.get("source_bank_changed",False) for e in result["events"])
print("LIVE_COMPOSER_ADAPTER_ISOLATED_SHARED_INTERPRETER_ROCK_NORMAL_PASS",json.dumps({"status":result["status"],"genre":route["genre"],"roles":len(route["selected_original_instrument_ids"]),"original_events":len(result["events"]),"handoff":route["link_state"],"fully_interpreted_music_not_claimed":True},sort_keys=True))
