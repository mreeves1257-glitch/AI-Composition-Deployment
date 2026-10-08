"""Independent Jazz Waltz genre musical profile and chord movement.

Each style owns its own chord progression, rather than a shared genre-size table.
The existing engine still supplies Theory, instrument rendering and playback.
"""
GENRE_NAME = "Jazz Waltz"
GENRE_PROFILE_ID = "JAZZ_WALTZ_V1"
CHORD_PATTERNS = [["ii","V","I","IV","iii","vi","ii","V"],["I","vi","ii","V","I","IV","V","I"]]
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
