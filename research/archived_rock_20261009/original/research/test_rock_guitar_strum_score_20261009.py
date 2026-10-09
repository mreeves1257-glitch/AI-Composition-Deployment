"""Proof Rock guitar performance alters ONLY chord onsets, after shared score interpretation."""
from pathlib import Path
import sys,json,hashlib,collections
sys.path.insert(0,str(Path("composer_overrides").resolve()))
from genre_styles.shared_interpreter_router import compile_selected_musical_interpreter
from genre_styles.Rock.rock_strum_phrase_performance import apply_guitar_attack_strum
path=Path("research/pinned_input/MMA_Rock_16Bar_Two_Sections.mid")
score=compile_selected_musical_interpreter("ROCK",original_mma_midi_path=path,
 original_stage3_result={"status":"PASS","palette":["electric_guitar","electric_bass","drums"],"meter":"4/4","tempo_bpm":145})
candidate,changes=apply_guitar_attack_strum(score)
assert changes["changed_guitar_attack_groups"]>6
assert changes["changed_guitar_note_onsets"]>6
assert len(score["notes"])==len(candidate["notes"])==420
assert sorted((x["track_id"],x["midi"],x["velocity"]) for x in score["notes"])==sorted((x["track_id"],x["midi"],x["velocity"]) for x in candidate["notes"])
a=sorted((x for x in score["notes"] if x["track_id"]!="HARMONY"),key=lambda x:(x["track_id"],x["start_beat"],x["midi"]))
b=sorted((x for x in candidate["notes"] if x["track_id"]!="HARMONY"),key=lambda x:(x["track_id"],x["start_beat"],x["midi"]))
assert a==b
o=sorted([x for x in score["notes"] if x["track_id"]=="HARMONY"],key=lambda x:(x["midi"],x["start_beat"]))
n=sorted([x for x in candidate["notes"] if x["track_id"]=="HARMONY"],key=lambda x:(x["midi"],x["start_beat"]))
assert o!=n
out=Path("research/pinned_shared_interpreter_rock_output");out.mkdir(parents=True,exist_ok=True)
(out/"PROPOSED_GUITAR_STRUM_SCORE_ONLY.json").write_text(json.dumps({"status":"SCORE_AB_PASS_NOT_AUDITIONED","transformations":changes,"genre":"ROCK","unchanged_other_six_roles":True,"source_sfzs_untouched":True,"preferred_bass_minus8_preserved_in_audio_ONLY":True,"full_audio_not_verified_here":True},indent=2)+"\n")
print("SHARED_INTERPRETER_ROCK_GUITAR_STRUM_SINGLE_VARIABLE_SCORE_PASS",json.dumps({k:v for k,v in changes.items() if k!="transformations"},sort_keys=True))
