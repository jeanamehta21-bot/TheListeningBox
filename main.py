import argparse
import logging

from birdnet_analyzer import analyze_audio
from database import initialize_database, save_detection, save_recording
from environmental import read_environment
from process_audio import process_audio
from record_audio import record_audio
from utils import ensure_directories, setup_logging

def run_once():
    logger = logging.getLogger("listeningbox")

    logger.info("Starting recording.")
    environment = read_environment()
    audio_file = record_audio()
    processed_info = process_audio(audio_file)

    recording_id = save_recording(
        audio_file, processed_info, environment
    )

    detections = analyze_audio(audio_file)

    for detection in detections:
        save_detection(
            recording_id,
            detection["species"],
            detection["confidence"],
            detection["start_seconds"],
            detection["end_seconds"],
        )
        logger.info(
            "Detection: %s %.3f",
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
