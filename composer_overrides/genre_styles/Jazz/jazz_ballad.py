"""Jazz Ballad: independent, complete genre-level music policy.

Every genre may have a similarly named module. Only shared infrastructure
(Theory, instrument library, SFZ playback, external 3D mixer, plug) belongs
in the common pipeline. The Jazz-specific chord progression, arranger
pattern decisions and relative instrument balance are owned here.
Other Jazz variants and Rock are *not* aliases of Jazz Ballad.
"""
from __future__ import annotations

from jazz_arranger_style import arrange_jazz_ballad as _arrange
from jazz_balance_contract import apply_jazz_ballad_balance as _balance
from .leveling import match_jazz_ballad_presence as _level

GENRE_NAME = "Jazz Ballad"
GENRE_PROFILE_ID = "JAZZ_BALLAD_V1"
STYLE_VERSION = "JAZZ_BALLAD_INDEPENDENT_STYLE_R1"

# This instrument package is genre-owned, while recorded samples stay
# in the shared sound_resources library. Do not duplicate the WAV/SFZ files.
from .instrument_packages import load_package as _load_instrument_package

INSTRUMENT_PACKAGE = _load_instrument_package("jazz_ballad")


def instrument_links() -> dict:
    """Return separate link metadata; never duplicate recorded source files."""
    from copy import deepcopy
    return deepcopy(INSTRUMENT_PACKAGE)


def validate_instrument_links(bindings: dict) -> None:
    """Reject missing or mismatched SFZ references; preserve sample identity."""
    if not isinstance(bindings, dict):
        raise ValueError("JAZZ_INSTRUMENT_BINDINGS_NOT_AVAILABLE")
    for role, spec in INSTRUMENT_PACKAGE["instruments"].items():
        resource = bindings.get(spec["registry_binding"])
        if not isinstance(resource, dict):
            raise ValueError("JAZZ_MISSING_INSTRUMENT_LINK:" + role)
        if (resource.get("resource_id") != spec["resource_id"]
                or resource.get("preferred_mapping") != spec["sfz"]
                or resource.get("resource_type") != "SFZ_SAMPLE_LIBRARY"):
            raise ValueError("JAZZ_INSTRUMENT_LINK_MISMATCH:" + role)


# Independent eight-bar phrases. The original pair of eight-bar cells often
# repeated the tonic over multiple measures and made the track feel static.
# Each element is a chord function validated by the existing Theory layer.
SECTION_PROGRESSIONS = (
    ("I", "vi", "ii", "V", "I", "IV", "ii", "V"),
    ("IV", "iii", "vi", "V", "I", "vi", "ii", "V"),
    ("iii", "vi", "ii", "V", "IV", "I", "ii", "V"),
    ("I", "IV", "iii", "vi", "ii", "V", "IV", "V"),
)


def chord_progression(bars: int, seedv: int) -> list[str]:
    """Compose Jazz Ballad-only chord movement, respecting original seed."""
    total = max(0, int(bars))
    first = (int(seedv) // 19) % len(SECTION_PROGRESSIONS)
    progression = [
        SECTION_PROGRESSIONS[(first + bar // 8) % len(SECTION_PROGRESSIONS)][bar % 8]
        for bar in range(total)
    ]
    if progression:
        progression[-1] = "I"
    return progression


def arrange_events(events: list[dict], context: dict, creation_seed: int) -> list[dict]:
    """Coordinate bass, clarinet and brush sections without touching the piano."""
    return _arrange(events, context, creation_seed)


def balance_mix(engine_result: dict, stems: list[dict] | None = None) -> dict:
    """Balance only Jazz Ballad, based on real recorded stem intensity.

    Without stems, retain the existing static Jazz balance for safe, backwards-
    compatible contracts and offline checks. With stems, match actual active
    source levels before forwarding to the unmodified standalone 3D mixer.
    """
    baseline = _balance(engine_result)
    if stems is None or not isinstance(baseline, dict) or baseline.get("genre") != GENRE_NAME:
        return baseline
    return _level(baseline, stems)
