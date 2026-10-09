"""One shared execution and evidence gate for the 22 researched music capabilities.

Every genre enters this SAME dispatch; never instantiate a Rock-only engine.
All output is symbolic until exact recorded source, render, and live handoff
are independently proven. The executor NEVER sets a genre live flag.
No proprietary Yamaha/Korg files, claims or implementations are included.
"""
from __future__ import annotations
from collections import defaultdict
from fractions import Fraction
from pathlib import Path
from typing import Any, Mapping, Sequence
from .shared_interpreter_router import (
    CAPABILITY_IDS, InterpreterConnectionError, route_to_shared_interpreter,
)

VERSION="GENRE_NEUTRAL_22_CAPABILITY_DISPATCH_V1"

def require(value: bool, reason: str) -> None:
    if not value: raise InterpreterConnectionError(reason)

def fraction(value: Any) -> Fraction:
    try:
        f=Fraction(str(value))
    except (ValueError,TypeError,ZeroDivisionError) as e:
        raise InterpreterConnectionError("INVALID_BEAT_NUMBER") from e
    require(f.denominator<=1920 and f>=0,"UNSUPPORTED_BEAT_NUMBER")
    return f

def _record(code: str, state: str, *, artifact: Any=None, reason: str="") -> dict:
    return {"handler":code, "state":state, "artifact":artifact,
            "reason":reason, "live_verified":False}

def _notes(ctx: Mapping[str,Any]) -> list[dict]:
    return list(ctx["plan"].get("symbolic_note_events",[]))

def _roles(ctx: Mapping[str,Any]) -> dict:
    return {r["role"]:r for r in ctx["plan"].get("roles",[])}

def _resources(ctx: Mapping[str,Any]) -> dict:
    return dict(ctx.get("resources") or {})

def _requests(ctx: Mapping[str,Any]) -> dict:
    return dict(ctx.get("requests") or {})

def _musical(code: str, ctx: Mapping[str,Any], key: str) -> dict:
    plan=ctx["plan"]
    if key=="genre_rules":
        return _record(code,"SYMBOLIC_RULES_CONNECTED",
                       artifact={"profile_id":plan["genre_profile_id"],
                                 "source_path":plan["source_path"],
                                 "genre_rules":plan["genre_rules"]})
    item=plan.get(key,[])
    return _record(code,"SYMBOLIC_EXECUTABLE" if item else "CONNECTED_INPUT_PENDING",
                   artifact=item,
                   reason="" if item else "Await authored "+key)

def _cap01(ctx):return _musical("ARRANGEMENT_INTENT",ctx,"sections")
def _cap02(ctx):return _musical("CHORD_CONTEXT",ctx,"chord_timeline")
def _cap03(ctx):return _musical("ROLE_VARIATION",ctx,"sections")
def _cap04(ctx):return _musical("ROOT_CONVERSION",ctx,"symbolic_note_events")
def _cap05(ctx):return _musical("CHORD_QUALITY",ctx,"symbolic_note_events")
def _cap06(ctx):return _musical("CHORD_RETRIGGER",ctx,"symbolic_note_events")
def _cap07(ctx):return _musical("RANGE_GUARD",ctx,"roles")
def _cap08(ctx):return _musical("SECTION_CONDUCTOR",ctx,"sections")
def _cap09(ctx):
    p=ctx["plan"]
    return _record("ENSEMBLE_CLOCK","SYMBOLIC_EXECUTABLE",
                   artifact={"tempo_bpm":p["tempo_bpm"],
                             "meter":p["meter"],
                             "quarter_beats_per_bar":p["quarter_beats_per_bar"]})
def _cap10(ctx):return _musical("INDIVIDUAL_GENRE_GRAMMAR",ctx,"genre_rules")

def _cap11(ctx):
    """Typed attack/sustain/release, never infer what sample articulations exist."""
    notes=_notes(ctx)
    if not notes:return _record("PERFORMANCE_STATE_MACHINE","CONNECTED_INPUT_PENDING",
                                reason="No authored symbolic notes")
    states=[]
    for i,n in enumerate(notes):
        start=fraction(n["start_beat"])
        end=start+fraction(n["duration_beats"])
        require(end>start,"NOTE_STATE_EMPTY_DURATION")
        states.extend([{"note_id":i,"role":n["role"],"beat":str(start),"state":"ATTACK"},
                       {"note_id":i,"role":n["role"],"beat":str(end),"state":"RELEASE"}])
    states.sort(key=lambda x:(fraction(x["beat"]),
                     0 if x["state"]=="RELEASE" else 1,x["role"],x["note_id"]))
    return _record("PERFORMANCE_STATE_MACHINE","SYMBOLIC_EXECUTABLE",
                   artifact={"events":states,"sample_articulations_verified":False})

def _cap12(ctx):
    """Physical guitar check requires exact per-string source tuning/fret mapping."""
    guitar=_requests(ctx).get("guitar_strums",[])
    if not guitar:return _record("PHYSICAL_GUITAR_STRUM","CONNECTED_INPUT_PENDING",
                                 reason="Requires authored guitar string/fret assignments")
    result=[]
    for x in guitar:
        role=x.get("role");notes=x.get("strings",[])
        instrument=_resources(ctx).get(role,{})
        tuning=instrument.get("open_string_midi")
        require(role in _roles(ctx) and instrument.get("instrument_id")==_roles(ctx)[role]["instrument_id"],
                "GUITAR_INSTRUMENT_UNVERIFIED")
        require(isinstance(tuning,list) and 4<=len(tuning)<=12 and
                all(isinstance(t,int) and 0<=t<=127 for t in tuning),
                "GUITAR_TUNING_UNVERIFIED")
        require(x.get("direction") in ("DOWN","UP"),"GUITAR_STRUM_DIRECTION_INVALID")
        require(isinstance(notes,list) and 1<=len(notes)<=len(tuning),
                "GUITAR_STRUM_NOTE_COUNT_INVALID")
        assigned=[]
        for n in notes:
            string=n.get("string");fret=n.get("fret");pitch=n.get("midi")
            require(type(string)==int and 0<=string<len(tuning) and type(fret)==int
                    and 0<=fret<=24 and pitch==tuning[string]+fret,
                    "GUITAR_FINGERING_DOES_NOT_MATCH_TUNING")
            assigned.append((string,pitch))
        require(len({s for s,_ in assigned})==len(assigned),
                "GUITAR_SAME_STRING_STRUCK_TWICE")
        order=sorted(assigned,reverse=x["direction"]=="UP")
        result.append({"role":role,"direction":x["direction"],
                       "source_pitches":[pitch for _,pitch in order],
                       "string_order":[s for s,_ in order],
                       "physical_tuning_check":"PASS","audio_verified":False})
    return _record("PHYSICAL_GUITAR_STRUM","SYMBOLIC_EXECUTABLE",
                   artifact=result)

def _cap13(ctx):
    req=_requests(ctx).get("articulations",[])
    if not req:return _record("SOURCE_NATIVE_ARTICULATION","CONNECTED_INPUT_PENDING",
                              reason="No verified program-specific articulation requests")
    converted=[]
    for x in req:
        res=_resources(ctx).get(x["role"],{})
        key=x.get("gesture")
        supported=res.get("verified_articulations",{})
        require(res.get("source_verified") is True and key in supported,
                "BANK_SPECIFIC_ARTICULATION_NOT_VERIFIED")
        mapping=supported[key]
        require(isinstance(mapping,Mapping) and mapping.get("type") in ("CC","KEYSWITCH","NATIVE_EVENT"),
                "ARTICULATION_SOURCE_MAP_UNSUPPORTED")
        converted.append({"role":x["role"],"gesture":key,"program":res["program"],
                          "mapping":dict(mapping),"sample_response_not_proven_here":True})
    return _record("SOURCE_NATIVE_ARTICULATION","SOURCE_MAPPED_PENDING_AUDIO",
                   artifact=converted)

def _cap14(ctx):
    requests=_requests(ctx).get("phrase_shapes",[])
    if not requests:return _record("PHRASE_EXPRESSION","CONNECTED_INPUT_PENDING",
                                   reason="Requires intentional phrase/breath/dynamic shape")
    plan=ctx["plan"];out=[]
    for x in requests:
        require(x.get("role") in _roles(ctx),"UNKNOWN_PHRASE_ROLE")
        anchor=fraction(x.get("start_beat"))
        duration=fraction(x.get("duration_beats"))
        need=int(x.get("start_level",0));end=int(x.get("end_level",0))
        require(duration>0 and 0<=need<=127 and 0<=end<=127,
                "INVALID_PHRASE_SHAPE")
        out.append({"role":x["role"],"start_beat":str(anchor),
                    "duration_beats":str(duration),
                    "start_level":need,"end_level":end,"type":"AUTHORED_CURVE",
                    "continuous_controls_require_bank_map":True})
    return _record("PHRASE_EXPRESSION","SYMBOLIC_EXECUTABLE",artifact=out)

def _cap15(ctx):
    """Assemble a deterministic timed MIDI1 message plan, not actual sample output."""
    notes=_notes(ctx)
    if not notes:return _record("TIMED_MIDI_WRITER","CONNECTED_INPUT_PENDING",
                                reason="No composed notes to schedule")
    events=[]
    for i,n in enumerate(notes):
        role=n["role"]
        begin=fraction(n["start_beat"])
        finish=begin+fraction(n["duration_beats"])
        pitch=n["midi"];v=n["velocity"]
        require(type(pitch)==int and 0<=pitch<=127 and type(v)==int and 1<=v<=127,
                "MIDI_NOTE_INVALID")
        events.append((begin,1,{"type":"note_on","role":role,"note":pitch,"velocity":v,"id":i}))
        events.append((finish,0,{"type":"note_off","role":role,"note":pitch,"velocity":0,"id":i}))
    for control in _requests(ctx).get("midi_controls",[]):
        role=control.get("role")
        res=_resources(ctx).get(role,{})
        cc=control.get("controller");value=control.get("value")
        require(res.get("source_verified") is True and type(cc)==int
                and cc in res.get("verified_cc",[]) and type(value)==int
                and 0<=value<=127,"MIDI_CC_NOT_BANK_VERIFIED")
        events.append((fraction(control.get("beat")),2,
                      {"type":"control_change","role":role,"cc":cc,"value":value}))
    events.sort(key=lambda x:(x[0],x[1],x[2].get("role","")))
    return _record("TIMED_MIDI_WRITER","SYMBOLIC_MIDI_MESSAGES_READY",
                   artifact={"messages":[{"beat":str(t),**e} for t,_,e in events],
                             "midi_file_written":False,"rendered":False})

def _cap16(ctx):
    roles=_roles(ctx);resource=_resources(ctx)
    if not roles:return _record("CAPABILITY_MANIFEST","CONNECTED_INPUT_PENDING",
                                reason="No instrument roles selected")
    result=[]
    for role,r in roles.items():
        source=resource.get(role,{})
        if not source or source.get("instrument_id")!=r["instrument_id"]:
            return _record("CAPABILITY_MANIFEST","BLOCKED_RESOURCE_EVIDENCE",
                           reason="Missing exact source-capability mapping for "+role)
        needed=("resource_id","program","source_type","source_verified")
        if any(k not in source for k in needed):
            return _record("CAPABILITY_MANIFEST","BLOCKED_RESOURCE_EVIDENCE",
                           reason="Incomplete sample manifest for "+role)
        require(source["source_type"] in ("SFZ_SAMPLE_LIBRARY","SAMPLE_INSTRUMENT") and
                source["source_verified"] is True,"UNVERIFIED_SAMPLE_SOURCE")
        result.append({"role":role,"resource_id":source["resource_id"],
                       "program":source["program"],"instrument_id":r["instrument_id"],
                       "verified_cc":source.get("verified_cc",[]),
                       "verified_articulations":list(source.get("verified_articulations",{})),
                       "complete_audio_proven":False})
    return _record("CAPABILITY_MANIFEST","DECLARED_SOURCE_PROGRAMS",
                   artifact=result)

def _cap17(ctx):
    roles=_roles(ctx)
    if not roles:return _record("SUSTAIN_RELEASE","CONNECTED_INPUT_PENDING",
                                reason="No selected sampled roles")
    out=[]
    for role in roles:
        source=_resources(ctx).get(role,{})
        lifetime=source.get("sample_lifetime")
        if not isinstance(lifetime,Mapping) or lifetime.get("note_off_action") not in (
                "RELEASE_ENVELOPE","SAMPLE_GATE","ONE_SHOT"):
            return _record("SUSTAIN_RELEASE","BLOCKED_SAMPLE_LIFETIME",
                           reason="No verified note-off semantics for "+role)
        out.append({"role":role,"note_off_action":lifetime["note_off_action"],
                    "loop_validated":bool(lifetime.get("loop_validated",False)),
                    "audible_sustain_not_proven_here":True})
    return _record("SUSTAIN_RELEASE","SOURCE_CONTRACT_DECLARED",artifact=out)

def _cap18(ctx):
    events=_requests(ctx).get("drum_strikes",[])
    if not events:return _record("SEPARATE_DRUM_STRIKES","CONNECTED_INPUT_PENDING",
                                 reason="No authored percussion struck-notes")
    mapped=[];counts=defaultdict(int)
    for n in events:
        role=n.get("role");res=_resources(ctx).get(role,{})
        raw=n.get("source_note")
        source_map=res.get("verified_drum_note_map",{})
        require(res.get("source_verified") is True and
                type(raw)==int and str(raw) in source_map,
                "DRUM_SOUND_MAP_NOT_VERIFIED")
        dest=source_map[str(raw)]
        require(type(dest)==int and 0<=dest<=127,"DRUM_TARGET_INVALID")
        counts[role]+=1
        variants=res.get("verified_round_robin_variants",1)
        require(type(variants)==int and 1<=variants<=32,"DRUM_ROUND_ROBIN_INVALID")
        mapped.append({"role":role,"beat":str(fraction(n.get("beat"))),
                       "source_note":raw,"destination_note":dest,
                       "velocity":n.get("velocity"),
                       "round_robin_index":(counts[role]-1)%variants,
                       "percussion_stem_role":role,"recorded_audio_pending":True})
        require(type(n.get("velocity"))==int and
                1<=n["velocity"]<=127,"DRUM_VELOCITY_INVALID")
    return _record("SEPARATE_DRUM_STRIKES","SYMBOLIC_SOURCE_MAP_READY",artifact=mapped)

def _cap19(ctx):
    requests=_requests(ctx).get("per_note_controls",[])
    if not requests:return _record("POLYPHONIC_ISOLATION","CONNECTED_INPUT_PENDING",
                                   reason="No per-note control needed")
    out=[];used={}
    for r in requests:
        role=r.get("role");note_id=r.get("note_id")
        manifest=_resources(ctx).get(role,{})
        channel=r.get("channel")
        require(manifest.get("mpe_verified") is True and
                type(channel)==int and 1<=channel<=15,
                "PER_NOTE_CHANNEL_ISOLATION_NOT_VERIFIED")
        key=(role,channel)
        if key in used:
            require(used[key]==note_id,"POLYPHONIC_NOTE_CHANNEL_COLLISION")
        used[key]=note_id
        out.append({"role":role,"note_id":note_id,"channel":channel})
    return _record("POLYPHONIC_ISOLATION","CHANNEL_PLAN_CHECKED",artifact=out)

def _cap20(ctx):
    roles=_roles(ctx)
    if not roles:return _record("SOURCE_STEM_TRACE","CONNECTED_INPUT_PENDING",
                                reason="No selected source roles")
    details=[]
    for role,r in roles.items():
        source=_resources(ctx).get(role,{})
        for key in ("resource_id","program","source_sha256","stem_id"):
            if not isinstance(source.get(key),str) or not source[key]:
                return _record("SOURCE_STEM_TRACE","BLOCKED_RESOURCE_EVIDENCE",
                               reason="Missing "+key+" for "+role)
        require(source.get("source_verified") is True and
                source.get("instrument_id")==r["instrument_id"],
                "ROLE_RESOURCE_ID_MISMATCH")
        details.append({k:source[k] for k in
                       ("resource_id","program","source_sha256","stem_id")})
    return _record("SOURCE_STEM_TRACE","PROVENANCE_DECLARED_PENDING_RENDER",
                   artifact=details)

def _cap21(ctx):
    e=_requests(ctx).get("audio_evidence")
    if not e:return _record("COMPLETE_PLAYBACK_AUDIT","BLOCKED_NO_AUDIO_EVIDENCE",
                            reason="Requires original source audio, full stems, 3D master and listening")
    fields=("source_identity","render_report","stem_integrity",
            "master_integrity","genre_listening_review")
    missing=[f for f in fields if not e.get(f)]
    if missing:return _record("COMPLETE_PLAYBACK_AUDIT","BLOCKED_NO_AUDIO_EVIDENCE",
                              reason="Unproven: "+",".join(missing))
    return _record("COMPLETE_PLAYBACK_AUDIT","SUBMITTED_FOR_INDEPENDENT_AUDIT",
                   artifact={"receipt_fields":list(fields),
                             "independent_verification_still_required":True})

def _cap22(ctx):
    evidence=_requests(ctx).get("live_handoff")
    if not evidence:return _record("LIVE_AUDIO_HANDOFF","BLOCKED_NOT_LIVE_VERIFIED",
                                   reason="No verified Composer→Plug→Control Panel return")
    fields=("composer_job_id","plug_delivery_receipt",
            "control_panel_audio_receipt","phone_playback_confirmation")
    if any(not evidence.get(k) for k in fields):
        return _record("LIVE_AUDIO_HANDOFF","BLOCKED_NOT_LIVE_VERIFIED",
                       reason="Missing actual user playback and transport receipts")
    return _record("LIVE_AUDIO_HANDOFF","SUBMITTED_FOR_LIVE_AUDIT",
                   artifact={"transport_fields":list(fields),
                             "deployment_not_authorized":True})

HANDLERS={
    "CAP_01":_cap01,"CAP_02":_cap02,"CAP_03":_cap03,"CAP_04":_cap04,
    "CAP_05":_cap05,"CAP_06":_cap06,"CAP_07":_cap07,"CAP_08":_cap08,
    "CAP_09":_cap09,"CAP_10":_cap10,"CAP_11":_cap11,"CAP_12":_cap12,
    "CAP_13":_cap13,"CAP_14":_cap14,"CAP_15":_cap15,"CAP_16":_cap16,
    "CAP_17":_cap17,"CAP_18":_cap18,"CAP_19":_cap19,"CAP_20":_cap20,
    "CAP_21":_cap21,"CAP_22":_cap22}
assert tuple(HANDLERS)==CAPABILITY_IDS,"ALL_22_CAPABILITY_CODE_PATHS_REQUIRED"

def evaluate_22_capabilities(
    plan: Mapping[str,Any], *,
    requests: Mapping[str,Any]|None=None,
    resources: Mapping[str,Any]|None=None,
) -> dict:
    """Execute all 22 capability *connections*, never auto-approve audio/live.

    Evidence is explicit. Missing inputs leave an honest blocked/awaiting state;
    a connected handler is not a proven instrument or live piece of music.
    """
    genre=plan["genre"]
    reference=route_to_shared_interpreter(genre)
    require(plan["genre_profile_id"]==reference["genre_profile_id"],
            "CROSS_GENRE_EXECUTION_FORBIDDEN")
    require(plan["stage_3_to_4"]==reference["stage_3_to_4"] and
            plan["original_7_stages"]==reference["original_7_stages"],
            "SEVEN_STAGE_HANDOFF_DRIFT")
    require(plan.get("recorded_audio_authorized") is False
            and plan.get("midi_authorized") is False,
            "UNVERIFIED_AUDIO_ACTIVATION_FORBIDDEN")
    context={"plan":plan,"requests":requests or {},"resources":resources or {}}
    output={}
    for id_,handler in HANDLERS.items():
        item=handler(context)
        require(item.get("live_verified") is False,"FALSE_LIVE_VERIFICATION")
        output[id_]={"name":next(x["requirement"] for x in
                      reference["capability_requirements"] if x["id"]==id_),
                     **item}
    require(tuple(output)==CAPABILITY_IDS,"CAPABILITY_ROUTER_NOT_COMPLETE")
    return {"schema":VERSION,"genre":genre,
            "genre_profile_id":reference["genre_profile_id"],
            "shared_interpreter":reference["stage_3_to_4"],
            "capability_count":22,"capabilities":output,
            "all_handlers_connected":True,
            "usable_symbolic_outputs_are_not_audio":True,
            "ready_for_live_deployment":False,"audio_verified":False}
