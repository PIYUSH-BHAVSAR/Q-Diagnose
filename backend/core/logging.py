"""
backend/core/logging.py
Owner: Arzaan
Purpose: Structured logger setup. All modules call get_logger(__name__).

Rules (phase1.md §39):
  - Log metadata only — NEVER log raw biomedical row content.
  - Format: %(asctime)s | %(levelname)s | %(name)s | %(message)s
  - Log level driven by config.
"""

from __future__ import annotations

import logging
import sys
from typing import Optional

_LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"

_root_configured = False


def _configure_root(level: str = "INFO", fmt: str = _LOG_FORMAT) -> None:
    """One-time root logger configuration."""
    global _root_configured
    if _root_configured:
        return

    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    if not root.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(getattr(logging, level.upper(), logging.INFO))
        formatter = logging.Formatter(fmt=fmt, datefmt=_DATE_FORMAT)
        handler.setFormatter(formatter)
        root.addHandler(handler)

    _root_configured = True


def setup_logging(level: Optional[str] = None, fmt: Optional[str] = None) -> None:
    """
    Initialise platform logging. Called once from backend/main.py startup.
    Falls back to INFO / default format if config is not yet available.
    """
    resolved_level = level or "INFO"
    resolved_fmt = fmt or _LOG_FORMAT

    if level is None or fmt is None:
        try:
            from backend.core.config import config as _cfg
            resolved_level = level or _cfg.logging.level
            resolved_fmt = fmt or _cfg.logging.format
        except Exception:
            pass

    _configure_root(level=resolved_level, fmt=resolved_fmt)


def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger. Usage:

        from backend.core.logging import get_logger
        logger = get_logger(__name__)
        logger.info("Dataset registered | dataset_id=%s sha256_prefix=%s", ds_id, sha[:8])

    IMPORTANT: never pass raw data rows or sensitive biomedical values to logger.
    """
    _configure_root()
    return logging.getLogger(name)
