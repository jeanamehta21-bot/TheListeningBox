import subprocess

def validate_audio(audio_file):
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration,size",
            "-of", "default=noprint_wrappers=1",
            str(audio_file),
        ],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr)

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
