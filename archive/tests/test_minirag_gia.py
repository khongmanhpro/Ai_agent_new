#!/usr/bin/env python3
"""
Test MiniRAG với dummy embedding để tránh lỗi OpenAI
"""

import os
import sys
import asyncio
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

def dummy_embedding_func():
    """Dummy embedding function"""
    def embed_texts(texts):
        # Return dummy embeddings
        return [[0.1] * 1536 for _ in texts]
    return embed_texts

async def test_minirag_dummy():
    """Test MiniRAG với dummy embedding"""
    print("🧪 Testing MiniRAG with dummy embedding...")

    # Khởi tạo MiniRAG
    working_dir = config.get('DEFAULT', 'WORKING_DIR', fallback='./insurance_rag')

    rag = MiniRAG(
        working_dir=working_dir,
        llm_model_func=gpt_4o_mini_complete,
        llm_model_max_token_size=int(config.get('DEFAULT', 'OPENAI_LLM_MAX_TOKENS', fallback='1000')),
        llm_model_name=config.get('DEFAULT', 'OPENAI_LLM_MODEL', fallback='gpt-4o-mini'),
        embedding_func=EmbeddingFunc(
            embedding_dim=1536,
            max_token_size=1000,
            func=dummy_embedding_func(),
        ),
    )

    # Test query
    question = "Bảo hiểm xe máy là gì?"
    print(f"❓ Question: {question}")

    try:
        answer = await rag.aquery(question, param=QueryParam(mode="mini"))
        print(f"✅ SUCCESS! Answer: {answer[:200]}...")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_minirag_dummy())
    if success:
        print("\\n🎉 MiniRAG with dummy embedding works!")
    else:
        print("\\n💥 MiniRAG failed even with dummy embedding!")
