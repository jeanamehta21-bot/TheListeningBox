import logging
import shutil

from config import (
    DATA_DIR,
    LOG_DIR,
    RECORDINGS_DIR,
)


def ensure_directories():
    for directory in (
        DATA_DIR,
        LOG_DIR,
        RECORDINGS_DIR,
    ):
        directory.mkdir(
            parents=True,
            exist_ok=True,
        )


def setup_logging():
    ensure_directories()

    logger = logging.getLogger("listeningbox")

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )

    file_handler = logging.FileHandler(
        LOG_DIR / "listeningbox.log"
    )

    console_handler = logging.StreamHandler()

    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def free_space_gb(path):
    path.mkdir(
        parents=True,
        exist_ok=True,
    )

    usage = shutil.disk_usage(path)

    return usage.free / (1024 ** 3)
