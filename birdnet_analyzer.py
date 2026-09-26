import logging
from pathlib import Path
from config import (
    BIRDNET_ENABLED,
    BIRDNET_MIN_CONFIDENCE,
    LATITUDE,
    LONGITUDE,
)

logger = logging.getLogger("listeningbox")

class BirdNETBackend:
    def __init__(self):
        self.available = False
        self.model = None

        if not BIRDNET_ENABLED:
            return

        try:
            from birdnet.models import ModelV2M4
            self.model = ModelV2M4()
            self.available = True
            logger.info("BirdNET ModelV2M4 loaded.")
        except Exception as exc:
            logger.warning(
                "BirdNET unavailable; recording continues without AI: %s",
                exc,
            )

    def analyze(self, audio_file):
        if not self.available:
            return []

        try:
            species_in_area = (
                self.model.predict_species_at_location_and_time(
                    LATITUDE, LONGITUDE, week=1
                )
            )

            predictions = self.model.predict_species_within_audio_file(
                Path(audio_file),
                filter_species=set(species_in_area.keys()),
            )

            results = []

            for interval, prediction_dict in predictions.items():
                if not prediction_dict:
                    continue

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

                results.append({
                    "species": common_name,
                    "scientific_name": scientific_name,
                    "confidence": confidence,
                    "start_seconds": float(interval[0]),
                    "end_seconds": float(interval[1]),
                })

            return results

        except Exception as exc:
            logger.exception("BirdNET analysis failed: %s", exc)
            return []

_backend = None

def analyze_audio(audio_file):
    global _backend
    if _backend is None:
        _backend = BirdNETBackend()
    return _backend.analyze(audio_file)
