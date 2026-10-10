"""Local-only tests; no production connections."""
import tempfile
import unittest
import wave
from pathlib import Path

try:
    from .generate import synthesize
except ImportError:
    from generate import synthesize


class TestSubBass(unittest.TestCase):
    def request(self):
        return {
            "enabled": True,
            "sample_rate": 44100,
            "duration_seconds": 1,
            "level_dbfs": -24,
            "events": [{"start_seconds": 0.1,
                        "duration_seconds": 0.25,
                        "frequency_hz": 40,
                        "sweep_hz": 20}],
        }

    def test_render_metadata(self):
        with tempfile.TemporaryDirectory() as folder:
            audio = Path(folder) / "sidecar.wav"
            info = synthesize(self.request(), audio)
            self.assertEqual(info["source_type"], "SYNTHETIC_OSCILLATOR")
            self.assertFalse(info["connected_to_live_pipeline"])
            with wave.open(str(audio), "rb") as wav:
                self.assertEqual(wav.getframerate(), 44100)
                self.assertEqual(wav.getnframes(), 44100)
                self.assertEqual(wav.getnchannels(), 1)
                self.assertEqual(wav.getsampwidth(), 2)
                self.assertNotEqual(wav.readframes(44100), bytes(2 * 44100))

    def test_refuse_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            audio = Path(folder) / "sidecar.wav"
            audio.write_bytes(b"keep-me")
            with self.assertRaises(FileExistsError):
                synthesize(self.request(), audio)
            self.assertEqual(audio.read_bytes(), b"keep-me")

    def test_requires_explicit_opt_in(self):
        with tempfile.TemporaryDirectory() as folder:
            request = self.request()
            request.pop("enabled")
            with self.assertRaises(ValueError):
                synthesize(request, Path(folder) / "unused.wav")


if __name__ == "__main__":
    unittest.main()
