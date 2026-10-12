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
    "plughw:2,0",
)
SAMPLE_RATE = 48000
CHANNELS = 1
RECORD_SECONDS = 30
INTERVAL_MINUTES = 10

# Set these only when you know the real monitoring coordinates.
LATITUDE = None
LONGITUDE = None

# Stop recording when free disk space drops below this amount.
MIN_FREE_GB = 1.0

# Optional bird species identification.
# Enable only after the BirdNET installation and API are verified.
BIRDNET_ENABLED = os.getenv(
    "LISTENING_BOX_BIRDNET", "0"
).strip().lower() in ("1", "true", "yes", "on")

BIRDNET_MIN_CONFIDENCE = 0.50
BIRDNET_LOCATION_FILTER = False

# Optional general environmental sound classification.
# YAMNet identifies sound categories, not exact bird species.
YAMNET_ENABLED = os.getenv(
    "LISTENING_BOX_YAMNET", "0"
).strip().lower() in ("1", "true", "yes", "on")

YAMNET_MIN_CONFIDENCE = 0.25
YAMNET_MODEL_URL = "https://tfhub.dev/google/yamnet/1"

# Dashboard access.
# 0.0.0.0 permits access from devices on the reachable network.
# Do not expose the development server directly to the public internet.
HOST = "0.0.0.0"
PORT = 5000
