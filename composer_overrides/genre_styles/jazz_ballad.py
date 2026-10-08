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

GENRE_NAME = "Jazz Ballad"
GENRE_PROFILE_ID = "JAZZ_BALLAD_V1"
STYLE_VERSION = "JAZZ_BALLAD_INDEPENDENT_STYLE_R1"

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


def balance_mix(engine_result: dict) -> dict:
    """Give the actual recorded Jazz instruments appropriate ensemble balance."""
    return _balance(engine_result)
