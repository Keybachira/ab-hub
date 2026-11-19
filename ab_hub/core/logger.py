"""Logging configuration for AB-hub."""

from __future__ import annotations

import logging
import sys
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler


def setup_logger(
    name: str = "ab_hub",
    level: str = "INFO",
    console: Optional[Console] = None,
) -> logging.Logger:
    """Configure and return the application logger."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)

    handler = RichHandler(
        console=console or Console(stderr=True),
        show_time=True,
        show_path=False,
        rich_tracebacks=True,
        markup=True,
    )
    handler.setLevel(log_level)
    formatter = logging.Formatter("%(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Prevent propagation to root logger
    logger.propagate = False
    return logger


def get_logger(name: str = "ab_hub") -> logging.Logger:
    """Return an existing logger or create a basic one."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        return setup_logger(name)
    return logger
