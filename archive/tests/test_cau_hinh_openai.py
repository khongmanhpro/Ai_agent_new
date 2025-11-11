#!/usr/bin/env python3
"""
Script test cấu hình OpenAI API với custom base URL
"""

import os
import sys
sys.path.append('/Volumes/data/MINIRAG/MiniRAG')

# Load config
import configparser
config = configparser.ConfigParser()
config.read('../config/insurance_config.ini')

def test_openai_config():
    print("🧪 TEST CẤU HÌNH OPENAI API")
    print("=" * 50)

    # Load config values
    api_key = config.get('DEFAULT', 'OPENAI_API_KEY', fallback=None)
    base_url = config.get('DEFAULT', 'OPENAI_BASE_URL', fallback=None)
    model = config.get('DEFAULT', 'EMBEDDING_MODEL', fallback='text-embedding-3-small')

    print(f"🔑 API Key: {api_key[:20]}..." if api_key else "❌ Không có API key")
    print(f"🌐 Base URL: {base_url}")
    print(f"🤖 Model: {model}")

    if not api_key:
        print("❌ Thiếu API key trong config")
        return

    # Test import
    try:
        from minirag.llm.openai import openai_embed
        from minirag.utils import EmbeddingFunc
        print("✅ Import OpenAI thành công")
    except ImportError as e:
        print(f"❌ Import thất bại: {e}")
        return

    # Test với embedding function
    try:
        embedding_func = EmbeddingFunc(
            embedding_dim=1536,
            max_token_size=8000,
            func=lambda texts: openai_embed(
                texts,
                model=model,
                api_key=api_key,
                base_url=base_url
            ),
        )

        # Test với một câu hỏi tiếng Việt
        test_texts = [
            "Bảo hiểm nhân thọ là gì?",
            "Điều kiện tham gia bảo hiểm xe máy"
        ]

        print(f"\\n📝 Test với {len(test_texts)} văn bản mẫu:")
        for i, text in enumerate(test_texts, 1):
            print(f"  {i}. \"{text}\"")

        print("\\n⏳ Đang gọi OpenAI API...")
        print(f"📡 URL: {base_url}")
        print(f"🔑 Key: {api_key[:10]}...")

        embeddings = embedding_func(test_texts)

        print("✅ OpenAI API thành công!")
        print(f"📊 Kích thước: {len(embeddings)} vectors x {len(embeddings[0])} dimensions")

        if all(len(emb) == 1536 for emb in embeddings):
            print("✅ Tất cả vectors có dimension đúng")
        else:
            print("❌ Vectors có dimension không nhất quán")

        # Tính cost ước tính
        total_tokens = sum(len(text.split()) * 1.3 for text in test_texts)
        estimated_cost = (total_tokens / 1000000) * 0.02
        print(f"💰 Cost ước tính: ${estimated_cost:.6f}")

    except Exception as e:
        print(f"❌ Test OpenAI thất bại: {e}")
        print("\\n💡 Kiểm tra:")
        print("   - API key có đúng không?")
        print("   - Base URL có accessible không?")
        print("   - Model name có đúng không?")
        return

    print("\\n🎉 CẤU HÌNH OPENAI THÀNH CÔNG!")
    print("🚀 Sẵn sàng sử dụng cho RAG system!")

if __name__ == "__main__":
    test_openai_config()
