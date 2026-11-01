"""Analyze recordings transferred from the Raspberry Pi on a desktop computer.

Example:
    python analyze_recordings.py
    python analyze_recordings.py --recordings-dir "C:/Users/you/ListeningBox/recordings"
"""

import argparse
import csv
import logging
import os
from pathlib import Path

# Enable the optional analyzer before importing the project's config/adapter.
os.environ.setdefault("LISTENING_BOX_BIRDNET", "1")

from birdnet_analyzer import analyze_audio  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def main():
    parser = argparse.ArgumentParser(
        description="Run official BirdNET-Analyzer 3.0 on transferred WAV recordings."
    )
    parser.add_argument(
        "--recordings-dir",
        type=Path,
        default=Path.home() / "ListeningBox" / "recordings",
        help="Folder containing WAV recordings copied from the Raspberry Pi.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path.home() / "ListeningBox" / "birdnet-results",
        help="Folder for normalized detection CSV files.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Reanalyze recordings even when a results CSV already exists.",
    )
    args = parser.parse_args()

    if not args.recordings_dir.is_dir():
        parser.error(f"Recordings folder does not exist: {args.recordings_dir}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    audio_files = sorted(args.recordings_dir.rglob("*.wav"))

    if not audio_files:
        logging.info("No WAV recordings found.")
        return

    analyzed = 0
    skipped = 0
    for audio_file in audio_files:
        output_file = args.output_dir / f"{audio_file.stem}.BirdNET.results.csv"
        if output_file.exists() and not args.force:
            skipped += 1
            continue

        logging.info("Analyzing %s", audio_file)
        detections = analyze_audio(audio_file)
        with output_file.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=[
                    "Start (s)", "End (s)", "Scientific name",
                    "Common name", "Confidence", "File",
                ],
            )
            writer.writeheader()
            for item in detections:
                writer.writerow({
                    "Start (s)": item["start_seconds"],
                    "End (s)": item["end_seconds"],
                    "Scientific name": item.get("scientific_name") or "",
                    "Common name": item.get("label") or "",
                    "Confidence": item["confidence"],
                    "File": str(audio_file),
                })
        analyzed += 1
        logging.info("Saved %d detections to %s", len(detections), output_file)

    logging.info(
        "Finished. Analyzed %d recordings; skipped %d existing results.",
        analyzed, skipped,
    )


if __name__ == "__main__":
    main()
