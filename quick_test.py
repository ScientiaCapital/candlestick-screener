#!/usr/bin/env python3
"""Quick test script for the candlestick screener"""
import requests

# Test pattern analysis
print("🔍 Testing pattern analysis...")
try:
    response = requests.get('http://127.0.0.1:5555/?pattern=CDLDOJI', timeout=10)
    if response.status_code == 200 and 'html' in response.text.lower():
        print("✅ Pattern analysis working!")
    else:
        print(f"❌ Pattern analysis failed: {response.status_code}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test API stats
print("\n📊 Testing API stats...")
headers = {'X-Requested-With': 'XMLHttpRequest'}
try:
    response = requests.get('http://127.0.0.1:5555/stats', headers=headers, timeout=5)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ API working! Loaded {data.get('symbols_count', 0)} symbols")
        print(f"   Cache: {data['cache']['status']}")
        print(f"   Rate limits: {data['rate_limits']['status']}")
    else:
        print(f"❌ API failed: {response.status_code}")
except Exception as e:
    print(f"❌ Error: {e}")

print(f"\n🌐 Access the applications at:")
print(f"   • Next.js Frontend: http://localhost:3000")
print(f"   • Flask Backend:    http://127.0.0.1:5555")