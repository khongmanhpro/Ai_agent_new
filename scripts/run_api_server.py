#!/usr/bin/env python3
"""
Script để chạy Insurance API Server
"""

import os
import sys
import subprocess

def run_api_server():
    """Chạy API server"""
    print("🚀 Starting Insurance Bot API Server...")

    # Đường dẫn đến API file
    api_file = os.path.join(os.path.dirname(__file__), "..", "core", "insurance_api_simple.py")

    if not os.path.exists(api_file):
        print(f"❌ API file not found: {api_file}")
        return

    # Chạy API server
    try:
        subprocess.run([
            sys.executable, api_file
        ], cwd=os.path.dirname(api_file))
    except KeyboardInterrupt:
        print("\n👋 API Server stopped")
    except Exception as e:
        print(f"❌ Error running API server: {e}")

if __name__ == "__main__":
    run_api_server()
