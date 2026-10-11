
import argparse
import logging
from datetime import datetime

from birdnet_analyzer import analyze_audio
from database import initialize_database, save_detection, save_recording
from environmental import read_environment
from process_audio import process_audio
from record_audio import record_audio
from utils import ensure_directories, setup_logging


def run_once():
    logger = logging.getLogger("listeningbox")

    logger.info("Starting recording.")
    recording_started_at = datetime.now().isoformat(timespec="seconds")

    audio_file = record_audio()
    logger.info("Recording saved: %s", audio_file)

    processed_info = process_audio(audio_file)

    # Analyze the actual saved audio file, not the environment beforehand.
    environment = read_environment(audio_file)
    environment["timestamp"] = recording_started_at

    recording_id = save_recording(
        audio_file, processed_info, environment
    )

    logger.info(
        "Audio level: %s | RMS: %s | Peak: %s",
        environment["sound_level"],
        environment["audio_rms"],
        environment["audio_peak"],
    )

    try:
        detections = analyze_audio(audio_file) or []
    except Exception:
        logger.exception("BirdNET analysis failed.")
        detections = []

    for detection in detections:
        save_detection(
            recording_id,
            detection["species"],
            detection["confidence"],
            detection.get("start_seconds"),
            detection.get("end_seconds"),
        )
        logger.info(
            "Bird detection: %s %.3f",
            detection["species"],
            detection["confidence"],
        )

    logger.info("Cycle complete.")
    return audio_file, detections


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()

    ensure_directories()
    initialize_database()
    setup_logging()

    if args.once:
        run_once()
    else:
        print("Use: python3 main.py --once")


if __name__ == "__main__":
    main()
