"""Shared *Jazz-family* harmonic realization, not a cross-genre style definition.

Each Jazz genre's profile, progression, and style identity belongs exclusively
to its own module. This shared helper handles common seventh/sixth realization
and chord-group dynamics; it contains no private patterns for any genre.
"""
from __future__ import annotations
from typing import Any
from ..registry import JAZZ_GENRE_PROFILES, get_style


def is_jazz_profile(genre_name: str, profile: dict[str, Any]) -> bool:
    return genre_name in JAZZ_GENRE_PROFILES and get_style(genre_name, profile) is not None


def build_jazz_progression(genre_name: str, profile: dict[str, Any],
                           quality: str, bars: int, seedv: int) -> list[str] | None:
    """Dispatch to the exact genre's independently owned progression."""
    if genre_name not in JAZZ_GENRE_PROFILES:
        return None
    style = get_style(genre_name, profile)
    if style is None:
        return None
    major = quality in ("major", "ionian")
    minor = quality in ("natural_minor", "aeolian", "minor")
    if (genre_name == "Jazz Fusion" and not minor) or (genre_name != "Jazz Fusion" and not major):
        raise ValueError("JAZZ_HARMONY_MODE_REQUIRES_REVIEW")
    return style.chord_progression(bars, seedv)


def realize_jazz_voicings(ctx: dict[str, Any], genre_name: str,
                           profile: dict[str, Any]) -> dict[str, Any]:
    """Extend Theory-validated Jazz harmony with sevenths and early-jazz sixths.

    Instrument samples, articulation DSP, routing and the standalone mixer
    remain unchanged. Return independent composition data, not mutated input.
    """
    if not is_jazz_profile(genre_name, profile):
        return ctx
    from copy import deepcopy
    built = deepcopy(ctx)
    key = built.get("key", {})
    mode = key.get("mode")
    major = mode in ("major", "ionian")
    minor = mode in ("natural_minor", "aeolian")
    if (genre_name == "Jazz Fusion" and not minor) or (genre_name != "Jazz Fusion" and not major):
        raise ValueError("JAZZ_HARMONY_MODE_REQUIRES_REVIEW")
    scale = key.get("scale", [])
    pcs = key.get("scale_pitch_classes", [])
    if len(scale) != 7 or len(pcs) != 7:
        raise ValueError("JAZZ_HARMONY_SCALE_INVALID")
    degrees = (
        {"I": 0, "ii": 1, "iii": 2, "IV": 3, "V": 4, "vi": 5, "vii°": 6}
        if major else
        {"i": 0, "ii°": 1, "III": 2, "iv": 3, "v": 4, "VI": 5, "VII": 6}
    )
    chords = built.get("harmony", {}).get("chords", [])
    for chord in chords:
        roman = chord.get("roman")
        if roman not in degrees:
            raise ValueError("JAZZ_HARMONY_DEGREE_UNSUPPORTED:" + str(roman))
        i = degrees[roman]
        early_jazz_sixth = genre_name == "Dixieland" and roman in ("I", "IV")
        indices = [i, (i + 2) % 7, (i + 4) % 7,
                   (i + (5 if early_jazz_sixth else 6)) % 7]
        notes = [scale[j] for j in indices]
        chord_pcs = [pcs[j] for j in indices]
        if chord.get("root") != notes[0]:
            raise ValueError("JAZZ_HARMONY_ROOT_MISMATCH")
        intervals = tuple((n - chord_pcs[0]) % 12 for n in chord_pcs[1:])
        quality = {
            (4, 7, 11): "major7",
            (4, 7, 10): "dominant7",
            (3, 7, 10): "minor7",
            (3, 7, 11): "minor_major7",
            (3, 6, 10): "half_diminished7",
            (3, 6, 9): "diminished7",
            (4, 8, 11): "augmented_major7",
            (4, 8, 10): "augmented7",
        }
        chord["notes"] = notes
        chord["pitch_classes"] = chord_pcs
        chord["quality"] = (
            "diatonic_sixth" if early_jazz_sixth else
            quality.get(intervals, "diatonic_seventh")
        )
    for bar, constraint in enumerate(built.get("melody_constraints_by_bar", [])):
        if bar < len(chords):
            constraint.get("constraints", {})["strong_beat_preference"] = list(
                chords[bar]["pitch_classes"]
            )
    built["harmony"]["voicing_model"] = "JAZZ_EXTENDED_HARMONY_V1"
    built["harmony"]["voicing_status"] = "EXTENDED_CHORDS_EXECUTABLE_NOT_AUDIO_VERIFIED"
    return built


def apply_jazz_phrase_expression(events: list[dict[str, Any]],
                                 genre_name: str, profile: dict[str, Any],
                                 meter: float, creation_seed: int = 0
                                 ) -> list[dict[str, Any]]:
    """Shape Jazz chord phrase dynamics while keeping all voices together.

    Do not randomize timing, modify bass/drums, or implement instrument DSP.
    Dixieland currently has no dedicated chord-playing track; do not invent one.
    """
    if not is_jazz_profile(genre_name, profile):
        return events
    shaped = [dict(event) for event in events]
    arc = (0.96, 0.98, 1.01, 1.03, 1.05, 1.04, 1.00, 0.95)
    for event in shaped:
        if str(event.get("track_id", "")).upper() != "HARMONY":
            continue
        if not isinstance(event.get("velocity"), (int, float)):
            continue
        bar = int(float(event.get("start_beat", 0.0)) // max(float(meter), 1e-9))
        section = (bar // 16 + int(creation_seed)) % 3
        factor = arc[bar % 8] * (0.98, 1.00, 1.02)[section]
        event["velocity"] = max(1, min(127, int(round(event["velocity"] * factor))))
    return shaped
