import logging
import sys
from typing import Optional

_LOG_CONFIGURED = False


def configure_logging(level: Optional[str] = None) -> None:
    """Configure root logging for the application."""
    global _LOG_CONFIGURED
    if _LOG_CONFIGURED:
        return

    log_level = (level or "INFO").upper()

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )

    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(log_level)
    root.handlers = [handler]

    # Quiet down noisy loggers if needed
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    _LOG_CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Get a namespaced application logger."""
    return logging.getLogger(name)
