# app/config.py
import os
from dotenv import load_dotenv
from pathlib import Path

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
