#!/usr/bin/env python3
"""
Script import văn bản pháp luật vào Neo4J cho dự án bảo hiểm

Parse và import file: 15-QD-QLBH_Quy-che-thi-DLBH_2015.md
"""

import os
import re
import asyncio
from typing import List, Dict, Any
import configparser

# Load config
config = configparser.ConfigParser()
config.read('../config/insurance_config.ini')
for key in config['DEFAULT']:
    os.environ[key.upper()] = str(config['DEFAULT'][key])

from neo4j import AsyncGraphDatabase

class LegalDocumentParser:
    """Parser cho văn bản pháp luật dạng Markdown"""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.document = None
        self.chapters = []
        self.articles = []
        self.clauses = []

    def parse_frontmatter(self, content: str) -> Dict[str, Any]:
        """Parse YAML frontmatter"""
        frontmatter = {}
        lines = content.split('\n')

        if lines[0].strip() == '---':
            i = 1
            while i < len(lines) and lines[i].strip() != '---':
                line = lines[i].strip()
                if ':' in line:
                    key, value = line.split(':', 1)
                    frontmatter[key.strip()] = value.strip().strip('"')
                i += 1

        return frontmatter

    def parse_chapters(self, content: str) -> List[Dict[str, Any]]:
        """Parse các chương"""
        chapters = []

        # Pattern cho Chương (Chapter)
        chapter_pattern = r'## Chương\s+([IVXLCDM]+)\.\s*(.+?)(?=\n## Chương|\n### Điều|\Z)'
        chapter_matches = re.findall(chapter_pattern, content, re.DOTALL | re.MULTILINE)

        for chapter_num, chapter_title in chapter_matches:
            chapters.append({
                'number': chapter_num,
                'title': chapter_title.strip(),
                'content': f"Chương {chapter_num}. {chapter_title}",
                'articles': []
            })

        return chapters

    def parse_articles(self, content: str) -> List[Dict[str, Any]]:
        """Parse các điều"""
        articles = []

        # Pattern cho Điều (Article)
        article_pattern = r'### Điều\s+(\d+)\.\s*(.+?)(?=\n### Điều|\n#### \d+\.|\n## Chương|\Z)'
        article_matches = re.findall(article_pattern, content, re.DOTALL | re.MULTILINE)

        for article_num, article_title in article_matches:
            articles.append({
                'number': int(article_num),
                'title': article_title.strip(),
                'content': f"Điều {article_num}. {article_title}",
                'clauses': []
            })

        return articles

    def parse_clauses(self, content: str) -> List[Dict[str, Any]]:
        """Parse các khoản"""
        clauses = []

        # Pattern cho khoản (số thứ tự)
        clause_pattern = r'#### (\d+)\.\s*(.+?)(?=\n#### \d+\.|\n### Điều|\n## Chương|\Z)'
        clause_matches = re.findall(clause_pattern, content, re.DOTALL | re.MULTILINE)

        for clause_num, clause_content in clause_matches:
            clauses.append({
                'number': int(clause_num),
                'content': f"{clause_num}. {clause_content.strip()}"
            })

        return clauses

    def parse_file(self) -> Dict[str, Any]:
        """Parse toàn bộ file"""
        with open(self.file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse frontmatter
        frontmatter = self.parse_frontmatter(content)

        # Parse content sau frontmatter
        content_parts = content.split('---', 2)
        if len(content_parts) >= 3:
            main_content = content_parts[2]
        else:
            main_content = content

        # Parse cấu trúc
        chapters = self.parse_chapters(main_content)
        articles = self.parse_articles(main_content)
        clauses = self.parse_clauses(main_content)

        return {
            'metadata': frontmatter,
            'chapters': chapters,
            'articles': articles,
            'clauses': clauses,
            'full_content': content
        }

class Neo4JLegalImporter:
    """Import dữ liệu pháp luật vào Neo4J"""

    def __init__(self):
        self.driver = AsyncGraphDatabase.driver(
            os.environ["NEO4J_URI"],
            auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"])
        )

    async def clear_existing_data(self):
        """Xóa dữ liệu pháp luật cũ"""
        print("🧹 Đang xóa dữ liệu pháp luật cũ...")
        async with self.driver.session() as session:
            await session.run("MATCH (n:LegalDocument) DETACH DELETE n")
            await session.run("MATCH (n:Chapter) DETACH DELETE n")
            await session.run("MATCH (n:Article) DETACH DELETE n")
            await session.run("MATCH (n:Clause) DETACH DELETE n")
        print("✅ Đã xóa dữ liệu cũ")

    async def import_document(self, parsed_data: Dict[str, Any]):
        """Import document và toàn bộ cấu trúc"""
        print("📄 Đang import văn bản pháp luật...")

        async with self.driver.session() as session:
            # Tạo document node
            metadata = parsed_data['metadata']
            doc_result = await session.run("""
                CREATE (d:LegalDocument {
                    title: $title,
                    source_title: $source_title,
                    source: $source,
                    language: $language,
                    encoding: $encoding,
                    doc_type: $doc_type,
                    jurisdiction: $jurisdiction,
                    created_at: $created_at,
                    full_content: $full_content
                })
                RETURN id(d) as doc_id
                """,
                title=metadata.get('title', ''),
                source_title=metadata.get('source_title', ''),
                source=metadata.get('source', ''),
                language=metadata.get('language', ''),
                encoding=metadata.get('encoding', ''),
                doc_type=metadata.get('doc_type', ''),
                jurisdiction=metadata.get('jurisdiction', ''),
                created_at=metadata.get('created_at', ''),
                full_content=parsed_data['full_content']
            )

            doc_record = await doc_result.single()
            doc_id = doc_record['doc_id']

            print(f"✅ Đã tạo document node với ID: {doc_id}")

            # Import chapters
            for chapter in parsed_data['chapters']:
                await session.run("""
                    MATCH (d:LegalDocument)
                    WHERE id(d) = $doc_id
                    CREATE (d)-[:HAS_CHAPTER]->(c:Chapter {
                        number: $number,
                        title: $title,
                        content: $content
                    })
                    """,
                    doc_id=doc_id,
                    number=chapter['number'],
                    title=chapter['title'],
                    content=chapter['content']
                )

            print(f"✅ Đã import {len(parsed_data['chapters'])} chương")

            # Import articles và link trực tiếp với document
            for article in parsed_data['articles']:
                await session.run("""
                    MATCH (d:LegalDocument)
                    WHERE id(d) = $doc_id
                    CREATE (d)-[:HAS_ARTICLE]->(a:Article {
                        number: $number,
                        title: $title,
                        content: $content
                    })
                    """,
                    doc_id=doc_id,
                    number=article['number'],
                    title=article['title'],
                    content=article['content']
                )

            print(f"✅ Đã import {len(parsed_data['articles'])} điều")

            # Import clauses và link với articles
            for clause in parsed_data['clauses']:
                await session.run("""
                    MATCH (a:Article)
                    WHERE a.number <= 20  // Link với các articles có sẵn
                    CREATE (a)-[:HAS_CLAUSE]->(cl:Clause {
                        number: $number,
                        content: $content
                    })
                    """,
                    number=clause['number'],
                    content=clause['content']
                )

            print(f"✅ Đã import {len(parsed_data['clauses'])} khoản")

    async def create_indexes(self):
        """Tạo indexes cho performance"""
        print("🔍 Đang tạo indexes...")

        async with self.driver.session() as session:
            await session.run("CREATE INDEX legal_doc_title IF NOT EXISTS FOR (d:LegalDocument) ON (d.title)")
            await session.run("CREATE INDEX chapter_number IF NOT EXISTS FOR (c:Chapter) ON (c.number)")
            await session.run("CREATE INDEX article_number IF NOT EXISTS FOR (a:Article) ON (a.number)")
            await session.run("CREATE INDEX clause_number IF NOT EXISTS FOR (cl:Clause) ON (cl.number)")

        print("✅ Đã tạo indexes")

    async def close(self):
        """Đóng connection"""
        await self.driver.close()

async def main():
    """Main async function"""
    print("🏛️  Import văn bản pháp luật vào Neo4J")
    print("=" * 50)

    # Path to legal document
    legal_doc_path = "/Volumes/data/data-tong/data-chatbot/DATACHUAN/15-QD-QLBH_Quy-che-thi-DLBH_2015.md"

    if not os.path.exists(legal_doc_path):
        print(f"❌ Không tìm thấy file: {legal_doc_path}")
        return

    # Parse document
    print("📖 Đang parse văn bản pháp luật...")
    parser = LegalDocumentParser(legal_doc_path)
    parsed_data = parser.parse_file()

    print(f"📊 Đã parse được:")
    print(f"   - {len(parsed_data['chapters'])} chương")
    print(f"   - {len(parsed_data['articles'])} điều")
    print(f"   - {len(parsed_data['clauses'])} khoản")

    # Import to Neo4J
    importer = Neo4JLegalImporter()

    try:
        await importer.clear_existing_data()
        await importer.import_document(parsed_data)
        await importer.create_indexes()

        print("\n" + "=" * 50)
        print("✅ Import hoàn thành!")
        print("🔍 Có thể query với các patterns:")
        print("   - MATCH (d:LegalDocument)-[:HAS_CHAPTER]->(c:Chapter) RETURN d.title, c.title")
        print("   - MATCH (c:Chapter)-[:HAS_ARTICLE]->(a:Article) WHERE c.number='III' RETURN a.title")
        print("   - MATCH (a:Article)-[:HAS_CLAUSE]->(cl:Clause) WHERE a.number=16 RETURN cl.content")

    except Exception as e:
        print(f"❌ Lỗi import: {str(e)}")

    finally:
        await importer.close()

def run_main():
    """Wrapper để chạy main với asyncio"""
    asyncio.run(main())

if __name__ == "__main__":
    run_main()
