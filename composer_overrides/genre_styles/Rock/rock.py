"""Rock genre owner: retain the verified Rock performance, resource and mix.

The existing Rock arrangement and guitar/drum performance remain protected.
This module is the genre-level entry point for later extraction of the Rock
score rules, NOT a rewrite of working Rock or a Jazz inheritance.
"""
from __future__ import annotations
from rock_balance_contract import apply_rock_balance

GENRE_NAME = "ROCK"
GENRE_PROFILE_ID = "ROCK_V1"
STYLE_VERSION = "ROCK_PRESERVED_INITIAL_SEPARATION"


def balance_mix(engine_result: dict) -> dict:
    return apply_rock_balance(engine_result)


def normal_length_tempo_and_bars(profile: dict, result: dict,
                                 original_tempo_bpm: int) -> tuple[int, int]:
    """Exact preserved fast-Rock tempo/form calculation from original adapter."""
    approved = profile.get("tempo_bpm_range") or [original_tempo_bpm, original_tempo_bpm]
    tempo_bpm = int(approved[-1])
    numerator, denominator = map(int, str(result["meter"]).split("/"))
    beats_per_bar = float(numerator) * 4.0 / float(denominator)
    bars = max(24, min(320, round(210.0 * tempo_bpm / (60.0 * beats_per_bar))))
    return tempo_bpm, bars
