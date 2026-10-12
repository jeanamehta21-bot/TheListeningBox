import tempfile
import unittest
import wave
from pathlib import Path

import numpy as np

from yamnet_analyzer import YAMNetBackend


class YAMNetAudioTests(unittest.TestCase):
    def create_wav(self, path, sample_rate, channels=1):
        # Create one second of a 440 Hz test tone.
        count = sample_rate
        times = np.arange(count, dtype=np.float32) / sample_rate
        tone = 0.5 * np.sin(2 * np.pi * 440 * times)

        if channels == 2:
            audio = np.column_stack((tone, tone))
        else:
            audio = tone

        pcm = (audio * 32767).astype("<i2")

        with wave.open(str(path), "wb") as wav:
            wav.setnchannels(channels)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)
            wav.writeframes(pcm.tobytes())

    def test_48000_hz_audio_resamples_to_16000_samples(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "test_48k.wav"
            self.create_wav(path, sample_rate=48000)

            samples = YAMNetBackend._read_mono_16k(path)

            self.assertEqual(len(samples), 16000)
            self.assertEqual(samples.dtype, np.float32)
            self.assertTrue(np.isfinite(samples).all())

    def test_16000_hz_audio_keeps_its_sample_count(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "test_16k.wav"
            self.create_wav(path, sample_rate=16000)

            samples = YAMNetBackend._read_mono_16k(path)

            self.assertEqual(len(samples), 16000)
            self.assertTrue(np.isfinite(samples).all())

    def test_stereo_audio_is_converted_to_mono(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "stereo_48k.wav"
            self.create_wav(
                path, sample_rate=48000, channels=2
            )

            samples = YAMNetBackend._read_mono_16k(path)

            self.assertEqual(len(samples), 16000)
            self.assertEqual(samples.ndim, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
