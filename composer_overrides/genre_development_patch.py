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


def build_profile_progression(genre_name: str, profile: dict[str, Any],
                              quality: str, bars: int, seedv: int,
                              fallback) -> list[str]:
    """Use specific approved harmonic baselines where supported.

    Genre identity and existing performance registry are authoritative.
    This layer selects only the Theory engine's currently supported triads.
    It never invents advanced seventh-chord rendering or edits instruments.
    All other styles keep the already working progression behavior.
    """
    if not isinstance(profile, dict):
        raise ValueError("GENRE_HARMONY_PROFILE_INVALID")
    if profile.get("resolution_policy") != "AUTOMATIC_BASELINE_ALLOWED":
        raise ValueError("GENRE_HARMONY_CONTROLLED_INPUT_REQUIRED")
    total = max(0, int(bars))
    if not total:
        return []
    major = quality in ("major", "ionian")
    known = (genre_name, profile.get("profile_id"))
    patterns = None
    if known == ("Funk", "FUNK_V1") and not major:
        # A mostly static, rhythm-centered vamp with occasional contrast.
        patterns = (
            ("i", "i", "i", "i", "i", "i", "VII", "i"),
            ("i", "i", "i", "i", "VI", "VI", "i", "i"),
            ("i", "i", "i", "i", "i", "i", "i", "i"),
        )
    elif known == ("Traditional Country", "TRADITIONAL_COUNTRY_V1") and major:
        # Strong I/IV/V vocabulary; vi and ii remain options, not mandates.
        patterns = (
            ("I", "I", "IV", "I", "V", "IV", "I", "V"),
            ("I", "IV", "I", "I", "V", "IV", "V", "I"),
            ("I", "I", "IV", "IV", "I", "V", "I", "V"),
        )
    elif known == ("Two-Step", "COUNTRY_TWO_STEP_V1") and major:
        # Functional cycle appropriate to the existing two-beat groove.
        patterns = (
            ("I", "I", "V", "V", "I", "IV", "V", "I"),
            ("I", "IV", "I", "V", "I", "IV", "V", "I"),
            ("I", "I", "IV", "I", "V", "V", "I", "I"),
        )
    if patterns is None:
        return fallback(quality, total, seedv)

    initial = (int(seedv) // 19) % len(patterns)
    out = []
    for bar in range(total):
        # Longer harmonic thoughts than the former universal four-chord cell.
        selected = (bar // 16 + initial) % len(patterns)
        out.append(patterns[selected][bar % 8])
    out[-1] = "I" if major else "i"
    return out



def _clamp_velocity(value: float) -> int:
    return max(1, min(127, int(round(value))))


def _bar_of(event: dict[str, Any], meter: float) -> int:
    return max(0, int(float(event.get("start_beat", 0.0)) // max(meter, 1e-9)))


def apply_genre_expression(
    events: list[dict[str, Any]],
    template: str,
    meter: float,
    creation_seed: int = 0,
) -> list[dict[str, Any]]:
    """Rock-first phrase expression in genre development, not instrument DSP.

    The instrument side already owns guitar sustain/vibrato, recordings,
    drum samples, and the separate recorded sub-kick. Do not duplicate those
    mechanisms here. Only existing Rock lead-guitar note velocity and slight
    offbeat timing are shaped. No new notes, timbres, or extra tracks.
    Unsupported genres stay completely untouched until separately profiled.
    """
    if str(template).lower() != "rock":
        return events
    shaped = [dict(event) for event in events]
    phrases: dict[int, list[int]] = {}
    for index, event in enumerate(shaped):
        if str(event.get("track_id", "")).upper() != "LEAD":
            continue
        if "guitar" not in str(event.get("instrument_id", "")).lower():
            continue
        start = float(event.get("start_beat", 0))
        phrase_id = int(start // max(float(meter), 1e-9)) // 4
        phrases.setdefault(phrase_id, []).append(index)

    for phrase_id, indices in phrases.items():
        indices.sort(key=lambda i: (
            float(shaped[i]["start_beat"]), int(shaped[i].get("midi", 0))
        ))
        count = len(indices)
        if count < 3:
            continue
        for position, index in enumerate(indices):
            event = shaped[index]
            articulation = str(event.get("articulation", "")).lower()
            if any(tag in articulation for tag in ("mute", "staccato", "chop", "short")):
                continue
            position_fraction = position / (count - 1)
            contour = 1.0 - abs(2 * position_fraction - 1.0)
            phrase_variation = 0.008 * ((phrase_id + int(creation_seed)) % 3 - 1)
            if isinstance(event.get("velocity"), (int, float)):
                factor = 0.98 + 0.06 * contour + phrase_variation
                event["velocity"] = max(
                    1, min(127, int(round(event["velocity"] * factor)))
                )
            # Preserve downbeat anchors and keep the existing groove tight.
            # Changes never move kick/bass/snare or the sample-based vibrato.
            if 0 < position < count - 1:
                start = float(event["start_beat"])
                previous = float(shaped[indices[position - 1]]["start_beat"])
                following = float(shaped[indices[position + 1]]["start_beat"])
                spacing = min(start - previous, following - start)
                if spacing >= 0.125 and abs(start - round(start)) >= 0.03:
                    offset = (0.005, -0.006, 0.003, -0.003)[
                        (position + phrase_id + int(creation_seed)) % 4
                    ]
                    offset = max(-spacing * 0.10, min(spacing * 0.10, offset))
                    event["start_beat"] = round(start + offset, 6)
    return shaped


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
        # Match legacy Rock drum notes to the dedicated SFZ instrument on
        # each logical track. Previously KICK and SNARE mixed "drums" with
        # their named identities, which the MIDI router correctly rejects.
        if tmpl == "rock" and e.get("instrument_id") == "drums":
            e["instrument_id"] = {
                "KICK": "kick_drum_rock",
                "SNARE": "snare_drum",
                "HAT": "hi_hat",
            }.get(str(e.get("track_id", "")).upper(), e["instrument_id"])
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
        # Jazz voicings are chords, not an unrelated collection of MIDI notes.
        # Never thin or invalidate their constituent pitches by MIDI parity.
        jazz_voicing = (
            ctx.get("harmony", {}).get("voicing_model")
            == "JAZZ_EXTENDED_HARMONY_V1"
        )
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
        # A sampled lead guitar is still a guitar, but it must not also be
        # processed as RHYTHM/HARMONY: chord timing edits can displace or
        # discard individual lead notes and create an unnaturally choppy line.
        if tmpl == "rock" and is_lead:
            is_harmony = False

        # Rock needs audible song-scale development, not a four-bar cell with
        # tiny velocity changes. Keep the same generated notes/resources but
        # reshape timing, density, and phrase roles across each 16-bar section.
        if tmpl == "rock":
            phrase_in_section = (bar % 16) // 4
            section_role = section % 6
            gain *= (0.82, 0.96, 1.08, 0.90, 1.12, 0.76)[section_role]

            if is_bass:
                # Keep Rock bass articulated. The previous 1.9-beat minimum made
                # a correct BPM feel half-speed. Use punchy quarter/eighth-note
                # values and let the sampled instrument provide its own decay.
                original = float(e.get("duration_beats", 0.1))
                e["duration_beats"] = min(original, 0.90 if phrase_in_section in (0, 2) else 0.48)
                e["duration_beats"] = max(0.22, e["duration_beats"])
                gain *= 1.08
            # Do not truncate all guitar notes to a universal short value.
            # The genre-authorized instrument performance layer below selects
            # ringing, fast-picked, legato, or explicitly short playing.

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
                # Preserve all notes in verified Jazz chord voicings, even
                # when the arrangement is dynamically quieter in a breakdown.
                if (midi + phrase + creation_seed) % 3 and not (
                    jazz_voicing and track == "HARMONY"
                ):
                    continue
            if is_hat and int(round(local * 4)) % 2:
                continue
            gain *= 0.78

        if is_harmony and not breakdown:
            variant = (phrase + section + creation_seed) % 4
            if variant == 1 and local > 0:
                shifted = min(meter - 0.06, local + 0.125)
                e["start_beat"] = bar * meter + shifted
            elif variant == 2 and local >= meter / 2 and not (
                (tmpl == "rock" and "guitar" in instrument)
                or (jazz_voicing and track == "HARMONY")
            ):
                # MIDI parity is not musical harmony. The protected Jazz
                # and Rock chord groups keep every approved chord tone.
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
            if isinstance(note, int) and tmpl != "rock":
                # Preserve non-Rock genre execution unchanged. Rock's old
                # automatic +12/-12 semitone flip made the sampled lead sound
                # thin and piercing regardless of the authored melodic range.
                octave_shift = (0, 12, 0, -12)[(section + creation_seed) % 4]
                candidate = note + octave_shift
                if 48 <= candidate <= 108:
                    e["midi"] = candidate
            # Rock lead keeps the notes authored by the theory/arrangement
            # engine; foreground presence is handled by the existing gain
            # contract, not by artificial transposition.
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

    # The preserved Rock profile requires a complete, audible kit. Add a
    # deterministic kick/snare backbeat underneath the legacy pattern so Rock
    # always has a physical groove. These are short one-shot drum triggers.
    if tmpl == "rock":
        for bar in range(total_bars):
            bar_start = bar * meter
            # Kick: strong 1 and 3, with selected eighth-note pushes for motion.
            kick_positions = [0.0, 2.0]
            if bar % 4 in (1, 3):
                kick_positions.append(2.5)
            if bar % 8 == 7:
                kick_positions.append(3.5)
            for beat in kick_positions:
                start = bar_start + beat
                if start < total_beats:
                    developed.append({
                        "track_id": "KICK",
                        "instrument_id": "kick_drum_rock",
                        "drum": "kick",
                        "start_beat": start,
                        "duration_beats": 0.10,
                        "midi": 36,
                        "velocity": 112 if beat in (0.0, 2.0) else 96,
                        "articulation": "rock_kick",
                    })

            # Snare: conventional backbeat on 2 and 4.
            for beat in (1.0, 3.0):
                start = bar_start + beat
                if start < total_beats:
                    developed.append({
                        "track_id": "SNARE",
                        "instrument_id": "snare_drum",
                        "drum": "snare",
                        "start_beat": start,
                        "duration_beats": 0.10,
                        "midi": 38,
                        "velocity": 108 if beat == 3.0 else 102,
                        "articulation": "rock_backbeat",
                    })

        existing_tracks = {str(e.get("track_id", "")).upper() for e in developed}

        if "TOMS" not in existing_tracks:
            # Short descending fills at 16-bar transitions.
            for bar in range(15, max(15, total_bars - 1), 16):
                if bar >= total_bars - 1:
                    break
                for frac, note, velocity in (
                    (0.625, 47, 86),
                    (0.750, 45, 94),
                    (0.875, 43, 102),
                ):
                    start = bar * meter + meter * frac
                    if start < total_beats:
                        developed.append({
                            "track_id": "TOMS",
                            "instrument_id": "tom_tom",
                            "drum": "tom",
                            "start_beat": start,
                            "duration_beats": 0.12,
                            "midi": note,
                            "velocity": velocity,
                            "articulation": "tom_fill",
                        })

        if "CRASH" not in existing_tracks:
            # Mark section arrivals without turning every phrase into a crash.
            crash_bars = [4] + list(range(16, total_bars, 16))
            for bar in crash_bars:
                start = bar * meter
                if bar < total_bars and start < total_beats:
                    developed.append({
                        "track_id": "CRASH",
                        "instrument_id": "crash_cymbal",
                        "drum": "crash",
                        "start_beat": start,
                        "duration_beats": 0.20,
                        "midi": 49,
                        "velocity": 90,
                        "articulation": "section_crash",
                    })

        if "RIDE" not in existing_tracks:
            # Alternate timekeeping in selected later lift phrases so the ride
            # has a musical role rather than duplicating the hi-hat everywhere.
            for section_start in range(32, total_bars, 32):
                for bar in range(section_start, min(section_start + 4, total_bars)):
                    for beat in (0.0, 1.0, 2.0, 3.0):
                        start = bar * meter + beat
                        if start < total_beats:
                            developed.append({
                                "track_id": "RIDE",
                                "instrument_id": "ride_cymbal",
                                "drum": "ride",
                                "start_beat": start,
                                "duration_beats": 0.10,
                                "midi": 51,
                                "velocity": 72,
                                "articulation": "ride_timekeeping",
                            })

    developed.sort(
        key=lambda x: (
            float(x.get("start_beat", 0.0)),
            str(x.get("track_id", "")),
            int(x.get("midi", 0) or 0),
        )
    )
    if tmpl == "rock":
        from instrument_performance_contract import perform
        developed = perform(developed, "ROCK")
        # Genre expression shapes the performance; SFZ owns the sound.
        developed = apply_genre_expression(developed, tmpl, meter, creation_seed)
    return developed

# --- Shared eight-section Genre Development template (non-rendering) ---
# This is a VIEW of the existing 55 authoritative performance profiles.
# No sound-bank settings, instrument DSP, new musical defaults or mixer behavior
# are duplicated inside individual genre configurations.
GENRE_TEMPLATE_VERSION = "GENRE_DEVELOPMENT_EIGHT_SECTION_R1"
GENRE_TEMPLATE_FIELDS = (
    ("Genre Identity", (
        "profile_id", "family", "status", "scope_note", "resolution_policy", "provenance")),
    ("Music Theory", ("harmony_behavior",)),
    ("Rhythm & Groove", (
        "meter_options", "groove_behavior", "percussion_behavior_if_applicable")),
    ("Tempo", ("tempo_bpm_range",)),
    ("Song Structure", (
        "form_tendencies", "phrase_behavior", "arrangement_transformation")),
    ("Instrumentation", (
        "instrument_role_behavior", "bass_behavior", "ensemble_player_behavior",
        "manufacturer_adapter_requirements")),
    ("Musical Expression & Natural Performance", (
        "dynamic_behavior", "articulation_behavior",
        "timing_humanization_behavior", "continuous_performance_control")),
    ("Genre Validation", (
        "sound_effects_intent", "mix_prominence_intent", "production_mastering_intent")),
)
# Shared references are defined once, never copied into instrument profiles.
UNIVERSAL_GENRE_REFERENCES = {
    "note_and_beat_engine": "EXISTING_COMPOSITION_THEORY_AND_EVENT_ENGINE",
    "expression_capabilities": "EXISTING_INSTRUMENT_PERFORMANCE_AND_SFZ_CONTROLS",
    "recorded_instrument_audio": "EXISTING_APPROVED_SAMPLE_RENDERER",
    "final_audio": "EXISTING_STANDALONE_3D_MIXER",
}


def compile_genre_template(genre_name: str, profile: dict[str, Any]) -> dict[str, Any]:
    """Read, but never rewrite, an authoritative genre performance profile.

    The eight original headings are kept as a fixed view of existing metadata.
    Fields cannot fall through to another genre or receive guessed defaults.
    The seven controlled-choice genres retain their input gates.
    """
    if not genre_name or not isinstance(profile, dict):
        raise ValueError("GENRE_TEMPLATE_SOURCE_INVALID")
    required = {field for _, fields in GENRE_TEMPLATE_FIELDS for field in fields}
    missing = sorted(field for field in required if field not in profile)
    if missing:
        raise ValueError("GENRE_TEMPLATE_FIELDS_MISSING:" + ",".join(missing))
    bounds = profile["tempo_bpm_range"]
    if (not isinstance(bounds, list) or len(bounds) != 2 or
            not all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in bounds) or
            not 0 < bounds[0] <= bounds[1]):
        raise ValueError("GENRE_TEMPLATE_TEMPO_RANGE_INVALID")
    if not isinstance(profile["meter_options"], list) or not profile["meter_options"]:
        raise ValueError("GENRE_TEMPLATE_METER_OPTIONS_INVALID")

    # Copy only values from the specific selected genre. No DSP settings here.
    from copy import deepcopy
    sections = [
        {"number": i, "heading": title,
         "genre_specific": {field: deepcopy(profile[field]) for field in fields}}
        for i, (title, fields) in enumerate(GENRE_TEMPLATE_FIELDS, 1)
    ]
    sections[3]["pace_choices"] = {
        "A": "SLOW_WITHIN_APPROVED_GENRE_RANGE",
        "B": "MEDIUM_WITHIN_APPROVED_GENRE_RANGE",
        "C": "FAST_WITHIN_APPROVED_GENRE_RANGE",
        "exact_pace_boundaries": "GENRE_SPECIFIC_VALIDATION_PENDING",
    }
    automatic = profile["resolution_policy"] == "AUTOMATIC_BASELINE_ALLOWED"
    return {
        "template_version": GENRE_TEMPLATE_VERSION,
        "selected_genre": str(genre_name),
        "selected_profile_id": profile["profile_id"],
        "resolution_policy": profile["resolution_policy"],
        "automatic_baseline_allowed": automatic,
        "decision_status": "BASELINE_ALLOWED" if automatic else "CONTROLLED_INPUT_REQUIRED",
        "universal_reference": UNIVERSAL_GENRE_REFERENCES,
        "sections": sections,
        "audio_validation": "NOT_ESTABLISHED_BY_TEMPLATE",
    }


def genre_template_from_registry(genre_name: str, registry: dict[str, Any]) -> dict[str, Any]:
    """Resolve by exact menu label and never substitute a neighboring style."""
    if not isinstance(registry, dict) or not isinstance(registry.get("profiles"), dict):
        raise ValueError("GENRE_TEMPLATE_REGISTRY_INVALID")
    profiles = registry["profiles"]
    if genre_name not in profiles:
        raise ValueError("GENRE_TEMPLATE_UNKNOWN_GENRE:" + str(genre_name))
    return compile_genre_template(genre_name, profiles[genre_name])

# --- Jazz harmony and phrased comping; independent of instrument audio ---
# This does not impose meditative triads on Jazz. Existing Theory validates
# the diatonic roots, then the genre layer supplies executable sevenths/sixths.
JAZZ_GENRE_PROFILES = {
    "Swing": "JAZZ_SWING_V1",
    "Jazz Ballad": "JAZZ_BALLAD_V1",
    "Big Band": "BIG_BAND_V1",
    "Jazz Waltz": "JAZZ_WALTZ_V1",
    "Bebop": "BEBOP_V1",
    "Cool Jazz": "COOL_JAZZ_V1",
    "Dixieland": "DIXIELAND_V1",
    "Jazz Fusion": "JAZZ_FUSION_V1",
}

# Project-authorized starting patterns, not fixed genre standards.
JAZZ_ROMAN_PATTERNS = {
    "Swing": (("ii", "V", "I", "vi", "ii", "V", "I", "V"),
              ("I", "IV", "iii", "vi", "ii", "V", "I", "V")),
    "Jazz Ballad": (("I", "I", "vi", "vi", "ii", "V", "I", "I"),
                   ("IV", "IV", "iii", "vi", "ii", "V", "I", "I")),
    "Big Band": (("I", "vi", "ii", "V", "I", "IV", "V", "I"),
                 ("IV", "V", "iii", "vi", "ii", "V", "I", "V")),
    "Jazz Waltz": (("ii", "V", "I", "IV", "iii", "vi", "ii", "V"),
                   ("I", "vi", "ii", "V", "I", "IV", "V", "I")),
    "Bebop": (("ii", "V", "I", "vi", "ii", "V", "iii", "vi"),
              ("iii", "vi", "ii", "V", "iii", "vi", "ii", "V")),
    "Cool Jazz": (("I", "I", "IV", "IV", "ii", "V", "I", "I"),
                  ("vi", "vi", "ii", "ii", "IV", "IV", "V", "I")),
    "Dixieland": (("I", "I", "IV", "I", "V", "IV", "I", "V"),
                  ("I", "IV", "I", "V", "I", "IV", "V", "I")),
    "Jazz Fusion": (("i", "i", "iv", "iv", "VII", "VI", "i", "i"),
                    ("i", "VI", "VII", "i", "iv", "VII", "VI", "i")),
}


def _approved_jazz(genre_name: str, profile: dict[str, Any]) -> bool:
    return (isinstance(profile, dict) and
            profile.get("resolution_policy") == "AUTOMATIC_BASELINE_ALLOWED" and
            genre_name in JAZZ_GENRE_PROFILES and
            JAZZ_GENRE_PROFILES[genre_name] == profile.get("profile_id"))


def build_jazz_progression(genre_name: str, profile: dict[str, Any],
                           quality: str, bars: int, seedv: int) -> list[str] | None:
    """Select Jazz movement without imposing the universal triad cycle."""
    if not _approved_jazz(genre_name, profile):
        return None
    major = quality in ("major", "ionian")
    minor = quality in ("natural_minor", "aeolian", "minor")
    if (genre_name == "Jazz Fusion" and not minor) or (genre_name != "Jazz Fusion" and not major):
        raise ValueError("JAZZ_HARMONY_MODE_REQUIRES_REVIEW")
    options = JAZZ_ROMAN_PATTERNS[genre_name]
    total = max(0, int(bars))
    initial = (int(seedv) // 19) % len(options)
    out = [options[(initial + bar // 16) % len(options)][bar % 8] for bar in range(total)]
    if out:
        out[-1] = "i" if minor else "I"
    return out


def realize_jazz_voicings(ctx: dict[str, Any], genre_name: str,
                           profile: dict[str, Any]) -> dict[str, Any]:
    """Extend Theory-validated Jazz harmony with sevenths and early-jazz sixths.

    Instrument samples, articulation DSP, routing and the standalone mixer
    remain unchanged. Return independent composition data, not mutated input.
    """
    if not _approved_jazz(genre_name, profile):
        return ctx
    from copy import deepcopy
    built = deepcopy(ctx)
    key = built.get("key", {})
    mode = key.get("mode")
    major = mode in ("major", "ionian")
    minor = mode in ("natural_minor", "aeolian")
    if (genre_name == "Jazz Fusion" and not minor) or (genre_name != "Jazz Fusion" and not major):
        raise ValueError("JAZZ_HARMONY_MODE_REQUIRES_REVIEW")
    scale = key.get("scale", [])
    pcs = key.get("scale_pitch_classes", [])
    if len(scale) != 7 or len(pcs) != 7:
        raise ValueError("JAZZ_HARMONY_SCALE_INVALID")
    degrees = (
        {"I": 0, "ii": 1, "iii": 2, "IV": 3, "V": 4, "vi": 5, "vii°": 6}
        if major else
        {"i": 0, "ii°": 1, "III": 2, "iv": 3, "v": 4, "VI": 5, "VII": 6}
    )
    chords = built.get("harmony", {}).get("chords", [])
    for chord in chords:
        roman = chord.get("roman")
        if roman not in degrees:
            raise ValueError("JAZZ_HARMONY_DEGREE_UNSUPPORTED:" + str(roman))
        i = degrees[roman]
        early_jazz_sixth = genre_name == "Dixieland" and roman in ("I", "IV")
        indices = [i, (i + 2) % 7, (i + 4) % 7,
                   (i + (5 if early_jazz_sixth else 6)) % 7]
        notes = [scale[j] for j in indices]
        chord_pcs = [pcs[j] for j in indices]
        if chord.get("root") != notes[0]:
            raise ValueError("JAZZ_HARMONY_ROOT_MISMATCH")
        intervals = tuple((n - chord_pcs[0]) % 12 for n in chord_pcs[1:])
        quality = {
            (4, 7, 11): "major7",
            (4, 7, 10): "dominant7",
            (3, 7, 10): "minor7",
            (3, 7, 11): "minor_major7",
            (3, 6, 10): "half_diminished7",
            (3, 6, 9): "diminished7",
            (4, 8, 11): "augmented_major7",
            (4, 8, 10): "augmented7",
        }
        chord["notes"] = notes
        chord["pitch_classes"] = chord_pcs
        chord["quality"] = (
            "diatonic_sixth" if early_jazz_sixth else
            quality.get(intervals, "diatonic_seventh")
        )
    for bar, constraint in enumerate(built.get("melody_constraints_by_bar", [])):
        if bar < len(chords):
            constraint.get("constraints", {})["strong_beat_preference"] = list(
                chords[bar]["pitch_classes"]
            )
    built["harmony"]["voicing_model"] = "JAZZ_EXTENDED_HARMONY_V1"
    built["harmony"]["voicing_status"] = "EXTENDED_CHORDS_EXECUTABLE_NOT_AUDIO_VERIFIED"
    return built


def apply_jazz_phrase_expression(events: list[dict[str, Any]],
                                 genre_name: str, profile: dict[str, Any],
                                 meter: float, creation_seed: int = 0
                                 ) -> list[dict[str, Any]]:
    """Shape Jazz chord phrase dynamics while keeping all voices together.

    Do not randomize timing, modify bass/drums, or implement instrument DSP.
    Dixieland currently has no dedicated chord-playing track; do not invent one.
    """
    if not _approved_jazz(genre_name, profile):
        return events
    shaped = [dict(event) for event in events]
    arc = (0.96, 0.98, 1.01, 1.03, 1.05, 1.04, 1.00, 0.95)
    for event in shaped:
        if str(event.get("track_id", "")).upper() != "HARMONY":
            continue
        if not isinstance(event.get("velocity"), (int, float)):
            continue
        bar = int(float(event.get("start_beat", 0.0)) // max(float(meter), 1e-9))
        section = (bar // 16 + int(creation_seed)) % 3
        factor = arc[bar % 8] * (0.98, 1.00, 1.02)[section]
        event["velocity"] = max(1, min(127, int(round(event["velocity"] * factor))))
    return shaped
