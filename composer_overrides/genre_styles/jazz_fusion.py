"""Independent Jazz Fusion genre musical profile and chord movement.

Each style owns its own chord progression, rather than a shared genre-size table.
The existing engine still supplies Theory, instrument rendering and playback.
"""
GENRE_NAME = "Jazz Fusion"
GENRE_PROFILE_ID = "JAZZ_FUSION_V1"
CHORD_PATTERNS = [["i","i","iv","iv","VII","VI","i","i"],["i","VI","VII","i","iv","VII","VI","i"]]
ENDING_CHORD = "i"
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
