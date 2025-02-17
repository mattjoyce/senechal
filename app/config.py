# app/config.py
import os
from dotenv import load_dotenv
from pathlib import Path

# Get the project root directory (where .env will live)
PROJECT_ROOT = Path(__file__).parent.parent

# Load environment variables from project root
load_dotenv(PROJECT_ROOT / ".env")

# Database paths
WITHINGS_DB_PATH = os.getenv("WITHINGS_DB_PATH", "/home/ubuntu/api/withings/withings.db")

# API Configuration paths - relative to project root
API_KEYS_PATH = os.getenv("API_KEYS_PATH", PROJECT_ROOT / "config" / "api_keys.yaml")
API_ROLES_PATH = os.getenv("API_ROLES_PATH", PROJECT_ROOT / "config" / "api_roles.yaml")