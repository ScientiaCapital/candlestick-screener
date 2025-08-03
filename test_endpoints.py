#!/usr/bin/env python3
"""
Simple script to test the Flask backend endpoints
"""
import requests
import json

def test_endpoint(url, headers=None, method="GET"):
    """Test a single endpoint"""
    print(f"\n🧪 Testing {method} {url}")
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        else:
            response = requests.post(url, headers=headers, timeout=10)
        
        print(f"   Status: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            try:
                data = response.json()
                print(f"   JSON Response: {json.dumps(data, indent=2)}")
            except:
                print(f"   Response: {response.text[:200]}...")
        else:
            print(f"   Response length: {len(response.text)} chars")
            if 'html' in response.text.lower():
                print("   ✅ HTML content detected")
                
    except Exception as e:
        print(f"   ❌ Error: {e}")

def main():
    """Test main Flask endpoints"""
    base_url = "http://127.0.0.1:5000"
    
    print("🚀 Testing Flask Backend Endpoints")
    print("=" * 50)
    
    # Test main endpoints
    endpoints = [
        "/",
        "/stats", 
        "/health",
        "/?pattern=CDLDOJI"
    ]
    
    for endpoint in endpoints:
        test_endpoint(f"{base_url}{endpoint}")
    
    # Test with CSRF headers for POST requests
    csrf_headers = {
        'X-Requested-With': 'XMLHttpRequest',
        'Content-Type': 'application/json'
    }
    
    print(f"\n🔒 Testing with CSRF headers:")
    test_endpoint(f"{base_url}/stats", headers=csrf_headers)
    
    print("\n" + "=" * 50)
    print("🎯 Testing Summary:")
    print("- If you see status 200, the endpoint works!")
    print("- If you see status 403, CSRF protection is active")
    print("- If you see HTML content, the frontend is working")

if __name__ == "__main__":
    main()