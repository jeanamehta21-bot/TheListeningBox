
"""BirdNET 2.4 adapter for The Listening Box.

BirdNET is optional. If it is disabled, missing, or fails to load,
recording and YAMNet analysis can continue.
"""

import logging
from datetime import date
from pathlib import Path

from config import (
    BIRDNET_ENABLED,
    BIRDNET_MIN_CONFIDENCE,
    BIRDNET_LOCATION_FILTER,
    LATITUDE,
    LONGITUDE,
)

logger = logging.getLogger("listeningbox")


class BirdNETBackend:
    """Lazy-loading adapter for the birdnet Python package."""

    def __init__(self):
        self.available = False
        self.model = None

        if not BIRDNET_ENABLED:
            logger.info("BirdNET disabled by configuration.")
            return

        try:
            # Import only when BirdNET is enabled.
            from birdnet.models import ModelV2M4

            self.model = ModelV2M4()
            self.available = True
            logger.info("BirdNET 2.4 model loaded.")

        except Exception:
            logger.exception(
                "BirdNET could not load. Continuing without BirdNET."
            )

    def _predict(self, audio_path):
        """Run BirdNET and return interval/species predictions."""

        location_filter = (
            BIRDNET_LOCATION_FILTER
            and LATITUDE is not None
            and LONGITUDE is not None
        )

        if location_filter:
            # Use the current calendar week rather than a fixed week.
            week = date.today().isocalendar().week

            try:
                species_in_area = (
                    self.model.predict_species_at_location_and_time(
                        LATITUDE,
                        LONGITUDE,
                        week=week,
                    )
                )

                return self.model.predict_species_within_audio_file(
                    audio_path,
                    filter_species=set(species_in_area.keys()),
                )

            except Exception:
                logger.exception(
                    "Location-filtered BirdNET prediction failed. "
                    "Retrying without location filtering."
                )

        elif BIRDNET_LOCATION_FILTER:
            logger.warning(
                "Location filtering requested, but coordinates are missing. "
                "Analyzing without location filtering."
            )

        return self.model.predict_species_within_audio_file(audio_path)

    def analyze(self, audio_file):
        if not self.available:
            return []

        audio_path = Path(audio_file)

        if not audio_path.is_file():
            logger.error("Audio file does not exist: %s", audio_path)
            return []

        try:
            predictions = self._predict(audio_path)
            results = []

            for interval, species_scores in predictions.items():
                if not species_scores:
                    continue

                # Keep the strongest candidate for each interval.
                species, confidence = max(
                    species_scores.items(),
                    key=lambda item: float(item[1]),
                )

                confidence = float(confidence)

                if confidence < BIRDNET_MIN_CONFIDENCE:
                    continue

                if "_" in species:
                    scientific_name, common_name = species.split("_", 1)
                else:
                    scientific_name = None
                    common_name = species

                start_seconds, end_seconds = interval

                results.append({
                    "model_name": "BirdNET",
                    "category": "bird",
                    "label": common_name,
                    "species": common_name,
                    "scientific_name": scientific_name,
                    "confidence": confidence,
                    "start_seconds": float(start_seconds),
                    "end_seconds": float(end_seconds),
                })

            logger.info(
                "BirdNET saved %d candidates at confidence >= %.2f.",
                len(results),
                BIRDNET_MIN_CONFIDENCE,
            )

            return results

        except Exception:
            logger.exception(
                "BirdNET analysis failed for %s.", audio_path
            )
            return []


_backend = None


def analyze_audio(audio_file):
    """Public entry point used by main.py."""

    global _backend

    if _backend is None:
        _backend = BirdNETBackend()

    return _backend.analyze(audio_file)
