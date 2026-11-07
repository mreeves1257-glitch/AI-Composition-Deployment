"""Audit the 40-bar Rock Core V3 symbolic development executor."""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
FORWARD=ROOT/"current_master_forward"
if str(FORWARD) not in sys.path:
    sys.path.insert(0,str(FORWARD))

from genre_v3_source_pattern_bridge import load_seed
from rock_v3_core_development_executor import execute, CHORDS
from rock_v3_core_form_plan import build as build_form


EXPECTED_ROLES={"BASS","HARMONY","KICK","SNARE","HAT","LEAD_GUITAR"}
EXPECTED_TRACK_IDS={"BASS","HARMONY","KICK","SNARE","HAT","LEAD"}
EXPECTED_INSTRUMENTS={
    "electric_bass_guitar","electric_guitar",
    "kick_drum_rock","snare_drum","hi_hat",
}


def structural_signature(events,bar):
    rows=[]
    for e in events:
        if int(float(e["start_beat"])//4)!=bar:
            continue
        rows.append((
            e["track_id"],
            round(float(e["start_beat"])%4,3),
            round(float(e["duration_beats"]),3),
            e.get("source_motif_id"),
            e.get("arrangement_role"),
        ))
    return tuple(sorted(rows))


def source_drum_signature(seed,cell,role):
    section=next(x for x in seed["sections"] if x["name"]==cell)
    variation=section["variation_by_role"][role]
    pattern=next(x for x in seed["patterns"] if x["role"]==role)
    return tuple(sorted(
        (
            round(float(__import__("fractions").Fraction(str(n["beat"]))),3),
            round(float(__import__("fractions").Fraction(str(n["duration"]))),3),
            int(n["midi"]),
        )
        for n in pattern["variations"][variation]
    ))


def main():
    source=load_seed("ROCK")
    form=build_form()
    result=execute()

    if result.get("status")!="PASS":
        raise RuntimeError("ROCK_DEVELOPED_EXECUTION_NOT_PASS")
    if result.get("genre")!="ROCK" or result.get("profile_id")!="ROCK_CORE_V2":
        raise RuntimeError("ROCK_DEVELOPED_EXECUTION_IDENTITY_DRIFT")
    if result.get("resolved_variant") is not None:
        raise RuntimeError("ROCK_DEVELOPED_EXECUTION_SILENTLY_CLAIMED_VARIANT")
    if result.get("family_baseline_only") is not True:
        raise RuntimeError("ROCK_DEVELOPED_EXECUTION_NOT_FAMILY_BASELINE")
    if result.get("bar_count")!=40:
        raise RuntimeError("ROCK_DEVELOPED_EXECUTION_NOT_40_BARS")

    for key in (
        "legacy_note_generator_used","old_genre_development_patch_used",
        "generic_progression_engine_used","generic_octave_flip_used",
        "random_jitter_used","cross_genre_melody_copy_used",
        "new_instrument_role_invented","audio_generated","audio_authority",
        "finished_composition_authority","live_runtime_authority",
        "reasoning_engine_used","musical_quality_proven","listening_approval",
        "performance_realization_applied","render_allowed",
    ):
        if result.get(key) is not False:
            raise RuntimeError("ROCK_DEVELOPED_FORBIDDEN_OR_PREMATURE_FLAG::"+key)

    events=result.get("events") or []
    if not events:
        raise RuntimeError("ROCK_DEVELOPED_EVENTS_EMPTY")
    if result.get("event_count")!=len(events):
        raise RuntimeError("ROCK_DEVELOPED_EVENT_COUNT_MISMATCH")

    roles={e["role"] for e in events}
    if roles!=EXPECTED_ROLES:
        raise RuntimeError(
            "ROCK_DEVELOPED_ROLE_SET_WRONG::"+json.dumps(sorted(roles))
        )
    track_ids={e["track_id"] for e in events}
    if track_ids!=EXPECTED_TRACK_IDS:
        raise RuntimeError(
            "ROCK_DEVELOPED_TRACK_ID_SET_WRONG::"+json.dumps(sorted(track_ids))
        )
    instruments={e["instrument_id"] for e in events}
    if instruments!=EXPECTED_INSTRUMENTS:
        raise RuntimeError(
            "ROCK_DEVELOPED_INSTRUMENT_SET_WRONG::"+json.dumps(sorted(instruments))
        )


    # Rhythm guitar must be actual vertical harmony, not a single-note line
    # mislabeled as HARMONY. Group simultaneous HARMONY events by attack.
    harmony_attacks=defaultdict(list)
    for e in events:
        if e["role"]=="HARMONY":
            harmony_attacks[(round(float(e["start_beat"]),6),e["section"])].append(e)
    if not harmony_attacks:
        raise RuntimeError("ROCK_DEVELOPED_HARMONY_ATTACKS_EMPTY")
    harmony_attack_sizes=[len(rows) for rows in harmony_attacks.values()]
    if min(harmony_attack_sizes)<3:
        raise RuntimeError(
            "ROCK_DEVELOPED_SINGLE_NOTE_OR_DYAD_RHYTHM_GUITAR::"+
            json.dumps(sorted(set(harmony_attack_sizes)))
        )
    for rows in harmony_attacks.values():
        if any(e.get("vertical_voicing") is not True for e in rows):
            raise RuntimeError("ROCK_DEVELOPED_HARMONY_ATTACK_NOT_VERTICAL")
        if len({int(e["midi"]) for e in rows})<3:
            raise RuntimeError("ROCK_DEVELOPED_HARMONY_VOICING_COLLAPSED")
        if any(int(e.get("voicing_size",0))<3 for e in rows):
            raise RuntimeError("ROCK_DEVELOPED_HARMONY_VOICING_SIZE_FLAG_WRONG")
    if result.get("rhythm_guitar_vertical_voicing_used") is not True:
        raise RuntimeError("ROCK_DEVELOPED_VERTICAL_VOICING_RESULT_FLAG_MISSING")
    if result.get("single_note_rhythm_guitar_attack_allowed") is not False:
        raise RuntimeError("ROCK_DEVELOPED_SINGLE_NOTE_RHYTHM_GUITAR_ALLOWED")

    # Every bar is populated and nothing escapes the 40-bar grid.
    events_by_bar=defaultdict(list)
    for e in events:
        start=float(e["start_beat"])
        duration=float(e["duration_beats"])
        if not 0<=start<160:
            raise RuntimeError("ROCK_DEVELOPED_EVENT_START_OUTSIDE_FORM")
        if duration<=0 or start+duration>160.000001:
            raise RuntimeError("ROCK_DEVELOPED_EVENT_DURATION_OUTSIDE_FORM")
        events_by_bar[int(start//4)].append(e)
    if set(events_by_bar)!=set(range(40)):
        raise RuntimeError(
            "ROCK_DEVELOPED_EMPTY_BAR_SET::"+
            json.dumps(sorted(set(range(40))-set(events_by_bar)))
        )

    form_by_bar={x["bar"]:x for x in form["bars"]}
    manifest_by_bar={x["bar"]:x for x in result["transform_manifest"]}
    if set(manifest_by_bar)!=set(range(40)):
        raise RuntimeError("ROCK_DEVELOPED_TRANSFORM_MANIFEST_NOT_40")

    # Lead must follow the form-plan foreground owner exactly.
    for bar in range(40):
        has_lead=any(e["track_id"]=="LEAD" and e["role"]=="LEAD_GUITAR" for e in events_by_bar[bar])
        expected=form_by_bar[bar]["foreground_owner"]=="LEAD_GUITAR"
        if has_lead!=expected:
            raise RuntimeError(
                f"ROCK_DEVELOPED_FOREGROUND_WINDOW_MISMATCH::{bar}::{has_lead}::{expected}"
            )

    # Every recurrent source-cell bar must contain a declared structural transform
    # AND its structural event signature must differ from that cell's first use.
    first_bar_for_cell={}
    recurrence_count=0
    for bar in range(40):
        row=form_by_bar[bar]
        cell=row["source_cell"]
        if cell not in first_bar_for_cell:
            first_bar_for_cell[cell]=bar
            continue
        recurrence_count+=1
        transforms=manifest_by_bar[bar].get("applied_transforms") or []
        if not transforms:
            raise RuntimeError("ROCK_DEVELOPED_RECURRENCE_WITHOUT_TRANSFORM::"+str(bar))
        first=first_bar_for_cell[cell]
        if structural_signature(events,bar)==structural_signature(events,first):
            raise RuntimeError(
                f"ROCK_DEVELOPED_RECURRENCE_STRUCTURALLY_LITERAL::{cell}::{bar}::{first}"
            )
    if recurrence_count<30:
        raise RuntimeError("ROCK_DEVELOPED_TOO_FEW_RECURRENCE_CHECKS")

    # Kick and snare retain source-authored count/timing/duration/pitch for the
    # selected cell. Velocity may follow section energy, but no new drum hits are
    # invented by this executor.
    for bar in range(40):
        cell=form_by_bar[bar]["source_cell"]
        for role in ("KICK","SNARE"):
            actual=tuple(sorted(
                (
                    round(float(e["start_beat"])%4,3),
                    round(float(e["duration_beats"]),3),
                    int(e["midi"]),
                )
                for e in events_by_bar[bar] if e["role"]==role
            ))
            expected=source_drum_signature(source,cell,role)
            if actual!=expected:
                raise RuntimeError(
                    f"ROCK_DEVELOPED_{role}_SOURCE_PATTERN_CHANGED::{bar}::{cell}"
                )

    # Bass/harmony remain chord-responsive to the bar's planned harmony.
    for bar in range(40):
        symbol=manifest_by_bar[bar]["chord_symbol"]
        chord=CHORDS[symbol]
        allowed_scale={
            (chord["root_pc"]+interval)%12 for interval in chord["scale"]
        }
        for e in events_by_bar[bar]:
            if e["role"] in ("BASS","HARMONY") and int(e["midi"])%12 not in allowed_scale:
                raise RuntimeError(
                    f"ROCK_DEVELOPED_PITCH_OUTSIDE_ACTIVE_CHORD_SCALE::{bar}::{e['role']}"
                )

    # Lead phrase beginnings/endings must anchor to current chord tones.
    def chord_tones(symbol):
        c=CHORDS[symbol]
        ints=(0,3,7) if c["quality"]=="m" else (0,4,7)
        return {(c["root_pc"]+x)%12 for x in ints}

    lead_bar_count=0
    for bar in range(40):
        lead=sorted(
            [e for e in events_by_bar[bar] if e["track_id"]=="LEAD" and e["role"]=="LEAD_GUITAR"],
            key=lambda x:x["start_beat"]
        )
        if not lead:
            continue
        lead_bar_count+=1
        tones=chord_tones(manifest_by_bar[bar]["chord_symbol"])
        if lead[0]["midi"]%12 not in tones:
            raise RuntimeError("ROCK_DEVELOPED_LEAD_OPENING_NOT_CHORD_TONE::"+str(bar))
        if lead[-1]["midi"]%12 not in tones:
            raise RuntimeError("ROCK_DEVELOPED_LEAD_ENDING_NOT_CHORD_TONE::"+str(bar))
        for a,b in zip(lead,lead[1:]):
            if a["start_beat"]+a["duration_beats"]>b["start_beat"]+1e-9:
                raise RuntimeError("ROCK_DEVELOPED_LEAD_OVERLAP::"+str(bar))

    if lead_bar_count==0:
        raise RuntimeError("ROCK_DEVELOPED_NO_FOREGROUND_BARS")

    # Later major sections must demonstrate the named V3 development strategy.
    verse2_transforms={
        t for row in result["transform_manifest"]
        if row["section_id"]=="VERSE_2"
        for t in row["applied_transforms"]
    }
    chorus2_transforms={
        t for row in result["transform_manifest"]
        if row["section_id"]=="CHORUS_2"
        for t in row["applied_transforms"]
    }
    if "VERSE2_FOREGROUND_MOTIF_TRANSFORMATION" not in verse2_transforms:
        raise RuntimeError("ROCK_DEVELOPED_VERSE2_MOTIF_TRANSFORM_MISSING")
    if "CHORUS2_MOTIF_REPRISE_RHYTHM_VARIATION" not in chorus2_transforms:
        raise RuntimeError("ROCK_DEVELOPED_CHORUS2_REPRISE_VARIATION_MISSING")
    if "HAT_SELECTIVE_SOFT_SUBDIVISION_REST" not in verse2_transforms|chorus2_transforms:
        raise RuntimeError("ROCK_DEVELOPED_LATER_SECTION_GROOVE_SPACE_MISSING")

    # Final bar must have a true sustained pitched arrival, not another short cell.
    final=events_by_bar[39]
    final_sustains=[
        e for e in final
        if e["role"] in ("BASS","HARMONY","LEAD")
        and e["duration_beats"]>=1.0
    ]
    if len(final_sustains)<2:
        raise RuntimeError("ROCK_DEVELOPED_FINAL_SUSTAINED_ARRIVAL_MISSING")
    final_transforms=manifest_by_bar[39]["applied_transforms"]
    if "FINAL_SUSTAINED_ARRIVAL" not in final_transforms:
        raise RuntimeError("ROCK_DEVELOPED_FINAL_ARRIVAL_TRANSFORM_MISSING")

    # Section event signatures prove the second verse/chorus are not literal copies.
    def section_signature(section_id):
        rows=[]
        section_bars=[b for b,x in form_by_bar.items() if x["section_id"]==section_id]
        first=min(section_bars)
        for bar in section_bars:
            for e in events_by_bar[bar]:
                rows.append((
                    e["role"],
                    round(e["start_beat"]-first*4,3),
                    round(e["duration_beats"],3),
                    e.get("source_motif_id"),
                    e.get("arrangement_role"),
                ))
        return tuple(sorted(rows))

    if section_signature("VERSE_1")==section_signature("VERSE_2"):
        raise RuntimeError("ROCK_DEVELOPED_VERSE2_LITERAL_SECTION_COPY")
    if section_signature("CHORUS_1")==section_signature("CHORUS_2"):
        raise RuntimeError("ROCK_DEVELOPED_CHORUS2_LITERAL_SECTION_COPY")

    summary={
        "status":"PASS",
        "diagnostic_only":True,
        "genre":"ROCK",
        "profile_id":"ROCK_CORE_V2",
        "resolved_variant":None,
        "family_baseline_only":True,
        "bar_count":40,
        "tempo_bpm":result["tempo_bpm"],
        "duration_seconds":round(result["duration_seconds"],3),
        "event_count":len(events),
        "role_count":len(roles),
        "track_id_count":len(track_ids),
        "instrument_count":len(instruments),
        "rhythm_guitar_attack_count":len(harmony_attacks),
        "minimum_rhythm_guitar_attack_pitch_count":min(harmony_attack_sizes),
        "maximum_rhythm_guitar_attack_pitch_count":max(harmony_attack_sizes),
        "single_note_rhythm_guitar_attack_present":False,
        "lead_foreground_bar_count":lead_bar_count,
        "recurrent_bar_count_checked":recurrence_count,
        "all_recurrent_bars_structurally_transformed":True,
        "kick_snare_source_pattern_timing_preserved":True,
        "verse2_not_literal_copy":True,
        "chorus2_not_literal_copy":True,
        "final_sustained_arrival_present":True,
        "legacy_note_generator_used":False,
        "old_generic_development_patch_used":False,
        "generic_progression_engine_used":False,
        "random_jitter_used":False,
        "new_instrument_roles_invented":False,
        "audio_generated":False,
        "finished_composition_authority":False,
        "musical_quality_proven":False,
        "listening_approval":False,
        "result":(
            "The Rock Core pilot now expands to a 40-bar symbolic composition candidate "
            "using V3-governed form, harmony, source-pattern and foreground development. "
            "Repeated cells are structurally transformed, rhythm guitar is realized as "
            "true vertical voicings, kick/snare source timing is preserved, and no generic "
            "development shortcuts are active. It is not yet performance-realized or "
            "listening-approved."
        ),
        "next_gate":"ROCK_CORE_PERFORMANCE_REALIZATION_PLAN__STILL_NO_AUDIO",
        "execution_sha256":result["execution_sha256"],
    }
    out=ROOT/"genre_contract_v3_research"/"ROCK_V3_CORE_DEVELOPED_EVENT_AUDIT.json"
    out.write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps(summary,indent=2))


if __name__=="__main__":
    main()
