#!/usr/bin/env python3
"""
Script để load dữ liệu từ Neo4J vào MiniRAG system
"""

import os
import sys
import asyncio
sys.path.append('/Volumes/data/MINIRAG/MiniRAG')

# Load config
import configparser
config = configparser.ConfigParser()
config.read('/Volumes/data/MINIRAG/config/insurance_config.ini')

# Set environment variables from config
for key in config['DEFAULT']:
    os.environ[key.upper()] = str(config['DEFAULT'][key])

from minirag import MiniRAG, QueryParam
from minirag.utils import EmbeddingFunc
from neo4j import AsyncGraphDatabase

async def load_documents_to_rag():
    """Load tất cả documents từ Neo4J vào MiniRAG"""
    print("🚀 LOAD DOCUMENTS TỪ NEO4J VÀO MINIRAG")
    print("=" * 60)

    # Kiểm tra loại embedding
    embedding_type = config.get('DEFAULT', 'EMBEDDING_TYPE', fallback='dummy')

    # Setup embedding function
    if embedding_type == 'openai':
        try:
            from minirag.llm.openai import openai_embed
            api_key = config.get('DEFAULT', 'OPENAI_API_KEY', fallback=os.environ.get('OPENAI_API_KEY'))
            base_url = config.get('DEFAULT', 'OPENAI_BASE_URL', fallback=None)

            embedding_func = EmbeddingFunc(
                embedding_dim=1536,
                max_token_size=8000,
                func=lambda texts: openai_embed(
                    texts,
                    model=config.get('DEFAULT', 'EMBEDDING_MODEL', fallback='text-embedding-3-small'),
                    api_key=api_key,
                    base_url=base_url
                ),
            )
            print("✅ Sử dụng OpenAI embeddings")
        except ImportError:
            print("⚠️  Không thể import OpenAI, chuyển sang dummy")
            embedding_type = 'dummy'
    else:
        embedding_type = 'dummy'

    if embedding_type == 'dummy':
        embedding_func = EmbeddingFunc(
            embedding_dim=384,
            max_token_size=1000,
            func=lambda texts: [[0.1] * 384 for _ in texts]
        )
        print("📝 Sử dụng dummy embeddings")

    # Khởi tạo MiniRAG
    rag = MiniRAG(
        working_dir=config.get('DEFAULT', 'WORKING_DIR', fallback='./insurance_rag'),
        kv_storage=config.get('DEFAULT', 'KV_STORAGE', fallback='JsonKVStorage'),
        vector_storage=config.get('DEFAULT', 'VECTOR_STORAGE', fallback='NanoVectorDBStorage'),
        graph_storage=config.get('DEFAULT', 'GRAPH_STORAGE', fallback='Neo4JStorage'),
        llm_model_func=None,
        embedding_func=embedding_func,
    )

    # Kết nối Neo4J
    driver = AsyncGraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"])
    )

    try:
        async with driver.session() as session:
            # Lấy tất cả documents có content
            result = await session.run("""
                MATCH (d)
                WHERE (d:LegalDocument OR d:InsuranceRulesDocument OR d:InsuranceDocument)
                AND d.full_content IS NOT NULL
                RETURN d.filename as filename, d.title as title, d.full_content as content
            """)

            documents = []
            async for record in result:
                filename = record['filename'] or 'unknown'
                title = record['title'] or 'No title'
                content = record['content'] or ''

                # Tạo document text với metadata
                doc_text = f"""
Tiêu đề: {title}
File: {filename}

{content}
                """.strip()

                documents.append(doc_text)
                print(f"📄 Loaded: {filename} - {title[:50]}...")

            print(f"\\n📊 Tổng số documents: {len(documents)}")

            if documents:
                print("\\n⏳ Đang insert vào MiniRAG...")
                await rag.ainsert(documents)
                print("✅ Đã insert tất cả documents vào MiniRAG!")
            else:
                print("⚠️  Không có documents nào để load")

    finally:
        await driver.close()

    # Test query
    print("\\n🧪 Test query mẫu:")
    test_queries = [
        "Bảo hiểm là gì?",
        "Bảo hiểm xe máy là gì?",
        "Điều kiện tham gia bảo hiểm"
    ]

    for query in test_queries:
        print(f"\\n❓ Query: {query}")
        try:
            response = await rag.aquery(query, param=QueryParam(mode="naive"))
            print(f"📄 Answer: {response[:200]}..." if len(response) > 200 else f"📄 Answer: {response}")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(load_documents_to_rag())
