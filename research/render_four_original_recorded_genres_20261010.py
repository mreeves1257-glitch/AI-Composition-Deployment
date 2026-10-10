#!/usr/bin/env python3
"""Isolated four-genre original SFZ stems -> unchanged standalone 3D mixer.

Never promotes source-pattern candidates into the live Composer event stream.
"""
import hashlib,json,math,os
from pathlib import Path
from genre_styles.source_pattern_library import compile_original_source_seed
from genre_styles.source_pattern_composer_handoff import prepare_source_pattern_composer_handoff
from sfz_renderer_adapter import render_midi
from standalone_3d_mixer import run_job
from importlib.util import spec_from_file_location,module_from_spec

spec=spec_from_file_location("rock_midi_writer",Path("research/render_isolated_rock_recorded_stems_20261010.py"))
writer=module_from_spec(spec);spec.loader.exec_module(writer)
GENRES=("Jazz Fusion","Rhythm and Blues","Soul","Neo-Soul-related")
IDS={"electric_bass_guitar":"electric_bass_guitar","electric_piano":"electric_piano",
     "kick_drum_rock":"kick_drum_rock","snare_drum":"snare_drum","hi_hat":"hi_hat"}

def main():
    registry=json.loads(Path("composer/runtime/target_registry.json").read_text())["targets"]["INTERNAL"]["instrument_bindings"]
    root=Path("four-genre-diagnostic-audio").resolve();root.mkdir(exist_ok=True)
    summary={"diagnostic_only":True,"approved_for_live":False,"genres":[]}
    for genre in GENRES:
        plan=compile_original_source_seed(genre)
        proposal=prepare_source_pattern_composer_handoff(plan,target_bindings=registry)
        roles=proposal["routing"]["roles"]
        if len(roles)!=5 or any(r["status"]!="EXACT_PROGRAM_REFERENCE_ONLY" for r in roles):
            raise RuntimeError("ORIGINAL_SOURCE_MAPPING_INCOMPLETE:"+genre)
        events=proposal["candidate_stage4_events"]
        if not events or proposal["audio_render_authorized"] or not proposal["candidate_is_not_live_events"]:
            raise RuntimeError("CANDIDATE_ISOLATION_FAILURE:"+genre)
        folder=root/genre.lower().replace(" ","_").replace("-","_");folder.mkdir(exist_ok=True)
        stems=[];profiles=[];resolved=[];bpm=plan["tempo_bpm"]
        for r in roles:
            track=r["role"];selected=[e for e in events if e["track_id"]==track]
            if not selected:raise RuntimeError("MISSING_GENRE_PART:"+genre+":"+track)
            binding=registry[r["binding_id"]]
            midi=folder/(track.lower()+".mid");wav=folder/(track.lower()+".wav")
            midi.write_bytes(writer.midi_track(selected,bpm))
            result=render_midi(binding,midi,wav,sample_rate=22050)
            if not result["audio_rendered"] or not math.isfinite(result["peak_linear"]) or result["peak_linear"]<=0:
                raise RuntimeError("SILENT_ORIGINAL_GENRE_STEM:"+genre+":"+track)
            iid=r["original_instrument_id"]
            if iid not in IDS:raise RuntimeError("UNVERIFIED_INSTRUMENT_ID:"+iid)
            stems.append({"track_id":track,"wav_path":str(wav)})
            profiles.append({"track_id":track,"instrument_id":IDS[iid],"role":track})
            resolved.append({"track_id":track,"resource":binding})
        fingerprint=hashlib.sha256(json.dumps(events,sort_keys=True).encode()).hexdigest()
        engine={"genre":genre,"modules":{"instrument":{"profiles":profiles},
               "target":{"resolved_resources":resolved},"performance":{"events":events},
               "theory":{"composition_fingerprint":fingerprint}}}
        job=folder/"isolated_mixer_job.json"
        job.write_text(json.dumps({"engine_result":engine,"stems":stems},indent=2))
        mixed=run_job(job,folder/"mixed")
        if mixed.get("status")!="AUDIO_RENDER_PASS" or not mixed.get("audio_rendered"):
            raise RuntimeError("ORIGINAL_3D_MIX_FAILED:"+genre)
        import shutil
        final=folder/"ORIGINAL_RECORDED_3D_DIAGNOSTIC.wav"
        shutil.copy2(mixed["wav_path"],final)
        summary["genres"].append({"genre":genre,"original_recorded_stems":len(stems),
           "events":len(events),"bpm":bpm,"audio":str(final.relative_to(root)),
           "mixer_stage":mixed["mixer_stage"],
           "sha256":hashlib.sha256(final.read_bytes()).hexdigest()})
        print("GENRE_ORIGINAL_RECORDED_3D_MIX_PASS",genre,len(events),flush=True)
    (root/"manifest.json").write_text(json.dumps(summary,indent=2)+"\n")
    print("FOUR_GENRES_DIAGNOSTIC_ONLY_NO_DEPLOY",flush=True)

if __name__=="__main__":main()
