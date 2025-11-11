#!/usr/bin/env python3
"""
Load configuration from deploy.env file
"""

import os
import configparser
from pathlib import Path

def load_env_config(env_file='.env'):
    """
    Load configuration from .env file and set environment variables
    """
    env_path = Path(env_file)

    if not env_path.exists():
        print(f"⚠️  File {env_file} không tồn tại, sử dụng config mặc định")
        return load_default_config()

    print(f"📁 Loading config from: {env_file}")

    # Read .env file and set environment variables
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()

                # Expand environment variables in value
                value = os.path.expandvars(value)

                os.environ[key] = value
                print(f"✅ {key} = {value}")

    print("🎉 Configuration loaded successfully!")
    return True

def load_default_config():
    """
    Load default configuration from insurance_config.ini
    """
    print("📁 Loading default config from: config/insurance_config.ini")

    config = configparser.ConfigParser()
    config_path = Path('config/insurance_config.ini')

    if not config_path.exists():
        print("❌ Default config file not found!")
        return False

    config.read(config_path)

    # Load config to environment variables
    if 'DEFAULT' in config:
        for key in config['DEFAULT']:
            os.environ[key.upper()] = str(config['DEFAULT'][key])
            print(f"✅ {key.upper()} = {config['DEFAULT'][key]}")

    print("🎉 Default configuration loaded successfully!")
    return True

def print_current_config():
    """
    Print current environment configuration
    """
    print("\n📋 CURRENT CONFIGURATION:")
    print("=" * 50)

    config_keys = [
        'API_HOST', 'API_PORT',
        'NEO4J_URI', 'NEO4J_USERNAME',
        'OPENAI_API_KEY', 'OPENAI_LLM_MODEL',
        'WORKING_DIR', 'KV_STORAGE', 'VECTOR_STORAGE', 'GRAPH_STORAGE',
        'TOP_K', 'COSINE_THRESHOLD'
    ]

    for key in config_keys:
        value = os.environ.get(key, 'Not set')
        if 'API_KEY' in key and value != 'Not set':
            # Hide API key for security
            value = '***' + value[-4:] if len(value) > 4 else value
        print(f"{key:<20} = {value}")

    print("=" * 50)

if __name__ == "__main__":
    import sys

    env_file = '.env'
    if len(sys.argv) > 1:
        env_file = sys.argv[1]

    print("⚙️  Loading Insurance Bot Configuration")
    print(f"📄 Config file: {env_file}")
    print("-" * 40)

    success = load_env_config(env_file)
    if success:
        print_current_config()
    else:
        print("❌ Failed to load configuration!")
        sys.exit(1)
