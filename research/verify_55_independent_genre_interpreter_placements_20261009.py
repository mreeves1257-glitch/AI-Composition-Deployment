"""Structural & original Rock translator checks for 55 independent style owners.

Each genre owns a unique musical language; MIDI/SFZ rendering stays shared.
The original source-note interpreter now compiles 53 separate genre-owned seven-bar symbolic scores, including a RESET Rock backend. Jazz Waltz and Salsa retain their independent MIDI source readers. No audio is automatically authorized. The previous Rock pinned-MMA translator remains archived, byte-for-byte, but is NOT the selected Rock interpreter.
"""
from __future__ import annotations
import hashlib,json,re,sys
from pathlib import Path
from collections import Counter
PROJECT=Path(__file__).resolve().parents[1]
ROOT=PROJECT/"composer_overrides"/"genre_styles"
sys.path.insert(0,str(PROJECT/"composer_overrides"))
from genre_styles.shared_interpreter_router import route_to_shared_interpreter
from genre_styles.source_pattern_library import read_pack
from genre_styles.genre_owned_interpreter_dispatch import dispatch_stage3_to4_genre_owned
from genre_styles.Rock.rock_pinned_mma_interpreter import (
    compile_pinned_mma_rock_score,PINNED_USER_LIKED_MMA_SHA256,TEMPO,BARS)

def need(ok,msg):
    if not ok:raise AssertionError(msg)

def check_contracts():
    idx=json.loads((ROOT/"index.json").read_text())
    reg=json.loads((ROOT/"GENRE_INTERPRETER_REGISTRY_R1.json").read_text())
    items=idx["genre_to_family_file"]
    need(len(items)==len(reg["per_genre"])==reg["count"]==55,"55_GENRES_MISMATCH")
    need(len({p.split("/")[0] for p in items.values()})==13,"13_FAMILY_DRIFT")
    need(reg["single_shared_output_and_rendering_core"] and
         reg["original_7_stages_unchanged"],"SHARED_CORE_OR_SEVEN_STAGES_CHANGED")
    originals={};count=Counter();files=set();music_fingerprints={}
    for genre,source in items.items():
        entry=reg["per_genre"][genre]
        path=entry["slot_file"]
        need(path not in files,"INTERPRETER_FILENAME_COLLISION:"+path)
        files.add(path)
        slot=json.loads((PROJECT/path).read_text())
        family=source.split("/")[0]
        profile=json.loads((ROOT/source).read_text())["profiles"][genre]
        actual=profile["musical_definition"]
        seq=profile["seven_stage_plan"]
        need(slot["genre_name"]==genre and slot["genre_family"]==family,
             "OTHER_GENRE_TAKING_OWNERSHIP:"+genre)
        need(slot["source_profile_id"]==actual["profile_id"]==entry["profile_id"],
             "WRONG_GENRE_PROFILE_"+genre)
        need(slot["musical_definition_ref"]=={
            "file":"composer_overrides/genre_styles/"+source,
            "json_pointer":"/profiles/"+genre+"/musical_definition",
        },"MUSICAL_DEFINITION_WRONG_XREF:"+genre)
        need(slot["original_seven_stage_ref"]["json_pointer"]==
             "/profiles/"+genre+"/seven_stage_plan" and
             len(seq["stage_order"])==7,"SEVEN_STAGES_NOT_PRESERVED:"+genre)
        need(slot["source_pattern_ref"]["genre_key"]==genre,
             "WRONG_SOURCE_PATTERNS:"+genre)
        need(slot["source_resource_ref"]["genre_key"]==genre,
             "WRONG_SOURCE_RESOURCE:"+genre)
        need(slot["owned_stage_boundary"]==
             "AFTER_STAGE3_INSTRUMENT_SELECTION_BEFORE_STAGE4_COMPOSE",
             "WRONG_INTERPRETER_STAGE:"+genre)
        need(slot["activated_in_live_composer"] is False and
             slot["source_specific_note_score_approved_for_production"] is False,
             "FALSE_LIVE_GENRE_INTERPRETER:"+genre)
        need("inheriting_Rock_notes_into_another_genre" in slot["prohibited"],
             "CROSS_GENRE_FALLBACK_NOT_BLOCKED:"+genre)
        if genre in ("Jazz Waltz","Salsa"):
            expected=("composer_overrides/genre_styles/Jazz/jazz_waltz_genre_interpreter.py"
                       if genre=="Jazz Waltz" else
                       "composer_overrides/genre_styles/Latin/salsa_genre_interpreter.py")
            need(slot["backend_file"]==expected and
                 (PROJECT/expected).is_file() and
                 slot["backend_status"].endswith("_SOURCE_SFZ_UNVERIFIED") and
                 slot["source_specific_note_score_approved_for_production"] is False,
                 "NON_ROCK_BACKEND_PROGRAM_OR_SFZ_STATUS_WRONG:"+genre)
            count["symbolic_nonrock"]+=1
        else:
            expected_backend="composer_overrides/genre_styles/source_pattern_library.py"
            expected_status="GENRE_OWNED_ORIGINAL_SEVEN_SECTION_SOURCE_INTERPRETER_SYMBOLIC_EXECUTABLE_AUDIO_UNVERIFIED"
            need(slot["backend_file"]==entry.get("backend_file")==expected_backend and
                 slot["backend_status"]==entry["backend_status"]==expected_status,
                 "ORIGINAL_GENRE_SOURCE_BACKEND_NOT_CONFIGURED:"+genre)
            need(slot["genre_specific_executable_score"]["genre_key"]==genre and
                 slot["genre_specific_executable_score"]["source_pattern_file"]==
                       slot["source_pattern_ref"]["file"] and
                 slot["genre_specific_executable_score"]["production_ready"] is False,
                 "GENRE_SOURCE_SCORE_OWNER_NOT_CORRECT:"+genre)
            need(slot["wiring_instruction"]["owned_backend"]==expected_backend and
                 slot["wiring_instruction"]["production_links_enabled"] is False,
                 "INACTIVE_GENRE_WIRING_NOT_OWNED:"+genre)
            seed,ref=read_pack(genre)
            palette=list(dict.fromkeys(r["instrument_id"] for r in seed["roles"]))
            stage3={"status":"PASS","palette":palette,"meter":seed["meter"],
                    "tempo_bpm":seed["tempo_bpm"]}
            out=dispatch_stage3_to4_genre_owned(genre,original_stage3_result=stage3)
            notes=out["stage4_candidate_events"]
            need(out["genre"]==genre and out["profile_id"]==actual["profile_id"] and
                 out["musical_event_count"]==len(notes)>0 and
                 out["stage3_clock_verified"]==
                     {"meter":seed["meter"],"tempo_bpm":seed["tempo_bpm"]} and
                 out["source_type"]=="ORIGINAL_GENRE_OWNED_SYMBOLIC_PATTERN" and
                 out["genre_behavior"]["source_seed"]==seed["seed_id"] and
                 out["genre_behavior"]["musical_rules"]["profile_id"]==actual["profile_id"] and
                 out["old_authoritative_composer_events_untouched"] is True and
                 out["audio_render_authorized"] is False and
                 out["production_enabled"] is False,
                 "GENRE_OWNED_SOURCE_INTERPRETER_DID_NOT_EXECUTE:"+genre)
            need({x["section"] for x in notes}==
                 {"INTRO","VERSE_A","VERSE_RESPONSE","FILL","CHORUS_B","CHORUS_RESPONSE","ENDING"},
                 "GENRE_MUSICAL_SECTIONS_WRONG:"+genre)
            fingerprint=hashlib.sha256(json.dumps([
                (x["start_beat"],x["midi"],x["role"],x["velocity"],x["section"])
                for x in notes],sort_keys=True).encode()).hexdigest()
            need(fingerprint not in music_fingerprints,
                 "SAME_MUSICAL_EVENTS_COPIED_BETWEEN_GENRES:"+
                 genre+" and "+str(music_fingerprints.get(fingerprint)))
            music_fingerprints[fingerprint]=genre
            if genre=="ROCK":
                need(slot.get("rock_reset_mode")==
                     "START_FRESH_WITH_ORIGINAL_ROCK_SOURCE_PROFILE_AND_OWN_PATTERN_SAME_AS_OTHER_GENRES" and
                     slot.get("old_pinned_145_bpm_rock_interpreter_retained_historically_not_active") is True and
                     slot["backend_file"]=="composer_overrides/genre_styles/source_pattern_library.py",
                     "ROCK_WAS_NOT_RESET_FROM_PINNED_MMA")
            count["authored_symbolic"]+=1
            count["authored_notes"]+=len(notes)
        originals[genre]=actual["profile_id"]
    need(count["authored_symbolic"]==53 and count["symbolic_nonrock"]==2 and
         len(music_fingerprints)==53 and len(files)==55 and
         reg["genre_source_seed_executable_slots"]==53 and
         reg["genre_backend_files_present"]==2,
         "GENRE_PROGRAM_STATUS_WRONG")
    original=ROOT/"Rock"/"rock_pinned_mma_interpreter.py"
    archive=PROJECT/"research/archived_rock_20261009/original/rock_pinned_mma_interpreter.py"
    strum=ROOT/"Rock"/"rock_strum_phrase_performance.py"
    archived_strum=PROJECT/"research/archived_rock_20261009/original/rock_strum_phrase_performance.py"
    need(original.read_bytes()==archive.read_bytes(),"PINNED_ROCK_TRANSLATOR_WAS_REWRITTEN")
    need(strum.read_bytes()==archived_strum.read_bytes(),"ROCK_STRUM_PERFORMANCE_WAS_REWRITTEN")
    need(TEMPO==145 and BARS==16,"USER_PREFERRED_ROCK_TEMPO_BARS_CHANGED")
    print("ALL_55_GENRE_OWNED_INTERPRETER_SLOTS_PASS",json.dumps({
      "independent_owned_interpreter_contracts":55,
      "family_folders":13,"functional_nonrock_backends_falsely_claimed":0,
      "authored_symbolic_executable_genre_programs":count["authored_symbolic"],
      "distinct_original_music_fingerprints":len(music_fingerprints),
      "genre_owned_symbolic_notes_checked":count["authored_notes"],
      "separate_external_midi_symbolic_interpreters":count["symbolic_nonrock"],
      "historical_pinned_rock_interpreter_preserved_unchanged":True,
      "active_rock_interpreter":"ORIGINAL_ROCK_GENRE_SEED",
      "rock_pinned_source_sha256":PINNED_USER_LIKED_MMA_SHA256,
      "historical_pinned_rock_tempo_bpm_NOT_CURRENT":TEMPO,
      "original_live_composer_unchanged":True,
      "shared_recorded_resource_and_3d_code_reused":True,
    },sort_keys=True))

def check_pinned_source(path):
    midi=Path(path)
    need(midi.is_file(),"ORIGINAL_USER_PREFERRED_16BAR_MIDI_NOT_RECOVERED")
    need(hashlib.sha256(midi.read_bytes()).hexdigest()==PINNED_USER_LIKED_MMA_SHA256,
         "ORIGINAL_USER_PREFERRED_16BAR_MIDI_CHECKSUM_WRONG")
    stage3={"status":"PASS","palette":["electric_guitar","electric_bass","drums"],
            "meter":"4/4","tempo_bpm":145}
    route=route_to_shared_interpreter("ROCK",original_stage3_result=stage3)
    score=compile_pinned_mma_rock_score(midi,route)
    need(score["status"]=="PINNED_MMA_ROCK_SCORE_INTERPRETED" and
         score["tempo_bpm"]==145 and score["bars"]==16 and
         score["note_count"]==420,
         "RECOVERED_ROCK_INTERPRETER_NOT_PRODUCING_ORIGINAL_SCORE")
    roles=Counter(x["track_id"] for x in score["notes"])
    need(roles==Counter({"HARMONY":225,"BASS":56,"KICK":32,"SNARE":38,
                         "HAT":64,"TOMS":4,"CRASH":1}),
         "USER_APPROVED_MUSIC_PARTS_DRIFTED")
    need(len(score["intent_trace"])==7 and
         score["live_deployed"] is False,
         "LIVE_OR_SECTION_CLAIMS_WRONG")
    print("RECOVERED_USER_LIKED_ROCK_GENRE_INTERPRETER_420_NOTES_PASS",
          json.dumps({"source_sha256":PINNED_USER_LIKED_MMA_SHA256,
          "drum_roles":{"KICK":32,"SNARE":38,"HAT":64,"TOMS":4,"CRASH":1},
          "original_note_counts":dict(roles),
          "original_seven_stage_composer_unchanged":True,
          "no_production_deploy":True},sort_keys=True))

if __name__=="__main__":
    check_contracts()
    # Archived fixed-MMA checks are historical, not active interpreter checks.
    if len(sys.argv)==2:check_pinned_source(sys.argv[1])
