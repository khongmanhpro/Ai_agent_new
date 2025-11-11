#!/usr/bin/env python3
"""
Test thời gian phản hồi của bot
"""

import os
import sys
import asyncio
import time
import configparser

# Load config
config = configparser.ConfigParser()
config.read('/Volumes/data/MINIRAG/config/insurance_config.ini')

for key in config['DEFAULT']:
    os.environ[key.upper()] = str(config['DEFAULT'][key])

sys.path.append('/Volumes/data/MINIRAG/MiniRAG')
from insurance_bot_minirag import InsuranceBotMiniRAG

async def test_response_time():
    """Test thời gian phản hồi"""
    print("⏱️  TESTING RESPONSE TIME...")

    # Test với câu hỏi khác nhau
    test_questions = [
        "Bảo hiểm xe máy là gì?",
        "Quy tắc bảo hiểm nhà tù nhân?",
        "Bảo hiểm du lịch toàn cầu?",
        "Bảo hiểm tai nạn con người?"
    ]

    # Khởi tạo bot
    bot = InsuranceBotMiniRAG()

    try:
        response_times = []

        print(f"\n🧪 Testing {len(test_questions)} questions...\n")

        for i, question in enumerate(test_questions, 1):
            print(f"❓ [{i}/{len(test_questions)}] {question}")

            # Đo thời gian
            start_time = time.time()

            try:
                answer = await bot.chat(question)
                end_time = time.time()

                response_time = end_time - start_time
                response_times.append(response_time)

                print(f"   ⏱️  Response time: {response_time:.2f}s")
                print(f"   📏 Answer length: {len(answer)} chars")
                print(f"   📝 Preview: {answer[:100]}...")
                print()

            except Exception as e:
                end_time = time.time()
                response_time = end_time - start_time
                print(f"   ⏱️  Response time: {response_time:.2f}s")
                print(f"   ❌ Error: {str(e)[:100]}...")
                print()
                response_times.append(response_time)

        # Thống kê
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            min_time = min(response_times)
            max_time = max(response_times)

            print("📊 RESPONSE TIME STATISTICS:")
            print(".2f")
            print(".2f")
            print(".2f")
            print(".2f")
            # Phân tích
            if avg_time < 2:
                speed_rating = "⚡ RẤT NHANH"
            elif avg_time < 5:
                speed_rating = "🚀 NHANH"
            elif avg_time < 10:
                speed_rating = "🐌 CHẬM"
            else:
                speed_rating = "🐌 RẤT CHẬM"

            print(f"\n🎯 ĐÁNH GIÁ: {speed_rating}")

            # So sánh
            print("\n📋 THAM KHẢO:")
            print("  - < 2s: Xuất sắc")
            print("  - 2-5s: Tốt")
            print("  - 5-10s: Chấp nhận được")
            print("  - > 10s: Cần cải thiện")
        else:
            print("❌ Không có dữ liệu thời gian phản hồi")

    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await bot.close()

if __name__ == "__main__":
    asyncio.run(test_response_time())
