"""Research-only melodic top-line validation for Classical-family period variants.

This harness deliberately uses one neutral 28-bar functional-harmony support for
both variants.  That keeps harmony and orchestration fixed while interval,
rhythm, contour, cadence targeting, and motivic-return behavior are tested.

The empirical source is a highest-non-grace-note-on-staff-1 proxy.  It is a
bounded upper-line reference, not a claim that every selected note is the
perceptual melody.
"""
from __future__ import annotations

from collections import Counter
import random

SCHEMA = "CLASSICAL_PERIOD_MELODY_VALIDATION_001"
BARS = 28
TOTAL_QB = 84.0
PITCH_RANGE = (60, 88)
SCALE_PCS = (0, 2, 4, 5, 7, 9, 11)

BAR_CHORDS = (
    "I","vi","ii","V","I6","IV","ii6","V",
    "vi","IV","iii","V","ii","V","I","V",
    "I","vi","ii","V","I6","IV","V7","I",
    "IV","ii6","V7","I",
)
CHORD_PCS = {
    "I":{0,4,7},"I6":{0,4,7},"ii":{2,5,9},"ii6":{2,5,9},
    "IV":{5,9,0},"V":{7,11,2},"V7":{7,11,2,5},
    "vi":{9,0,4},"iii":{4,7,11},
}

TARGET_REFERENCE = {
    "CLASSICAL_PERIOD_TOPLINE": {
        "notes_per_qb":2.185,
        "mean_abs_interval":3.103,
        "repeat_pct":9.13,
        "step_pct":52.34,
        "third_pct":18.63,
        "leap5_pct":19.90,
        "large7_pct":12.93,
        "direction_change_pct":53.34,
    },
    "ROMANTIC_TONAL_TOPLINE": {
        "notes_per_qb":1.694,
        "mean_abs_interval":3.787,
        "repeat_pct":12.90,
        "step_pct":38.39,
        "third_pct":18.54,
        "leap5_pct":30.17,
        "large7_pct":19.43,
        "direction_change_pct":58.14,
    },
}

RHYTHM_PATTERNS = {
    "CLASSICAL_PERIOD_TOPLINE": (
        (0,.5,1,1.5,2,2.5),
        (0,.25,.5,1,1.5,2,2.5),
        (0,.25,.5,.75,1,1.5,2,2.5),
    ),
    "ROMANTIC_TONAL_TOPLINE": (
        (0,.75,1.5,2.25),
        (0,.5,1,1.75,2.5),
        (0,.5,1,1.5,2,2.5),
    ),
}
RHYTHM_WEIGHTS = {
    "CLASSICAL_PERIOD_TOPLINE": (0.48,0.42,0.10),
    "ROMANTIC_TONAL_TOPLINE": (0.22,0.53,0.25),
}
INTERVAL_WEIGHTS = {
    "CLASSICAL_PERIOD_TOPLINE": {
        "repeat":9, "step":52, "third":19, "medium":7, "large":13,
    },
    "ROMANTIC_TONAL_TOPLINE": {
        "repeat":13, "step":38, "third":19, "medium":11, "large":19,
    },
}
BUCKET = {
    "repeat":{0},
    "step":{1,2},
    "third":{3,4},
    "medium":{5,6},
    "large":set(range(7,13)),
}
DIRECTION_REVERSAL_BASE = {
    "CLASSICAL_PERIOD_TOPLINE":0.40,
    "ROMANTIC_TONAL_TOPLINE":0.45,
}
LARGE_LEAP_RECOVERY = {
    "CLASSICAL_PERIOD_TOPLINE":0.90,
    "ROMANTIC_TONAL_TOPLINE":0.80,
}

def _weighted_choice(rng, mapping):
    total=sum(mapping.values())
    pick=rng.random()*total
    for key,value in mapping.items():
        pick-=value
        if pick<=0:
            return key
    return next(reversed(mapping))

def _pattern_choice(rng, variant, bar):
    patterns=RHYTHM_PATTERNS[variant]
    weights=RHYTHM_WEIGHTS[variant]
    pick=rng.random()
    running=0.0
    choice=patterns[-1]
    for pattern,weight in zip(patterns,weights):
        running+=weight
        if pick<=running:
            choice=pattern
            break
    # Cadential bars breathe slightly; never force the densest pattern there.
    if bar in (8,16,24,28) and len(choice)>6:
        choice=patterns[0] if variant=="CLASSICAL_PERIOD_TOPLINE" else patterns[1]
    return choice

def _bucket_of(interval):
    absolute=abs(interval)
    for name,values in BUCKET.items():
        if absolute in values:
            return name
    return "large"

def _candidate_notes(pcs):
    return [
        midi for midi in range(PITCH_RANGE[0],PITCH_RANGE[1]+1)
        if midi%12 in pcs
    ]

def _choose_from_bucket(rng, current, pcs, bucket, direction):
    candidates=_candidate_notes(pcs)
    exact=[
        note for note in candidates
        if abs(note-current) in BUCKET[bucket]
        and (direction==0 or (note-current)*direction>0)
    ]
    if exact:
        desired=0 if bucket=="repeat" else rng.choice(tuple(BUCKET[bucket]))
        return min(exact,key=lambda n:(abs(abs(n-current)-desired),abs(n-current),n))

    directional=[
        note for note in candidates
        if direction==0 or (note-current)*direction>0
    ]
    pool=directional or candidates
    center=0 if bucket=="repeat" else (
        2 if bucket=="step" else
        4 if bucket=="third" else
        5 if bucket=="medium" else 8
    )
    return min(pool,key=lambda n:(abs(abs(n-current)-center),abs(n-current),n))

def build_melody(variant, seed=0):
    if variant not in TARGET_REFERENCE:
        raise ValueError("UNKNOWN_MELODY_VARIANT")

    rng=random.Random(seed*10007 + (3 if variant=="CLASSICAL_PERIOD_TOPLINE" else 71))
    motif_rng=random.Random(seed*53 + 17 + (0 if variant=="CLASSICAL_PERIOD_TOPLINE" else 1000))

    # Categorical motif identity is stated in bar 1 and recalled in bar 17.
    motif=[]
    motif_direction=1
    for _ in range(7):
        category=_weighted_choice(motif_rng,INTERVAL_WEIGHTS[variant])
        if category!="repeat" and motif_rng.random()<DIRECTION_REVERSAL_BASE[variant]:
            motif_direction*=-1
        motif.append((category,motif_direction if category!="repeat" else 0))

    current=72 if variant=="CLASSICAL_PERIOD_TOPLINE" else 69
    last_direction=1
    previous_interval_abs=0
    events=[]

    for bar in range(1,BARS+1):
        onsets=_pattern_choice(rng,variant,bar)
        chord=CHORD_PCS[BAR_CHORDS[bar-1]]

        for onset_index,offset in enumerate(onsets):
            last_in_bar=onset_index==len(onsets)-1
            cadence=bar in (8,16,24,28) and last_in_bar
            motif_position=(onset_index-1) if bar in (1,17) and onset_index>0 else None

            if motif_position is not None and motif_position<len(motif):
                category,direction=motif[motif_position]
            else:
                category=_weighted_choice(rng,INTERVAL_WEIGHTS[variant])
                if category=="repeat":
                    direction=0
                elif previous_interval_abs>=5 and rng.random()<LARGE_LEAP_RECOVERY[variant]:
                    direction=-last_direction
                elif rng.random()<DIRECTION_REVERSAL_BASE[variant]:
                    direction=-last_direction
                else:
                    direction=last_direction

            if cadence:
                target_pc=7 if bar in (8,16) else 0
                cadence_candidates=_candidate_notes({target_pc})
                next_note=min(cadence_candidates,key=lambda n:(abs(n-current),n))
            elif onset_index==0:
                # Bar downbeat is harmonically anchored.
                next_note=_choose_from_bucket(rng,current,chord,category,direction)
            else:
                # Weak/inner positions may use any diatonic scale tone.
                next_note=_choose_from_bucket(rng,current,set(SCALE_PCS),category,direction)

            interval=next_note-current
            actual_direction=0 if interval==0 else (1 if interval>0 else -1)
            next_offset=onsets[onset_index+1] if onset_index+1<len(onsets) else 3.0
            inter_onset=next_offset-offset
            articulation=0.82 if variant=="CLASSICAL_PERIOD_TOPLINE" else 0.90
            duration=max(0.12,inter_onset*articulation)

            events.append({
                "bar":bar,
                "offset_qb":offset,
                "midi":next_note,
                "duration_qb":round(duration,4),
                "chord":BAR_CHORDS[bar-1],
                "bar_downbeat":onset_index==0,
                "cadence":cadence,
                "interval":interval,
                "desired_interval_bucket":category,
                "actual_interval_bucket":_bucket_of(interval),
                "motif_return":bar==17 and motif_position is not None and motif_position<len(motif),
            })

            if actual_direction:
                last_direction=actual_direction
            previous_interval_abs=abs(interval)
            current=next_note

    return {
        "schema":SCHEMA,
        "variant":variant,
        "seed":seed,
        "bars":BARS,
        "meter":"3/4",
        "neutral_harmony":list(BAR_CHORDS),
        "motif_template":[{"bucket":b,"direction":d} for b,d in motif],
        "events":events,
    }

def summarize(plan):
    events=plan["events"]
    intervals=[abs(e["interval"]) for e in events[1:]]
    directions=[
        1 if e["interval"]>0 else -1
        for e in events[1:] if e["interval"]!=0
    ]
    direction_changes=sum(
        directions[i]!=directions[i-1]
        for i in range(1,len(directions))
    )

    leap_indices=[
        i for i,e in enumerate(events[:-1])
        if abs(e["interval"])>=5 and e["interval"]!=0
    ]
    recovered=0
    for index in leap_indices:
        direction=1 if events[index]["interval"]>0 else -1
        next_index=index+1
        while next_index<len(events) and events[next_index]["interval"]==0:
            next_index+=1
        if next_index<len(events):
            next_direction=1 if events[next_index]["interval"]>0 else -1
            if next_direction==-direction:
                recovered+=1

    downbeats=[e for e in events if e["bar_downbeat"]]
    cadences=[e for e in events if e["cadence"]]
    motif_return=[e for e in events if e["motif_return"]]

    return {
        "variant":plan["variant"],
        "seed":plan["seed"],
        "note_count":len(events),
        "notes_per_qb":round(len(events)/TOTAL_QB,3),
        "mean_abs_interval":round(sum(intervals)/len(intervals),3),
        "repeat_pct":round(100*sum(x==0 for x in intervals)/len(intervals),2),
        "step_pct":round(100*sum(1<=x<=2 for x in intervals)/len(intervals),2),
        "third_pct":round(100*sum(3<=x<=4 for x in intervals)/len(intervals),2),
        "leap5_pct":round(100*sum(x>=5 for x in intervals)/len(intervals),2),
        "large7_pct":round(100*sum(x>=7 for x in intervals)/len(intervals),2),
        "direction_change_pct":round(100*direction_changes/max(1,len(directions)-1),2),
        "mean_note_duration_qb":round(sum(e["duration_qb"] for e in events)/len(events),3),
        "large_leap_recovery_pct":round(100*recovered/max(1,len(leap_indices)),2),
        "bar_downbeat_chord_tone_pct":round(
            100*sum(e["midi"]%12 in CHORD_PCS[e["chord"]] for e in downbeats)/len(downbeats),2
        ),
        "cadence_target_pct":round(
            100*sum(
                e["midi"]%12==(7 if e["bar"] in (8,16) else 0)
                for e in cadences
            )/len(cadences),2
        ),
        "motif_return_bucket_match_pct":round(
            100*sum(e["desired_interval_bucket"]==e["actual_interval_bucket"] for e in motif_return)
            /max(1,len(motif_return)),2
        ),
        "max_interval_semitones":max(intervals),
        "pitch_min":min(e["midi"] for e in events),
        "pitch_max":max(e["midi"] for e in events),
    }

def aggregate_validation(seeds=32):
    result={
        "schema":SCHEMA,
        "status":"PASS",
        "research_only":True,
        "live_runtime_modified":False,
        "neutral_harmony_shared":True,
        "variants":{},
    }
    for variant in TARGET_REFERENCE:
        summaries=[summarize(build_melody(variant,seed)) for seed in range(seeds)]
        metrics=(
            "note_count","notes_per_qb","mean_abs_interval","repeat_pct",
            "step_pct","third_pct","leap5_pct","large7_pct",
            "direction_change_pct","mean_note_duration_qb",
            "large_leap_recovery_pct","bar_downbeat_chord_tone_pct",
            "cadence_target_pct","motif_return_bucket_match_pct",
            "max_interval_semitones",
        )
        means={
            key:round(sum(s[key] for s in summaries)/len(summaries),3)
            for key in metrics
        }
        result["variants"][variant]={
            "seed_count":seeds,
            "means":means,
            "worst_case":{
                "max_interval_semitones":max(s["max_interval_semitones"] for s in summaries),
                "minimum_large_leap_recovery_pct":min(s["large_leap_recovery_pct"] for s in summaries),
                "minimum_cadence_target_pct":min(s["cadence_target_pct"] for s in summaries),
                "minimum_bar_downbeat_chord_tone_pct":min(s["bar_downbeat_chord_tone_pct"] for s in summaries),
            },
            "example_seed_0":summaries[0],
        }

    c=result["variants"]["CLASSICAL_PERIOD_TOPLINE"]["means"]
    r=result["variants"]["ROMANTIC_TONAL_TOPLINE"]["means"]

    assert 2.0<=c["notes_per_qb"]<=2.35
    assert 2.5<=c["mean_abs_interval"]<=3.6
    assert 6<=c["repeat_pct"]<=15
    assert 43<=c["step_pct"]<=60
    assert 13<=c["third_pct"]<=27
    assert 14<=c["leap5_pct"]<=27
    assert 7<=c["large7_pct"]<=19
    assert 45<=c["direction_change_pct"]<=62

    assert 1.5<=r["notes_per_qb"]<=1.85
    assert 2.9<=r["mean_abs_interval"]<=4.4
    assert 7<=r["repeat_pct"]<=19
    assert 28<=r["step_pct"]<=48
    assert 13<=r["third_pct"]<=27
    assert 22<=r["leap5_pct"]<=38
    assert 11<=r["large7_pct"]<=25
    assert 50<=r["direction_change_pct"]<=69

    for variant,data in result["variants"].items():
        assert data["means"]["bar_downbeat_chord_tone_pct"]==100
        assert data["means"]["cadence_target_pct"]==100
        assert data["means"]["motif_return_bucket_match_pct"]>=70
        assert data["means"]["large_leap_recovery_pct"]>=78
        assert data["worst_case"]["max_interval_semitones"]<=12

    assert r["notes_per_qb"]<c["notes_per_qb"]-0.3
    assert r["mean_abs_interval"]>c["mean_abs_interval"]+0.25
    assert r["step_pct"]<c["step_pct"]-7
    assert r["leap5_pct"]>c["leap5_pct"]+5
    assert r["mean_note_duration_qb"]>c["mean_note_duration_qb"]+0.10

    return result

def main():
    import json
    print(json.dumps(aggregate_validation(),indent=2,sort_keys=True))

if __name__=="__main__":
    main()
