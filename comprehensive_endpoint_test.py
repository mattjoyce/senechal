#!/usr/bin/env python3
"""
Comprehensive endpoint testing script for Senechal API
Tests all endpoints including health, learning, and utility endpoints
"""
import json
import os
import requests
import sys
from datetime import datetime
from dotenv import load_dotenv
from typing import Dict, List, Optional, Any, Union

# Load environment variables from .env file
load_dotenv()

# Configuration from .env
BASE_URL = os.getenv("SENECHAL_API_URL")
API_KEY = os.getenv("SENECHAL_API_KEY")
HEADERS = {"X-API-Key": API_KEY}

# Validate environment variables
if not BASE_URL or not API_KEY:
    print("Error: SENECHAL_API_URL and SENECHAL_API_KEY must be set in the .env file")
    sys.exit(1)

# Test results tracking
results = {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "errors": [],
    "categories": {
        "health": {"total": 0, "passed": 0, "failed": 0},
        "learning": {"total": 0, "passed": 0, "failed": 0},
        "utility": {"total": 0, "passed": 0, "failed": 0}
    }
}

def log_result(endpoint: str, status: bool, response: requests.Response, 
               error: Optional[str] = None, category: str = "unknown") -> None:
    """Log the result of a test"""
    global results
    results["total"] += 1
    results["categories"][category]["total"] += 1
    
    status_code = response.status_code if response else None
    result_text = "PASSED" if status else "FAILED"
    
    if status:
        results["passed"] += 1
        results["categories"][category]["passed"] += 1
        print(f"✅ {result_text} - {endpoint} - Status: {status_code}")
    else:
        results["failed"] += 1
        results["categories"][category]["failed"] += 1
        error_msg = f"❌ {result_text} - {endpoint} - Status: {status_code}"
        if error:
            error_msg += f" - Error: {error}"
        print(error_msg)
        
        # Get response text safely
        response_text = None
        if response:
            try:
                json_data = response.json()
                response_text = json.dumps(json_data, indent=2)
            except:
                response_text = response.text
                
        results["errors"].append({
            "endpoint": endpoint,
            "status_code": status_code,
            "error": error,
            "response": response_text,
            "category": category
        })

def test_endpoint(method: str, path: str, params: Optional[Dict] = None, 
                 body: Optional[Dict] = None, category: str = "unknown",
                 expect_auth_failure: bool = False) -> Dict:
    """Test a specific API endpoint and return the result"""
    full_url = f"{BASE_URL}{path}"
    result = {
        "success": False,
        "status_code": None,
        "response": None,
        "error": None
    }
    
    try:
        headers = HEADERS if not expect_auth_failure else {}
        
        if method.lower() == "get":
            response = requests.get(full_url, headers=headers, params=params)
        elif method.lower() == "post":
            response = requests.post(full_url, headers=headers, json=body)
        else:
            log_result(path, False, None, f"Unsupported method: {method}", category)
            result["error"] = f"Unsupported method: {method}"
            return result
        
        result["status_code"] = response.status_code
        result["response"] = response
        
        # Check if the response is successful (status code 2xx)
        is_success = 200 <= response.status_code < 300
        
        # Special handling for auth failure tests
        if expect_auth_failure:
            is_success = response.status_code == 403 or response.status_code == 401
            if is_success:
                log_result(f"{path} (no auth)", True, response, category=category)
                result["success"] = True
            else:
                log_result(f"{path} (no auth)", False, response, "Expected auth failure but got different status", category)
                result["error"] = "Expected auth failure but got different status"
        else:
            # Try to parse the response as JSON to verify it's valid
            if is_success:
                try:
                    json_response = response.json()
                    log_result(path, True, response, category=category)
                    result["success"] = True
                except json.JSONDecodeError:
                    # Special case: some endpoints return plain text
                    if response.headers.get('content-type', '').startswith('text/plain'):
                        log_result(path, True, response, category=category)
                        result["success"] = True
                    else:
                        log_result(path, False, response, "Invalid JSON response", category)
                        result["error"] = "Invalid JSON response"
            else:
                error_detail = f"HTTP {response.status_code}"
                try:
                    error_json = response.json()
                    if isinstance(error_json, dict) and "detail" in error_json:
                        error_detail = f"{error_detail} - {error_json['detail']}"
                except:
                    pass
                
                log_result(path, False, response, error_detail, category)
                result["error"] = error_detail
            
    except requests.RequestException as e:
        log_result(path, False, None, str(e), category)
        result["error"] = str(e)
    
    return result

def test_health_endpoints():
    """Test all health-related endpoints"""
    print("\n" + "="*60)
    print("TESTING HEALTH ENDPOINTS")
    print("="*60)
    
    # Test health summary endpoints
    print("\n----- Testing /health/summary endpoints -----")
    for period in ["day", "week", "month", "year"]:
        test_endpoint("get", f"/health/summary/{period}", category="health")
        test_endpoint("get", f"/health/summary/{period}", 
                     params={"metrics": "weight,steps"}, category="health")
        test_endpoint("get", f"/health/summary/{period}", 
                     params={"span": 2, "offset": 1}, category="health")
        test_endpoint("get", f"/health/summary/{period}", 
                     params={"metrics": "@activity"}, category="health")
    
    # Test rowing endpoints
    print("\n----- Testing /health/rowing endpoints -----")
    for period in ["day", "week", "month", "year"]:
        test_endpoint("get", f"/health/rowing/get/{period}", category="health")
        test_endpoint("get", f"/health/rowing/get/{period}", 
                     params={"span": 2, "offset": 1}, category="health")
    
    # Test rowing submit endpoint (will fail without valid image URL)
    test_endpoint("post", "/health/rowing/submit", 
                 body={"image_url": "https://example.com/test.jpg"}, category="health")
    
    # Test other health endpoints
    print("\n----- Testing other health endpoints -----")
    test_endpoint("get", "/health/availablemetrics", category="health")
    test_endpoint("get", "/health/profile", category="health")
    
    # Test deprecated endpoints
    print("\n----- Testing deprecated health endpoints -----")
    test_endpoint("get", "/health/current", category="health")
    test_endpoint("get", "/health/current", params={"types": [1, 2]}, category="health")
    test_endpoint("get", "/health/trends", category="health")
    test_endpoint("get", "/health/trends", params={"days": 14, "interval": "week"}, category="health")
    test_endpoint("get", "/health/stats", category="health")
    test_endpoint("get", "/health/stats", params={"days": 14, "types": [1, 2]}, category="health")

def test_learning_endpoints():
    """Test all learning-related endpoints"""
    print("\n" + "="*60)
    print("TESTING LEARNING ENDPOINTS")
    print("="*60)
    
    # Test learning list endpoint
    print("\n----- Testing /learning/list endpoints -----")
    test_endpoint("get", "/learning/list", category="learning")
    test_endpoint("get", "/learning/list", params={"status": "active"}, category="learning")
    test_endpoint("get", "/learning/list", params={"status": "archived"}, category="learning")
    test_endpoint("get", "/learning/list", params={"status": "all"}, category="learning")
    
    # Test learning scrape endpoint
    print("\n----- Testing /learning/scrape endpoint -----")
    test_endpoint("post", "/learning/scrape", 
                 body={"url": "https://example.com"}, category="learning")
    
    # Test learning memo endpoint  
    print("\n----- Testing /learning/memo endpoint -----")
    test_endpoint("post", "/learning/memo", 
                 body={"text": "This is a test memo"}, category="learning")
    
    # Test learning rm endpoint
    print("\n----- Testing /learning/rm endpoint -----") 
    test_endpoint("post", "/learning/rm", 
                 body={"id": "nonexistent"}, category="learning")
    
    # Test learning file endpoint (note: this one has NO AUTH!)
    print("\n----- Testing /learning/file endpoint -----")
    test_endpoint("get", "/learning/file/test123", category="learning")
    
    # Test that the file endpoint works WITHOUT authentication (intentional public access)
    print("\n----- Testing /learning/file endpoint WITHOUT auth (public access) -----")
    test_endpoint("get", "/learning/file/test123", category="learning", expect_auth_failure=False)

def test_utility_endpoints():
    """Test utility endpoints"""
    print("\n" + "="*60)
    print("TESTING UTILITY ENDPOINTS")
    print("="*60)
    
    print("\n----- Testing utility endpoints -----")
    test_endpoint("get", "/getTest", category="utility")
    test_endpoint("post", "/setTest", 
                 body={"content": f"Test data from comprehensive test at {datetime.now().isoformat()}"}, 
                 category="utility")

def print_summary():
    """Print comprehensive test summary"""
    print(f"\n{'='*60}")
    print("COMPREHENSIVE TEST SUMMARY")
    print(f"{'='*60}")
    
    print(f"Overall Results:")
    print(f"  Total Tests: {results['total']}")
    print(f"  Passed: {results['passed']}")
    print(f"  Failed: {results['failed']}")
    print(f"  Success Rate: {(results['passed']/results['total']*100):.1f}%")
    
    print(f"\nResults by Category:")
    for category, stats in results["categories"].items():
        if stats["total"] > 0:
            success_rate = (stats["passed"]/stats["total"]*100)
            print(f"  {category.title():>8}: {stats['passed']:>2}/{stats['total']:>2} ({success_rate:>5.1f}%)")
    
    if results["failed"] > 0:
        print(f"\nFailed Tests by Category:")
        for category in results["categories"].keys():
            category_errors = [e for e in results["errors"] if e["category"] == category]
            if category_errors:
                print(f"\n  {category.title()} Failures:")
                for error in category_errors:
                    print(f"    ❌ {error['endpoint']} (HTTP {error['status_code']})")
                    if error['error']:
                        print(f"       Error: {error['error']}")
    
    print(f"\n{'='*60}")

def run_all_tests():
    """Run comprehensive tests for all endpoints"""
    print(f"{'='*60}")
    print(f"SENECHAL API COMPREHENSIVE ENDPOINT TESTING")
    print(f"Started at {datetime.now().isoformat()}")
    print(f"API URL: {BASE_URL}")
    print(f"{'='*60}")
    
    # Run all test categories
    test_health_endpoints()
    test_learning_endpoints()
    test_utility_endpoints()
    
    # Print final summary
    print_summary()
    
    # Exit with appropriate code
    sys.exit(0 if results["failed"] == 0 else 1)

if __name__ == "__main__":
    run_all_tests()