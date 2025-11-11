#!/usr/bin/env python3
"""
Test configuration loading
"""

import os
import configparser

def test_config_loading():
    """Test loading config from insurance_config.ini"""
    print("🔍 Testing configuration loading...")

    # Load config
    config = configparser.ConfigParser()
    config_path = 'config/insurance_config.ini'
    config.read(config_path)

    print(f"📁 Config file: {config_path}")

    if 'DEFAULT' not in config:
        print("❌ No DEFAULT section found")
        return False

    # Test server config
    api_port = config.get('DEFAULT', 'API_PORT', fallback='8001')
    api_host = config.get('DEFAULT', 'API_HOST', fallback='0.0.0.0')

    print(f"✅ API_PORT: {api_port}")
    print(f"✅ API_HOST: {api_host}")

    # Test Neo4J config
    neo4j_uri = config.get('DEFAULT', 'NEO4J_URI', fallback='')
    neo4j_user = config.get('DEFAULT', 'NEO4J_USERNAME', fallback='')

    print(f"✅ NEO4J_URI: {neo4j_uri}")
    print(f"✅ NEO4J_USERNAME: {neo4j_user}")

    # Test OpenAI config
    openai_key = config.get('DEFAULT', 'OPENAI_API_KEY', fallback='')
    openai_model = config.get('DEFAULT', 'OPENAI_LLM_MODEL', fallback='')

    print(f"✅ OPENAI_API_KEY: {'***' + openai_key[-4:] if openai_key else 'Not set'}")
    print(f"✅ OPENAI_LLM_MODEL: {openai_model}")

    # Test MiniRAG config
    working_dir = config.get('DEFAULT', 'WORKING_DIR', fallback='')
    kv_storage = config.get('DEFAULT', 'KV_STORAGE', fallback='')

    print(f"✅ WORKING_DIR: {working_dir}")
    print(f"✅ KV_STORAGE: {kv_storage}")

    return True

def test_environment_variables():
    """Test that config is loaded to environment variables"""
    print("\n🔍 Testing environment variables...")

    # Simulate loading config to env (like in the API files)
    config = configparser.ConfigParser()
    config.read('config/insurance_config.ini')

    # Load config to environment variables
    for key in config['DEFAULT']:
        os.environ[key.upper()] = str(config['DEFAULT'][key])

    # Test server config from env
    api_port = os.environ.get('API_PORT', '8001')
    api_host = os.environ.get('API_HOST', '0.0.0.0')

    print(f"✅ ENV API_PORT: {api_port}")
    print(f"✅ ENV API_HOST: {api_host}")

    return True

if __name__ == "__main__":
    print("⚙️ Testing Insurance Bot Configuration")
    print("=" * 50)

    success = True
    success &= test_config_loading()
    success &= test_environment_variables()

    print("\n" + "=" * 50)
    if success:
        print("🎉 Configuration test passed!")
        print("\n📋 Summary:")
        print("- Config file: config/insurance_config.ini")
        print("- Port: Can be changed in API_PORT setting")
        print("- Host: Can be changed in API_HOST setting")
        print("- All settings are loaded to environment variables")
    else:
        print("❌ Configuration test failed!")

    print("\n💡 To change port for deployment:")
    print("   1. Edit config/insurance_config.ini")
    print("   2. Change API_PORT=8001 to your desired port")
    print("   3. Restart the API server")
