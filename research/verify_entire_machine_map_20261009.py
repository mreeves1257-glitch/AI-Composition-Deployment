"""Static code-grounded checks for October 9 whole-machine connection map.

Checks the original hard-copy Composer archive without deploying anything.
Cross-repository Plug/Control Panel wiring and historical Render evidence are
documented separately: tests here do NOT claim to execute their live HTTP path.
"""
from __future__ import annotations
import base64,io,tarfile,sys,json
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE/"composer_overrides"))
from genre_styles.shared_interpreter_router import (
  listed_genres,route_to_shared_interpreter,ORIGINAL_STAGE_ORDER)
from genre_styles.source_pattern_library import compile_original_source_seed
from genre_styles.source_pattern_resource_handoff import load_binding_file
from genre_styles.source_pattern_composer_handoff import (
  prepare_source_pattern_composer_handoff)

def check(flag,reason):
  if not flag:raise AssertionError(reason)

def main():
    m=BASE/"research"/"VERIFIED_ENTIRE_MACHINE_CONNECTION_MAP_2026-10-09_1342_CDT.md"
    check(m.is_file(),"CONNECTION_MAP_MISSING")
    text=m.read_text()
    check("## Map A" in text and "## Map B" in text and "L11" in text and "D10" in text,
          "MACHINE_MAP_HAS_MISSING_CONNECTION_LAYER")
    names=listed_genres();check(len(names)==55,"GENRE_COUNT_CHANGED")
    check(len(ORIGINAL_STAGE_ORDER)==7,"SEVEN_STAGE_ORDER_CHANGED")
    schemas=set();families=set();policies={"EXACT_ID":0,"EXACT_CONTEXTUAL":0,"BLOCKED_UNVERIFIED":0}
    score_notes=0
    for name in names:
        route=route_to_shared_interpreter(name)
        check(tuple(route["original_7_stages"])==ORIGINAL_STAGE_ORDER,
              "STAGE_ORDER_NOT_PRESERVED:"+name)
        check(len(route["capability_requirements"])==22,
              "GENRE_CAPABILITIES_NOT_22:"+name)
        score=compile_original_source_seed(name)
        check(score["recorded_audio_authorized"] is False,
              "UNVERIFIED_MUSIC_ACTIVATED:"+name)
        check(score["capability_execution"]["ready_for_live_deployment"] is False,
              "UNVERIFIED_DISPATCH_ACTIVATED:"+name)
        identities,ref=load_binding_file(name)
        families.add(ref["family"]);schemas.add(score["schema"])
        score_notes+=len(score["symbolic_note_events"])
        for r in identities["role_bindings"].values():
            check(r["lookup_policy"] in policies,"UNKNOWN_INSTRUMENT_MAPPING_POLICY")
            policies[r["lookup_policy"]]+=1
    check(len(families)==13,"GENRE_FAMILY_COUNT_DRIFT")
    check(policies=={"EXACT_ID":103,"EXACT_CONTEXTUAL":1,"BLOCKED_UNVERIFIED":130},
          "SOURCE_INSTRUMENT_ROLE_COUNT_DRIFT:"+str(policies))
    check(score_notes==4371,"SOURCE_MUSICAL_NOTE_COUNT_DRIFT:"+str(score_notes))
    build=(BASE/"build_current_composer.sh").read_text()
    check("developed['events'] = events" in build and
          "developed['source_pattern_composer_handoff']" in build,
          "MISSING_DEVELOPMENT_COMPOSER_PROPOSAL_HOOK")
    check("developed['events'] = developed['source_pattern_composer_handoff']" not in build,
          "PREMATURE_LIVE_EVENT_ACTIVATION")
    check("standalone_3d_mixer.py" in build and
          "[sys.executable, str(ROOT / 'standalone_3d_mixer.py')" in build,
          "STANDALONE_3D_MIXER_NOT_SEPARATE_PROCESS")
    check((BASE/"composer_overrides"/"standalone_3d_mixer.py").is_file(),
          "STANDALONE_MIXER_MISSING")
    pack=base64.b64decode((BASE/"composer"/"runtime.b64").read_bytes())
    with tarfile.open(fileobj=io.BytesIO(pack),mode="r:gz") as tar:
        names=set(tar.getnames())
        def source(name):
            targets=[n for n in names if n==name or n.endswith("/"+name)]
            check(len(targets)==1,"UNIQUE_RUNTIME_FILE_MISSING:"+name)
            return tar.extractfile(targets[0]).read().decode()
        engine=source("engine.py")
        gateway=source("input_gateway.py")
        output=source("output_handoff.py")
    actual_order=("self.genre.select","self.theory.create_new","self.instrument.resolve_events",
                  "self.target.resolve","self.performance.execute","execute_output_handoff",
                  "preflight_audio_resources","execute_audio_render")
    run_body=engine.split("    def run(",1)[1]
    observed=[run_body.find(x) for x in actual_order]
    check(all(x>=0 for x in observed) and observed==sorted(observed),
          "ORIGINAL_RUNTIME_COMPONENT_ORDER_CHANGED")
    check("theory['events']" in output and
          "for item in engine_result['modules']['target']['resolved_resources']" in output and
          "render_midi(" in output,"RENDERER_REQUIRES_OLD_COMPOSITION_EVENTS")
    check("result=AICompositionEngine().run" in gateway,
          "ORIGINAL_HTTP_TO_ENGINE_HANDOFF_CHANGED")
    check("genre=payload.get('genre')" in gateway and
          "tuning_reference_hz" not in gateway,
          "TUNING_INPUT_CONSUMPTION_CHANGED_REAUDIT_REQUIRED")
    for key in ("SOURCE VERIFIED","LIVE OBSERVED","PREPARED / ISOLATED TEST PASS",
                "UNVERIFIED","UNVERIFIED TODAY"):
        check(key in text,"MISSING_AUDIT_QUALIFICATION:"+key)
    print("ENTIRE_MACHINE_CONNECTION_MAP_STATIC_AUDIT_PASS",json.dumps({
       "genres":len(names),"families":len(families),"capability_handlers":22,
       "roles":sum(policies.values()),"role_policies":policies,
       "authored_preview_notes":score_notes,
       "runtime_components_traced":len(actual_order),
       "actual_audio_reverified":False,"production_modified":False,
       "cross_repository_live_proof":"HISTORICAL_RENDER_LOGS_NOT_RETESTED"}))
if __name__=="__main__":main()
