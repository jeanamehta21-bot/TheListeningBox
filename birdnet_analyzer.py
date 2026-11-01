"""BirdNET-Analyzer CLI adapter for The Listening Box.

The full analyzer is intentionally run on a capable computer (such as the
Windows laptop), not on the Raspberry Pi 3 recording process. Install the
official birdnet_analyzer package and its birdnet-analyze command first.
"""

import csv
import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

from config import BIRDNET_ENABLED, BIRDNET_MIN_CONFIDENCE

logger = logging.getLogger("listeningbox")


def _analyzer_command():
    """Return the installed official BirdNET-Analyzer command."""
    command = shutil.which("birdnet-analyze")
    if command is None:
        raise RuntimeError(
            "BirdNET-Analyzer is not installed in this Python environment. "
            "Install it with: python -m pip install -r requirements-ai.txt"
        )
    return command


def analyze_audio(audio_file):
    """Return BirdNET-Analyzer detections in the project's database format."""
    if not BIRDNET_ENABLED:
        logger.info("BirdNET disabled by configuration.")
        return []

    audio_path = Path(audio_file)
    if not audio_path.is_file():
        logger.error("BirdNET audio file does not exist: %s", audio_path)
        return []

    command = _analyzer_command()

    with tempfile.TemporaryDirectory(prefix="listeningbox-birdnet-") as temp:
        output_dir = Path(temp)
        args = [
            command,
            str(audio_path),
            "--birdnet", "3.0",
            "--min_conf", str(BIRDNET_MIN_CONFIDENCE),
            "--threads", "1",
            "--batch_size", "1",
            "--merge_consecutive", "0",
            "--rtype", "csv",
            "--output", str(output_dir),
            "--quiet",
        ]

        logger.info("Running BirdNET-Analyzer 3.0 for %s", audio_path.name)
        completed = subprocess.run(
            args,
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout).strip()
            raise RuntimeError(
                "BirdNET-Analyzer failed "
                f"(exit {completed.returncode}): {detail[-4000:]}"
            )

        result_files = list(output_dir.glob("*.BirdNET.results.csv"))
        if not result_files:
            result_files = list(output_dir.glob("*.csv"))
        if len(result_files) != 1:
            raise RuntimeError(
                "BirdNET-Analyzer did not produce exactly one results CSV "
                f"for {audio_path.name}; found {len(result_files)}."
            )

        detections = []
        with result_files[0].open(
            "r", encoding="utf-8-sig", newline=""
        ) as handle:
            reader = csv.DictReader(handle)
            required = {
                "Start (s)", "End (s)", "Scientific name",
                "Common name", "Confidence",
            }
            if not required.issubset(set(reader.fieldnames or [])):
                raise RuntimeError(
                    "Unexpected BirdNET-Analyzer CSV columns: "
                    f"{reader.fieldnames}"
                )

            for row in reader:
                confidence = float(row["Confidence"])
                if confidence < BIRDNET_MIN_CONFIDENCE:
                    continue
                common_name = row["Common name"].strip()
                scientific_name = row["Scientific name"].strip()
                detections.append({
                    "model_name": "BirdNET",
                    "category": "bird",
                    "label": common_name or scientific_name or "Unknown",
                    "species": common_name or scientific_name or "Unknown",
                    "scientific_name": scientific_name or None,
                    "confidence": confidence,
                    "start_seconds": float(row["Start (s)"]),
                    "end_seconds": float(row["End (s)"]),
                })

        logger.info(
            "BirdNET-Analyzer found %d candidates at confidence >= %.2f.",
            len(detections),
            BIRDNET_MIN_CONFIDENCE,
        )
        return detections
