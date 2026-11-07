"""Research-only Classical variant orchestration harness.

This module does NOT replace the live Classical generator. It imports the
existing thematic/harmonic pilot, preserves one plan, and applies an isolated
role-state orchestration layer for structural/listening validation.

The goal is to test whether evidence-backed Classical variants can change
foreground ownership, supporting density, and section interaction without
changing the underlying thematic seed or harmony.
"""
from __future__ import annotations

import copy
import json
from collections import Counter, defaultdict
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "current_master_forward"))

import classical_composition as cc  # noqa: E402

SCHEMA_ID = "CLASSICAL_VARIANT_VALIDATION_HARNESS_001"

FAMILY_BY_INSTRUMENT = {
    "violin": "STRINGS",
    "viola": "STRINGS",
    "cello": "STRINGS",
    "double_bass": "STRINGS",
    "concert_flute": "WOODWINDS",
    "oboe": "WOODWINDS",
    "clarinet_bb": "WOODWINDS",
    "bassoon": "WOODWINDS",
    "horn_f": "BRASS",
    "trumpet_c": "BRASS",
    "tenor_trombone": "BRASS",
    "bass_tuba": "BRASS",
    "timpani": "PERCUSSION",
}

PLAYER_BY_INSTRUMENT = {
    "violin": "VIOLIN_I_1",
    "viola": "VIOLA_1",
    "cello": "CELLO_1",
    "double_bass": "DOUBLE_BASS_1",
    "concert_flute": "FLUTE_1",
    "oboe": "OBOE_1",
    "clarinet_bb": "CLARINET_1",
    "bassoon": "BASSOON_1",
    "horn_f": "HORN_1",
    "trumpet_c": "TRUMPET_1",
    "tenor_trombone": "TROMBONE_1",
    "bass_tuba": "TUBA_1",
}

ACTIVITY_TARGET_PERCENT = {
    "CLASSICAL_PERIOD_BASELINE": {
        "STRINGS": 92.78,
        "WOODWINDS": 74.23,
        "BRASS": 46.76,
        "PERCUSSION": 17.85,
    },
    "LATE_ROMANTIC_EXPANDED": {
        "STRINGS": 91.88,
        "WOODWINDS": 70.12,
        "BRASS": 62.19,
        "PERCUSSION": 24.47,
    },
}

ACTIVITY_TARGETS = {
    "CLASSICAL_PERIOD_BASELINE": {
        "STRINGS": 92.78,
        "WOODWINDS": 74.23,
        "BRASS": 46.76,
        "PERCUSSION": 17.85,
    },
    "LATE_ROMANTIC_EXPANDED": {
        "STRINGS": 91.88,
        "WOODWINDS": 70.12,
        "BRASS": 62.19,
        "PERCUSSION": 24.47,
    },
}

VARIANT_SCHEDULES = {
    "CLASSICAL_PERIOD_BASELINE": {
        "A": ("violin", "violin", "oboe", "violin"),
        "B": ("concert_flute", "violin", "clarinet_bb", "violin"),
        "A_RETURN": ("violin", "concert_flute", "violin", "oboe"),
        "CODA": ("violin", "clarinet_bb"),
    },
    "LATE_ROMANTIC_EXPANDED": {
        "A": ("violin", "oboe", "horn_f", "cello"),
        "B": ("clarinet_bb", "horn_f", "concert_flute", "violin"),
        "A_RETURN": ("violin", "tenor_trombone", "oboe", "horn_f"),
        "CODA": ("violin", "concert_flute", "trumpet_c", "cello"),
    },
}


def _is_theme_event(event):
    rule = event.get("source_rule", "")
    return rule == "cadence_goal" or rule.startswith("motif_")


def _family(event):
    return FAMILY_BY_INSTRUMENT.get(event.get("instrument_id"), "OTHER")


def _foreground_instrument(variant_id, bar):
    schedule = VARIANT_SCHEDULES[variant_id][bar["section"]]
    # Two-bar ownership windows make handoffs explicit while keeping phrase
    # continuity. Coda may be shorter; modulo keeps the rule deterministic.
    window = ((bar["phrase_position"] // 2) % len(schedule))
    return schedule[window]


def _retarget_note(note, instrument):
    return cc.nearest({int(note) % 12}, int(note), cc.RANGES[instrument])


def _activity_bar_sets(plan, base_events, variant_id):
    """Choose deterministic active bars close to corpus-derived family bands.

    Foreground bars are mandatory. Remaining active bars are selected only from
    bars where the base realization already contains that family, so this layer
    does not fabricate support activity merely to hit a number.
    """
    total_bars = len(plan["bars"])
    fg_by_bar = {
        bar["bar"]: FAMILY_BY_INSTRUMENT[_foreground_instrument(variant_id, bar)]
        for bar in plan["bars"]
    }
    available = defaultdict(set)
    for event in base_events:
        fam = _family(event)
        if fam in ACTIVITY_TARGET_PERCENT[variant_id]:
            available[fam].add(int(event["plan_bar"]))

    offsets = {"STRINGS": 3, "WOODWINDS": 7, "BRASS": 11, "PERCUSSION": 13}
    result = {}
    for fam, target in ACTIVITY_TARGET_PERCENT[variant_id].items():
        required = {bar for bar, fg in fg_by_bar.items() if fg == fam}
        desired = max(len(required), int(round(total_bars * target / 100.0)))
        candidates = list((available.get(fam, set()) | required) - required)
        candidates.sort(key=lambda b: (((b * 17) + offsets[fam]) % max(1, total_bars), b))
        selected = set(required)
        selected.update(candidates[: max(0, desired - len(required))])
        result[fam] = selected
    return result


def _even_fill(candidates, count):
    candidates = sorted(candidates)
    if count <= 0:
        return set()
    if count >= len(candidates):
        return set(candidates)
    if count == 1:
        return {candidates[len(candidates) // 2]}
    chosen = set()
    for i in range(count):
        index = round(i * (len(candidates) - 1) / (count - 1))
        chosen.add(candidates[index])
    if len(chosen) < count:
        for candidate in candidates:
            chosen.add(candidate)
            if len(chosen) == count:
                break
    return chosen


def _activity_bar_plan(plan, variant_id, base_events):
    total_bars = len(plan["bars"])
    foreground_by_bar = {
        bar["bar"]: FAMILY_BY_INSTRUMENT[_foreground_instrument(variant_id, bar)]
        for bar in plan["bars"]
    }
    available_by_family = defaultdict(set)
    for event in base_events:
        fam = _family(event)
        if fam != "OTHER":
            available_by_family[fam].add(int(event["plan_bar"]))

    planned = {}
    for fam, target_percent in ACTIVITY_TARGETS[variant_id].items():
        desired_count = round(total_bars * target_percent / 100.0)
        mandatory = {bar for bar, fg in foreground_by_bar.items() if fg == fam}
        desired_count = max(desired_count, len(mandatory))
        support_candidates = available_by_family[fam] - mandatory
        support_needed = max(0, desired_count - len(mandatory))
        planned[fam] = mandatory | _even_fill(support_candidates, support_needed)
    return planned


def _support_keep(variant_id, event, foreground_family, bar_number, activity_plan):
    """Deterministic activity-window + density shaping; never a gain decision."""
    fam = _family(event)
    pid = event.get("player_id", "")

    if fam in activity_plan and bar_number not in activity_plan[fam]:
        return False

    if fam == "STRINGS" and foreground_family != "STRINGS":
        # Keep harmonic foundation while yielding upper-string density.
        if pid.startswith("DOUBLE_BASS") or pid.startswith("CELLO") or pid.startswith("VIOLA"):
            return True
        if variant_id == "LATE_ROMANTIC_EXPANDED":
            # Large Romantic mass remains present, but not every upper desk.
            return pid == "VIOLIN_II_1" or bar_number % 2 == 0
        return pid == "VIOLIN_II_1" and bar_number % 2 == 0

    if fam == "BRASS":
        if variant_id == "CLASSICAL_PERIOD_BASELINE":
            # Classical baseline keeps brass structural; activity-window planning
            # controls when the family may be present.
            return event.get("source_rule") in {"orchestral_horn_support", "orchestral_brass_punctuation"}
        # Late Romantic keeps substantially more brass active.
        return True

    if fam == "WOODWINDS" and foreground_family == "BRASS":
        # Leave wind color under brass, but prevent all winds from clustering.
        return bar_number % 2 == 0 or pid.startswith(("BASSOON", "CLARINET"))

    return True


def orchestrate_variant(plan, variant_id):
    if variant_id not in VARIANT_SCHEDULES:
        raise ValueError(f"UNKNOWN_CLASSICAL_VARIANT:{variant_id}")

    base_events = cc.realize(copy.deepcopy(plan))
    bars = {bar["bar"]: bar for bar in plan["bars"]}
    activity_plan = _activity_bar_plan(plan, variant_id, base_events)
    active_bar_sets = _activity_bar_sets(plan, base_events, variant_id)
    output = []
    original_theme_count = 0
    transferred_theme_count = 0
    pitch_class_matches = 0

    for event in base_events:
        bar_number = int(event["plan_bar"])
        bar = bars[bar_number]
        fg_instrument = _foreground_instrument(variant_id, bar)
        fg_family = FAMILY_BY_INSTRUMENT[fg_instrument]

        if _is_theme_event(event):
            original_theme_count += 1
            e = copy.deepcopy(event)
            old_pc = int(e["midi"]) % 12
            e["instrument_id"] = fg_instrument
            e["track_id"] = cc.TRACKS[fg_instrument]
            e["player_id"] = PLAYER_BY_INSTRUMENT[fg_instrument]
            e["midi"] = _retarget_note(e["midi"], fg_instrument)
            e["source_rule"] = "variant_foreground_transfer"
            e["role_state"] = "FOREGROUND"
            e["foreground_family"] = fg_family
            e["variant_id"] = variant_id
            transferred_theme_count += 1
            if int(e["midi"]) % 12 == old_pc:
                pitch_class_matches += 1
            output.append(e)
            continue

        fam = _family(event)
        if fam in active_bar_sets and fam != fg_family and bar_number not in active_bar_sets[fam]:
            continue
        if not _support_keep(variant_id, event, fg_family, bar_number, activity_plan):
            continue

        e = copy.deepcopy(event)
        e["variant_id"] = variant_id
        e["foreground_family"] = fg_family
        if fam == "STRINGS" and fg_family != "STRINGS":
            e["role_state"] = "HARMONIC_SUPPORT" if "DOUBLE_BASS" not in e.get("player_id", "") else "FOUNDATION"
        elif fam == fg_family:
            e["role_state"] = "COUNTERLINE"
        elif fam == "PERCUSSION":
            e["role_state"] = "TEXTURAL_SUPPORT"
        elif fam == "BRASS":
            e["role_state"] = "HARMONIC_SUPPORT"
        else:
            e["role_state"] = "TEXTURAL_SUPPORT"
        output.append(e)

    if original_theme_count != transferred_theme_count:
        raise AssertionError("THEME_EVENT_COUNT_CHANGED")
    if pitch_class_matches != transferred_theme_count:
        raise AssertionError("THEME_PITCH_CLASS_CHANGED")

    return sorted(output, key=lambda e: (e["start_beat"], e["track_id"], e.get("player_id", ""), e["midi"]))


def summarize_variant(plan, variant_id, events):
    bar_fg = {}
    active_by_bar = defaultdict(set)
    event_count_by_bar_family = defaultdict(Counter)

    for event in events:
        bar = int(event["plan_bar"])
        fam = _family(event)
        if event.get("role_state") == "FOREGROUND":
            bar_fg[bar] = event["foreground_family"]
        if fam != "OTHER":
            active_by_bar[bar].add(fam)
            event_count_by_bar_family[bar][fam] += 1

    total_bars = len(plan["bars"])
    fg_counts = Counter(bar_fg.values())
    activity_counts = Counter()
    for families in active_by_bar.values():
        for fam in families:
            activity_counts[fam] += 1

    def pct(count):
        return round(100.0 * count / total_bars, 2) if total_bars else 0.0

    foreground_bar_percent = {k: pct(v) for k, v in sorted(fg_counts.items())}
    active_bar_percent = {k: pct(v) for k, v in sorted(activity_counts.items())}

    non_string_fg_bars = [b for b, fam in bar_fg.items() if fam != "STRINGS"]
    string_density_non_string_fg = 0.0
    if non_string_fg_bars:
        string_density_non_string_fg = round(
            sum(event_count_by_bar_family[b]["STRINGS"] for b in non_string_fg_bars)
            / len(non_string_fg_bars),
            3,
        )

    return {
        "schema": SCHEMA_ID,
        "variant_id": variant_id,
        "plan_sha256": cc.digest(plan),
        "seed": plan["seed"],
        "bars": total_bars,
        "event_count": len(events),
        "foreground_bar_percent": foreground_bar_percent,
        "active_bar_percent": active_bar_percent,
        "brass_foreground_bars": fg_counts.get("BRASS", 0),
        "woodwind_foreground_bars": fg_counts.get("WOODWINDS", 0),
        "string_foreground_bars": fg_counts.get("STRINGS", 0),
        "avg_string_events_per_non_string_foreground_bar": string_density_non_string_fg,
        "gain_fields_present": any("gain" in str(k).lower() for e in events for k in e.keys()),
        "role_states": dict(sorted(Counter(e.get("role_state", "UNSET") for e in events).items())),
        "activity_target_percent": ACTIVITY_TARGETS[variant_id],
    }


def build_validation(seed=0, mode="quick"):
    plan = cc.make_plan(seed=seed, mode=mode)
    result = {
        "schema": SCHEMA_ID,
        "research_only": True,
        "live_runtime_modified": False,
        "plan_sha256": cc.digest(plan),
        "seed": seed,
        "mode": mode,
        "variants": {},
    }
    for variant_id in VARIANT_SCHEDULES:
        events = orchestrate_variant(plan, variant_id)
        result["variants"][variant_id] = summarize_variant(plan, variant_id, events)

    a = result["variants"]["CLASSICAL_PERIOD_BASELINE"]
    b = result["variants"]["LATE_ROMANTIC_EXPANDED"]
    if a["plan_sha256"] != b["plan_sha256"]:
        raise AssertionError("VARIANTS_DO_NOT_SHARE_PLAN")
    if a["brass_foreground_bars"] != 0:
        raise AssertionError("CLASSICAL_BASELINE_UNEXPECTED_BRASS_FOREGROUND")
    if b["brass_foreground_bars"] <= 0:
        raise AssertionError("LATE_ROMANTIC_REQUIRES_BRASS_FOREGROUND")
    if a["gain_fields_present"] or b["gain_fields_present"]:
        raise AssertionError("ORCHESTRATION_HARNESS_MUST_NOT_USE_GAIN")
    return result


def main():
    result = build_validation()
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
