"""Regression checks for equal Jazz Ballad instrument intensity."""
from __future__ import annotations

from array import array
from copy import deepcopy
import math
from pathlib import Path
import sys
import tempfile
import unittest
import wave

sys.path.insert(0, str(Path(__file__).resolve().parent))
from genre_styles.Jazz.equal_intensity import (
    REQUIRED, VERSION, active_rms_dbfs, equalize_jazz_ballad
)
from jazz_balance_contract import (
    JAZZ_EXPECTED_INSTRUMENTS, JAZZ_GAIN_TRIMS_DB
)


def write_recorded_like_wav(path: Path, amplitude: float):
    sample_rate = 8000
    samples = array("h")
    # Different musical notes and instrument timbres can vary dynamically.
    # A silence and quiet trail verify that active RMS does not penalize rests.
    for i in range(12000):
        if 1000 <= i < 9000:
            v = amplitude * math.sin(2 * math.pi * (330 + (i // 2000) * 40) * i / sample_rate)
        elif 9000 <= i < 10000:
            v = amplitude * 0.0001
        else:
            v = 0.0
        samples.append(int(round(max(-1, min(1, v)) * 30000)))
    with wave.open(str(path), "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(sample_rate)
        out.writeframes(samples.tobytes())


def test_case(root: Path):
    stems = []
    profiles = []
    resolved = []
    amps = {
        "HARMONY": 0.15, "BASS": 0.04, "LEAD": 0.018,
        "KICK": 0.22, "SNARE": 0.08, "HAT": 0.035,
    }
    for role in sorted(REQUIRED):
        path = root / (role + ".wav")
        write_recorded_like_wav(path, amps[role])
        stems.append({"track_id": role, "wav_path": str(path)})
        profiles.append({
            "track_id": role, "instrument_id": JAZZ_EXPECTED_INSTRUMENTS[role]
        })
        resolved.append({"track_id": role, "resource": {
            "target_gain_db": -6.0 + JAZZ_GAIN_TRIMS_DB[role],
            "jazz_gain_offset_db": JAZZ_GAIN_TRIMS_DB[role],
            "resource_type": "SFZ_SAMPLE_LIBRARY"
        }})
    engine_result = {
        "genre": "Jazz Ballad",
        "modules": {
            "instrument": {"profiles": profiles},
            "target": {"resolved_resources": resolved},
        },
    }
    return engine_result, stems


class EqualJazzIntensityTests(unittest.TestCase):
    def test_six_real_voices_same_active_intensity(self):
        with tempfile.TemporaryDirectory() as folder:
            engine, stems = test_case(Path(folder))
            original = deepcopy(engine)
            data_before = {s["track_id"]: Path(s["wav_path"]).read_bytes() for s in stems}
            mixed = equalize_jazz_ballad(engine, stems)
            self.assertEqual(engine, original)
            self.assertEqual(mixed["jazz_equal_intensity"]["version"], VERSION)
            levels = mixed["jazz_equal_intensity"]["tracks"]
            self.assertEqual(set(levels), REQUIRED)
            self.assertLess(max(s["post_gain_active_rms_dbfs"] for s in levels.values()) -
                            min(s["post_gain_active_rms_dbfs"] for s in levels.values()), 0.05)
            gains = {r["track_id"]: r["resource"]["target_gain_db"]
                     for r in mixed["modules"]["target"]["resolved_resources"]}
            self.assertEqual(gains["HARMONY"], -6.0)
            self.assertGreater(gains["LEAD"], gains["HARMONY"])
            self.assertLess(gains["KICK"], gains["HARMONY"])
            for stem in stems:
                self.assertEqual(Path(stem["wav_path"]).read_bytes(),
                                 data_before[stem["track_id"]])

    def test_missing_part_is_not_mislabeled_as_complete_music(self):
        with tempfile.TemporaryDirectory() as folder:
            engine, stems = test_case(Path(folder))
            with self.assertRaisesRegex(ValueError, "MISSING_WAV"):
                equalize_jazz_ballad(engine, stems[:-1])

    def test_silence_is_reported_not_amplified(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "silent.wav"
            with wave.open(str(path), "wb") as writer:
                writer.setnchannels(1)
                writer.setsampwidth(2)
                writer.setframerate(8000)
                writer.writeframes(bytes(8000 * 2))
            with self.assertRaisesRegex(ValueError, "JAZZ_INSTRUMENT_SILENT"):
                active_rms_dbfs(path)

    def test_rock_and_other_jazz_styles_are_exactly_untouched(self):
        bogus = {"genre": "ROCK"}
        self.assertIs(equalize_jazz_ballad(bogus, []), bogus)
        for name in ("Swing", "Jazz Waltz", "Cool Jazz", "Dixieland", "Bebop", "Big Band", "Jazz Fusion"):
            bogus = {"genre": name}
            self.assertIs(equalize_jazz_ballad(bogus, []), bogus)

    def test_piano_reference_ignores_legacy_static_gain(self):
        with tempfile.TemporaryDirectory() as folder:
            engine, stems = test_case(Path(folder))
            r = equalize_jazz_ballad(engine, stems)
            self.assertEqual(r["jazz_equal_intensity"]["reference"],
                             "HARMONY_WURLITZER_PIANO")
            self.assertTrue(r["jazz_equal_intensity"]["source_audio_untouched"])
            self.assertTrue(r["jazz_equal_intensity"]
                            ["static_presets_replaced_by_recorded_measurements"])


if __name__ == "__main__":
    unittest.main()
