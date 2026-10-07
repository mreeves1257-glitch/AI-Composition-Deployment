"""Deterministic full-length musical development layer for AI Composition.

This module does not generate sound and does not replace the composition engine.
It gives normal-length pieces harmonic/arrangement development so the 3:30 target
is not filled by a tiny repeated cell.
"""
from __future__ import annotations

from typing import Any


def build_developed_progression(quality: str, bars: int, seedv: int) -> list[str]:
    """Return a bar-length diatonic progression with phrase and section variation."""
    is_major = quality in ("major", "ionian")
    if is_major:
        variants = [
            ("I", "vi", "IV", "V"),
            ("I", "V", "vi", "IV"),
            ("vi", "IV", "I", "V"),
            ("IV", "I", "V", "vi"),
            ("I", "IV", "vi", "V"),
            ("vi", "V", "IV", "V"),
        ]
        tonic, dominant = "I", "V"
    else:
        variants = [
            ("i", "VI", "III", "VII"),
            ("i", "VII", "VI", "VII"),
            ("VI", "III", "VII", "i"),
            ("III", "VII", "i", "VI"),
            ("i", "VI", "VII", "i"),
            ("VI", "VII", "i", "VII"),
        ]
        tonic, dominant = "i", "VII"

    out: list[str] = []
    phase = (seedv // 19) % len(variants)
    for bar in range(max(0, int(bars))):
        phrase = bar // 4
        section = bar // 16
        pattern = variants[(phase + section * 2 + phase // 3 + seedv + phrase // 8) % len(variants)]
        chord = pattern[bar % 4]
        if bar % 8 == 7:
            chord = dominant
        if bar > 0 and bar % 16 == 0:
            chord = tonic
        if section % 4 == 3 and (bar % 16) < 4:
            opening = variants[phase]
            chord = opening[bar % 4]
        out.append(chord)
    return out


def _clamp_velocity(value: float) -> int:
    return max(1, min(127, int(round(value))))


def _bar_of(event: dict[str, Any], meter: float) -> int:
    return max(0, int(float(event.get("start_beat", 0.0)) // max(meter, 1e-9)))


def develop_full_length(
    events: list[dict[str, Any]],
    ctx: dict[str, Any],
    tmpl: str,
    creation_seed: int = 0,
) -> list[dict[str, Any]]:
    """Shape a valid event list across the complete normal-length form."""
    if not events:
        return events

    meter = float(ctx["meter"]["numerator"]) * 4.0 / float(ctx["meter"]["denominator"])
    total_beats = max(
        float(e.get("start_beat", 0.0)) + float(e.get("duration_beats", 0.0))
        for e in events
    )
    total_bars = max(1, int((total_beats + meter - 1e-9) // meter))

    developed: list[dict[str, Any]] = []
    for source in events:
        e = dict(source)
        bar = _bar_of(e, meter)
        local = float(e.get("start_beat", 0.0)) - bar * meter
        phrase = bar // 4
        section = bar // 16
        section_bar = bar % 16
        track = str(e.get("track_id", "")).upper()
        instrument = str(e.get("instrument_id", "")).lower()

        if bar < min(8, total_bars):
            gain = 0.74 + 0.03 * bar
        elif bar >= max(0, total_bars - 8):
            remaining = max(0, total_bars - 1 - bar)
            gain = 0.70 + 0.035 * remaining
        else:
            contour = (section + creation_seed) % 4
            gain = (0.90, 1.00, 0.83, 1.07)[contour]

        breakdown = total_bars >= 32 and section % 4 == 2 and section_bar in (8, 9)
        transition = section_bar in (14, 15)

        is_hat = "HAT" in track or "hat" in instrument
        is_kick = "KICK" in track or e.get("drum") == "kick"
        is_snare = "SNARE" in track or e.get("drum") == "snare"
        is_lead = "LEAD" in track or any(
            token in instrument for token in ("lead", "trumpet", "trombone", "clarinet", "flute", "violin")
        )
        is_bass = "BASS" in track or "bass" in instrument
        is_harmony = "HARMONY" in track or any(
            token in instrument
            for token in ("piano", "guitar", "chord", "pad", "strings", "clav", "pulse", "arp")
        )
        is_support = track.startswith("SUPPORT_")

        if breakdown:
            if is_lead:
                continue
            if is_harmony or is_support:
                midi = int(e.get("midi", 60))
                if (midi + phrase + creation_seed) % 3:
                    continue
            if is_hat and int(round(local * 4)) % 2:
                continue
            gain *= 0.78

        if is_harmony and not breakdown:
            variant = (phrase + creation_seed) % 4
            if variant == 1 and local > 0:
                shifted = min(meter - 0.06, local + 0.125)
                e["start_beat"] = bar * meter + shifted
            elif variant == 2 and local >= meter / 2:
                midi = int(e.get("midi", 60))
                if midi % 2:
                    continue
            elif variant == 3:
                e["duration_beats"] = min(
                    float(e.get("duration_beats", 0.1)) * 1.35,
                    max(0.06, meter - local - 0.02),
                )

        if is_bass and bar % 4 == 3 and local >= meter / 2:
            note = e.get("midi")
            if isinstance(note, int):
                candidate = note + (12 if ((phrase + creation_seed) % 2 == 0) else -12)
                if 24 <= candidate <= 84:
                    e["midi"] = candidate

        if is_lead:
            note = e.get("midi")
            if isinstance(note, int):
                octave_shift = (0, 12, 0, -12)[(section + creation_seed) % 4]
                candidate = note + octave_shift
                if 48 <= candidate <= 108:
                    e["midi"] = candidate
            if total_bars >= 24 and phrase % 6 == 4 and bar % 4 == 0:
                continue

        if is_hat:
            if section % 2 == 1 and int(round(local * 4)) % 4 == 2:
                continue
            if transition:
                gain *= 1.12
        if is_kick and transition and local >= meter / 2 and (bar + creation_seed) % 2:
            continue
        if is_snare and transition:
            gain *= 1.10

        if "velocity" in e:
            e["velocity"] = _clamp_velocity(float(e["velocity"]) * gain)

        start = float(e.get("start_beat", 0.0))
        if start >= total_beats:
            continue
        e["duration_beats"] = min(
            float(e.get("duration_beats", 0.1)),
            max(0.01, total_beats - start),
        )
        if e["duration_beats"] > 0:
            developed.append(e)

    developed.sort(
        key=lambda x: (
            float(x.get("start_beat", 0.0)),
            str(x.get("track_id", "")),
            int(x.get("midi", 0) or 0),
        )
    )
    return developed
