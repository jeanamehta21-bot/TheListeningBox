import logging
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
    def __init__(self):
        self.available = False
        self.model = None

        if not BIRDNET_ENABLED:
            logger.info("BirdNET disabled by configuration.")
            return

        try:
            from birdnet.models import ModelV2M4

            self.model = ModelV2M4()
            self.available = True

            logger.info("BirdNET ModelV2M4 loaded.")

        except Exception:
            logger.exception(
                "BirdNET could not load. Recording can continue without it."
            )

    def analyze(self, audio_file):
        if not self.available:
            return []

        audio_path = Path(audio_file)

        if not audio_path.is_file():
            logger.error("BirdNET audio file does not exist: %s", audio_path)
            return []

        try:
            # Only filter by likely local species when explicitly enabled
            # and valid coordinates have been configured.
            use_location_filter = (
                BIRDNET_LOCATION_FILTER
                and LATITUDE is not None
                and LONGITUDE is not None
            )

            if use_location_filter:
                species_in_area = (
                    self.model.predict_species_at_location_and_time(
                        LATITUDE,
                        LONGITUDE,
                        week=1,
                    )
                )

                predictions = (
                    self.model.predict_species_within_audio_file(
                        audio_path,
                        filter_species=set(species_in_area.keys()),
                    )
                )

            else:
                if BIRDNET_LOCATION_FILTER:
                    logger.warning(
                        "BirdNET location filtering is enabled, but "
                        "coordinates are missing. Analyzing without "
                        "location filtering."
                    )

                predictions = (
                    self.model.predict_species_within_audio_file(
                        audio_path
                    )
                )

            results = []

            for interval, prediction_dict in predictions.items():
                if not prediction_dict:
                    continue

                # Save the strongest prediction for each time interval.
                species, confidence = max(
                    prediction_dict.items(),
                    key=lambda item: item[1],
                )

                confidence = float(confidence)

                if confidence < BIRDNET_MIN_CONFIDENCE:
                    continue

                if "_" in species:
                    scientific_name, common_name = species.split("_", 1)
                else:
                    scientific_name = ""
                    common_name = species

                results.append(
                    {
                        "model_name": "BirdNET",
                        "category": "bird",
                        "label": common_name,
                        "species": common_name,
                        "scientific_name": scientific_name,
                        "confidence": confidence,
                        "start_seconds": float(interval[0]),
                        "end_seconds": float(interval[1]),
                    }
                )

            logger.info(
                "BirdNET produced %d detections above confidence %.2f.",
                len(results),
                BIRDNET_MIN_CONFIDENCE,
            )

            return results

        except Exception:
            logger.exception("BirdNET analysis failed for %s", audio_path)
            return []


_backend = None


def analyze_audio(audio_file):
    global _backend

    if _backend is None:
        _backend = BirdNETBackend()

    return _backend.analyze(audio_file)
