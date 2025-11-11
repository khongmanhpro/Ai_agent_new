#!/usr/bin/env python3
"""
Script để chạy Demo Swagger UI - không cần MiniRAG/OpenAI
"""

import os
import sys
import time
import webbrowser
import subprocess
import signal

def get_api_port():
    """Get API port from config"""
    try:
        import configparser
        config = configparser.ConfigParser()
        config.read('config/insurance_config.ini')
        return int(config.get('DEFAULT', 'API_PORT', fallback='8001'))
    except:
        return 8001

def check_api_server(base_url=None):
    """Kiểm tra API server có chạy không"""
    if base_url is None:
        port = get_api_port()
        base_url = f"http://localhost:{port}"

    try:
        import requests
        response = requests.get(f"{base_url}/", timeout=5)
        return response.status_code == 200
    except:
        return False

def start_demo_server():
    """Khởi động demo API server"""
    port = get_api_port()
    print("🚀 Khởi động Insurance Bot API Demo Server...")
    print(f"📍 Server sẽ chạy tại: http://localhost:{port}")
    print("⚠️  DEMO MODE: Không cần MiniRAG/OpenAI")

    # Chạy demo API server
    process = subprocess.Popen([
        sys.executable, "demo_swagger_api.py"
    ], cwd=os.path.dirname(__file__))

    # Đợi server khởi động
    print("⏳ Đang khởi tạo demo server...")
    for i in range(10):  # Đợi tối đa 10 giây cho demo server
        if check_api_server():
            print("✅ Demo API Server đã sẵn sàng!")
            return process
        time.sleep(1)
        print(f"   Đang chờ... ({i+1}/10)")

    print("❌ Demo API Server không thể khởi động trong 10 giây")
    process.terminate()
    return None

def open_swagger_ui():
    """Mở Swagger UI trong browser"""
    port = get_api_port()
    swagger_url = f"http://localhost:{port}/api/docs"

    print(f"🌐 Mở Swagger UI Demo: {swagger_url}")
    print("📚 Demo Swagger UI sẽ hiển thị:")
    print("   - Interactive API documentation")
    print("   - Try-it-out functionality")
    print("   - Demo chat responses")
    print("   - Schema definitions")
    print()
    print("🎯 Cách test:")
    print("1. Click 'POST /chat'")
    print("2. Click 'Try it out'")
    print("3. Nhập message bất kỳ")
    print("4. Click 'Execute'")
    print("5. Xem demo response")

    try:
        webbrowser.open(swagger_url)
        print("✅ Đã mở browser!")
    except Exception as e:
        print(f"❌ Không thể mở browser tự động: {e}")
        print(f"   Vui lòng truy cập thủ công: {swagger_url}")

def main():
    """Main function"""
    print("🎭 Insurance Bot API Demo - Swagger UI Launcher")
    print("=" * 60)
    print("🚀 Chế độ DEMO: Không cần MiniRAG, OpenAI, Neo4J")
    print("📚 Chỉ để demo Swagger UI interface")
    print("=" * 60)

    # Kiểm tra xem server đã chạy chưa
    if check_api_server():
        print("✅ Demo API Server đã đang chạy!")
        open_swagger_ui()
        return

    # Khởi động demo server
    process = start_demo_server()
    if process:
        open_swagger_ui()

        print("\n" + "=" * 60)
        print("🎯 Demo Swagger UI đã sẵn sàng!")
        print("💡 Demo responses sẽ có tag [DEMO MODE]")
        print("🔄 Để chạy bot thật với MiniRAG:")
        print("   python run_swagger_ui.py  # (sẽ cần Neo4J + OpenAI)")
        print("\n🛑 Nhấn Ctrl+C để dừng demo server")

        try:
            process.wait()
        except KeyboardInterrupt:
            print("\n👋 Đang dừng demo server...")
            process.terminate()
            process.wait()
            print("✅ Đã dừng demo server")

if __name__ == "__main__":
    main()
