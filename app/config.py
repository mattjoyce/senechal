"""Configuration file for the application."""
import os
from pathlib import Path

from dotenv import load_dotenv

# Get the project root directory (where .env will live)
PROJECT_ROOT = Path(__file__).parent.parent

# Load environment variables from project root
load_dotenv(PROJECT_ROOT / ".env")

# Database paths
WITHINGS_DB_PATH = os.getenv("WITHINGS_DB_PATH")
SENECHAL_DB_PATH = os.getenv("SENECHAL_DB_PATH")
GARMIN_DB_PATH = os.getenv("GARMIN_DB_PATH")
GARMIN_MONITORING_DB_PATH = os.getenv("GARMIN_MONITORING_DB_PATH")
GARMIN_SUMMARY_DB_PATH = os.getenv("GARMIN_SUMMARY_DB_PATH")


# API Configuration paths - relative to project root
API_KEYS_PATH = os.getenv("API_KEYS_PATH")
API_ROLES_PATH = os.getenv("API_ROLES_PATH")

HEALTH_PROFILE_PATH = os.getenv("HEALTH_PROFILE_PATH")

# Senechal API URL
SENECHAL_API_URL = os.getenv("SENECHAL_API_URL")

# Theme configuration
MARKDOWN_THEME = os.getenv("MARKDOWN_THEME", "Minimal-dark")

# Logging path - defaults to log directory in project root
APP_LOGGING_PATH = os.getenv("APP_LOGGING_PATH", PROJECT_ROOT / "log")

JINAAI_API_KEY = os.getenv("JINAAI_API_KEY")
JINAAI_URL = os.getenv("JINAAI_URL")
LEARNING_CONTENT_PATH = os.getenv("LEARNING_CONTENT_PATH")

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
YOUTUBE_API_URL = os.getenv("YOUTUBE_API_URL")

PROXY_HTTP_URL = os.getenv("PROXY_HTTP_URL")
PROXY_HTTPS_URL = os.getenv("PROXY_HTTPS_URL")