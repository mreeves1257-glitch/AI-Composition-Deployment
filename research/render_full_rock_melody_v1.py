"""Actual full Rock composer melodic-grammar audition (research, no deployment).

Verifies Composer's own 127-bar score OFF/ON, then renders only the opt-in
candidate through original SFZ instruments and the unchanged 3D mixer.
The original real full-song WAV is already archived in the 19:13 CDT hard save.
"""
from __future__ import annotations
from collections import defaultdict, Counter
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import wave

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "composer" / "runtime"
OUT = ROOT / "research" / "rock_melody_v1_full_song"
SWITCH = "AI_COMP_ROCK_MELODY_V1"


def must(condition, reason):
    if not condition:
        raise AssertionError(reason)


def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for part in iter(lambda:f.read(1024*1024),b""):
            h.update(part)
    return h.hexdigest()


def score_stats(notes):
    leads=[e for e in notes if e.get("track_id")=="LEAD"]
    harmony=defaultdict(set)
    for e in notes:
        if (e.get("track_id")=="HARMONY"
                and (float(e.get("start_beat",0))%4)<0.6):
            harmony[int(float(e["start_beat"])//4)].add(int(e["midi"])%12)
    aligned=sum(int(e["midi"])%12 in harmony[int(float(e["start_beat"])//4)]
                for e in leads)
    return {"lead_count":len(leads),
            "distinct_lead_pitches":len({e["midi"] for e in leads}),
            "distinct_lead_onsets_in_bar":len({round(float(e["start_beat"])%4,2) for e in leads}),
            "lead_chord_tone_fraction":round(aligned/max(len(leads),1),4),
            "lead_pitch_frequency":dict(Counter(str(e["midi"]) for e in leads))}


def run():
    OUT.mkdir(parents=True,exist_ok=True)
    RUNTIME.resolve()
    os.environ["AI_COMP_OUTPUT_ROOT"]=str(OUT/"engine_audio")
    os.environ["AI_COMP_RESOURCE_BANK"]=str(RUNTIME/"sound_resources")
    os.environ["AI_COMP_SFZ_RENDERER"]=str(ROOT/".composer_tools"/"bin"/"sfizz_render")
    os.environ["AI_COMP_ROCK_BASS_SUSTAIN_V1"]="0"
    os.environ["AI_COMP_AUTO_PHRASING_V1"]="0"
    os.environ[SWITCH]="0"
    sys.path.insert(0,str(RUNTIME))
    from engine import AICompositionEngine
    engine=AICompositionEngine(history_path=OUT/"fresh_generation_history.json")
    original=engine.theory.resolve("ROCK","normal",0)
    must(original.get("status")=="PASS","CANONICAL_SCORE_NOT_VALID")
    os.environ[SWITCH]="1"
    actual=engine.run("ROCK",target_id="INTERNAL",mode="normal")
    theory=actual.get("modules",{}).get("theory",{})
    current=theory.get("events") or []
    old=original["events"]
    must(len(old)==3065,"CANONICAL_SCORE_CHANGED_OR_NOT_SEED0")
    must(len(current)>2000,"MELODY_BROKE_FULL_SCORE")
    old_nonlead=[e for e in old if e["track_id"]!="LEAD"]
    new_nonlead=[e for e in current if e["track_id"]!="LEAD"]
    must(old_nonlead==new_nonlead,"PROTECTED_NONLEAD_SCORE_CHANGED")
    old_lead=[e for e in old if e["track_id"]=="LEAD"]
    new_lead=[e for e in current if e["track_id"]=="LEAD"]
    must(len(new_lead)<len(old_lead),"UNIFORM_SIX_NOTE_RUNS_NOT_REMOVED")
    must(len(new_lead)>100,"MELODY_UNDERWRITTEN")
    must(all(e.get("articulation")=="rock_melodic_phrase" for e in new_lead),"ORIGINAL_LEAD_NOT_REPLACED")
    pre=score_stats(old)
    post=score_stats(current)
    must(post["lead_chord_tone_fraction"]>=.9,"MELODY_CHORD_ALIGNMENT_NOT_PROVEN")
    must(post["distinct_lead_onsets_in_bar"]>pre["distinct_lead_onsets_in_bar"],
         "RHYTHMIC_PHRASING_DID_NOT_GAIN_VARIETY")
    must(post["distinct_lead_pitches"]>pre["distinct_lead_pitches"],
         "MELODY_DID_NOT_EXPAND_REGISTERS")
    # Native audio rendering, not score-only success
    render=actual.get("audio_render") or {}
    must(actual.get("audio_rendered") and render.get("status")=="AUDIO_RENDER_PASS",
         "ACTUAL_REAL_SOURCE_AUDIO_NOT_FINISHED:"+str(render.get("status")))
    wav=Path(render.get("wav_path",""))
    master=Path(render.get("master_path",""))
    must(wav.is_file() and master.is_file(),"3D_RESULT_MISSING")
    with wave.open(str(wav),"rb") as f:
        count=f.getnframes()
        rate=f.getframerate()
        channels=f.getnchannels()
        sample_width=f.getsampwidth()
    duration=count/rate
    must(170 <=duration<=240 and rate==44100 and channels==2 and sample_width==2,
         "NOT_REAL_FULL_LENGTH_STEREO_WAV")
    meta=json.loads(master.read_text())
    must(meta.get("authoritative_3d_master") is True and len(meta.get("audio_objects",[]))>=9,
         "INVALID_3D_MASTER")
    saved=OUT/"ROCK_FULL_SONG_MELODY_R1_RECORDED_3D.wav"
    shutil.copyfile(wav,saved)
    source_stems=render.get("stems") or []
    stem_report=[{"track_id":s.get("track_id"),"note_count":s.get("note_count"),
                  "peak_dbfs":s.get("peak_dbfs"),"rms_dbfs":s.get("rms_dbfs")}
                 for s in source_stems]
    result={
        "status":"REAL_FULL_ROCK_MELODIC_CANDIDATE_COMPLETE",
        "study":"ROCK_THEME_RESPONSE_CHORD_TONE_GRAMMAR_R1",
        "genre":"ROCK","tempo_bpm":theory.get("tempo_bpm"),
        "bars":theory.get("bars"),
        "original_event_count":len(old),"candidate_event_count":len(current),
        "original_score_metrics":pre,
        "melodic_candidate_score_metrics":post,
        "unchanged_nonlead_event_count":len(old_nonlead),
        "every_nonlead_event_equal":True,
        "audio_rendered":True,"native_3d_master":True,
        "recorded_stems":stem_report,"duration_seconds":round(duration,3),
        "sample_rate":rate,"channels":channels,
        "full_song_wav":saved.name,
        "wav_sha256":sha(saved),
        "deployed":False,"musical_preference_proven":False,
        "feature_switch":SWITCH,
        "feature_enabled_only_in_isolated_research_run":True,
        "known_limit":"Chord-tone grammar alone does not guarantee an engaging song; audition and revise."
    }
    (OUT/"REPORT.json").write_text(json.dumps(result,indent=2)+"\n")
    print("REAL_FULL_ROCK_MELODY_V1_WAV_PASS",json.dumps({
        "bars":result["bars"],"source_events":len(old),
        "candidate_events":len(current),"old_lead":len(old_lead),
        "new_lead":len(new_lead),
        "original_chord_fraction":pre["lead_chord_tone_fraction"],
        "candidate_chord_fraction":post["lead_chord_tone_fraction"],
        "all_nonlead_identical":True,
        "recorded_sources":len(source_stems),"duration_s":round(duration,3),
        "full_3d_music":True,
    }),flush=True)


if __name__=="__main__":
    run()
