"""Read-only resolver for the Composer's preserved 55 genre definitions.

Provides one stable access point for genre family reference material without
changing the existing score generator, sample bank, plug or 3D mixing engine.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
RATIOS = BASE / "genre_mix_ratios"
KIT_FILE = BASE.parent / "drum_kits" / "drum_kit_catalog.json"


@lru_cache(maxsize=1)
def _index() -> dict:
    data = json.loads((RATIOS / "index.json").read_text(encoding="utf-8"))
    if (data.get("profile_count") != 55
            or data.get("family_count") != 13
            or data.get("automatic_application_enabled") is not False):
        raise ValueError("GENRE_FAMILY_INDEX_INVALID")
    return data


@lru_cache(maxsize=13)
def _family_file(filename: str) -> dict:
    if filename not in set(_index()["genre_to_family_file"].values()):
        raise ValueError("GENRE_FAMILY_UNKNOWN_FILE")
    return json.loads((RATIOS / filename).read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _drums() -> dict:
    data = json.loads(KIT_FILE.read_text(encoding="utf-8"))
    if data.get("original_files_copied") is not False:
        raise ValueError("DRUM_SOURCE_PROTECTION_FAILED")
    return data


def all_families() -> dict[str, tuple[str, ...]]:
    return {name: tuple(members) for name, members in
            _index()["family_memberships"].items()}


def all_genres() -> tuple[str, ...]:
    return tuple(_index()["genre_to_family_file"])


def get_genre(name: str) -> dict:
    """Copy of the original musical profile plus source and kit connections."""
    if not isinstance(name, str) or name not in _index()["genre_to_family_file"]:
        raise ValueError("UNKNOWN_COMPOSER_GENRE:" + str(name))
    filename = _index()["genre_to_family_file"][name]
    family = _family_file(filename)
    profile = family["profiles"].get(name)
    if not isinstance(profile, dict) or profile.get("auto_apply") is not False:
        raise ValueError("GENRE_SOURCE_REFERENCE_INVALID:" + name)
    if not profile.get("musical_definition"):
        raise ValueError("GENRE_MUSIC_MISSING:" + name)
    return deepcopy(profile)


def get_genre_parts(name: str) -> dict:
    """Organized view of existing musical information, not generated audio.

    All sections below point to the selected genre's own original definition,
    rather than inventing progressions, MIDI notes, or sound libraries.
    """
    p = get_genre(name)
    m = p["musical_definition"]
    kit_id = p.get("selected_shared_drum_kit_id")
    kit = _drums()["kits"].get(kit_id) if kit_id else None
    return {
        "genre": name,
        "family": p["family_name"],
        "original_profile_id": m["profile_id"],
        "tempo_bpm_range": deepcopy(m["tempo_bpm_range"]),
        "meter_options": deepcopy(m["meter_options"]),
        "form": {
            "tendencies": deepcopy(m["form_tendencies"]),
            "arrangement": m["arrangement_transformation"],
        },
        "melody": {
            "phrases": m["phrase_behavior"],
            "player_interaction": m["ensemble_player_behavior"],
        },
        "harmony": m["harmony_behavior"],
        "rhythm": {
            "groove": m["groove_behavior"],
            "timing": m["timing_humanization_behavior"],
        },
        "bass": m["bass_behavior"],
        "percussion": {
            "musical_behavior": m["percussion_behavior_if_applicable"],
            "kit_reference_id": kit_id,
            "kit_status": kit.get("status") if kit else "NO_DRUM_KIT_IN_ORIGINAL_PALETTE",
            "independent_tracks": kit.get("independent_roles", []) if kit else [],
        },
        "performance": {
            "dynamics": m["dynamic_behavior"],
            "articulation": m["articulation_behavior"],
            "expression": m["continuous_performance_control"],
        },
        "instruments": deepcopy(p["individual_instrument_tracks"]),
        "sound_design": m["sound_effects_intent"],
        "mix": {
            "genre_intent": m["mix_prominence_intent"],
            "genre_ratios_reference": p["reference_instrument_track"],
            "original_ratio_kind": p["ratio_kind"],
            "ratio_entries": deepcopy(p["individual_instrument_tracks"]),
        },
        "mastering_intent": m["production_mastering_intent"],
        "source_references": deepcopy(p["runtime_musical_connections"]),
        "music_implementation_state": p["runtime_musical_connections"]["musical_implementation_state"],
        "original_sound_files_untouched": True,
        "reference_only": True,
    }
