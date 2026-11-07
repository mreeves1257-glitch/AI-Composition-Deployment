"""Audit Rock Core V3 Mode A performance execution."""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
FORWARD=ROOT/"current_master_forward"
if str(FORWARD) not in sys.path:
    sys.path.insert(0,str(FORWARD))

from rock_v3_core_development_executor import execute as build_symbolic
from rock_v3_core_performance_executor import execute, MODE


IDENTITY_FIELDS=(
    "track_id","role","instrument_id","source_instrument_id",
    "start_beat","midi","velocity","section","section_type",
    "source_cell","chord_symbol",
)


def main():
    source=build_symbolic()
    result=execute(MODE)

    if result.get("status")!="PASS":
        raise RuntimeError("ROCK_MODE_A_NOT_PASS")
    if result.get("mode")!=MODE:
        raise RuntimeError("ROCK_MODE_A_IDENTITY_WRONG")
    if result.get("bar_count")!=40 or result.get("event_count")!=897:
        raise RuntimeError(
            "ROCK_MODE_A_SCORE_SIZE_CHANGED::"+
            json.dumps({
                "bars":result.get("bar_count"),
                "events":result.get("event_count"),
            },sort_keys=True)
        )
    if result.get("source_execution_sha256")!=source.get("execution_sha256"):
        raise RuntimeError("ROCK_MODE_A_SOURCE_HASH_MISMATCH")

    for key in (
        "pitch_changed","onset_changed","velocity_changed","track_changed",
        "instrument_changed","event_count_changed","drums_changed","bass_changed",
        "random_jitter_used","shared_groove_numeric_offsets_applied",
        "strum_candidate_applied","bass_sustain_candidate_applied",
        "continuous_control_applied","target_articulation_switching_applied",
        "harmony_bar_boundary_crossing_allowed","audio_generated",
        "audio_authority","render_allowed","finished_composition_authority",
        "live_runtime_authority","reasoning_engine_used",
        "musical_quality_proven","listening_approval",
    ):
        if result.get(key) is not False:
            raise RuntimeError("ROCK_MODE_A_FORBIDDEN_FLAG::"+key)

    if result.get("performance_realization_applied") is not True:
        raise RuntimeError("ROCK_MODE_A_PERFORMANCE_NOT_MARKED_APPLIED")
    if result.get("performance_realization_scope")!="GUITAR_DURATION_ONLY":
        raise RuntimeError("ROCK_MODE_A_SCOPE_WRONG")

    events=result.get("events") or []
    src=source.get("events") or []
    if len(events)!=len(src):
        raise RuntimeError("ROCK_MODE_A_EVENT_COUNT_MUTATED")
    if result.get("duration_changed_event_count",0)<=0:
        raise RuntimeError("ROCK_MODE_A_NO_GUITAR_DURATION_CHANGE")
    if len(result.get("duration_change_manifest") or [])!=result["duration_changed_event_count"]:
        raise RuntimeError("ROCK_MODE_A_DURATION_MANIFEST_COUNT_MISMATCH")

    changed_indices=set()
    for i,(before,after) in enumerate(zip(src,events)):
        for field in IDENTITY_FIELDS:
            if before.get(field)!=after.get(field):
                raise RuntimeError(
                    "ROCK_MODE_A_IDENTITY_MUTATION::"+field+"::"+str(i)
                )
        before_d=float(before["duration_beats"])
        after_d=float(after["duration_beats"])
        if abs(before_d-after_d)>1e-9:
            changed_indices.add(i)
            if before.get("instrument_id")!="electric_guitar":
                raise RuntimeError(
                    "ROCK_MODE_A_NON_GUITAR_DURATION_CHANGED::"+
                    str(before.get("track_id"))
                )
        elif before.get("instrument_id")!="electric_guitar":
            # Non-guitar events must remain untouched by the performance stage.
            for forbidden in (
                "performance_execution_mode",
                "duration_realization_source",
                "pre_performance_duration_beats",
            ):
                if forbidden in after:
                    raise RuntimeError(
                        "ROCK_MODE_A_NON_GUITAR_PERFORMANCE_METADATA::"+
                        str(before.get("track_id"))
                    )

        start=float(after["start_beat"])
        end=start+after_d
        bar_end=(int(start//4)+1)*4.0
        if end>bar_end+1e-9:
            raise RuntimeError(
                "ROCK_MODE_A_CROSSED_BAR_HARMONY_BOUNDARY::"+str(i)
            )

    manifest_indices={int(x["event_index"]) for x in result["duration_change_manifest"]}
    if manifest_indices!=changed_indices:
        raise RuntimeError("ROCK_MODE_A_DURATION_MANIFEST_INDEX_SET_MISMATCH")

    # Bass and drums are exactly unchanged, including duration.
    protected={"BASS","KICK","SNARE","HAT"}
    protected_count=0
    for before,after in zip(src,events):
        if before.get("track_id") in protected:
            protected_count+=1
            if before!=after:
                raise RuntimeError(
                    "ROCK_MODE_A_PROTECTED_EVENT_CHANGED::"+
                    str(before.get("track_id"))
                )
    if protected_count<=0:
        raise RuntimeError("ROCK_MODE_A_PROTECTED_EVENT_SET_EMPTY")

    # Simultaneous rhythm-guitar chord members must still behave as one gesture:
    # same attack, same realized duration, at least three distinct pitches.
    attacks=defaultdict(list)
    for event in events:
        if event.get("track_id")=="HARMONY":
            attacks[round(float(event["start_beat"]),6)].append(event)
    if len(attacks)!=73:
        raise RuntimeError(
            "ROCK_MODE_A_HARMONY_ATTACK_COUNT_WRONG::"+str(len(attacks))
        )
    for onset,rows in attacks.items():
        if len(rows)!=3:
            raise RuntimeError(
                "ROCK_MODE_A_HARMONY_GESTURE_NOT_THREE_NOTES::"+
                str(onset)+"::"+str(len(rows))
            )
        if len({int(e["midi"]) for e in rows})!=3:
            raise RuntimeError(
                "ROCK_MODE_A_HARMONY_GESTURE_PITCH_COLLAPSE::"+str(onset)
            )
        durations={round(float(e["duration_beats"]),6) for e in rows}
        if len(durations)!=1:
            raise RuntimeError(
                "ROCK_MODE_A_VERTICAL_GESTURE_DURATION_SPLIT::"+
                str(onset)+"::"+json.dumps(sorted(durations))
            )

    # Lead phrase gaps must not be bridged across bars.
    lead=sorted(
        [e for e in events if e.get("track_id")=="LEAD"],
        key=lambda e:float(e["start_beat"]),
    )
    if len(lead)!=112:
        raise RuntimeError("ROCK_MODE_A_LEAD_EVENT_COUNT_WRONG::"+str(len(lead)))
    for a,b in zip(lead,lead[1:]):
        a_start=float(a["start_beat"])
        b_start=float(b["start_beat"])
        if int(a_start//4)!=int(b_start//4):
            if a_start+float(a["duration_beats"])> (int(a_start//4)+1)*4.0+1e-9:
                raise RuntimeError("ROCK_MODE_A_LEAD_BRIDGED_BAR_GAP")

    changed_by_track=defaultdict(int)
    for i in changed_indices:
        changed_by_track[str(events[i]["track_id"])]+=1
    if not changed_by_track.get("HARMONY") and not changed_by_track.get("LEAD"):
        raise RuntimeError("ROCK_MODE_A_NO_GUITAR_TRACK_DURATION_CHANGE")

    summary={
        "status":"PASS",
        "diagnostic_only":True,
        "genre":"ROCK",
        "profile_id":"ROCK_CORE_V2",
        "mode":MODE,
        "bar_count":40,
        "event_count":897,
        "duration_changed_event_count":len(changed_indices),
        "duration_changed_by_track":dict(changed_by_track),
        "guitar_gesture_count":result["guitar_gesture_count"],
        "rhythm_guitar_attack_count":len(attacks),
        "rhythm_guitar_pitch_count_per_attack":3,
        "vertical_gesture_duration_coherent":True,
        "lead_event_count":len(lead),
        "protected_bass_drum_event_count":protected_count,
        "protected_bass_drums_exactly_unchanged":True,
        "pitch_onset_velocity_identity_preserved":True,
        "bar_harmony_boundary_crossing_present":False,
        "random_jitter_used":False,
        "shared_microtiming_applied":False,
        "strum_candidate_applied":False,
        "bass_sustain_candidate_applied":False,
        "audio_generated":False,
        "finished_composition_authority":False,
        "musical_quality_proven":False,
        "listening_approval":False,
        "result":(
            "Rock Core Mode A now applies only project-authored electric-guitar "
            "duration behavior to the 40-bar V3 score. Vertical rhythm-guitar chords "
            "remain coherent gestures, bass/drums remain exactly unchanged, and no "
            "timing jitter, strum offset, pitch, onset or velocity mutation occurs."
        ),
        "next_gate":"ROCK_MODE_A_RESOURCE_CAPABILITY_PREFLIGHT__STILL_NO_AUDIO",
        "performance_execution_sha256":result["execution_sha256"],
    }
    out=ROOT/"genre_contract_v3_research"/"ROCK_V3_CORE_PERFORMANCE_EXECUTION_AUDIT.json"
    out.write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps(summary,indent=2))


if __name__=="__main__":
    main()
