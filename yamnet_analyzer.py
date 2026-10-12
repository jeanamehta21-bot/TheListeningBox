
"""Optional YAMNet general environmental sound classifier."""

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
        self.tf = None

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
                class_map_path,
                newline="",
                encoding="utf-8",
            ) as handle:
                self.class_names = [
                    row["display_name"]
                    for row in csv.DictReader(handle)
                ]

            if not self.class_names:
                raise RuntimeError("YAMNet returned an empty class map.")

            self.available = True
            logger.info("YAMNet model loaded.")

        except Exception:
            logger.exception(
                "YAMNet could not load; continuing without YAMNet."
            )
            self.available = False
            self.model = None

    @staticmethod
    def _read_mono_16k(audio_file):
        """Read 16-bit PCM WAV and convert it to mono 16 kHz audio."""
        import numpy as np

        with wave.open(str(Path(audio_file)), "rb") as wav:
            channels = wav.getnchannels()
            width = wav.getsampwidth()
            rate = wav.getframerate()
            frame_count = wav.getnframes()
            raw = wav.readframes(frame_count)

        if channels < 1:
            raise ValueError("Audio file has an invalid channel count.")

        if width != 2:
            raise ValueError("YAMNet requires 16-bit PCM WAV audio.")

        if rate not in (16000, 48000):
            raise ValueError(
                f"Unsupported sample rate {rate}; use 16000 or 48000 Hz."
            )

        samples = (
            np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
        )

        if samples.size == 0:
            raise ValueError("Audio file contains no samples.")

        if samples.size % channels != 0:
            raise ValueError("Audio data is incomplete for its channel count.")

        if channels > 1:
            samples = samples.reshape(-1, channels).mean(axis=1)

        if rate == 48000:
            from scipy.signal import resample_poly

            samples = resample_poly(
                samples,
                up=1,
                down=3,
            ).astype(np.float32)

        if samples.size == 0:
            raise ValueError("Audio is empty after sample-rate conversion.")

        return samples

    def analyze(self, audio_file):
        if not self.available:
            return []

        try:
            waveform = self._read_mono_16k(audio_file)
            tensor = self.tf.convert_to_tensor(waveform)
            scores, _, _ = self.model(tensor)
            scores = scores.numpy()

            if scores.size == 0 or scores.ndim != 2:
                logger.warning("YAMNet returned no usable sound scores.")
                return []

            if scores.shape[1] != len(self.class_names):
                raise RuntimeError(
                    "YAMNet scores do not match the class-name list."
                )

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
            logger.exception("YAMNet analysis failed for %s.", audio_file)
            return []


def analyze_audio(audio_file):
    """Public entry point used by main.py."""
    global _backend

    if _backend is None:
        _backend = YAMNetBackend()

    return _backend.analyze(audio_file)
