
from datetime import datetime
import math
import struct
import wave


def read_environment(audio_file=None):
    """Collect timestamp and microphone-derived sound measurements."""

    environment = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "cpu_temperature_c": None,
        "audio_rms": None,
        "audio_peak": None,
        "sound_level": "unknown",
    }

    if audio_file is None:
        return environment

    try:
        with wave.open(str(audio_file), "rb") as audio:
            sample_width = audio.getsampwidth()
            frames = audio.readframes(audio.getnframes())

        if not frames or sample_width != 2:
            return environment

        sample_count = len(frames) // 2
        samples = struct.unpack(
            "<" + "h" * sample_count, frames[:sample_count * 2]
        )

        if not samples:
            return environment

        rms = math.sqrt(sum(s * s for s in samples) / len(samples))
        peak = max(abs(s) for s in samples)

        environment["audio_rms"] = round(rms, 2)
        environment["audio_peak"] = peak

        if rms < 300:
            environment["sound_level"] = "very quiet"
        elif rms < 1500:
            environment["sound_level"] = "quiet"
        elif rms < 5000:
            environment["sound_level"] = "moderate"
        else:
            environment["sound_level"] = "loud"

    except (OSError, wave.Error, ValueError, struct.error):
        pass

    return environment
