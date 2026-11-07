"""Canonical audit for Rock Core V3 Mode A guitar-duration performance."""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
FORWARD=ROOT/"current_master_forward"
if str(FORWARD) not in sys.path:
    sys.path.insert(0,str(FORWARD))

from rock_v3_core_development_executor import execute as execute_developed
from rock_v3_core_performance_executor import execute as execute_performance, MODE


IDENTITY_FIELDS=(
    "track_id","role","instrument_id","source_instrument_id",
    "start_beat","midi","velocity","section","section_type",
    "source_cell","chord_symbol",
)


def main():
    before=execute_developed()
    after=execute_performance(MODE)

    if after.get("status")!="PASS" or after.get("mode")!=MODE:
        raise RuntimeError("ROCK_MODE_A_NOT_PASS")
    if after.get("bar_count")!=40 or after.get("event_count")!=before.get("event_count"):
        raise RuntimeError("ROCK_MODE_A_FORM_OR_EVENT_COUNT_CHANGED")
    if after.get("source_execution_sha256")!=before.get("execution_sha256"):
        raise RuntimeError("ROCK_MODE_A_SOURCE_HASH_MISMATCH")
    if after.get("performance_realization_applied") is not True:
        raise RuntimeError("ROCK_MODE_A_REALIZATION_FLAG_MISSING")
    if after.get("performance_realization_scope")!="GUITAR_DURATION_ONLY":
        raise RuntimeError("ROCK_MODE_A_SCOPE_WRONG")

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
        if after.get(key) is not False:
            raise RuntimeError("ROCK_MODE_A_FORBIDDEN_FLAG::"+key)

    source_events=before["events"]
    out_events=after["events"]
    if len(source_events)!=len(out_events):
        raise RuntimeError("ROCK_MODE_A_EVENT_ARRAY_LENGTH_CHANGED")

    changed=[]
    changed_tracks=set()
    unchanged_non_guitar=0
    for index,(src,out) in enumerate(zip(source_events,out_events)):
        for field in IDENTITY_FIELDS:
            if src.get(field)!=out.get(field):
                raise RuntimeError(
                    "ROCK_MODE_A_MUSICAL_IDENTITY_CHANGED::"+
                    field+"::"+str(index)
                )
        guitar=src["instrument_id"]=="electric_guitar"
        if not guitar:
            if src!=out:
                raise RuntimeError(
                    "ROCK_MODE_A_NON_GUITAR_EVENT_CHANGED::"+
                    str(index)+"::"+str(src.get("role"))
                )
            unchanged_non_guitar+=1

        if abs(float(src["duration_beats"])-float(out["duration_beats"]))>1e-9:
            if not guitar:
                raise RuntimeError("ROCK_MODE_A_NON_GUITAR_DURATION_CHANGED")
            changed.append((index,src,out))
            changed_tracks.add(str(src["track_id"]))

    if not changed:
        raise RuntimeError("ROCK_MODE_A_CHANGED_NO_GUITAR_DURATIONS")
    if changed_tracks!={"HARMONY","LEAD"}:
        raise RuntimeError(
            "ROCK_MODE_A_EXPECTED_BOTH_GUITAR_ROLES_TO_CHANGE::"+
            json.dumps(sorted(changed_tracks))
        )
    if after.get("duration_changed_event_count")!=len(changed):
        raise RuntimeError("ROCK_MODE_A_CHANGE_MANIFEST_COUNT_MISMATCH")
    manifest_indices={int(x["event_index"]) for x in after["duration_change_manifest"]}
    if manifest_indices!={x[0] for x in changed}:
        raise RuntimeError("ROCK_MODE_A_CHANGE_MANIFEST_INDEX_MISMATCH")

    # Every event remains inside its current harmony bar.
    for event in out_events:
        start=float(event["start_beat"])
        end=start+float(event["duration_beats"])
        bar_end=(int(start//4)+1)*4
        if end>bar_end+1e-9:
            raise RuntimeError(
                "ROCK_MODE_A_EVENT_CROSSED_BAR::"+
                str(event["track_id"])+"::"+str(start)
            )

    # Simultaneous vertical HARMONY voices remain one coherent chord gesture.
    harmony_attacks=defaultdict(list)
    for event in out_events:
        if event["track_id"]=="HARMONY":
            harmony_attacks[round(float(event["start_beat"]),6)].append(event)
    if len(harmony_attacks)!=73:
        raise RuntimeError(
            "ROCK_MODE_A_HARMONY_ATTACK_COUNT_WRONG::"+str(len(harmony_attacks))
        )
    for onset,rows in harmony_attacks.items():
        if len(rows)!=3:
            raise RuntimeError(
                "ROCK_MODE_A_HARMONY_GESTURE_NOT_THREE_NOTES::"+
                str(onset)+"::"+str(len(rows))
            )
        if len({int(e["midi"]) for e in rows})!=3:
            raise RuntimeError("ROCK_MODE_A_VERTICAL_VOICING_COLLAPSED::"+str(onset))
        ends={
            round(float(e["start_beat"])+float(e["duration_beats"]),6)
            for e in rows
        }
        if len(ends)!=1:
            raise RuntimeError(
                "ROCK_MODE_A_VERTICAL_GESTURE_DURATION_SPLIT::"+
                str(onset)+"::"+json.dumps(sorted(ends))
            )

    # Lead phrase gaps remain intentional: the last note in each active lead bar
    # is not stretched into a later bar.
    source_lead=defaultdict(list)
    out_lead=defaultdict(list)
    for src,out in zip(source_events,out_events):
        if src["track_id"]=="LEAD":
            bar=int(float(src["start_beat"])//4)
            source_lead[bar].append(src)
            out_lead[bar].append(out)
    if len([e for e in out_events if e["track_id"]=="LEAD"])!=112:
        raise RuntimeError("ROCK_MODE_A_LEAD_EVENT_COUNT_WRONG")
    for bar in source_lead:
        s=sorted(source_lead[bar],key=lambda e:e["start_beat"])[-1]
        o=sorted(out_lead[bar],key=lambda e:e["start_beat"])[-1]
        if abs(float(s["duration_beats"])-float(o["duration_beats"]))>1e-9:
            raise RuntimeError("ROCK_MODE_A_DESTROYED_LEAD_PHRASE_GAP::"+str(bar))

    # Final developed sustained arrival remains intact.
    final_src=[e for e in source_events if int(float(e["start_beat"])//4)==39]
    final_out=[e for e in out_events if int(float(e["start_beat"])//4)==39]
    for src in final_src:
        matches=[
            e for e in final_out
            if e["track_id"]==src["track_id"]
            and e["midi"]==src["midi"]
            and e["start_beat"]==src["start_beat"]
        ]
        if len(matches)!=1:
            raise RuntimeError("ROCK_MODE_A_FINAL_EVENT_IDENTITY_MISSING")
        if abs(float(matches[0]["duration_beats"])-float(src["duration_beats"]))>1e-9:
            raise RuntimeError("ROCK_MODE_A_CHANGED_FINAL_SUSTAINED_ARRIVAL")

    changed_by_track=defaultdict(int)
    for _,src,_ in changed:
        changed_by_track[str(src["track_id"])]+=1

    summary={
        "status":"PASS",
        "diagnostic_only":True,
        "genre":"ROCK",
        "profile_id":"ROCK_CORE_V2",
        "mode":MODE,
        "bar_count":40,
        "event_count":len(out_events),
        "unchanged_non_guitar_event_count":unchanged_non_guitar,
        "duration_changed_event_count":len(changed),
        "duration_changed_by_track":dict(changed_by_track),
        "guitar_gesture_count":after["guitar_gesture_count"],
        "rhythm_guitar_attack_count":len(harmony_attacks),
        "rhythm_guitar_pitch_count_per_attack":3,
        "vertical_gesture_duration_coherent":True,
        "lead_event_count":112,
        "protected_bass_drums_exactly_unchanged":True,
        "pitch_onset_velocity_identity_preserved":True,
        "lead_phrase_gap_preservation":"PASS",
        "harmony_bar_boundary_safety":"PASS",
        "final_sustained_arrival_preserved":True,
        "random_jitter_used":False,
        "strum_candidate_applied":False,
        "bass_sustain_candidate_applied":False,
        "audio_generated":False,
        "finished_composition_authority":False,
        "musical_quality_proven":False,
        "listening_approval":False,
        "result":(
            "Canonical Rock Core Mode A changes only electric-guitar durations. "
            "Vertical rhythm-guitar voicings remain coherent, lead phrase gaps and "
            "the final arrival are preserved, bass/drums are exact, and no timing, "
            "pitch, velocity, strum or sustain candidate is smuggled into the score."
        ),
        "next_gate":"ROCK_MODE_A_TARGET_CAPABILITY_AND_RESOURCE_PREFLIGHT__NO_AUDIO",
        "execution_sha256":after["execution_sha256"],
    }
    out=ROOT/"genre_contract_v3_research"/"ROCK_V3_CORE_PERFORMANCE_MODE_A_AUDIT.json"
    out.write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps(summary,indent=2))


if __name__=="__main__":
    main()
