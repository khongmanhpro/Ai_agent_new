#!/usr/bin/env python3
"""
Script để clear cache của Insurance Bot
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

# Insurance Bot Prompt (rút gọn)
INSURANCE_BOT_PROMPT = """
Bạn là nhân viên tư vấn chuyên nghiệp của Công ty đại lý bảo hiểm FISS.
Trả lời một cách thân thiện, chuyên nghiệp và chính xác dựa trên thông tin được cung cấp.
"""

class CacheClearBot:
    def __init__(self):
        print("🧹 Clearing cache and testing...")
        self.neo4j_driver = AsyncGraphDatabase.driver(
            os.environ["NEO4J_URI"],
            auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"])
        )

        self.openai_client = AsyncOpenAI(
            api_key=config.get('DEFAULT', 'OPENAI_API_KEY'),
            base_url=config.get('DEFAULT', 'OPENAI_BASE_URL')
        )

        # Fresh cache - empty
        self.response_cache = {}
        print("✅ Cache cleared")

    def extract_keywords(self, question: str):
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

    async def get_relevant_context(self, question: str) -> str:
        keywords = self.extract_keywords(question.lower())
        context_parts = []

        async with self.neo4j_driver.session() as session:
            for keyword in keywords[:3]:
                result = await session.run("""
                    MATCH (d)
                    WHERE (d:LegalDocument OR d:InsuranceRulesDocument OR d:InsuranceDocument)
                    AND d.full_content IS NOT NULL
                    AND toLower(d.full_content) CONTAINS toLower($keyword)
                    RETURN d.title as title, left(d.full_content, 1000) as content
                    LIMIT 2
                """, keyword=keyword)

                async for record in result:
                    title = record['title'] or 'Unknown'
                    content = record['content'] or ''

                    # Clean YAML frontmatter
                    if content.startswith('---'):
                        lines = content.split('\n')
                        try:
                            end_yaml = lines[1:].index('---') + 1
                            content = '\n'.join(lines[end_yaml:]).strip()
                        except:
                            pass

                    context_parts.append(f"Tiêu đề: {title}\nNội dung: {content}")

        full_context = '\n\n'.join(context_parts[:3])
        if len(full_context) > 2000:
            full_context = full_context[:2000] + "..."

        return full_context

    async def generate_response(self, question: str, context: str) -> str:
        if len(context.strip()) < 50:
            return "Xin lỗi, tôi không tìm thấy thông tin liên quan đến câu hỏi của bạn trong cơ sở dữ liệu."

        user_prompt = f"""
Dựa trên thông tin sau đây từ cơ sở dữ liệu bảo hiểm:

{context}

Hãy trả lời câu hỏi của khách hàng: {question}

Lưu ý: Trả lời ngắn gọn, thân thiện và không đề cập đến nguồn tài liệu.
"""

        try:
            response = await self.openai_client.chat.completions.create(
                model=config.get('DEFAULT', 'OPENAI_LLM_MODEL', fallback='gpt-4o-mini'),
                messages=[
                    {"role": "system", "content": INSURANCE_BOT_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )

            answer = response.choices[0].message.content.strip()
            return answer

        except Exception as e:
            return f"Lỗi khi tạo câu trả lời: {e}"

    async def chat(self, question: str) -> str:
        print(f"🧹 CACHE CLEARED - Testing: {question}")

        context = await self.get_relevant_context(question)
        print(f"📄 Context found: {len(context)} chars")

        answer = await self.generate_response(question, context)
        return answer

    async def close(self):
        await self.neo4j_driver.close()

async def test_cache_cleared():
    print("🧹 TEST WITH CACHE CLEARED")
    print("=" * 50)

    bot = CacheClearBot()

    try:
        question = "Bảo hiểm xe máy là gì?"
        answer = await bot.chat(question)

        print("\\n" + "=" * 50)
        print("💬 ANSWER WITH CACHE CLEARED:")
        print(answer)
        print("\\n✅ CACHE CLEAR TEST COMPLETED")

    finally:
        await bot.close()

if __name__ == "__main__":
    asyncio.run(test_cache_cleared())
