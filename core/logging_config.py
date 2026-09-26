# core/logging_config.py
# Structured logging setup for the Dataset API.
# Rule from phase1.md §39: NEVER log actual biomedical data or file content.
# Only log metadata: filename, size, sha256 prefix, dataset_id.

import logging
import sys


def setup_logging(level: str = "INFO") -> logging.Logger:
    """
    Configure and return the root logger for the Dataset API.
    Call once from main.py at startup.
    """
    log_format = (
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    )
    date_format = "%Y-%m-%dT%H:%M:%S"

    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )

    # Suppress noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("multipart").setLevel(logging.WARNING)

    return logging.getLogger("q_diagnose")


def get_logger(name: str) -> logging.Logger:
    """
    Get a named child logger.
    Usage:
        from core.logging_config import get_logger
        logger = get_logger(__name__)
    """
    return logging.getLogger(f"q_diagnose.{name}")
