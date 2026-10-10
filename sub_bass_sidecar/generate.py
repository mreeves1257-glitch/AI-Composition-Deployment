"""Standalone, optional synthesized sub-bass WAV stem for AI Composer.

Separate from recorded instruments, genre folders and the existing 3D mixer.
This module is NOT connected to production by itself. Requires explicit events.
Only numpy (already used by the Composer build) and Python stdlib are required.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import tempfile
import wave
from pathlib import Path

import numpy as np

VERSION = "SUB_BASS_SIDECAR_001"
BLOCK_FRAMES = 8192
ALLOWED_SAMPLE_RATES = (44100, 48000)


def _real(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name}_MUST_BE_NUMERIC")
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{name}_MUST_BE_FINITE")
    return value


def _between(value, name, low, high):
    number = _real(value, name)
    if not low <= number <= high:
        raise ValueError(f"{name}_OUT_OF_RANGE_{low}_TO_{high}")
    return number


def validate_request(request):
    if not isinstance(request, dict):
        raise ValueError("SUB_BASS_REQUEST_MUST_BE_OBJECT")
    if request.get("enabled") is not True:
        raise ValueError("SUB_BASS_EXPLICIT_ENABLE_REQUIRED")
    rate = request.get("sample_rate", 44100)
    if isinstance(rate, bool) or rate not in ALLOWED_SAMPLE_RATES:
        raise ValueError("SUB_BASS_UNSUPPORTED_SAMPLE_RATE")
    duration = _between(request.get("duration_seconds"), "duration_seconds", 0.1, 600)
    level = _between(request.get("level_dbfs", -21), "level_dbfs", -48, -12)
    attack = _between(request.get("attack_ms", 6), "attack_ms", 2, 50) / 1000
    release = _between(request.get("release_ms", 120), "release_ms", 30, 600) / 1000
    events = request.get("events")
    if not isinstance(events, list) or not 1 <= len(events) <= 10000:
        raise ValueError("SUB_BASS_EVENTS_REQUIRED_1_TO_10000")

    parsed = []
    for i, event in enumerate(events):
        if not isinstance(event, dict):
            raise ValueError(f"SUB_BASS_EVENT_{i}_INVALID")
        start = _between(event.get("start_seconds"), "start_seconds", 0, duration)
        hold = _between(event.get("duration_seconds", 0.30),
                        "event_duration_seconds", 0.04, 10)
        frequency = _between(event.get("frequency_hz", 45),
                             "frequency_hz", 20, 80)
        sweep = _between(event.get("sweep_hz", 0), "sweep_hz", 0, 70)
        if frequency + sweep > 120:
            raise ValueError("SUB_BASS_SWEEP_EXCEEDS_120_HZ")
        velocity = _between(event.get("velocity", 1),
                            "velocity", 0, 1)
        parsed.append({
            "start_frame": round(start * rate),
            "stop_frame": min(round(duration * rate),
                              round((start + hold + release) * rate)),
            "frequency_hz": frequency,
            "sweep_hz": sweep,
            "hold_seconds": hold,
            "velocity": velocity,
        })
    return {
        "sample_rate": rate,
        "duration_seconds": duration,
        "total_frames": round(duration * rate),
        "level_dbfs": level,
        "attack_seconds": attack,
        "release_seconds": release,
        "events": sorted(parsed, key=lambda e: e["start_frame"]),
    }


def synthesize(request, wav_path, manifest_path=None):
    """Generate mono PCM16 safely in small blocks; never edit any source track."""
    c = validate_request(request)
    destination = Path(wav_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FileExistsError("SUB_BASS_OUTPUT_EXISTS_REFUSE_OVERWRITE")
    temp_path = None
    amplitude = 10.0 ** (c["level_dbfs"] / 20.0)
    peak = 0.0
    try:
        with tempfile.NamedTemporaryFile(dir=destination.parent,
                                         prefix=".sub-bass-",
                                         suffix=".wav", delete=False) as tmp:
            temp_path = Path(tmp.name)
        with wave.open(str(temp_path), "wb") as writer:
            writer.setnchannels(1)
            writer.setsampwidth(2)
            writer.setframerate(c["sample_rate"])
            for left in range(0, c["total_frames"], BLOCK_FRAMES):
                right = min(left + BLOCK_FRAMES, c["total_frames"])
                block = np.zeros(right - left, dtype=np.float64)
                for e in c["events"]:
                    if e["start_frame"] >= right:
                        break
                    if e["stop_frame"] <= left or e["velocity"] == 0:
                        continue
                    lo = max(left, e["start_frame"])
                    hi = min(right, e["stop_frame"])
                    if lo >= hi:
                        continue
                    t = np.arange(lo - e["start_frame"],
                                  hi - e["start_frame"],
                                  dtype=np.float64) / c["sample_rate"]
                    attack = np.minimum(1, t / c["attack_seconds"])
                    release = np.clip((e["hold_seconds"] +
                                       c["release_seconds"] - t) /
                                      c["release_seconds"], 0, 1)
                    envelope = attack * release
                    # Frequency starts at f+sweep and smoothly descends toward f.
                    tau = 0.08
                    phase_cycles = (e["frequency_hz"] * t +
                                    e["sweep_hz"] * tau *
                                    (-np.expm1(-t / tau)))
                    block[lo - left:hi - left] += (
                        amplitude * e["velocity"] * envelope *
                        np.sin(2 * math.pi * phase_cycles))
                local_peak = float(np.max(np.abs(block))) if block.size else 0
                peak = max(peak, local_peak)
                if peak >= 0.98:
                    raise ValueError("SUB_BASS_PEAK_TOO_HIGH_ADJUST_LEVEL_OR_EVENTS")
                pcm = np.rint(block * 32767.0).astype("<i2")
                writer.writeframes(pcm.tobytes())
        os.replace(temp_path, destination)
        temp_path = None
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)

    # Deliberately not a recorded SFZ instrument. Not a drop-in mixer manifest.
    manifest = {
        "module": VERSION,
        "source_type": "SYNTHETIC_OSCILLATOR",
        "track_id": "SUB_BASS_SIDECAR",
        "wav_path": str(destination.resolve()),
        "sample_rate": c["sample_rate"],
        "duration_seconds": c["duration_seconds"],
        "frames": c["total_frames"],
        "event_count": len(c["events"]),
        "peak_dbfs": round(20 * math.log10(max(peak, 1e-12)), 2),
        "stage": "PARALLEL_AUDIO_STEM_AFTER_GENRE_INTERPRETATION",
        "connected_to_live_pipeline": False,
        "mixer_compatibility": "NOT_YET_VALIDATED",
        "original_instruments_modified": False,
    }
    if manifest_path is not None:
        path = Path(manifest_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            raise FileExistsError("SUB_BASS_MANIFEST_EXISTS_REFUSE_OVERWRITE")
        path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def main():
    parser = argparse.ArgumentParser(description="Independent sub-bass WAV sidecar")
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--wav", type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    request = json.loads(args.request.read_text(encoding="utf-8"))
    print(json.dumps(synthesize(request, args.wav, args.manifest), indent=2))


if __name__ == "__main__":
    main()
