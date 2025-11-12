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

# Singleton OpenAI client để reuse connection (tối ưu performance)
_openai_client: Optional[AsyncOpenAI] = None

def get_openai_client() -> AsyncOpenAI:
    """Get or create singleton OpenAI client với connection pooling"""
    global _openai_client
    if _openai_client is None:
        api_key = os.environ.get('OPENAI_API_KEY') or config.get('DEFAULT', 'OPENAI_API_KEY', fallback=None)
        base_url = os.environ.get('OPENAI_BASE_URL') or os.environ.get('OPENAI_API_BASE') or config.get('DEFAULT', 'OPENAI_BASE_URL', fallback=None)
        
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables or config file")
        
        # Tối ưu: reuse connections, timeout ngắn hơn
        _openai_client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=30.0,  # Timeout 30s thay vì default
            max_retries=2,  # Giảm retries để fail fast
        )
        print("✅ OpenAI client initialized (singleton, connection pooling enabled)")
    return _openai_client

async def get_openai_embedding_func(texts):
    """Async OpenAI embedding function cho MiniRAG với cache và connection reuse"""
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
            embedding_model = os.environ.get('EMBEDDING_MODEL') or config.get('DEFAULT', 'EMBEDDING_MODEL', fallback='text-embedding-3-small')
            
            # Reuse singleton client (connection pooling)
            client = get_openai_client()

            # Batch request với timeout ngắn
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
### VAI TRÒ VÀ BỐI CẢNH 

Bạn là nhân viên tư vấn chuyên nghiệp của Công ty đại lý bảo hiểm FISS. 

Nhiệm vụ chính của bạn là:

- Tư vấn và giải đáp mọi thắc mắc về các sản phẩm bảo hiểm

- Hỗ trợ khách hàng tra cứu thông tin hợp đồng, quyền lợi bảo hiểm

- Hướng dẫn quy trình mua bảo hiểm, nộp hồ sơ bồi thường

- Cung cấp báo giá và tư vấn sản phẩm phù hợp với nhu cầu khách hàng

### PHONG CÁCH GIAO TIẾP

- Thân thiện, nhiệt tình và chuyên nghiệp

- Sử dụng ngôn ngữ dễ hiểu, tránh thuật ngữ phức tạp (hoặc giải thích rõ nếu cần dùng)

- Lắng nghe và thấu hiểu nhu cầu khách hàng

- Luôn kết thúc câu trả lời bằng câu hỏi/ghi chú tích cực để duy trì cuộc hội thoại

### NGUYÊN TẮC TRỢ GIÚP

1. **Làm rõ nhu cầu**: Nếu câu hỏi chưa rõ ràng, hãy đặt câu hỏi để hiểu đúng ý khách hàng

   - Ví dụ: "Anh/chị quan tâm đến bảo hiểm xe máy hay ô tô ạ?"

   - Ví dụ: "Để tư vấn chính xác, cho em hỏi anh/chị muốn mức phí bảo hiểm khoảng bao nhiêu?"

2. **Trả lời chính xác**: Chỉ cung cấp thông tin dựa trên kiến thức đã được đào tạo về:

   - Sản phẩm bảo hiểm của công ty

   - Quy định pháp luật về bảo hiểm Việt Nam

   - Quy trình và chính sách của công ty

3. **Phản hồi khi không biết**: Nếu câu hỏi nằm ngoài phạm vi kiến thức:

   "Em xin lỗi, thông tin này em chưa được cập nhật đầy đủ. Để được tư vấn chính xác nhất, anh/chị vui lòng:

   - Liên hệ hotline: 0385 10 10 18

   - Email: cskh@fiss.com.vn

   - Hoặc em có thể chuyển anh/chị sang tư vấn viên chuyên môn để được hỗ trợ tốt hơn ạ."

4. **Xử lý yêu cầu phức tạp**: Với các vấn đề về:

   - Bồi thường bảo hiểm cụ thể

   - Tranh chấp hợp đồng

   - Thay đổi thông tin hợp đồng quan trọng

   → Hướng dẫn khách hàng kết nối với bộ phận chuyên trách

### GIỚI HẠN VÀ RANH GIỚI

1. **KHÔNG tiết lộ dữ liệu hệ thống**: 

   - Không đề cập đến việc bạn có quyền truy cập vào cơ sở dữ liệu đào tạo

   - Không nói "trong dữ liệu của tôi có...", thay vào đó nói "theo quy định hiện hành..." hoặc "theo chính sách công ty..."

2. **Duy trì focus**: 

   - Nếu khách hàng hỏi về chủ đề không liên quan (thời tiết, chính trị, giải trí...):

     "Em hiểu anh/chị quan tâm, nhưng chuyên môn của em là tư vấn về bảo hiểm. Anh/chị có thắc mắc gì về các sản phẩm bảo hiểm của công ty không ạ?"

3. **Chỉ dựa vào kiến thức được đào tạo**:

   - Không tự suy diễn hoặc đưa ra thông tin không chắc chắn

   - Không so sánh với sản phẩm của đối thủ (trừ khi có dữ liệu chính thức)

4. **TUYỆT ĐỐI KHÔNG**:

   - Hiển thị phần "References", "Nguồn tài liệu", hoặc tên file (.md, .pdf)

   - Liệt kê [1], [2], [3] ở cuối câu trả lời

   - Đưa ra lời khuyên pháp lý hoặc tài chính chuyên sâu

   - Cam kết về kết quả bồi thường cụ thể mà chưa có thẩm định

### CẤU TRÚC CÂU TRẢ LỜI LÝ TƯỞNG

1. **Chào hỏi/Thừa nhận câu hỏi**: "Dạ, em xin giải đáp thắc mắc của anh/chị về..."

2. **Nội dung chính**: Trả lời trực tiếp, súc tích, có cấu trúc

3. **Thông tin bổ sung** (nếu cần): Ví dụ, lưu ý quan trọng

4. **Kết thúc tích cực**: Câu hỏi mở hoặc lời khuyên hữu ích

   - "Anh/chị còn thắc mắc gì khác em có thể hỗ trợ không ạ?"

   - "Em có thể tư vấn thêm về gói bảo hiểm phù hợp với nhu cầu của anh/chị nếu muốn ạ!"

### VÍ DỤ TƯƠNG TÁC

**Tốt:**

Khách: "Xe máy tôi bị tai nạn, bảo hiểm có chi trả không?"

Bot: "Dạ, em xin giải đáp ạ. Bảo hiểm bắt buộc trách nhiệm dân sự xe máy sẽ chi trả cho:

- Thiệt hại về người và tài sản của bên thứ ba (người bị nạn)

- Không bồi thường cho chính xe máy và chủ xe gây tai nạn

Nếu anh/chị muốn xe máy được bảo hiểm khi bị hư hỏng, anh/chị cần mua thêm gói bảo hiểm vật chất xe (bảo hiểm tự nguyện) ạ.

Xe của anh/chị hiện có mua bảo hiểm tự nguyện không ạ? Em có thể tư vấn thêm nếu anh/chị quan tâm!"

**Không tốt:**

Khách: "Xe máy tôi bị tai nạn, bảo hiểm có chi trả không?"

Bot: "Có, bảo hiểm sẽ chi trả.

### XỬ LÝ CÁC TÌNH HUỐNG ĐẶC BIỆT

**1. Khách hàng tức giận:**

"Em rất hiểu sự bức xúc của anh/chị. Em sẽ cố gắng hỗ trợ tốt nhất. Để giải quyết vấn đề nhanh chóng, anh/chị vui lòng cho em biết [thông tin cần thiết]..."

**2. Yêu cầu ngoài khả năng:**

"Em xin lỗi vì chưa thể hỗ trợ vấn đề này qua chat. Để được xử lý nhanh chóng và chính xác, em xin chuyển anh/chị sang bộ phận CSKH qua Zalo: 033 6691379."

**3. Thông tin nhạy cảm:**

"Để bảo mật thông tin cá nhân, em không thể xử lý thông tin này qua chat ạ. Anh/chị vui lòng liên hệ trực tiếp với chúng em qua hotline 0385 10 10 18 hoặc đến văn phòng để được hỗ trợ an toàn hơn ạ."

### Hướng dẫn mua hàng

Khi khách hỏi cách mua sản phẩm, trả lời quy trình mua hàng của sản phẩm đó theo format:

**Quy trình mua [Tên sản phẩm]:**

- Bước 1: [Hành động đầu tiên]

- Bước 2: [Hành động tiếp theo]

- Bước 3: [Hành động tiếp theo]

- Bước 4: [Hoàn tất]

**Ví dụ - Mua Bảo hiểm bắt buộc xe máy:**

- Bước 1: Mở app Fiss → chọn sản phẩm → nhận báo giá

- Bước 2: Nhập số khung, số máy

- Bước 3: Xem lại và thanh toán

- Bước 4: Giấy chứng nhận điện tử tự động lưu trong app

Chỉ liệt kê các bước thực hiện, không giải thích thêm.

### chú ý

- Nếu câu hỏi đã từng trả lời hãy lấy từ bộ nhớ ra để trả lời không cần truy vấn lâu

### LƯU Ý QUAN TRỌNG

- Luôn đảm bảo độ chính xác 100% về số tiền, ngày tháng, điều khoản

- Không tự ý sửa đổi hoặc giải thích sai các quy định pháp luật

- Khi đề cập số liệu, phải rõ ràng (ví dụ: "66.000 VNĐ/năm" thay vì "khoảng 60k")

- Luôn cập nhật thông tin theo quy định mới nhất của Bộ Tài chính
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
        
        # Tối ưu: Giữ max_tokens đủ để có câu trả lời đầy đủ (1200 cho bảo hiểm cần chi tiết)
        llm_max_tokens = int(os.environ.get('OPENAI_LLM_MAX_TOKENS') or config.get('DEFAULT', 'OPENAI_LLM_MAX_TOKENS', fallback='1200'))
        llm_model = os.environ.get('OPENAI_LLM_MODEL') or config.get('DEFAULT', 'OPENAI_LLM_MODEL', fallback='gpt-4o-mini')
        
        print(f"📁 Working directory: {working_dir}")

        self.rag = MiniRAG(
            working_dir=working_dir,
            llm_model_func=gpt_4o_mini_complete,
            llm_model_max_token_size=llm_max_tokens,
            llm_model_name=llm_model,
            llm_model_kwargs={
                "system_prompt": INSURANCE_BOT_PROMPT
            },
            embedding_func=EmbeddingFunc(
                embedding_dim=1536,
                max_token_size=1000,
                func=get_openai_embedding_func,
            ),
        )

        # Cache cho response với TTL
        self.response_cache: Dict[str, Dict] = {}
        self.cache_ttl = 3600  # 1 giờ
        
        # Pre-warm cache với common queries (tối ưu tốc độ)
        self._pre_warm_cache()
        
        print("✅ Insurance Bot with MiniRAG initialized!")
    
    def _pre_warm_cache(self):
        """Pre-warm cache với common queries để tăng tốc độ"""
        common_queries = [
            "Bảo hiểm xe máy là gì?",
            "Phí bảo hiểm xe máy bao nhiêu?",
            "Quy trình mua bảo hiểm xe máy?",
            "Bảo hiểm sức khỏe là gì?",
            "Bảo hiểm bắt buộc là gì?",
        ]
        
        # Pre-compute embeddings cho common queries (async, không block)
        async def pre_warm_embeddings():
            try:
                for query in common_queries:
                    await get_openai_embedding_func([query])
                print(f"✅ Pre-warmed cache với {len(common_queries)} common queries")
            except Exception as e:
                print(f"⚠️ Pre-warm cache error: {e}")
        
        # Chạy pre-warm trong background (không block initialization)
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Nếu loop đang chạy, schedule task
                asyncio.create_task(pre_warm_embeddings())
            else:
                # Nếu không, chạy sync
                loop.run_until_complete(pre_warm_embeddings())
        except Exception:
            # Nếu không có event loop, bỏ qua pre-warm
            pass

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

    async def chat_stream(self, question: str):
        """Chat với bot sử dụng streaming - Trả về async generator (công nghệ mới nhất)"""
        print(f"👤 Question (streaming): {question}")
        start_time = time.time()
        
        # Check cache first (không stream cached responses)
        cache_key = question.lower().strip()
        if cache_key in self.response_cache:
            entry = self.response_cache[cache_key]
            if time.time() - entry['timestamp'] < self.cache_ttl:
                print(f"📋 Using cached response (streaming disabled for cache)")
                # Trả về cached response như một chunk
                yield entry['answer']
                return
        
        print("🔍 Querying MiniRAG with streaming (latest tech)...")
        
        try:
            # Bước 1: Lấy context từ MiniRAG (nhanh, không stream)
            # Sử dụng only_need_context=True để chỉ lấy context, không generate
            query_param_context = QueryParam(
                mode="light",
                top_k=8,
                max_token_for_text_unit=2500,
                max_token_for_node_context=400,
                max_token_for_local_context=2000,
                max_token_for_global_context=2000,
                only_need_context=True,  # Chỉ lấy context, không generate
            )
            
            # Lấy context (nhanh)
            context_start = time.time()
            context = await self.rag.aquery(question, param=query_param_context)
            context_time = time.time() - context_start
            print(f"⏱️ Context retrieval: {context_time:.2f}s")
            
            # Bước 2: Stream LLM response trực tiếp từ OpenAI
            # Build prompt với context (format giống MiniRAG nhưng dùng INSURANCE_BOT_PROMPT)
            from minirag.operate import PROMPTS
            
            # Build system prompt: Kết hợp INSURANCE_BOT_PROMPT + context
            # Format: System prompt + Context data
            sys_prompt_base = INSURANCE_BOT_PROMPT
            sys_prompt_with_context = f"""{sys_prompt_base}

Dưới đây là thông tin từ cơ sở dữ liệu để trả lời câu hỏi:

{context}

Hãy sử dụng thông tin trên để trả lời câu hỏi một cách chính xác và đầy đủ."""
            
            # Stream trực tiếp từ LLM
            client = get_openai_client()
            llm_model = os.environ.get('OPENAI_LLM_MODEL') or config.get('DEFAULT', 'OPENAI_LLM_MODEL', fallback='gpt-4o-mini')
            llm_max_tokens = int(os.environ.get('OPENAI_LLM_MAX_TOKENS') or config.get('DEFAULT', 'OPENAI_LLM_MAX_TOKENS', fallback='1200'))
            
            messages = [
                {"role": "system", "content": sys_prompt_with_context},
                {"role": "user", "content": question}
            ]
            
            # Stream từ OpenAI
            stream = await client.chat.completions.create(
                model=llm_model,
                messages=messages,
                max_tokens=llm_max_tokens,
                temperature=0.7,
                stream=True  # Enable streaming
            )
            
            full_response = ""
            first_token_time = None
            
            async for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'content') and delta.content:
                        content = delta.content
                        full_response += content
                        
                        # Track TTFT (Time To First Token)
                        if first_token_time is None:
                            first_token_time = time.time() - start_time
                            print(f"⚡ TTFT (Time To First Token): {first_token_time:.2f}s")
                        
                        yield content
            
            # Cache full response
            self.response_cache[cache_key] = {
                'answer': full_response,
                'timestamp': time.time()
            }
            
            total_time = time.time() - start_time
            print(f"⏱️ Total streaming time: {total_time:.2f}s, TTFT: {first_token_time:.2f}s")
                
        except Exception as e:
            print(f"❌ Streaming error: {e}")
            import traceback
            traceback.print_exc()
            yield f"Xin lỗi, hiện tại hệ thống đang gặp sự cố kỹ thuật. Anh/chị vui lòng thử lại sau hoặc liên hệ hotline 0385 10 10 18 để được hỗ trợ ạ."
    
    async def chat(self, question: str) -> str:
        """Chat với bot sử dụng MiniRAG - Tối ưu cho tốc độ < 15s"""
        start_time = time.time()
        print(f"👤 Question: {question}")

        # Check cache first
        cache_key = question.lower().strip()
        if cache_key in self.response_cache:
            entry = self.response_cache[cache_key]
            if time.time() - entry['timestamp'] < self.cache_ttl:
                print(f"📋 Using cached response (saved {time.time() - entry['timestamp']:.1f}s ago)")
                return entry['answer']
            else:
                # Cache expired
                del self.response_cache[cache_key]

        print("🔍 Querying MiniRAG (optimized for speed + accuracy)...")

        try:
            # Tối ưu cân bằng: Tốc độ + Độ chính xác (quan trọng cho lĩnh vực bảo hiểm)
            # - top_k: 8-10 (đủ để có kết quả chính xác và đầy đủ)
            # - max_token_for_text_unit: 2500 (đủ context, không mất từ)
            # - Light mode: Có graph context, chính xác hơn naive mode
            # - Tối ưu bằng caching, connection pooling, không giảm chất lượng
            query_param = QueryParam(
                mode="light",  # Light mode: có graph context, chính xác hơn naive
                top_k=8,  # Đủ để có kết quả chính xác và đầy đủ (không giảm)
                max_token_for_text_unit=2500,  # Đủ context, không mất từ
                max_token_for_node_context=400,  # Đủ context cho entities
                max_token_for_local_context=2000,  # Đủ context cho local
                max_token_for_global_context=2000,  # Đủ context cho global
            )
            
            query_start = time.time()
            try:
                answer = await self.rag.aquery(question, param=query_param)
                query_time = time.time() - query_start
            except Exception as light_error:
                # Nếu light mode fail, fallback sang naive mode với top_k đủ
                print(f"⚠️ Light mode failed: {light_error}, trying naive mode with top_k=8...")
                query_param = QueryParam(
                    mode="naive",
                    top_k=8,  # Vẫn giữ đủ để chính xác
                    max_token_for_text_unit=2500,  # Vẫn giữ đủ context
                )
                query_start = time.time()
                answer = await self.rag.aquery(question, param=query_param)
                query_time = time.time() - query_start

            total_time = time.time() - start_time
            print(f"⏱️ Query time: {query_time:.2f}s, Total time: {total_time:.2f}s")

            # Cache response với timestamp
            self.response_cache[cache_key] = {
                'answer': answer,
                'timestamp': time.time()
            }

            # Cleanup expired cache entries (keep cache size manageable)
            if len(self.response_cache) > 100:
                current_time = time.time()
                expired_keys = [
                    key for key, entry in self.response_cache.items()
                    if current_time - entry['timestamp'] >= self.cache_ttl
                ]
                for key in expired_keys[:50]:  # Remove up to 50 expired entries
                    del self.response_cache[key]

            print(f"💬 MiniRAG Answer: {answer[:100]}...")
            return answer

        except Exception as e:
            print(f"❌ MiniRAG query error: {e}")
            import traceback
            traceback.print_exc()
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
