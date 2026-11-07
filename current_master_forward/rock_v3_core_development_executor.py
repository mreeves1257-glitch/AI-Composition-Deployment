"""Rock Core V3 40-bar symbolic development executor.

Expands the current project-authored Rock source patterns through the validated
Rock Core form, development and harmony plans.

This remains symbolic research:
- no audio;
- no live promotion;
- no generic progression engine;
- no old generic genre_development_patch;
- no random jitter;
- no invented instruments;
- kick/snare source patterns are preserved rather than augmented generically.

Musical-quality approval remains a human listening gate after later performance
and rendering preflight.
"""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
import hashlib
import json
from typing import Any

from genre_v3_source_pattern_bridge import load_seed, resolve_source_roles
from rock_v3_core_form_plan import build as build_form
from rock_v3_core_development_plan import build as build_development
from rock_v3_core_harmony_plan import build as build_harmony
from rock_v3_foreground_pilot import (
    _compose_bar as compose_foreground_bar,
    SECTION_PLAN,
)

SCHEMA="ROCK_V3_CORE_DEVELOPMENT_EXECUTOR_001"

ROOT_PC={"C":0,"D":2,"E":4,"F":5,"G":7,"A":9,"B":11}
CHORDS={
    "Em":{"root_pc":4,"quality":"m","scale":(0,2,3,5,7,8,10)},
    "C":{"root_pc":0,"quality":"","scale":(0,2,4,5,7,9,11)},
    "G":{"root_pc":7,"quality":"","scale":(0,2,4,5,7,9,11)},
    "D":{"root_pc":2,"quality":"","scale":(0,2,4,5,7,9,11)},
}
ENERGY_FACTOR={
    "INTRO_1":0.82,
    "VERSE_1":0.94,
    "CHORUS_1":1.04,
    "VERSE_2":0.98,
    "CHORUS_2":1.08,
    "OUTRO_1":0.90,
}
SECONDARY_MOTIF_BY_EPOCH={
    "VERSE_2":{"VERSE_A":"A_REPRISE","FILL":"A_CALL"},
    "CHORUS_2":{"CHORUS_B":"B_LIFT","FILL":"A_REPRISE"},
    "OUTRO_1":{"CHORUS_B":"A_REPRISE","ENDING":"CADENCE"},
}


class RockV3CoreDevelopmentExecutorError(RuntimeError):
    pass


def _sha(value:Any)->str:
    return hashlib.sha256(
        json.dumps(value,sort_keys=True,separators=(",",":"),default=str).encode()
    ).hexdigest()


def _frac(value:Any)->Fraction:
    try:
        out=Fraction(str(value))
    except (ValueError,TypeError,ZeroDivisionError) as exc:
        raise RockV3CoreDevelopmentExecutorError("INVALID_PATTERN_FRACTION") from exc
    if out.denominator>1920:
        raise RockV3CoreDevelopmentExecutorError("PATTERN_GRID_TOO_FINE")
    return out


def _clamp_velocity(value:float)->int:
    return max(1,min(127,int(round(value))))


def _cell_to_variations(seed:dict[str,Any])->dict[str,dict[str,str]]:
    out={}
    for section in seed.get("sections") or []:
        out[section["name"]]=dict(section["variation_by_role"])
    expected={
        "INTRO","VERSE_A","VERSE_RESPONSE","FILL",
        "CHORUS_B","CHORUS_RESPONSE","ENDING",
    }
    if set(out)!=expected:
        raise RockV3CoreDevelopmentExecutorError("ROCK_SOURCE_CELL_MAP_CHANGED")
    return out


def _realize_degree(symbol:str,degree:int,octave:int)->int:
    chord=CHORDS.get(symbol)
    if chord is None:
        raise RockV3CoreDevelopmentExecutorError(
            "ROCK_EXECUTOR_UNSUPPORTED_CHORD::"+str(symbol)
        )
    if type(degree) is not int or not 1<=degree<=7:
        raise RockV3CoreDevelopmentExecutorError("ROCK_EXECUTOR_BAD_DEGREE")
    if type(octave) is not int or not -1<=octave<=9:
        raise RockV3CoreDevelopmentExecutorError("ROCK_EXECUTOR_BAD_OCTAVE")
    return (
        (octave+1)*12
        + chord["root_pc"]
        + chord["scale"][degree-1]
    )


def _source_role_map(seed:dict[str,Any])->dict[str,dict[str,Any]]:
    return {x["role"]:x for x in seed.get("roles") or []}


def _pattern_map(seed:dict[str,Any])->dict[str,dict[str,Any]]:
    return {x["role"]:x for x in seed.get("patterns") or []}


def _structural_transform_notes(
    *,
    role:str,
    notes:list[dict[str,Any]],
    bar_spec:dict[str,Any],
    final_bar:bool,
)->tuple[list[dict[str,Any]],list[str]]:
    """Apply explicit Rock-development transforms at source-pattern level."""
    working=[deepcopy(x) for x in notes]
    transforms=[]
    recurrence=bool(bar_spec["source_cell_recurrence"])
    epoch=bar_spec["development_epoch"]
    cell=bar_spec["source_cell"]
    owner=bar_spec["foreground_owner"]
    occurrence=int(bar_spec["source_cell_occurrence"])

    # Final arrival: sustain the pitched foundation rather than replaying another
    # short OUTRO cell. Drum one-shots remain one-shots.
    if final_bar and role in ("BASS","HARMONY") and working:
        working=working[:1]
        working[0]["beat"]="0"
        working[0]["duration"]="5/2"
        transforms.append("FINAL_SUSTAINED_ARRIVAL")

    # Rhythm guitar makes physical room for the lead. This is arrangement, not mix.
    if role=="HARMONY" and owner=="LEAD_GUITAR" and not final_bar and working:
        working=working[:1]
        transforms.append("RHYTHM_GUITAR_YIELDS_DENSITY_TO_LEAD")

    # Recurrent riff-window guitar gets a real timing/duration variation rather
    # than only a velocity change.
    if (
        role=="HARMONY" and owner=="HARMONY_RIFF"
        and recurrence and len(working)>1 and not final_bar
    ):
        idx=len(working)-1
        beat=_frac(working[idx]["beat"])
        delta=Fraction(1,4) if occurrence%2 else Fraction(-1,4)
        shifted=max(Fraction(0),min(Fraction(15,4),beat+delta))
        if shifted==beat:
            shifted=max(Fraction(0),beat-Fraction(1,4))
        working[idx]["beat"]=str(shifted)
        working[idx]["duration"]="3/8"
        transforms.append("RHYTHM_GUITAR_RECURRENT_TIMING_VARIATION")

    # Bass preserves source note count, but recurrent cells get controlled pickup
    # movement. Single-note INTRO/OUTRO recurrences change placement/duration.
    if role=="BASS" and recurrence and working and not final_bar:
        idx=len(working)-1
        beat=_frac(working[idx]["beat"])
        if len(working)==1:
            shifted=Fraction(1,4) if occurrence%2 else Fraction(0)
            working[idx]["beat"]=str(shifted)
            working[idx]["duration"]="5/8"
            transforms.append("BASS_SINGLE_NOTE_RECURRENCE_VARIATION")
        else:
            delta=Fraction(-1,4) if occurrence%2 else Fraction(1,4)
            shifted=max(Fraction(0),min(Fraction(15,4),beat+delta))
            if shifted==beat:
                shifted=max(Fraction(0),beat-Fraction(1,4))
            working[idx]["beat"]=str(shifted)
            transforms.append("BASS_PICKUP_PLACEMENT_VARIATION")

    # Later verse/chorus recurrences can breathe by removing one soft subdivision.
    # Kick and snare are intentionally excluded: their source-authored backbeat is
    # preserved rather than generically "developed".
    if (
        role=="HAT" and recurrence and epoch in ("VERSE_2","CHORUS_2")
        and len(working)>=6 and not final_bar
    ):
        candidate_indices=[
            i for i,n in enumerate(working)
            if int(n.get("velocity",127))<=75
        ]
        if candidate_indices:
            remove_index=candidate_indices[occurrence%len(candidate_indices)]
            del working[remove_index]
            transforms.append("HAT_SELECTIVE_SOFT_SUBDIVISION_REST")

    # Intro recurrence stays sparse by moving a repeated hat attack off the first
    # exact downbeat when there is only a single source hit.
    if role=="HAT" and recurrence and epoch=="INTRO_1" and len(working)==1:
        working[0]["beat"]="1/2"
        transforms.append("INTRO_HAT_RECURRENT_OFFBEAT")

    # Section energy shapes velocity only after a structural/timing plan exists.
    factor=ENERGY_FACTOR[epoch]
    for note in working:
        if isinstance(note.get("velocity"),int):
            note["velocity"]=_clamp_velocity(note["velocity"]*factor)

    # A recurrent BAR must transform, but not every instrument has to mutate.
    # Stable foundation parts are permitted when another role supplies the real
    # section development; the bar-level gate in execute() enforces that.
    return working,transforms


def _lead_motif_for_bar(bar_spec:dict[str,Any])->str|None:
    cell=bar_spec["source_cell"]
    base=SECTION_PLAN[cell]["motif"]
    epoch=bar_spec["development_epoch"]
    return SECONDARY_MOTIF_BY_EPOCH.get(epoch,{}).get(cell,base)


def _vary_lead_events(
    events:list[dict[str,Any]],
    *,
    bar_spec:dict[str,Any],
    final_bar:bool,
)->tuple[list[dict[str,Any]],list[str]]:
    working=[deepcopy(x) for x in events]
    transforms=[]
    epoch=bar_spec["development_epoch"]

    # Verse 2 uses alternate motif IDs before this function; mark that explicit.
    if epoch=="VERSE_2":
        transforms.append("VERSE2_FOREGROUND_MOTIF_TRANSFORMATION")

    # Chorus 2 recalls B_LIFT but changes interior rhythmic placement. This is a
    # reprise-with-variation, not an octave copy.
    if epoch=="CHORUS_2" and len(working)>=4:
        for idx,delta in ((1,0.125),(2,-0.125)):
            start=float(working[idx]["start_beat"])
            bar_start=int(start//4)*4
            local=start-bar_start
            shifted=max(0.0,min(3.75,local+delta))
            working[idx]["start_beat"]=round(bar_start+shifted,6)
        working.sort(key=lambda x:(x["start_beat"],x["midi"]))
        for a,b in zip(working,working[1:]):
            max_d=max(0.08,b["start_beat"]-a["start_beat"]-0.04)
            a["duration_beats"]=round(min(a["duration_beats"],max_d),6)
        transforms.append("CHORUS2_MOTIF_REPRISE_RHYTHM_VARIATION")

    if epoch=="OUTRO_1":
        transforms.append("OUTRO_CADENTIAL_FOREGROUND")
        if final_bar and working:
            # Final lead arrival sustains but remains inside the final bar.
            last=working[-1]
            bar_start=int(float(last["start_beat"])//4)*4
            remaining=(bar_start+4)-float(last["start_beat"])
            last["duration_beats"]=round(max(last["duration_beats"],min(1.5,remaining-0.05)),6)
            transforms.append("FINAL_LEAD_SUSTAIN")

    return working,transforms


def execute()->dict[str,Any]:
    seed=load_seed("ROCK")
    role_authority=resolve_source_roles("ROCK")
    if role_authority.get("status")!="PASS":
        raise RockV3CoreDevelopmentExecutorError("ROCK_SOURCE_ROLES_NOT_READY")

    form=build_form()
    development=build_development()
    harmony=build_harmony()
    if development["form_plan_sha256"]!=form["form_plan_sha256"]:
        raise RockV3CoreDevelopmentExecutorError("ROCK_DEVELOPMENT_FORM_HASH_MISMATCH")
    if harmony["bar_count"]!=form["bar_count"]:
        raise RockV3CoreDevelopmentExecutorError("ROCK_HARMONY_FORM_LENGTH_MISMATCH")

    cell_variations=_cell_to_variations(seed)
    patterns=_pattern_map(seed)
    source_roles=_source_role_map(seed)
    role_mappings={x["role"]:x for x in role_authority["role_mappings"]}
    harmony_by_bar={x["bar"]:x["chord_symbol"] for x in harmony["bars"]}
    development_by_bar={x["bar"]:x for x in development["bars"]}

    events=[]
    transform_manifest=[]
    previous_lead_pitch=None

    for bar in range(40):
        spec=development_by_bar[bar]
        cell=spec["source_cell"]
        symbol=harmony_by_bar[bar]
        final_bar=bar==39
        per_bar_transforms=[]

        for role,source_role in source_roles.items():
            pattern=patterns[role]
            variation=cell_variations[cell][role]
            source_notes=pattern["variations"][variation]
            notes,transforms=_structural_transform_notes(
                role=role,
                notes=source_notes,
                bar_spec=spec,
                final_bar=final_bar,
            )
            per_bar_transforms.extend(transforms)

            mapping=role_mappings[role]
            playable=source_role.get("playable_midi_range")
            for note in notes:
                beat=_frac(note["beat"])
                duration=_frac(note["duration"])
                if not (Fraction(0)<=beat<Fraction(4)) or duration<=0:
                    raise RockV3CoreDevelopmentExecutorError("ROCK_EVENT_TIMING_INVALID")

                if pattern["kind"]=="CHORD_RELATIVE":
                    midi=_realize_degree(symbol,int(note["degree"]),int(note["octave"]))
                elif pattern["kind"]=="DRUM_ABSOLUTE":
                    midi=int(note["midi"])
                else:
                    raise RockV3CoreDevelopmentExecutorError(
                        "ROCK_PATTERN_KIND_UNSUPPORTED::"+str(pattern["kind"])
                    )

                if (
                    isinstance(playable,list) and len(playable)==2
                    and not int(playable[0])<=midi<=int(playable[1])
                ):
                    raise RockV3CoreDevelopmentExecutorError(
                        "ROCK_EVENT_OUTSIDE_ROLE_RANGE::"+role
                    )

                event={
                    "track_id":role,
                    "role":role,
                    "instrument_id":mapping["instrument_id"],
                    "source_instrument_id":mapping["source_instrument_id"],
                    "start_beat":float(Fraction(bar*4)+beat),
                    "duration_beats":float(duration),
                    "midi":midi,
                    "velocity":int(note["velocity"]),
                    "section":spec["section_id"],
                    "section_type":spec["section_type"],
                    "source_cell":cell,
                    "source_variation":variation,
                    "source_cell_occurrence":spec["source_cell_occurrence"],
                    "chord_symbol":symbol,
                    "foreground_owner":spec["foreground_owner"],
                    "arrangement_role":(
                        "SUPPORTING_HARMONY"
                        if role=="HARMONY" and spec["foreground_owner"]=="LEAD_GUITAR"
                        else "FOREGROUND_RIFF"
                        if role=="HARMONY"
                        else "FOUNDATION"
                    ),
                    "source_rule":"ROCK_V3_CORE_DEVELOPED_SOURCE_PATTERN",
                    "symbolic_only":True,
                }
                events.append(event)

        motif_id=_lead_motif_for_bar(spec)
        if spec["foreground_owner"]=="LEAD_GUITAR":
            if motif_id is None:
                raise RockV3CoreDevelopmentExecutorError(
                    "ROCK_LEAD_WINDOW_WITHOUT_MOTIF::"+cell
                )
            chord={
                "symbol":symbol,
                "root_pc":CHORDS[symbol]["root_pc"],
                "quality":CHORDS[symbol]["quality"],
            }
            lead,previous_lead_pitch=compose_foreground_bar(
                bar=bar,
                section=cell,
                motif_id=motif_id,
                chord=chord,
                previous_pitch=previous_lead_pitch,
            )
            lead,lead_transforms=_vary_lead_events(
                lead,bar_spec=spec,final_bar=final_bar
            )
            per_bar_transforms.extend(lead_transforms)
            for event in lead:
                event=deepcopy(event)
                event["section"]=spec["section_id"]
                event["section_type"]=spec["section_type"]
                event["source_cell"]=cell
                event["source_cell_occurrence"]=spec["source_cell_occurrence"]
                event["chord_symbol"]=symbol
                event["source_rule"]="ROCK_V3_CORE_DEVELOPED_FOREGROUND"
                event["source_motif_id"]=motif_id
                event["symbolic_only"]=True
                events.append(event)

        # Every recurrent source-cell bar must show a non-velocity structural
        # transformation somewhere in that bar.
        if spec["source_cell_recurrence"] and not per_bar_transforms:
            raise RockV3CoreDevelopmentExecutorError(
                "ROCK_RECURRENT_BAR_WITHOUT_STRUCTURAL_TRANSFORM::"+str(bar)
            )

        transform_manifest.append({
            "bar":bar,
            "section_id":spec["section_id"],
            "source_cell":cell,
            "source_cell_occurrence":spec["source_cell_occurrence"],
            "source_cell_recurrence":spec["source_cell_recurrence"],
            "chord_symbol":symbol,
            "foreground_owner":spec["foreground_owner"],
            "applied_transforms":sorted(set(per_bar_transforms)),
        })

    events.sort(key=lambda x:(
        float(x["start_beat"]),
        str(x["track_id"]),
        int(x.get("midi") or 0),
    ))
    if not events:
        raise RockV3CoreDevelopmentExecutorError("ROCK_DEVELOPED_EVENTS_EMPTY")

    # No event may escape the 40-bar piece.
    for e in events:
        start=float(e["start_beat"])
        duration=float(e["duration_beats"])
        if start<0 or duration<=0 or start+duration>160.000001:
            raise RockV3CoreDevelopmentExecutorError("ROCK_DEVELOPED_EVENT_OUT_OF_RANGE")

    result={
        "schema":SCHEMA,
        "status":"PASS",
        "genre":"ROCK",
        "profile_id":"ROCK_CORE_V2",
        "resolved_variant":None,
        "family_baseline_only":True,
        "meter":"4/4",
        "tempo_bpm":seed["tempo_bpm"],
        "bar_count":40,
        "duration_seconds":40*4*60/seed["tempo_bpm"],
        "form_plan_sha256":form["form_plan_sha256"],
        "development_plan_sha256":development["development_plan_sha256"],
        "harmony_plan_sha256":harmony["harmony_plan_sha256"],
        "instrument_authority":role_authority,
        "events":events,
        "event_count":len(events),
        "transform_manifest":transform_manifest,
        "legacy_note_generator_used":False,
        "old_genre_development_patch_used":False,
        "generic_progression_engine_used":False,
        "generic_octave_flip_used":False,
        "random_jitter_used":False,
        "cross_genre_melody_copy_used":False,
        "new_instrument_role_invented":False,
        "audio_generated":False,
        "audio_authority":False,
        "finished_composition_authority":False,
        "live_runtime_authority":False,
        "reasoning_engine_used":False,
        "research_candidate_only":True,
        "musical_quality_proven":False,
        "listening_approval":False,
        "performance_realization_applied":False,
        "render_allowed":False,
        "next_gate":"ROCK_CORE_DEVELOPED_EVENT_AUDIT__THEN_PERFORMANCE_PLAN__NO_AUDIO_YET",
    }
    result["execution_sha256"]=_sha({
        k:v for k,v in result.items() if k!="execution_sha256"
    })
    return result
