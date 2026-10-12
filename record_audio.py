import subprocess
from datetime import datetime

from config import (
    AUDIO_DEVICE,
    CHANNELS,
    MIN_FREE_GB,
    RECORDINGS_DIR,
    RECORD_SECONDS,
    SAMPLE_RATE,
)

from utils import free_space_gb


def list_microphones():
    result = subprocess.run(
        ["arecord", "-l"],
        capture_output=True,
        text=True,
    )

    return result.stdout + result.stderr


def record_audio():
    if free_space_gb(RECORDINGS_DIR) < MIN_FREE_GB:
        raise RuntimeError(
            "Not enough free storage space."
        )

    started_at = datetime.now()

    date_folder = (
        RECORDINGS_DIR /
        started_at.strftime("%Y-%m-%d")
    )

    date_folder.mkdir(
        parents=True,
        exist_ok=True,
    )

    filename = (
        date_folder /
        f"recording_{started_at.strftime('%H-%M-%S')}.wav"
    )

    command = [
        "arecord",
        "-D", AUDIO_DEVICE,
        "-t", "wav",
        "-f", "S16_LE",
        "-r", str(SAMPLE_RATE),
        "-c", str(CHANNELS),
        "-d", str(RECORD_SECONDS),
        str(filename),
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "Microphone recording failed.\n"
            f"Device: {AUDIO_DEVICE}\n"
            f"Error: {result.stderr}\n"
            "Check the device using arecord -l."
        )

    if (
        not filename.exists()
        or filename.stat().st_size < 1000
    ):
        raise RuntimeError(
            "The recording file is missing "
            "or unexpectedly small."
        )

    return filename


if __name__ == "__main__":
    print(list_microphones())
    print(record_audio())
