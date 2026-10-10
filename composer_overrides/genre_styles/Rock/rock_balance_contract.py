"""Composer-side Rock-only relative gains for preserved sampled stereo stems.

Production defaults remain unchanged; ROCK2_ENSEMBLE_AUDITION is opt-in and
changes only the recorded Wurlitzer gain for comparison.
"""
from __future__ import annotations

import os

CONTRACT_VERSION = "ROCK_ARRANGEMENT_BALANCE_R1"

# Relative to the recorded resource's already verified target_gain_db.
# Musical roles are the authority, not sample-library identities alone.
ROCK_GAIN_TRIMS_DB = {
    "HARMONY": -5.5,  # Chord guitar supports, rather than masks, the melody
    "LEAD": +5.5,     # Lead line is foreground
    "BASS": +1.0,     # Natural electric bass remains a distinct band foundation
    "KICK": +0.5,     # Retain the measured kick peak; DEPTH needs separate work
    "SNARE": +6.5,    # Bring backbeat forward
    "HAT": +12.0,     # Quiet real sampled hat needs large lift
    "TOMS": +5.0,
    "CRASH": +5.0,
    "RIDE": +8.0,
}

# Protect against accidental gain changes if the genre instrumentation changes.
ROCK_EXPECTED_INSTRUMENTS = {
    "HARMONY": "electric_guitar",
    "KEYS": "electric_piano",
    "LEAD": "electric_guitar",
    "BASS": "electric_bass_guitar",
    "KICK": "kick_drum_rock",
    "SNARE": "snare_drum",
    "HAT": "hi_hat",
    "TOMS": "tom_tom",
    "CRASH": "crash_cymbal",
    "RIDE": "ride_cymbal",
}


def apply_rock_balance(engine_result: dict) -> dict:
    """Return an independent, Rock-only resource-gain overlay.

    The returned payload is consumed by the existing mixer. Never change the
    source engine result, MIDI, tempo, timing, SFZ mapping, sample audio,
    spatial positions, limiter, mastering algorithm, or other genres.
    """
    if str(engine_result.get("genre", "")).upper() != "ROCK":
        return engine_result

    modules = engine_result.get("modules")
    if not isinstance(modules, dict):
        return engine_result
    target = modules.get("target")
    instruments = modules.get("instrument")
    if not isinstance(target, dict) or not isinstance(instruments, dict):
        return engine_result
    resolved = target.get("resolved_resources")
    profiles = instruments.get("profiles")
    if not isinstance(resolved, list) or not isinstance(profiles, list):
        return engine_result

    identities = {
        str(p.get("track_id", "")).upper(): str(p.get("instrument_id", ""))
        for p in profiles if isinstance(p, dict)
    }

    # The listener liked the original clean instrument separation. Only an
    # isolated opt-in audition may lift ONLY the real Wurlitzer.
    # No stem or source sample is changed and no other genre is affected.
    audition = os.environ.get("AI_COMP_ROCK2_ENSEMBLE_AUDITION", "") == "1"
    trims = dict(ROCK_GAIN_TRIMS_DB)
    if audition:
        trims.update({"KEYS": +4.0})
    changed = []
    edited = []
    for record in resolved:
        if not isinstance(record, dict):
            edited.append(record)
            continue
        track = str(record.get("track_id", "")).upper()
        resource = record.get("resource")
        if (track not in trims or
                identities.get(track) != ROCK_EXPECTED_INSTRUMENTS.get(track) or
                not isinstance(resource, dict)):
            edited.append(record)
            continue
        original = resource.get("target_gain_db", 0.0)
        if not isinstance(original, (int, float)) or isinstance(original, bool):
            edited.append(record)
            continue
        gain = float(original) + trims[track]
        # The current 3D mixer normalizes the entire stereo master.
        # These trims are relative, not a promise of final loudness or kick EQ.
        new_resource = dict(resource)
        new_resource["target_gain_db"] = gain
        new_resource["rock_gain_offset_db"] = trims[track]
        new_resource["mix_profile"] = (CONTRACT_VERSION + "_ENSEMBLE_AUDITION" if audition else CONTRACT_VERSION)
        edited.append({**record, "resource": new_resource})
        changed.append(track)

    if not changed:
        return engine_result

    return {
        **engine_result,
        "modules": {
            **modules,
            "target": {
                **target,
                "resolved_resources": edited,
            },
        },
        "composer_mix_instruction": {
            "name": CONTRACT_VERSION + ("_ENSEMBLE_AUDITION" if audition else ""),
            "adjusted_tracks": changed,
            "keyboard_only_option": audition,
            "kick_depth_note": "NO_SUBKICK_OR_LOW_FREQUENCY_PROCESSING_IN_THIS_RELEASE",
        },
    }
