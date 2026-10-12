import tempfile
import unittest
import wave
from pathlib import Path

import numpy as np

from environmental import read_environment


class EnvironmentalAudioTests(unittest.TestCase):
    def create_wav(self, path, amplitude, sample_rate=16000):
        """Create a one-second, 16-bit mono test recording."""
        samples = np.full(
            sample_rate,
            amplitude,
            dtype="<i2",
        )

        with wave.open(str(path), "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)
            wav.writeframes(samples.tobytes())

    def test_quiet_audio_is_measured(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "quiet.wav"
            self.create_wav(path, amplitude=100)

            result = read_environment(path)

            self.assertEqual(result["audio_rms"], 100.0)
            self.assertEqual(result["audio_peak"], 100)
            self.assertEqual(result["sound_level"], "very quiet")

    def test_louder_audio_is_measured(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "loud.wav"
            self.create_wav(path, amplitude=6000)

            result = read_environment(path)

            self.assertEqual(result["audio_rms"], 6000.0)
            self.assertEqual(result["audio_peak"], 6000)
            self.assertEqual(result["sound_level"], "loud")

    def test_missing_recording_does_not_crash(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "missing.wav"

            result = read_environment(path)

            self.assertIsNone(result["audio_rms"])
            self.assertIsNone(result["audio_peak"])
            self.assertEqual(result["sound_level"], "unknown")

    def test_timestamp_is_provided(self):
        result = read_environment()

        self.assertIsInstance(result["timestamp"], str)
        self.assertTrue(result["timestamp"])

    def test_empty_recording_has_no_audio_measurements(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "empty.wav"

            with wave.open(str(path), "wb") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(16000)

            result = read_environment(path)

            self.assertIsNone(result["audio_rms"])
            self.assertIsNone(result["audio_peak"])
            self.assertEqual(result["sound_level"], "unknown")


if __name__ == "__main__":
    unittest.main(verbosity=2)
