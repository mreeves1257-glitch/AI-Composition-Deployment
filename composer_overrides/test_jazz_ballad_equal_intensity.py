"""Measured six-instrument Jazz Ballad balance regressions.

Uses synthetic WAV fixtures ONLY to test the gain-math algorithm: no fake
instruments are inserted in the Composer or in live audio rendering.
"""
from __future__ import annotations
import copy
import tempfile
import unittest
import wave
from pathlib import Path

import numpy as np

from genre_styles.Jazz.jazz_ballad import balance_mix
from genre_styles.Jazz.ballad_leveler import (
    INSTRUMENTS, PROFILE, equalize_ballad_stems, _active_rms_and_peak_db
)


def make_source(path, peak=0.1, sr=16000, zero=False):
    t = np.arange(sr, dtype=np.float64) / sr
    samples = (np.sin(2 * np.pi * 220 * t) * peak if not zero
               else np.zeros(sr))
    pcm = np.round(samples * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def make_engine(stems_path, genre="Jazz Ballad", silent_role=None):
    amplitudes = {
        "HARMONY": 0.35, "LEAD": 0.028, "BASS": 0.10,
        "SNARE": 0.065, "HAT": 0.075, "KICK": 0.115,
    }
    profiles = []
    resources = []
    stems = []
    for role, iid in INSTRUMENTS.items():
        p = stems_path / (role.lower() + ".wav")
        make_source(p, amplitudes[role], zero=(role == silent_role))
        profiles.append({"track_id": role, "instrument_id": iid})
        resources.append({"track_id": role,
                          "resource": {"instrument_id": iid,
                                       "target_gain_db": -6.0,
                                       "resource_type": "SFZ_SAMPLE_LIBRARY"}})
        stems.append({"track_id": role, "wav_path": str(p)})
    return {"genre": genre, "modules": {
        "instrument": {"profiles": profiles},
        "target": {"resolved_resources": resources},
    }}, stems


class JazzEqualIntensityTest(unittest.TestCase):
    def test_all_six_have_equal_active_intensity(self):
        with tempfile.TemporaryDirectory() as folder:
            score, stems = make_engine(Path(folder))
            original = copy.deepcopy(score)
            output = balance_mix(score, stems)
            self.assertEqual(score, original, "MUST_NOT_MUTATE_SOURCE_SCORE")
            self.assertEqual(output["jazz_mix_instruction"]["name"], PROFILE)
            self.assertTrue(output["jazz_mix_instruction"]["all_six_recorded_stems_present"])
            levels = [t["effective_active_rms_dbfs"] for t in
                      output["jazz_mix_instruction"]["track_measurements"].values()]
            self.assertLess(max(levels) - min(levels), 1.2,
                            "All six recorded parts need comparable active level")
            self.assertEqual(len(levels), 6)
            self.assertEqual(set(output["jazz_mix_instruction"]["track_measurements"]),
                             set(INSTRUMENTS))

    def test_preserve_piano_source_and_no_modified_wavs(self):
        with tempfile.TemporaryDirectory() as folder:
            score, stems = make_engine(Path(folder))
            piano = next(x for x in stems if x["track_id"] == "HARMONY")
            before = Path(piano["wav_path"]).read_bytes()
            output = balance_mix(score, stems)
            self.assertEqual(Path(piano["wav_path"]).read_bytes(), before)
            self.assertEqual(output["jazz_mix_instruction"]["preserve_original_piano_samples"], True)
            self.assertTrue(output["jazz_mix_instruction"]["preserve_standalone_3d_mixer"])

    def test_silent_recorded_instrument_fails_not_missing_music(self):
        with tempfile.TemporaryDirectory() as folder:
            score, stems = make_engine(Path(folder), silent_role="LEAD")
            with self.assertRaisesRegex(ValueError, "JAZZ_BALLAD_SILENT_INSTRUMENT:LEAD"):
                equalize_ballad_stems(score, stems)

    def test_missing_audio_stem_fails(self):
        with tempfile.TemporaryDirectory() as folder:
            score, stems = make_engine(Path(folder))
            stems = [x for x in stems if x["track_id"] != "BASS"]
            with self.assertRaisesRegex(ValueError, "JAZZ_BALLAD_MISSING_AUDIO_STEM:BASS"):
                equalize_ballad_stems(score, stems)

    def test_rock_and_other_jazz_unchanged(self):
        with tempfile.TemporaryDirectory() as folder:
            for genre in ("ROCK", "Swing"):
                score, stems = make_engine(Path(folder), genre=genre)
                self.assertIs(balance_mix(score, stems), score)
                self.assertNotIn("jazz_mix_instruction", score)

    def test_active_not_whole_song_silence(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "limited_notes.wav"
            make_source(path, 0.12)
            with wave.open(str(path), "rb") as w:
                params = w.getparams()
                data = w.readframes(w.getnframes())
            with wave.open(str(path), "wb") as w:
                w.setparams(params)
                w.writeframes(data + bytes(len(data) * 3))
            level, peak = _active_rms_and_peak_db(str(path))
            self.assertGreater(level, -30)
            self.assertGreater(peak, level)


if __name__ == "__main__":
    unittest.main()
