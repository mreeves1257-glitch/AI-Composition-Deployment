"""Jazz Ballad-only equal instrument *active* intensity from actual recorded stems.

The Wurlitzer is the stable reference; raw WAV/SFZ recordings, note velocity,
performance envelopes, stereo placement and the standalone 3D mixer stay
untouched. All six real stems are matched by their non-silent audio energy,
not by synthetic presets or full-song RMS (which penalizes musical rests).
"""
from __future__ import annotations

from array import array
from copy import deepcopy
import math
from pathlib import Path
import sys
import wave

VERSION = "JAZZ_BALLAD_EQUAL_ACTIVE_INTENSITY_R1"
REQUIRED = frozenset(("HARMONY", "BASS", "LEAD", "KICK", "SNARE", "HAT"))
WINDOW_FRAMES = 4096
GATE_RELATIVE_DB = 24.0
GATE_FLOOR_DBFS = -58.0
MAX_CORRECTION_DB = 30.0

def _pcm_chunk_level(raw: bytes, sample_width: int) -> float:
    """Channel-averaged RMS; no in-place processing of recorded audio."""
    if sample_width == 1:
        samples = [x - 128 for x in raw]
        denominator = 128.0
    elif sample_width in (2, 4):
        samples = array("h" if sample_width == 2 else "i")
        samples.frombytes(raw)
        if sys.byteorder != "little":
            samples.byteswap()
        denominator = 32768.0 if sample_width == 2 else 2147483648.0
    elif sample_width == 3:
        samples = []
        for i in range(0, len(raw), 3):
            word = int.from_bytes(raw[i:i+3], "little", signed=False)
            samples.append(word - 16777216 if word & 0x800000 else word)
        denominator = 8388608.0
    else:
        raise ValueError("JAZZ_INTENSITY_UNSUPPORTED_PCM_WIDTH")
    if not samples:
        return 0.0
    squares = sum(int(x) * int(x) for x in samples)
    return math.sqrt(squares / len(samples)) / denominator

def active_rms_dbfs(wav_path: str | Path) -> tuple[float, int]:
    """Calculate gated RMS of active ~93ms windows, preserving rests.

    Gate is relative to the loudest recorded window, with a hard low-level
    floor to exclude noise-only tails. Never edits audio bytes.
    """
    path = Path(wav_path)
    if not path.is_file():
        raise ValueError("JAZZ_INSTRUMENT_WAV_MISSING:" + path.name)
    with wave.open(str(path), "rb") as reader:
        width = reader.getsampwidth()
        channels = reader.getnchannels()
        if (reader.getcomptype() != "NONE" or channels not in (1, 2)
                or reader.getnframes() <= 0 or width not in (1, 2, 3, 4)):
            raise ValueError("JAZZ_INSTRUMENT_WAV_UNSUPPORTED:" + path.name)
        levels = []
        while True:
            raw = reader.readframes(WINDOW_FRAMES)
            if not raw:
                break
            levels.append(_pcm_chunk_level(raw, width))
    if not levels or max(levels) <= 1e-7:
        raise ValueError("JAZZ_INSTRUMENT_SILENT:" + path.name)
    ceiling = max(levels)
    gate = max(10.0 ** (GATE_FLOOR_DBFS / 20.0),
               ceiling * 10.0 ** (-GATE_RELATIVE_DB / 20.0))
    active = [level for level in levels if level >= gate]
    if not active:
        raise ValueError("JAZZ_INSTRUMENT_NO_ACTIVE_AUDIO:" + path.name)
    rms = math.sqrt(sum(level*level for level in active) / len(active))
    return 20.0 * math.log10(rms), len(active)

def equalize_jazz_ballad(engine_result: dict, stems: list[dict]) -> dict:
    """Set every Jazz instrument to piano's measured active intensity.

    The baseline piano gain stays fixed; other gains are determined from
    recorded WAV energy. Existing precomputed/static jazz trim is removed
    first, so this does not compound prior adjustments. Non-Ballad results
    are returned by identity with no audio inspection or effect.
    """
    if not isinstance(engine_result, dict) or engine_result.get("genre") != "Jazz Ballad":
        return engine_result

    modules = engine_result["modules"]
    profiles = {str(p["track_id"]).upper(): p for p in
                modules["instrument"]["profiles"]}
    bindings = {str(x["track_id"]).upper(): x for x in
                modules["target"]["resolved_resources"]}
    waveforms = {str(s["track_id"]).upper(): s for s in stems}
    for title, collection in (("PROFILE", profiles), ("RESOURCE", bindings),
                              ("WAV", waveforms)):
        missing = REQUIRED.difference(collection)
        if missing:
            raise ValueError("JAZZ_EQUAL_INTENSITY_MISSING_" + title + ":" +
                             ",".join(sorted(missing)))
    from jazz_balance_contract import JAZZ_EXPECTED_INSTRUMENTS
    for track in REQUIRED:
        if profiles[track].get("instrument_id") != JAZZ_EXPECTED_INSTRUMENTS[track]:
            raise ValueError("JAZZ_EQUAL_INTENSITY_INSTRUMENT_MISMATCH:" + track)

    measured = {track: active_rms_dbfs(waveforms[track]["wav_path"])[0]
                for track in sorted(REQUIRED)}
    # The piano's recorded sound and established source gain are the reference.
    piano = bindings["HARMONY"]["resource"]
    piano_gain = float(piano.get("target_gain_db", 0.0)) - float(
        piano.get("jazz_gain_offset_db", 0.0))
    if not math.isfinite(piano_gain):
        raise ValueError("JAZZ_INTENSITY_INVALID_PIANO_GAIN")
    target = measured["HARMONY"] + piano_gain
    changed = []
    report = {}
    for track in sorted(REQUIRED):
        item = bindings[track]
        old = item["resource"]
        prior = float(old.get("target_gain_db", 0.0))
        static_offset = float(old.get("jazz_gain_offset_db", 0.0))
        original = prior - static_offset
        desired = target - measured[track]
        if not (math.isfinite(desired) and math.isfinite(original)):
            raise ValueError("JAZZ_INTENSITY_INVALID_RESOURCE_GAIN:" + track)
        delta = desired - original
        if abs(delta) > MAX_CORRECTION_DB:
            raise ValueError("JAZZ_INTENSITY_GAIN_EXCEEDS_SAFE_LIMIT:" + track)
        gain = dict(old)
        gain["target_gain_db"] = round(desired, 5)
        gain["jazz_gain_offset_db"] = round(delta, 5)
        gain["mix_profile"] = VERSION
        changed.append({**item, "resource": gain})
        report[track] = {
            "recorded_active_rms_dbfs": round(measured[track], 2),
            "gain_db": round(desired, 2),
            "post_gain_active_rms_dbfs": round(measured[track] + desired, 2),
            "basis": "ACTUAL_RECORDED_ACTIVE_WINDOWS",
        }
    if max(r["post_gain_active_rms_dbfs"] for r in report.values()) - min(
            r["post_gain_active_rms_dbfs"] for r in report.values()) > 0.05:
        raise ValueError("JAZZ_INTENSITY_EQUALIZATION_CHECK_FAILED")
    result = dict(engine_result)
    result["modules"] = {
        **modules,
        "target": {**modules["target"], "resolved_resources": [
            next((new for new in changed if new["track_id"] == item["track_id"]), item)
            for item in modules["target"]["resolved_resources"]
        ]},
    }
    result["jazz_equal_intensity"] = {
        "version": VERSION,
        "reference": "HARMONY_WURLITZER_PIANO",
        "target_active_rms_dbfs": round(target, 2),
        "source_audio_untouched": True,
        "static_presets_replaced_by_recorded_measurements": True,
        "tracks": report,
    }
    return result
