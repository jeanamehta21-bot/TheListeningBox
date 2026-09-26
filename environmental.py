from datetime import datetime
from pathlib import Path

def read_cpu_temperature():
    path = Path("/sys/class/thermal/thermal_zone0/temp")
    if not path.exists():
        return None
    try:
        return int(path.read_text().strip()) / 1000.0
    except (ValueError, OSError):
        return None

def read_environment():
    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "cpu_temperature_c": read_cpu_temperature(),
        "air_temperature_c": None,
        "humidity_percent": None,
        "rain": None,
    }
