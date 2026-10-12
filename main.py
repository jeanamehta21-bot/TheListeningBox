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

    recording_id = save_recording(
        audio_file,
        processed_info,
        environment,
    )

    logger.info(
        "Acoustic measurements: level=%s RMS=%s peak=%s",
        environment.get("sound_level"),
        environment.get("audio_rms"),
        environment.get("audio_peak"),
    )

    all_detections = []

    # Run each model independently so one failure does not stop the other.
    analyzers = (
        ("YAMNet", analyze_environmental_sounds),
        ("BirdNET", analyze_birds),
    )

    for model_name, analyzer in analyzers:
        try:
            # Both analyzers accept the audio file path.
            detections = analyzer(audio_file)

            for detection in detections or []:
                # Keep a consistent model name in saved results.
                detection.setdefault("model_name", model_name)

                save_detection(recording_id, detection)
                all_detections.append(detection)

                label = (
                    detection.get("label")
                    or detection.get("species")
                    or "Unknown"
                )

                logger.info(
                    "%s candidate: %s (confidence %.3f)",
                    model_name,
                    label,
                    float(detection.get("confidence", 0.0)),
                )

        except Exception:
            logger.exception(
                "%s analysis failed for %s",
                model_name,
                audio_file,
            )

    logger.info(
        "Cycle complete; %d candidate detections saved.",
        len(all_detections),
    )

    return audio_file, all_detections


def main():
    parser = argparse.ArgumentParser(
        description="The Listening Box audio pipeline"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Record and analyze one clip",
    )
    args = parser.parse_args()

    ensure_directories()
    initialize_database()
    setup_logging()

    if args.once:
        run_once()
    else:
        parser.error(
            "Use --once for a single recording or run scheduler.py "
            "for repetition."
        )


if __name__ == "__main__":
    main()
