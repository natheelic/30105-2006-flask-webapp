#!/usr/bin/env python3
"""
Test script for IoT Flask Web Application
Tests all API endpoints and functionality
"""

import requests
import json
import time
import random
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:4000"
API_HEADERS = {"Content-Type": "application/json"}

def test_health_check():
    """Test the health check endpoint"""
    print("🔍 Testing Health Check...")
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_esp32_data_post():
    """Test posting ESP32 data"""
    print("\n📡 Testing ESP32 Data POST...")
    
    # Generate random sensor data
    test_data = {
        "temperature": round(random.uniform(20.0, 35.0), 1),
        "humidity": round(random.uniform(40.0, 80.0), 1),
        "light": round(random.uniform(0, 1000), 1),
        "device_id": f"ESP32_TEST_{random.randint(1, 999):03d}",
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/esp32/data",
            headers=API_HEADERS,
            json=test_data
        )
        print(f"Status: {response.status_code}")
        print(f"Test Data: {test_data}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ ESP32 POST failed: {e}")
        return False

def test_esp32_data_get():
    """Test getting ESP32 data"""
    print("\n📊 Testing ESP32 Data GET...")
    try:
        response = requests.get(f"{BASE_URL}/api/esp32/data?limit=10")
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Count: {data.get('count', 'N/A')}")
        print(f"First record: {data.get('data', [{}])[0] if data.get('data') else 'None'}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ ESP32 GET failed: {e}")
        return False

def test_esp32_latest():
    """Test getting latest ESP32 data"""
    print("\n🔥 Testing Latest ESP32 Data...")
    try:
        response = requests.get(f"{BASE_URL}/api/esp32/latest")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code in [200, 404]  # 404 is OK if no data
    except Exception as e:
        print(f"❌ ESP32 Latest failed: {e}")
        return False

def send_multiple_test_data(count=5):
    """Send multiple test records"""
    print(f"\n🚀 Sending {count} test records...")
    
    devices = ["ESP32_TEMP_01", "ESP32_HUMID_02", "ESP32_MULTI_03"]
    success_count = 0
    
    for i in range(count):
        test_data = {
            "temperature": round(random.uniform(18.0, 40.0), 1),
            "humidity": round(random.uniform(30.0, 90.0), 1),
            "light": round(random.uniform(0, 1500), 1),
            "device_id": random.choice(devices),
            "sensor_reading": i + 1
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/esp32/data",
                headers=API_HEADERS,
                json=test_data
            )
            if response.status_code == 200:
                success_count += 1
                print(f"✅ Record {i+1}: {test_data['device_id']} - {test_data['temperature']}°C")
            else:
                print(f"❌ Record {i+1} failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Record {i+1} error: {e}")
        
        time.sleep(0.5)  # Small delay between requests
    
    print(f"\n📈 Successfully sent {success_count}/{count} records")
    return success_count

def test_web_pages():
    """Test web page endpoints"""
    print("\n🌐 Testing Web Pages...")
    
    pages = [
        "/",
        "/esp32",
        "/add-data",
        "/about-me",
        "/data-history"
    ]
    
    success_count = 0
    for page in pages:
        try:
            response = requests.get(f"{BASE_URL}{page}")
            status = "✅" if response.status_code == 200 else "❌"
            print(f"{status} {page}: {response.status_code}")
            if response.status_code == 200:
                success_count += 1
        except Exception as e:
            print(f"❌ {page}: {e}")
    
    return success_count == len(pages)

def run_comprehensive_test():
    """Run all tests"""
    print("🧪 Starting Comprehensive IoT Flask App Test")
    print("=" * 50)
    
    results = {}
    
    # Run individual tests
    results['health'] = test_health_check()
    results['esp32_post'] = test_esp32_data_post()
    results['esp32_get'] = test_esp32_data_get()
    results['esp32_latest'] = test_esp32_latest()
    results['web_pages'] = test_web_pages()
    
    # Send multiple test data
    sent_count = send_multiple_test_data(10)
    results['bulk_data'] = sent_count >= 8  # Allow some failures
    
    # Final verification
    time.sleep(2)  # Wait for data to be processed
    test_esp32_data_get()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{test_name.upper()}: {status}")
    
    print(f"\nOVERALL: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the logs above.")
    
    return passed == total

if __name__ == "__main__":
    run_comprehensive_test()
