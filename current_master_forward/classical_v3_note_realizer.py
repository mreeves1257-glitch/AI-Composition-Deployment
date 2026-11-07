"""Classical V3 abstract note/harmony/texture realizer.

Research/diagnostic only. Consumes a validated Classical V3 structural plan and
produces an abstract four-voice note plan:
- one clearly separate foreground melody,
- three simultaneous harmonic-support voices,
- chord-aware structural melody tones,
- controlled passing/neighbor non-chord tones with step resolution.

No instrument IDs, MIDI files, soundfonts, orchestration, or audio are produced.
"""
from __future__ import annotations

from collections import defaultdict
import itertools
import math

SCHEMA = "CLASSICAL_V3_ABSTRACT_NOTE_PLAN_001"

VOICE_RANGES = {
    "SUPPORT_BASS": (36, 55),
    "SUPPORT_TENOR": (48, 67),
    "SUPPORT_ALTO": (55, 76),
    "MELODY": (67, 89),
}
INITIAL = {
    "SUPPORT_BASS": 43,
    "SUPPORT_TENOR": 55,
    "SUPPORT_ALTO": 64,
    "MELODY": 76,
}
REGION_ROOT_OFFSET = {"I": 0, "V": 7, "vi": 9, "IV": 5}
MAJOR_SCALE = (0, 2, 4, 5, 7, 9, 11)

RHYTHM_CELLS = (
    (0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5),
    (0.5, 0.5, 1.0, 0.5, 0.5, 0.5, 0.5),
    (1.0, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5),
)
CADENCE_CELL = (0.5, 1.0, 0.5, 0.5, 1.0, 0.5)
CONTOUR = (0, 2, 4, 5, 3, 1, 2, 4, 2, 0)


def _pcset(root, intervals):
    return {(root + x) % 12 for x in intervals}


def _roman_spec(label, local_root):
    if label == "I":
        root = local_root
        pcs = _pcset(root, (0, 4, 7))
        return pcs, root, {root, (root + 4) % 12}
    if label == "I6":
        root = local_root
        pcs = _pcset(root, (0, 4, 7))
        return pcs, (root + 4) % 12, {root, (root + 4) % 12}
    if label == "I64":
        root = local_root
        pcs = _pcset(root, (0, 4, 7))
        return pcs, (root + 7) % 12, {root, (root + 4) % 12}
    if label == "vi":
        root = (local_root + 9) % 12
        pcs = _pcset(root, (0, 3, 7))
        return pcs, root, {root, (root + 3) % 12}
    if label in ("ii", "ii6"):
        root = (local_root + 2) % 12
        pcs = _pcset(root, (0, 3, 7))
        bass = (root + 3) % 12 if label == "ii6" else root
        return pcs, bass, {root, (root + 3) % 12}
    if label == "IV":
        root = (local_root + 5) % 12
        pcs = _pcset(root, (0, 4, 7))
        return pcs, root, {root, (root + 4) % 12}
    if label == "V/V":
        root = (local_root + 2) % 12
        pcs = _pcset(root, (0, 4, 7))
        return pcs, root, {root, (root + 4) % 12}
    if label == "viio/V":
        root = (local_root + 6) % 12
        pcs = _pcset(root, (0, 3, 6))
        return pcs, root, set(pcs)
    if label in ("V", "V7"):
        root = (local_root + 7) % 12
        intervals = (0, 4, 7, 10) if label == "V7" else (0, 4, 7)
        pcs = _pcset(root, intervals)
        essential = {root, (root + 4) % 12}
        if label == "V7":
            essential.add((root + 10) % 12)
        return pcs, root, essential
    if label == "viio":
        root = (local_root + 11) % 12
        pcs = _pcset(root, (0, 3, 6))
        return pcs, root, set(pcs)
    raise ValueError("CLASSICAL_V3_UNSUPPORTED_ROMAN::" + label)


def _candidates(pcs, role, reference, required_pc=None):
    lo, hi = VOICE_RANGES[role]
    vals = [
        n for n in range(lo, hi + 1)
        if n % 12 in pcs and (required_pc is None or n % 12 == required_pc)
    ]
    vals.sort(key=lambda n: (abs(n - reference), n))
    return vals[:8]


def _choose_support_voicing(pcs, bass_pc, essential, previous):
    bvals = _candidates(
        pcs, "SUPPORT_BASS", previous["SUPPORT_BASS"], required_pc=bass_pc
    )
    tvals = _candidates(pcs, "SUPPORT_TENOR", previous["SUPPORT_TENOR"])
    avals = _candidates(pcs, "SUPPORT_ALTO", previous["SUPPORT_ALTO"])
    best = None
    for bass, tenor, alto in itertools.product(bvals, tvals, avals):
        if not bass < tenor < alto:
            continue
        if tenor - bass > 19 or alto - tenor > 12:
            continue
        present = {bass % 12, tenor % 12, alto % 12}
        missing = len(set(essential) - present)
        coverage = len(present)
        cost = (
            missing * 90
            + max(0, min(3, len(pcs)) - coverage) * 40
            + abs(bass - previous["SUPPORT_BASS"])
            + abs(tenor - previous["SUPPORT_TENOR"])
            + abs(alto - previous["SUPPORT_ALTO"])
        )
        for old, new in (
            (previous["SUPPORT_BASS"], bass),
            (previous["SUPPORT_TENOR"], tenor),
            (previous["SUPPORT_ALTO"], alto),
        ):
            leap = abs(new - old)
            if leap > 7:
                cost += (leap - 7) * 5
        if best is None or cost < best[0]:
            best = (cost, {
                "SUPPORT_BASS": bass,
                "SUPPORT_TENOR": tenor,
                "SUPPORT_ALTO": alto,
            })
    if best is None:
        raise ValueError("CLASSICAL_V3_NO_SUPPORT_VOICING")
    return best[1]


def _nearest_pc_set(pcs, target, role):
    lo, hi = VOICE_RANGES[role]
    values = [n for n in range(lo, hi + 1) if n % 12 in pcs]
    if not values:
        raise ValueError("CLASSICAL_V3_EMPTY_PITCH_POOL")
    return min(values, key=lambda n: (abs(n - target), n))


def _active_harmony(harmony_events, absolute_beat):
    for event in harmony_events:
        if event["start_beat"] - 1e-9 <= absolute_beat < event["end_beat"] - 1e-9:
            return event
    return harmony_events[-1]


def _melody_onsets_for_bar(bar):
    if bar.get("cadence"):
        durations = CADENCE_CELL
    else:
        durations = RHYTHM_CELLS[
            (bar["bar"] + bar["phrase_position"]) % len(RHYTHM_CELLS)
        ]
    out = []
    offset = 0.0
    for duration in durations:
        out.append((offset, duration))
        offset += duration
    if abs(offset - 4.0) > 1e-9:
        raise ValueError("CLASSICAL_V3_MELODY_CELL_NOT_4_4")
    return out


def realize(structural_plan):
    if structural_plan.get("schema") != "CLASSICAL_V3_STRUCTURAL_PLAN_001":
        raise ValueError("CLASSICAL_V3_STRUCTURE_REQUIRED")
    if structural_plan.get("tonal_mode") != "major":
        raise ValueError("CLASSICAL_V3_NOTE_REALIZER_MAJOR_ONLY")

    global_root = int(structural_plan["global_tonic_pc"])
    notes = []
    harmony_timeline = []
    previous = dict(INITIAL)

    # First realize simultaneous support for every harmonic event.
    for bar in structural_plan["bars"]:
        local_root = (
            global_root + REGION_ROOT_OFFSET[bar["local_key_region"]]
        ) % 12
        for hindex, event in enumerate(bar["harmonic_events"]):
            pcs, bass_pc, essential = _roman_spec(
                event["roman_candidate"], local_root
            )
            voicing = _choose_support_voicing(
                pcs, bass_pc, essential, previous
            )
            start = (bar["bar"] - 1) * 4.0 + float(event["offset_qb"])
            duration = float(event["duration_qb"])
            harmony_id = f"B{bar['bar']}_H{hindex}"
            record = {
                "harmony_id": harmony_id,
                "bar": bar["bar"],
                "phrase_id": bar["phrase_id"],
                "start_beat": start,
                "end_beat": start + duration,
                "duration_beats": duration,
                "local_root_pc": local_root,
                "roman": event["roman_candidate"],
                "chord_pcs": sorted(pcs),
                "cadence": bar.get("cadence"),
            }
            harmony_timeline.append(record)
            phrase_pos = bar["phrase_position"]
            phrase_len = max(2, bar["phrase_length"])
            arc = math.sin(math.pi * phrase_pos / (phrase_len - 1))
            velocity = 56 + round(8 * arc)
            for role in ("SUPPORT_BASS", "SUPPORT_TENOR", "SUPPORT_ALTO"):
                notes.append({
                    "role": role,
                    "midi": voicing[role],
                    "start_beat": start,
                    "duration_beats": max(0.12, duration * 0.985),
                    "velocity": velocity - (2 if role == "SUPPORT_TENOR" else 0),
                    "articulation": "legato",
                    "harmony_id": harmony_id,
                    "chord_pcs": sorted(pcs),
                    "structural": True,
                    "cadence": bool(bar.get("cadence")),
                })
                previous[role] = voicing[role]

    harmony_timeline.sort(key=lambda x: x["start_beat"])

    # Prebuild melody onset records so non-chord tones are only introduced when
    # the next note remains under the same harmony and can resolve by step.
    onset_records = []
    for bar in structural_plan["bars"]:
        for idx, (offset, duration) in enumerate(_melody_onsets_for_bar(bar)):
            absolute = (bar["bar"] - 1) * 4.0 + offset
            harmony = _active_harmony(harmony_timeline, absolute)
            onset_records.append({
                "bar_data": bar,
                "index_in_bar": idx,
                "offset": offset,
                "duration": duration,
                "absolute": absolute,
                "harmony": harmony,
            })

    pending = None
    previous_melody = INITIAL["MELODY"]
    for index, onset in enumerate(onset_records):
        bar = onset["bar_data"]
        harmony = onset["harmony"]
        pcs = set(harmony["chord_pcs"])
        local_root = int(harmony["local_root_pc"])
        scale_pcs = {(local_root + x) % 12 for x in MAJOR_SCALE}
        absolute = float(onset["absolute"])
        offset = float(onset["offset"])
        at_harmony_boundary = abs(absolute - harmony["start_beat"]) < 1e-9
        structural = at_harmony_boundary or abs(offset - round(offset)) < 1e-9
        last_in_phrase = (
            bool(bar.get("cadence"))
            and onset["index_in_bar"] == len(_melody_onsets_for_bar(bar)) - 1
        )

        if last_in_phrase:
            cadence = bar["cadence"]
            target_pc = (
                local_root
                if cadence in ("PAC", "IAC", "EC")
                else (local_root + 7) % 12
            )
            note = _nearest_pc_set({target_pc}, previous_melody, "MELODY")
            pending = None
            structural = True
        elif pending is not None and pending % 12 in pcs:
            note = pending
            pending = None
        else:
            pending = None
            contour_target = 76 + CONTOUR[
                (bar["bar"] * 3 + onset["index_in_bar"]) % len(CONTOUR)
            ] - 2
            reference = round(previous_melody * 0.72 + contour_target * 0.28)

            next_same_harmony = False
            next_is_forced_cadence = False
            if index + 1 < len(onset_records):
                next_onset = onset_records[index + 1]
                next_same_harmony = (
                    next_onset["harmony"]["harmony_id"]
                    == harmony["harmony_id"]
                )
                next_bar = next_onset["bar_data"]
                next_is_forced_cadence = (
                    bool(next_bar.get("cadence"))
                    and next_onset["index_in_bar"]
                    == len(_melody_onsets_for_bar(next_bar)) - 1
                )

            # A decorative non-chord tone is legal only when the *next* event is
            # free to execute the precomputed step resolution. Do not place one
            # immediately before a forced cadence target, where the cadence rule
            # would override that resolution.
            if not structural and next_same_harmony and not next_is_forced_cadence:
                direction = 1 if ((bar["bar"] + onset["index_in_bar"]) % 2 == 0) else -1
                neighbor = [
                    previous_melody + step
                    for step in ((1, 2) if direction > 0 else (-1, -2))
                    if VOICE_RANGES["MELODY"][0]
                    <= previous_melody + step
                    <= VOICE_RANGES["MELODY"][1]
                    and (previous_melody + step) % 12 in scale_pcs
                    and (previous_melody + step) % 12 not in pcs
                ]
                if neighbor:
                    candidate = neighbor[0]
                    resolutions = [
                        n for n in range(
                            VOICE_RANGES["MELODY"][0],
                            VOICE_RANGES["MELODY"][1] + 1,
                        )
                        if n % 12 in pcs and 1 <= abs(n - candidate) <= 2
                    ]
                    if resolutions:
                        note = candidate
                        pending = min(
                            resolutions,
                            key=lambda n: (abs(n - reference), n),
                        )
                    else:
                        note = _nearest_pc_set(pcs, reference, "MELODY")
                else:
                    note = _nearest_pc_set(pcs, reference, "MELODY")
            else:
                note = _nearest_pc_set(pcs, reference, "MELODY")

        phrase_pos = bar["phrase_position"]
        phrase_len = max(2, bar["phrase_length"])
        arc = math.sin(math.pi * phrase_pos / (phrase_len - 1))
        velocity = 82 + round(11 * arc)
        duration = float(onset["duration"]) * (0.96 if last_in_phrase else 0.90)
        notes.append({
            "role": "MELODY",
            "midi": int(note),
            "start_beat": absolute,
            "duration_beats": max(0.12, duration),
            "velocity": velocity,
            "articulation": "tenuto" if last_in_phrase else "legato",
            "harmony_id": harmony["harmony_id"],
            "chord_pcs": sorted(pcs),
            "structural": structural,
            "cadence": last_in_phrase,
            "phrase_id": bar["phrase_id"],
            "bar": bar["bar"],
        })
        previous_melody = int(note)

    notes.sort(key=lambda n: (
        n["start_beat"],
        1 if n["role"] == "MELODY" else 0,
        n["midi"],
    ))
    return {
        "schema": SCHEMA,
        "status": "PASS",
        "research_only": True,
        "audio_approved": False,
        "instrumentation_bound": False,
        "structural_plan_sha256": structural_plan["plan_sha256"],
        "harmony_timeline": harmony_timeline,
        "notes": notes,
    }


def validate(note_plan, structural_plan):
    if note_plan.get("schema") != SCHEMA or note_plan.get("status") != "PASS":
        raise ValueError("CLASSICAL_V3_NOTE_PLAN_INVALID")

    notes = note_plan["notes"]
    melody = [n for n in notes if n["role"] == "MELODY"]
    support = [n for n in notes if n["role"] != "MELODY"]
    harmony = note_plan["harmony_timeline"]
    if not melody or not support:
        raise ValueError("CLASSICAL_V3_NOTE_PLAN_EMPTY_LAYER")

    by_harmony = defaultdict(list)
    for n in support:
        by_harmony[n["harmony_id"]].append(n)

    support_attack_pass = 0
    for h in harmony:
        group = by_harmony[h["harmony_id"]]
        starts = [n for n in group if abs(n["start_beat"] - h["start_beat"]) < 1e-9]
        if len(starts) >= 3 and all(n["midi"] % 12 in h["chord_pcs"] for n in starts):
            support_attack_pass += 1

    structural_melody = [n for n in melody if n["structural"]]
    structural_chord = sum(
        n["midi"] % 12 in n["chord_pcs"] for n in structural_melody
    )

    cadence_notes = [n for n in melody if n["cadence"]]
    cadence_correct = 0
    phrase_map = {p["phrase_id"]: p for p in structural_plan["phrases"]}
    harmony_by_id = {h["harmony_id"]: h for h in harmony}
    for n in cadence_notes:
        phrase = phrase_map[n["phrase_id"]]
        h = harmony_by_id[n["harmony_id"]]
        local_root = h["local_root_pc"]
        target_pc = (
            local_root
            if phrase["cadence"] in ("PAC", "IAC", "EC")
            else (local_root + 7) % 12
        )
        if n["midi"] % 12 == target_pc:
            cadence_correct += 1

    nonchord = [
        (i, n) for i, n in enumerate(melody[:-1])
        if n["midi"] % 12 not in n["chord_pcs"]
    ]
    resolved = 0
    for i, n in nonchord:
        nxt = melody[i + 1]
        if (
            1 <= abs(nxt["midi"] - n["midi"]) <= 2
            and nxt["midi"] % 12 in nxt["chord_pcs"]
        ):
            resolved += 1

    overlap = 0
    for m in melody:
        active = [
            s for s in support
            if s["start_beat"] - 1e-9 <= m["start_beat"]
            < s["start_beat"] + s["duration_beats"] - 1e-9
        ]
        if len(active) >= 3:
            overlap += 1

    intervals = [
        abs(melody[i]["midi"] - melody[i - 1]["midi"])
        for i in range(1, len(melody))
    ]
    step_pct = 100 * sum(1 <= x <= 2 for x in intervals) / max(1, len(intervals))
    total_qb = len(structural_plan["bars"]) * structural_plan["beats_per_bar"]
    density = len(melody) / total_qb
    durations = [round(float(n["duration_beats"]), 3) for n in melody]
    onset_gaps = [
        round(melody[i]["start_beat"] - melody[i - 1]["start_beat"], 3)
        for i in range(1, len(melody))
    ]

    summary = {
        "status": "PASS",
        "support_harmony_attack_pass_pct": round(
            100 * support_attack_pass / max(1, len(harmony)), 2
        ),
        "structural_melody_chord_tone_pct": round(
            100 * structural_chord / max(1, len(structural_melody)), 2
        ),
        "cadence_target_pct": round(
            100 * cadence_correct / max(1, len(cadence_notes)), 2
        ),
        "nonchord_step_resolution_pct": round(
            100 * resolved / max(1, len(nonchord)), 2
        ),
        "melody_with_three_voice_support_overlap_pct": round(
            100 * overlap / len(melody), 2
        ),
        "melody_notes_per_quarterbeat": round(density, 3),
        "melody_step_motion_pct": round(step_pct, 2),
        "melody_max_duration_qb": max(durations),
        "melody_distinct_duration_count": len(set(durations)),
        "melody_distinct_onset_gap_count": len(set(onset_gaps)),
        "melody_note_count": len(melody),
        "support_note_count": len(support),
        "audio_generated": False,
        "instrumentation_bound": False,
    }

    if summary["support_harmony_attack_pass_pct"] != 100:
        raise ValueError("CLASSICAL_V3_SUPPORT_HARMONY_FAIL")
    if summary["structural_melody_chord_tone_pct"] != 100:
        raise ValueError("CLASSICAL_V3_STRUCTURAL_MELODY_HARMONY_FAIL")
    if summary["cadence_target_pct"] != 100:
        raise ValueError("CLASSICAL_V3_CADENCE_MELODY_FAIL")
    if nonchord and summary["nonchord_step_resolution_pct"] != 100:
        raise ValueError("CLASSICAL_V3_NONCHORD_RESOLUTION_FAIL")
    if summary["melody_with_three_voice_support_overlap_pct"] != 100:
        raise ValueError("CLASSICAL_V3_SINGLE_NOTE_TEXTURE_FAIL")
    if not 1.6 <= summary["melody_notes_per_quarterbeat"] <= 2.7:
        raise ValueError("CLASSICAL_V3_MELODY_DENSITY_FAIL")
    if summary["melody_step_motion_pct"] < 35:
        raise ValueError("CLASSICAL_V3_MELODY_TOO_LEAPY")
    if summary["melody_max_duration_qb"] > 1.0:
        raise ValueError("CLASSICAL_V3_MELODY_TOO_STATIC")
    if summary["melody_distinct_duration_count"] < 2:
        raise ValueError("CLASSICAL_V3_MELODY_DURATION_TOO_EVEN")
    if summary["melody_distinct_onset_gap_count"] < 2:
        raise ValueError("CLASSICAL_V3_MELODY_ONSETS_TOO_EVEN")

    return summary
