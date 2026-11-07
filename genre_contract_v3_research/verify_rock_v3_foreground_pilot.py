"""Structural audit for the Rock V3 foreground research pilot."""
from __future__ import annotations

from pathlib import Path
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
FORWARD=ROOT/"current_master_forward"
if str(FORWARD) not in sys.path:
    sys.path.insert(0,str(FORWARD))

from rock_v3_foreground_pilot import realize, SECTION_PLAN, E_NATURAL_MINOR_PCS
from genre_v3_symbolic_pattern_executor import compile_seed


def chord_pcs(chord):
    root=int(chord["root_pc"])
    q=chord.get("quality") or ""
    if q=="m":
        ints=(0,3,7)
    elif q in ("","maj7"):
        ints=(0,4,7)
    elif q=="7":
        ints=(0,4,7,10)
    else:
        raise RuntimeError("UNSUPPORTED_TEST_CHORD_QUALITY:"+str(q))
    return {(root+x)%12 for x in ints}


def comparable(event):
    return {
        k:event.get(k)
        for k in (
            "track_id","role","instrument_id","start_beat","duration_beats",
            "midi","velocity","section","variation","source_seed_id",
            "source_pattern_kind","source_rule","symbolic_only"
        )
        if k in event
    }


def main():
    source=compile_seed("ROCK")
    pilot=realize()
    if pilot.get("status")!="PASS":
        raise RuntimeError("ROCK_FOREGROUND_PILOT_NOT_PASS")
    gate=pilot.get("rock_variant_gate") or {}
    if gate.get("status")!="ROCK_VARIANT_REQUIRED":
        raise RuntimeError("ROCK_VARIANT_GATE_NOT_ACTIVE")
    if pilot.get("resolved_rock_variant") is not None:
        raise RuntimeError("ROCK_VARIANT_WAS_SILENTLY_DEFAULTED")
    if pilot.get("variant_specific_music_ready") is not False:
        raise RuntimeError("ROCK_VARIANT_MUSIC_FABRICATED")
    if pilot.get("song_form_expansion_ready") is not False:
        raise RuntimeError("ROCK_FORM_EXPANSION_PREMATURELY_READY")
    if pilot.get("audio_generated") is not False or pilot.get("audio_authority") is not False:
        raise RuntimeError("ROCK_FOREGROUND_AUDIO_ESCALATION")
    if pilot.get("live_runtime_authority") is not False:
        raise RuntimeError("ROCK_FOREGROUND_LIVE_ESCALATION")
    if pilot.get("generic_melody_generator_used") is not False:
        raise RuntimeError("GENERIC_MELODY_GENERATOR_ENTERED_ROCK_PILOT")
    if pilot.get("legacy_note_generator_used") is not False:
        raise RuntimeError("LEGACY_NOTE_GENERATOR_ENTERED_ROCK_PILOT")

    events=pilot["events"]
    lead=sorted(
        [e for e in events if e.get("role")=="LEAD_GUITAR"],
        key=lambda x:x["start_beat"]
    )
    if not lead:
        raise RuntimeError("ROCK_FOREGROUND_PILOT_HAS_NO_LEAD")

    expected_sections={
        name for name,spec in SECTION_PLAN.items()
        if spec["owner"]=="LEAD_GUITAR"
    }
    actual_sections={e["section"] for e in lead}
    if actual_sections!=expected_sections:
        raise RuntimeError(
            "ROCK_FOREGROUND_SECTION_SET_MISMATCH::"+
            json.dumps(sorted(actual_sections))
        )
    forbidden={
        name for name,spec in SECTION_PLAN.items()
        if spec["owner"]!="LEAD_GUITAR"
    }
    if actual_sections & forbidden:
        raise RuntimeError("ROCK_FOREGROUND_ENTERED_RESPONSE_OR_RIFF_WINDOW")

    # Current electric-guitar identity, not a fabricated lead_guitar instrument.
    if {e["instrument_id"] for e in lead}!={"electric_guitar"}:
        raise RuntimeError("ROCK_FOREGROUND_INSTRUMENT_IDENTITY_CHANGED")

    # Playable and diatonic for this candidate.
    for e in lead:
        if not 59<=int(e["midi"])<=76:
            raise RuntimeError("ROCK_FOREGROUND_OUTSIDE_PILOT_REGISTER")
        if int(e["midi"])%12 not in E_NATURAL_MINOR_PCS:
            raise RuntimeError("ROCK_FOREGROUND_OUTSIDE_CANDIDATE_SCALE")
        if e["duration_beats"]<=0:
            raise RuntimeError("ROCK_FOREGROUND_NONPOSITIVE_DURATION")
        bar=int(float(e["start_beat"])//4)
        if float(e["start_beat"])+float(e["duration_beats"])>(bar+1)*4+1e-9:
            raise RuntimeError("ROCK_FOREGROUND_NOTE_CROSSES_BAR")

    # No overlapping lead events.
    for a,b in zip(lead,lead[1:]):
        if a["start_beat"]+a["duration_beats"]>b["start_beat"]+1e-9:
            raise RuntimeError("ROCK_FOREGROUND_LEAD_OVERLAP")

    # First and final note of every foreground window are chord tones.
    chords={int(x["bar"]):x for x in source["chords"]}
    bybar={}
    for e in lead:
        bybar.setdefault(int(e["start_beat"]//4),[]).append(e)
    for bar,notes in bybar.items():
        notes.sort(key=lambda x:x["start_beat"])
        pcs=chord_pcs(chords[bar])
        if notes[0]["midi"]%12 not in pcs:
            raise RuntimeError("ROCK_FOREGROUND_OPENING_NOT_CHORD_TONE::"+str(bar))
        if notes[-1]["midi"]%12 not in pcs:
            raise RuntimeError("ROCK_FOREGROUND_RESOLUTION_NOT_CHORD_TONE::"+str(bar))

    # Bass and percussion must be bit-for-bit musically identical to source.
    protected_roles={"BASS","KICK","SNARE","HAT"}
    src_protected=[
        comparable(e) for e in source["events"] if e["role"] in protected_roles
    ]
    out_protected=[
        comparable(e) for e in events if e["role"] in protected_roles
    ]
    if src_protected!=out_protected:
        raise RuntimeError("ROCK_FOREGROUND_CHANGED_PROTECTED_FOUNDATION")

    # HARMONY is allowed to lose density only in lead windows; no new HARMONY notes.
    src_harmony=[e for e in source["events"] if e["role"]=="HARMONY"]
    out_harmony=[e for e in events if e["role"]=="HARMONY"]
    src_key={(e["start_beat"],e["midi"]) for e in src_harmony}
    if any((e["start_beat"],e["midi"]) not in src_key for e in out_harmony):
        raise RuntimeError("ROCK_FOREGROUND_INVENTED_NEW_RHYTHM_GUITAR_NOTE")
    if len(out_harmony)>=len(src_harmony):
        raise RuntimeError("ROCK_FOREGROUND_DID_NOT_CREATE_RHYTHM_GUITAR_SPACE")
    if pilot.get("rhythm_guitar_events_removed_for_space") != len(src_harmony)-len(out_harmony):
        raise RuntimeError("ROCK_FOREGROUND_THINNING_MANIFEST_COUNT_MISMATCH")

    # Non-lead response/riff bars retain all original HARMONY events.
    section_by_bar={}
    for e in source["events"]:
        section_by_bar.setdefault(int(e["start_beat"]//4),e["section"])
    for bar,section in section_by_bar.items():
        if SECTION_PLAN[section]["owner"]=="LEAD_GUITAR":
            continue
        src=[e for e in src_harmony if int(e["start_beat"]//4)==bar]
        out=[e for e in out_harmony if int(e["start_beat"]//4)==bar]
        if len(src)!=len(out):
            raise RuntimeError("ROCK_FOREGROUND_THINNED_NONLEAD_WINDOW::"+section)

    summary={
        "status":"PASS",
        "diagnostic_only":True,
        "audio_generated":False,
        "live_runtime_promoted":False,
        "genre":"ROCK",
        "profile_id":pilot["profile_id"],
        "source_seed_id":pilot["source_seed_id"],
        "foreground_sections":sorted(expected_sections),
        "riff_or_response_sections":sorted(forbidden),
        "lead_event_count":len(lead),
        "unique_lead_pitches":len({e["midi"] for e in lead}),
        "unique_lead_onsets_in_bar":len({round(e["start_beat"]%4,3) for e in lead}),
        "unique_lead_durations":len({round(e["duration_beats"],3) for e in lead}),
        "rhythm_guitar_source_event_count":len(src_harmony),
        "rhythm_guitar_output_event_count":len(out_harmony),
        "rhythm_guitar_events_removed_for_space":len(src_harmony)-len(out_harmony),
        "protected_foundation_roles_unchanged":sorted(protected_roles),
        "generic_melody_generator_used":False,
        "legacy_note_generator_used":False,
        "musical_quality_proven":False,
        "listening_approval":False,
        "rock_variant_gate_status":gate.get("status"),
        "resolved_rock_variant":pilot.get("resolved_rock_variant"),
        "variant_specific_music_ready":pilot.get("variant_specific_music_ready"),
        "song_form_expansion_ready":pilot.get("song_form_expansion_ready"),
        "result":(
            "Rock now has a structurally valid V3 foreground research candidate: "
            "project-authored motif vocabulary creates chord-responsive electric-guitar "
            "lead windows while bass/drums remain untouched and rhythm guitar yields "
            "density. This is not yet listening-approved."
        ),
        "next_gate":"ROCK_VARIANT_MUSICAL_PACKAGE__THEN_FORM_EXPANSION__THEN_RESOURCE_AND_LISTENING",
        "execution_sha256":pilot["execution_sha256"],
    }
    out=ROOT/"genre_contract_v3_research"/"ROCK_V3_FOREGROUND_PILOT_AUDIT.json"
    out.write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps(summary,indent=2))


if __name__=="__main__":
    main()
