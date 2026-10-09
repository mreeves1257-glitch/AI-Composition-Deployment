"""Prove genuine external style-program output enters its OWN genre interpreter.

Public GPL MMA remains a standalone program. Project-owned individual
Jazz Waltz and Salsa translators produce typed score events, NOT sampled WAVs.
This preserves all original audio, the seven-stage Composer, and 3D mixer.
"""
from __future__ import annotations
from pathlib import Path
import json,sys,zipfile,hashlib
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"composer_overrides"))
from genre_styles.Jazz.jazz_waltz_genre_interpreter import (
    interpret_genre as jazz_waltz)
from genre_styles.Latin.salsa_genre_interpreter import (
    interpret_genre as salsa)
from genre_styles.external_style_midi_reader import StyleMidiInterfaceError
from genre_styles.genre_owned_interpreter_dispatch import dispatch_stage3_to4_genre_owned

OUT=ROOT/"research_artifacts"/"two_unique_genre_interpreter_proofs_20261009"

def must(flag,why):
    if not flag:raise AssertionError(why)

def run(jazz_path,salsa_path):
    j=jazz_waltz(jazz_path,selected_genre="Jazz Waltz")
    s=salsa(salsa_path,selected_genre="Salsa")
    jazz_stage3={"status":"PASS","palette":["double_bass","piano","drums"],
                 "meter":"3/4","tempo_bpm":156}
    salsa_stage3={"status":"PASS","palette":["bass","piano","latin percussion"],
                  "meter":"4/4","tempo_bpm":190}
    jazz_handoff=dispatch_stage3_to4_genre_owned(
        "Jazz Waltz",source_midi_path=jazz_path,
        original_stage3_result=jazz_stage3)
    salsa_handoff=dispatch_stage3_to4_genre_owned(
        "Salsa",source_midi_path=salsa_path,
        original_stage3_result=salsa_stage3)
    must(jazz_handoff["musical_event_count"]==j["event_count"] and
         jazz_handoff["stage4_candidate_events"]==j["actual_music_events"] and
         jazz_handoff["stage3_clock_verified"]["meter"]=="3/4",
         "JAZZ_WALTZ_NOT_DIRECTED_FROM_OWN_INTERPRETER")
    must(salsa_handoff["musical_event_count"]==s["event_count"] and
         salsa_handoff["stage4_candidate_events"]==s["actual_music_events"] and
         salsa_handoff["stage3_clock_verified"]["meter"]=="4/4",
         "SALSA_NOT_DIRECTED_FROM_OWN_INTERPRETER")
    waiting=dispatch_stage3_to4_genre_owned(
        "Swing",source_midi_path=jazz_path,
        original_stage3_result={"status":"PASS","palette":["piano"],
                                "meter":"4/4","tempo_bpm":160})
    must(waiting["status"]=="BLOCKED_GENRE_OWNED_BACKEND_NOT_YET_IMPLEMENTED" and
         waiting["musical_event_count"]==0,
         "NONIMPLEMENTED_GENRE_FAKED_A_SONG")
    for name,stage3,midi in [
        ("Jazz Waltz",{"status":"PASS","palette":["double_bass"],"meter":"4/4","tempo_bpm":156},jazz_path),
        ("Salsa",{"status":"PASS","palette":["piano"],"meter":"3/4","tempo_bpm":190},salsa_path)]:
        try:dispatch_stage3_to4_genre_owned(
            name,source_midi_path=midi,original_stage3_result=stage3)
        except StyleMidiInterfaceError as e:
            must("STAGE3_CLOCK_MISMATCH" in str(e),
                 "WRONG_INTERPRETER_FAILURE_REASON")
        else:raise AssertionError("WRONG_GENRE_CLOCK_ACCEPTED:"+name)
    must(j["genre"]=="Jazz Waltz" and j["meter"]=="3/4" and
         j["tempo_bpm"]==156 and j["bars"]==8,
         "JAZZ_WALTZ_INTERPRETER_NOT_3_4")
    must(s["genre"]=="Salsa" and s["meter"]=="4/4" and
         s["tempo_bpm"]==190 and s["bars"]==8,
         "SALSA_INTERPRETER_NOT_4_4")
    must(j["event_count"]>=150 and s["event_count"]>=250,
         "STYLE_PROGRAM_DID_NOT_GENERATE_REAL_ENOUGH_EVENTS")
    must(j["event_count"]!=s["event_count"] and
         j["source_track_roles"]!=s["source_track_roles"],
         "TWO_STYLE_PROGRAMS_SHOULD_NOT_HAVE_IDENTICAL_PATTERNS")
    must(j["source_percussion_note_classes"]["RIDE_CYMBAL"]>0 and
         j["jazz_3_4_walking_bass_and_ride_verified"],
         "JAZZ_WALTZ_RIDE_AND_BASS_NOT_PERFORMED")
    must(s["latin_percussion_roles"]["CLAVES"]>0 and
         s["latin_percussion_roles"]["LOW_BONGO"]>0 and
         s["two_bar_clave_periodicity_observed"] and
         not s["exact_2_3_vs_3_2_clave_orientation_verified"],
         "SALSA_CLAVE_SOURCE_CYCLE_NOT_DISTINCT")
    for label,score in (("jazz_waltz",j),("salsa",s)):
        must(score["distinct_style_language_executed"] is True and
             score["audio_render_authorized"] is False and
             score["production_enabled"] is False and
             score["native_recorded_programs_mapped"] is False and
             score["live_composer_events_replaced"] is False,
             "FALSE_CLAIM_SOURCE_PROGRAM_IS_RECORDED_MUSIC:"+label)
        must(all(e["real_SFZ_sample_program_verified"] is False and
                 e["stage4_status"]=="INTERPRETED_SOURCE_NOTE_NOT_AUTHORIZED_FOR_AUDIO"
                 for e in score["actual_music_events"]),
             "SOURCE_SAMPLE_MAPPING_FABRICATED:"+label)
    def rejected(f,source,expected,wrong):
        try:f(source,selected_genre=wrong)
        except StyleMidiInterfaceError as e:
            must("CROSS_GENRE_FORBIDDEN" in str(e),
                 "CROSS_GENRE_REJECTED_FOR_WRONG_REASON")
        else:raise AssertionError("CROSS_GENRE_STYLE_FALLBACK_ALLOWED:"+expected)
    rejected(jazz_waltz,jazz_path,"Jazz Waltz","Salsa")
    rejected(salsa,salsa_path,"Salsa","Jazz Waltz")
    try:jazz_waltz(salsa_path)
    except StyleMidiInterfaceError as e:must("WRONG_GENRE_METER" in str(e),"JAZZ_METER_CROSSOVER_GUARD_WRONG")
    else:raise AssertionError("SALSA_ROUTED_AS_JAZZ_WALTZ")
    try:salsa(jazz_path)
    except StyleMidiInterfaceError as e:must("WRONG_GENRE_METER" in str(e),"SALSA_METER_CROSSOVER_GUARD_WRONG")
    else:raise AssertionError("JAZZ_ROUTED_AS_SALSA")
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"Jazz_Waltz_8_Bar_Interpreted_Stage4_Source_Notes.json").write_text(json.dumps(j,indent=2)+"\n")
    (OUT/"Salsa_8_Bar_Interpreted_Stage4_Source_Notes.json").write_text(json.dumps(s,indent=2)+"\n")
    evidence={"status":"GENRE_OWNED_INTERPRETER_EXECUTION_VERIFIED_NOT_AUDIO_APPROVED",
          "separately_licensed_software":"OFFICIAL_MMA_25.05.0_GPLv2",
          "original_generated_style_files":["lib/stdlib/jazzwaltz.mma","lib/stdlib/salsa.mma"],
          "jazz":{"tempo":156,"meter":"3/4","events":j["event_count"],
                  "tracks":j["source_track_roles"]},
          "salsa":{"tempo":190,"meter":"4/4","events":s["event_count"],
                   "tracks":s["source_track_roles"],
                   "percussion":s["latin_percussion_roles"]},
          "per_genre_music_interpretation_engines_functional":True,
          "stage3_to4_genre_dispatch_worked_without_generic_fallback":True,
          "real_SFZ_programs_installed_or_verified_for_these_genres":False,
          "genre_audition_approval":False,"live_composer_activated":False,
          "original_rock_interpreter_or_frozen_hard_copy_changed":False}
    (OUT/"PROOF_MANIFEST.json").write_text(json.dumps(evidence,indent=2)+"\n")
    (OUT/"README.txt").write_text(
       "JAZZ WALTZ and SALSA: 2 distinct independently executing musical interpreters\n"
       "from official separately licensed MMA style programs. These are typed\n"
       "source MIDI events. They are NOT mapped to native recorded SFZ programs,\n"
       "are NOT finished audio, and are NOT activated in the live Composer.\n"
       "3/4 Jazz ride/walking bass MUST NOT become 4/4 Salsa/clave;\n"
       "Latin claves/guiro/cowbell/bongo are NOT Rock drums. License audit\n"
       "and source sound mapping remain required before any audio rendering.\n")
    archive=OUT.parent/"TWO_ACTUAL_GENRE_SPECIFIC_INTERPRETERS_JAZZ_WALTZ_SALSA_2026-10-09.zip"
    with zipfile.ZipFile(archive,"w",compression=zipfile.ZIP_DEFLATED) as z:
        for f in sorted(OUT.iterdir()):
            z.write(f,f.name)
    must(archive.stat().st_size>1000,"EMPTY_PROOF_ARCHIVE")
    print("TWO_ACTUAL_DISTINCT_GENRE_MUSICAL_INTERPRETERS_PASS",
          json.dumps({**evidence,"bytes":archive.stat().st_size},sort_keys=True))

if __name__=="__main__":
    must(len(sys.argv)==3,"USAGE: test_script.py jazzwaltz.mid salsa.mid")
    run(sys.argv[1],sys.argv[2])
