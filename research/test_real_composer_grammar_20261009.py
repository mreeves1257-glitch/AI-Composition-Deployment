"""Exercise new shared grammar from the preserved actual Composer normal-mode path."""
from pathlib import Path
import importlib.util,shutil,sys
root=Path("/tmp/original-composer-runtime")
original=root/"AI_Comp_Genre_Execution_Adapter_002_WORKING_2026-10-02_184019_CDT.py"
assert original.is_file(),"ORIGINAL_COMPOSER_ADAPTER_NOT_EXTRACTED"
shutil.copytree("composer_overrides/genre_styles",root/"genre_styles",dirs_exist_ok=True)
for helper in Path("composer_overrides").glob("*.py"):
    dest=root/helper.name
    if not dest.is_file():shutil.copyfile(helper,dest)
build=Path("build_current_composer.sh").read_text()
anchor='override=r"""'
start=build.index(anchor)+len(anchor)
stop=build.index('"""',start)
patch=build[start:stop]
assert patch.count("developed['shared_musical_plan'] = compile_musical_plan(")==1
original.write_text(original.read_text()+"\n"+patch+"\n")
sys.path.insert(0,str(root.resolve()))
spec=importlib.util.spec_from_file_location("isolated_development_composer",original)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
result=module.GenreExecutionAdapter().resolve("ROCK",mode="normal",creation_seed=0)
assert result.get("status")=="PASS",result.get("status")
assert len(result.get("events",[]))>0,"ORIGINAL_STAGE4_NOT_GENERATING_NOTES"
plan=result["shared_musical_plan"]
assert plan["genre"]=="ROCK"
assert plan["genre_profile_id"]==result["shared_interpreter_handoff"]["genre_profile_id"]
assert plan["arranger_status"]=="EXECUTABLE_SYMBOLIC_INTENT_ONLY"
assert plan["meter"]==result["meter"] and plan["tempo_bpm"]==result["tempo_bpm"]
assert plan["symbolic_note_events"]==[]
assert plan["midi_authorized"] is False and plan["recorded_audio_authorized"] is False
assert len(plan["capability_status"])==22
seed=result["source_pattern_seed_plan"]
assert seed["genre"]=="ROCK" and seed["source_pattern_contract"]["genre_specific_seed"]=="ROCK"
assert len(seed["symbolic_note_events"])>0
assert seed["recorded_audio_authorized"] is False and seed["midi_authorized"] is False
assert seed["source_pattern_contract"]["production_enabled"] is False
assert "KICK" in {x["role"] for x in seed["symbolic_note_events"]}
proposal=result["source_pattern_composer_handoff"]
assert proposal["genre"]=="ROCK"
assert proposal["requested_note_count"]==len(seed["symbolic_note_events"])
assert proposal["original_events_count"]==len(result["events"])
assert proposal["candidate_is_not_live_events"] is True
assert proposal["audio_render_authorized"] is False
assert proposal["original_composer_is_authoritative_for_audio"] is True
assert proposal["status"] in ("CANDIDATE_STAGE4_EVENTS_READY_SOURCE_PREFLIGHT_PENDING",
                             "BLOCKED_INCOMPLETE_EXACT_INSTRUMENT_MAPPING")
print("PRESERVED_ORIGINAL_COMPOSER_DEVELOPMENT_GRAMMAR_HOOK_PASS",
      {"original_event_count":len(result["events"]),"genre":plan["genre"],
       "symbolic_layer_attached":True,"finished_music_claimed":False})
