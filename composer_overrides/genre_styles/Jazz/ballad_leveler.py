"""Jazz Ballad-only measurable, equal-presence real-instrument mix balancing.

Measure the already-rendered WAV stem for every Ballad part. Compare its
ACTIVE sound, not the whole-song average: rests and sparse bass/snares
should not count as silence and trigger huge noise-amplifying boosts.

This only edits the per-track gain instructions going TO the independent 3D
mixer. It never changes WAV samples, piano timbre, MIDI, other Jazz styles,
Rock, the plug or any shared mixer implementation.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import math
import wave

import numpy as np

PROFILE = "JAZZ_BALLAD_EQUAL_ACTIVE_INTENSITY_V1"
INSTRUMENTS = {
    "HARMONY": "electric_piano",
    "LEAD": "clarinet_bb",
    "BASS": "double_bass",
    "KICK": "kick_drum_rock",
    "SNARE": "snare_drum",
    "HAT": "hi_hat",
}
MAX_TRIM_DB = 22.0
WINDOW_SECONDS = 0.25
ACTIVE_WINDOW_RANGE_DB = 24.0
PEAK_HEADROOM_DB = -2.0


def _active_rms_and_peak_db(wav_path: str) -> tuple[float, float] | None:
    """Read one 0.25-s window at a time. Bounded RAM for long compositions."""
    windows = []
    peak = 0.0
    with wave.open(str(Path(wav_path)), "rb") as stream:
        channels = stream.getnchannels()
        width = stream.getsampwidth()
        sample_rate = stream.getframerate()
        if channels not in (1, 2) or width not in (1, 2, 4) or sample_rate < 8000:
            raise ValueError("JAZZ_BALLAD_UNSUPPORTED_SOURCE_WAV")
        frames_per_window = max(512, round(sample_rate * WINDOW_SECONDS))
        while True:
            raw = stream.readframes(frames_per_window)
            if not raw:
                break
            if width == 1:
                audio = (np.frombuffer(raw, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0
            elif width == 2:
                audio = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
            else:
                audio = np.frombuffer(raw, dtype="<i4").astype(np.float32) / 2147483648.0
            if not len(audio) or len(audio) % channels:
                raise ValueError("JAZZ_BALLAD_INVALID_SOURCE_WAV_FRAMES")
            peak = max(peak, float(np.max(np.abs(audio))))
            power = float(np.mean(audio * audio, dtype=np.float64))
            if power > 1e-16:
                windows.append(10.0 * math.log10(power))
    if not windows or peak < 1e-8:
        return None
    loudest = max(windows)
    active = [w for w in windows if w >= loudest - ACTIVE_WINDOW_RANGE_DB]
    if not active:
        return None
    # The 65th percentile captures a note's audible body and rejects silent
    # gaps, low-level sample tails and the occasional spike in a snare hit.
    active_db = float(np.percentile(np.asarray(active), 65))
    peak_db = 20.0 * math.log10(peak)
    return active_db, peak_db


def equalize_ballad_stems(engine_result: dict, stems: list[dict]) -> dict:
    """Match active instrument-track levels, not fader positions.

    The measured source must contain real audio for every required Ballad
    instrument. A silent/missing required part fails clearly rather than
    producing a misleading "successful" piano-and-snare-only master.
    """
    if not isinstance(engine_result, dict) or engine_result.get("genre") != "Jazz Ballad":
        return engine_result
    if not isinstance(stems, list):
        raise ValueError("JAZZ_BALLAD_STEMS_NOT_AVAILABLE")
    modules = engine_result.get("modules", {})
    profiles = modules.get("instrument", {}).get("profiles", [])
    resource_list = modules.get("target", {}).get("resolved_resources", [])
    if not isinstance(profiles, list) or not isinstance(resource_list, list):
        raise ValueError("JAZZ_BALLAD_INVALID_MIX_INSTRUMENTS")
    identities = {str(row.get("track_id", "")).upper(): row.get("instrument_id")
                  for row in profiles if isinstance(row, dict)}
    resources = {str(row.get("track_id", "")).upper(): row.get("resource")
                 for row in resource_list if isinstance(row, dict)}
    stems_by_track = {str(row.get("track_id", "")).upper(): row
                      for row in stems if isinstance(row, dict)}
    levels = {}
    for role, expected_instrument in INSTRUMENTS.items():
        if identities.get(role) != expected_instrument:
            raise ValueError("JAZZ_BALLAD_INSTRUMENT_MISMATCH:" + role)
        binding = resources.get(role)
        if not isinstance(binding, dict):
            raise ValueError("JAZZ_BALLAD_MISSING_INSTRUMENT_RESOURCE:" + role)
        stem = stems_by_track.get(role)
        if not isinstance(stem, dict) or not stem.get("wav_path"):
            raise ValueError("JAZZ_BALLAD_MISSING_AUDIO_STEM:" + role)
        measurement = _active_rms_and_peak_db(stem["wav_path"])
        if measurement is None:
            raise ValueError("JAZZ_BALLAD_SILENT_INSTRUMENT:" + role)
        original_gain = float(binding.get("target_gain_db", 0.0))
        if not math.isfinite(original_gain):
            raise ValueError("JAZZ_BALLAD_INVALID_ORIGINAL_GAIN:" + role)
        db, peak_db = measurement
        levels[role] = {
            "measured_active_rms_dbfs": db, "measured_peak_dbfs": peak_db,
            "original_gain_db": original_gain,
            "original_effective_rms_dbfs": db + original_gain,
        }

    # Identical *active* level for every sounding part. Sparse accents still
    # retain musical rests; we don't force an always-on snare or synth.
    original_levels = [data["original_effective_rms_dbfs"] for data in levels.values()]
    reference_db = float(np.median(np.asarray(original_levels)))
    new_gains = {}
    for role, metrics in levels.items():
        desired_trim = reference_db - metrics["original_effective_rms_dbfs"]
        trim = max(-MAX_TRIM_DB, min(MAX_TRIM_DB, desired_trim))
        # Never demand an individual boosted track exceed 2 dB of sample
        # headroom. The existing stereo mixer separately normalizes the master.
        max_safe_gain = PEAK_HEADROOM_DB - metrics["measured_peak_dbfs"]
        next_gain = min(metrics["original_gain_db"] + trim, max_safe_gain)
        if not math.isfinite(next_gain):
            raise ValueError("JAZZ_BALLAD_INVALID_EQUALIZED_GAIN:" + role)
        metrics["balance_adjustment_db"] = round(next_gain - metrics["original_gain_db"], 3)
        metrics["effective_active_rms_dbfs"] = round(
            metrics["measured_active_rms_dbfs"] + next_gain, 3)
        metrics["peak_after_gain_dbfs"] = round(
            metrics["measured_peak_dbfs"] + next_gain, 3)
        new_gains[role] = next_gain

    result = deepcopy(engine_result)
    for row in result["modules"]["target"]["resolved_resources"]:
        role = str(row.get("track_id", "")).upper()
        if role in new_gains:
            row["resource"]["target_gain_db"] = round(new_gains[role], 3)
            row["resource"]["mix_profile"] = PROFILE
    result["jazz_mix_instruction"] = {
        "name": PROFILE,
        "method": "EQUAL_ACTIVE_TRACK_RMS_WITH_PEAK_HEADROOM",
        "target_active_rms_dbfs": round(reference_db, 3),
        "track_measurements": levels,
        "all_six_recorded_stems_present": True,
        "preserve_original_piano_samples": True,
        "preserve_standalone_3d_mixer": True,
        "do_not_claim_equal_perceived_loudness_without_listening": True,
    }
    return result
