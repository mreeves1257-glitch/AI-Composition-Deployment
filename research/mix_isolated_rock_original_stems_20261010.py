#!/usr/bin/env python3
"""Pass isolated original-recording Rock stems through the unchanged 3D mixer.

Diagnostic only. Does not modify Composer events, genre formulas, or live deployment.
"""
import hashlib
import json
from pathlib import Path
from genre_styles.source_pattern_library import compile_original_source_seed
from genre_styles.source_pattern_composer_handoff import prepare_source_pattern_composer_handoff
from standalone_3d_mixer import run_job

def main():
    root=Path("rock-diagnostic-audio").resolve()
    manifest=json.loads((root/"manifest.json").read_text())
    if not manifest["diagnostic_only"] or not manifest["live_composer_unchanged"]:
        raise RuntimeError("ISOLATION_NOT_PROVEN")
    registry=json.loads(Path("composer/runtime/target_registry.json").read_text())["targets"]["INTERNAL"]["instrument_bindings"]
    proposal=prepare_source_pattern_composer_handoff(compile_original_source_seed("ROCK"),target_bindings=registry)
    if not proposal["candidate_is_not_live_events"] or proposal["audio_render_authorized"]:
        raise RuntimeError("CANDIDATE_ACTIVATION_FORBIDDEN")
    events=proposal["candidate_stage4_events"]
    roles={r["role"]:r for r in proposal["routing"]["roles"]}
    instrument_ids={"BASS":"electric_bass_guitar","HARMONY":"electric_guitar","KICK":"kick_drum_rock","SNARE":"snare_drum","HAT":"hi_hat"}
    profiles=[];resolved=[];stems=[]
    for item in manifest["stems"]:
        track=item["role"]; role=roles[track]
        if role["binding_id"]!=item["source"] or track not in instrument_ids:
            raise RuntimeError("ORIGINAL_RESOURCE_MISMATCH:"+track)
        path=root/item["wav"]
        if not path.is_file():raise RuntimeError("MISSING_RECORDED_STEM:"+track)
        profiles.append({"track_id":track,"instrument_id":instrument_ids[track],
                         "role":"RHYTHM_POWER_CHORDS" if track=="HARMONY" else track})
        resolved.append({"track_id":track,"resource":registry[item["source"]]})
        stems.append({"track_id":track,"wav_path":str(path)})
    if len(stems)!=5:raise RuntimeError("INCOMPLETE_ROCK_STEMS")
    fingerprint=hashlib.sha256(json.dumps(events,sort_keys=True).encode()).hexdigest()
    engine={"genre":"ROCK","modules":{"instrument":{"profiles":profiles},
             "target":{"resolved_resources":resolved},"performance":{"events":events},
             "theory":{"composition_fingerprint":fingerprint}}}
    job=root/"isolated_mixer_job.json"
    job.write_text(json.dumps({"engine_result":engine,"stems":stems},indent=2)+"\n")
    result=run_job(job,root/"mixed")
    if result.get("status")!="AUDIO_RENDER_PASS" or not result.get("audio_rendered"):
        raise RuntimeError("UNCHANGED_3D_MIXER_DID_NOT_RENDER")
    final=Path(result["wav_path"])
    import shutil
    target=root/"ROCK_SEVEN_BAR_ORIGINAL_SFZ_3D_DIAGNOSTIC.wav"
    shutil.copy2(final,target)
    report={"diagnostic_only":True,"approved_for_live":False,"genre":"ROCK",
            "original_instruments":5,"event_count":len(events),
            "mixer_stage":result.get("mixer_stage"),
            "output_wav":target.name,"sha256":hashlib.sha256(target.read_bytes()).hexdigest()}
    (root/"isolated_mixed_report.json").write_text(json.dumps(report,indent=2)+"\n")
    print("ISOLATED_ORIGINAL_ROCK_3D_MIXED_AUDIO_RENDERED",target,flush=True)

if __name__=="__main__":main()
