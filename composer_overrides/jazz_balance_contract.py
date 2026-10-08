"""Jazz Ballad-only final-stage instrument balance metadata.

This is not an instrument, a synthesizer, a mixer rewrite, or a change to Rock.
The existing standalone 3D mixer reads target_gain_db for each real sample stem.
"""
from __future__ import annotations

JAZZ_BALANCE_VERSION = "JAZZ_BALLAD_AUDIBILITY_R1"

# Relative changes to the instrument bank's already approved target gains.
# Measured unbalanced Jazz Ballad stems: piano -35.7 dBFS RMS,
# clarinet -56.1, bass -44.7, brushed snare -50.3. These trims improve
# relative balance without replacing recordings or modifying source stems.
JAZZ_GAIN_TRIMS_DB = {
    "LEAD": 18.0,      # Recorded clarinet must be the audible melody
    "BASS": 3.0,       # Recorded double bass should anchor the ensemble
    "HARMONY": -5.0,   # Piano accompanies the melody; no masking
    "SNARE": -9.0,     # Recorded brush stirring must not become constant hiss
    "HAT": -3.0,
    "KICK": -2.0,
}

JAZZ_EXPECTED_INSTRUMENTS = {
    "LEAD": "clarinet_bb",
    "BASS": "double_bass",
    "HARMONY": "electric_piano",
    "SNARE": "snare_drum",
    "HAT": "hi_hat",
    "KICK": "kick_drum_rock",
}


def apply_jazz_ballad_balance(engine_result: dict) -> dict:
    """Return an independent Jazz Ballad-only overlay; other genres unchanged."""
    if not isinstance(engine_result, dict) or engine_result.get("genre") != "Jazz Ballad":
        return engine_result
    modules = engine_result.get("modules")
    if not isinstance(modules, dict):
        return engine_result
    instruments = modules.get("instrument")
    target = modules.get("target")
    if not isinstance(instruments, dict) or not isinstance(target, dict):
        return engine_result
    profiles = instruments.get("profiles")
    resolved = target.get("resolved_resources")
    if not isinstance(profiles, list) or not isinstance(resolved, list):
        return engine_result
    identities = {
        str(p.get("track_id", "")).upper(): str(p.get("instrument_id", ""))
        for p in profiles if isinstance(p, dict)
    }
    updated, applied = [], []
    for record in resolved:
        if not isinstance(record, dict):
            updated.append(record)
            continue
        track = str(record.get("track_id", "")).upper()
        resource = record.get("resource")
        if (track not in JAZZ_GAIN_TRIMS_DB
                or identities.get(track) != JAZZ_EXPECTED_INSTRUMENTS[track]
                or not isinstance(resource, dict)):
            updated.append(record)
            continue
        baseline = resource.get("target_gain_db", 0.0)
        if not isinstance(baseline, (int, float)) or isinstance(baseline, bool):
            updated.append(record)
            continue
        new_resource = dict(resource)
        new_resource["target_gain_db"] = float(baseline) + JAZZ_GAIN_TRIMS_DB[track]
        new_resource["jazz_gain_offset_db"] = JAZZ_GAIN_TRIMS_DB[track]
        new_resource["mix_profile"] = JAZZ_BALANCE_VERSION
        updated.append({**record, "resource": new_resource})
        applied.append(track)
    if not applied:
        return engine_result
    return {
        **engine_result,
        "modules": {
            **modules,
            "target": {**target, "resolved_resources": updated},
        },
        "jazz_mix_instruction": {
            "name": JAZZ_BALANCE_VERSION,
            "adjusted_tracks": applied,
            "preserve_sample_sources": True,
            "preserve_standalone_3d_mixer": True,
        },
    }
