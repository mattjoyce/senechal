# app/auth.py
import yaml
from fastapi import HTTPException, Security, Depends
from fastapi.security import APIKeyHeader
from typing import Dict
from .config import API_KEYS_PATH, API_ROLES_PATH

# Load YAML files
def load_yaml(filename: str) -> Dict:
    with open(filename, "r") as file:
        return yaml.safe_load(file)

API_KEYS = load_yaml(API_KEYS_PATH)["api_keys"]
ROLES = load_yaml(API_ROLES_PATH)["roles"]

# API Key Security
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def get_api_key(api_key: str = Security(api_key_header)):
    if api_key not in API_KEYS:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    role = API_KEYS[api_key]
    return {"api_key": api_key, "role": role, "access": ROLES.get(role, {}).get("access", [])}


# Middleware to check endpoint access
def check_access(endpoint: str):
    def role_check(api_key_data: Dict = Depends(get_api_key)):
        if endpoint not in api_key_data["access"]:
            raise HTTPException(status_code=403, detail="Access Denied")
        return api_key_data
    return role_check
