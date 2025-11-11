#!/usr/bin/env python3
"""
Reload dữ liệu vào MiniRAG đơn giản hơn
"""

import os
import sys
import asyncio
import configparser

# Load config
config = configparser.ConfigParser()
config.read('/Volumes/data/MINIRAG/config/insurance_config.ini')

# Set environment variables
for key in config['DEFAULT']:
    os.environ[key.upper()] = str(config['DEFAULT'][key])

# Add MiniRAG path
sys.path.append('/Volumes/data/MINIRAG/MiniRAG')

from neo4j import AsyncGraphDatabase
from minirag import MiniRAG
from minirag.llm import gpt_4o_mini_complete
from minirag.utils import EmbeddingFunc

def dummy_embedding_func():
    """Dummy embedding function for testing"""
    def embed_texts(texts):
        return [[0.1] * 1536 for _ in texts]
    return embed_texts

async def reload_data_simple():
    """Reload data đơn giản vào MiniRAG"""
    print("🔄 Reloading data into MiniRAG (simple mode)...")

    # Clear old data
    working_dir = config.get('DEFAULT', 'WORKING_DIR', fallback='./insurance_rag')

    # Remove old files
    import shutil
    if os.path.exists(working_dir):
        shutil.rmtree(working_dir)
        print(f"🗑️  Removed old working directory: {working_dir}")

    os.makedirs(working_dir)
    print(f"📁 Created new working directory: {working_dir}")

    # Khởi tạo MiniRAG với dummy embedding
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

    # Khởi tạo Neo4J driver
    neo4j_driver = AsyncGraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"])
    )

    try:
        # Query documents từ Neo4J
        async with neo4j_driver.session() as session:
            result = await session.run("""
                MATCH (d)
                WHERE (d:LegalDocument OR d:InsuranceRulesDocument OR d:InsuranceDocument)
                AND d.full_content IS NOT NULL
                RETURN d.title as title, d.full_content as content, d.filename as filename
                ORDER BY d.title
                LIMIT 3  // Test với 3 documents đầu
            """)

            documents = []
            async for record in result:
                documents.append({
                    'title': record['title'] or 'Unknown',
                    'content': record['content'] or '',
                    'filename': record['filename'] or 'unknown.md'
                })

            print(f"📄 Found {len(documents)} test documents in Neo4J")

            # Insert từng document
            for i, doc in enumerate(documents):
                print(f"📥 [{i+1}/{len(documents)}] Inserting: {doc['title'][:40]}...")

                # Clean content
                content = doc['content']
                if content.startswith('---'):
                    lines = content.split('\n')
                    try:
                        end_yaml = lines[1:].index('---') + 1
                        content = '\n'.join(lines[end_yaml:]).strip()
                    except:
                        pass

                # Simple text for testing
                full_text = f"Title: {doc['title']}\n\n{content[:1000]}"  # Limit content

                try:
                    # Use sync insert
                    rag.insert(full_text)
                    print(f"✅ Successfully inserted: {doc['title'][:30]}...")
                except Exception as e:
                    print(f"❌ Error inserting {doc['title']}: {e}")
                    continue

            print(f"🎉 Successfully loaded {len(documents)} test documents into MiniRAG!")

    finally:
        await neo4j_driver.close()

async def test_reloaded_data():
    """Test data đã reload"""
    print("\\n🧪 Testing reloaded data...")

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

    from minirag import QueryParam

    test_question = "bảo hiểm"
    print(f"❓ Test question: {test_question}")

    try:
        answer = await rag.aquery(test_question, param=QueryParam(mode="mini"))
        print(f"💬 Answer: {answer}")
        print("✅ Reload test successful!")
    except Exception as e:
        print(f"❌ Reload test failed: {e}")

if __name__ == "__main__":
    asyncio.run(reload_data_simple())
    asyncio.run(test_reloaded_data())
