"""Logging configuration for the application."""
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from .config import APP_LOGGING_PATH


def setup_logging():
    """Configure logging for the application"""
    # Create logging directory if it doesn't exist
    log_dir = Path(APP_LOGGING_PATH)
    log_dir.mkdir(parents=True, exist_ok=True)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Console handler for all logs
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console.setFormatter(console_formatter)
    root_logger.addHandler(console)

    # Auth logger setup
    auth_logger = logging.getLogger("auth")
    auth_logger.setLevel(logging.INFO)
    auth_file = RotatingFileHandler(
        log_dir / "auth.log", maxBytes=10485760, backupCount=5  # 10MB
    )
    auth_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    auth_file.setFormatter(auth_formatter)
    auth_logger.addHandler(auth_file)

    # API calls logger setup
    api_logger = logging.getLogger("api")
    api_logger.setLevel(logging.INFO)
    api_file = RotatingFileHandler(
        log_dir / "api.log", maxBytes=10485760, backupCount=5  # 10MB
    )
    api_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    api_file.setFormatter(api_formatter)
    api_logger.addHandler(api_file)

    return root_logger
