#!/usr/bin/env python3
"""
Script để load dữ liệu bảo hiểm mẫu vào MiniRAG + Neo4J
"""

import os
import sys
import asyncio
sys.path.append('/Volumes/data/MINIRAG/MiniRAG')

# Import MiniRAG (nếu có thể)
try:
    from minirag import MiniRAG, QueryParam
    from minirag.utils import EmbeddingFunc
    MINIRAG_AVAILABLE = True
except ImportError:
    from neo4j import AsyncGraphDatabase
    MINIRAG_AVAILABLE = False

# Dữ liệu bảo hiểm mẫu (JSON format)
SAMPLE_INSURANCE_DATA = [
    {
        "customer_id": "C001",
        "name": "Nguyễn Văn A",
        "dob": "1985-03-15",
        "policies": [
            {
                "policy_id": "BH-001",
                "type": "life_insurance",
                "amount": 500000000,
                "monthly_premium": 2500000,
                "duration": 20,
                "status": "active"
            }
        ]
    },
    {
        "customer_id": "C002",
        "name": "Trần Thị B",
        "dob": "1990-07-22",
        "policies": [
            {
                "policy_id": "BH-002",
                "type": "health_insurance",
                "amount": 200000000,
                "monthly_premium": 1800000,
                "duration": 10,
                "status": "active"
            }
        ]
    },
    {
        "customer_id": "C003",
        "name": "Lê Văn C",
        "dob": "1978-12-10",
        "policies": [
            {
                "policy_id": "BH-003",
                "type": "vehicle_insurance",
                "vehicle": "Toyota Camry 2020",
                "plate_number": "29A-12345",
                "amount": 800000000,
                "yearly_premium": 15000000,
                "status": "active"
            }
        ]
    }
]

async def load_data_with_minirag():
    """Load dữ liệu sử dụng MiniRAG"""
    if not MINIRAG_AVAILABLE:
        print("⚠️  MiniRAG không khả dụng, sử dụng Neo4J driver trực tiếp")
        await load_data_with_neo4j()
        return

    print("🚀 Load dữ liệu với MiniRAG...")

    # Khởi tạo MiniRAG với Neo4J
    rag = MiniRAG(
        working_dir="./insurance_rag",
        kv_storage="JsonKVStorage",
        vector_storage="NanoVectorDBStorage",
        graph_storage="Neo4JStorage",
        llm_model_func=None,  # Không cần LLM cho demo
        embedding_func=EmbeddingFunc(
            embedding_dim=384,
            max_token_size=1000,
            func=lambda texts: [[0.1] * 384 for _ in texts]  # Dummy embeddings
        ),
    )

    # Chuyển đổi dữ liệu thành text documents
    documents = []
    for customer in SAMPLE_INSURANCE_DATA:
        doc = f"""
        Khách hàng: {customer['name']} (ID: {customer['customer_id']})
        Ngày sinh: {customer['dob']}

        Thông tin bảo hiểm:
        """
        for policy in customer['policies']:
            doc += f"""
        - Mã hợp đồng: {policy['policy_id']}
        - Loại bảo hiểm: {policy['type']}
        - Số tiền bảo hiểm: {policy['amount']:,} VND
        - Phí bảo hiểm: {policy.get('monthly_premium', policy.get('yearly_premium', 0)):,} VND
        - Thời hạn: {policy['duration']} năm
        - Trạng thái: {policy['status']}
        """
        documents.append(doc.strip())

    await rag.ainsert(documents)
    print("✅ Dữ liệu đã được load vào MiniRAG!")

async def load_data_with_neo4j():
    """Load dữ liệu sử dụng Neo4J driver trực tiếp"""
    print("🔗 Load dữ liệu với Neo4J driver...")

    driver = AsyncGraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"])
    )

    try:
        async with driver.session() as session:
            for customer in SAMPLE_INSURANCE_DATA:
                # Tạo customer node
                await session.run("""
                    CREATE (c:Customer {
                        customer_id: $customer_id,
                        name: $name,
                        dob: date($dob),
                        created_at: datetime()
                    })
                    """,
                    customer_id=customer["customer_id"],
                    name=customer["name"],
                    dob=customer["dob"]
                )

                # Tạo policy nodes và relationships
                for policy in customer["policies"]:
                    await session.run("""
                        CREATE (p:Policy {
                            policy_id: $policy_id,
                            type: $type,
                            amount: $amount,
                            duration: $duration,
                            status: $status,
                            created_at: datetime()
                        })
                        """,
                        policy_id=policy["policy_id"],
                        type=policy["type"],
                        amount=policy["amount"],
                        duration=policy["duration"],
                        status=policy["status"]
                    )

                    # Tạo relationship giữa customer và policy
                    await session.run("""
                        MATCH (c:Customer {customer_id: $customer_id})
                        MATCH (p:Policy {policy_id: $policy_id})
                        CREATE (c)-[:HAS_POLICY]->(p)
                        """,
                        customer_id=customer["customer_id"],
                        policy_id=policy["policy_id"]
                    )

        print("✅ Dữ liệu đã được load vào Neo4J!")

    finally:
        await driver.close()

def main():
    """Main function"""
    print("📊 Load dữ liệu bảo hiểm mẫu")
    print("=" * 40)

    # Load dữ liệu
    asyncio.run(load_data_with_minirag())

    print("\n" + "=" * 40)
    print("✅ Hoàn thành load dữ liệu mẫu!")

if __name__ == "__main__":
    main()
