
from datetime import datetime
import math
import struct
import wave
from pathlib import Path


def read_cpu_temperature():
    """Read the Raspberry Pi CPU temperature, not outdoor temperature."""
    path = Path("/sys/class/thermal/thermal_zone0/temp")

    try:
        return int(path.read_text().strip()) / 1000.0
    except (OSError, ValueError):
        return None


def read_environment(audio_file=None):
    """Return timestamp, CPU temperature, and relative audio measurements."""
    result = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "cpu_temperature_c": read_cpu_temperature(),
        "audio_rms": None,
        "audio_peak": None,
        "sound_level": "unknown",
    }

    if audio_file is None:
        return result

    try:
        with wave.open(str(Path(audio_file)), "rb") as audio:
            if audio.getsampwidth() != 2:
                return result

            total_squares = 0
            sample_count = 0
            peak = 0

            while True:
                frames = audio.readframes(8192)
                if not frames:
                    break

                usable_bytes = len(frames) - len(frames) % 2
                if usable_bytes == 0:
                    continue

                samples = struct.unpack(
                    "<" + "h" * (usable_bytes // 2),
                    frames[:usable_bytes],
                )

                total_squares += sum(sample * sample for sample in samples)
                sample_count += len(samples)

                if samples:
                    peak = max(
                        peak,
                        max(abs(sample) for sample in samples),
                    )

            if sample_count == 0:
                return result

            rms = math.sqrt(total_squares / sample_count)

            result["audio_rms"] = round(rms, 2)
            result["audio_peak"] = peak

            # Provisional digital-amplitude bands, not dB SPL.
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
        # Keep the recording pipeline alive if a WAV cannot be measured.
        pass

    return result
