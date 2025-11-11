#!/usr/bin/env python3
"""
Kiểm tra status của MiniRAG để xem data được load như thế nào
"""

import os
import sys
import json
sys.path.append('/Volumes/data/MINIRAG/MiniRAG')

# Load config
import configparser
config = configparser.ConfigParser()
config.read('/Volumes/data/MINIRAG/config/insurance_config.ini')

working_dir = config.get('DEFAULT', 'WORKING_DIR', fallback='./insurance_rag')

print("🔍 Checking MiniRAG status...")
print(f"Working directory: {working_dir}")

# Check files
files_to_check = [
    'kv_store_doc_status.json',
    'kv_store_llm_response_cache.json',
    'kv_store_full_docs.json',
    'kv_store_text_chunks.json',
    'vdb_chunks.json',
    'vdb_entities.json',
    'vdb_relationships.json',
    'graph_chunk_entity_relation.graphml'
]

for filename in files_to_check:
    filepath = os.path.join(working_dir, filename)
    if os.path.exists(filepath):
        size = os.path.getsize(filepath)
        print(f"✅ {filename}: {size} bytes")

        # Try to read JSON files
        if filename.endswith('.json'):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        print(f"   📊 Keys: {list(data.keys())[:5]}...")  # First 5 keys
                        print(f"   📊 Total items: {len(data)}")
                    elif isinstance(data, list):
                        print(f"   📊 Total items: {len(data)}")
                        if len(data) > 0:
                            print(f"   📊 Sample: {str(data[0])[:100]}...")
            except Exception as e:
                print(f"   ❌ Error reading: {e}")
    else:
        print(f"❌ {filename}: Not found")

# Check Neo4J data count
print("\n🔍 Checking Neo4J data...")
import asyncio
from neo4j import AsyncGraphDatabase

async def check_neo4j():
    neo4j_driver = AsyncGraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"])
    )

    try:
        async with neo4j_driver.session() as session:
            # Count documents
            result = await session.run("""
                MATCH (d)
                WHERE (d:LegalDocument OR d:InsuranceRulesDocument OR d:InsuranceDocument)
                RETURN count(d) as count
            """)
            record = await result.single()
            print(f"📄 Neo4J documents: {record['count']}")

            # Sample document
            result = await session.run("""
                MATCH (d)
                WHERE (d:LegalDocument OR d:InsuranceRulesDocument OR d:InsuranceDocument)
                RETURN d.title as title, left(d.full_content, 200) as content
                LIMIT 1
            """)
            record = await result.single()
            if record:
                print(f"📄 Sample title: {record['title']}")
                print(f"📄 Sample content: {record['content'][:100]}...")

    finally:
        await neo4j_driver.close()

asyncio.run(check_neo4j())

print("\n💡 Recommendations:")
print("1. Re-run load_neo4j_to_minirag.py to reload all data")
print("2. Check if async embedding function is working")
print("3. Try with lower similarity threshold (default 0.2 might be too high)")
