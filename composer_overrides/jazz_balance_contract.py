"""Jazz Ballad-only *measured* equal-intensity final-stage gain metadata.

The standalone 3D mixer remains unchanged and still reads target_gain_db.
Measure the actual six SFZ-rendered stems per composition, not genre-wide
fixed guesses. Equal presence is a mix goal; peak/RMS cannot prove identical
human-perceived loudness without listening or frequency-weighted measurement.
No WAV files, instrument definitions or Rock mix data are changed here.
"""
from __future__ import annotations

from math import isfinite
from statistics import median

JAZZ_BALANCE_VERSION = "JAZZ_BALLAD_MEASURED_EQUAL_INTENSITY_R2"

# Weight sustained energy vs transient strength for a modest, reproducible
# first-order intensity proxy. This is NOT claimed to be LUFS or psychoacoustic
# equal loudness. Short kick/hat/brush hits have less full-track RMS than
# sustained melodic parts, so weighting them identically would over-amplify
# the brushed samples and turn their natural texture into static.
JAZZ_INTENSITY_WEIGHTS = {
    "HARMONY": (0.70, 0.30),
    "LEAD": (0.70, 0.30),
    "BASS": (0.70, 0.30),
    "SNARE": (0.25, 0.75),
    "HAT": (0.25, 0.75),
    "KICK": (0.25, 0.75),
}
JAZZ_EXPECTED_INSTRUMENTS = {
    "LEAD": "clarinet_bb",
    "BASS": "double_bass",
    "HARMONY": "electric_piano",
    "SNARE": "snare_drum",
    "HAT": "hi_hat",
    "KICK": "kick_drum_rock",
}
# Ceiling prevents sudden enormous boosts for very quiet/noisy recordings.
# The composer refuses to label the result equal-intensity if a constraint
# prevents matching. Absolute output peaks remain the final mixer's concern.
MIN_TRIM_DB = -24.0
MAX_TRIM_DB = +24.0
EQUALITY_TOLERANCE_DB = 1.0


def _measured_stems(stems: list[dict]) -> dict[str, float]:
    """Map six raw rendered tracks to a finite per-track intensity proxy."""
    measured = {}
    for item in stems:
        if not isinstance(item, dict):
            continue
        track = str(item.get("track_id", "")).upper()
        if track not in JAZZ_INTENSITY_WEIGHTS:
            continue
        if track in measured:
            raise ValueError("JAZZ_BALLAD_DUPLICATE_AUDIO_STEM:" + track)
        expected = JAZZ_EXPECTED_INSTRUMENTS[track]
        if item.get("instrument_id") != expected:
            raise ValueError("JAZZ_BALLAD_WRONG_AUDIO_SOURCE:" + track)
        if not isinstance(item.get("note_count"), int) or item["note_count"] < 1:
            raise ValueError("JAZZ_BALLAD_EMPTY_AUDIO_PART:" + track)
        peak = item.get("peak_dbfs")
        rms = item.get("rms_dbfs")
        if not all(isinstance(x, (int, float)) and not isinstance(x, bool)
                   and isfinite(float(x)) for x in (peak, rms)):
            raise ValueError("JAZZ_BALLAD_NO_MEASURABLE_AUDIO:" + track)
        if float(peak) < float(rms):
            raise ValueError("JAZZ_BALLAD_INVALID_AUDIO_LEVELS:" + track)
        rms_weight, transient_weight = JAZZ_INTENSITY_WEIGHTS[track]
        measured[track] = rms_weight * float(rms) + transient_weight * float(peak)
    missing = set(JAZZ_EXPECTED_INSTRUMENTS) - set(measured)
    if missing:
        raise ValueError("JAZZ_BALLAD_EQUAL_INTENSITY_MISSING_TRACKS:" +
                         ",".join(sorted(missing)))
    return measured


def apply_jazz_ballad_balance(engine_result: dict,
                              stems: list[dict] | None = None) -> dict:
    """Add equal-intensity trim metadata to six *real* Jazz Ballad resources.

    No resource or input dictionary is mutated. If stems aren't provided,
    leave the original mix unchanged and do not imply equalization occurred.
    If stems are provided but insufficient, fail explicitly rather than
    deliver a nominally finished, mostly-silent arrangement.
    """
    if not isinstance(engine_result, dict) or engine_result.get("genre") != "Jazz Ballad":
        return engine_result
    if stems is None:
        return engine_result
    observed = _measured_stems(stems)
    modules = engine_result.get("modules")
    if not isinstance(modules, dict):
        raise ValueError("JAZZ_BALLAD_NO_MIX_MODULES")
    instruments = modules.get("instrument")
    target = modules.get("target")
    if not isinstance(instruments, dict) or not isinstance(target, dict):
        raise ValueError("JAZZ_BALLAD_NO_INSTRUMENT_TARGETS")
    profiles = instruments.get("profiles")
    resolved = target.get("resolved_resources")
    if not isinstance(profiles, list) or not isinstance(resolved, list):
        raise ValueError("JAZZ_BALLAD_NO_RESOLVED_RESOURCES")

    identities = {
        str(p.get("track_id", "")).upper(): str(p.get("instrument_id", ""))
        for p in profiles if isinstance(p, dict)
    }
    gain_before = {}
    for record in resolved:
        if not isinstance(record, dict):
            continue
        track = str(record.get("track_id", "")).upper()
        if track not in JAZZ_EXPECTED_INSTRUMENTS:
            continue
        if identities.get(track) != JAZZ_EXPECTED_INSTRUMENTS[track]:
            raise ValueError("JAZZ_BALLAD_INSTRUMENT_PROFILE_MISMATCH:" + track)
        resource = record.get("resource")
        if not isinstance(resource, dict):
            raise ValueError("JAZZ_BALLAD_RESOURCE_MISSING:" + track)
        base = resource.get("target_gain_db", 0.0)
        if not isinstance(base, (int, float)) or isinstance(base, bool) or not isfinite(float(base)):
            raise ValueError("JAZZ_BALLAD_INVALID_BASE_GAIN:" + track)
        if track in gain_before:
            raise ValueError("JAZZ_BALLAD_DUPLICATE_RESOURCE:" + track)
        gain_before[track] = float(base)
    if set(gain_before) != set(JAZZ_EXPECTED_INSTRUMENTS):
        raise ValueError("JAZZ_BALLAD_MISSING_RESOURCES:" +
                         ",".join(sorted(set(JAZZ_EXPECTED_INSTRUMENTS) - set(gain_before))))

    before = {track:observed[track] + gain_before[track] for track in gain_before}
    shared_target = float(median(before.values()))
    desired = {track:shared_target - before[track] for track in before}
    trimmed = {track:max(MIN_TRIM_DB, min(MAX_TRIM_DB, offset))
               for track,offset in desired.items()}
    after = {track:before[track] + trimmed[track] for track in before}
    span = max(after.values()) - min(after.values())
    if span > EQUALITY_TOLERANCE_DB:
        raise ValueError("JAZZ_BALLAD_EQUAL_INTENSITY_OUT_OF_RANGE:" + str(round(span,2)))

    updated = []
    for record in resolved:
        if not isinstance(record, dict):
            updated.append(record)
            continue
        track = str(record.get("track_id", "")).upper()
        if track not in trimmed:
            updated.append(record)
            continue
        resource = dict(record["resource"])
        resource["target_gain_db"] = gain_before[track] + trimmed[track]
        resource["jazz_gain_offset_db"] = trimmed[track]
        resource["mix_profile"] = JAZZ_BALANCE_VERSION
        updated.append({**record, "resource": resource})
    return {
        **engine_result,
        "modules": {
            **modules,
            "target": {**target, "resolved_resources": updated},
        },
        "jazz_mix_instruction": {
            "name": JAZZ_BALANCE_VERSION,
            "goal": "EQUAL_PERCEIVED_INTENSITY",
            "verification": "MEASURED_PEAK_AND_RMS_PROXY_REQUIRES_AUDITION",
            "target_proxy_db": round(shared_target, 3),
            "post_mix_proxy_spread_db": round(span, 3),
            "individual_offsets_db": {t:round(v, 3) for t,v in trimmed.items()},
            "adjusted_tracks": sorted(trimmed),
            "preserve_sample_sources": True,
            "preserve_standalone_3d_mixer": True,
        },
    }
