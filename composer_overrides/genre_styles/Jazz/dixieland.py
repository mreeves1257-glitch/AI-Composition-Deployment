"""Independent Dixieland genre musical profile and chord movement.

Each style owns its own chord progression, rather than a shared genre-size table.
The existing engine still supplies Theory, instrument rendering and playback.
"""
GENRE_NAME = "Dixieland"
GENRE_PROFILE_ID = "DIXIELAND_V1"
CHORD_PATTERNS = [["I","I","IV","I","V","IV","I","V"],["I","IV","I","V","I","IV","V","I"]]
ENDING_CHORD = "I"
STYLE_SECTION_BARS = 16


def chord_progression(bars: int, seedv: int) -> list[str]:
    total = max(0, int(bars))
    initial = (int(seedv) // 19) % len(CHORD_PATTERNS)
    out = [CHORD_PATTERNS[(initial + bar // STYLE_SECTION_BARS) %
                          len(CHORD_PATTERNS)][bar % 8]
           for bar in range(total)]
    if out:
        out[-1] = ENDING_CHORD
    return out


from .instrument_packages import load_package as _load_instrument_package


def instrument_links() -> dict:
    """Read this genre's links to the common Jazz instrument catalog."""
    return _load_instrument_package("dixieland")
