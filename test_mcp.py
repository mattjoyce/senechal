#!/usr/bin/env python3
"""
Test script for validating MCP implementation.
"""

import requests
import json
import yaml
from datetime import datetime, timedelta

# Configuration
API_URL = "http://127.0.0.1:8000"

def load_api_key():
    """
    Load an API key from the configuration file.
    """
    try:
        with open("config/api_keys.yaml", "r") as f:
            api_keys = yaml.safe_load(f)
            # Just use the first key for testing
            key_id = list(api_keys["keys"].keys())[0]
            return key_id, api_keys["keys"][key_id]
    except Exception as e:
        print(f"Error loading API key: {str(e)}")
        return None, None

def test_mcp_definition(api_key):
    """
    Test retrieving the MCP function definitions.
    """
    headers = {"X-API-Key": api_key}
    response = requests.get(f"{API_URL}/mcp/definition", headers=headers)
    
    if response.status_code == 200:
        definition = response.json()
        print("✅ Successfully retrieved MCP definition")
        print(f"Found {len(definition['functions'])} functions:")
        for func in definition['functions']:
            print(f"  - {func['name']}: {func['description']}")
        return True
    else:
        print(f"❌ Failed to retrieve MCP definition: {response.status_code}")
        print(response.text)
        return False

def test_get_available_metrics(api_key):
    """
    Test the get_available_metrics MCP function.
    """
    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        f"{API_URL}/mcp/invoke/get_available_metrics", 
        headers=headers,
        json={}
    )
    
    if response.status_code == 200:
        metrics = response.json()
        print("✅ Successfully retrieved available metrics")
        print(f"Found {len(metrics['metrics'])} metrics:")
        for metric in metrics['metrics'][:3]:  # Show first 3 for brevity
            print(f"  - {metric['name']} ({metric['unit']}): {metric['description']}")
        return True
    else:
        print(f"❌ Failed to retrieve available metrics: {response.status_code}")
        print(response.text)
        return False

def test_get_health_data(api_key):
    """
    Test the get_health_data MCP function.
    """
    # Set date range for last 7 days
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    
    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }
    
    params = {
        "start_date": start_date,
        "end_date": end_date,
        "metrics": ["steps", "heart_rate"]
    }
    
    response = requests.post(
        f"{API_URL}/mcp/invoke/get_health_data", 
        headers=headers,
        json=params
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Successfully retrieved health data")
        print(f"Retrieved {len(data['data'])} data points")
        return True
    else:
        print(f"❌ Failed to retrieve health data: {response.status_code}")
        print(response.text)
        return False

def main():
    """
    Main test function that runs all tests.
    """
    print("=" * 50)
    print("MCP Test Script")
    print("=" * 50)
    
    key_id, api_key = load_api_key()
    if not api_key:
        print("❌ Could not load API key. Exiting.")
        return
    
    print(f"Using API key: {key_id}")
    print("-" * 50)
    
    # Run tests
    test_mcp_definition(api_key)
    print("-" * 50)
    
    test_get_available_metrics(api_key)
    print("-" * 50)
    
    test_get_health_data(api_key)
    print("-" * 50)
    
    print("Tests completed!")

if __name__ == "__main__":
    main()