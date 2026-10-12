import argparse
import logging
from datetime import datetime

from birdnet_analyzer import analyze_audio as analyze_birds
from database import initialize_database, save_detection, save_recording
from environmental import read_environment
from process_audio import process_audio
from record_audio import record_audio
from utils import ensure_directories, setup_logging
from yamnet_analyzer import analyze_audio as analyze_environmental_sounds


def run_once():
    logger = logging.getLogger("listeningbox")
    logger.info("Starting recording.")
    started_at = datetime.now()
    audio_file = record_audio()
    logger.info("Recording saved: %s", audio_file)

    processed_info = process_audio(audio_file)
    environment = read_environment(audio_file)
    environment["timestamp"] = started_at.isoformat(timespec="seconds")
    recording_id = save_recording(audio_file, processed_info, environment)

    logger.info(
        "Acoustic measurements: level=%s RMS=%s peak=%s",
        environment["sound_level"], environment["audio_rms"],
        environment["audio_peak"],
    )

    all_detections = []
    # Keep each model independent: one failing must not stop the other.
    for model_name, analyzer in (
        ("YAMNet", analyze_environmental_sounds),
        ("BirdNET", analyze_birds),
    ):
        try:
            detections = analyzer(audio_file, recorded_at=started_at) if model_name == "BirdNET" else analyzer(audio_file)
            for detection in detections or []:
                save_detection(recording_id, detection)
                all_detections.append(detection)
                logger.info(
                    "%s candidate: %s (confidence %.3f)",
                    model_name, detection.get("label"),
                    detection.get("confidence", 0.0),
                )
        except Exception:
            logger.exception("%s analysis failed for %s", model_name, audio_file)

    logger.info("Cycle complete; %d candidate detections saved.", len(all_detections))
    return audio_file, all_detections


def main():
    parser = argparse.ArgumentParser(description="The Listening Box audio pipeline")
    parser.add_argument("--once", action="store_true", help="Record and analyze one clip")
    args = parser.parse_args()
    ensure_directories()
    initialize_database()
    setup_logging()
    if args.once:
        run_once()
    else:
        parser.error("Use --once for a single recording or run scheduler.py for repetition.")


if __name__ == "__main__":
    main()
