#!/usr/bin/env python3
"""
Debug MiniRAG retrieval để tìm hiểu tại sao không tìm thấy context
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
            base_url=config.get('DEFAULT', 'OPENAI_API_BASE')
        )

        response = await client.embeddings.create(
            input=texts,
            model=config.get('DEFAULT', 'EMBEDDING_MODEL', fallback='text-embedding-3-small')
        )
        return [data.embedding for data in response.data]
    except Exception as e:
        print(f"❌ Embedding error: {e}")
        return [[0.1] * 1536 for _ in texts]

async def debug_retrieval():
    """Debug retrieval với different parameters"""
    print("🔍 Debug MiniRAG retrieval...")

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

    # Test queries với different thresholds
    test_queries = [
        "bảo hiểm xe máy",
        "bảo hiểm bắt buộc",
        "xe máy",
        "thông tư 04/2021"
    ]

    thresholds = [0.2, 0.1, 0.05, 0.01]

    for query in test_queries:
        print(f"\n🔍 Testing query: '{query}'")
        print("-" * 50)

        for threshold in thresholds:
            print(f"\n📊 Threshold: {threshold}")

            try:
                # Try different modes
                for mode in ["mini", "global"]:
                    param = QueryParam(mode=mode, similarity_threshold=threshold)
                    answer = await rag.aquery(query, param=param)

                    print(f"  Mode '{mode}': {answer[:100]}...")

            except Exception as e:
                print(f"  ❌ Error: {e}")

    # Try to get raw retrieval results
    print("\n🔍 Raw retrieval test...")
    try:
        # Access internal retrieval
        query = "bảo hiểm xe máy"
        print(f"Testing raw retrieval for: '{query}'")

        # This is internal method, might not work
        # But let's try to understand what's happening

        # Check if we can access vector storage
        if hasattr(rag, 'vector_db_storage'):
            print("Vector DB storage found")
        else:
            print("No vector DB storage")

        if hasattr(rag, 'graph'):
            print("Graph found")
            nodes = rag.graph.nodes()
            print(f"Graph has {len(nodes)} nodes")
            for i, node in enumerate(nodes):
                if i < 5:  # Show first 5
                    print(f"  Node {i}: {node}")
        else:
            print("No graph found")

    except Exception as e:
        print(f"❌ Raw retrieval error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_retrieval())
