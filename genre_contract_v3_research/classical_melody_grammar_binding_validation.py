"""Research-only binding of period melody behavior to period harmony.

This gate combines the already isolated melody and grammar candidates while
orchestration remains disabled.  Melody is generated with awareness of the
currently active harmony rather than generated first and snapped onto chords
afterward.

Non-chord tones are permitted only as controlled diatonic/chromatic motion.
Resolution may cross a harmony boundary when the next melodic event resolves by
step to a chord tone, allowing suspension/anticipation behavior.
"""
from __future__ import annotations

import random

from genre_contract_v3_research import classical_grammar_validation as grammar
from genre_contract_v3_research import classical_melody_validation as melody
from genre_contract_v3_research import classical_voice_leading_validation as voice

SCHEMA="CLASSICAL_MELODY_GRAMMAR_BINDING_001"
PITCH_RANGE=(60,88)
CLASSICAL_SCALE=(0,2,4,5,7,9,11)
ROMANTIC_SCALE=(0,2,3,5,7,8,10,11)

PAIRINGS={
    "CLASSICAL_PERIOD_TOPLINE":"CLASSICAL_PERIOD_TONAL",
    "ROMANTIC_TONAL_TOPLINE":"ROMANTIC_TONAL_EXPANDED",
}

def _active_harmony(plan,bar,offset):
    events=[e for e in plan["events"] if e["bar"]==bar]
    for index,event in enumerate(events):
        if event["offset_qb"]-1e-9<=offset<event["offset_qb"]+event["duration_qb"]-1e-9:
            return index,event
    return len(events)-1,events[-1]

def _bucket(interval):
    absolute=abs(interval)
    for name,values in melody.BUCKET.items():
        if absolute in values:
            return name
    return "large"

def _pitch_pool(pcs):
    return [
        midi for midi in range(PITCH_RANGE[0],PITCH_RANGE[1]+1)
        if midi%12 in pcs
    ]

def _choose_pitch(rng,previous,pcs,category,direction):
    candidates=_pitch_pool(pcs)
    if not candidates:
        raise RuntimeError("EMPTY_MELODY_PITCH_POOL")
    center={
        "repeat":0,
        "step":2,
        "third":4,
        "medium":5,
        "large":8,
    }[category]
    best=None
    for note in candidates:
        interval=note-previous
        absolute=abs(interval)
        actual_direction=0 if interval==0 else (1 if interval>0 else -1)
        cost=abs(absolute-center)*0.25
        if _bucket(interval)!=category:
            cost+=4.0
        if direction and actual_direction!=direction:
            cost+=2.5
        if note==previous and category!="repeat":
            cost+=5.0
        if absolute>12:
            cost+=100.0
        if best is None or cost<best[0]:
            best=(cost,note)
    return best[1]

def _onset_plan(melody_variant,grammar_plan,seed):
    rng=random.Random(
        seed*10007 + (3 if melody_variant=="CLASSICAL_PERIOD_TOPLINE" else 71)
    )
    result=[]
    for bar in range(1,29):
        onsets=melody._pattern_choice(rng,melody_variant,bar)
        for onset_index,offset in enumerate(onsets):
            harmony_index,harmony=_active_harmony(grammar_plan,bar,offset)
            local_root=voice.LOCAL_ROOT_PC.get(harmony["localkey"],0)
            spec=voice.chord_spec(
                harmony["numeral"],local_root,grammar_plan["variant"]
            )
            chord_pcs=set(spec[0])
            scale_intervals=(
                CLASSICAL_SCALE
                if melody_variant=="CLASSICAL_PERIOD_TOPLINE"
                else ROMANTIC_SCALE
            )
            scale_pcs={(local_root+x)%12 for x in scale_intervals}
            result.append({
                "bar":bar,
                "offset_qb":offset,
                "onset_index":onset_index,
                "last_in_bar":onset_index==len(onsets)-1,
                "harmony_id":(bar,harmony_index),
                "harmony":harmony,
                "local_root_pc":local_root,
                "chord_pcs":chord_pcs,
                "scale_pcs":scale_pcs,
            })
    return result

def build_bound_melody(melody_variant,seed=0):
    if melody_variant not in PAIRINGS:
        raise ValueError("UNKNOWN_BOUND_MELODY_VARIANT")
    grammar_variant=PAIRINGS[melody_variant]
    grammar_plan=grammar.build_plan(grammar_variant,seed)
    onsets=_onset_plan(melody_variant,grammar_plan,seed)

    motif_rng=random.Random(
        seed*53+17+(0 if melody_variant=="CLASSICAL_PERIOD_TOPLINE" else 1000)
    )
    motif=[]
    motif_direction=1
    for _ in range(7):
        category=melody._weighted_choice(
            motif_rng,melody.INTERVAL_WEIGHTS[melody_variant]
        )
        if (
            category!="repeat"
            and motif_rng.random()<melody.DIRECTION_REVERSAL_BASE[melody_variant]
        ):
            motif_direction*=-1
        motif.append((category,motif_direction if category!="repeat" else 0))

    rng=random.Random(
        seed*20011+(11 if melody_variant=="CLASSICAL_PERIOD_TOPLINE" else 97)
    )
    previous=72 if melody_variant=="CLASSICAL_PERIOD_TOPLINE" else 69
    last_direction=1
    previous_interval_abs=0
    pending_resolution=None
    output=[]

    for index,onset in enumerate(onsets):
        motif_position=(
            onset["onset_index"]-1
            if onset["bar"] in (1,17) and onset["onset_index"]>0
            else None
        )
        if motif_position is not None and motif_position<len(motif):
            category,direction=motif[motif_position]
        else:
            category=melody._weighted_choice(
                rng,melody.INTERVAL_WEIGHTS[melody_variant]
            )
            if category=="repeat":
                direction=0
            elif (
                previous_interval_abs>=5
                and rng.random()<melody.LARGE_LEAP_RECOVERY[melody_variant]
            ):
                direction=-last_direction
            elif rng.random()<melody.DIRECTION_REVERSAL_BASE[melody_variant]:
                direction=-last_direction
            else:
                direction=last_direction

        structural=(
            index==0
            or onset["harmony_id"]!=onsets[index-1]["harmony_id"]
        )
        cadence=bool(onset["harmony"]["cadence"]) and onset["last_in_bar"]
        if cadence:
            structural=True

        if (
            pending_resolution is not None
            and pending_resolution["harmony_id"]==onset["harmony_id"]
            and pending_resolution["target"] in _pitch_pool(onset["chord_pcs"])
        ):
            note=pending_resolution["target"]
            pending_resolution=None
        else:
            pending_resolution=None
            pcs=(
                onset["chord_pcs"]
                if structural
                else onset["scale_pcs"]|onset["chord_pcs"]
            )
            note=_choose_pitch(rng,previous,pcs,category,direction)

            if (
                not structural
                and note%12 not in onset["chord_pcs"]
                and index+1<len(onsets)
                and onsets[index+1]["harmony_id"]==onset["harmony_id"]
            ):
                resolution_targets=[
                    pitch for pitch in _pitch_pool(onset["chord_pcs"])
                    if 1<=abs(pitch-note)<=2
                ]
                if resolution_targets:
                    pending_resolution={
                        "harmony_id":onset["harmony_id"],
                        "target":min(
                            resolution_targets,
                            key=lambda pitch:(abs(pitch-previous),pitch),
                        ),
                    }
                else:
                    note=_choose_pitch(
                        rng,previous,onset["chord_pcs"],category,direction
                    )

        interval=note-previous
        actual_direction=0 if interval==0 else (1 if interval>0 else -1)

        if index+1<len(onsets) and onsets[index+1]["bar"]==onset["bar"]:
            next_offset=onsets[index+1]["offset_qb"]
        else:
            next_offset=3.0
        articulation=(
            0.82
            if melody_variant=="CLASSICAL_PERIOD_TOPLINE"
            else 0.90
        )
        duration=max(0.12,(next_offset-onset["offset_qb"])*articulation)

        output.append({
            **onset,
            "midi":note,
            "duration_qb":round(duration,4),
            "interval":interval,
            "structural":structural,
            "cadence_melody":cadence,
            "desired_interval_bucket":category,
            "actual_interval_bucket":_bucket(interval),
            "motif_return":(
                onset["bar"]==17
                and motif_position is not None
                and motif_position<len(motif)
            ),
        })

        if actual_direction:
            last_direction=actual_direction
        previous_interval_abs=abs(interval)
        previous=note

    return {
        "schema":SCHEMA,
        "melody_variant":melody_variant,
        "grammar_variant":grammar_variant,
        "seed":seed,
        "grammar_plan":grammar_plan,
        "motif_template":[
            {"bucket":bucket,"direction":direction}
            for bucket,direction in motif
        ],
        "events":output,
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

    structural=[e for e in events if e["structural"]]
    nonchord=[
        e for e in events
        if not e["structural"] and e["midi"]%12 not in e["chord_pcs"]
    ]
    nonchord_resolution=0
    for index,event in enumerate(events[:-1]):
        if event not in nonchord:
            continue
        next_event=events[index+1]
        if (
            1<=abs(next_event["midi"]-event["midi"])<=2
            and next_event["midi"]%12 in next_event["chord_pcs"]
        ):
            nonchord_resolution+=1

    motif_return=[e for e in events if e["motif_return"]]
    cadences=[e for e in events if e["cadence_melody"]]

    leap_indices=[
        index for index,event in enumerate(events[:-1])
        if abs(event["interval"])>=5 and event["interval"]!=0
    ]
    leap_recovery=0
    for index in leap_indices:
        direction=1 if events[index]["interval"]>0 else -1
        next_index=index+1
        while next_index<len(events) and events[next_index]["interval"]==0:
            next_index+=1
        if next_index<len(events):
            next_direction=1 if events[next_index]["interval"]>0 else -1
            if next_direction==-direction:
                leap_recovery+=1

    return {
        "melody_variant":plan["melody_variant"],
        "grammar_variant":plan["grammar_variant"],
        "seed":plan["seed"],
        "note_count":len(events),
        "notes_per_qb":round(len(events)/84.0,3),
        "mean_abs_interval":round(sum(intervals)/len(intervals),3),
        "repeat_pct":round(100*sum(x==0 for x in intervals)/len(intervals),2),
        "step_pct":round(100*sum(1<=x<=2 for x in intervals)/len(intervals),2),
        "third_pct":round(100*sum(3<=x<=4 for x in intervals)/len(intervals),2),
        "leap5_pct":round(100*sum(x>=5 for x in intervals)/len(intervals),2),
        "large7_pct":round(100*sum(x>=7 for x in intervals)/len(intervals),2),
        "direction_change_pct":round(
            100*direction_changes/max(1,len(directions)-1),2
        ),
        "mean_note_duration_qb":round(
            sum(e["duration_qb"] for e in events)/len(events),3
        ),
        "structural_chord_tone_pct":round(
            100*sum(e["midi"]%12 in e["chord_pcs"] for e in structural)
            /len(structural),2
        ),
        "nonchord_step_resolution_pct":round(
            100*nonchord_resolution/max(1,len(nonchord)),2
        ),
        "nonchord_event_count":len(nonchord),
        "cadence_chord_tone_pct":round(
            100*sum(e["midi"]%12 in e["chord_pcs"] for e in cadences)
            /max(1,len(cadences)),2
        ),
        "motif_return_bucket_match_pct":round(
            100*sum(
                e["desired_interval_bucket"]==e["actual_interval_bucket"]
                for e in motif_return
            )/max(1,len(motif_return)),2
        ),
        "large_leap_recovery_pct":round(
            100*leap_recovery/max(1,len(leap_indices)),2
        ),
        "max_interval_semitones":max(intervals),
    }

def aggregate_validation(seeds=32):
    result={
        "schema":SCHEMA,
        "status":"PASS",
        "research_only":True,
        "live_runtime_modified":False,
        "orchestration_enabled":False,
        "variants":{},
    }

    for melody_variant in PAIRINGS:
        summaries=[
            summarize(build_bound_melody(melody_variant,seed))
            for seed in range(seeds)
        ]
        keys=(
            "note_count","notes_per_qb","mean_abs_interval","repeat_pct",
            "step_pct","third_pct","leap5_pct","large7_pct",
            "direction_change_pct","mean_note_duration_qb",
            "structural_chord_tone_pct","nonchord_step_resolution_pct",
            "nonchord_event_count","cadence_chord_tone_pct",
            "motif_return_bucket_match_pct","large_leap_recovery_pct",
            "max_interval_semitones",
        )
        means={
            key:round(sum(s[key] for s in summaries)/len(summaries),3)
            for key in keys
        }
        result["variants"][melody_variant]={
            "seed_count":seeds,
            "means":means,
            "worst_case":{
                "max_interval_semitones":max(
                    s["max_interval_semitones"] for s in summaries
                ),
                "minimum_structural_chord_tone_pct":min(
                    s["structural_chord_tone_pct"] for s in summaries
                ),
                "minimum_cadence_chord_tone_pct":min(
                    s["cadence_chord_tone_pct"] for s in summaries
                ),
            },
            "example_seed_0":summaries[0],
        }

    c=result["variants"]["CLASSICAL_PERIOD_TOPLINE"]["means"]
    r=result["variants"]["ROMANTIC_TONAL_TOPLINE"]["means"]

    for variant,data in result["variants"].items():
        assert data["means"]["structural_chord_tone_pct"]==100
        assert data["means"]["cadence_chord_tone_pct"]==100
        assert data["worst_case"]["max_interval_semitones"]<=12
        assert data["means"]["motif_return_bucket_match_pct"]>=75

    assert c["nonchord_step_resolution_pct"]>=70
    assert r["nonchord_step_resolution_pct"]>=60
    assert c["large_leap_recovery_pct"]>=80
    assert r["large_leap_recovery_pct"]>=75

    assert 2.0<=c["notes_per_qb"]<=2.35
    assert 1.5<=r["notes_per_qb"]<=1.85
    assert 45<=c["step_pct"]<=65
    assert 34<=r["step_pct"]<=53
    assert 12<=c["leap5_pct"]<=25
    assert 20<=r["leap5_pct"]<=35
    assert c["max_interval_semitones"]<=12
    assert r["max_interval_semitones"]<=12

    assert r["notes_per_qb"]<c["notes_per_qb"]-0.3
    assert r["mean_abs_interval"]>c["mean_abs_interval"]+0.25
    assert r["step_pct"]<c["step_pct"]-5
    assert r["leap5_pct"]>c["leap5_pct"]+5
    assert r["mean_note_duration_qb"]>c["mean_note_duration_qb"]+0.10

    return result

def main():
    import json
    print(json.dumps(aggregate_validation(),indent=2,sort_keys=True))

if __name__=="__main__":
    main()
