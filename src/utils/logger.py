import logging
from pathlib import Path

from src.config import LOG_DIR, APP_NAME


def setup_logging() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(LOG_DIR / "app.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def get_logger(name: str | None = None) -> logging.Logger:
    if name is None:
        name = APP_NAME
    return logging.getLogger(name)
