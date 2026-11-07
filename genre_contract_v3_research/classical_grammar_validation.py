"""Research-only period composition-grammar harness for Classical family.

This module intentionally does not modify the live Composer and does not render
audio.  It creates abstract harmonic-event plans so period grammar can be tested
before pitches, orchestration, mixing, or sound design are allowed to confound
the result.

Evidence sources are recorded in GENRE_CONTRACT_V3_ALL_55.json.  Corpus values
are treated as descriptive bands, never literal composition quotas.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
import random

SCHEMA = "CLASSICAL_PERIOD_GRAMMAR_VALIDATION_001"
BAR_QB = 3.0
BARS = 28

SECTIONS = (
    ("A", 1, 8),
    ("B", 9, 16),
    ("A_RETURN", 17, 24),
    ("CODA", 25, 28),
)

TARGETS = {
    "CLASSICAL_PERIOD_TONAL": {
        "mean_harmony_qb": 1.467,
        "localkey_duration_pct": 43.10,
        "applied_pct": 10.40,
        "altered_pct": 11.35,
        "diminished_pct": 9.93,
        "aug6_pct": 0.88,
        "extended_pct": 24.97,
        "cadence_rate_per_100_qb": 4.976,
        "cadence_weights": {
            "PAC": 47.35, "HC": 35.70, "IAC": 6.19, "EC": 7.35, "DC": 3.41,
        },
    },
    "ROMANTIC_TONAL_EXPANDED": {
        "mean_harmony_qb": 1.434,
        "localkey_duration_pct": 66.31,
        "applied_pct": 17.23,
        "altered_pct": 21.49,
        "diminished_pct": 12.26,
        "aug6_pct": 1.33,
        "extended_pct": 33.98,
        "cadence_rate_per_100_qb": 4.189,
        "cadence_weights": {
            "PAC": 38.43, "HC": 34.49, "IAC": 22.92, "PC": 2.55, "EC": 1.16, "DC": 0.46,
        },
    },
}

# Number of harmonic events per 3/4 bar.  These counts approximate the corpus
# harmonic-rhythm observations while allowing stability at structural arrivals.
EVENT_COUNT_PROFILE = {
    "CLASSICAL_PERIOD_TONAL": [2] * 23 + [3] * 3 + [1] * 2,  # 57 events / 84 qb
    "ROMANTIC_TONAL_EXPANDED": [2] * 21 + [3] * 5 + [1] * 2, # 59 events / 84 qb
}

CLASSICAL_LOCAL_REGIONS = ("V", "vi", "IV", "III")
ROMANTIC_LOCAL_REGIONS = ("III", "V", "bVI", "iv", "bIII", "vi")

CLASSICAL_NUMERALS = {
    "TONIC": ("I", "I6", "vi", "I"),
    "PREDOMINANT": ("ii6", "IV", "ii7", "IV6"),
    "DOMINANT": ("V", "V7", "vii6", "V65"),
}
ROMANTIC_NUMERALS = {
    "TONIC": ("i", "I6", "III", "bVI"),
    "PREDOMINANT": ("iv6", "iiø65", "N6", "Ger+6"),
    "DOMINANT": ("V7", "V9", "viio7", "V65"),
}

def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()

def _section_for_bar(bar):
    for name, start, end in SECTIONS:
        if start <= bar <= end:
            return name
    raise ValueError("BAR_OUT_OF_FORM")

def _weighted_choice(rng, weights):
    items = list(weights.items())
    total = sum(max(0.0, float(v)) for _, v in items)
    pick = rng.random() * total
    running = 0.0
    for key, value in items:
        running += max(0.0, float(value))
        if pick <= running:
            return key
    return items[-1][0]

def _internal_cadence_weights(weights):
    """Compensate three internal choices for one deliberately forced final PAC.

    With four cadences per plan, one PAC is structurally reserved for the coda.
    The other three are reweighted so the aggregate cadence family remains near
    the corpus distribution across many seeds.
    """
    total=sum(float(v) for v in weights.values())
    p={k:float(v)/total for k,v in weights.items()}
    q={}
    for k,v in p.items():
        expected_total=4.0*v
        forced=1.0 if k=="PAC" else 0.0
        q[k]=max(0.0,(expected_total-forced)/3.0)
    qsum=sum(q.values())
    return {k:100.0*v/qsum for k,v in q.items()}

def _event_counts(variant, seed):
    profile = list(EVENT_COUNT_PROFILE[variant])
    rng = random.Random(seed * 101 + (17 if variant.startswith("ROMANTIC") else 3))
    rng.shuffle(profile)
    # Cadential bars should not be the sparsest bars.
    for cadence_bar in (8, 16, 24, 28):
        idx = cadence_bar - 1
        if profile[idx] == 1:
            swap = next((j for j, n in enumerate(profile) if n == 2 and j not in (7,15,23,27)), None)
            if swap is not None:
                profile[idx], profile[swap] = profile[swap], profile[idx]
    return profile

def _durations_for_count(count, seed, bar, variant):
    rng = random.Random(seed * 1009 + bar * 37 + (5 if variant.startswith("ROMANTIC") else 1))
    if count == 1:
        return (3.0,)
    if count == 2:
        return rng.choice(((1.5,1.5),(1.0,2.0),(2.0,1.0)))
    if count == 3:
        return rng.choice(((1.0,1.0,1.0),(0.5,1.0,1.5),(1.5,1.0,0.5)))
    raise ValueError("UNSUPPORTED_EVENT_COUNT")

def _localkey_by_bar(variant, seed):
    """Contiguous tonal-region windows, not random per-event key flipping."""
    rng = random.Random(seed * 211 + (71 if variant.startswith("ROMANTIC") else 29))
    out = {bar:"I" for bar in range(1, BARS+1)}
    if variant == "CLASSICAL_PERIOD_TONAL":
        # 12 of 28 bars (~43%) outside global tonic.
        regions = list(CLASSICAL_LOCAL_REGIONS)
        rng.shuffle(regions)
        spans = ((9,16,regions[0]), (19,22,regions[1]))
    else:
        # 19 of 28 bars (~68%), near the 66% empirical reference.
        regions = list(ROMANTIC_LOCAL_REGIONS)
        rng.shuffle(regions)
        spans = ((5,12,regions[0]), (14,20,regions[1]), (22,25,regions[2]))
    for start,end,key in spans:
        for bar in range(start,end+1):
            out[bar]=key
    return out

def _formal_function(event_index, event_count, bar, section):
    if bar in (8,16,24,28):
        if event_index == event_count - 1:
            return "CADENCE"
        if event_index >= max(0,event_count-2):
            return "DOMINANT"
    frac=(event_index+1)/event_count
    if frac <= 0.34:
        return "TONIC"
    if frac <= 0.67:
        return "PREDOMINANT"
    return "DOMINANT"

def _feature_threshold(seed, bar, event_index, salt):
    rng=random.Random(seed*65537 + bar*257 + event_index*17 + salt)
    return rng.random()*100.0

def _decorate_event(variant, seed, bar, event_index, function, numeral, cadence):
    target=TARGETS[variant]
    romantic=variant.startswith("ROMANTIC")
    applied=_feature_threshold(seed,bar,event_index,11) < target["applied_pct"]
    altered=_feature_threshold(seed,bar,event_index,23) < target["altered_pct"]
    diminished=_feature_threshold(seed,bar,event_index,31) < target["diminished_pct"]
    extended=_feature_threshold(seed,bar,event_index,43) < max(0.0, target["extended_pct"] - 10.0)
    aug6=_feature_threshold(seed,bar,event_index,59) < target["aug6_pct"]

    # Keep feature choices functionally plausible.
    if function == "DOMINANT":
        if diminished:
            numeral = "viio7/V" if applied else "viio7"
            extended = True
        elif applied:
            numeral = "V7/V"
            extended = True
        elif extended:
            numeral = "V9" if romantic else "V7"
    elif function == "PREDOMINANT":
        if aug6:
            numeral = "Ger+6"
            altered = True
            extended = True
        elif romantic and altered:
            numeral = "N6"
        elif diminished:
            numeral = "iiø65"
            extended = True
    elif function == "TONIC" and romantic and altered:
        numeral = "bVI" if (bar + event_index + seed) % 2 == 0 else "III"

    # Cadence outcome owns the last event label.
    if cadence:
        if cadence == "PAC":
            numeral = "I" if not romantic else "i"
        elif cadence == "IAC":
            numeral = "I6" if not romantic else "i6"
        elif cadence == "HC":
            numeral = "V"
            extended = False
        elif cadence in ("DC","EC"):
            numeral = "vi" if not romantic else "VI"
        elif cadence == "PC":
            numeral = "I" if not romantic else "i"

    return {
        "numeral": numeral,
        "applied": bool(applied),
        "altered": bool(altered),
        "diminished": bool(diminished),
        "augmented_sixth": bool(aug6),
        "seventh_or_extended": bool(extended),
    }

def build_plan(variant, seed=0):
    if variant not in TARGETS:
        raise ValueError("UNKNOWN_GRAMMAR_VARIANT")
    rng=random.Random(seed*4099 + (101 if variant.startswith("ROMANTIC") else 13))
    counts=_event_counts(variant,seed)
    localkeys=_localkey_by_bar(variant,seed)
    cadence_weights=_internal_cadence_weights(TARGETS[variant]["cadence_weights"])
    events=[]
    cadence_bars=(8,16,24,28)
    cadence_types={}
    for bar in cadence_bars:
        # Final cadence favors closure while still allowing corpus-weighted variety elsewhere.
        cadence_types[bar] = "PAC" if bar == 28 else _weighted_choice(rng,cadence_weights)

    for bar in range(1,BARS+1):
        section=_section_for_bar(bar)
        count=counts[bar-1]
        durations=_durations_for_count(count,seed,bar,variant)
        offset=0.0
        library=ROMANTIC_NUMERALS if variant.startswith("ROMANTIC") else CLASSICAL_NUMERALS
        for i,duration in enumerate(durations):
            function=_formal_function(i,count,bar,section)
            cadence=cadence_types.get(bar) if function=="CADENCE" else None
            source_function="DOMINANT" if function=="CADENCE" else function
            numeral=library[source_function][(bar+i+seed)%len(library[source_function])]
            decorated=_decorate_event(variant,seed,bar,i,source_function,numeral,cadence)
            events.append({
                "bar":bar,
                "section":section,
                "offset_qb":round(offset,3),
                "duration_qb":round(duration,3),
                "localkey":localkeys[bar],
                "function":function,
                "cadence":cadence,
                **decorated,
            })
            offset += duration
        if abs(offset-BAR_QB)>1e-8:
            raise AssertionError("BAR_DURATION_MISMATCH")
    return {
        "schema":SCHEMA,
        "variant":variant,
        "seed":seed,
        "meter":"3/4",
        "bars":BARS,
        "sections":[{"name":n,"start_bar":s,"end_bar":e} for n,s,e in SECTIONS],
        "events":events,
    }

def summarize(plan):
    events=plan["events"]
    total_qb=sum(e["duration_qb"] for e in events)
    local_qb=sum(e["duration_qb"] for e in events if e["localkey"]!="I")
    cad=Counter(e["cadence"] for e in events if e["cadence"])
    def pct(field):
        return round(100.0*sum(bool(e[field]) for e in events)/len(events),2)
    return {
        "schema":SCHEMA,
        "variant":plan["variant"],
        "seed":plan["seed"],
        "plan_sha256":digest(plan),
        "event_count":len(events),
        "total_qb":round(total_qb,3),
        "mean_harmony_qb":round(total_qb/len(events),3),
        "localkey_duration_pct":round(100.0*local_qb/total_qb,2),
        "applied_pct":pct("applied"),
        "altered_pct":pct("altered"),
        "diminished_pct":pct("diminished"),
        "aug6_pct":pct("augmented_sixth"),
        "extended_pct":pct("seventh_or_extended"),
        "cadences_per_100_qb":round(100.0*sum(cad.values())/total_qb,3),
        "cadence_counts":dict(sorted(cad.items())),
        "numeral_counts":dict(Counter(e["numeral"] for e in events).most_common()),
        "localkey_counts":dict(Counter(e["localkey"] for e in events).most_common()),
    }

def aggregate_validation(seeds=32):
    by_variant={}
    for variant in TARGETS:
        summaries=[summarize(build_plan(variant,seed)) for seed in range(seeds)]
        keys=("mean_harmony_qb","localkey_duration_pct","applied_pct","altered_pct",
              "diminished_pct","aug6_pct","extended_pct","cadences_per_100_qb")
        means={k:round(sum(s[k] for s in summaries)/len(summaries),3) for k in keys}
        cads=Counter()
        for s in summaries:
            cads.update(s["cadence_counts"])
        by_variant[variant]={
            "seed_count":seeds,
            "means":means,
            "cadence_counts":dict(sorted(cads.items())),
            "examples":{"seed_0":summaries[0]},
        }

    c=by_variant["CLASSICAL_PERIOD_TONAL"]["means"]
    r=by_variant["ROMANTIC_TONAL_EXPANDED"]["means"]

    # Broad evidence bands, deliberately not exact-quota tests.
    assert 1.20 <= c["mean_harmony_qb"] <= 1.80
    assert 30 <= c["localkey_duration_pct"] <= 55
    assert 5 <= c["applied_pct"] <= 16
    assert 6 <= c["altered_pct"] <= 18
    assert 5 <= c["diminished_pct"] <= 16
    assert 18 <= c["extended_pct"] <= 34
    assert 3.5 <= c["cadences_per_100_qb"] <= 6.5

    assert 1.15 <= r["mean_harmony_qb"] <= 1.80
    assert 50 <= r["localkey_duration_pct"] <= 80
    assert 10 <= r["applied_pct"] <= 26
    assert 14 <= r["altered_pct"] <= 32
    assert 7 <= r["diminished_pct"] <= 19
    assert 27 <= r["extended_pct"] <= 45
    assert 2.5 <= r["cadences_per_100_qb"] <= 5.5

    assert r["localkey_duration_pct"] > c["localkey_duration_pct"] + 15
    assert r["applied_pct"] > c["applied_pct"]
    assert r["altered_pct"] > c["altered_pct"]
    assert r["extended_pct"] > c["extended_pct"]
    assert abs(r["mean_harmony_qb"]-c["mean_harmony_qb"]) < 0.30

    return {
        "schema":SCHEMA,
        "status":"PASS",
        "research_only":True,
        "live_runtime_modified":False,
        "abstract_harmony_only":True,
        "variants":by_variant,
    }

def main():
    print(json.dumps(aggregate_validation(),indent=2,sort_keys=True))

if __name__ == "__main__":
    main()
