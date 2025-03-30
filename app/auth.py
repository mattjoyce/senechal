# app/auth.py
import logging
from typing import Dict

import yaml
from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader

from .config import API_KEYS_PATH, API_ROLES_PATH

# Set up logger for authentication
logger = logging.getLogger('auth')

# Load YAML files
def load_yaml(filename: str) -> Dict:
    with open(filename, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)

API_KEYS = load_yaml(API_KEYS_PATH)["api_keys"]
ROLES = load_yaml(API_ROLES_PATH)["roles"]

# API Key Security
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def get_api_key(api_key: str = Security(api_key_header)):
    if not api_key:
        logger.warning("API request missing API key")
        raise HTTPException(status_code=401, detail="API Key is missing")
        
    if api_key not in API_KEYS:
        # Mask the key in logs for security
        masked_key = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "****"
        logger.warning(f"Invalid API key attempt: {masked_key}")
        raise HTTPException(status_code=403, detail="Invalid API Key")
        
    role = API_KEYS[api_key]
    logger.info(f"API key authenticated: role={role}")
    return {"api_key": api_key, "role": role, "access": ROLES.get(role, {}).get("access", [])}


# Middleware to check endpoint access
def check_access(endpoint: str):
    def role_check(api_key_data: Dict = Depends(get_api_key)):
        role = api_key_data["role"]
        
        if endpoint not in api_key_data["access"]:
            logger.warning(f"Access denied: role={role}, endpoint={endpoint}")
            raise HTTPException(status_code=403, detail="Access Denied")
            
        logger.info(f"Access granted: role={role}, endpoint={endpoint}")
        return api_key_data
    return role_check
