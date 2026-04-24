"""Logging setup for the alignment demo."""

import logging
import os
from pathlib import Path


def get_log_path() -> str:
    """Return the configured log file path."""
    log_dir = Path(os.getenv("LOG_DIR", "logs"))
    log_file = os.getenv("LOG_FILE", "alignment_demo.log")
    return str(log_dir / log_file)


def setup_logging() -> logging.Logger:
    """Configure console and file logging once."""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_dir = Path(os.getenv("LOG_DIR", "logs"))
    log_file = os.getenv("LOG_FILE", "alignment_demo.log")

    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / log_file

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    root = logging.getLogger()
    root.setLevel(getattr(logging, log_level, logging.INFO))

    if not any(getattr(handler, "_alignment_demo_handler", False) for handler in root.handlers):
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler._alignment_demo_handler = True
        root.addHandler(console_handler)

        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        file_handler._alignment_demo_handler = True
        root.addHandler(file_handler)

    logger = logging.getLogger("alignment")
    logger.info("System startup")
    return logger
