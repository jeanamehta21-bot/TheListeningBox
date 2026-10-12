import subprocess
from pathlib import Path


def validate_audio(audio_file):
    path = Path(audio_file)
    if not path.is_file() or path.stat().st_size < 1000:
        raise RuntimeError(f"Audio file is missing or too small: {path}")

    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration,size",
            "-of", "default=noprint_wrappers=1",
            str(path),
        ],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe could not read audio: {result.stderr.strip()}")

    values = {}
    for line in result.stdout.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            values[key] = value
    return values


def process_audio(audio_file):
    info = validate_audio(audio_file)
    return {
        "duration_seconds": float(info.get("duration", 0)),
        "size_bytes": int(float(info.get("size", 0))),
    }
