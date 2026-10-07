"""Deterministic full-length musical development layer for AI Composition.

This module does not generate sound and does not replace the composition engine.
It gives normal-length pieces harmonic/arrangement development so the 3:30 target
is not filled by a tiny repeated cell.
"""
from __future__ import annotations

from typing import Any


def build_developed_progression(quality: str, bars: int, seedv: int) -> list[str]:
    """Return a bar-length progression that develops every phrase, not every section."""
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
    total = max(0, int(bars))
    for bar in range(total):
        phrase = bar // 4
        section = bar // 16
        phrase_in_section = phrase % 4

        # The previous version selected one four-bar pattern for almost an
        # entire 16-bar section. Move through a different approved pattern
        # on each four-bar phrase so the piece actually travels.
        pattern_index = (
            phase
            + (seedv % 3)
            + section * 2
            + phrase_in_section
            + (section // 2)
        ) % len(variants)
        pattern = variants[pattern_index]
        chord = pattern[bar % 4]

        # Eight-bar cadences give phrases punctuation without resetting the
        # whole section to the same four-chord cell.
        if bar % 8 == 7 and bar != total - 1:
            chord = dominant
        if bar % 16 == 15:
            chord = tonic if section % 2 else dominant

        # Later sections can deliberately recall the opening, but only for
        # one phrase rather than repeating the whole opening block.
        if section % 4 == 3 and phrase_in_section == 0:
            chord = variants[phase][bar % 4]

        if bar == total - 1:
            chord = tonic
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

    # A guitar chord is not a keyboard block. For Rock, stagger the individual
    # sampled-guitar notes by a few milliseconds in alternating pick direction.
    # This changes performance timing only; it does not invent notes or timbre.
    working_events = [dict(event) for event in events]
    if tmpl == "rock":
        chord_groups: dict[float, list[dict[str, Any]]] = {}
        for event in working_events:
            if str(event.get("track_id", "")).upper() != "HARMONY":
                continue
            if "guitar" not in str(event.get("instrument_id", "")).lower():
                continue
            chord_groups.setdefault(round(float(event.get("start_beat", 0.0)), 6), []).append(event)
        for start_key, chord in chord_groups.items():
            if len(chord) < 2:
                continue
            bar = int(start_key // max(meter, 1e-9))
            reverse = ((bar + creation_seed) % 2) == 1
            ordered = sorted(chord, key=lambda event: int(event.get("midi", 0)), reverse=reverse)
            strum_step = 0.032
            for index, event in enumerate(ordered):
                original_duration = float(event.get("duration_beats", 0.1))
                event["start_beat"] = float(start_key) + index * strum_step
                event["duration_beats"] = max(0.08, original_duration - index * strum_step)
                if "velocity" in event:
                    event["velocity"] = _clamp_velocity(float(event["velocity"]) + (2 - index))

    developed: list[dict[str, Any]] = []
    for source in working_events:
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

        # Rock needs audible song-scale development, not a four-bar cell with
        # tiny velocity changes. Keep the same generated notes/resources but
        # reshape timing, density, and phrase roles across each 16-bar section.
        if tmpl == "rock":
            phrase_in_section = (bar % 16) // 4
            section_role = section % 6
            gain *= (0.82, 0.96, 1.08, 0.90, 1.12, 0.76)[section_role]

            if is_bass:
                e["duration_beats"] = max(float(e.get("duration_beats", 0.1)), min(1.55, max(0.5, meter / 2 - 0.25)))
                gain *= 1.06
            if is_harmony and "guitar" in instrument:
                e["duration_beats"] = max(float(e.get("duration_beats", 0.1)), 0.88)

            # First phrase behaves like an intro: establish groove before lead.
            if bar < 4:
                if is_lead:
                    continue
                if is_kick and local >= meter / 2:
                    continue
                if is_hat and int(round(local * 2)) % 2:
                    continue

            # Make each four-bar phrase use a genuinely different rhythmic
            # accompaniment shape.
            if is_harmony:
                if phrase_in_section == 1 and local >= meter / 2:
                    e["start_beat"] = bar * meter + min(meter - 0.08, local + 0.25)
                elif phrase_in_section == 2:
                    if local >= meter / 2 and bar % 2 == 0:
                        continue
                    if local < meter / 2:
                        e["duration_beats"] = min(1.35, max(0.08, meter / 2 - 0.08))
                elif phrase_in_section == 3 and local >= meter / 2:
                    e["start_beat"] = bar * meter + min(meter - 0.08, local + 0.50)

            if is_bass and local >= meter / 2:
                if phrase_in_section == 1:
                    e["start_beat"] = bar * meter + min(meter - 0.08, local + 0.25)
                elif phrase_in_section == 3:
                    e["start_beat"] = bar * meter + max(0.0, local - 0.25)

            if is_kick and local >= meter / 2:
                if phrase_in_section == 1:
                    e["start_beat"] = bar * meter + min(meter - 0.08, local + 0.50)
                elif phrase_in_section == 2 and bar % 2 == 0:
                    continue
                elif phrase_in_section == 3:
                    e["start_beat"] = bar * meter + min(meter - 0.08, local + 0.75)

            if is_hat:
                eighth_slot = int(round(local * 2))
                if phrase_in_section == 0 and section % 2 == 0 and eighth_slot % 2:
                    continue
                if phrase_in_section == 2 and bar % 2 == 1 and eighth_slot in (1, 5):
                    continue

            # Leave real spaces in verse-like phrases and bring the lead back
            # for the lift, instead of playing the same short figure forever.
            if is_lead:
                if phrase_in_section == 0 and section % 2 == 0:
                    continue
                if phrase_in_section == 2 and bar % 4 == 1:
                    continue

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
            variant = (phrase + section + creation_seed) % 4
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
