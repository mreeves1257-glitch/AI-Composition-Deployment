"""Opt-in Rock BASS performance release policy (2026-10-08 research).

Works on the *already authored* genre events, before original MIDI and SFZ
routing. Exactly one approved genre (ROCK), one track (BASS), and approved
recorded bass identities. NEVER adds events or changes source samples, tempo,
MIDI pitches, starts, velocities, other instruments, or the downstream 3D mix.

The observed real-sample A/B showed over-early note-offs. This research
candidate is disabled unless AI_COMP_ROCK_BASS_SUSTAIN_V1=1.

The env switch is deliberately separate from all existing controls. Enable
only for isolated validation; original behavior is restored by leaving it unset.
"""
from __future__ import annotations

from collections import defaultdict
from fractions import Fraction
import math
import os
from typing import Any

POLICY_ID = "ROCK_BASS_SUSTAIN_V1_RESEARCH_DISABLED_DEFAULT"
SWITCH = "AI_COMP_ROCK_BASS_SUSTAIN_V1"
BASS_IDENTITIES = frozenset(("electric_bass_guitar", "electric_bass"))
EXPLICIT_SHORT = ("mute", "staccato", "chop", "short", "pizz", "stop", "ghost", "dead")
MIN_NEXT_ATTACK_BEATS = 0.80
MAX_NEXT_ATTACK_BEATS = 2.50
FRACTION_OF_SPACING = 0.78
MAX_SUSTAIN_BEATS = 1.50
MIN_EXTENSION_BEATS = 0.14


def _beat(value: Any) -> float:
    if isinstance(value, bool):
        raise ValueError("BOOL_IS_NOT_A_BEAT")
    out = float(Fraction(str(value)))
    if not math.isfinite(out):
        raise ValueError("NONFINITE_BEAT")
    return out


def is_enabled() -> bool:
    """Strict feature gate: only literal 1 opts in, never by accident."""
    return os.environ.get(SWITCH, "") == "1"


def adapt_rock_bass(events: list[dict[str, Any]], genre: str, *, enabled: bool | None = None) -> list[dict[str, Any]]:
    """Produce a note-off-only copy of source music; no in-place mutations.

    Does not guess musical sustain where next phrase has a large silence.
    Gaps of at least 22% are retained, and limits apply before changing notes.
    At repeated same-time notes, base the decision on the next DISTINCT onset.
    If no distinct next attack exists, the last note remains unchanged.
    """
    if enabled is None:
        enabled = is_enabled()
    if enabled is not True or str(genre).upper() != "ROCK":
        return [dict(e) for e in events]
    out = [dict(e) for e in events]
    by_track: dict[str, list[int]] = defaultdict(list)
    for idx, event in enumerate(out):
        if (str(event.get("track_id","")).upper() == "BASS"
                and str(event.get("instrument_id","")).lower() in BASS_IDENTITIES):
            by_track[str(event["track_id"]).upper()].append(idx)
    for idxs in by_track.values():
        idxs.sort(key=lambda idx: (_beat(out[idx]["start_beat"]), int(out[idx].get("midi", 0))))
        onsets = sorted({_beat(out[idx]["start_beat"]) for idx in idxs})
        next_for_start = {a:b for a,b in zip(onsets,onsets[1:])}
        for idx in idxs:
            event = out[idx]
            start = _beat(event["start_beat"])
            nxt = next_for_start.get(start)
            if nxt is None:
                continue
            spacing = nxt - start
            if not MIN_NEXT_ATTACK_BEATS <= spacing <= MAX_NEXT_ATTACK_BEATS:
                continue
            name = str(event.get("articulation","")).lower()
            if any(tag in name for tag in EXPLICIT_SHORT):
                continue
            original = _beat(event["duration_beats"])
            if original <= 0:
                continue
            desired = min(MAX_SUSTAIN_BEATS, spacing * FRACTION_OF_SPACING)
            if desired - original < MIN_EXTENSION_BEATS:
                continue
            # Never shorten the existing note, extend past next attack, or
            # remove the natural gap designed into the original phrase.
            if desired <= original or desired >= spacing:
                continue
            event["duration_beats"] = round(desired, 6)
    return out
