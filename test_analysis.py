#!/usr/bin/env python3
"""
Test script for the analysis endpoint
Usage: python test_analysis.py
"""

import requests
import json
import sys

# Configuration
BASE_URL = "http://127.0.0.1:8000"
API_KEY = "HandwritingRepair"  # Using the same key from CLAUDE.md
HEADERS = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

def test_analysis_types():
    """Test getting available analysis types"""
    print("Testing /analysis/types endpoint...")
    try:
        response = requests.get(
            f"{BASE_URL}/analysis/types",
            headers={"X-API-Key": API_KEY}
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_url_analysis():
    """Test analyzing a URL"""
    print("\nTesting /analysis/analyze endpoint with URL...")
    
    test_data = {
        "url": "https://httpbin.org/html",  # Simple test page
        "analysis_type": "summary",
        "model_name": "gpt-4o",
        "save_result": True
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/analysis/analyze",
            headers=HEADERS,
            json=test_data
        )
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Analysis ID: {result['data']['id']}")
            print(f"Title: {result['data']['title']}")
            print(f"Analysis Type: {result['data']['analysis_type']}")
            print(f"Content Type: {result['data']['content_type']}")
            print(f"Analysis Result: {result['data']['analysis_content'][:200]}...")
            return result['data']['id']
        else:
            print(f"Error Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_text_analysis():
    """Test analyzing direct text"""
    print("\nTesting /analysis/analyze endpoint with text...")
    
    test_data = {
        "text": "FastAPI is a modern, fast web framework for building APIs with Python 3.7+ based on standard Python type hints. It's designed to be easy to use and learn, fast to code, and ready for production.",
        "analysis_type": "extraction",
        "model_name": "gpt-4o",
        "save_result": True
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/analysis/analyze",
            headers=HEADERS,
            json=test_data
        )
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Analysis ID: {result['data']['id']}")
            print(f"Analysis Type: {result['data']['analysis_type']}")
            print(f"Analysis Result: {result['data']['analysis_content'][:200]}...")
            return result['data']['id']
        else:
            print(f"Error Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_list_analyses():
    """Test listing all analyses"""
    print("\nTesting /analysis/list endpoint...")
    try:
        response = requests.get(
            f"{BASE_URL}/analysis/list",
            headers={"X-API-Key": API_KEY}
        )
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Found {len(result['data'])} analyses")
            for item in result['data'][:3]:  # Show first 3
                print(f"  - {item['id']}: {item['title']} ({item['analysis_type']})")
        else:
            print(f"Error Response: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

def test_get_analysis_file(analysis_id):
    """Test getting analysis file content"""
    if not analysis_id:
        print("Skipping file test - no analysis ID available")
        return
        
    print(f"\nTesting /analysis/file/{analysis_id} endpoint...")
    try:
        response = requests.get(
            f"{BASE_URL}/analysis/file/{analysis_id}",
            headers={"X-API-Key": API_KEY}
        )
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            content = response.text
            print(f"File content length: {len(content)}")
            print(f"First 300 chars: {content[:300]}...")
        else:
            print(f"Error Response: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

def main():
    """Run all tests"""
    print("=== Analysis Endpoint Test Suite ===")
    
    # Test 1: Get analysis types
    if not test_analysis_types():
        print("Failed to get analysis types - check if server is running")
        sys.exit(1)
    
    # Test 2: Analyze URL (if network access available)
    url_analysis_id = test_url_analysis()
    
    # Test 3: Analyze text
    text_analysis_id = test_text_analysis()
    
    # Test 4: List analyses
    test_list_analyses()
    
    # Test 5: Get analysis file
    test_analysis_id = url_analysis_id or text_analysis_id
    test_get_analysis_file(test_analysis_id)
    
    print("\n=== Test Suite Complete ===")

if __name__ == "__main__":
    main()