#!/usr/bin/env python3
"""
Test Insurance Bot một lần với câu hỏi cụ thể
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

Nhiệm vụ chính của bạn là:
- Tư vấn và giải đáp mọi thắc mắc về các sản phẩm bảo hiểm
- Hỗ trợ khách hàng tra cứu thông tin hợp đồng, quyền lợi bảo hiểm
- Hướng dẫn quy trình mua bảo hiểm, nộp hồ sơ bồi thường
- Cung cấp báo giá và tư vấn sản phẩm phù hợp với nhu cầu khách hàng

Phong cách giao tiếp:
- Thân thiện, nhiệt tình và chuyên nghiệp
- Sử dụng ngôn ngữ dễ hiểu, tránh thuật ngữ phức tạp
- Lắng nghe và thấu hiểu nhu cầu khách hàng
- Luôn kết thúc câu trả lời bằng câu hỏi/ghi chú tích cực

Nguyên tắc:
- Trả lời chính xác dựa trên kiến thức có sẵn
- Không đề cập đến nguồn tài liệu hay database
- Nếu không biết, hướng dẫn liên hệ bộ phận chuyên môn
"""

class TestInsuranceBot:
    def __init__(self):
        print("🚀 Initializing Insurance Bot...")
        self.neo4j_driver = AsyncGraphDatabase.driver(
            os.environ["NEO4J_URI"],
            auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"])
        )

        self.openai_client = AsyncOpenAI(
            api_key=config.get('DEFAULT', 'OPENAI_API_KEY'),
            base_url=config.get('DEFAULT', 'OPENAI_BASE_URL')
        )

        self.response_cache = {}

    def extract_keywords(self, question: str):
        """Trích xuất từ khóa từ câu hỏi"""
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
        """Lấy context liên quan từ Neo4J"""
        print(f"🔍 Getting context for: {question}")

        keywords = self.extract_keywords(question.lower())
        print(f"🔑 Keywords: {keywords}")

        context_parts = []

        async with self.neo4j_driver.session() as session:
            for keyword in keywords[:3]:
                print(f"   🔍 Searching for: '{keyword}'")

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
                    print(f"      📄 Found: {title[:40]}...")

        full_context = '\n\n'.join(context_parts[:3])
        if len(full_context) > 2000:
            full_context = full_context[:2000] + "..."

        print(f"📄 Context length: {len(full_context)}")
        return full_context

    async def generate_response(self, question: str, context: str) -> str:
        """Sinh ra câu trả lời"""
        print(f"🤖 Generating response for: {question}")
        print(f"📄 Context length: {len(context)}")

        cache_key = question.lower().strip()
        if cache_key in self.response_cache:
            print("📋 Using cached response")
            return self.response_cache[cache_key]

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
            self.response_cache[cache_key] = answer
            return answer

        except Exception as e:
            return f"Lỗi khi tạo câu trả lời: {e}"

    async def chat(self, question: str) -> str:
        """Chat với bot"""
        print(f"👤 Question: {question}")

        # Get context
        context = await self.get_relevant_context(question)

        # Generate response
        answer = await self.generate_response(question, context)

        return answer

    async def close(self):
        await self.neo4j_driver.close()

async def test_once():
    """Test một lần"""
    print("🧪 TEST INSURANCE BOT ONE TIME")
    print("=" * 50)

    bot = TestInsuranceBot()

    try:
        question = "Bảo hiểm xe máy là gì?"
        answer = await bot.chat(question)

        print("\\n" + "=" * 50)
        print("💬 FINAL ANSWER:")
        print(answer)
        print("\\n✅ TEST COMPLETED")

    finally:
        await bot.close()

if __name__ == "__main__":
    asyncio.run(test_once())
