"""Read-only validation of every separate per-genre draft mix reference."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
index=json.loads((ROOT/"index.json").read_text())
assert index["profile_count"]==55
assert len(index["genre_to_file"])==55
assert len(set(index["genre_to_file"].values()))==55
for genre,filename in index["genre_to_file"].items():
    p=json.loads((ROOT/filename).read_text())
    assert p["genre"]==genre
    assert p["actual_source_wav_sfz_files_must_remain_unchanged"] is True
    assert p["auto_apply"] is False
    ids=[r["track_id"] for r in p["individual_instrument_tracks"]]
    assert len(ids)==len(set(ids)) and ids
    assert all(r["source_is_read_only"] is True for r in p["individual_instrument_tracks"])
    if genre=="ROCK":
        assert len(ids)==9
        assert all("existing_gain_trim_db" in item for item in p["individual_instrument_tracks"])
    elif genre=="Jazz Ballad":
        assert len(ids)==6
        levels={r["track_id"]:r["proposed_relative_active_level_db"] for r in p["individual_instrument_tracks"]}
        assert levels=={"HARMONY":0,"LEAD":0,"BASS":-3,"KICK":8,"SNARE":-22,"HAT":-7}
    else:
        assert p["profile_status"]=="DRAFT_SUGGESTED_RATIOS_NOT_DEPLOYED"
        assert all(isinstance(item["proposed_relative_active_level_db"],(int,float))
                   for item in p["individual_instrument_tracks"])
        if p["pending_drum_source_splits"]:
            assert {"KICK","SNARE","HAT"}<=set(ids)
            for item in p["individual_instrument_tracks"]:
                if item["track_id"] in ("KICK","SNARE","HAT"):
                    assert item["instrument_id"] is None
print("ALL_55_SEPARATE_GENRE_PROFILE_FILES_VALIDATED")
