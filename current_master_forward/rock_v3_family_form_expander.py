"""Neutral ROCK_CORE_V2 family-baseline form research candidate.

This module expands the seven one-bar original Rock source patterns into a
36-bar structural candidate without claiming a Rock subgenre.

Allowed authority:
- V3 family baseline only when no subgenre cues are available;
- original source-pattern variation vocabulary;
- original source-seed chord vocabulary Em/C/G/D only;
- structurally validated Rock foreground motif vocabulary.

Not allowed:
- inventing Classic/Hard/Alternative/etc. rules;
- treating source-seed harmony as universal Rock harmony;
- generic melody fallback;
- audio/live promotion.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any

from genre_v3_source_pattern_bridge import load_seed
from genre_v3_symbolic_pattern_executor import realize_variation_bar, parse_chord
from rock_v3_foreground_pilot import _compose_bar
from rock_v3_variant_resolver import resolve as resolve_rock_variant

SCHEMA="ROCK_V3_FAMILY_FORM_EXPANSION_001"
PROFILE_ID="ROCK_CORE_V2"
CHORD_CYCLE=("Em","C","G","D")

# Five V3-compatible phrase blocks: a 4-bar intro, then four 8-bar phrases.
# Each micro-pattern name comes from the original project-authored source seed.
FORM_SPEC=(
    {
        "formal_section":"INTRO",
        "length_bars":4,
        "micro_sections":("INTRO","VERSE_A","VERSE_RESPONSE","FILL"),
        "lead_motifs":(None,None,None,None),
    },
    {
        "formal_section":"VERSE_1",
        "length_bars":8,
        "micro_sections":(
            "VERSE_A","VERSE_RESPONSE","VERSE_A","VERSE_RESPONSE",
            "VERSE_A","VERSE_RESPONSE","VERSE_A","FILL",
        ),
        "lead_motifs":(
            "A_CALL",None,None,None,
            "A_REPRISE",None,None,None,
        ),
    },
    {
        "formal_section":"CHORUS_1",
        "length_bars":8,
        "micro_sections":(
            "CHORUS_B","CHORUS_RESPONSE","CHORUS_B","CHORUS_RESPONSE",
            "CHORUS_B","CHORUS_RESPONSE","CHORUS_B","FILL",
        ),
        "lead_motifs":(
            "B_LIFT",None,None,None,
            "A_REPRISE",None,None,None,
        ),
    },
    {
        "formal_section":"VERSE_2",
        "length_bars":8,
        "micro_sections":(
            "VERSE_A","VERSE_RESPONSE","VERSE_A","VERSE_RESPONSE",
            "VERSE_A","VERSE_RESPONSE","VERSE_A","FILL",
        ),
        "lead_motifs":(
            "A_REPRISE",None,None,None,
            "A_ANSWER",None,None,None,
        ),
    },
    {
        "formal_section":"CHORUS_2",
        "length_bars":8,
        "micro_sections":(
            "CHORUS_B","CHORUS_RESPONSE","CHORUS_B","CHORUS_RESPONSE",
            "CHORUS_B","CHORUS_RESPONSE","CHORUS_B","ENDING",
        ),
        "lead_motifs":(
            "B_LIFT",None,None,None,
            "A_REPRISE",None,None,"CADENCE",
        ),
    },
)


class RockV3FamilyFormError(RuntimeError):
    pass


def _sha(value:Any)->str:
    return hashlib.sha256(
        json.dumps(value,sort_keys=True,separators=(",",":"),default=str).encode()
    ).hexdigest()


def _bar_chord(local_bar:int, formal_section:str)->str:
    if formal_section=="CHORUS_2" and local_bar==7:
        return "Em"
    return CHORD_CYCLE[local_bar % len(CHORD_CYCLE)]


def _source_section_map(seed:dict[str,Any])->dict[str,dict[str,Any]]:
    rows={x["name"]:x for x in seed.get("sections") or []}
    required={
        "INTRO","VERSE_A","VERSE_RESPONSE","FILL",
        "CHORUS_B","CHORUS_RESPONSE","ENDING",
    }
    if set(rows)!=required:
        raise RockV3FamilyFormError("ROCK_SOURCE_MICRO_SECTION_SET_CHANGED")
    return rows


def expand(
    *,
    variant_name:str|None=None,
    variant_cues_present:bool=False,
)->dict[str,Any]:
    gate=resolve_rock_variant(
        variant_name,
        variant_cues_present=variant_cues_present,
    )
    if gate.get("status")=="ROCK_VARIANT_REQUIRED_BY_AVAILABLE_CUES":
        raise RockV3FamilyFormError(
            "ROCK_VARIANT_CUES_PRESENT__FAMILY_BASELINE_EXPANSION_REFUSED"
        )
    if gate.get("selected_variant") is not None:
        raise RockV3FamilyFormError(
            "ROCK_SELECTED_VARIANT_REQUIRES_EVIDENCE_BACKED_MUSICAL_PACKAGE"
        )
    if gate.get("status")!="ROCK_CORE_BASELINE_ALLOWED__NO_VARIANT_CUES":
        raise RockV3FamilyFormError("ROCK_CORE_BASELINE_GATE_NOT_OPEN")
    if gate.get("family_baseline_music_allowed") is not True:
        raise RockV3FamilyFormError("ROCK_CORE_BASELINE_PERMISSION_MISSING")

    seed=load_seed("ROCK")
    if seed.get("profile_id")!=PROFILE_ID:
        raise RockV3FamilyFormError("ROCK_PROFILE_ID_DRIFT")
    if seed.get("meter")!="4/4":
        raise RockV3FamilyFormError("ROCK_CORE_FORM_REQUIRES_4_4")
    source_sections=_source_section_map(seed)

    events=[]
    bar_plan=[]
    thinning=[]
    previous_lead_pitch=None
    destination_bar=0

    for phrase_index,phrase in enumerate(FORM_SPEC):
        length=int(phrase["length_bars"])
        micro_sections=tuple(phrase["micro_sections"])
        lead_motifs=tuple(phrase["lead_motifs"])
        if length not in (4,8):
            raise RockV3FamilyFormError("ROCK_CORE_PHRASE_LENGTH_NOT_4_OR_8")
        if len(micro_sections)!=length or len(lead_motifs)!=length:
            raise RockV3FamilyFormError("ROCK_CORE_FORM_SPEC_LENGTH_MISMATCH")

        for local_bar,(micro_section,motif_id) in enumerate(
            zip(micro_sections,lead_motifs)
        ):
            chord_symbol=_bar_chord(local_bar,phrase["formal_section"])
            source_section=source_sections[micro_section]
            raw=realize_variation_bar(
                "ROCK",
                variation_by_role=dict(source_section["variation_by_role"]),
                chord_symbol=chord_symbol,
                destination_bar=destination_bar,
                section_name=micro_section,
            )

            lead_active=motif_id is not None
            harmony=[
                e for e in raw if e["role"]=="HARMONY"
            ]
            earliest_harmony=min(
                harmony,
                key=lambda x:(float(x["start_beat"]),int(x["midi"]))
            ) if harmony else None

            arranged=[]
            for event in raw:
                item=deepcopy(event)
                item["formal_section"]=phrase["formal_section"]
                item["formal_section_bar"]=local_bar
                item["phrase_index"]=phrase_index
                item["phrase_length_bars"]=length
                item["family_baseline_identity"]=PROFILE_ID
                item["resolved_rock_variant"]=None

                if item["role"]=="HARMONY" and lead_active:
                    if event is not earliest_harmony:
                        thinning.append({
                            "bar":destination_bar,
                            "formal_section":phrase["formal_section"],
                            "formal_section_bar":local_bar,
                            "micro_section":micro_section,
                            "start_beat":item["start_beat"],
                            "reason":"YIELD_DENSITY_TO_LEAD_GUITAR",
                        })
                        continue
                    item["foreground_owner"]="LEAD_GUITAR"
                    item["arrangement_role"]="SUPPORTING_HARMONY"
                    item["source_rule"]="V3_ROCK_CORE_FORM_RHYTHM_GUITAR_YIELD"
                elif item["role"]=="HARMONY":
                    item["foreground_owner"]="HARMONY_RIFF"
                    item["arrangement_role"]="FOREGROUND_RIFF"
                else:
                    item["foreground_owner"]=(
                        "LEAD_GUITAR" if lead_active else "HARMONY_RIFF"
                    )
                    item["arrangement_role"]="FOUNDATION"
                arranged.append(item)

            lead=[]
            if lead_active:
                lead,previous_lead_pitch=_compose_bar(
                    bar=destination_bar,
                    section=micro_section,
                    motif_id=motif_id,
                    chord=parse_chord(chord_symbol),
                    previous_pitch=previous_lead_pitch,
                )
                for item in lead:
                    item["formal_section"]=phrase["formal_section"]
                    item["formal_section_bar"]=local_bar
                    item["phrase_index"]=phrase_index
                    item["phrase_length_bars"]=length
                    item["family_baseline_identity"]=PROFILE_ID
                    item["resolved_rock_variant"]=None
                    item["source_rule"]="ROCK_V3_CORE_FORM_FOREGROUND_CANDIDATE"

            events.extend(arranged)
            events.extend(lead)
            bar_plan.append({
                "bar":destination_bar,
                "formal_section":phrase["formal_section"],
                "formal_section_bar":local_bar,
                "phrase_index":phrase_index,
                "phrase_length_bars":length,
                "micro_section":micro_section,
                "chord_symbol":chord_symbol,
                "foreground_owner":"LEAD_GUITAR" if lead_active else "HARMONY_RIFF",
                "lead_motif":motif_id,
                "boundary_transition":micro_section=="FILL",
                "ending_bar":micro_section=="ENDING",
            })
            destination_bar+=1

    events.sort(
        key=lambda x:(
            float(x["start_beat"]),
            str(x["track_id"]),
            int(x.get("midi") or 0),
        )
    )

    if destination_bar!=36:
        raise RockV3FamilyFormError(
            "ROCK_CORE_FORM_BAR_COUNT_CHANGED::"+str(destination_bar)
        )
    if not events:
        raise RockV3FamilyFormError("ROCK_CORE_FORM_EMPTY")

    result={
        "schema":SCHEMA,
        "status":"PASS",
        "genre":"ROCK",
        "profile_id":PROFILE_ID,
        "family_baseline_identity":PROFILE_ID,
        "resolved_rock_variant":None,
        "variant_gate":gate,
        "variant_cues_present":False,
        "family_baseline_must_not_claim_subgenre":True,
        "tempo_bpm":int(seed["tempo_bpm"]),
        "meter":seed["meter"],
        "bar_count":destination_bar,
        "duration_seconds":destination_bar*4*60/int(seed["tempo_bpm"]),
        "phrase_lengths_bars":[int(x["length_bars"]) for x in FORM_SPEC],
        "formal_sections":[x["formal_section"] for x in FORM_SPEC],
        "bar_plan":bar_plan,
        "source_seed_id":seed["seed_id"],
        "source_micro_pattern_authority":"ORIGINAL_PROJECT_AUTHORED_SYMBOLIC_SEED",
        "source_harmony_policy":"SOURCE_SEED_BASELINE_ONLY__NOT_SUBGENRE_AUTHORITY",
        "source_chord_vocabulary":list(CHORD_CYCLE),
        "new_chord_vocabulary_added":False,
        "rhythm_guitar_thinning_manifest":thinning,
        "events":events,
        "event_count":len(events),
        "lead_event_count":sum(1 for e in events if e.get("role")=="LEAD_GUITAR"),
        "audio_authority":False,
        "audio_generated":False,
        "live_runtime_authority":False,
        "finished_composition_authority":False,
        "musical_audition_approved":False,
        "research_candidate_only":True,
        "reasoning_engine_used":False,
        "generic_melody_generator_used":False,
        "legacy_note_generator_used":False,
        "promotion_gate":"STRUCTURAL_FORM_VALIDATION__THEN_DEVELOPMENT_AND_RESOURCE_CAPABILITY__THEN_LISTENING",
        "next_gate":"ROCK_CORE_FORM_STRUCTURAL_AUDIT",
    }
    result["execution_sha256"]=_sha({
        k:v for k,v in result.items() if k!="execution_sha256"
    })
    return result
