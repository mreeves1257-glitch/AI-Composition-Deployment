"""Validate the ORIGINAL Composer generates a *new* score by default.

Both normal and quick/test compose modes must change even if history resets.
Controlled A/B can still request an explicit creation_seed and replay exactly.
This inspects the real preserved Python Composer adapter, not simulated music.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT/"research"))
sys.path.insert(0,str(PROJECT/"composer_overrides"))
from verify_composer_to_midi_wiring_step01_20261009 import extract_original_runtime
from enable_fresh_song_seed import install, OLD, NEW, patch_source

def score_signature(result):
    if result.get("status")!="PASS" or not result.get("events"):
        raise AssertionError("COMPOSER_CREATED_NO_SCORE:"+str(result.get("status")))
    score=[(n["track_id"],n["instrument_id"],n["midi"],
            round(float(n["start_beat"]),4),round(float(n["duration_beats"]),4))
           for n in result["events"]]
    return hashlib.sha256(json.dumps(score,sort_keys=True).encode()).hexdigest()

def new_adapter(p,name):
    spec=importlib.util.spec_from_file_location(name,p)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def main():
    build=(PROJECT/"build_current_composer.sh").read_text()
    assert "from enable_fresh_song_seed import install as _install_fresh_song_seed" in build
    assert "_install_fresh_song_seed(adapter)" in build
    assert "if start_seed is None: start_seed = len(prior)" not in NEW

    with tempfile.TemporaryDirectory(prefix="composer-new-every-request-") as td:
        root=Path(td)
        extract_original_runtime(root)
        sys.path.insert(0,str(root))
        p=root/"AI_Comp_Genre_Execution_Adapter_002_WORKING_2026-10-02_184019_CDT.py"
        orig=p.read_text()
        assert orig.count(OLD)==1,"PRESERVED_CREATION_SEED_DEFAULT_DRIFTED"
        install(p)
        updated=p.read_text()
        assert NEW in updated and OLD not in updated
        assert updated.replace(NEW,OLD)==orig,"COMPOSER_OTHER_THAN_SEED_CHANGED"

        a=new_adapter(p,"actual_original_composer_with_fresh_song_default")
        per_mode={}
        for mode in ("normal","quick"):
            scores=[]
            seeds=[]
            # Artificially empty new history each time: simulates fresh server
            # and testing which used to replay seed=0.
            for i in range(3):
                fresh_history=root/("empty_history_"+mode+"_"+str(i)+".json")
                composer=a.GenreExecutionAdapter(history_path=fresh_history)
                created=composer.create_new("ROCK",mode=mode,remember=False)
                scores.append(score_signature(created))
                seeds.append(created["creation_seed"])
                assert not fresh_history.exists(),"TEST_REMEMBER_FALSE_WRITES_HISTORY"
            assert len(set(scores))==3,"NEW_SONG_BUTTON_REPEATED_SCORE_"+mode.upper()
            assert len(set(seeds))==3,"NEW_SONG_BUTTON_REPEATED_SEED_"+mode.upper()
            per_mode[mode]={"unique_songs":len(set(scores)),
                            "seeds_different":True,
                            "fresh_empty_history_each_request":True}

        # Even if a user explicitly hits 'New' repeatedly within a session
        # and the persistent history isn't committed until the end, do not
        # regenerate the previous score.
        c=a.GenreExecutionAdapter(history_path=root/"shared_empty.json")
        consecutive=[c.create_new("ROCK",mode="normal",remember=False)
                     for _ in range(3)]
        assert len({score_signature(x) for x in consecutive})==3

        # Older QA procedures can still replay a known musical score on purpose
        # without changing default new-song behavior.
        d=a.GenreExecutionAdapter(history_path=root/"controlled.json")
        same1=d.resolve("ROCK",mode="normal",creation_seed=0)
        same2=d.resolve("ROCK",mode="normal",creation_seed=0)
        assert score_signature(same1)==score_signature(same2)

        print("COMPOSER_CREATES_NEW_MUSIC_BY_DEFAULT_PASS",json.dumps({
            "modes":per_mode,
            "consecutive_same_session_unique":True,
            "controlled_explicit_seed_still_repeatable":True,
            "composer": "ORIGINAL_PRESERVED_RUNTIME_WITH_DEFAULT_SEED_PATCH",
            "new_musical_events_checked":True,
            "no_sfz_or_mixer_changes":True,
            "live_deployed":False
        },sort_keys=True))

if __name__=="__main__":
    main()
