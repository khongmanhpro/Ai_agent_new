#!/usr/bin/env python3
"""
Kiểm tra dữ liệu trong MiniRAG
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
from openai import AsyncOpenAI

async def async_embedding_func(texts):
    """Async OpenAI embedding function"""
    try:
        client = AsyncOpenAI(
            api_key=config.get('DEFAULT', 'OPENAI_API_KEY'),
            base_url=config.get('DEFAULT', 'OPENAI_BASE_URL')
        )

        response = await client.embeddings.create(
            input=texts,
            model=config.get('DEFAULT', 'EMBEDDING_MODEL', fallback='text-embedding-3-small')
        )
        return [data.embedding for data in response.data]
    except Exception as e:
        print(f"❌ Async embedding error: {e}")
        return [[0.1] * 1536 for _ in texts]

async def check_minirag_data():
    """Kiểm tra dữ liệu trong MiniRAG"""
    print("🔍 Checking MiniRAG data...")

    working_dir = config.get('DEFAULT', 'WORKING_DIR', fallback='./insurance_rag')

    rag = MiniRAG(
        working_dir=working_dir,
        llm_model_func=gpt_4o_mini_complete,
        llm_model_max_token_size=int(config.get('DEFAULT', 'OPENAI_LLM_MAX_TOKENS', fallback='1000')),
        llm_model_name=config.get('DEFAULT', 'OPENAI_LLM_MODEL', fallback='gpt-4o-mini'),
        embedding_func=EmbeddingFunc(
            embedding_dim=1536,
            max_token_size=1000,
            func=async_embedding_func,
        ),
    )

    # Kiểm tra storage
    print("📊 Storage info:")
    print(f"  - Working dir: {working_dir}")

    # Thử query với các từ khóa khác nhau
    test_queries = [
        "bảo hiểm",
        "xe máy",
        "bảo hiểm bắt buộc",
        "Thông tư 04/2021"
    ]

    for query in test_queries:
        print(f"\\n🔍 Testing query: '{query}'")
        try:
            answer = await rag.aquery(query, param=QueryParam(mode="mini"))
            print(f"  Answer: {answer[:150]}...")
        except Exception as e:
            print(f"  ❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_minirag_data())
