"""Local source-level and isolation tests for Jazz Ballad's measured mix."""
from __future__ import annotations

import hashlib
import math
import struct
import tempfile
import unittest
import wave
from pathlib import Path

from genre_styles.Jazz.jazz_ballad import balance_mix
from genre_styles.Jazz.leveling import _measure_active_rms, ROLES


INSTRUMENTS = {
    "LEAD": "clarinet_bb",
    "BASS": "double_bass",
    "HARMONY": "electric_piano",
    "KICK": "kick_drum_rock",
    "SNARE": "snare_drum",
    "HAT": "hi_hat",
}
AMPLITUDES = {
    "LEAD": 0.04, "BASS": 0.06, "HARMONY": 0.09,
    "KICK": 0.13, "SNARE": 0.12, "HAT": 0.11,
}


def write_recording(path: Path, amplitude: float) -> None:
    """Synthetic fixtures test math only; production uses existing real SFZ WAV."""
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(16000)
        for chunk in range(6):
            pcm = []
            for i in range(1600):
                frame = chunk * 1600 + i
                level = amplitude if chunk < 3 else 0.0
                value = int(32767 * level * math.sin(2 * math.pi * 247.0 * frame / 16000))
                pcm.append(value)
            output.writeframesraw(struct.pack("<" + "h" * len(pcm), *pcm))


class JazzEqualPresenceTests(unittest.TestCase):
    def test_all_six_active_roles_match_and_preserve_recordings(self):
        with tempfile.TemporaryDirectory() as directory:
            profiles = [{"track_id": role, "instrument_id": INSTRUMENTS[role]}
                        for role in sorted(ROLES)]
            resolved = [{"track_id": role, "resource": {
                "resource_type": "SFZ_SAMPLE_LIBRARY", "target_gain_db": -6.0,
                "resource_id": "PINNED_TEST_RECORDING",
            }} for role in sorted(ROLES)]
            score = {"genre": "Jazz Ballad",
                     "modules": {"instrument": {"profiles": profiles},
                                 "target": {"resolved_resources": resolved}}}
            stems = []
            original_hashes = {}
            for role in sorted(ROLES):
                path = Path(directory) / (role + ".wav")
                write_recording(path, AMPLITUDES[role])
                original_hashes[role] = hashlib.sha256(path.read_bytes()).hexdigest()
                stems.append({"track_id": role, "wav_path": str(path)})
            mixed = balance_mix(score, stems=stems)
            self.assertEqual(len(mixed["jazz_equal_presence"]["tracks"]), 6)
            postlevels = [x["estimated_postgain_active_dbfs"]
                          for x in mixed["jazz_equal_presence"]["tracks"].values()]
            self.assertLessEqual(max(postlevels) - min(postlevels), 3.1)
            self.assertFalse(any(x["trim_limit_reached"] for x in
                                 mixed["jazz_equal_presence"]["tracks"].values()))
            for role in ROLES:
                path = Path(directory) / (role + ".wav")
                self.assertEqual(original_hashes[role],
                                 hashlib.sha256(path.read_bytes()).hexdigest())
            self.assertEqual(resolved[0]["resource"]["target_gain_db"], -6.0)
            self.assertNotIn("jazz_equal_presence", score)

    def test_rock_is_unmodified_even_if_stems_present(self):
        original = {"genre": "ROCK", "modules": {}}
        self.assertIs(balance_mix(original, stems=[]), original)

    def test_missing_track_rejected_instead_of_fake_ready(self):
        score = {
            "genre": "Jazz Ballad",
            "modules": {
                "instrument": {"profiles": [
                    {"track_id": r, "instrument_id": iid} for r, iid in INSTRUMENTS.items()
                ]},
                "target": {"resolved_resources": [
                    {"track_id": r, "resource": {
                        "resource_type": "SFZ_SAMPLE_LIBRARY", "target_gain_db": 0
                    }} for r in INSTRUMENTS
                ]},
            },
        }
        with self.assertRaisesRegex(ValueError, "JAZZ_LEVEL_ROLE_MISSING"):
            balance_mix(score, stems=[])

    def test_silent_source_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "empty.wav"
            with wave.open(str(path), "wb") as output:
                output.setnchannels(1)
                output.setsampwidth(2)
                output.setframerate(16000)
                output.writeframes(b"\\x00\\x00" * 8000)
            with self.assertRaisesRegex(ValueError, "JAZZ_LEVEL_SILENT_INSTRUMENT"):
                _measure_active_rms(path)


if __name__ == "__main__":
    unittest.main()
