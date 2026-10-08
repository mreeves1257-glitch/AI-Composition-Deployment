"""Genre-authorized instrument performance: notes -> playable gestures.

V1 enables ROCK electric-guitar timing only. The mechanism is shared, but an
untested genre is never silently assigned another genre's playing conventions.
Never invents notes, sound banks, tracks, tempos, or changes drums/bass/mixer.
"""
from __future__ import annotations
from collections import defaultdict
from fractions import Fraction
from typing import Any

CONTRACT_VERSION = "INSTRUMENT_PERFORMANCE_V1"
# Audited genre behavior. Remaining genre profiles are pending distinct tests.
GENRE_POLICIES = {
    "ROCK": {
        "electric_guitar": {
            "close_attack_beats": 0.105,
            "rapid_phrase_beats": 0.82,
            "release_gap_beats": 0.15,
            "ring_fraction": 0.84,
            "max_ringing_beats": 2.8,
        }
    }
}


def _beats(value: Any) -> float:
    """Read decimal or rational beat coordinates without changing the grid."""
    return float(Fraction(str(value)))


def _electric_guitar(event: dict[str, Any]) -> bool:
    name = str(event.get("instrument_id", "")).lower()
    return "electric_guitar" in name or name == "lead_guitar"


def perform(events: list[dict[str, Any]], genre: str) -> list[dict[str, Any]]:
    """Preserve every note and its pitch/onset; vary only justified durations.

    A strummed chord consists of near-simultaneous attacks and is treated as
    one gesture. Otherwise, the second string in a strum could falsely force
    every chord note to be staccato. Explicit muted/short playing is honored.
    No other genre changes until its instrument-specific policy is validated.
    """
    result = [dict(e) for e in events]
    rules = GENRE_POLICIES.get(str(genre).upper(), {}).get("electric_guitar")
    if rules is None:
        return result
    tracks: dict[str, list[int]] = defaultdict(list)
    for index, event in enumerate(result):
        if _electric_guitar(event):
            tracks[str(event.get("track_id", ""))].append(index)

    for track, indices in tracks.items():
        indices.sort(key=lambda i: (_beats(result[i]["start_beat"]), int(result[i].get("midi", 0))))
        gestures: list[list[int]] = []
        for index in indices:
            start = _beats(result[index]["start_beat"])
            if not gestures or start - _beats(result[gestures[-1][0]]["start_beat"]) > rules["close_attack_beats"]:
                gestures.append([index])
            else:
                gestures[-1].append(index)

        for pos, members in enumerate(gestures):
            first = _beats(result[members[0]]["start_beat"])
            next_onset = _beats(result[gestures[pos + 1][0]]["start_beat"]) if pos + 1 < len(gestures) else None
            # At the end of an instrumental phrase, honor the source duration;
            # do not invent a held note to fill a musical gap or song length.
            if next_onset is None:
                continue
            spacing = next_onset - first
            if spacing <= 0:
                continue
            for index in members:
                event = result[index]
                start = _beats(event["start_beat"])
                original = _beats(event["duration_beats"])
                technique = str(event.get("articulation", "")).lower()
                explicit_short = any(word in technique for word in ("mute", "staccato", "chop", "short", "pizz"))
                explicit_legato = "legato" in technique
                if original <= 0 or explicit_short:
                    continue
                if spacing < rules["rapid_phrase_beats"]:
                    # Faster attacks do not automatically mean staccato.
                    # Respect the source articulation, including legato.
                    if explicit_legato:
                        event["duration_beats"] = max(original, min(spacing * 0.96, next_onset - start))
                    else:
                        event["duration_beats"] = min(original, max(0.08, next_onset - start - 0.03))
                else:
                    end = first + min(rules["max_ringing_beats"], spacing * rules["ring_fraction"])
                    end = min(end, next_onset - rules["release_gap_beats"])
                    # Strum members end together, with natural staggered onset.
                    event["duration_beats"] = max(original, max(0.08, end - start))
    return result
