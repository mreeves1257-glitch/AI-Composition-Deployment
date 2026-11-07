"""Audit Rock Core Mode A duration changes without rendering audio.

This gate does not alter the composition. It measures the already-authored
A_GUITAR_DURATION_ONLY transformation and verifies that duration changes remain
musically bounded:
- guitar only;
- no pitch/onset/velocity/identity mutation;
- no new overlap into the next same-track gesture;
- no cross-bar/harmony-boundary sustain;
- cross-bar lead phrase gaps remain untouched;
- vertical rhythm-guitar chord members remain duration-coherent.

Output is diagnostic evidence only. It does not approve musical quality or
promote anything into the live Composer.
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import json
import math
import statistics
import sys

ROOT=Path(__file__).resolve().parents[1]
FORWARD=ROOT/"current_master_forward"
if str(FORWARD) not in sys.path:
    sys.path.insert(0,str(FORWARD))

from rock_v3_core_development_executor import execute as execute_before
from rock_v3_core_performance_executor import execute as execute_after, MODE

SCHEMA="ROCK_MODE_A_DURATION_SHAPE_AUDIT_001"
TRACKS=("HARMONY","LEAD")


class RockModeADurationShapeAuditError(RuntimeError):
    pass


def _bar_end(start:float)->float:
    return (int(start//4)+1)*4.0


def _gesture_rows(events:list[dict])->dict[str,list[dict]]:
    grouped:dict[str,dict[float,list[dict]]]=defaultdict(lambda:defaultdict(list))
    for event in events:
        track=str(event.get("track_id","")).upper()
        if track not in TRACKS:
            continue
        grouped[track][float(event["start_beat"])].append(event)

    result={}
    for track,by_start in grouped.items():
        rows=[]
        for start,members in sorted(by_start.items()):
            durations=[float(x["duration_beats"]) for x in members]
            rows.append({
                "track_id":track,
                "start_beat":start,
                "bar":int(start//4),
                "section":members[0].get("section"),
                "section_type":members[0].get("section_type"),
                "chord_symbol":members[0].get("chord_symbol"),
                "member_count":len(members),
                "durations":durations,
                "duration_min":min(durations),
                "duration_max":max(durations),
                "duration_spread":max(durations)-min(durations),
            })
        result[track]=rows
    return result


def main()->None:
    before=execute_before()
    after=execute_after(MODE)
    if before.get("status")!="PASS" or after.get("status")!="PASS":
        raise RockModeADurationShapeAuditError("ROCK_MODE_A_SOURCE_NOT_PASS")
    if before["event_count"]!=after["event_count"]:
        raise RockModeADurationShapeAuditError("EVENT_COUNT_CHANGED")

    identity_fields=(
        "track_id","role","instrument_id","source_instrument_id",
        "start_beat","midi","velocity","section","section_type",
        "source_cell","chord_symbol",
    )

    changes=[]
    by_track=defaultdict(list)
    by_section=defaultdict(list)
    extended=0
    shortened=0
    unchanged=0

    for index,(a,b) in enumerate(zip(before["events"],after["events"])):
        for field in identity_fields:
            if a.get(field)!=b.get(field):
                raise RockModeADurationShapeAuditError("IDENTITY_CHANGED::"+field)

        da=float(a["duration_beats"])
        db=float(b["duration_beats"])
        delta=db-da
        if abs(delta)<=1e-9:
            unchanged+=1
            continue

        track=str(a.get("track_id","")).upper()
        if track not in TRACKS or a.get("instrument_id")!="electric_guitar":
            raise RockModeADurationShapeAuditError("NON_GUITAR_DURATION_CHANGED")

        row={
            "event_index":index,
            "track_id":track,
            "section":a.get("section"),
            "section_type":a.get("section_type"),
            "bar":int(float(a["start_beat"])//4),
            "start_beat":float(a["start_beat"]),
            "midi":int(a["midi"]),
            "before":da,
            "after":db,
            "delta":delta,
        }
        changes.append(row)
        by_track[track].append(delta)
        by_section[str(a.get("section"))].append(delta)
        if delta>0:
            extended+=1
        else:
            shortened+=1

    if len(changes)!=int(after.get("duration_changed_event_count", -1)):
        raise RockModeADurationShapeAuditError("CHANGE_COUNT_DISAGREES_WITH_EXECUTOR")
    if not changes:
        raise RockModeADurationShapeAuditError("NO_DURATION_CHANGES")

    before_g=_gesture_rows(before["events"])
    after_g=_gesture_rows(after["events"])

    overlap_violations=[]
    cross_bar_violations=[]
    harmony_spread_violations=[]
    lead_cross_bar_gap_mutations=[]
    post_mode_gaps=[]

    for track in TRACKS:
        bg=before_g[track]
        ag=after_g[track]
        if len(bg)!=len(ag):
            raise RockModeADurationShapeAuditError("GESTURE_COUNT_CHANGED::"+track)

        for i,(a,b) in enumerate(zip(bg,ag)):
            if a["start_beat"]!=b["start_beat"] or a["member_count"]!=b["member_count"]:
                raise RockModeADurationShapeAuditError("GESTURE_IDENTITY_CHANGED::"+track)

            end=b["start_beat"]+b["duration_max"]
            if end>_bar_end(b["start_beat"])+1e-9:
                cross_bar_violations.append({
                    "track_id":track,
                    "start_beat":b["start_beat"],
                    "end_beat":end,
                    "bar_end":_bar_end(b["start_beat"]),
                })

            if track=="HARMONY" and b["member_count"]>1 and b["duration_spread"]>1e-9:
                harmony_spread_violations.append({
                    "start_beat":b["start_beat"],
                    "duration_spread":b["duration_spread"],
                    "durations":b["durations"],
                })

            if i+1<len(ag):
                next_start=ag[i+1]["start_beat"]
                gap=next_start-end
                post_mode_gaps.append({
                    "track_id":track,
                    "from_start":b["start_beat"],
                    "to_start":next_start,
                    "gap_beats":gap,
                    "cross_bar":int(b["start_beat"]//4)!=int(next_start//4),
                })
                if gap<-1e-9:
                    overlap_violations.append({
                        "track_id":track,
                        "from_start":b["start_beat"],
                        "to_start":next_start,
                        "overlap_beats":-gap,
                    })

                if track=="LEAD" and int(a["start_beat"]//4)!=int(bg[i+1]["start_beat"]//4):
                    before_gap=bg[i+1]["start_beat"]-(a["start_beat"]+a["duration_max"])
                    after_gap=next_start-end
                    if abs(before_gap-after_gap)>1e-9:
                        lead_cross_bar_gap_mutations.append({
                            "from_start":a["start_beat"],
                            "to_start":bg[i+1]["start_beat"],
                            "before_gap":before_gap,
                            "after_gap":after_gap,
                        })

    if overlap_violations:
        raise RockModeADurationShapeAuditError(
            "MODE_A_CREATED_SAME_TRACK_OVERLAP::"+json.dumps(overlap_violations[:10],sort_keys=True)
        )
    if cross_bar_violations:
        raise RockModeADurationShapeAuditError(
            "MODE_A_CROSSED_BAR_BOUNDARY::"+json.dumps(cross_bar_violations[:10],sort_keys=True)
        )
    if harmony_spread_violations:
        raise RockModeADurationShapeAuditError(
            "RHYTHM_GUITAR_CHORD_DURATION_SPLIT::"+json.dumps(harmony_spread_violations[:10],sort_keys=True)
        )
    if lead_cross_bar_gap_mutations:
        raise RockModeADurationShapeAuditError(
            "LEAD_CROSS_BAR_PHRASE_GAP_CHANGED::"+json.dumps(lead_cross_bar_gap_mutations[:10],sort_keys=True)
        )

    deltas=[x["delta"] for x in changes]
    positive_gaps=[x["gap_beats"] for x in post_mode_gaps if x["gap_beats"]>=0]
    min_gap=min(positive_gaps) if positive_gaps else None

    def stat(values:list[float])->dict:
        return {
            "count":len(values),
            "min":min(values),
            "max":max(values),
            "mean":statistics.fmean(values),
            "median":statistics.median(values),
        }

    section_stats={
        key:stat(values)
        for key,values in sorted(by_section.items())
    }
    track_stats={
        key:stat(values)
        for key,values in sorted(by_track.items())
    }

    report={
        "schema":SCHEMA,
        "status":"PASS",
        "diagnostic_only":True,
        "genre":"ROCK",
        "profile_id":"ROCK_CORE_V2",
        "performance_mode":MODE,
        "bar_count":before["bar_count"],
        "tempo_bpm":before["tempo_bpm"],
        "total_event_count":before["event_count"],
        "duration_changed_event_count":len(changes),
        "duration_unchanged_event_count":unchanged,
        "extended_event_count":extended,
        "shortened_event_count":shortened,
        "duration_delta_stats_beats":stat(deltas),
        "by_track":track_stats,
        "by_section":section_stats,
        "minimum_same_track_post_mode_gap_beats":min_gap,
        "same_track_overlap_violation_count":0,
        "cross_bar_duration_violation_count":0,
        "rhythm_guitar_vertical_duration_split_count":0,
        "lead_cross_bar_phrase_gap_mutation_count":0,
        "identity_mutation_count":0,
        "pitch_changed":False,
        "onset_changed":False,
        "velocity_changed":False,
        "instrument_changed":False,
        "bass_changed":False,
        "drums_changed":False,
        "reasoning_engine_used":False,
        "production_fidelity_certified":False,
        "listening_approval":False,
        "live_runtime_promoted":False,
        "change_manifest":changes,
        "result":"Mode A duration-only guitar realization is structurally bounded and does not create same-track overlaps, cross-bar sustain, split rhythm-guitar chord durations, or altered cross-bar lead phrase gaps.",
        "next_gate":"HUMAN_A_B_LISTENING_REVIEW__NO_NEW_PERFORMANCE_VARIABLE_YET",
    }

    out=ROOT/"genre_contract_v3_research"/"ROCK_MODE_A_DURATION_SHAPE_AUDIT.json"
    out.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({k:v for k,v in report.items() if k!="change_manifest"},indent=2))


if __name__=="__main__":
    main()
