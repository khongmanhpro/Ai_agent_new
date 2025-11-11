#!/usr/bin/env python3
"""
Insurance Bot sử dụng MiniRAG framework thay vì Neo4J trực tiếp
"""

import os
import sys
import asyncio
import hashlib
import time
from typing import Dict, List, Optional

# Get base directory (works in both local and Docker)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(BASE_DIR, 'MiniRAG'))

# Load config
import configparser
config = configparser.ConfigParser()
config_path = os.path.join(BASE_DIR, 'config', 'insurance_config.ini')
if os.path.exists(config_path):
    config.read(config_path)
    # Set environment variables from config (only if config exists)
    if 'DEFAULT' in config:
        for key in config['DEFAULT']:
            # Only set if not already in environment
            if key.upper() not in os.environ:
                os.environ[key.upper()] = str(config['DEFAULT'][key])

from minirag import MiniRAG, QueryParam
from minirag.llm import gpt_4o_mini_complete
from minirag.utils import EmbeddingFunc
from openai import AsyncOpenAI

class EmbeddingCache:
    """Cache cho embeddings để tránh gọi API lặp lại"""

    def __init__(self, ttl_seconds: int = 3600):  # 1 giờ TTL
        self.cache: Dict[str, Dict] = {}
        self.ttl_seconds = ttl_seconds

    def _get_cache_key(self, text: str) -> str:
        """Tạo cache key từ text"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def get(self, text: str) -> Optional[List[float]]:
        """Lấy embedding từ cache nếu còn hợp lệ"""
        cache_key = self._get_cache_key(text)
        if cache_key in self.cache:
            entry = self.cache[cache_key]
            if time.time() - entry['timestamp'] < self.ttl_seconds:
                print(f"📋 Cache hit for: {text[:50]}...")
                return entry['embedding']
            else:
                # Cache expired
                del self.cache[cache_key]
        return None

    def set(self, text: str, embedding: List[float]):
        """Lưu embedding vào cache"""
        cache_key = self._get_cache_key(text)
        self.cache[cache_key] = {
            'embedding': embedding,
            'timestamp': time.time()
        }
        print(f"💾 Cached embedding for: {text[:50]}...")

    def clear_expired(self):
        """Xóa cache entries đã hết hạn"""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.cache.items()
            if current_time - entry['timestamp'] >= self.ttl_seconds
        ]
        for key in expired_keys:
            del self.cache[key]
        if expired_keys:
            print(f"🗑️ Cleared {len(expired_keys)} expired cache entries")

# Global embedding cache
embedding_cache = EmbeddingCache()

async def get_openai_embedding_func(texts):
    """Async OpenAI embedding function cho MiniRAG với cache"""
    try:
        # Check cache cho từng text
        cached_embeddings = []
        texts_to_fetch = []
        cache_indices = []

        for i, text in enumerate(texts):
            cached = embedding_cache.get(text)
            if cached is not None:
                cached_embeddings.append((i, cached))
            else:
                texts_to_fetch.append(text)
                cache_indices.append(i)

        # Chỉ gọi API cho texts chưa có trong cache
        if texts_to_fetch:
            print(f"🔍 Fetching embeddings for {len(texts_to_fetch)} texts...")
            # Ưu tiên đọc từ environment variables, nếu không có thì đọc từ config
            api_key = os.environ.get('OPENAI_API_KEY') or config.get('DEFAULT', 'OPENAI_API_KEY', fallback=None)
            base_url = os.environ.get('OPENAI_BASE_URL') or os.environ.get('OPENAI_API_BASE') or config.get('DEFAULT', 'OPENAI_BASE_URL', fallback=None)
            embedding_model = os.environ.get('EMBEDDING_MODEL') or config.get('DEFAULT', 'EMBEDDING_MODEL', fallback='text-embedding-3-small')
            
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in environment variables or config file")
            
            client = AsyncOpenAI(
                api_key=api_key,
                base_url=base_url
            )

            response = await client.embeddings.create(
                input=texts_to_fetch,
                model=embedding_model
            )

            fetched_embeddings = [data.embedding for data in response.data]

            # Cache các embeddings mới
            for text, embedding in zip(texts_to_fetch, fetched_embeddings):
                embedding_cache.set(text, embedding)
        else:
            fetched_embeddings = []

        # Kết hợp cached và fetched embeddings theo thứ tự gốc
        result = [None] * len(texts)

        # Điền cached embeddings
        for idx, embedding in cached_embeddings:
            result[idx] = embedding

        # Điền fetched embeddings
        for i, embedding in enumerate(fetched_embeddings):
            result[cache_indices[i]] = embedding

        return result

    except Exception as e:
        print(f"❌ OpenAI embedding error: {e}")
        # Return dummy embeddings if OpenAI fails
        return [[0.1] * 1536 for _ in texts]

# Insurance Bot Prompt
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

class InsuranceBotMiniRAG:
    """Bot sử dụng MiniRAG framework"""

    def __init__(self):
        print("🚀 Initializing Insurance Bot with MiniRAG...")

        # Ưu tiên đọc từ environment variables
        working_dir = os.environ.get('WORKING_DIR') or config.get('DEFAULT', 'WORKING_DIR', fallback='./insurance_rag')
        # Normalize working_dir: nếu là đường dẫn tuyệt đối chứa /Volumes, chuyển thành relative
        if working_dir.startswith('/Volumes'):
            # Extract relative path from /Volumes/data/MINIRAG/logs/insurance_rag
            if 'logs/insurance_rag' in working_dir:
                working_dir = './logs/insurance_rag'
            else:
                working_dir = './insurance_rag'
        # Đảm bảo working_dir là relative path trong container
        if not working_dir.startswith('./'):
            working_dir = './' + working_dir.lstrip('/')
        
        llm_max_tokens = int(os.environ.get('OPENAI_LLM_MAX_TOKENS') or config.get('DEFAULT', 'OPENAI_LLM_MAX_TOKENS', fallback='1000'))
        llm_model = os.environ.get('OPENAI_LLM_MODEL') or config.get('DEFAULT', 'OPENAI_LLM_MODEL', fallback='gpt-4o-mini')
        
        print(f"📁 Working directory: {working_dir}")

        self.rag = MiniRAG(
            working_dir=working_dir,
            llm_model_func=gpt_4o_mini_complete,
            llm_model_max_token_size=llm_max_tokens,
            llm_model_name=llm_model,
            embedding_func=EmbeddingFunc(
                embedding_dim=1536,
                max_token_size=1000,
                func=get_openai_embedding_func,
            ),
        )

        # Cache cho response
        self.response_cache = {}
        print("✅ Insurance Bot with MiniRAG initialized!")

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

    async def chat(self, question: str) -> str:
        """Chat với bot sử dụng MiniRAG"""
        print(f"👤 Question: {question}")

        # Check cache first
        cache_key = question.lower().strip()
        if cache_key in self.response_cache:
            print("📋 Using cached response")
            return self.response_cache[cache_key]

        print("🔍 Querying MiniRAG...")

        try:
            # Query MiniRAG
            answer = await self.rag.aquery(question, param=QueryParam(mode="mini"))

            # Cache response
            self.response_cache[cache_key] = answer

            print(f"💬 MiniRAG Answer: {answer[:100]}...")
            return answer

        except Exception as e:
            print(f"❌ MiniRAG query error: {e}")
            return f"Xin lỗi, hiện tại hệ thống đang gặp sự cố kỹ thuật. Anh/chị vui lòng thử lại sau hoặc liên hệ hotline 0385 10 10 18 để được hỗ trợ ạ."

    async def close(self):
        """Close resources"""
        print("👋 Insurance Bot closed")

async def main():
    """Main function for interactive chat"""
    print("🤖 INSURANCE BOT - Sử dụng MiniRAG Framework")
    print("=" * 60)

    bot = InsuranceBotMiniRAG()

    try:
        print("💬 Chào mừng bạn đến với dịch vụ tư vấn bảo hiểm FISS!")
        print("📝 Hãy đặt câu hỏi về bảo hiểm, em sẽ hỗ trợ bạn ngay ạ.")
        print("❌ Gõ 'quit' để thoát")
        print()

        while True:
            try:
                question = input("👤 Bạn: ").strip()

                if question.lower() in ['quit', 'exit', 'bye']:
                    print("💬 Cảm ơn bạn đã sử dụng dịch vụ tư vấn của FISS!")
                    print("📞 Nếu cần hỗ trợ thêm, hãy liên hệ hotline 0385 10 10 18 nhé!")
                    break

                if not question:
                    continue

                answer = await bot.chat(question)
                print(f"💬 FISS Bot: {answer}")
                print()

            except KeyboardInterrupt:
                print("\n💬 Cảm ơn bạn đã sử dụng dịch vụ!")
                break
            except Exception as e:
                print(f"❌ Lỗi: {e}")
                continue

    finally:
        await bot.close()

if __name__ == "__main__":
    asyncio.run(main())
