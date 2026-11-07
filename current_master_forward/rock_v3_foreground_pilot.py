"""Rock V3 foreground research pilot.

Builds a Rock-only foreground candidate on top of the validated V3-governed
source-pattern accompaniment.

This is deliberately narrow:
- no generic melody generator;
- no audio;
- no live promotion;
- same canonical electric_guitar identity for rhythm and lead roles;
- bass/drums are untouched;
- rhythm guitar is structurally thinned in explicit lead windows;
- motif vocabulary and chord-responsive pitch treatment derive from the prior
  project-authored ROCK_MELODIC_AUTHOR_V1 research candidate.

The section-to-foreground schedule below is a new research candidate and is not
claimed as a universal Rock rule.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any

from genre_v3_foreground_authority import compile_authority
from genre_v3_symbolic_pattern_executor import compile_seed
from rock_v3_variant_resolver import resolve as resolve_rock_variant

SCHEMA="ROCK_V3_FOREGROUND_PILOT_001"
PROFILE_ID="ROCK_CORE_V2"
LEAD_INSTRUMENT_ID="electric_guitar"
LEAD_REGISTER=(59,76)
E_NATURAL_MINOR_PCS={4,6,7,9,11,0,2}

# Preserved motif vocabulary from ROCK_MELODIC_AUTHOR_V1.
MOTIFS={
    "A_CALL":((0.00,0),(0.75,1),(1.50,3),(2.50,1)),
    "A_ANSWER":((0.00,2),(1.00,1),(1.75,0),(2.75,-1)),
    "B_LIFT":((0.50,0),(1.00,2),(1.75,3),(2.50,1),(3.00,0)),
    "A_REPRISE":((0.00,0),(0.75,1),(1.50,3),(2.25,2),(3.00,0)),
    "CADENCE":((0.00,2),(1.00,1),(2.25,0)),
}

# New research-only section schedule. Response sections deliberately return
# foreground authority to the riff/rhythm-guitar layer.
SECTION_PLAN={
    "INTRO":{"owner":"HARMONY_RIFF","motif":None},
    "VERSE_A":{"owner":"LEAD_GUITAR","motif":"A_CALL"},
    "VERSE_RESPONSE":{"owner":"HARMONY_RIFF","motif":None},
    "FILL":{"owner":"LEAD_GUITAR","motif":"A_ANSWER"},
    "CHORUS_B":{"owner":"LEAD_GUITAR","motif":"B_LIFT"},
    "CHORUS_RESPONSE":{"owner":"HARMONY_RIFF","motif":None},
    "ENDING":{"owner":"LEAD_GUITAR","motif":"CADENCE"},
}


class RockV3ForegroundPilotError(RuntimeError):
    pass


def _sha(value:Any)->str:
    return hashlib.sha256(
        json.dumps(value,sort_keys=True,separators=(",",":"),default=str).encode()
    ).hexdigest()


def _pitch_candidates(pcs:set[int],low:int=LEAD_REGISTER[0],high:int=LEAD_REGISTER[1]):
    return [m for m in range(low,high+1) if m%12 in pcs]


def _near(pcs:set[int],target:float,previous:int|None=None)->int:
    pitches=_pitch_candidates(pcs)
    if not pitches:
        raise RockV3ForegroundPilotError("EMPTY_ALLOWED_PITCH_SET")
    return min(
        pitches,
        key=lambda p:(
            abs(p-target)+(0.16*abs(p-previous) if previous is not None else 0),
            abs(p-66),
            p,
        ),
    )


def _nearest_scale(target:float,reference:int)->int:
    pitches=_pitch_candidates(E_NATURAL_MINOR_PCS)
    return min(pitches,key=lambda p:(abs(p-target),abs(p-reference),p))


def _chord_pcs(chord:dict[str,Any])->set[int]:
    root=int(chord["root_pc"])
    quality=chord.get("quality") or ""
    if quality=="m":
        intervals=(0,3,7)
    elif quality in ("","maj7"):
        intervals=(0,4,7)
    elif quality=="7":
        intervals=(0,4,7,10)
    else:
        raise RockV3ForegroundPilotError(
            "ROCK_PILOT_UNSUPPORTED_CHORD_QUALITY::"+str(quality)
        )
    return {(root+x)%12 for x in intervals}


def _compose_bar(
    *,
    bar:int,
    section:str,
    motif_id:str,
    chord:dict[str,Any],
    previous_pitch:int|None,
)->tuple[list[dict[str,Any]],int]:
    motif=MOTIFS[motif_id]
    chord_pcs=_chord_pcs(chord)
    root_pc=int(chord["root_pc"])
    midpoint=66 if section!="CHORUS_B" else 68
    root=_near({root_pc},midpoint if previous_pitch is None else previous_pitch,previous_pitch)

    contour_sign=-1 if section=="ENDING" else 1
    pitches=[]
    for j,(position,degree) in enumerate(motif):
        final=j==len(motif)-1
        if j==0:
            pitch=_near(chord_pcs,root+(2 if motif_id=="B_LIFT" else 0),previous_pitch)
        elif final:
            target=root if motif_id in ("CADENCE","A_REPRISE") else pitches[-1]-1
            allowed={root_pc} if motif_id=="CADENCE" else chord_pcs
            pitch=_near(allowed,target,pitches[-1])
        else:
            target=root+contour_sign*degree*2
            if pitches:
                target=round(.65*target+.35*pitches[-1])
            pitch=_nearest_scale(target,pitches[-1] if pitches else root)
        pitches.append(pitch)

    events=[]
    base_velocity={
        "VERSE_A":84,
        "FILL":88,
        "CHORUS_B":94,
        "ENDING":82,
    }[section]
    for j,((position,_),pitch) in enumerate(zip(motif,pitches)):
        following=motif[j+1][0] if j+1<len(motif) else 3.90
        distance=following-position
        if distance<=0:
            raise RockV3ForegroundPilotError("NON_MONOTONIC_ROCK_MOTIF")
        length=min(1.45,max(.19,distance*(.89 if j==len(motif)-1 else .79)))
        accent=(1.02,.91,1.09,.96,.97)[j%5]
        events.append({
            "track_id":"LEAD",
            "role":"LEAD_GUITAR",
            "instrument_id":LEAD_INSTRUMENT_ID,
            "start_beat":round(bar*4+position,6),
            "duration_beats":round(length,6),
            "midi":int(pitch),
            "velocity":max(50,min(115,round(base_velocity*accent))),
            "section":section,
            "variation":"V3_FOREGROUND_"+motif_id,
            "articulation":"genre_lead",
            "foreground_owner":"LEAD_GUITAR",
            "arrangement_role":"FOREGROUND_LEAD",
            "source_rule":"ROCK_V3_FOREGROUND_RESEARCH_PILOT",
            "source_motif_id":motif_id,
            "symbolic_only":True,
        })
    return events,pitches[-1]


def realize()->dict[str,Any]:
    foreground=compile_authority("ROCK")
    variant_gate=resolve_rock_variant(None)
    if variant_gate.get("status")!="ROCK_VARIANT_REQUIRED":
        raise RockV3ForegroundPilotError("ROCK_VARIANT_GATE_DID_NOT_BLOCK_BROAD_ROCK")
    if foreground.get("profile_id")!=PROFILE_ID:
        raise RockV3ForegroundPilotError("ROCK_PROFILE_ID_DRIFT")
    if foreground.get("execution_status")!="STRUCTURED_FOREGROUND_AUTHORITY_PRESENT__NOTE_EXECUTION_NOT_COMPILED":
        raise RockV3ForegroundPilotError("ROCK_FOREGROUND_BASELINE_STATUS_UNEXPECTED")

    source=compile_seed("ROCK")
    if source.get("status")!="PASS":
        raise RockV3ForegroundPilotError("ROCK_SOURCE_PATTERN_NOT_PASS")
    if source.get("meter")!="4/4":
        raise RockV3ForegroundPilotError("ROCK_PILOT_REQUIRES_4_4")
    if [x["section"] for x in source["events"] if x["role"]=="HARMONY"]==[]:
        raise RockV3ForegroundPilotError("ROCK_HARMONY_EVENTS_MISSING")

    chord_by_bar={int(x["bar"]):x for x in source["chords"]}
    section_by_bar={}
    for event in source["events"]:
        bar=int(float(event["start_beat"])//4)
        section_by_bar.setdefault(bar,event["section"])
    if len(section_by_bar)!=7:
        raise RockV3ForegroundPilotError("ROCK_SECTION_MAP_NOT_SEVEN_BARS")

    original=[deepcopy(e) for e in source["events"]]
    lead_sections={name for name,spec in SECTION_PLAN.items() if spec["owner"]=="LEAD_GUITAR"}

    # Thin rhythm guitar structurally in lead windows: keep only the earliest
    # HARMONY event in each foreground bar. Do not modify bass or percussion.
    earliest_harmony={}
    for e in original:
        if e["role"]!="HARMONY":
            continue
        bar=int(float(e["start_beat"])//4)
        if section_by_bar.get(bar) not in lead_sections:
            continue
        current=earliest_harmony.get(bar)
        if current is None or float(e["start_beat"])<float(current["start_beat"]):
            earliest_harmony[bar]=e

    arranged=[]
    thinned=[]
    for e in original:
        item=deepcopy(e)
        bar=int(float(item["start_beat"])//4)
        section=section_by_bar[bar]
        if item["role"]=="HARMONY" and section in lead_sections:
            if e is not earliest_harmony[bar]:
                thinned.append({
                    "bar":bar,
                    "section":section,
                    "start_beat":item["start_beat"],
                    "reason":"YIELD_DENSITY_TO_LEAD_GUITAR",
                })
                continue
            item["foreground_owner"]="LEAD_GUITAR"
            item["arrangement_role"]="SUPPORTING_HARMONY"
            item["source_rule"]="V3_FOREGROUND_WINDOW_RHYTHM_GUITAR_SIMPLIFICATION"
        elif item["role"]=="HARMONY":
            item["foreground_owner"]="HARMONY_RIFF"
            item["arrangement_role"]="FOREGROUND_RIFF"
        else:
            item["foreground_owner"]=SECTION_PLAN[section]["owner"]
            item["arrangement_role"]="FOUNDATION"
        arranged.append(item)

    lead=[]
    previous=None
    for bar in range(7):
        section=section_by_bar[bar]
        spec=SECTION_PLAN[section]
        motif=spec["motif"]
        if motif is None:
            continue
        bar_events,previous=_compose_bar(
            bar=bar,
            section=section,
            motif_id=motif,
            chord=chord_by_bar[bar],
            previous_pitch=previous,
        )
        lead.extend(bar_events)

    combined=arranged+lead
    combined.sort(key=lambda x:(float(x["start_beat"]),str(x["track_id"]),int(x.get("midi") or 0)))

    result={
        "schema":SCHEMA,
        "status":"PASS",
        "genre":"ROCK",
        "profile_id":PROFILE_ID,
        "meter":source["meter"],
        "tempo_bpm":source["tempo_bpm"],
        "bar_count":source["bar_count"],
        "source_seed_id":source["source_seed_id"],
        "source_execution_sha256":source["execution_sha256"],
        "foreground_authority_sha256":foreground["foreground_authority_sha256"],
        "foreground_schedule":deepcopy(SECTION_PLAN),
        "rock_variant_gate":variant_gate,
        "resolved_rock_variant":None,
        "variant_specific_music_ready":False,
        "song_form_expansion_ready":False,
        "lead_instrument_id":LEAD_INSTRUMENT_ID,
        "lead_register_midi":list(LEAD_REGISTER),
        "lead_event_count":len(lead),
        "rhythm_guitar_events_removed_for_space":len(thinned),
        "rhythm_guitar_thinning_manifest":thinned,
        "events":combined,
        "audio_authority":False,
        "audio_generated":False,
        "live_runtime_authority":False,
        "musical_audition_approved":False,
        "research_candidate_only":True,
        "generic_melody_generator_used":False,
        "legacy_note_generator_used":False,
        "prior_project_melodic_vocabulary":"ROCK_MELODIC_AUTHOR_V1",
        "new_candidate_decision":"SECTION_TO_FOREGROUND_SCHEDULE_REQUIRES_LISTENING_VALIDATION",
        "promotion_gate":"ROCK_VARIANT_REQUIRED__THEN_VARIANT_FORM_RESOURCE_AND_LISTENING_GATES",
    }
    result["execution_sha256"]=_sha({k:v for k,v in result.items() if k!="execution_sha256"})
    return result
