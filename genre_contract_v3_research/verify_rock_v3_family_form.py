"""Structural audit for the neutral ROCK_CORE_V2 36-bar form candidate."""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
FORWARD=ROOT/"current_master_forward"
if str(FORWARD) not in sys.path:
    sys.path.insert(0,str(FORWARD))

from rock_v3_family_form_expander import (
    expand, RockV3FamilyFormError, CHORD_CYCLE
)
from genre_v3_symbolic_pattern_executor import parse_chord


def mean(values):
    return sum(values)/len(values) if values else 0.0


def chord_pcs(symbol):
    chord=parse_chord(symbol)
    root=int(chord["root_pc"])
    q=chord.get("quality") or ""
    if q=="m":
        ints=(0,3,7)
    elif q in ("","maj7"):
        ints=(0,4,7)
    elif q=="7":
        ints=(0,4,7,10)
    else:
        raise RuntimeError("UNSUPPORTED_ROCK_AUDIT_CHORD_QUALITY::"+q)
    return {(root+x)%12 for x in ints}


def expect_refusal(**kwargs):
    try:
        expand(**kwargs)
    except RockV3FamilyFormError:
        return
    raise RuntimeError("ROCK_FAMILY_FORM_SHOULD_HAVE_REFUSED::"+json.dumps(kwargs,sort_keys=True))


def main():
    expect_refusal(variant_cues_present=True)
    expect_refusal(variant_name="Classic rock",variant_cues_present=True)

    result=expand(variant_cues_present=False)
    if result.get("status")!="PASS":
        raise RuntimeError("ROCK_CORE_FORM_NOT_PASS")
    if result.get("family_baseline_identity")!="ROCK_CORE_V2":
        raise RuntimeError("ROCK_CORE_FORM_IDENTITY_CHANGED")
    if result.get("resolved_rock_variant") is not None:
        raise RuntimeError("ROCK_CORE_FORM_FALSELY_CLAIMED_SUBGENRE")
    if result.get("family_baseline_must_not_claim_subgenre") is not True:
        raise RuntimeError("ROCK_CORE_FORM_SUBGENRE_GUARD_MISSING")
    if result.get("bar_count")!=36:
        raise RuntimeError("ROCK_CORE_FORM_NOT_36_BARS")
    if result.get("phrase_lengths_bars")!=[4,8,8,8,8]:
        raise RuntimeError("ROCK_CORE_FORM_PHRASE_LENGTHS_CHANGED")
    if result.get("formal_sections")!=[
        "INTRO","VERSE_1","CHORUS_1","VERSE_2","CHORUS_2"
    ]:
        raise RuntimeError("ROCK_CORE_FORM_SECTION_ORDER_CHANGED")
    if result.get("source_harmony_policy")!="SOURCE_SEED_BASELINE_ONLY__NOT_SUBGENRE_AUTHORITY":
        raise RuntimeError("ROCK_CORE_FORM_HARMONY_AUTHORITY_OVERCLAIMED")
    if result.get("new_chord_vocabulary_added") is not False:
        raise RuntimeError("ROCK_CORE_FORM_ADDED_CHORD_VOCABULARY")
    if set(result.get("source_chord_vocabulary") or [])!=set(CHORD_CYCLE):
        raise RuntimeError("ROCK_CORE_FORM_SOURCE_CHORD_VOCABULARY_CHANGED")

    plan=result["bar_plan"]
    if len(plan)!=36 or [x["bar"] for x in plan]!=list(range(36)):
        raise RuntimeError("ROCK_CORE_FORM_BAR_PLAN_INVALID")
    if any(x["phrase_length_bars"] not in (4,8) for x in plan):
        raise RuntimeError("ROCK_CORE_FORM_NON_4_OR_8_PHRASE")

    # FILL is a phrase-boundary transition, never a generic every-bar decoration.
    fill_rows=[x for x in plan if x["micro_section"]=="FILL"]
    if len(fill_rows)!=4:
        raise RuntimeError("ROCK_CORE_FORM_FILL_COUNT_CHANGED")
    if any(x["formal_section_bar"]!=x["phrase_length_bars"]-1 for x in fill_rows):
        raise RuntimeError("ROCK_CORE_FORM_FILL_NOT_AT_BOUNDARY")
    if any(not x["boundary_transition"] for x in fill_rows):
        raise RuntimeError("ROCK_CORE_FORM_FILL_BOUNDARY_FLAG_MISSING")
    if sum(1 for x in plan if x["ending_bar"])!=1 or not plan[-1]["ending_bar"]:
        raise RuntimeError("ROCK_CORE_FORM_ENDING_NOT_FINAL_BAR")

    chords=[x["chord_symbol"] for x in plan]
    if not set(chords).issubset(set(CHORD_CYCLE)):
        raise RuntimeError("ROCK_CORE_FORM_OUTSIDE_SOURCE_CHORD_VOCABULARY")
    if chords[-1]!="Em":
        raise RuntimeError("ROCK_CORE_FORM_FINAL_CHORD_NOT_SOURCE_TONIC")

    events=result["events"]
    if not events:
        raise RuntimeError("ROCK_CORE_FORM_EMPTY")
    expected_instruments={
        "electric_bass_guitar","electric_guitar",
        "kick_drum_rock","snare_drum","hi_hat",
    }
    if {e["instrument_id"] for e in events}!=expected_instruments:
        raise RuntimeError("ROCK_CORE_FORM_INSTRUMENT_SET_CHANGED")

    # Every bar keeps the protected rhythm-section identities.
    protected={"BASS","KICK","SNARE","HAT"}
    roles_by_bar=defaultdict(set)
    for e in events:
        bar=int(float(e["start_beat"])//4)
        roles_by_bar[bar].add(e["role"])
        if not 0<=bar<36:
            raise RuntimeError("ROCK_CORE_FORM_EVENT_OUTSIDE_FORM")
        if float(e["start_beat"])+float(e["duration_beats"])>(bar+1)*4+1e-9:
            raise RuntimeError("ROCK_CORE_FORM_EVENT_CROSSES_BAR")
    for bar in range(36):
        missing=protected-roles_by_bar[bar]
        if missing:
            raise RuntimeError(
                "ROCK_CORE_FORM_FOUNDATION_ROLE_MISSING::"+
                str(bar)+"::"+",".join(sorted(missing))
            )

    # Response bars must remain lead-free and return agency to the riff layer.
    lead=[e for e in events if e["role"]=="LEAD_GUITAR"]
    lead_bars={int(e["start_beat"]//4) for e in lead}
    response_bars={
        x["bar"] for x in plan
        if x["micro_section"] in ("VERSE_RESPONSE","CHORUS_RESPONSE")
    }
    if lead_bars & response_bars:
        raise RuntimeError("ROCK_CORE_FORM_LEAD_ENTERED_RESPONSE_BAR")
    if any(x["foreground_owner"]!="HARMONY_RIFF" for x in plan if x["bar"] in response_bars):
        raise RuntimeError("ROCK_CORE_FORM_RESPONSE_OWNER_WRONG")
    if not lead_bars:
        raise RuntimeError("ROCK_CORE_FORM_HAS_NO_FOREGROUND_WINDOWS")
    if len(lead_bars)>=18:
        raise RuntimeError("ROCK_CORE_FORM_LEAD_NOT_SELECTIVE")

    # Every lead bar must create real arrangement space: exactly one surviving
    # rhythm-guitar support event, not a parallel full-density rhythm track.
    harmony_by_bar=defaultdict(list)
    for e in events:
        if e["role"]=="HARMONY":
            harmony_by_bar[int(e["start_beat"]//4)].append(e)
    for bar in lead_bars:
        if len(harmony_by_bar[bar])!=1:
            raise RuntimeError(
                "ROCK_CORE_FORM_LEAD_WINDOW_RHYTHM_GUITAR_NOT_THINNED::"+
                str(bar)
            )
    if result.get("rhythm_guitar_thinning_manifest")==[]:
        raise RuntimeError("ROCK_CORE_FORM_NO_RHYTHM_GUITAR_YIELD")

    # First/final note of each lead window lands on the active source-seed chord.
    lead_by_bar=defaultdict(list)
    for e in lead:
        lead_by_bar[int(e["start_beat"]//4)].append(e)
    for bar,rows in lead_by_bar.items():
        rows.sort(key=lambda x:x["start_beat"])
        pcs=chord_pcs(plan[bar]["chord_symbol"])
        if rows[0]["midi"]%12 not in pcs:
            raise RuntimeError("ROCK_CORE_FORM_LEAD_OPENING_NOT_CHORD_TONE::"+str(bar))
        if rows[-1]["midi"]%12 not in pcs:
            raise RuntimeError("ROCK_CORE_FORM_LEAD_CLOSE_NOT_CHORD_TONE::"+str(bar))

    # Lead events may not overlap each other.
    ordered=sorted(lead,key=lambda x:x["start_beat"])
    for a,b in zip(ordered,ordered[1:]):
        if a["start_beat"]+a["duration_beats"]>b["start_beat"]+1e-9:
            raise RuntimeError("ROCK_CORE_FORM_LEAD_OVERLAP")

    # Source B patterns should produce an objective chorus lift versus A patterns
    # without adding a new instrument or a gain-only foreground trick.
    accompaniment=[e for e in events if e["role"]!="LEAD_GUITAR"]
    by_form=defaultdict(list)
    for e in accompaniment:
        by_form[e["formal_section"]].append(e)
    verse_velocity=mean([
        e["velocity"] for section in ("VERSE_1","VERSE_2")
        for e in by_form[section]
    ])
    chorus_velocity=mean([
        e["velocity"] for section in ("CHORUS_1","CHORUS_2")
        for e in by_form[section]
    ])
    verse_density=mean([
        len([e for e in by_form[section] if int(e["start_beat"]//4)==bar])
        for section in ("VERSE_1","VERSE_2")
        for bar in [x["bar"] for x in plan if x["formal_section"]==section]
    ])
    chorus_density=mean([
        len([e for e in by_form[section] if int(e["start_beat"]//4)==bar])
        for section in ("CHORUS_1","CHORUS_2")
        for bar in [x["bar"] for x in plan if x["formal_section"]==section]
    ])
    if chorus_velocity<=verse_velocity:
        raise RuntimeError(
            f"ROCK_CORE_FORM_NO_CHORUS_VELOCITY_LIFT::{verse_velocity:.3f}::{chorus_velocity:.3f}"
        )
    if chorus_density<=verse_density:
        raise RuntimeError(
            f"ROCK_CORE_FORM_NO_CHORUS_DENSITY_LIFT::{verse_density:.3f}::{chorus_density:.3f}"
        )

    # Safety/promotional gates.
    for key in (
        "audio_authority","audio_generated","live_runtime_authority",
        "finished_composition_authority","musical_audition_approved",
        "reasoning_engine_used","generic_melody_generator_used",
        "legacy_note_generator_used",
    ):
        if result.get(key) is not False:
            raise RuntimeError("ROCK_CORE_FORM_SAFETY_FLAG_ESCALATED::"+key)

    summary={
        "status":"PASS",
        "diagnostic_only":True,
        "genre":"ROCK",
        "profile_id":"ROCK_CORE_V2",
        "resolved_rock_variant":None,
        "subgenre_claimed":False,
        "bar_count":36,
        "duration_seconds":round(result["duration_seconds"],3),
        "phrase_lengths_bars":result["phrase_lengths_bars"],
        "formal_sections":result["formal_sections"],
        "fill_boundary_bar_count":len(fill_rows),
        "lead_window_bar_count":len(lead_bars),
        "lead_event_count":len(lead),
        "response_bar_count":len(response_bars),
        "rhythm_guitar_events_removed_for_space":len(result["rhythm_guitar_thinning_manifest"]),
        "verse_mean_accompaniment_velocity":round(verse_velocity,3),
        "chorus_mean_accompaniment_velocity":round(chorus_velocity,3),
        "verse_mean_accompaniment_events_per_bar":round(verse_density,3),
        "chorus_mean_accompaniment_events_per_bar":round(chorus_density,3),
        "source_harmony_policy":result["source_harmony_policy"],
        "source_chord_vocabulary":result["source_chord_vocabulary"],
        "variant_cues_refusal":"PASS",
        "selected_variant_without_package_refusal":"PASS",
        "audio_generated":False,
        "finished_composition_authority":False,
        "musical_quality_proven":False,
        "listening_approval":False,
        "result":(
            "The seven one-bar Rock source patterns now function as micro-pattern "
            "vocabulary inside a 36-bar ROCK_CORE_V2 family-baseline form with 4/8-bar "
            "phrasing, explicit verse/chorus contrast, boundary fills and selective "
            "lead/riff handoffs. The package refuses subgenre cues and does not claim "
            "subgenre-specific harmony or finished-composition authority."
        ),
        "next_gate":"ROCK_CORE_PHRASE_LEVEL_DEVELOPMENT_AND_CAPABILITY_AUDIT_BEFORE_AUDIO",
        "execution_sha256":result["execution_sha256"],
    }
    out=ROOT/"genre_contract_v3_research"/"ROCK_V3_FAMILY_FORM_AUDIT.json"
    out.write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps(summary,indent=2))


if __name__=="__main__":
    main()
