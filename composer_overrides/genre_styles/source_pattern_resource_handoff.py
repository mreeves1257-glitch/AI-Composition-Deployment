"""One genre-neutral source-pattern role -> exact recorded SFZ identity resolver.

Never substitutes instruments. Only pinned IDs present in the real preserved
Composer builder or exact manifest can be named as source candidates.
The existence of registry metadata is NOT proof of installed SFZ samples,
key ranges, note-off lifetime, MIDI behavior or audible rendered stems.
All 55 genres use the same resolver, each with its own family binding XRefs.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Mapping
from .shared_interpreter_router import route_to_shared_interpreter, InterpreterConnectionError

ROOT=Path(__file__).resolve().parent
FILE="SOURCE_RESOURCE_BINDINGS_R1.json"
SCHEMA="AI_COMP_SOURCE_PATTERN_EXACT_INSTRUMENT_BINDINGS_R1"
# IDs and programs observed in the preserved build_current_composer.sh script.
# A declared program is not automatically installed, validated or auditioned.
PINNED={
 "electric_bass_guitar":("KARORYFER_GROWLYBASS_V1_002","growlybass_clean.sfz"),
 "electric_piano":("GREG_SULLIVAN_E_PIANOS","Wurlitzer EP200/composer-wurlitzer.sfz"),
 "kick_drum_rock":("KARORYFER_BIG_RUSTY_DRUMS","Programs/composer-kick-lite.sfz"),
 "snare_drum":("KARORYFER_BIG_RUSTY_DRUMS","Programs/composer-snare-lite.sfz"),
 "hi_hat":("KARORYFER_BIG_RUSTY_DRUMS","Programs/composer-hihat-lite.sfz"),
 "ride_cymbal":("KARORYFER_BIG_RUSTY_DRUMS","Programs/composer-ride-lite.sfz"),
 "crash_cymbal":("KARORYFER_BIG_RUSTY_DRUMS","Programs/composer-crash-lite.sfz"),
 "tom_tom":("KARORYFER_BIG_RUSTY_DRUMS","Programs/composer-tom-lite.sfz"),
 "conga":("FREEPATS_WORLD_PERCUSSION","composer-conga-five-strokes.sfz")
}
# Source authority taken from composer_overrides/production_resource_policy.py.
# Never accept a lookalike SFZ program with a changed bank or license.
ORIGINAL_SOURCE_PROVENANCE={
 "KARORYFER_GROWLYBASS_V1_002":("Karoryfer Growlybass","CC0"),
 "KARORYFER_SHINYGUITAR":("Karoryfer Shinyguitar","CC0-1.0"),
 "KARORYFER_BIG_RUSTY_DRUMS":("Karoryfer Big Rusty Drums","CC0-1.0"),
 "GREG_SULLIVAN_E_PIANOS":("Greg Sullivan E-Pianos / Wurlitzer EP200","CC-BY-3.0"),
 "FREEPATS_WORLD_PERCUSSION":("FreePats World Percussion","CC0-1.0"),
}
CONTEXT_PINNED={
 # Explicit authoring choice on ROCK harmony. This is *not* a fallback for
 # other genre electric guitars, acoustic guitars, or leads.
 ("ROCK","HARMONY","electric_guitar"):
   ("electric_guitar:RHYTHM_POWER_CHORDS",
    "KARORYFER_SHINYGUITAR","Programs/composer-electric.sfz")
}
EXACT_PERCUSSION_NOTES={"kick_drum_rock":(36,),
 "snare_drum":(38,), "hi_hat":(42,), "ride_cymbal":(51,),
 "crash_cymbal":(49,), "tom_tom":tuple(range(41,48)),
 "conga":tuple(range(60,65))}
PER_GENRE_DRUMS_ALLOWED={"ROCK":frozenset({"kick_drum_rock","snare_drum","hi_hat"})}
# Only identity aliases documented in the preserved runtime builder.
REGISTERED_PALETTE_ALIASES={"electric_bass_guitar":("electric_bass",)}

def require(cond: bool, code: str) -> None:
    if not cond: raise InterpreterConnectionError(code)

def load_installed_registry(path: str|Path|None=None) -> dict:
    """Read original Composer target bindings; fail closed if unavailable."""
    if path is None:
        path=ROOT.parent/"target_registry.json"
    p=Path(path)
    if not p.is_file():return {}
    try:
        data=json.loads(p.read_text(encoding="utf-8"))
        return dict(data["targets"]["INTERNAL"]["instrument_bindings"])
    except (OSError,KeyError,ValueError,TypeError) as exc:
        raise InterpreterConnectionError("INSTALLED_TARGET_REGISTRY_INVALID") from exc

def load_binding_file(genre: str) -> tuple[dict,dict]:
    ref=route_to_shared_interpreter(genre)
    p=ROOT/ref["family"]/FILE
    require(p.is_file(),"SOURCE_BINDING_FILE_MISSING:"+genre)
    data=json.loads(p.read_text(encoding="utf-8"))
    require(data.get("schema_version")==SCHEMA and
            data.get("family")==ref["family"] and
            data.get("live_audio_enabled") is False,
            "SOURCE_BINDING_FILE_INVALID:"+genre)
    matches=[r for r in data.get("genres",[]) if r.get("genre")==genre]
    require(len(matches)==1 and
            matches[0].get("profile_id")==ref["genre_profile_id"],
            "SOURCE_BINDING_PROFILE_MISMATCH:"+genre)
    return matches[0],ref

def map_source_roles(
    seed: Mapping[str,Any], *, stage3: Mapping[str,Any]|None=None,
    target_bindings: Mapping[str,Any]|None=None,
) -> dict:
    """Resolve roles to exact declared source programs, with hard blockers.

    Does not infer sample key zones or falsely validate rendered audio. Exact
    selected source banks require independent SFZ/sample and stem preflight.
    """
    genre=seed["genre"]
    entry,ref=load_binding_file(genre)
    original_roles=seed["roles"]
    require({r["role"] for r in original_roles}==set(entry["role_bindings"]) and
            len(original_roles)==len(entry["role_bindings"]),
            "SOURCE_ROLE_LIST_CHANGED:"+genre)
    if stage3 is not None:
        require(stage3.get("status")=="PASS","SOURCE_STAGE3_NOT_READY")
        selection=stage3.get("palette")
        require(isinstance(selection,list) and len(selection)==len(set(selection)) and
                all(isinstance(x,str) for x in selection),
                "SOURCE_STAGE3_INSTRUMENT_SELECTION_INVALID")
    else:selection=None
    bindings=dict(target_bindings) if target_bindings is not None else load_installed_registry()
    resolved=[];missing=[];hits=0
    for role in original_roles:
        name=role["role"]; requested=role["instrument_id"]
        record=entry["role_bindings"][name]
        require(record["original_instrument_id"]==requested,
                "SOURCE_ROLE_INSTRUMENT_CHANGED:"+name)
        if record["lookup_policy"]=="EXACT_CONTEXTUAL":
            key=(genre,name,requested)
            require(key in CONTEXT_PINNED,"CONTEXT_PROGRAM_NOT_AUTHORIZED:"+name)
            binding_id,rid,sfz=CONTEXT_PINNED[key]
        elif record["lookup_policy"]=="EXACT_ID":
            require(requested in PINNED,"UNVERIFIED_SOURCE_ID_IN_EXACT_SLOT")
            binding_id=requested;rid,sfz=PINNED[requested]
        else:
            require(record["lookup_policy"]=="BLOCKED_UNVERIFIED",
                    "UNKNOWN_BINDING_POLICY")
            resolved.append({"role":name,"original_instrument_id":requested,
                "status":"BLOCKED_NO_AUTHORITATIVE_SOURCE_PROGRAM",
                "reason":"No explicit recorded-program mapping for this instrument"});
            missing.append(name);continue
        require(record.get("binding_id")==binding_id and
                record.get("resource_id")==rid and
                record.get("preferred_mapping")==sfz,
                "SOURCE_PROGRAM_PIN_DRIFT:"+name)
        selection_ok=(selection is None or requested in selection or
                      any(a in selection for a in REGISTERED_PALETTE_ALIASES.get(requested,())) or
                      binding_id in selection or
                      (requested in PER_GENRE_DRUMS_ALLOWED.get(genre,frozenset())
                        and "drums" in selection))
        if not selection_ok:
            resolved.append({"role":name,"original_instrument_id":requested,
              "status":"BLOCKED_NOT_SELECTED_BY_STAGE3",
              "reason":"Stage 3 did not select this exact instrument"});
            missing.append(name);continue
        resource=bindings.get(binding_id)
        if not isinstance(resource,dict):
            resolved.append({"role":name,"original_instrument_id":requested,
              "status":"BLOCKED_NO_INSTALLED_REGISTRY_BINDING",
              "binding_id":binding_id,"resource_id":rid,
              "reason":"Original target registry lacks exact source binding"});
            missing.append(name);continue
        if not (resource.get("resource_id")==rid and
                resource.get("preferred_mapping")==sfz and
                resource.get("resource_type")=="SFZ_SAMPLE_LIBRARY" and
                resource.get("fallback_policy")=="NO_SYNTHETIC_SUBSTITUTION" and
                (resource.get("library"),resource.get("license"))==
                     ORIGINAL_SOURCE_PROVENANCE[rid]):
            resolved.append({"role":name,"original_instrument_id":requested,
              "status":"BLOCKED_REGISTRY_SOURCE_MISMATCH",
              "binding_id":binding_id,"resource_id":rid,
              "reason":"Stored target binding differs from pinned recorded source"});
            missing.append(name);continue
        # A program could exist in the registry while its sound files are not
        # installed or its requested notes don't exist in that sound's range.
        resolved.append({"role":name,"original_instrument_id":requested,
            "binding_id":binding_id,"resource_id":rid,
            "preferred_mapping":sfz,"source_type":"SFZ_SAMPLE_LIBRARY",
            "status":"EXACT_PROGRAM_REFERENCE_ONLY",
            "source_files_validated":False,"requested_note_zones_validated":False,
            "audible_recorded_stem_validated":False,
            "percussion_allowed_midi_notes":list(EXACT_PERCUSSION_NOTES.get(requested,()))})
        hits+=1
    note_errors=[]
    partnotes=seed.get("symbolic_note_events",[])
    perRole={r["role"]:r for r in resolved}
    for n in partnotes:
        item=perRole.get(n["role"])
        if item is None or item["status"]!="EXACT_PROGRAM_REFERENCE_ONLY":continue
        if n.get("pattern_kind")=="DRUM_ABSOLUTE":
            notes=item["percussion_allowed_midi_notes"]
            if n["midi"] not in notes:
                note_errors.append({"role":n["role"],"note":n["midi"],
                                    "reason":"SOURCE_DRUM_MIDI_NOTE_NOT_IN_KNOWN_PROGRAM"})
    return {"schema":"AI_COMP_SOURCE_PROGRAM_ROUTING_V1","genre":genre,
       "genre_profile_id":ref["genre_profile_id"],
       "original_stage3_selected":selection,
       "registry_binding_count":len(bindings),
       "roles":resolved,"roles_total":len(resolved),
       "exact_registry_references":hits,
       "unresolved_roles":missing,"unsupported_percussion_notes":note_errors,
       "source_program_identification_complete":not missing and not note_errors,
       "playback_preflight_complete":False,"recorded_audio_authorized":False,
       "live_deployment_authorized":False}
