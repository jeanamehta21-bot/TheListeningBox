
import shutil
import subprocess
from pathlib import Path


def validate_audio(audio_file):
    """Validate an audio file and read its duration and size."""
    path = Path(audio_file)

    if not path.is_file() or path.stat().st_size < 1000:
        raise RuntimeError(
            f"Audio file is missing or too small: {path}"
        )

    if shutil.which("ffprobe") is None:
        raise RuntimeError(
            "ffprobe was not found. Install FFmpeg with "
            "`sudo apt install ffmpeg`."
        )

    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration,size",
                "-of", "default=noprint_wrappers=1",
                str(path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise RuntimeError(f"Could not run ffprobe: {exc}") from exc

    if result.returncode != 0:
        raise RuntimeError(
            f"ffprobe could not read {path}: "
            f"{result.stderr.strip()}"
        )

    values = {}
    for line in result.stdout.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()

    try:
        duration = float(values["duration"])
        size = int(float(values["size"]))
    except (KeyError, ValueError) as exc:
        raise RuntimeError(
            f"ffprobe returned incomplete audio information for {path}."
        ) from exc

    if not duration > 0 or size <= 0:
        raise RuntimeError(f"Invalid audio duration or size: {path}")

    return {
        "duration_seconds": duration,
        "size_bytes": size,
    }


def process_audio(audio_file):
    """Return validated audio metadata."""
    return validate_audio(audio_file)
