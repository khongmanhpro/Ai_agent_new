#!/usr/bin/env python3
"""
Test API integration - Giả lập frontend gọi API
"""

import requests
import json
import time

def test_api_integration():
    """Test API endpoints"""
    base_url = "http://localhost:8001"

    print("🧪 TESTING INSURANCE BOT API...")
    print("=" * 50)

    try:
        # 1. Test health check
        print("🏥 Testing health check...")
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Health: {health_data['status']}")
            print(f"   Bot ready: {health_data['bot_ready']}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return

        # 2. Test chat endpoint
        test_messages = [
            "Bảo hiểm xe máy là gì?",
            "Quy tắc bảo hiểm nhà tù nhân?",
            "Bảo hiểm du lịch toàn cầu?"
        ]

        print("\n💬 Testing chat endpoint...")
        for i, message in enumerate(test_messages, 1):
            print(f"\n📤 [{i}/{len(test_messages)}] Sending: {message}")

            chat_request = {
                "message": message,
                "session_id": f"test_session_{i}"
            }

            start_time = time.time()
            response = requests.post(
                f"{base_url}/chat",
                json=chat_request,
                timeout=60  # Increased timeout for bot processing
            )
            end_time = time.time()

            if response.status_code == 200:
                chat_data = response.json()
                print("✅ Response received")
                print(f"   ⏱️  Processing time: {end_time - start_time:.2f}s")
                print(f"   Session: {chat_data.get('session_id', 'N/A')}")
                print(f"   Response preview: {chat_data['response'][:100]}...")
            else:
                print(f"❌ Chat failed: {response.status_code}")
                print(f"   Error: {response.text}")

        print("\n🎉 API TEST COMPLETED!")

    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION ERROR: API server không chạy!")
        print("💡 Hãy chạy API server trước:")
        print("   cd /Volumes/data/MINIRAG")
        print("   python scripts/run_api_server.py")

    except Exception as e:
        print(f"❌ Test error: {e}")

def test_api_with_curl():
    """Hướng dẫn test với curl commands"""
    print("\n🔧 TEST VỚI CURL COMMANDS:")
    print("=" * 50)

    print("# Health check:")
    print('curl -X GET "http://localhost:8001/health"')
    print()

    print("# Chat test:")
    print('''curl -X POST "http://localhost:8001/chat" \\
  -H "Content-Type: application/json" \\
  -d '{
    "message": "Bảo hiểm xe máy là gì?",
    "session_id": "test_123"
  }' ''')
    print()

    print("# API documentation:")
    print("Xem trong core/insurance_api_simple.py")
    print("Hoặc test với curl commands ở trên")

if __name__ == "__main__":
    # Run integration test
    test_api_integration()

    # Show curl examples
    test_api_with_curl()
