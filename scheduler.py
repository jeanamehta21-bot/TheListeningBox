import logging
import time

from config import INTERVAL_MINUTES
from database import initialize_database
from main import run_once
from utils import ensure_directories, setup_logging

def main():
    ensure_directories()
    initialize_database()
    logger = setup_logging()

    logger.info("Scheduler started.")

    while True:
        started = time.monotonic()

        try:
            run_once()
        except Exception:
            logger.exception("Recording cycle failed.")

        elapsed = time.monotonic() - started
        wait_seconds = max(0, INTERVAL_MINUTES * 60 - elapsed)

        logger.info(
            "Next recording in %.1f minutes.",
            wait_seconds / 60,
        )
        time.sleep(wait_seconds)

if __name__ == "__main__":
    main()
