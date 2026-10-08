"""Isolated real-instrument eight-bar Rock ensemble bass-release comparison.

No changes to deployed Composer, plug, control panel, source SFZs or the
standalone 3D mixer. Reuse original composed Rock events and all non-bass MIDI
identically. Only alternative BASS note-off timings differ in candidate.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import wave

import numpy as np

from rock_bass_real_sample_ab_v1 import (
    BEATS_PER_BAR, BARS_IN_WINDOW, OUT as BASS_AB_OUT, PPQ,
    candidate_duration, load_real_rock, vlq,
)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent / "composer" / "runtime"
DEST = HERE / "rock_full_band_ab_output"
SR = 44100

TRACKS = {
    "HARMONY": ("electric_guitar:RHYTHM_POWER_CHORDS","electric_guitar","RHYTHM_POWER_CHORDS"),
    "LEAD": ("electric_guitar:LEAD_MELODY","electric_guitar","LEAD_MELODY"),
    "BASS": ("electric_bass_guitar","electric_bass_guitar","BASS"),
    "KICK": ("kick_drum_rock","kick_drum_rock","KICK_PULSE"),
    "SNARE": ("snare_drum","snare_drum","SNARE_BACKBEAT"),
    "HAT": ("hi_hat","hi_hat","HI_HAT"),
    "TOMS": ("tom_tom","tom_tom","TOM_FILL"),
    "CRASH": ("crash_cymbal","crash_cymbal","CRASH_ACCENT"),
    "RIDE": ("ride_cymbal","ride_cymbal","RIDE_TIMEKEEPING"),
}
ALLOWED_IDS = {
    "HARMONY": {"electric_guitar"},
    "LEAD": {"electric_guitar","lead_guitar"},
    "BASS": {"electric_bass","electric_bass_guitar"},
    "KICK": {"kick_drum_rock"},
    "SNARE": {"snare_drum"},
    "HAT": {"hi_hat"},
    "TOMS": {"tom_tom","tom_drum"},
    "CRASH": {"crash_cymbal"},
    "RIDE": {"ride_cymbal"},
}


def require(yes, msg):
    if not yes:
        raise AssertionError(msg)


def midi_from_notes(notes, bpm, path, initial_cc):
    tempo = round(60_000_000 / bpm)
    events = [(0, -20, b"\xff\x51\x03" + tempo.to_bytes(3,"big"))]
    for controller, value in initial_cc.items():
        cc = int(controller)
        require(0 <= cc <= 127 and type(value) is int and 0 <= value <= 127,
                "BAD_SOURCE_CC")
        events.append((0, -10, bytes((0xB0, cc, value))))
    for note in notes:
        onset = round(float(note["start_beat"]) * PPQ)
        finish = round((float(note["start_beat"])+float(note["duration_beats"])) * PPQ)
        pitch = int(note["midi"])
        velocity = int(note["velocity"])
        require(0 <= onset < finish and 0 <= pitch <= 127
                and 1 <= velocity <= 127, "INVALID_SCORE_NOTE")
        events.append((onset, 1, bytes((0x90, pitch, velocity))))
        events.append((finish, 0, bytes((0x80, pitch, 0))))
    events.sort(key=lambda r:(r[0],r[1]))
    previous = 0
    seq = bytearray()
    for tick,_,data in events:
        seq += vlq(tick-previous)+data
        previous=tick
    seq += b"\x00\xff\x2f\x00"
    data=(b"MThd"+struct.pack(">IHHH",6,0,1,PPQ)
          +b"MTrk"+struct.pack(">I",len(seq))+seq)
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def pcm_rms(audio, first_n_seconds=8):
    with wave.open(str(audio),"rb") as w:
        require(w.getsampwidth() == 2 and w.getframerate() == SR,"BAD_STEREO_OUTPUT")
        raw=w.readframes(int(first_n_seconds*SR))
        channels=w.getnchannels()
    vals=np.frombuffer(raw,dtype="<i2").astype(np.float64).reshape(-1,channels)
    return float(np.sqrt(np.mean(vals*vals)) /32768.0)


def run():
    composer,score,bass=load_real_rock()
    bpm=float(composer["tempo_bpm"])
    require(int(bpm)==145,"ROCK_TEMPO_CHANGED")
    end=BEATS_PER_BAR*BARS_IN_WINDOW
    eligible=[dict(e) for e in score
              if 0 <= float(e.get("start_beat",-1)) < end
              and str(e.get("track_id","")).upper() in TRACKS]
    require(eligible,"NO_COMPOSED_ROCK_EVENTS")
    bytrack={}
    for src in eligible:
        track=str(src["track_id"]).upper()
        require(str(src.get("instrument_id")) in ALLOWED_IDS[track],
                "WRONG_OR_UNEXPECTED_INSTRUMENT:"+track+":"+str(src.get("instrument_id")))
        note=dict(src)
        note["start_beat"]=float(note["start_beat"])
        note["duration_beats"]=min(float(note["duration_beats"]),end-note["start_beat"])
        require(note["duration_beats"]>0,"INVALID_NOTELENGTH")
        bytrack.setdefault(track,[]).append(note)
    for required in ("HARMONY","LEAD","BASS","KICK","SNARE","HAT"):
        require(bytrack.get(required),"MISSING_ENSEMBLE_MEMBER:"+required)
    for notes in bytrack.values():
        notes.sort(key=lambda n:(n["start_beat"],int(n["midi"])))

    registry=json.loads((ROOT/"target_registry.json").read_text(encoding="utf-8"))
    bindings=registry["targets"]["INTERNAL"]["instrument_bindings"]
    from sfz_renderer_adapter import render_midi
    from genre_styles.Rock.rock_balance_contract import apply_rock_balance
    from genre_styles.Rock.recorded_subkick import prepare_recorded_subkick
    renderer=HERE.parent/".composer_tools"/"bin"/"sfizz_render"
    require(renderer.is_file(),"ORIGINAL_SFIZZ_NOT_BUILT")
    os.environ["AI_COMP_SFZ_RENDERER"]=str(renderer)
    os.environ["AI_COMP_RESOURCE_BANK"]=str(ROOT/"sound_resources")
    DEST.mkdir(parents=True,exist_ok=True)
    fingerprint="ISOLATED_8BAR_ROCK_BASS_AB_EXISTING_SCORE_SEED0"
    original_engine={
        "genre":"ROCK",
        "modules":{
            "theory":{"composition_fingerprint":fingerprint},
            "instrument":{"profiles":[]},
            "target":{"resolved_resources":[]},
            "performance":{"events":eligible},
        },
    }
    for track in bytrack:
        binding_key,instrument,role=TRACKS[track]
        resource=copy.deepcopy(bindings[binding_key])
        require(resource.get("resource_type")=="SFZ_SAMPLE_LIBRARY","NOT_RECORDED")
        original_engine["modules"]["instrument"]["profiles"].append({
            "track_id":track,"instrument_id":instrument,"role":role
        })
        original_engine["modules"]["target"]["resolved_resources"].append({
            "track_id":track,"instrument_id":instrument,"resource":resource
        })
    engine=apply_rock_balance(original_engine)
    render_manifest={}
    originals={}
    candidates={}
    changed=[]
    for track,notes in sorted(bytrack.items()):
        mapped=next(x["resource"] for x in
                    original_engine["modules"]["target"]["resolved_resources"]
                    if x["track_id"]==track)
        rawmap=mapped.get("midi_mapping",{}).get("initial_cc",{})
        control=DEST/(track.lower()+"-source.mid")
        origin_path=DEST/(track.lower()+"-source.wav")
        original_hash=midi_from_notes(notes,bpm,control,rawmap)
        first=render_midi(mapped,control,origin_path,sample_rate=SR)
        require(first.get("audio_rendered"),"SOURCE_STEM_FAILED:"+track)
        render_manifest[track]={"midi_sha256_original":original_hash,
                                "source":mapped["resource_id"],
                                "mapping":mapped["preferred_mapping"]}
        originals[track]={"track_id":track,"instrument_id":TRACKS[track][1],
                          "wav_path":str(origin_path)}
        candidates[track]=dict(originals[track])
        if track=="BASS":
            options=[]
            ordered=sorted(bass,key=lambda r:(float(r["start_beat"]),int(r["midi"])))
            for note in notes:
                absolute=float(note["start_beat"])
                # The original generated Rock bass may have multiple events at
                # one onset; resolve the following DISTINCT attack.
                next_onset=next((float(x["start_beat"]) for x in ordered
                    if float(x["start_beat"])>absolute+1e-9),None)
                suggested=candidate_duration(note,next_onset)
                suggested=min(suggested,end-absolute)
                clone=dict(note)
                clone["duration_beats"]=suggested
                options.append(clone)
                if suggested-note["duration_beats"]>=0.14:
                    changed.append({"at_beat":absolute,
                                    "old_length":note["duration_beats"],
                                    "new_length":suggested})
            require(changed,"NOTHING_CHANGED_IN_BASS")
            alternative=DEST/"bass-candidate.mid"
            second_hash=midi_from_notes(options,bpm,alternative,rawmap)
            alternative_audio=DEST/"bass-candidate.wav"
            second=render_midi(mapped,alternative,alternative_audio,sample_rate=SR)
            require(second.get("audio_rendered"),"BASS_CANDIDATE_NOT_REAL")
            candidates[track]={"track_id":track,"instrument_id":TRACKS[track][1],
                              "wav_path":str(alternative_audio)}
            render_manifest[track]["midi_sha256_candidate"]=second_hash
        else:
            render_manifest[track]["midi_sha256_candidate"]=original_hash
    require(len(changed)>0,"NO_BASS_RELEASE_DIFF")
    for track in bytrack:
        if track=="BASS":continue
        require(originals[track]==candidates[track],"OTHER_INSTRUMENT_CHANGED:"+track)
    print("ROCK_ENSEMBLE_IDENTICAL_OTHER_STEMS",sorted(t for t in bytrack if t!="BASS"),flush=True)

    products={}
    for key,stems in (("original",originals),("candidate",candidates)):
        job_dir=DEST/key
        job_dir.mkdir(exist_ok=True)
        adjusted,with_sub=prepare_recorded_subkick(engine,list(stems.values()),job_dir)
        jobfile=job_dir/"job.json"
        jobfile.write_text(json.dumps({"engine_result":adjusted,"stems":with_sub}))
        proc=subprocess.run([sys.executable,str(ROOT/"standalone_3d_mixer.py"),
                str(jobfile),str(job_dir/"final_audio")],text=True,capture_output=True,timeout=120)
        try:
            payload=json.loads(proc.stdout.strip())
        except (ValueError,TypeError):
            raise RuntimeError("3D_MIX_RESPONSE_UNREADABLE:"+proc.stderr[-500:])
        require(proc.returncode==0 and payload.get("status")=="AUDIO_RENDER_PASS",
                "EXISTING_3D_MIX_FAILED:"+json.dumps(payload)[:900])
        actual=Path(payload["wav_path"])
        require(actual.is_file(),"STEREO_DERIVATIVE_MISSING")
        audible=DEST/("Rock-8bar-full-band-"+key+".wav")
        shutil.copyfile(actual,audible)
        products[key]=str(audible)
        print("REAL_ROCK_ENSEMBLE_3D_AUDIO",key,audible.name,
            "rms8",round(pcm_rms(audible),8),flush=True)
    r1=pcm_rms(products["original"])
    r2=pcm_rms(products["candidate"])
    summary={
        "study":"FULL_ROCK_8_BAR_EXACT_RECORDED_ENSEMBLE_AB",
        "status":"3D_DERIVATIVE_CREATED_NOT_MUSIC_APPROVAL",
        "tempo_bpm":bpm,"original_full_song_events":len(score),
        "source_8bar_events":len(eligible),
        "stems":[k for k in sorted(bytrack)],
        "bass_timing_changes":changed,
        "other_tracks_midi_and_audio_identical":True,
        "preserved_recorded_subkick":True,
        "original_stereo_rms8":r1,
        "candidate_stereo_rms8":r2,
        "genre_links_or_live_composer_changed":False,
        "render_manifest":render_manifest,
        "audio_files":products,
    }
    (DEST/"findings.json").write_text(json.dumps(summary,indent=2)+"\n")
    print("REAL_ROCK_ENSEMBLE_AB_COMPLETE",json.dumps({
        "source_8bar_events":len(eligible),"track_count":len(bytrack),
        "bass_modified":len(changed),"original_rms8":r1,"candidate_rms8":r2,
        "other_instruments_identical":True,"full_3d_stage_used":True,
    }),flush=True)


if __name__=="__main__":
    run()
