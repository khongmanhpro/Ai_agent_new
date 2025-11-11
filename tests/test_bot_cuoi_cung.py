#!/usr/bin/env python3
"""
Test Insurance Bot mới sử dụng MiniRAG framework
"""

import os
import sys
import asyncio
sys.path.append('/Volumes/data/MINIRAG/MiniRAG')

from insurance_bot_minirag import InsuranceBotMiniRAG

async def test_final_bot():
    """Test bot mới với MiniRAG"""
    print("🎯 Testing FINAL Insurance Bot with MiniRAG")
    print("=" * 60)

    bot = InsuranceBotMiniRAG()

    try:
        question = "Bảo hiểm xe máy là gì?"
        print(f"🧪 Testing question: {question}")

        answer = await bot.chat(question)

        print("\\n" + "=" * 60)
        print("💬 FINAL ANSWER:")
        print(answer)
        print("\\n✅ FINAL BOT TEST COMPLETED")

    finally:
        await bot.close()

if __name__ == "__main__":
    asyncio.run(test_final_bot())
