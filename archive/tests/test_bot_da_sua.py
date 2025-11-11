#!/usr/bin/env python3
"""
Test Insurance Bot sau khi sửa logic
"""

import os
import sys
import asyncio
sys.path.append('/Volumes/data/MINIRAG/MiniRAG')

from insurance_bot import InsuranceBot

async def test_fixed_bot():
    """Test bot sau khi sửa"""
    print("🔧 TEST FIXED INSURANCE BOT")
    print("=" * 50)

    bot = InsuranceBot()

    try:
        question = "Bảo hiểm xe máy là gì?"
        print(f"🧪 Testing question: {question}")

        answer = await bot.chat(question)

        print("\\n" + "=" * 50)
        print("💬 FINAL ANSWER:")
        print(answer)
        print("\\n✅ FIXED BOT TEST COMPLETED")

    finally:
        await bot.close()

if __name__ == "__main__":
    asyncio.run(test_fixed_bot())
