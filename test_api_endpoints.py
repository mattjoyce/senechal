#!/usr/bin/env python3
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
    "errors": []
}

def log_result(endpoint: str, status: bool, response: requests.Response, error: Optional[str] = None) -> None:
    """Log the result of a test"""
    global results
    results["total"] += 1
    
    status_code = response.status_code if response else None
    result_text = "PASSED" if status else "FAILED"
    
    if status:
        results["passed"] += 1
        print(f"✅ {result_text} - {endpoint} - Status: {status_code}")
    else:
        results["failed"] += 1
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
            "response": response_text
        })

def test_endpoint(method: str, path: str, params: Optional[Dict] = None, body: Optional[Dict] = None) -> Dict:
    """Test a specific API endpoint and return the result"""
    full_url = f"{BASE_URL}{path}"
    result = {
        "success": False,
        "status_code": None,
        "response": None,
        "error": None
    }
    
    try:
        if method.lower() == "get":
            response = requests.get(full_url, headers=HEADERS, params=params)
        elif method.lower() == "post":
            response = requests.post(full_url, headers=HEADERS, json=body)
        else:
            log_result(path, False, None, f"Unsupported method: {method}")
            result["error"] = f"Unsupported method: {method}"
            return result
        
        result["status_code"] = response.status_code
        result["response"] = response
        
        # Check if the response is successful (status code 2xx)
        is_success = 200 <= response.status_code < 300
        
        # Try to parse the response as JSON to verify it's valid
        if is_success:
            try:
                json_response = response.json()
                log_result(path, True, response)
                result["success"] = True
            except json.JSONDecodeError:
                log_result(path, False, response, "Invalid JSON response")
                result["error"] = "Invalid JSON response"
        else:
            error_detail = f"HTTP {response.status_code}"
            response_text = ""
            try:
                error_json = response.json()
                if isinstance(error_json, dict) and "detail" in error_json:
                    error_detail = f"{error_detail} - {error_json['detail']}"
                response_text = json.dumps(error_json)
            except:
                response_text = response.text
            
            log_result(path, False, response, error_detail)
            result["error"] = error_detail
            
    except requests.RequestException as e:
        log_result(path, False, None, str(e))
        result["error"] = str(e)
    
    return result

def run_all_tests() -> None:
    """Run tests for all endpoints defined in the OpenAPI spec"""
    print(f"\n{'=' * 50}")
    print(f"Starting API Endpoint Tests at {datetime.now().isoformat()}")
    print(f"Using API URL: {BASE_URL}")
    print(f"{'=' * 50}\n")
    
    # Test GET /health/summary/{period} - test with different periods and parameters
    print("\n----- Testing /health/summary endpoints -----")
    for period in ["day", "week", "month", "year"]:
        # Basic test with defaults
        test_endpoint("get", f"/health/summary/{period}")
        
        # Test with specific metrics
        test_endpoint("get", f"/health/summary/{period}", params={"metrics": "weight,steps"})
        
        # Test with span and offset
        test_endpoint("get", f"/health/summary/{period}", params={"span": 2, "offset": 1})
        
        # Test with metric group using @ prefix
        test_endpoint("get", f"/health/summary/{period}", params={"metrics": "@activity"})
        
        # Test with mixed individual metrics and groups
        test_endpoint("get", f"/health/summary/{period}", params={"metrics": "weight,@activity,@body"})
    
    # Test GET /health/profile
    print("\n----- Testing /health/profile endpoint -----")
    profile_result = test_endpoint("get", "/health/profile")
    
    # Test GET /health/current - with and without type filter
    print("\n----- Testing /health/current endpoints -----")
    test_endpoint("get", "/health/current")
    if profile_result["success"]:  # Only run the type filter test if profile succeeded
        test_endpoint("get", "/health/current", params={"types": [1, 2]})
    
    # Test GET /health/trends
    print("\n----- Testing /health/trends endpoints -----")
    test_endpoint("get", "/health/trends")
    test_endpoint("get", "/health/trends", params={"days": 14})
    test_endpoint("get", "/health/trends", params={"types": [1, 2], "interval": "week"})
    
    # Test GET /health/stats
    print("\n----- Testing /health/stats endpoints -----")
    test_endpoint("get", "/health/stats")
    test_endpoint("get", "/health/stats", params={"days": 14, "types": [1, 2]})
    
    # Test GET /getTest and POST /setTest
    print("\n----- Testing utility endpoints -----")
    test_endpoint("get", "/getTest")
    test_endpoint("post", "/setTest", body={"content": "test data"})
    
    # Test unified LLM endpoints
    print("\n----- Testing unified LLM endpoints -----")
    
    # Test GET /llm/prompts
    test_endpoint("get", "/llm/prompts")
    
    # Test POST /llm/process - main processing endpoint
    test_endpoint("post", "/llm/process", body={
        "model": "gpt-4o",
        "prompt": "analyze_summary",
        "query_text": "This is a test article about AI and machine learning.",
        "save_result": False,
        "output_format": "text"
    })
    
    # Test POST /llm/process with save_result=True
    process_result = test_endpoint("post", "/llm/process", body={
        "model": "gpt-4o", 
        "prompt": "extract_learning",
        "query_text": "Python is a powerful programming language with simple syntax.",
        "save_result": True,
        "output_format": "markdown"
    })
    
    # Test POST /llm/extract - convenience endpoint
    test_endpoint("post", "/llm/extract", body={
        "query_text": "FastAPI is a modern web framework for Python.",
        "model": "gpt-4o",
        "save_result": True
    })
    
    # Test POST /llm/analyze - convenience endpoint
    test_endpoint("post", "/llm/analyze", body={
        "analysis_type": "summary",
        "query_text": "Machine learning is transforming industries.",
        "model": "gpt-4o", 
        "save_result": False
    })
    
    # Test POST /llm/custom - custom prompt endpoint
    test_endpoint("post", "/llm/custom", body={
        "custom_prompt": "Translate this to French:",
        "query_text": "Hello, how are you?",
        "model": "gpt-4o",
        "save_result": False,
        "output_format": "text"
    })
    
    # Test GET /llm/list
    test_endpoint("get", "/llm/list")
    
    # Test backward compatibility with learning endpoints
    print("\n----- Testing backward compatibility -----")
    
    # Test POST /learning/scrape
    test_endpoint("post", "/learning/scrape", body={
        "text": "React is a JavaScript library for building user interfaces."
    })
    
    # Test POST /analysis/analyze
    test_endpoint("post", "/analysis/analyze", body={
        "text": "Artificial intelligence is revolutionizing technology.",
        "analysis_type": "summary",
        "model_name": "gpt-4o",
        "save_result": False
    })
    
    # Test GET /analysis/types
    test_endpoint("get", "/analysis/types")
    
    # Print summary
    print(f"\n{'=' * 50}")
    print(f"Test Summary:")
    print(f"  Total: {results['total']}")
    print(f"  Passed: {results['passed']}")
    print(f"  Failed: {results['failed']}")
    
    if results["failed"] > 0:
        print("\nFailed Tests:")
        for error in results["errors"]:
            print(f"  - {error['endpoint']} (Status: {error['status_code']})")
            print(f"    Error: {error['error']}")
            print(f"    Response: {error['response'][:200]}..." if error['response'] and len(error['response']) > 200 else f"    Response: {error['response']}")
    
    print(f"{'=' * 50}\n")
    
    # Exit with proper code based on critical endpoints
    # This ensures we consider the test successful if key endpoints pass
    critical_endpoints = ["/health/summary/", "/llm/prompts", "/llm/process"]
    critical_success = True
    
    for error in results["errors"]:
        # Check if any critical endpoint failed
        if any(critical in error["endpoint"] for critical in critical_endpoints):
            critical_success = False
            break
    
    print(f"Critical endpoint tests: {'Passed' if critical_success else 'Failed'}")
    print(f"Overall test success rate: {results['passed']}/{results['total']} ({(results['passed']/results['total']*100):.1f}%)")
    sys.exit(0 if critical_success else 1)

if __name__ == "__main__":
    run_all_tests()