"""Optional YAMNet environmental classifier.

Install its dependencies separately. TensorFlow may be too heavy for a
Raspberry Pi 3, so develop and test on a computer first.
This adapter accepts 16-bit PCM WAV audio.
"""

import csv
import logging
import wave
from pathlib import Path

from config import (
    YAMNET_ENABLED,
    YAMNET_MIN_CONFIDENCE,
    YAMNET_MODEL_URL,
)

logger = logging.getLogger("listeningbox")
_backend = None


class YAMNetBackend:
    def __init__(self):
        self.available = False
        self.model = None
        self.class_names = []

        if not YAMNET_ENABLED:
            logger.info("YAMNet disabled by configuration.")
            return

        try:
            import tensorflow as tf
            import tensorflow_hub as hub

            self.tf = tf
            self.model = hub.load(YAMNET_MODEL_URL)

            class_map_path = (
                self.model.class_map_path().numpy().decode("utf-8")
            )

            with open(
                class_map_path, newline="", encoding="utf-8"
            ) as handle:
                self.class_names = [
                    row["display_name"]
                    for row in csv.DictReader(handle)
                ]

            self.available = True
            logger.info("YAMNet model loaded.")

        except Exception:
            logger.exception(
                "YAMNet unavailable; recording can continue."
            )

    @staticmethod
    def _read_mono_16k(audio_file):
        import numpy as np

        with wave.open(str(Path(audio_file)), "rb") as wav:
            channels = wav.getnchannels()
            width = wav.getsampwidth()
            rate = wav.getframerate()
            raw = wav.readframes(wav.getnframes())

        if width != 2:
            raise ValueError("YAMNet input must be 16-bit PCM WAV.")

        samples = (
            np.frombuffer(raw, dtype="<i2").astype(np.float32)
            / 32768.0
        )

        # Convert stereo to mono before resampling.
        if channels > 1:
            samples = samples.reshape(-1, channels).mean(axis=1)

        if rate == 48000:
            # Proper filtered conversion from 48 kHz to 16 kHz.
            from scipy.signal import resample_poly

            samples = resample_poly(
                samples, up=1, down=3
            ).astype(np.float32)

        elif rate != 16000:
            raise ValueError(
                f"Unsupported sample rate {rate}; "
                "use 16000 or 48000 Hz."
            )

        return samples

    def analyze(self, audio_file):
        if not self.available:
            return []

        try:
            waveform = self._read_mono_16k(audio_file)

            scores, _, _ = self.model(
                self.tf.convert_to_tensor(waveform)
            )
            scores = scores.numpy()

            if scores.size == 0:
                return []

            # Rank sound classes by their average score across the clip.
            mean_scores = scores.mean(axis=0)
            ranked = mean_scores.argsort()[::-1][:10]

            results = []

            for index in ranked:
                confidence = float(mean_scores[index])

                if confidence < YAMNET_MIN_CONFIDENCE:
                    continue

                results.append({
                    "model_name": "YAMNet",
                    "category": "environmental",
                    "label": self.class_names[index],
                    "scientific_name": None,
                    "confidence": confidence,
                    "start_seconds": None,
                    "end_seconds": None,
                })

            return results

        except Exception:
            logger.exception("YAMNet analysis failed.")
            return []


def analyze_audio(audio_file):
    global _backend

    if _backend is None:
        _backend = YAMNetBackend()

    return _backend.analyze(audio_file)
