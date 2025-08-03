#!/usr/bin/env python3
"""
Deployment Verification Script
Tests the deployed candlestick screener application
"""

import requests
import json
import time
import sys
from urllib.parse import urljoin

def test_endpoint(base_url, endpoint, method='GET', expected_status=200, timeout=30):
    """Test a single endpoint"""
    url = urljoin(base_url, endpoint)
    print(f"Testing {method} {url}...")
    
    try:
        if method == 'GET':
            response = requests.get(url, timeout=timeout)
        elif method == 'POST':
            response = requests.post(url, timeout=timeout)
        else:
            print(f"  ❌ Unsupported method: {method}")
            return False
            
        print(f"  Status: {response.status_code}")
        
        if response.status_code == expected_status:
            print(f"  ✅ Success")
            return True
        else:
            print(f"  ❌ Expected {expected_status}, got {response.status_code}")
            if response.text:
                print(f"  Response: {response.text[:200]}...")
            return False
            
    except requests.exceptions.Timeout:
        print(f"  ❌ Timeout after {timeout} seconds")
        return False
    except requests.exceptions.RequestException as e:
        print(f"  ❌ Request failed: {str(e)}")
        return False

def test_json_endpoint(base_url, endpoint, required_fields=None):
    """Test endpoint that returns JSON"""
    url = urljoin(base_url, endpoint)
    print(f"Testing JSON endpoint {url}...")
    
    try:
        response = requests.get(url, timeout=30)
        print(f"  Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"  ❌ Expected 200, got {response.status_code}")
            return False
            
        try:
            data = response.json()
            print(f"  ✅ Valid JSON response")
            
            if required_fields:
                for field in required_fields:
                    if field not in data:
                        print(f"  ❌ Missing required field: {field}")
                        return False
                    else:
                        print(f"  ✅ Field '{field}' present: {data[field]}")
            
            return True
            
        except json.JSONDecodeError:
            print(f"  ❌ Invalid JSON response")
            print(f"  Response: {response.text[:200]}...")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"  ❌ Request failed: {str(e)}")
        return False

def run_verification(base_url):
    """Run complete verification suite"""
    print(f"🚀 Starting verification for: {base_url}")
    print("=" * 50)
    
    results = []
    
    # Test 1: Basic connectivity
    print("\\n1. Testing basic connectivity...")
    results.append(test_endpoint(base_url, "/", timeout=10))
    
    # Test 2: Health check
    print("\\n2. Testing health check...")
    health_result = test_json_endpoint(
        base_url, 
        "/health", 
        required_fields=['status', 'cache', 'symbols', 'alpaca_api', 'timestamp']
    )
    results.append(health_result)
    
    # Test 3: Stats endpoint
    print("\\n3. Testing stats endpoint...")
    stats_result = test_json_endpoint(
        base_url,
        "/stats",
        required_fields=['symbols_count', 'server_time']
    )
    results.append(stats_result)
    
    # Test 4: Pattern search (with parameter)
    print("\\n4. Testing pattern search...")
    results.append(test_endpoint(base_url, "/?pattern=CDLDOJI", timeout=30))
    
    # Test 5: API endpoints (these may require auth, so 401/403 is acceptable)
    print("\\n5. Testing API endpoints...")
    api_result = test_endpoint(base_url, "/api/alpaca/account", expected_status=[200, 401, 403])
    results.append(api_result)
    
    # Summary
    print("\\n" + "=" * 50)
    print("VERIFICATION SUMMARY")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - Deployment successful!")
        print("\\n✅ Your application is ready for use")
        return True
    else:
        print("❌ Some tests failed - Review deployment")
        print("\\n🔧 Check the following:")
        print("  - Environment variables are set correctly")
        print("  - Alpaca API credentials are valid")
        print("  - Database connection is working")
        print("  - Application logs for errors")
        return False

def main():
    """Main verification function"""
    if len(sys.argv) != 2:
        print("Usage: python verify-deployment.py <base-url>")
        print("Example: python verify-deployment.py https://your-app.vercel.app")
        sys.exit(1)
    
    base_url = sys.argv[1]
    
    # Ensure URL has protocol
    if not base_url.startswith(('http://', 'https://')):
        base_url = 'https://' + base_url
    
    # Remove trailing slash
    base_url = base_url.rstrip('/')
    
    success = run_verification(base_url)
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()