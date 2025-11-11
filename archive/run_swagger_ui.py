#!/usr/bin/env python3
"""
Script để chạy API server và tự động mở Swagger UI
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

def start_api_server():
    """Khởi động API server"""
    port = get_api_port()
    print("🚀 Khởi động Insurance Bot API Server...")
    print(f"📍 Server sẽ chạy tại: http://localhost:{port}")

    # Chạy API server
    process = subprocess.Popen([
        sys.executable, "core/insurance_api_simple.py"
    ], cwd=os.path.dirname(__file__))

    # Đợi server khởi động
    print("⏳ Đang khởi tạo server...")
    for i in range(30):  # Đợi tối đa 30 giây
        if check_api_server():
            print("✅ API Server đã sẵn sàng!")
            return process
        time.sleep(1)
        print(f"   Đang chờ... ({i+1}/30)")

    print("❌ API Server không thể khởi động trong 30 giây")
    process.terminate()
    return None

def open_swagger_ui():
    """Mở Swagger UI trong browser"""
    port = get_api_port()
    swagger_url = f"http://localhost:{port}/api/docs"

    print(f"🌐 Mở Swagger UI: {swagger_url}")
    print("📚 Swagger UI sẽ hiển thị:")
    print("   - Interactive API documentation")
    print("   - Try-it-out functionality")
    print("   - Request/Response examples")
    print("   - Schema definitions")

    try:
        webbrowser.open(swagger_url)
        print("✅ Đã mở browser!")
    except Exception as e:
        print(f"❌ Không thể mở browser tự động: {e}")
        print(f"   Vui lòng truy cập thủ công: {swagger_url}")

def main():
    """Main function"""
    print("🤖 Insurance Bot API - Swagger UI Launcher")
    print("=" * 50)

    # Kiểm tra xem server đã chạy chưa
    if check_api_server():
        print("✅ API Server đã đang chạy!")
        open_swagger_ui()
        return

    # Khởi động server
    process = start_api_server()
    if process:
        open_swagger_ui()

        print("\n" + "=" * 50)
        print("🎯 Hướng dẫn sử dụng Swagger UI:")
        print("1. Trong browser, bạn sẽ thấy Swagger UI")
        print("2. Click vào endpoint 'POST /chat'")
        print("3. Click 'Try it out'")
        print("4. Nhập câu hỏi trong 'message' field")
        print("5. Click 'Execute' để test")
        print("\n🛑 Nhấn Ctrl+C để dừng server")

        try:
            process.wait()
        except KeyboardInterrupt:
            print("\n👋 Đang dừng server...")
            process.terminate()
            process.wait()
            print("✅ Đã dừng server")

if __name__ == "__main__":
    main()
