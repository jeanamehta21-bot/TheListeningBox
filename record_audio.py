import subprocess
from datetime import datetime
from config import CHANNELS, MIN_FREE_GB, RECORDINGS_DIR, RECORD_SECONDS, SAMPLE_RATE
from utils import free_space_gb

def find_arecord_devices():
    result = subprocess.run(["arecord", "-l"], capture_output=True, text=True)
    return result.stdout + result.stderr

def record_audio():
    if free_space_gb(RECORDINGS_DIR) < MIN_FREE_GB:
        raise RuntimeError(f"Less than {MIN_FREE_GB} GB free.")

    now = datetime.now()
    folder = RECORDINGS_DIR / now.strftime("%Y-%m-%d")
    folder.mkdir(parents=True, exist_ok=True)
    filename = folder / f"{now.strftime('%H-%M-%S')}.wav"

    command = [
        "arecord", "-D", "default",
        "-f", "S16_LE",
        "-r", str(SAMPLE_RATE),
        "-c", str(CHANNELS),
        "-d", str(RECORD_SECONDS),
        str(filename),
    ]

    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(
            f"arecord failed:\n{result.stderr}\nRun `arecord -l`."
        )

    if not filename.exists() or filename.stat().st_size < 1000:
        raise RuntimeError("Recording file was not created correctly.")

    return filename

if __name__ == "__main__":
    print(find_arecord_devices())
    print(record_audio())
