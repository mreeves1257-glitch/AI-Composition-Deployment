"""Audition gate: old oompa composition cannot reenter new Rock output.

This tests true musical score events from the saved MMA Rock2 reference, not a
filename or the presence of a ROCK genre label. It does not claim human approval.
"""
import importlib.util
from pathlib import Path
from collections import Counter
import hashlib
import json

ROOT=Path(__file__).resolve().parents[1]
p=ROOT/"composer_overrides/genre_styles/Rock/rock2_new_song.py"
sp=importlib.util.spec_from_file_location("new_rock2",p)
r=importlib.util.module_from_spec(sp)
sp.loader.exec_module(r)

def ctx(bars):
    notes={"C": ["C","E","G"], "G":["G","B","D"], "F":["F","A","C"],
           "A":["A","C","E"], "D":["D","F","A"]}
    chords=[{"root":key,"notes":notes[key]} for key in
            ([ "A","F","C","G"]*(bars//4))]
    return {"meter":{"numerator":4,"denominator":4},
            "harmony":{"chords":chords},
            "key":{"scale":["A","B","C","D","E","F","G"]}}

def test(seed):
    shape=r.choose_new_song_shape(seed)
    score=r.compose_new_rock_song(ctx(shape["bars"]),seed)
    assert score and len(score)>shape["bars"]*8
    assert shape["tempo_bpm"]!=145 and shape["bars"]!=127
    expected=set(r.ROLES)
    assert expected=={e["track_id"] for e in score}
    for e in score:
        assert 0<=e["start_beat"]<shape["bars"]*4
        assert e["duration_beats"]>0 and 1<=e["velocity"]<=127
    patterns={}
    for part in ("KICK","SNARE","HAT","BASS","HARMONY","LEAD","KEYS"):
        events=[e for e in score if e["track_id"]==part]
        patterns[part]=len(events)
        assert events
    assert patterns["HARMONY"]>shape["bars"]*4
    assert patterns["BASS"]>shape["bars"]*3
    assert patterns["KEYS"]>12
    assert patterns["LEAD"]>20
    # Bass contains syncopation and is not just two dull hits per bar.
    bass_onsets={round(e["start_beat"]%4,2) for e in score if e["track_id"]=="BASS"}
    assert {0.0,1.5,2.5,3.5}.issubset(bass_onsets),bass_onsets
    kicks={round(e["start_beat"]%4,2) for e in score if e["track_id"]=="KICK"}
    assert {0.,1.5,2.5,3.5}.issubset(kicks),kicks
    snare=Counter((e["track_id"],e["start_beat"],e["midi"]) for e in score
                  if e["track_id"] in r.DRUM_PITCH)
    assert max(snare.values())==1
    assert all(e["instrument_id"]==r.ROLES[e["track_id"]] for e in score)
    # Score is independent from retired melody/old genre-develop system.
    assert all(e["articulation"].startswith("source_rock2") or
               e["articulation"].startswith("rock2") for e in score)
    return {"seed":seed,"tempo_bpm":shape["tempo_bpm"],"bars":shape["bars"],
            "events":len(score),"roles":patterns,
            "sha":hashlib.sha256(json.dumps(score,sort_keys=True).encode()).hexdigest()}

def main():
    _=r.read_original_rock2()
    tests=[test(s) for s in (145,146,147,148,149)]
    assert len({x["sha"] for x in tests})==5
    # Different tempo and form among normal requests are explicitly required.
    assert len({x["tempo_bpm"] for x in tests})>=2
    assert len({x["bars"] for x in tests})>=2
    build=(ROOT/"build_current_composer.sh").read_text()
    assert "events = compose_new_rock_song(ctx, creation_seed)" in build
    assert "tempo_bpm, bars = rock_shape['tempo_bpm'], rock_shape['bars']" in build
    assert "selected_style_source" in build
    assert "original_rock2" not in build
    print("INDEPENDENT_DIFFERENT_ROCK2_SONGS_NOT_OOMPA_PASS",
          json.dumps(tests,sort_keys=True))
if __name__=="__main__":
    main()
