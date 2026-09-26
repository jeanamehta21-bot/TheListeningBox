import logging
import shutil
from config import DATA_DIR, LOG_DIR, RECORDINGS_DIR

def ensure_directories():
    RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

def setup_logging():
    ensure_directories()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(LOG_DIR / "listeningbox.log"),
            logging.StreamHandler(),
        ],
    )
    return logging.getLogger("listeningbox")

def free_space_gb(path):
    return shutil.disk_usage(path).free / (1024 ** 3)
