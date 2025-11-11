#!/usr/bin/env python3
"""
Script test Insurance Bot với một câu hỏi mẫu
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

from neo4j import AsyncGraphDatabase
from openai import AsyncOpenAI

async def test_insurance_bot():
    """Test Insurance Bot với một câu hỏi mẫu"""
    print("🧪 TEST INSURANCE BOT")
    print("=" * 50)

    # Test Neo4J connection
    print("1. Kiểm tra Neo4J connection...")
    try:
        driver = AsyncGraphDatabase.driver(
            os.environ["NEO4J_URI"],
            auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"])
        )

        async with driver.session() as session:
            result = await session.run("MATCH (n) RETURN count(n) as count")
            record = await result.single()
            count = record['count']
            print(f"✅ Neo4J OK - {count} nodes")

        await driver.close()
    except Exception as e:
        print(f"❌ Neo4J Error: {e}")
        return

    # Test OpenAI connection
    print("\\n2. Kiểm tra OpenAI connection...")
    try:
        client = AsyncOpenAI(
            api_key=config.get('DEFAULT', 'OPENAI_API_KEY'),
            base_url=config.get('DEFAULT', 'OPENAI_BASE_URL')
        )

        # Simple test
        response = await client.embeddings.create(
            model="text-embedding-3-small",
            input=["test"],
            encoding_format="float"
        )

        print("✅ OpenAI OK - Embeddings working")

    except Exception as e:
        print(f"❌ OpenAI Error: {e}")
        return

    # Test keyword extraction
    print("\\n3. Test keyword extraction...")
    def extract_keywords(question: str):
        stop_words = ['là', 'cái', 'đó', 'đây', 'ở', 'tại', 'và', 'hoặc', 'như', 'thế nào', 'gì', 'được', 'có', 'không']
        words = question.split()
        keywords = []

        for word in words:
            if len(word) > 2 and word not in stop_words:
                keywords.append(word)

        if not keywords:
            keywords = [question]

        insurance_terms = ['bảo hiểm', 'bảo', 'hiểm', 'xe', 'máy', 'ô tô', 'phương tiện', 'thiệt hại', 'tai nạn', 'sức khỏe', 'du lịch', 'nhân thọ']

        prioritized_keywords = []
        for term in insurance_terms:
            if term in question:
                prioritized_keywords.append(term)

        final_keywords = prioritized_keywords + [k for k in keywords if k not in prioritized_keywords]
        return final_keywords[:5]

    question = "bảo hiểm xe máy là gì?"
    keywords = extract_keywords(question)
    print(f"📝 Question: {question}")
    print(f"🔍 Keywords: {keywords}")

    # Test Neo4J search
    print("\\n4. Test Neo4J search...")
    try:
        driver = AsyncGraphDatabase.driver(
            os.environ["NEO4J_URI"],
            auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"])
        )

        async with driver.session() as session:
            context_parts = []

            for keyword in keywords[:3]:
                result = await session.run("""
                    MATCH (d)
                    WHERE (d:LegalDocument OR d:InsuranceRulesDocument OR d:InsuranceDocument)
                    AND d.full_content IS NOT NULL
                    AND toLower(d.full_content) CONTAINS toLower($keyword)
                    RETURN d.title as title, left(d.full_content, 500) as content
                    LIMIT 1
                """, keyword=keyword)

                async for record in result:
                    title = record['title'] or 'Unknown'
                    content = record['content'] or ''

                    # Clean content
                    if content.startswith('---'):
                        lines = content.split('\\n')
                        try:
                            end_yaml = lines[1:].index('---') + 1
                            content = '\\n'.join(lines[end_yaml:]).strip()
                        except:
                            pass

                    context_parts.append(f"Tiêu đề: {title}\\nNội dung: {content[:200]}...")
                    break  # Chỉ lấy 1 document per keyword

            context = '\\n\\n'.join(context_parts[:2])  # Max 2 documents
            print("📄 Context found:")
            print(context[:300] + "..." if len(context) > 300 else context)

        await driver.close()

    except Exception as e:
        print(f"❌ Neo4J Search Error: {e}")
        return

    # Test OpenAI response generation
    print("\\n5. Test OpenAI response generation...")
    try:
        system_prompt = """Bạn là nhân viên tư vấn chuyên nghiệp của Công ty đại lý bảo hiểm FISS.
Trả lời một cách thân thiện, chuyên nghiệp và chính xác dựa trên thông tin được cung cấp."""

        user_prompt = f"""
Dựa trên thông tin sau đây từ cơ sở dữ liệu bảo hiểm:

{context}

Hãy trả lời câu hỏi của khách hàng: {question}

Lưu ý: Trả lời ngắn gọn, thân thiện và không đề cập đến nguồn tài liệu.
"""

        response = await client.chat.completions.create(
            model=config.get('DEFAULT', 'OPENAI_LLM_MODEL', fallback='gpt-4o-mini'),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )

        answer = response.choices[0].message.content.strip()
        print("🤖 Generated Response:")
        print(answer)

        print("\\n✅ TẤT CẢ TEST THÀNH CÔNG!")
        print("🎉 Insurance Bot đã sẵn sàng!")

    except Exception as e:
        print(f"❌ OpenAI Generation Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_insurance_bot())
