"""Jazz Ballad-only equal-presence trim over the *existing recorded* stems.

No synthetic audio, replacement recordings, compression, noise-processing, or
changes to the independent spatial mixer. Read the already-rendered WAV stems
and write only their source gain metadata before the normal mixer runs.
Musical intensity is estimated by active-window RMS, not overall silent-bar
RMS or momentary drum peaks. Perceived loudness still requires listening.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import math
import wave

import numpy as np

GENRE = "Jazz Ballad"
VERSION = "JAZZ_BALLAD_EQUAL_ACTIVE_PRESENCE_R1"
ROLES = frozenset(("HARMONY", "LEAD", "BASS", "KICK", "SNARE", "HAT"))
MAX_ADJUST_DB = 16.0
TOLERANCE_DB = 3.0
MIN_PEAK = 1e-6


def _measure_active_rms(path: str | Path) -> dict:
    """Stream the real WAV; return the active-window level, not full-song silence."""
    source = Path(path)
    with wave.open(str(source), "rb") as reader:
        channels = reader.getnchannels()
        width = reader.getsampwidth()
        if channels not in (1, 2) or width not in (1, 2, 4):
            raise ValueError("JAZZ_LEVEL_UNSUPPORTED_WAV_FORMAT")
        chunks = []
        max_abs = 0.0
        while True:
            raw = reader.readframes(8192)
            if not raw:
                break
            if width == 1:
                samples = (np.frombuffer(raw, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0
            elif width == 2:
                samples = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
            else:
                samples = np.frombuffer(raw, dtype="<i4").astype(np.float32) / 2147483648.0
            if not len(samples) or len(samples) % channels:
                raise ValueError("JAZZ_LEVEL_UNALIGNED_WAV")
            samples = samples.reshape(-1, channels)
            power = float(np.mean(samples.astype(np.float64) ** 2))
            chunks.append(math.sqrt(power))
            max_abs = max(max_abs, float(np.max(np.abs(samples))))
    if not chunks or max_abs < MIN_PEAK:
        raise ValueError("JAZZ_LEVEL_SILENT_INSTRUMENT:" + str(source))
    peak_window = max(chunks)
    # Exclude near-silence and decay tails. This is especially important for
    # sparse brushes, acoustic bass and clarinet; otherwise boosts hiss.
    active = sorted(v for v in chunks if v >= max(0.16 * peak_window, MIN_PEAK))
    if not active:
        raise ValueError("JAZZ_LEVEL_NO_ACTIVE_INSTRUMENT:" + str(source))
    # Upper half of the musical windows: robust against rests/short note fades.
    upper = active[len(active) // 2:]
    level = math.sqrt(sum(v * v for v in upper) / len(upper))
    return {
        "active_rms_dbfs": 20.0 * math.log10(level),
        "peak_dbfs": 20.0 * math.log10(max_abs),
        "active_windows": len(active),
    }


def match_jazz_ballad_presence(engine_result: dict, stems: list[dict]) -> dict:
    """Copy only Jazz Ballad's six role gains; measured acoustic source untouched.

    Choose the median post-baseline active RMS of the six actual instruments,
    rather than privileging the piano or clarinet. Return diagnostics so the
    measured result can be audited and a missing part is never called 'ready'.
    """
    if not isinstance(engine_result, dict) or engine_result.get("genre") != GENRE:
        return engine_result
    if not isinstance(stems, list):
        raise ValueError("JAZZ_LEVEL_STEMS_REQUIRED")
    modules = engine_result.get("modules", {})
    target = modules.get("target", {})
    instrument = modules.get("instrument", {})
    resources = target.get("resolved_resources")
    profiles = instrument.get("profiles")
    if not isinstance(resources, list) or not isinstance(profiles, list):
        raise ValueError("JAZZ_LEVEL_TARGET_RESOURCES_MISSING")
    by_track = {str(s["track_id"]).upper(): s for s in stems
                if isinstance(s, dict) and "track_id" in s and "wav_path" in s}
    bindings = {str(s["track_id"]).upper(): s for s in resources
                if isinstance(s, dict) and "track_id" in s}
    profiles_by_track = {str(p["track_id"]).upper(): p for p in profiles
                         if isinstance(p, dict) and "track_id" in p}
    measured = {}
    for track in sorted(ROLES):
        if track not in by_track or track not in bindings or track not in profiles_by_track:
            raise ValueError("JAZZ_LEVEL_ROLE_MISSING:" + track)
        resource = bindings[track].get("resource")
        if not isinstance(resource, dict) or resource.get("resource_type") != "SFZ_SAMPLE_LIBRARY":
            raise ValueError("JAZZ_LEVEL_RECORDED_RESOURCE_MISSING:" + track)
        previous_gain = resource.get("target_gain_db", 0.0)
        if not isinstance(previous_gain, (int, float)) or not math.isfinite(float(previous_gain)):
            raise ValueError("JAZZ_LEVEL_GAIN_INVALID:" + track)
        measured[track] = {
            **_measure_active_rms(by_track[track]["wav_path"]),
            "baseline_gain_db": float(previous_gain),
            "instrument_id": profiles_by_track[track].get("instrument_id"),
        }
        measured[track]["baseline_postgain_dbfs"] = (
            measured[track]["active_rms_dbfs"] + measured[track]["baseline_gain_db"])
    levels = sorted(x["baseline_postgain_dbfs"] for x in measured.values())
    desired = (levels[2] + levels[3]) / 2.0
    updated = []
    diagnostics = {}
    for record in resources:
        track = str(record.get("track_id", "")).upper()
        if track not in measured:
            updated.append(record)
            continue
        old = record["resource"]
        raw_delta = desired - measured[track]["baseline_postgain_dbfs"]
        # Protect against outlier/silent sources. Don't inflate faint noisy
        # brush recordings by 30 dB merely to equal an accompaniment chord.
        delta = max(-MAX_ADJUST_DB, min(MAX_ADJUST_DB, raw_delta))
        next_resource = dict(old)
        next_resource["target_gain_db"] = measured[track]["baseline_gain_db"] + delta
        next_resource["jazz_presence_adjust_db"] = round(delta, 2)
        next_resource["jazz_presence_profile"] = VERSION
        updated.append({**record, "resource": next_resource})
        diagnostics[track] = {
            **measured[track],
            "presence_adjust_db": round(delta, 2),
            "estimated_postgain_active_dbfs": round(
                measured[track]["baseline_postgain_dbfs"] + delta, 2),
            "trim_limit_reached": abs(raw_delta) > MAX_ADJUST_DB,
        }
    return {
        **engine_result,
        "modules": {**modules, "target": {**target, "resolved_resources": updated}},
        "jazz_equal_presence": {
            "name": VERSION,
            "target_active_dbfs": round(desired, 2),
            "tracks": diagnostics,
            "measurement": "GATED_WAV_ACTIVE_RMS_NOT_PSYCHOACOUSTIC_LOUDNESS",
            "audio_sources_unchanged": True,
            "other_genres_unchanged": True,
        },
    }
