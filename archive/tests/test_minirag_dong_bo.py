#!/usr/bin/env python3
"""
Test MiniRAG hoàn toàn sync
"""

import os
import sys
sys.path.append('/Volumes/data/MINIRAG/MiniRAG')

# Load config
import configparser
config = configparser.ConfigParser()
config.read('/Volumes/data/MINIRAG/config/insurance_config.ini')

# Set environment variables
for key in config['DEFAULT']:
    os.environ[key.upper()] = str(config['DEFAULT'][key])

from minirag import MiniRAG, QueryParam
from minirag.llm import gpt_4o_mini_complete
from minirag.utils import EmbeddingFunc

async def dummy_embedding_func(texts):
    """Async dummy embedding function"""
    return [[0.1] * 1536 for _ in texts]

def test_sync_minirag():
    """Test MiniRAG sync"""
    print("🧪 Testing sync MiniRAG...")

    working_dir = config.get('DEFAULT', 'WORKING_DIR', fallback='./insurance_rag')

    rag = MiniRAG(
        working_dir=working_dir,
        llm_model_func=gpt_4o_mini_complete,
        llm_model_max_token_size=int(config.get('DEFAULT', 'OPENAI_LLM_MAX_TOKENS', fallback='1000')),
        llm_model_name=config.get('DEFAULT', 'OPENAI_LLM_MODEL', fallback='gpt-4o-mini'),
        embedding_func=EmbeddingFunc(
            embedding_dim=1536,
            max_token_size=1000,
            func=dummy_embedding_func,
        ),
    )

    # Add test document
    test_text = "Bảo hiểm xe máy là loại bảo hiểm bắt buộc cho chủ xe máy."
    print("📥 Inserting test document...")
    rag.insert(test_text)

    # Query
    question = "bảo hiểm xe máy là gì?"
    print(f"❓ Question: {question}")

    try:
        answer = rag.query(question, param=QueryParam(mode="mini"))
        print(f"💬 Answer: {answer}")
        print("✅ Sync MiniRAG test successful!")
        return True
    except Exception as e:
        print(f"❌ Sync MiniRAG test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_sync_minirag()
    if success:
        print("\\n🎉 Sync MiniRAG works!")
    else:
        print("\\n💥 Sync MiniRAG failed!")
