"""Research-only SATB voice-leading validation for Classical period grammar.

Consumes abstract harmonic plans from classical_grammar_validation.py and
resolves them into four independent voices.  No live Composer code is modified
and no orchestration/audio behavior is activated here.
"""
from __future__ import annotations

from collections import Counter
import itertools
import math
import re

from genre_contract_v3_research import classical_grammar_validation as grammar

SCHEMA = "CLASSICAL_PERIOD_VOICE_LEADING_VALIDATION_001"

VOICE_RANGES = {
    "S": (60, 81),
    "A": (55, 74),
    "T": (48, 67),
    "B": (36, 60),
}
VOICE_TARGET = {"S":72, "A":64, "T":57, "B":48}
VOICES = ("S","A","T","B")
VOICE_PAIRS = tuple(itertools.combinations(VOICES, 2))

LOCAL_ROOT_PC = {
    "I":0, "V":7, "vi":9, "IV":5, "III":4,
    "bVI":8, "iv":5, "bIII":3,
}

def chord_spec(label, local_root, variant):
    """Return (pitch_classes, bass_pc, essential_pitch_classes)."""
    if label == "Ger+6":
        pcs={(local_root+x)%12 for x in (8,0,3,6)}
        return pcs,(local_root+8)%12,pcs
    if label == "N6":
        pcs={(local_root+x)%12 for x in (1,5,8)}
        return pcs,(local_root+5)%12,pcs

    base=label
    target_root=local_root
    if label.endswith("/V"):
        base=label[:-2]
        target_root=(local_root+7)%12

    if base.startswith("viio"):
        root=(target_root+11)%12
        pcs={root,(root+3)%12,(root+6)%12}
        if "7" in base:
            pcs.add((root+9)%12)
        if "65" in base:
            bass=(root+3)%12
        elif "43" in base:
            bass=(root+6)%12
        elif base.endswith("2"):
            bass=(root+9)%12
        elif base.endswith("6") and "7" not in base:
            bass=(root+3)%12
        else:
            bass=root
        return pcs,bass,pcs

    if base.startswith("iiø"):
        root=(target_root+2)%12
        pcs={root,(root+3)%12,(root+6)%12,(root+10)%12}
        bass=(root+3)%12 if "65" in base else root
        return pcs,bass,pcs

    match=re.match(r"([b#]?)([IViv]+)",base)
    if match is None:
        raise ValueError("UNSUPPORTED_ROMAN_LABEL:"+label)
    accidental,roman=match.groups()
    upper=roman.upper()
    degree={"I":0,"II":2,"III":4,"IV":5,"V":7,"VI":9,"VII":11}
    root=(target_root+degree[upper])%12

    # Deceptive VI in the Romantic-minor grammar is flat-six scale degree.
    if variant.startswith("ROMANTIC") and roman=="VI":
        root=(target_root+8)%12
    if accidental=="b":
        root=(root-1)%12
    elif accidental=="#":
        root=(root+1)%12

    is_minor=roman.islower()
    if upper=="VII":
        intervals=(0,3,6)
    else:
        intervals=(0,3,7) if is_minor else (0,4,7)
    pcs={(root+x)%12 for x in intervals}

    seventh=False
    seventh_interval=10 if upper=="V" or is_minor else 11
    if any(x in base for x in ("7","65","43")) or base.endswith("2"):
        seventh=True
        pcs.add((root+seventh_interval)%12)
    if "9" in base:
        seventh=True
        # Dominant ninth includes both seventh and ninth.
        pcs.add((root+seventh_interval)%12)
        pcs.add((root+2)%12)

    if "64" in base:
        bass=(root+7)%12
    elif "65" in base or (base.endswith("6") and "7" not in base):
        bass=(root+(3 if is_minor or upper=="VII" else 4))%12
    elif "43" in base:
        bass=(root+7)%12
    elif base.endswith("2"):
        bass=(root+seventh_interval)%12
    else:
        bass=root

    third=(root+(3 if is_minor or upper=="VII" else 4))%12
    essential={root,third}
    if seventh:
        essential.add((root+seventh_interval)%12)
    return pcs,bass,essential

def pitch_candidates(pcs, voice, previous=None, bass_pc=None):
    lo,hi=VOICE_RANGES[voice]
    values=[
        n for n in range(lo,hi+1)
        if n%12 in pcs and (bass_pc is None or n%12==bass_pc)
    ]
    center=VOICE_TARGET[voice] if previous is None else previous
    values.sort(key=lambda n:(abs(n-center),n))
    return values[:7]

def has_parallel_perfect(previous, current):
    for v1,v2 in VOICE_PAIRS:
        old_interval=(previous[v1]-previous[v2])%12
        new_interval=(current[v1]-current[v2])%12
        if old_interval in (0,7) and new_interval==old_interval:
            d1=current[v1]-previous[v1]
            d2=current[v2]-previous[v2]
            if d1*d2>0:
                return True
    return False

def choose_voicing(spec, previous=None, cadence=None, local_root=0):
    pcs,bass_pc,essential=spec
    candidates={
        "S":pitch_candidates(pcs,"S",None if previous is None else previous["S"]),
        "A":pitch_candidates(pcs,"A",None if previous is None else previous["A"]),
        "T":pitch_candidates(pcs,"T",None if previous is None else previous["T"]),
        "B":pitch_candidates(pcs,"B",None if previous is None else previous["B"],bass_pc=bass_pc),
    }
    best=None
    for S,A,T,B in itertools.product(
        candidates["S"],candidates["A"],candidates["T"],candidates["B"]
    ):
        if not (S>A>T>B):
            continue
        if S-A>12 or A-T>12 or T-B>19:
            continue
        current={"S":S,"A":A,"T":T,"B":B}
        if previous is not None and has_parallel_perfect(previous,current):
            continue

        present={n%12 for n in current.values()}
        cost=len(essential-present)*120 + max(0,3-len(present))*60

        leading_tone=(local_root+11)%12
        if sum(n%12==leading_tone for n in current.values())>1:
            cost+=50

        if previous is None:
            cost += sum(abs(current[v]-VOICE_TARGET[v])*0.3 for v in VOICES)
        else:
            for voice in VOICES:
                leap=abs(current[voice]-previous[voice])
                cost+=leap
                if leap>7:
                    cost+=(leap-7)*5
                if leap>12:
                    cost+=200
                if current[voice]%12==previous[voice]%12:
                    cost-=1.5

            if cadence in ("PAC","IAC"):
                dominant_seventh=(local_root+5)%12
                for voice in VOICES:
                    if previous[voice]%12==leading_tone:
                        correct=(
                            current[voice]%12==local_root%12
                            and current[voice]-previous[voice] in (1,-11)
                        )
                        if not correct:
                            cost+=35
                    if previous[voice]%12==dominant_seventh:
                        descending=previous[voice]-current[voice]
                        target_ok=current[voice]%12 in (
                            (local_root+4)%12,(local_root+3)%12
                        )
                        if not (target_ok and descending in (1,2,13,14)):
                            cost+=22

        if best is None or cost<best[0]:
            best=(cost,current)

    if best is None:
        raise RuntimeError("NO_PLAYABLE_VOICING")
    return best[1],best[0]

def realize(plan):
    previous=None
    output=[]
    for event in plan["events"]:
        local_root=LOCAL_ROOT_PC.get(event["localkey"],0)
        spec=chord_spec(event["numeral"],local_root,plan["variant"])
        voicing,cost=choose_voicing(spec,previous,event["cadence"],local_root)
        output.append({
            **event,
            "local_root_pc":local_root,
            "voicing":voicing,
            "voice_leading_cost":round(cost,3),
            "chord_pcs":sorted(spec[0]),
            "expected_bass_pc":spec[1],
            "essential_pcs":sorted(spec[2]),
        })
        previous=voicing
    return output

def summarize(realized, variant):
    leaps={voice:[] for voice in VOICES}
    crossings=0
    parallels=0
    full_essential=0
    bass_correct=0
    doubled_leading=0
    common_tone_steps=0
    transition_count=max(0,len(realized)-1)

    lt_total=lt_resolved=0
    seventh_total=seventh_resolved=0

    for index,event in enumerate(realized):
        v=event["voicing"]
        if not (v["S"]>v["A"]>v["T"]>v["B"]):
            crossings+=1
        present={v[voice]%12 for voice in VOICES}
        if set(event["essential_pcs"]).issubset(present):
            full_essential+=1
        if v["B"]%12==event["expected_bass_pc"]:
            bass_correct+=1
        leading_tone=(event["local_root_pc"]+11)%12
        if sum(v[voice]%12==leading_tone for voice in VOICES)>1:
            doubled_leading+=1

        if index==0:
            continue
        previous=realized[index-1]["voicing"]
        if has_parallel_perfect(previous,v):
            parallels+=1
        if any(v[voice]%12==previous[voice]%12 for voice in VOICES):
            common_tone_steps+=1
        for voice in VOICES:
            leaps[voice].append(abs(v[voice]-previous[voice]))

        if event["cadence"] in ("PAC","IAC"):
            root=event["local_root_pc"]
            lt=(root+11)%12
            seventh=(root+5)%12
            for voice in VOICES:
                if previous[voice]%12==lt:
                    lt_total+=1
                    if (
                        v[voice]%12==root%12
                        and v[voice]-previous[voice] in (1,-11)
                    ):
                        lt_resolved+=1
                if previous[voice]%12==seventh:
                    seventh_total+=1
                    descending=previous[voice]-v[voice]
                    target_ok=v[voice]%12 in ((root+4)%12,(root+3)%12)
                    if target_ok and descending in (1,2,13,14):
                        seventh_resolved+=1

    all_leaps=[x for values in leaps.values() for x in values]
    all_leaps_sorted=sorted(all_leaps)
    p95=all_leaps_sorted[min(len(all_leaps_sorted)-1,math.ceil(0.95*len(all_leaps_sorted))-1)]

    return {
        "variant":variant,
        "event_count":len(realized),
        "voice_crossings":crossings,
        "parallel_perfect_5_8":parallels,
        "full_essential_coverage_pct":round(100*full_essential/len(realized),2),
        "bass_inversion_accuracy_pct":round(100*bass_correct/len(realized),2),
        "doubled_leading_tone_event_pct":round(100*doubled_leading/len(realized),2),
        "mean_leap_semitones":round(sum(all_leaps)/len(all_leaps),3),
        "p95_leap_semitones":p95,
        "max_leap_semitones":max(all_leaps),
        "common_tone_transition_pct":round(100*common_tone_steps/max(1,transition_count),2),
        "leading_tone_resolution_pct":round(100*lt_resolved/max(1,lt_total),2),
        "dominant_seventh_resolution_pct":round(100*seventh_resolved/max(1,seventh_total),2),
        "voice_mean_leap":{
            voice:round(sum(values)/len(values),3) for voice,values in leaps.items()
        },
        "tendency_counts":{
            "leading_tone_total":lt_total,
            "leading_tone_resolved":lt_resolved,
            "dominant_seventh_total":seventh_total,
            "dominant_seventh_resolved":seventh_resolved,
        },
    }

def aggregate_validation(seeds=32):
    result={
        "schema":SCHEMA,
        "status":"PASS",
        "research_only":True,
        "live_runtime_modified":False,
        "voice_model":"ABSTRACT_SATB",
        "variants":{},
    }
    for variant in grammar.TARGETS:
        summaries=[]
        total_tendency=Counter()
        for seed in range(seeds):
            plan=grammar.build_plan(variant,seed)
            summary=summarize(realize(plan),variant)
            summaries.append(summary)
            total_tendency.update({
                "lt_total":summary["tendency_counts"]["leading_tone_total"],
                "lt_resolved":summary["tendency_counts"]["leading_tone_resolved"],
                "seventh_total":summary["tendency_counts"]["dominant_seventh_total"],
                "seventh_resolved":summary["tendency_counts"]["dominant_seventh_resolved"],
            })

        means={}
        for key in (
            "voice_crossings","parallel_perfect_5_8",
            "full_essential_coverage_pct","bass_inversion_accuracy_pct",
            "doubled_leading_tone_event_pct","mean_leap_semitones",
            "p95_leap_semitones","max_leap_semitones",
            "common_tone_transition_pct",
        ):
            means[key]=round(sum(s[key] for s in summaries)/len(summaries),3)

        means["leading_tone_resolution_pct"]=round(
            100*total_tendency["lt_resolved"]/max(1,total_tendency["lt_total"]),2
        )
        means["dominant_seventh_resolution_pct"]=round(
            100*total_tendency["seventh_resolved"]/max(1,total_tendency["seventh_total"]),2
        )

        result["variants"][variant]={
            "seed_count":seeds,
            "means":means,
            "worst_case":{
                "max_leap_semitones":max(s["max_leap_semitones"] for s in summaries),
                "p95_leap_semitones":max(s["p95_leap_semitones"] for s in summaries),
                "mean_leap_semitones":max(s["mean_leap_semitones"] for s in summaries),
                "minimum_common_tone_transition_pct":min(s["common_tone_transition_pct"] for s in summaries),
            },
            "example_seed_0":summaries[0],
        }

        assert means["voice_crossings"]==0
        assert means["parallel_perfect_5_8"]==0
        assert means["full_essential_coverage_pct"]==100
        assert means["bass_inversion_accuracy_pct"]==100
        assert means["doubled_leading_tone_event_pct"]==0
        assert result["variants"][variant]["worst_case"]["max_leap_semitones"]<=12
        assert result["variants"][variant]["worst_case"]["p95_leap_semitones"]<=7
        assert result["variants"][variant]["worst_case"]["mean_leap_semitones"]<=2.5
        assert means["leading_tone_resolution_pct"]>=80
        assert means["dominant_seventh_resolution_pct"]>=65
        assert result["variants"][variant]["worst_case"]["minimum_common_tone_transition_pct"]>=45

    return result

def main():
    import json
    print(json.dumps(aggregate_validation(),indent=2,sort_keys=True))

if __name__=="__main__":
    main()
