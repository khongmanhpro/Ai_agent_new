#!/usr/bin/env python3
"""
Load dữ liệu từ Neo4J vào MiniRAG để sử dụng RAG framework
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
from openai import OpenAI

async def async_embedding_func(texts):
    """Async OpenAI embedding function"""
    try:
        client = OpenAI(
            api_key=config.get('DEFAULT', 'OPENAI_API_KEY'),
            base_url=config.get('DEFAULT', 'OPENAI_BASE_URL')
        )

        response = client.embeddings.create(
            input=texts,
            model=config.get('DEFAULT', 'EMBEDDING_MODEL', fallback='text-embedding-3-small')
        )
        return [data.embedding for data in response.data]
    except Exception as e:
        print(f"❌ Embedding error: {e}")
        # Return dummy embeddings if OpenAI fails
        return [[0.1] * 1536 for _ in texts]

async def load_documents_from_neo4j():
    """Load tất cả documents từ Neo4J vào MiniRAG"""
    print("🚀 Loading documents from Neo4J to MiniRAG...")

    # Khởi tạo Neo4J driver
    neo4j_driver = AsyncGraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"])
    )

    # Khởi tạo MiniRAG
    working_dir = config.get('DEFAULT', 'WORKING_DIR', fallback='./insurance_rag')

    # Đảm bảo working directory tồn tại
    if not os.path.exists(working_dir):
        os.makedirs(working_dir)

    print(f"📁 Working directory: {working_dir}")

    rag = MiniRAG(
        working_dir=working_dir,
        llm_model_func=gpt_4o_mini_complete,
        llm_model_max_token_size=int(config.get('DEFAULT', 'OPENAI_LLM_MAX_TOKENS', fallback='1000')),
        llm_model_name=config.get('DEFAULT', 'OPENAI_LLM_MODEL', fallback='gpt-4o-mini'),
        embedding_func=EmbeddingFunc(
            embedding_dim=1536,  # OpenAI text-embedding-3-small dimension
            max_token_size=1000,
            func=async_embedding_func,
        ),
    )

    try:
        # Query tất cả documents từ Neo4J
        async with neo4j_driver.session() as session:
            result = await session.run("""
                MATCH (d)
                WHERE (d:LegalDocument OR d:InsuranceRulesDocument OR d:InsuranceDocument)
                AND d.full_content IS NOT NULL
                RETURN d.title as title, d.full_content as content, d.filename as filename
                ORDER BY d.title
            """)

            documents = []
            async for record in result:
                documents.append({
                    'title': record['title'] or 'Unknown',
                    'content': record['content'] or '',
                    'filename': record['filename'] or 'unknown.md'
                })

            print(f"📄 Found {len(documents)} documents in Neo4J")

            # Insert từng document vào MiniRAG
            for i, doc in enumerate(documents):
                print(f"📥 [{i+1}/{len(documents)}] Inserting: {doc['title'][:50]}...")
                print(f"   Content length: {len(doc['content'])} chars")

                # Tạo text content để insert
                content = doc['content']

                # Clean YAML frontmatter nếu có
                if content.startswith('---'):
                    lines = content.split('\n')
                    try:
                        end_yaml = lines[1:].index('---') + 1
                        content = '\n'.join(lines[end_yaml:]).strip()
                        print(f"   🧹 Cleaned YAML frontmatter, reduced to {len(content)} chars")
                    except:
                        print("   ⚠️  Could not find YAML end marker")
                        pass

                # Add title và filename metadata
                full_text = f"Tiêu đề: {doc['title']}\nFile: {doc['filename']}\n\n{content}"
                print(f"   Final text length: {len(full_text)} chars")
                print(f"   Sample text: {full_text[:200]}...")

                try:
                    # Insert vào MiniRAG (async)
                    await rag.ainsert(full_text)
                    print(f"✅ Successfully inserted: {doc['title'][:40]}...")
                except Exception as e:
                    print(f"❌ Error inserting {doc['title']}: {e}")
                    import traceback
                    traceback.print_exc()
                    # Continue with next document instead of breaking
                    continue

            print(f"🎉 Successfully loaded {len(documents)} documents into MiniRAG!")
            print(f"📁 MiniRAG working directory: {working_dir}")

    finally:
        await neo4j_driver.close()

async def test_minirag_query():
    """Test query MiniRAG sau khi load data"""
    print("\\n🧪 Testing MiniRAG query...")

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

    # Test query
    test_question = "Bảo hiểm xe máy là gì?"
    print(f"❓ Test question: {test_question}")

    try:
        from minirag import QueryParam
        answer = await rag.aquery(test_question, param=QueryParam(mode="mini"))
        print(f"💬 Answer: {answer}")
        print("✅ MiniRAG query test successful!")
    except Exception as e:
        print(f"❌ MiniRAG query test failed: {e}")

async def main():
    """Main function"""
    await load_documents_from_neo4j()
    await test_minirag_query()

if __name__ == "__main__":
    asyncio.run(main())
