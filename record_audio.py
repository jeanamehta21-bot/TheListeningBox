
import subprocess
from datetime import datetime
from pathlib import Path

from config import (
    AUDIO_DEVICE,
    CHANNELS,
    MIN_FREE_GB,
    RECORDINGS_DIR,
    RECORD_SECONDS,
    SAMPLE_RATE,
)
from utils import free_space_gb


def find_arecord_devices():
    """Return the audio devices reported by ALSA."""
    try:
        result = subprocess.run(
            ["arecord", "-l"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(
            "arecord was not found. Install alsa-utils first."
        ) from exc

    return result.stdout + result.stderr


def record_audio():
    """Record one WAV file and return its path."""
    if RECORD_SECONDS <= 0:
        raise ValueError("RECORD_SECONDS must be greater than zero.")

    if SAMPLE_RATE <= 0 or CHANNELS <= 0:
        raise ValueError("Audio sample rate and channels must be positive.")

    RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)

    available_gb = free_space_gb(RECORDINGS_DIR)
    if available_gb < MIN_FREE_GB:
        raise RuntimeError(
            f"Only {available_gb:.2f} GB is free; "
            f"at least {MIN_FREE_GB:.2f} GB is required."
        )

    now = datetime.now()
    folder = RECORDINGS_DIR / now.strftime("%Y-%m-%d")
    folder.mkdir(parents=True, exist_ok=True)

    timestamp = now.strftime("%H-%M-%S-%f")
    filename = folder / f"{timestamp}.wav"

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

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(
            "arecord was not found. Install alsa-utils first."
        ) from exc

    if result.returncode != 0:
        filename.unlink(missing_ok=True)
        raise RuntimeError(
            f"Recording failed using audio device {AUDIO_DEVICE!r}.\n"
            f"{result.stderr.strip()}\n"
            "Check the microphone with `arecord -l` and configure "
            "LISTENING_BOX_AUDIO_DEVICE or AUDIO_DEVICE."
        )

    if not filename.is_file() or filename.stat().st_size < 1000:
        filename.unlink(missing_ok=True)
        raise RuntimeError(
            "The recording is missing or too small to be valid."
        )

    return filename


if __name__ == "__main__":
    print(find_arecord_devices())
    print(record_audio())
