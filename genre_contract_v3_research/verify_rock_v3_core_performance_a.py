"""Audit Rock Core V3 performance candidate A."""
from __future__ import annotations

from pathlib import Path
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
FORWARD=ROOT/"current_master_forward"
if str(FORWARD) not in sys.path:
    sys.path.insert(0,str(FORWARD))

from rock_v3_core_development_executor import execute as build_source
from rock_v3_core_performance_a import execute as perform_a


def immutable_signature(event):
    return (
        event.get("track_id"),
        event.get("role"),
        event.get("instrument_id"),
        round(float(event.get("start_beat",0)),6),
        int(event.get("midi",0)),
        int(event.get("velocity",0)),
        event.get("section"),
        event.get("source_cell"),
        event.get("chord_symbol"),
    )


def main():
    source=build_source()
    result=perform_a()
    if result.get("status")!="PASS":
        raise RuntimeError("ROCK_PERFORMANCE_A_NOT_PASS")
    if result.get("performance_mode")!="A_GUITAR_DURATION_ONLY":
        raise RuntimeError("ROCK_PERFORMANCE_A_MODE_CHANGED")
    if result.get("event_count")!=source.get("event_count"):
        raise RuntimeError("ROCK_PERFORMANCE_A_EVENT_COUNT_CHANGED")

    for key in (
        "onsets_changed","pitches_changed","velocities_changed","event_count_changed",
        "instrument_ids_changed","drum_events_changed","bass_events_changed",
        "rhythm_guitar_strum_applied","bass_sustain_candidate_applied",
        "random_jitter_used","audio_generated","audio_authority",
        "finished_composition_authority","live_runtime_authority",
        "reasoning_engine_used","musical_quality_proven","listening_approval",
        "render_allowed",
    ):
        if result.get(key) is not False:
            raise RuntimeError("ROCK_PERFORMANCE_A_FORBIDDEN_FLAG::"+key)
    if result.get("harmony_boundary_cap_applied") is not True:
        raise RuntimeError("ROCK_PERFORMANCE_A_HARMONY_CAP_NOT_APPLIED")

    before=source["events"]
    after=result["events"]
    if len(before)!=len(after):
        raise RuntimeError("ROCK_PERFORMANCE_A_LENGTH_MISMATCH")
    if [immutable_signature(x) for x in before] != [immutable_signature(x) for x in after]:
        raise RuntimeError("ROCK_PERFORMANCE_A_CHANGED_NON_DURATION_EVENT_DATA")

    changed=[]
    changed_tracks=set()
    non_guitar_changed=[]
    for a,b in zip(before,after):
        da=round(float(a["duration_beats"]),6)
        db=round(float(b["duration_beats"]),6)
        if da==db:
            continue
        changed.append((a,b))
        changed_tracks.add(str(a["track_id"]).upper())
        if str(a["instrument_id"]).lower()!="electric_guitar":
            non_guitar_changed.append({
                "track":a["track_id"],"start":a["start_beat"],
                "instrument":a["instrument_id"],"before":da,"after":db,
            })
    if non_guitar_changed:
        raise RuntimeError(
            "ROCK_PERFORMANCE_A_CHANGED_NON_GUITAR_DURATION::"+
            json.dumps(non_guitar_changed[:10])
        )
    if not changed:
        raise RuntimeError("ROCK_PERFORMANCE_A_CHANGED_NOTHING")
    if not {"HARMONY","LEAD"}.issubset(changed_tracks):
        raise RuntimeError(
            "ROCK_PERFORMANCE_A_DID_NOT_TOUCH_BOTH_GUITAR_ROLES::"+
            json.dumps(sorted(changed_tracks))
        )
    if len(changed)!=result.get("changed_duration_count"):
        raise RuntimeError("ROCK_PERFORMANCE_A_CHANGED_COUNT_MISMATCH")

    # Preserve every non-guitar event exactly, including duration.
    source_non_guitar=[x for x in before if x["instrument_id"]!="electric_guitar"]
    output_non_guitar=[x for x in after if x["instrument_id"]!="electric_guitar"]
    if source_non_guitar!=output_non_guitar:
        raise RuntimeError("ROCK_PERFORMANCE_A_NON_GUITAR_EVENT_CHANGED")

    # No guitar note may now cross the next bar boundary/harmony change.
    for e in after:
        if e["instrument_id"]!="electric_guitar":
            continue
        start=float(e["start_beat"])
        end=start+float(e["duration_beats"])
        bar_end=(int(start//4)+1)*4
        if end>bar_end+1e-9:
            raise RuntimeError(
                "ROCK_PERFORMANCE_A_GUITAR_CROSSES_HARMONY_BOUNDARY::"+
                json.dumps({
                    "track":e["track_id"],"start":start,
                    "duration":e["duration_beats"],"bar_end":bar_end,
                })
            )

    # Lead durations may connect phrases, but cannot overlap the next lead attack.
    lead=sorted(
        [x for x in after if x["track_id"]=="LEAD"],
        key=lambda x:(float(x["start_beat"]),int(x["midi"]))
    )
    for a,b in zip(lead,lead[1:]):
        if float(a["start_beat"])+float(a["duration_beats"])>float(b["start_beat"])+1e-9:
            raise RuntimeError("ROCK_PERFORMANCE_A_LEAD_OVERLAP")

    # Rhythm-guitar vertical voicings remain vertical in Mode A: no strum onset
    # staggering has been introduced yet.
    harmony=[x for x in after if x["track_id"]=="HARMONY"]
    by_onset={}
    for e in harmony:
        by_onset.setdefault(round(float(e["start_beat"]),6),[]).append(e)
    chord_groups=[g for g in by_onset.values() if len(g)>=2]
    if not chord_groups:
        raise RuntimeError("ROCK_PERFORMANCE_A_NO_VERTICAL_GUITAR_CHORDS")
    if any(len({round(float(x["start_beat"]),6) for x in group})!=1 for group in chord_groups):
        raise RuntimeError("ROCK_PERFORMANCE_A_STRUM_TIMING_SNEAKED_IN")

    harmonic_changes=sum(1 for a,b in zip(
        [x["duration_beats"] for x in before if x["track_id"]=="HARMONY"],
        [x["duration_beats"] for x in after if x["track_id"]=="HARMONY"],
    ) if round(float(a),6)!=round(float(b),6))
    lead_changes=sum(1 for a,b in zip(
        [x["duration_beats"] for x in before if x["track_id"]=="LEAD"],
        [x["duration_beats"] for x in after if x["track_id"]=="LEAD"],
    ) if round(float(a),6)!=round(float(b),6))

    summary={
        "status":"PASS",
        "diagnostic_only":True,
        "genre":"ROCK",
        "profile_id":"ROCK_CORE_V2",
        "performance_mode":"A_GUITAR_DURATION_ONLY",
        "event_count":len(after),
        "changed_guitar_duration_count":len(changed),
        "changed_rhythm_guitar_duration_count":harmonic_changes,
        "changed_lead_guitar_duration_count":lead_changes,
        "non_guitar_events_identical":True,
        "onsets_identical":True,
        "pitches_identical":True,
        "velocities_identical":True,
        "instrument_ids_identical":True,
        "rhythm_guitar_strum_applied":False,
        "bass_sustain_applied":False,
        "random_jitter_used":False,
        "harmony_boundary_crossings":0,
        "lead_overlap_count":0,
        "audio_generated":False,
        "finished_composition_authority":False,
        "listening_approval":False,
        "result":(
            "Rock Core performance candidate A changes only electric-guitar note "
            "durations. Bass/drums and all note identities/onsets/velocities remain "
            "identical, and the V3 harmony boundary cap prevents new cross-chord sustain."
        ),
        "next_gate":"OPTIONAL_MODE_B_STRUM_CANDIDATE_SYMBOLIC_A_B__STILL_NO_AUDIO",
        "performance_execution_sha256":result["performance_execution_sha256"],
    }
    out=ROOT/"genre_contract_v3_research"/"ROCK_V3_CORE_PERFORMANCE_A_AUDIT.json"
    out.write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps(summary,indent=2))


if __name__=="__main__":
    main()
