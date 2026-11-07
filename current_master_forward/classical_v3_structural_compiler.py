"""Classical V3 structural compiler.

Research/diagnostic only. Produces form, phrase, harmonic-rhythm, cadence,
melody-density and texture requirements. It produces no MIDI, no pitches and no
audio. The purpose is to prevent the old fixed Classical pilot from reaching
rendering while the V3 contract is only partially executed.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import random

SCHEMA = "CLASSICAL_V3_STRUCTURAL_PLAN_001"

FUNCTION_CANDIDATES = {
    "TONIC": ("I", "I6", "vi"),
    "PREDOMINANT": ("ii", "ii6", "IV"),
    "APPLIED_DOMINANT": ("V/V", "viio/V"),
    "CADENTIAL_64": ("I64",),
    "DOMINANT": ("V", "V7", "viio"),
    "TONIC_ARRIVAL": ("I", "I6"),
}

QUICK_PHRASES = (
    ("A_STATEMENT", 4, "HC", "I"),
    ("A_ANSWER", 4, "PAC", "I"),
    ("B_CONTRAST", 5, "IAC", "V"),
    ("DEVELOPMENT", 4, "HC", "vi"),
    ("A_RETURN", 4, "PAC", "I"),
    ("CODA", 3, "PAC", "I"),
)

NORMAL_PHRASES = (
    ("A_STATEMENT", 4, "HC", "I"),
    ("A_ANSWER", 5, "PAC", "I"),
    ("TRANSITION", 4, "HC", "V"),
    ("B_CONTRAST", 6, "IAC", "V"),
    ("DEVELOPMENT_1", 4, "EC", "vi"),
    ("DEVELOPMENT_2", 5, "HC", "IV"),
    ("RETRANSITION", 4, "HC", "V"),
    ("A_RETURN", 5, "PAC", "I"),
    ("CLOSING", 4, "IAC", "I"),
    ("CODA", 3, "PAC", "I"),
)


def _sha(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()


def _bar_harmony(phrase_name, bar_index, phrase_length, cadence, rng):
    final = bar_index == phrase_length - 1
    prefinal = bar_index == phrase_length - 2

    if final:
        if cadence == "HC":
            functions = ("PREDOMINANT", "DOMINANT")
            durations = (2.0, 2.0)
        elif cadence in ("PAC", "IAC"):
            functions = ("PREDOMINANT", "CADENTIAL_64", "DOMINANT", "TONIC_ARRIVAL")
            durations = (1.0, 1.0, 1.0, 1.0)
        elif cadence == "EC":
            functions = ("PREDOMINANT", "DOMINANT", "TONIC")
            durations = (1.0, 1.0, 2.0)
        else:
            functions = ("PREDOMINANT", "DOMINANT", "TONIC_ARRIVAL")
            durations = (1.0, 1.0, 2.0)
    elif prefinal:
        functions = ("PREDOMINANT", "APPLIED_DOMINANT", "DOMINANT")
        durations = (1.0, 1.0, 2.0)
    elif "DEVELOPMENT" in phrase_name or "TRANSITION" in phrase_name:
        functions = ("TONIC", "PREDOMINANT", "APPLIED_DOMINANT", "DOMINANT")
        durations = (1.0, 1.0, 1.0, 1.0)
    elif bar_index == 0:
        functions = ("TONIC", "TONIC")
        durations = (2.0, 2.0)
    else:
        if rng.random() < 0.5:
            functions = ("TONIC", "PREDOMINANT", "DOMINANT")
            durations = (1.0, 1.0, 2.0)
        else:
            functions = ("TONIC", "PREDOMINANT", "DOMINANT", "TONIC")
            durations = (1.0, 1.0, 1.0, 1.0)

    events = []
    offset = 0.0
    for function, duration in zip(functions, durations):
        candidates = FUNCTION_CANDIDATES[function]
        roman = candidates[rng.randrange(len(candidates))]
        events.append({
            "offset_qb": offset,
            "duration_qb": duration,
            "function": function,
            "roman_candidate": roman,
        })
        offset += duration
    return events


def compile_plan(package, *, tempo_bpm, meter="4/4", mode="quick", seed=0, tonic_pc=0, tonal_mode="major"):
    if package.get("package_id") != "CLASSICAL_V3_VARIANT_PACKAGE_001":
        raise ValueError("CLASSICAL_V3_PACKAGE_INVALID")
    if package.get("variant_id") != "CLASSICAL_PERIOD_ORCHESTRAL":
        raise ValueError("CLASSICAL_V3_STRUCTURAL_VARIANT_UNSUPPORTED")

    constraints = package.get("profile_constraints") or {}
    tempo_range = constraints.get("tempo_bpm_range") or []
    if len(tempo_range) != 2 or not tempo_range[0] <= tempo_bpm <= tempo_range[1]:
        raise ValueError("CLASSICAL_V3_TEMPO_OUTSIDE_PROFILE")
    if meter not in (constraints.get("meter_options") or []):
        raise ValueError("CLASSICAL_V3_METER_OUTSIDE_PROFILE")
    if meter != "4/4":
        raise ValueError("CLASSICAL_V3_STRUCTURAL_COMPILER_CURRENTLY_4_4_ONLY")
    if mode not in ("quick", "normal"):
        raise ValueError("CLASSICAL_V3_MODE_INVALID")
    if not isinstance(tonic_pc, int) or not 0 <= tonic_pc <= 11:
        raise ValueError("CLASSICAL_V3_TONIC_PC_INVALID")
    if tonal_mode != "major":
        raise ValueError("CLASSICAL_V3_FIRST_NOTE_REALIZER_SUPPORTS_MAJOR_ONLY")

    phrase_specs = QUICK_PHRASES if mode == "quick" else NORMAL_PHRASES
    rng = random.Random(seed * 7919 + 31)
    phrases = []
    bars = []
    cursor = 1

    for phrase_id, length, cadence, local_region in phrase_specs:
        phrase = {
            "phrase_id": phrase_id,
            "start_bar": cursor,
            "length_bars": length,
            "cadence": cadence,
            "local_key_region": local_region,
        }
        phrases.append(phrase)
        for local_bar in range(length):
            harmonic_events = _bar_harmony(
                phrase_id, local_bar, length, cadence, rng
            )
            bars.append({
                "bar": cursor + local_bar,
                "phrase_id": phrase_id,
                "phrase_position": local_bar,
                "phrase_length": length,
                "local_key_region": local_region,
                "cadence": cadence if local_bar == length - 1 else None,
                "harmonic_events": harmonic_events,
                "melody_requirements": {
                    "foreground_required": True,
                    "reference_notes_per_quarterbeat": (
                        package["empirical_validation_reference"]["melody"][
                            "notes_per_quarterbeat"
                        ]
                    ),
                    "validation_band_notes_per_quarterbeat": [1.6, 2.7],
                    "active_small_values_required": True,
                    "phrase_breathing_required": True,
                    "step_dominant_contour_required": True,
                    "large_leap_recovery_required": True,
                },
                "texture_requirements": {
                    "simultaneous_harmonic_support_required": True,
                    "minimum_supporting_voices_at_structural_attacks": 3,
                    "foreground_voice_separate_from_support": True,
                    "single_note_stream_cannot_be_default_texture": True,
                },
            })
        cursor += length

    tempo_map = []
    for phrase in phrases:
        start = (phrase["start_bar"] - 1) * 4.0
        tempo_map.append({"start_beat": start, "bpm": float(tempo_bpm)})
        cadence_start = (phrase["start_bar"] + phrase["length_bars"] - 2) * 4.0
        factor = 0.96 if phrase["phrase_id"] != "CODA" else 0.92
        tempo_map.append({
            "start_beat": cadence_start,
            "bpm": round(float(tempo_bpm) * factor, 3),
            "reason": "phrase_cadence_breathing",
        })

    plan = {
        "schema": SCHEMA,
        "status": "PASS",
        "research_only": True,
        "audio_approved": False,
        "variant_id": package["variant_id"],
        "tempo_bpm": float(tempo_bpm),
        "meter": meter,
        "mode": mode,
        "seed": seed,
        "global_tonic_pc": tonic_pc,
        "tonal_mode": tonal_mode,
        "beats_per_bar": 4.0,
        "phrases": phrases,
        "bars": bars,
        "tempo_map": tempo_map,
        "harmony_authority": {
            "candidate": deepcopy(package["composition_grammar"]),
            "empirical_reference": deepcopy(
                package["empirical_validation_reference"]["harmony"]
            ),
            "rule": "EMPIRICAL_PERCENTAGES_VALIDATE_BEHAVIOR_NOT_LITERAL_QUOTAS",
        },
        "melody_authority": {
            "candidate": deepcopy(package["melody_behavior"]),
            "empirical_reference": deepcopy(
                package["empirical_validation_reference"]["melody"]
            ),
        },
        "role_state_authority": deepcopy(package["role_state"]),
        "execution_requirements": deepcopy(package["execution_requirements"]),
    }
    plan["plan_sha256"] = _sha(plan)
    return plan


def validate_plan(plan):
    if plan.get("schema") != SCHEMA or plan.get("status") != "PASS":
        raise ValueError("CLASSICAL_V3_STRUCTURAL_PLAN_INVALID")
    beats = float(plan["beats_per_bar"])
    bars = plan["bars"]
    phrases = plan["phrases"]
    if not bars or not phrases:
        raise ValueError("CLASSICAL_V3_STRUCTURAL_PLAN_EMPTY")

    phrase_lengths = {p["length_bars"] for p in phrases}
    if len(phrase_lengths) < 3:
        raise ValueError("CLASSICAL_V3_PHRASE_LENGTHS_TOO_UNIFORM")
    if all(p["length_bars"] == 8 for p in phrases):
        raise ValueError("CLASSICAL_V3_FIXED_EIGHT_BAR_FAILURE")

    single_event_bars = 0
    harmony_durations = []
    cadence_types = set()
    for bar in bars:
        events = bar["harmonic_events"]
        if len(events) == 1:
            single_event_bars += 1
        total = sum(float(e["duration_qb"]) for e in events)
        if abs(total - beats) > 1e-9:
            raise ValueError("CLASSICAL_V3_HARMONIC_BAR_DURATION_MISMATCH")
        harmony_durations.extend(float(e["duration_qb"]) for e in events)
        if bar.get("cadence"):
            cadence_types.add(bar["cadence"])
        tex = bar["texture_requirements"]
        if not tex["simultaneous_harmonic_support_required"]:
            raise ValueError("CLASSICAL_V3_SIMULTANEOUS_SUPPORT_MISSING")
        if tex["minimum_supporting_voices_at_structural_attacks"] < 3:
            raise ValueError("CLASSICAL_V3_SUPPORT_VOICE_COUNT_TOO_LOW")
        mel = bar["melody_requirements"]
        lo, hi = mel["validation_band_notes_per_quarterbeat"]
        ref = float(mel["reference_notes_per_quarterbeat"])
        if not lo <= ref <= hi:
            raise ValueError("CLASSICAL_V3_MELODY_DENSITY_REFERENCE_OUTSIDE_BAND")

    if single_event_bars / len(bars) > 0.10:
        raise ValueError("CLASSICAL_V3_TOO_MANY_WHOLE_BAR_HARMONIES")
    if not any(d <= 1.0 for d in harmony_durations):
        raise ValueError("CLASSICAL_V3_NO_ACTIVE_HARMONIC_RHYTHM")
    if max(harmony_durations) > 2.0:
        raise ValueError("CLASSICAL_V3_HARMONIC_EVENTS_TOO_STATIC")
    if len(cadence_types) < 3:
        raise ValueError("CLASSICAL_V3_CADENCE_PALETTE_TOO_NARROW")

    return {
        "status": "PASS",
        "bar_count": len(bars),
        "phrase_count": len(phrases),
        "phrase_lengths": sorted(phrase_lengths),
        "cadence_types": sorted(cadence_types),
        "single_event_bar_percent": round(100 * single_event_bars / len(bars), 2),
        "minimum_harmony_duration_qb": min(harmony_durations),
        "maximum_harmony_duration_qb": max(harmony_durations),
        "simultaneous_support_minimum_voices": 3,
        "foreground_melody_required_every_bar": True,
        "audio_generated": False,
    }
