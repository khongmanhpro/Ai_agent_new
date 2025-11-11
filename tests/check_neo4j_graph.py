#!/usr/bin/env python3
"""
Kiểm tra graph data đã import vào Neo4J
"""

import os
import sys
sys.path.append('/Volumes/data/MINIRAG')

import configparser
config = configparser.ConfigParser()
config.read('/Volumes/data/MINIRAG/config/insurance_config.ini')

# Neo4J connection
from neo4j import GraphDatabase

NEO4J_URI = config.get('DEFAULT', 'NEO4J_URI')
NEO4J_USERNAME = config.get('DEFAULT', 'NEO4J_USERNAME')
NEO4J_PASSWORD = config.get('DEFAULT', 'NEO4J_PASSWORD')

def check_graph_data():
    """Kiểm tra dữ liệu graph trong Neo4J"""
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

    try:
        with driver.session() as session:
            print("🔍 KIỂM TRA GRAPH DATA TRONG NEO4J...")
            print("=" * 50)

            # Count total nodes
            result = session.run("MATCH (n) RETURN count(n) as node_count")
            node_count = result.single()["node_count"]
            print(f"📊 Tổng số nodes: {node_count:,}")

            # Count total relationships
            result = session.run("MATCH ()-[r]->() RETURN count(r) as rel_count")
            rel_count = result.single()["rel_count"]
            print(f"🔗 Tổng số relationships: {rel_count:,}")

            print()

            # Sample nodes
            print("🎯 MẪU NODES:")
            result = session.run("MATCH (n) RETURN n LIMIT 5")
            for record in result:
                node = record["n"]
                labels = list(node.labels)
                properties = dict(node)
                print(f"  • Labels: {labels}")
                print(f"    Properties: {properties}")
                print()

            # Sample relationships
            print("🔗 MẪU RELATIONSHIPS:")
            result = session.run("MATCH (a)-[r]->(b) RETURN a.id, type(r), r.weight, b.id LIMIT 5")
            for record in result:
                print(f"  • {record['a.id']} -[{record['type(r)']}:{record['r.weight']}]-> {record['b.id']}")
                print()

            # Entity types
            print("🏷️  LOẠI ENTITIES:")
            result = session.run("MATCH (n) RETURN DISTINCT labels(n) as labels, count(*) as count ORDER BY count DESC LIMIT 10")
            for record in result:
                labels = list(record["labels"])
                count = record["count"]
                print(f"  • {labels}: {count} nodes")

            print()
            print("✅ KIỂM TRA HOÀN TẤT!")

    except Exception as e:
        print(f"❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()

    finally:
        driver.close()

if __name__ == "__main__":
    check_graph_data()
