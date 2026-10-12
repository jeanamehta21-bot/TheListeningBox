from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent

RECORDINGS_DIR = BASE_DIR / "recordings"
DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"

DATABASE_PATH = DATA_DIR / "listeningbox.db"

# Audio settings
AUDIO_DEVICE = os.getenv(
    "LISTENING_BOX_AUDIO_DEVICE",
    "plughw:2,0"
)

SAMPLE_RATE = 48000
CHANNELS = 1
RECORD_SECONDS = 30
INTERVAL_MINUTES = 10

# Monitoring location.
# Leave these as None until you configure the real location.
LATITUDE = None
LONGITUDE = None

# Storage
MIN_FREE_GB = 1.0


# BirdNET
BIRDNET_ENABLED = os.getenv(
    "LISTENING_BOX_BIRDNET", "1"
).strip().lower() in ("1", "true", "yes", "on")

BIRDNET_MIN_CONFIDENCE = 0.50
BIRDNET_LOCATION_FILTER = False

# Environmental sound classification
YAMNET_ENABLED = os.getenv(
    "LISTENING_BOX_YAMNET", "1"
).strip().lower() in ("1", "true", "yes", "on")

YAMNET_MIN_CONFIDENCE = 0.25

YAMNET_MODEL_URL = (
    "https://tfhub.dev/google/yamnet/1"
)

# Flask dashboard
HOST = "0.0.0.0"
PORT = 5000
