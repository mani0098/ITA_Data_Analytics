"""
Centralized logging utilities.

Every module in the project should obtain its logger from this module.

Example
-------
>>> from src.logger import get_logger
>>> logger = get_logger(__name__)
>>> logger.info("Database connected")
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from config.paths import LOG_DIR


def _build_log_filename() -> Path:
    """
    Build the log filename for the current execution.

    Returns
    -------
    Path
        Path to the log file.
    """

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    return LOG_DIR / f"{timestamp}.log"


def get_logger(
    name: str,
    level: int = logging.INFO,
) -> logging.Logger:
    """
    Return a configured logger.

    Parameters
    ----------
    name
        Logger name.

    level
        Logging level.

    Returns
    -------
    logging.Logger
    """

    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(level)

    formatter = logging.Formatter(
        fmt=(
            "%(asctime)s | "
            "%(levelname)-8s | "
            "%(name)-25s | "
            "%(funcName)-20s | "
            "%(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(
        _build_log_filename(),
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    logger.propagate = False

    return logger