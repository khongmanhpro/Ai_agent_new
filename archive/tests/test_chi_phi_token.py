#!/usr/bin/env python3
"""
Ước tính chi phí token cho một câu hỏi
"""

import os
import sys
import asyncio
import configparser
from openai import AsyncOpenAI

# Load config
config = configparser.ConfigParser()
config.read('/Volumes/data/MINIRAG/config/insurance_config.ini')

for key in config['DEFAULT']:
    os.environ[key.upper()] = str(config['DEFAULT'][key])

sys.path.append('/Volumes/data/MINIRAG/MiniRAG')
from insurance_bot_minirag import InsuranceBotMiniRAG

async def estimate_token_cost():
    """Ước tính chi phí token"""
    print("🧮 ESTIMATING TOKEN COST FOR ONE QUESTION...")

    # Test với câu hỏi đơn giản
    question = "Bảo hiểm xe máy là gì?"

    # Khởi tạo OpenAI client để test trực tiếp
    client = AsyncOpenAI(
        api_key=config.get('DEFAULT', 'OPENAI_API_KEY'),
        base_url=config.get('DEFAULT', 'OPENAI_API_BASE')
    )

    try:
        print(f"❓ Question: {question}")

        # Test embedding cost (ước tính)
        print("\n🔍 Testing Embedding...")
        embed_response = await client.embeddings.create(
            input=[question],
            model="text-embedding-3-small"
        )
        embedding_tokens = embed_response.usage.total_tokens
        print(f"  Embedding tokens used: {embedding_tokens}")

        # Test LLM cost (ước tính với prompt ngắn)
        print("\n🤖 Testing LLM...")
        system_prompt = """
        Bạn là nhân viên tư vấn chuyên nghiệp của Công ty đại lý bảo hiểm FISS.
        Trả lời ngắn gọn về bảo hiểm xe máy.
        """

        llm_response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            max_tokens=1000,
            temperature=0.7
        )

        llm_input_tokens = llm_response.usage.prompt_tokens
        llm_output_tokens = llm_response.usage.completion_tokens
        total_llm_tokens = llm_response.usage.total_tokens

        print(f"  LLM input tokens: {llm_input_tokens}")
        print(f"  LLM output tokens: {llm_output_tokens}")
        print(f"  LLM total tokens: {total_llm_tokens}")

        # Tính chi phí
        embedding_cost = (embedding_tokens / 1_000_000) * 0.02  # $0.02 per 1M tokens
        llm_input_cost = (llm_input_tokens / 1_000_000) * 0.15   # $0.15 per 1M input tokens
        llm_output_cost = (llm_output_tokens / 1_000_000) * 0.60  # $0.60 per 1M output tokens

        total_cost = embedding_cost + llm_input_cost + llm_output_cost

        print("\n💰 COST BREAKDOWN PER QUESTION:")
        print(f"  Embedding: ${embedding_cost:.6f} ({embedding_tokens} tokens)")
        print(f"  LLM Input: ${llm_input_cost:.6f} ({llm_input_tokens} tokens)")
        print(f"  LLM Output: ${llm_output_cost:.6f} ({llm_output_tokens} tokens)")
        print(f"  TOTAL: ${total_cost:.6f}")

        # Ước tính cho nhiều câu hỏi
        print("\n📈 ESTIMATES:")
        print(f"  100 questions: ${total_cost * 100:.4f}")
        print(f"  1,000 questions: ${total_cost * 1000:.4f}")
        print(f"  10,000 questions: ${total_cost * 10000:.2f}")

        # Trong thực tế với MiniRAG, có nhiều embedding calls hơn
        print("\n⚠️  LƯU Ý:")
        print("  - MiniRAG thực hiện nhiều embedding queries để tìm context")
        print("  - Chi phí thực tế có thể cao hơn 2-3 lần")
        print("  - Giá trên là cho text-embedding-3-small + gpt-4o-mini")

        print("\n💬 Sample Answer:")
        print(llm_response.choices[0].message.content[:200] + "...")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(estimate_token_cost())
