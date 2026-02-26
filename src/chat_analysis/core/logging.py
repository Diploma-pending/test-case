"""Centralised logging configuration for the chat analysis package."""

import logging
import os
import sys


def setup_logging() -> None:
    """Configure root logger for the application.

    Log level is controlled by the LOG_LEVEL env var (default: INFO).
    Output goes to stdout so it is captured by uvicorn / Docker / systemd.
    Third-party loggers that are typically very noisy are silenced to WARNING.
    """
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)-8s %(name)s | %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stdout,
        force=True,
    )

    for noisy in ("httpx", "httpcore", "grpc", "urllib3", "google"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
