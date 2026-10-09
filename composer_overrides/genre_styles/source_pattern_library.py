"""Original seven-bar source-pattern seeds; ONE shared selector for 55 genres.

Patterns are provisional *authored music data* owned by the genre folders.
No manufacturer style files, paid/proprietary arrangements, or imported MMA
source are used. Instrument IDs here are role intentions until stage-3 source
programs are independently resolved. This does NOT produce authorized audio.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from .shared_interpreter_router import route_to_shared_interpreter, InterpreterConnectionError
from .shared_musical_grammar import compile_musical_plan, measure

ROOT=Path(__file__).resolve().parent
PACK_NAME="SOURCE_PATTERN_LIBRARY_R1.json"
SCHEMA="AI_COMP_GENRE_ORIGINAL_SOURCE_PATTERNS_R1"
SECTION_NAMES=("INTRO","VERSE_A","VERSE_RESPONSE","FILL",
               "CHORUS_B","CHORUS_RESPONSE","ENDING")
VARIATIONS=("INTRO","A1","A2","FILL","B1","B2","OUTRO")
REQUIREMENTS={
    "authoring_status":"ORIGINAL_PROJECT_SEED_NOT_AUDITIONED",
    "source_ownership":"ORIGINAL_PROJECT_AUTHORED_SYMBOLIC_SEED",
    "recorded_source_binding":"UNVERIFIED_NOT_CONNECTED"
}

def need(cond,reason):
    if not cond:raise InterpreterConnectionError(reason)

def read_pack(genre: str) -> tuple[dict,dict]:
    ref=route_to_shared_interpreter(genre)
    family=ref["family"]
    path=ROOT/family/PACK_NAME
    need(path.is_file(),"GENRE_SOURCE_PATTERN_PACK_MISSING:"+genre)
    root=json.loads(path.read_text(encoding="utf-8"))
    need(root.get("schema_version")==SCHEMA and
         root.get("family")==family and
         root.get("original_profile_files_unchanged") is True and
         root.get("audio_verified") is False,
         "GENRE_SOURCE_PATTERN_PACK_SCHEMA_MISMATCH:"+genre)
    records=root.get("genres")
    need(isinstance(records,list),"INVALID_SOURCE_PATTERN_ENTRIES")
    entry=[x for x in records if x.get("genre")==genre]
    need(len(entry)==1,"SOURCE_PATTERN_GENRE_NOT_UNIQUE:"+genre)
    obj=entry[0]
    for k,v in REQUIREMENTS.items():
        need(obj.get(k)==v,"INVALID_SOURCE_PATTERN_PROVENANCE:"+genre)
    need(obj.get("profile_id")==ref["genre_profile_id"],
         "SOURCE_PATTERN_PROFILE_ID_DRIFT:"+genre)
    need(obj.get("meter") in
         ref["genre_specific_musical_intentions"]["meter_options"],
         "SOURCE_PATTERN_UNSUPPORTED_METER:"+genre)
    tempo=obj.get("tempo_bpm")
    lo,hi=ref["genre_specific_musical_intentions"]["tempo_bpm_range"]
    need(type(tempo)==int and lo<=tempo<=hi,
         "SOURCE_PATTERN_UNSUPPORTED_TEMPO:"+genre)
    need(obj.get("sections") and len(obj["sections"])==7 and
         [x["name"] for x in obj["sections"]]==list(SECTION_NAMES) and
         all(s["bars"]==1 for s in obj["sections"]),
         "SOURCE_PATTERN_SECTIONS_NOT_SEVEN_VARIANTS:"+genre)
    need(len(obj.get("chords",[]))==7 and
         [x["bar"] for x in obj["chords"]]==list(range(7)),
         "SOURCE_PATTERN_HARMONY_NOT_SEVEN_BARS:"+genre)
    role_set={r["role"] for r in obj.get("roles",[])}
    need(role_set and len(role_set)==len(obj["roles"]),
         "SOURCE_PATTERN_ROLE_IDS_UNSAFE:"+genre)
    pats=obj.get("patterns",[])
    need(set(p["role"] for p in pats)==role_set and
         len(pats)==len(role_set),"SOURCE_PATTERN_MISSING_ROLE_PATTERN:"+genre)
    for s,variation in zip(obj["sections"],VARIATIONS):
        need(s.get("variation_by_role")=={r:variation for r in role_set},
             "SOURCE_PATTERN_UNALIGNED_SECTION_VARIATIONS:"+genre)
    for p in pats:
        need(set(p["variations"])==set(VARIATIONS) and
             p["kind"] in ("CHORD_RELATIVE","DRUM_ABSOLUTE","ABSOLUTE_MIDI"),
             "SOURCE_PATTERN_VARIATION_INCOMPLETE:"+genre)
        need(all(isinstance(v,list) for v in p["variations"].values()),
             "SOURCE_PATTERN_UNPLAYABLE_VARIANTS:"+genre)
    return obj,ref

def compile_original_source_seed(genre: str, *, selected_tempo_bpm: int|None=None) -> dict[str,Any]:
    """Compile original patterns at genre tempo or an explicit permitted Stage-3 tempo.

    Preserve the original source JSON unchanged. The selected tempo is the same
    authority consumed by the shared CAP_09 ensemble clock, not an independent
    DAW/playback tempo. Audio/production authorization remains false.
    """
    data,ref=read_pack(genre)
    if selected_tempo_bpm is not None:
        need(type(selected_tempo_bpm) is int and
             ref["genre_specific_musical_intentions"]["tempo_bpm_range"][0]
             <= selected_tempo_bpm <=
             ref["genre_specific_musical_intentions"]["tempo_bpm_range"][-1],
             "SOURCE_PATTERN_SELECTED_TEMPO_OUTSIDE_GENRE")
    chosen_tempo=(data["tempo_bpm"] if selected_tempo_bpm is None
                  else selected_tempo_bpm)
    plan=compile_musical_plan(
        genre,meter=data["meter"],tempo_bpm=chosen_tempo,bars=7,
        sections=data["sections"],chords=data["chords"],
        roles=data["roles"],patterns=data["patterns"])
    events=plan["symbolic_note_events"]
    need(events,"SOURCE_PATTERN_NO_INSTRUMENT_NOTES:"+genre)
    roles={e["role"] for e in events}
    need(roles=={x["role"] for x in data["roles"]},
         "SOURCE_PATTERN_SILENT_INSTRUMENT_ROLE:"+genre)
    need({x["section"] for x in events}==set(SECTION_NAMES),
         "SOURCE_PATTERN_SILENT_SECTION:"+genre)
    need(all(x["status"]=="SYMBOLIC_ONLY" for x in events),
         "SOURCE_PATTERN_UNAUTHORIZED_AUDIO")
    plan["source_pattern_contract"]={
        "schema":SCHEMA,
        "genre_specific_seed":genre,
        "genre_family":ref["family"],
        "seed_id":data["seed_id"],
        "source_pattern_file":str((ROOT/ref["family"]/PACK_NAME).relative_to(ROOT)),
        "authoring_status":data["authoring_status"],
        "source_ownership":data["source_ownership"],
        "role_ids":list(roles),
        "played_section_sequence":list(SECTION_NAMES),
        "original_seed_tempo_bpm":data["tempo_bpm"],
        "selected_stage3_tempo_bpm":chosen_tempo,
        "tempo_origin":("GENRE_SOURCE_DEFAULT" if selected_tempo_bpm is None
                        else "EXPLICIT_STAGE3_ENSEMBLE_CLOCK"),
        "recorded_instruments_verified":False,
        "musical_audition_approved":False,
        "production_enabled":False}
    return plan
