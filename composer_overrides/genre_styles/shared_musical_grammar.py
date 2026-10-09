"""One shared, source-grounded genre grammar: symbolic music only, no audio."""
from __future__ import annotations
from bisect import bisect_right
from fractions import Fraction
import re
from typing import Any, Mapping, Sequence
from .shared_interpreter_router import route_to_shared_interpreter, InterpreterConnectionError

GRAMMAR_VERSION = "AI_COMP_SHARED_GENRE_GRAMMAR_V1"
ROOTS = dict(C=0,D=2,E=4,F=5,G=7,A=9,B=11)
SCALES = {"":(0,2,4,5,7,9,11),"m":(0,2,3,5,7,8,10),
          "7":(0,2,4,5,7,9,10),"m7":(0,2,3,5,7,9,10),
          "maj7":(0,2,4,5,7,9,11),"sus4":(0,2,5,5,7,9,10),
          "dim":(0,2,3,5,6,8,9),"aug":(0,2,4,5,8,9,11)}
CHORD_RE = re.compile(r"^([A-G])([#b]?)(maj7|m7|sus4|dim|aug|m|7)?(?:/([A-G])([#b]?))?$")
SYMBOLIC = {
 "CAP_01":"COMPILED_TYPED_GENRE_ARRANGEMENT_INTENT",
 "CAP_02":"EXPLICIT_CHORD_CONTEXT_AND_OPTIONAL_SLASH_BASS",
 "CAP_03":"EXPLICIT_VARIATION_SELECTION_BY_ROLE_AND_SECTION",
 "CAP_04":"CHORD_ROOT_SYMBOLIC_NOTE_CONVERSION",
 "CAP_05":"LIMITED_VERIFIED_CHORD_QUALITY_MAPPING",
 "CAP_06":"CHORD_BOUNDARY_HOLD_OR_STOP_POLICY",
 "CAP_07":"CHECK_DECLARED_INSTRUMENT_MIDI_RANGE",
 "CAP_08":"EXPLICIT_SECTION_PLAN_WITH_VARIANTS",
 "CAP_09":"SHARED_EXACT_BEAT_CLOCK",
 "CAP_10":"SOURCE_GENRE_LANGUAGE_PRESERVED_IN_COMMON_ROUTE"}
GATED = {
 "CAP_11":"INSTRUMENT_EXPRESSION_STATE_MACHINE",
 "CAP_12":"PHYSICALLY_REALISTIC_GUITAR_FINGERING",
 "CAP_13":"BANK_SPECIFIC_ARTICULATION",
 "CAP_14":"PHRASE_EXPRESSION_AND_BREATH",
 "CAP_15":"ACTUAL_TIMED_MIDI_CC_WRITER",
 "CAP_16":"COMPLETE_SOUND_PROGRAM_CAPABILITY_MANIFEST",
 "CAP_17":"SAMPLE_RELEASE_AND_SUSTAIN",
 "CAP_18":"RECORDED_DRUM_MAPPING_AND_FILLS",
 "CAP_19":"PER_NOTE_POLYPHONIC_CONTROLLER_ISOLATION",
 "CAP_20":"REAL_SAMPLE_TO_STEM_PROOF",
 "CAP_21":"AUDITED_COMPLETE_PLAYBACK",
 "CAP_22":"LIVE_COMPOSER_PLUG_CONTROL_PANEL_AUDIO"}

def need(test: bool, reason: str) -> None:
    if not test: raise InterpreterConnectionError(reason)

def beat(value: Any, field: str) -> Fraction:
    need(not isinstance(value,bool),"INVALID_"+field)
    try: value=Fraction(str(value))
    except (TypeError,ValueError,ZeroDivisionError) as exc:
        raise InterpreterConnectionError("INVALID_"+field) from exc
    need(value.denominator<=1920,"UNSUPPORTED_"+field+"_GRID")
    return value

def chord(symbol: str) -> dict:
    found=CHORD_RE.fullmatch(str(symbol))
    need(found is not None,"UNSUPPORTED_CHORD_SYMBOL:"+str(symbol))
    root,acc,quality,bass_root,bass_acc=found.groups()
    root_pc=(ROOTS[root]+{"":0,"#":1,"b":-1}[acc])%12
    bass_pc=None if bass_root is None else (ROOTS[bass_root]+{"":0,"#":1,"b":-1}[bass_acc])%12
    return {"symbol":symbol,"root_pc":root_pc,"quality":quality or "",
            "slash_bass_pc":bass_pc}

def measure(meter: str) -> Fraction:
    try: num,den=map(int,str(meter).split("/"))
    except (ValueError,TypeError) as exc:
        raise InterpreterConnectionError("INVALID_METER") from exc
    need(num>0 and den in (2,4,8,16),"INVALID_METER")
    return Fraction(num*4,den)

def compile_musical_plan(
    genre: str, *, meter: str|None=None, tempo_bpm: float|None=None,
    bars: int|None=None, sections: Sequence[Mapping[str,Any]]=(),
    chords: Sequence[Mapping[str,Any]]=(),
    roles: Sequence[Mapping[str,Any]]=(),
    patterns: Sequence[Mapping[str,Any]]=(),
    original_stage3_result: Mapping[str,Any]|None=None,
) -> dict:
    """Turn a selected genre and *explicit* score intent into symbolic events.

    Does not invent genre music, drum beats or instrument capabilities.
    Stage 4 cannot render these notes until real source authority is verified.
    """
    route=route_to_shared_interpreter(genre,original_stage3_result=original_stage3_result)
    rules=route["genre_specific_musical_intentions"]
    stage3=original_stage3_result or {}
    if meter is None: meter=stage3.get("meter")
    if tempo_bpm is None: tempo_bpm=stage3.get("tempo_bpm")
    if bars is None: bars=stage3.get("bars")
    if meter is None:
        need(len(rules["meter_options"])==1,"EXPLICIT_METER_REQUIRED")
        meter=rules["meter_options"][0]
    need(meter in rules["meter_options"],"METER_NOT_ALLOWED_FOR_GENRE")
    beats_per_bar=measure(meter)
    low_t,high_t=rules["tempo_bpm_range"]
    need(isinstance(tempo_bpm,(int,float)) and not isinstance(tempo_bpm,bool)
         and low_t<=tempo_bpm<=high_t,"TEMPO_NOT_ALLOWED_FOR_GENRE")
    need(bars is None or (isinstance(bars,int) and not isinstance(bars,bool)
         and 1<=bars<=512),"INVALID_SONG_BARS")
    resolved_sections=[];cursor=0
    for s in sections:
        need(isinstance(s,Mapping) and isinstance(s.get("name"),str)
             and s["name"].strip(),"INVALID_SECTION")
        count=s.get("bars");var=s.get("variation_by_role",{})
        need(isinstance(count,int) and not isinstance(count,bool) and 1<=count<=256,
             "INVALID_SECTION_BARS")
        need(isinstance(var,Mapping) and all(isinstance(k,str) and
             isinstance(v,str) for k,v in var.items()),"INVALID_SECTION_VARIATIONS")
        resolved_sections.append({"name":s["name"],"start_bar":cursor,
            "bars":count,"end_bar":cursor+count,"variation_by_role":dict(var)})
        cursor+=count
    if resolved_sections:
        need(bars is None or cursor==bars,"SECTIONS_DO_NOT_FILL_SONG")
        bars=cursor
    resolved_chords=[]
    for c in chords:
        need(isinstance(c,Mapping),"INVALID_CHORD")
        bar=c.get("bar");offset=beat(c.get("beat",0),"CHORD_BEAT")
        need(isinstance(bar,int) and not isinstance(bar,bool) and bar>=0,
             "INVALID_CHORD_BAR")
        need(0<=offset<beats_per_bar and (bars is None or bar<bars),
             "CHORD_OUTSIDE_METER_OR_SONG")
        obj=chord(c.get("symbol"))
        obj.update(bar=bar,beat=str(offset),position=bar*beats_per_bar+offset)
        resolved_chords.append(obj)
    resolved_chords.sort(key=lambda c:c["position"])
    times=[c["position"] for c in resolved_chords]
    need(len(set(times))==len(times),"MULTIPLE_CHORDS_AT_ONE_BEAT")
    available={}
    for r in roles:
        need(isinstance(r,Mapping),"INVALID_ROLE")
        name=r.get("role");sound=r.get("instrument_id")
        limits=r.get("playable_midi_range")
        need(isinstance(name,str) and name.strip() and name not in available,
             "DUPLICATE_OR_INVALID_ROLE")
        need(isinstance(sound,str) and sound.strip(),"INVALID_INSTRUMENT_ID")
        if original_stage3_result is not None:
            need(sound in route["selected_original_instrument_ids"],
                 "ROLE_NOT_SELECTED_AT_STAGE3")
        if limits is not None:
            need(isinstance(limits,(tuple,list)) and len(limits)==2
                 and all(isinstance(v,int) and not isinstance(v,bool) for v in limits)
                 and 0<=limits[0]<=limits[1]<=127,"INVALID_MIDI_RANGE")
        available[name]={"role":name,"instrument_id":sound,
            "declared_midi_range":list(limits) if limits is not None else None,
            "sample_program_verified":False}
    notes=[];used_patterns=set()
    for p in patterns:
        need(isinstance(p,Mapping),"INVALID_PATTERN")
        role=p.get("role")
        need(isinstance(role,str) and role in available and role not in used_patterns,
             "UNKNOWN_OR_DUPLICATE_PATTERN_ROLE")
        used_patterns.add(role)
        need(p.get("kind")=="CHORD_RELATIVE","UNSUPPORTED_PATTERN_KIND")
        need(p.get("retrigger") in ("STOP_AT_CHORD","HOLD_THROUGH_CHORD"),
             "MISSING_CHORD_RETRIGGER_POLICY")
        variants=p.get("variations")
        need(isinstance(variants,Mapping) and bool(variants),"MISSING_PATTERN_VARIANTS")
        need(resolved_sections and resolved_chords,
             "PATTERNS_REQUIRE_AUTHORED_SECTIONS_AND_CHORDS")
        limits=available[role]["declared_midi_range"]
        need(limits is not None,"PATTERN_REQUIRES_DECLARED_PLAYABLE_RANGE")
        for section in resolved_sections:
            var=section["variation_by_role"].get(role)
            if var is None: continue
            need(var in variants and isinstance(variants[var],list),
                 "UNKNOWN_PATTERN_VARIANT")
            for bar in range(section["start_bar"],section["end_bar"]):
                for n in variants[var]:
                    need(isinstance(n,Mapping),"INVALID_PATTERN_NOTE")
                    offset=beat(n.get("beat"),"PATTERN_BEAT")
                    duration=beat(n.get("duration"),"PATTERN_DURATION")
                    degree=n.get("degree");octave=n.get("octave")
                    velocity=n.get("velocity")
                    need(0<=offset<beats_per_bar and duration>0,
                         "INVALID_PATTERN_NOTE_TIMING")
                    need(isinstance(degree,int) and not isinstance(degree,bool)
                         and 1<=degree<=7,"INVALID_CHORD_DEGREE")
                    need(isinstance(octave,int) and not isinstance(octave,bool)
                         and -1<=octave<=9,"INVALID_NOTE_OCTAVE")
                    need(isinstance(velocity,int) and not isinstance(velocity,bool)
                         and 1<=velocity<=127,"INVALID_NOTE_VELOCITY")
                    at=bar*beats_per_bar+offset
                    ix=bisect_right(times,at)-1
                    need(ix>=0,"NO_CHORD_FOR_PATTERN_NOTE")
                    c=resolved_chords[ix]
                    pitch=(octave+1)*12+c["root_pc"]+SCALES[c["quality"]][degree-1]
                    need(limits[0]<=pitch<=limits[1],"OUTSIDE_DECLARED_NOTE_RANGE")
                    end=at+duration
                    need(bars is not None and end<=bars*beats_per_bar,
                         "PATTERN_END_OUTSIDE_SONG")
                    cross=bisect_right(times,at)
                    held=False
                    if cross<len(times) and times[cross]<end:
                        if p["retrigger"]=="STOP_AT_CHORD":end=times[cross]
                        else:held=True
                    need(end>at,"ZERO_DURATION_AFTER_CHORD_CHANGE")
                    notes.append({"role":role,
                        "instrument_id":available[role]["instrument_id"],
                        "start_beat":str(at),"duration_beats":str(end-at),
                        "midi":pitch,"velocity":velocity,"source_chord":c["symbol"],
                        "section":section["name"],"variation":var,
                        "cross_chord_held":held,"status":"SYMBOLIC_ONLY"})
    notes.sort(key=lambda n:(Fraction(n["start_beat"]),n["role"],n["midi"]))
    statuses=[{"id":entry["id"],
        "state":"PARTIAL_SYMBOLIC_EXECUTABLE" if entry["id"] in SYMBOLIC
                 else "NOT_YET_FULLY_IMPLEMENTED",
        "scope":SYMBOLIC.get(entry["id"],GATED.get(entry["id"])),
        "audio_verified":False} for entry in route["capability_requirements"]]
    need(len(statuses)==22 and all(x["scope"] for x in statuses),
         "22_CAPABILITY_RECORDS_INCOMPLETE")
    output={"schema":GRAMMAR_VERSION,"genre":genre,"family":route["family"],
        "genre_profile_id":route["genre_profile_id"],
        "source_path":route["source_path"],
        "stage_3_to_4":route["stage_3_to_4"],
        "original_7_stages":route["original_7_stages"],
        "genre_rules":rules,"meter":meter,
        "quarter_beats_per_bar":str(beats_per_bar),
        "tempo_bpm":tempo_bpm,"bars":bars,"sections":resolved_sections,
        "chord_timeline":[{k:v for k,v in c.items() if k!="position"}
                           for c in resolved_chords],
        "roles":list(available.values()),"symbolic_note_events":notes,
        "capability_status":statuses,
        "arranger_status":"EXECUTABLE_SYMBOLIC_INTENT_ONLY",
        "midi_authorized":False,"recorded_audio_authorized":False,
        "live_playback_verified":False,
        "original_genre_stage_flags_unchanged":True}

    # Single source-grounded dispatcher invoked for every selected genre:
    # all 22 paths exist, but unsupported sound/playback claims stay blocked.
    from .shared_capability_execution import evaluate_22_capabilities
    output["capability_execution"]=evaluate_22_capabilities(output)
    # The public 22-row status must reflect the actual executed handler,
    # not the older research-only flag. Handler connected != audio verified.
    verified_connections=output["capability_execution"]["capabilities"]
    for item in output["capability_status"]:
        handler=verified_connections[item["id"]]
        item["state"]=handler["state"]
        item["handler"]=handler["handler"]
        item["handler_connected"]=True
        item["audio_verified"]=False
    return output
