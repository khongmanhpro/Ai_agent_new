#!/usr/bin/env python3
"""
Ứng dụng chính MiniRAG cho dự án bảo hiểm

Sử dụng: python insurance_app.py "câu hỏi về bảo hiểm"
"""

import os
import sys
import asyncio
import argparse
sys.path.append('/Volumes/data/MINIRAG/MiniRAG')

# Load config
import configparser
config = configparser.ConfigParser()
config.read('insurance_config.ini')

# Set environment variables from config
for key in config['DEFAULT']:
    os.environ[key.upper()] = str(config['DEFAULT'][key])

# Import Neo4J
from neo4j import AsyncGraphDatabase

# Sẽ import MiniRAG trong class khi cần
MINIRAG_AVAILABLE = False

class InsuranceRAG:
    """Class xử lý RAG cho bảo hiểm"""

    def __init__(self):
        self.minirag_available = MINIRAG_AVAILABLE
        self.rag = None
        self.driver = None

        if self.minirag_available:
            self.init_minirag()
        else:
            self.init_neo4j_direct()

    def init_minirag(self):
        """Khỏi tạo MiniRAG - chỉ khi thực sự cần"""
        try:
            import sys
            sys.path.append('/Volumes/data/MINIRAG/MiniRAG')
            from minirag import MiniRAG, QueryParam
            from minirag.utils import EmbeddingFunc

            print("🚀 Khởi tạo MiniRAG với Neo4J...")

            # Kiểm tra loại embedding từ config
            embedding_type = config.get('DEFAULT', 'EMBEDDING_TYPE', fallback='dummy')

            if embedding_type == 'openai':
                # Sử dụng OpenAI embeddings
                try:
                    from minirag.llm.openai import openai_embed
                    api_key = config.get('DEFAULT', 'OPENAI_API_KEY', fallback=os.environ.get('OPENAI_API_KEY'))
                    base_url = config.get('DEFAULT', 'OPENAI_BASE_URL', fallback=None)

                    if not api_key:
                        print("❌ Thiếu OPENAI_API_KEY trong config hoặc environment variables")
                        embedding_type = 'dummy'
                    else:
                        print("✅ Sử dụng OpenAI embeddings")
                        if base_url:
                            print(f"📡 Sử dụng custom base URL: {base_url}")
                        self.rag = MiniRAG(
                            working_dir=config.get('DEFAULT', 'WORKING_DIR', fallback='./insurance_rag'),
                            kv_storage=config.get('DEFAULT', 'KV_STORAGE', fallback='JsonKVStorage'),
                            vector_storage=config.get('DEFAULT', 'VECTOR_STORAGE', fallback='NanoVectorDBStorage'),
                            graph_storage=config.get('DEFAULT', 'GRAPH_STORAGE', fallback='Neo4JStorage'),
                            llm_model_func=None,
                            embedding_func=EmbeddingFunc(
                                embedding_dim=1536,  # Dimension của text-embedding-3-small
                                max_token_size=8000,  # Token limit của OpenAI
                                func=lambda texts: openai_embed(
                                    texts,
                                    model=config.get('DEFAULT', 'EMBEDDING_MODEL', fallback='text-embedding-3-small'),
                                    api_key=api_key,
                                    base_url=base_url
                                ),
                            ),
                        )
                except ImportError:
                    print("⚠️  Không thể import OpenAI, chuyển sang dummy")
                    embedding_type = 'dummy'

            else:
                # Dummy embeddings
                print("📝 Sử dụng dummy embeddings")
                self.rag = MiniRAG(
                    working_dir=config.get('DEFAULT', 'WORKING_DIR', fallback='./insurance_rag'),
                    kv_storage=config.get('DEFAULT', 'KV_STORAGE', fallback='JsonKVStorage'),
                    vector_storage=config.get('DEFAULT', 'VECTOR_STORAGE', fallback='NanoVectorDBStorage'),
                    graph_storage=config.get('DEFAULT', 'GRAPH_STORAGE', fallback='Neo4JStorage'),
                    llm_model_func=None,
                    embedding_func=EmbeddingFunc(
                        embedding_dim=384,
                        max_token_size=1000,
                        func=lambda texts: [[0.1] * 384 for _ in texts]  # Dummy embeddings
                    ),
                )

            self.minirag_available = True
            print("✅ MiniRAG khởi tạo thành công")

        except Exception as e:
            print(f"❌ Không thể khởi tạo MiniRAG: {e}")
            self.minirag_available = False

    def init_neo4j_direct(self):
        """Khởi tạo Neo4J driver trực tiếp"""
        print("🔗 Khởi tạo Neo4J driver trực tiếp...")

        self.driver = AsyncGraphDatabase.driver(
            os.environ["NEO4J_URI"],
            auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"])
        )

    async def search_customer_policies(self, customer_name):
        """Tìm kiếm các hợp đồng của khách hàng"""
        if self.minirag_available:
            query = f"Khách hàng {customer_name} có những hợp đồng bảo hiểm nào?"
            return await self.rag.aquery(query, param=QueryParam(mode="naive"))

        # Neo4J direct query
        async with self.driver.session() as session:
            result = await session.run("""
                MATCH (c:Customer)-[:HAS_POLICY]->(p:Policy)
                WHERE c.name CONTAINS $customer_name
                RETURN c.name as customer, collect({
                    policy_id: p.policy_id,
                    type: p.type,
                    amount: p.amount,
                    status: p.status
                }) as policies
                """,
                customer_name=customer_name
            )

            record = await result.single()
            if record:
                customer = record["customer"]
                policies = record["policies"]

                response = f"Khách hàng {customer} có {len(policies)} hợp đồng:\n"
                for policy in policies:
                    response += f"- {policy['policy_id']}: {policy['type']} - {policy['amount']:,} VND ({policy['status']})\n"

                return response
            else:
                return f"Không tìm thấy khách hàng {customer_name}"

    async def search_vehicle_insurance(self, plate_number):
        """Tìm kiếm bảo hiểm xe theo biển số"""
        if self.minirag_available:
            query = f"Bảo hiểm xe có biển số {plate_number}?"
            return await self.rag.aquery(query, param=QueryParam(mode="naive"))

        # Neo4J direct query
        async with self.driver.session() as session:
            result = await session.run("""
                MATCH (c:Customer)-[:HAS_POLICY]->(p:Policy)
                WHERE p.plate_number = $plate_number
                RETURN c.name as owner, p.vehicle as vehicle,
                       p.amount as coverage, p.yearly_premium as premium
                """,
                plate_number=plate_number
            )

            record = await result.single()
            if record:
                return f"""Biển số {plate_number}:
- Chủ xe: {record['owner']}
- Loại xe: {record['vehicle']}
- Mức bảo hiểm: {record['coverage']:,} VND
- Phí bảo hiểm năm: {record['premium']:,} VND"""
            else:
                return f"Không tìm thấy bảo hiểm cho biển số {plate_number}"

    async def query(self, question):
        """Query tổng quát"""
        print(f"🔍 Đang xử lý câu hỏi: {question}")

        # Phân tích câu hỏi để chọn loại query phù hợp
        question_lower = question.lower()

        if "khách hàng" in question_lower or "người" in question_lower:
            # Extract tên khách hàng từ câu hỏi
            customer_name = self.extract_customer_name(question)
            if customer_name:
                return await self.search_customer_policies(customer_name)

        elif "xe" in question_lower or "biển số" in question_lower:
            # Extract biển số từ câu hỏi
            plate_number = self.extract_plate_number(question)
            if plate_number:
                return await self.search_vehicle_insurance(plate_number)

        # Default: tìm kiếm trong documents Neo4J
        return await self.search_in_documents(question)

    def extract_customer_name(self, question):
        """Extract tên khách hàng từ câu hỏi"""
        import re
        # Tìm pattern tên tiếng Việt sau "khách hàng"
        name_match = re.search(r'khách hàng ([^?]+)', question, re.IGNORECASE)
        if name_match:
            name = name_match.group(1).strip()
            # Chuẩn hóa tên (loại bỏ từ thừa)
            name = re.sub(r'\s+có\s+.*', '', name, flags=re.IGNORECASE)  # Loại bỏ "có những hợp đồng nào"
            return name.strip()
        return None

    def extract_plate_number(self, question):
        """Extract biển số xe từ câu hỏi"""
        import re
        # Pattern biển số Việt Nam
        plate_match = re.search(r'([0-9]{1,2}[A-Z]-[0-9]{4,5})', question.upper())
        if plate_match:
            return plate_match.group(1)
        return None

    async def search_in_documents(self, question):
        """Tìm kiếm trong nội dung documents Neo4J"""
        # Tách câu hỏi thành các từ khóa chính
        keywords = self.extract_keywords(question.lower())

        async with self.driver.session() as session:
            documents = []

            # Thử từng từ khóa
            for keyword in keywords[:3]:  # Giới hạn 3 từ khóa đầu
                result = await session.run("""
                    MATCH (d)
                    WHERE (d:LegalDocument OR d:InsuranceRulesDocument OR d:InsuranceDocument)
                    AND d.full_content IS NOT NULL
                    AND toLower(d.full_content) CONTAINS toLower($keyword)
                    RETURN d.filename as filename, d.title as title,
                           left(d.full_content, 500) as content
                    LIMIT 2
                """, keyword=keyword)

                async for record in result:
                    doc_info = {
                        'filename': record['filename'] or 'Unknown',
                        'title': record['title'] or 'No title',
                        'content': record['content'],
                        'keyword': keyword
                    }

                    # Tránh duplicate documents
                    if not any(d['filename'] == doc_info['filename'] for d in documents):
                        documents.append(doc_info)

                if len(documents) >= 3:  # Đủ 3 documents thì dừng
                    break

            if documents:
                response = f"Tìm thấy {len(documents)} tài liệu liên quan đến câu hỏi của bạn:\n\n"
                for i, doc in enumerate(documents[:3], 1):  # Giới hạn hiển thị 3 docs
                    response += f"{i}. **{doc['title']}**\n"
                    response += f"   📄 {doc['filename']}\n"
                    response += f"   🔍 Từ khóa: \"{doc['keyword']}\"\n"
                    response += f"   💡 {doc['content']}...\n\n"

                response += "💡 Để biết thêm chi tiết, hãy hỏi cụ thể hơn về chủ đề bạn quan tâm!"
                return response
            else:
                return "Xin lỗi, tôi không tìm thấy thông tin liên quan đến câu hỏi của bạn trong cơ sở dữ liệu. Vui lòng hỏi cụ thể hơn về bảo hiểm hoặc thử tìm kiếm theo tên khách hàng/biển số xe."

    def extract_keywords(self, question):
        """Trích xuất từ khóa chính từ câu hỏi"""
        # Loại bỏ từ dừng
        stop_words = ['là', 'cái', 'đó', 'đây', 'ở', 'tại', 'và', 'hoặc', 'như', 'thế nào', 'gì', 'được', 'có', 'không', 'sao', 'tại sao', 'bị', 'bởi', 'với', 'từ', 'đến']

        words = question.split()
        keywords = []

        # Lọc từ khóa quan trọng (dài hơn 2 ký tự và không phải stop words)
        for word in words:
            if len(word) > 2 and word not in stop_words:
                keywords.append(word)

        # Nếu không có từ khóa, dùng toàn bộ câu hỏi
        if not keywords:
            keywords = [question]

        # Ưu tiên từ khóa liên quan đến bảo hiểm
        insurance_terms = ['bảo hiểm', 'xe', 'máy', 'ô tô', 'phương tiện', 'thiệt hại', 'tai nạn', 'sức khỏe', 'du lịch', 'nhân thọ']

        prioritized_keywords = []
        for term in insurance_terms:
            if term in question:
                prioritized_keywords.append(term)

        # Kết hợp prioritized keywords với keywords khác
        final_keywords = prioritized_keywords + [k for k in keywords if k not in prioritized_keywords]

        return final_keywords[:5]  # Giới hạn 5 keywords

    async def close(self):
        """Đóng connections"""
        if self.driver:
            await self.driver.close()

async def main():
    """Main function"""
    # Load config và set environment variables trước khi parse args
    import configparser
    config = configparser.ConfigParser()
    config.read('insurance_config.ini')

    # Set environment variables from config
    for key in config['DEFAULT']:
        os.environ[key.upper()] = str(config['DEFAULT'][key])

    parser = argparse.ArgumentParser(description="MiniRAG Insurance Application")
    parser.add_argument("question", nargs="?", help="Câu hỏi về bảo hiểm")
    parser.add_argument("--mode", choices=["customer", "vehicle", "general"],
                       default="general", help="Chế độ query")

    args = parser.parse_args()

    if not args.question:
        # Interactive mode
        print("🏛️  Ứng dụng MiniRAG cho Bảo hiểm")
        print("=" * 50)
        print("💡 Ví dụ câu hỏi:")
        print("   - Khách hàng Nguyễn Văn A có những hợp đồng nào?")
        print("   - Bảo hiểm xe biển số 29A-12345?")
        print("   - exit để thoát")
        print("=" * 50)

        insurance_rag = InsuranceRAG()

        while True:
            try:
                question = input("\n❓ Hỏi tôi về bảo hiểm: ").strip()
                if question.lower() in ['exit', 'quit', 'q']:
                    break

                if question:
                    answer = await insurance_rag.query(question)
                    print(f"\n📄 Trả lời: {answer}")

            except KeyboardInterrupt:
                break

        await insurance_rag.close()

    else:
        # Single query mode
        insurance_rag = InsuranceRAG()
        answer = await insurance_rag.query(args.question)
        print(answer)
        await insurance_rag.close()

if __name__ == "__main__":
    asyncio.run(main())
