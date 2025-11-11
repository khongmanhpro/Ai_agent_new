#!/usr/bin/env python3
"""
Test Swagger UI và OpenAPI specification
"""

import requests
import json
import time
import webbrowser
from typing import Dict, Any

def test_api_spec(base_url: str = "http://localhost:8001") -> bool:
    """Test OpenAPI specification endpoint"""
    print("🔍 Testing OpenAPI Specification...")

    try:
        response = requests.get(f"{base_url}/api/spec", timeout=10)
        response.raise_for_status()

        spec = response.json()

        # Validate required OpenAPI fields
        required_fields = ["openapi", "info", "paths", "components"]
        for field in required_fields:
            if field not in spec:
                print(f"❌ Missing required field: {field}")
                return False

        # Validate info section
        info = spec.get("info", {})
        if not all(key in info for key in ["title", "version"]):
            print("❌ Missing title or version in info")
            return False

        # Validate paths
        paths = spec.get("paths", {})
        required_paths = ["/health", "/chat", "/"]
        for path in required_paths:
            if path not in paths:
                print(f"❌ Missing required path: {path}")
                return False

        print("✅ OpenAPI specification is valid")
        print(f"   Title: {info.get('title')}")
        print(f"   Version: {info.get('version')}")
        print(f"   Paths: {len(paths)}")

        return True

    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to fetch API spec: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON response: {e}")
        return False

def test_swagger_ui_accessible(base_url: str = "http://localhost:8001") -> bool:
    """Test Swagger UI is accessible"""
    print("\n🔍 Testing Swagger UI accessibility...")

    try:
        response = requests.get(f"{base_url}/api/docs", timeout=10)

        if response.status_code == 200:
            print("✅ Swagger UI is accessible")
            return True
        else:
            print(f"❌ Swagger UI returned status: {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to access Swagger UI: {e}")
        return False

def test_api_functionality(base_url: str = "http://localhost:8001") -> bool:
    """Test basic API functionality through Swagger endpoints"""
    print("\n🔍 Testing API functionality...")

    try:
        # Test health endpoint
        health_response = requests.get(f"{base_url}/health", timeout=10)
        health_response.raise_for_status()
        health_data = health_response.json()

        if health_data.get("status") != "healthy":
            print("❌ Health check failed")
            return False

        print("✅ Health check passed")

        # Test chat endpoint (basic validation)
        chat_payload = {
            "message": "Hello",
            "session_id": "test_swagger"
        }

        chat_response = requests.post(f"{base_url}/chat", json=chat_payload, timeout=60)
        chat_response.raise_for_status()
        chat_data = chat_response.json()

        if "response" not in chat_data:
            print("❌ Chat response missing 'response' field")
            return False

        print("✅ Chat endpoint responded correctly")
        print(f"   Processing time: {chat_data.get('processing_time', 'N/A'):.2f}s")
        return True

    except requests.exceptions.RequestException as e:
        print(f"❌ API functionality test failed: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON response: {e}")
        return False

def open_swagger_ui(base_url: str = "http://localhost:8001"):
    """Open Swagger UI in browser"""
    swagger_url = f"{base_url}/api/docs"
    print(f"\n🌐 Opening Swagger UI: {swagger_url}")

    try:
        webbrowser.open(swagger_url)
        print("✅ Browser opened successfully")
    except Exception as e:
        print(f"❌ Failed to open browser: {e}")
        print(f"   Please manually open: {swagger_url}")

def main():
    """Main test function"""
    print("🚀 Testing Insurance Bot API with Swagger UI")
    print("=" * 60)

    base_url = "http://localhost:8001"

    # Check if API server is running
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        response.raise_for_status()
    except requests.exceptions.RequestException:
        print("❌ API server is not running!")
        print("💡 Please start the server first:")
        print("   python core/insurance_api_simple.py")
        return False

    print("✅ API server is running")

    # Run all tests
    tests = [
        test_api_spec,
        test_swagger_ui_accessible,
        test_api_functionality
    ]

    results = []
    for test_func in tests:
        try:
            result = test_func(base_url)
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)

    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")

    passed = sum(results)
    total = len(results)

    for i, (test_func, result) in enumerate(zip(tests, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {i+1}. {test_func.__name__}: {status}")

    print(f"\n📈 Overall: {passed}/{total} tests passed")

    if all(results):
        print("🎉 All tests passed! Swagger UI is working correctly.")
        open_swagger_ui(base_url)
    else:
        print("⚠️  Some tests failed. Please check the API configuration.")

    return all(results)

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
