from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
RECORDINGS_DIR = BASE_DIR / "recordings"
DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"
DATABASE_PATH = DATA_DIR / "listeningbox.db"

SAMPLE_RATE = 48000
CHANNELS = 1
RECORD_SECONDS = 60
INTERVAL_MINUTES = 10

# Replace with the actual deployment location.
LATITUDE = 41.28
LONGITUDE = -73.00

BIRDNET_ENABLED = True
BIRDNET_MIN_CONFIDENCE = 0.50
MIN_FREE_GB = 2.0

HOST = "0.0.0.0"
PORT = 5000
