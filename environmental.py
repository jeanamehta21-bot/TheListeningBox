import math
import struct
import wave

from pathlib import Path
from datetime import datetime


def get_cpu_temperature():
    """Read Pi CPU temperature, not outdoor temperature."""

    path = Path(
        "/sys/class/thermal/thermal_zone0/temp"
    )

    try:
        return int(
            path.read_text().strip()
        ) / 1000.0

    except (OSError, ValueError):
        return None


def analyze_audio_levels(audio_file):
    result = {
        "timestamp": datetime.now().isoformat(),
        "cpu_temperature_c": get_cpu_temperature(),
        "audio_rms": None,
        "audio_peak": None,
        "sound_level": "unknown",
    }

    try:
        with wave.open(
            str(audio_file),
            "rb",
        ) as audio:

            if audio.getsampwidth() != 2:
                return result

            total_squares = 0
            sample_count = 0
            peak = 0

            while True:
                frames = audio.readframes(8192)

                if not frames:
                    break

                usable = len(frames) - len(frames) % 2

                if usable == 0:
                    continue

                samples = struct.unpack(
                    "<" + "h" * (usable // 2),
                    frames[:usable],
                )

                total_squares += sum(
                    sample * sample
                    for sample in samples
                )

                sample_count += len(samples)

                peak = max(
                    peak,
                    max(abs(sample) for sample in samples),
                )

            if sample_count == 0:
                return result

            rms = math.sqrt(
                total_squares / sample_count
            )

            result["audio_rms"] = round(rms, 2)
            result["audio_peak"] = peak

            if rms < 300:
                level = "very quiet"
            elif rms < 1500:
                level = "quiet"
            elif rms < 5000:
                level = "moderate"
            else:
                level = "loud"

            result["sound_level"] = level

    except (OSError, wave.Error, ValueError, struct.error):
        pass

    return result
