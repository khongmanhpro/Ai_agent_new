#!/usr/bin/env python3
"""
Script import tất cả văn bản pháp luật bảo hiểm vào Neo4J

Import 6 files:
1. 04-2021-TTBTC_Bảo hiểm bắt buộc xe cơ giơi.md
2. MIC - Quy tắc bảo hiểm du lịch trong nước.md
3. MIC_CARE_Quy_tac_bao_hiem_suc_khoe_toan_dien_2025.md
4. MIC_Quy-tac-BH-Tai-nan-con-nguoi_2025.md
5. MIC_Quy-tac-BH-tu-nguyen-xe-o-to_2025.md
6. thuat-ngu-bao-hiem-phi-nhan-tho.md
"""

import os
import re
import asyncio
from typing import List, Dict, Any, Tuple
import configparser

# Load config
config = configparser.ConfigParser()
config.read('../config/insurance_config.ini')
for key in config['DEFAULT']:
    os.environ[key.upper()] = str(config['DEFAULT'][key])

from neo4j import AsyncGraphDatabase

class LegalDocumentParser:
    """Parser tổng hợp cho các loại văn bản pháp luật"""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.filename = os.path.basename(file_path)

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

    def parse_legal_document(self, content: str) -> Tuple[str, List[Dict[str, Any]]]:
        """Parse văn bản pháp luật (Điều 1, Điều 2, v.v.)"""
        articles = []

        # Pattern cho Điều (Article)
        article_pattern = r'###\s*Điều\s+(\d+)[\.\s]*(.*?)(?=\n###\s*Điều\s+\d+|\n##\s+[A-Z]|\Z)'
        matches = re.findall(article_pattern, content, re.DOTALL | re.MULTILINE)

        for match in matches:
            article_num, article_content = match
            title_match = re.search(r'^([^\n]+)', article_content.strip())
            title = title_match.group(1).strip() if title_match else f"Điều {article_num}"

            articles.append({
                'number': int(article_num),
                'title': title,
                'content': article_content.strip(),
                'type': 'legal_article'
            })

        return "legal_document", articles

    def parse_glossary(self, content: str) -> Tuple[str, List[Dict[str, Any]]]:
        """Parse từ điển thuật ngữ A-Z"""
        terms = []

        # Pattern cho từng term trong glossary
        # Tìm các dòng bắt đầu bằng - **term** — definition
        term_pattern = r'-\s*\*\*(.+?)\*\*\s*—\s*(.+?)(?=\n-\s*\*\*|\n##\s+[A-Z]|\Z)'
        matches = re.findall(term_pattern, content, re.DOTALL | re.MULTILINE)

        for match in matches:
            term, definition = match
            terms.append({
                'term': term.strip(),
                'definition': definition.strip(),
                'type': 'glossary_term'
            })

        return "glossary", terms

    def parse_file(self) -> Dict[str, Any]:
        """Parse file theo loại"""
        with open(self.file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse frontmatter
        frontmatter = self.parse_frontmatter(content)

        # Xác định loại file và parse content
        if 'glossary' in self.filename.lower() or 'thuat-ngu' in self.filename.lower():
            doc_type, items = self.parse_glossary(content)
        else:
            doc_type, items = self.parse_legal_document(content)

        return {
            'metadata': frontmatter,
            'doc_type': doc_type,
            'items': items,
            'full_content': content,
            'filename': self.filename
        }

class Neo4JInsuranceImporter:
    """Import dữ liệu bảo hiểm vào Neo4J"""

    def __init__(self):
        self.driver = AsyncGraphDatabase.driver(
            os.environ["NEO4J_URI"],
            auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"])
        )

    async def clear_existing_insurance_data(self):
        """Xóa dữ liệu bảo hiểm cũ (giữ lại dữ liệu cũ đã import)"""
        print("🧹 Đang xóa dữ liệu bảo hiểm cũ...")
        async with self.driver.session() as session:
            # Chỉ xóa nodes có label InsuranceDocument, không xóa LegalDocument cũ
            await session.run("MATCH (n:InsuranceDocument) DETACH DELETE n")
            await session.run("MATCH (n:InsuranceArticle) DETACH DELETE n")
            await session.run("MATCH (n:GlossaryTerm) DETACH DELETE n")
        print("✅ Đã xóa dữ liệu bảo hiểm cũ")

    async def import_insurance_document(self, parsed_data: Dict[str, Any]):
        """Import document bảo hiểm"""
        print(f"📄 Đang import: {parsed_data['filename']}")

        async with self.driver.session() as session:
            metadata = parsed_data['metadata']

            # Tạo document node
            doc_result = await session.run("""
                CREATE (d:InsuranceDocument {
                    title: $title,
                    source_title: $source_title,
                    source: $source,
                    language: $language,
                    encoding: $encoding,
                    doc_type: $doc_type,
                    issuer: $issuer,
                    jurisdiction: $jurisdiction,
                    created_at: $created_at,
                    filename: $filename,
                    full_content: $full_content
                })
                RETURN id(d) as doc_id
                """,
                title=metadata.get('title', ''),
                source_title=metadata.get('source_title', ''),
                source=metadata.get('source', ''),
                language=metadata.get('language', ''),
                encoding=metadata.get('encoding', ''),
                doc_type=metadata.get('doc_type', parsed_data['doc_type']),
                issuer=metadata.get('issuer', ''),
                jurisdiction=metadata.get('jurisdiction', ''),
                created_at=metadata.get('created_at', ''),
                filename=parsed_data['filename'],
                full_content=parsed_data['full_content']
            )

            doc_record = await doc_result.single()
            doc_id = doc_record['doc_id']

            print(f"✅ Đã tạo document node với ID: {doc_id}")

            # Import items theo loại
            if parsed_data['doc_type'] == 'legal_document':
                await self._import_legal_articles(session, doc_id, parsed_data['items'])
            elif parsed_data['doc_type'] == 'glossary':
                await self._import_glossary_terms(session, doc_id, parsed_data['items'])

    async def _import_legal_articles(self, session, doc_id: int, articles: List[Dict[str, Any]]):
        """Import các điều luật"""
        for article in articles:
            await session.run("""
                MATCH (d:InsuranceDocument)
                WHERE id(d) = $doc_id
                CREATE (d)-[:HAS_ARTICLE]->(a:InsuranceArticle {
                    number: $number,
                    title: $title,
                    content: $content,
                    type: $type
                })
                """,
                doc_id=doc_id,
                number=article['number'],
                title=article['title'],
                content=article['content'],
                type=article['type']
            )

        print(f"✅ Đã import {len(articles)} điều luật")

    async def _import_glossary_terms(self, session, doc_id: int, terms: List[Dict[str, Any]]):
        """Import từ điển thuật ngữ"""
        for term in terms:
            await session.run("""
                MATCH (d:InsuranceDocument)
                WHERE id(d) = $doc_id
                CREATE (d)-[:HAS_TERM]->(t:GlossaryTerm {
                    term: $term,
                    definition: $definition,
                    type: $type
                })
                """,
                doc_id=doc_id,
                term=term['term'],
                definition=term['definition'],
                type=term['type']
            )

        print(f"✅ Đã import {len(terms)} thuật ngữ")

    async def create_indexes(self):
        """Tạo indexes cho performance"""
        print("🔍 Đang tạo indexes cho dữ liệu bảo hiểm...")

        async with self.driver.session() as session:
            await session.run("CREATE INDEX insurance_doc_title IF NOT EXISTS FOR (d:InsuranceDocument) ON (d.title)")
            await session.run("CREATE INDEX insurance_article_number IF NOT EXISTS FOR (a:InsuranceArticle) ON (a.number)")
            await session.run("CREATE INDEX glossary_term IF NOT EXISTS FOR (t:GlossaryTerm) ON (t.term)")

        print("✅ Đã tạo indexes")

    async def get_statistics(self):
        """Lấy thống kê dữ liệu đã import"""
        async with self.driver.session() as session:
            # Đếm số lượng documents
            doc_result = await session.run("MATCH (d:InsuranceDocument) RETURN count(d) as count")
            doc_count = doc_result.single()['count']

            # Đếm số lượng articles
            article_result = await session.run("MATCH (a:InsuranceArticle) RETURN count(a) as count")
            article_count = article_result.single()['count']

            # Đếm số lượng terms
            term_result = await session.run("MATCH (t:GlossaryTerm) RETURN count(t) as count")
            term_count = term_result.single()['count']

            return {
                'documents': doc_count,
                'articles': article_count,
                'terms': term_count
            }

    async def close(self):
        """Đóng connection"""
        await self.driver.close()

def get_insurance_files():
    """Lấy danh sách files bảo hiểm cần import"""
    base_path = "/Volumes/data/data-tong/data-chatbot/DATACHUAN"
    files_to_import = [
        "04-2021-TTBTC_Bảo hiểm bắt buộc xe cơ giơi.md",
        "MIC - Quy tắc bảo hiểm du lịch trong nước.md",
        "MIC_CARE_Quy_tac_bao_hiem_suc_khoe_toan_dien_2025.md",
        "MIC_Quy-tac-BH-Tai-nan-con-nguoi_2025.md",
        "MIC_Quy-tac-BH-tu-nguyen-xe-o-to_2025.md",
        "thuat-ngu-bao-hiem-phi-nhan-tho.md"
    ]

    return [os.path.join(base_path, f) for f in files_to_import if os.path.exists(os.path.join(base_path, f))]

async def main():
    """Main async function"""
    print("🏛️  Import tất cả văn bản pháp luật bảo hiểm vào Neo4J")
    print("=" * 60)

    # Lấy danh sách files
    insurance_files = get_insurance_files()
    print(f"📁 Tìm thấy {len(insurance_files)} files cần import:")
    for i, file_path in enumerate(insurance_files, 1):
        print(f"  {i}. {os.path.basename(file_path)}")

    if not insurance_files:
        print("❌ Không tìm thấy files nào để import!")
        return

    # Khởi tạo importer
    importer = Neo4JInsuranceImporter()

    try:
        # Clear dữ liệu cũ
        await importer.clear_existing_insurance_data()

        # Import từng file
        total_files = len(insurance_files)
        for i, file_path in enumerate(insurance_files, 1):
            print(f"\n🔄 [{i}/{total_files}] Processing: {os.path.basename(file_path)}")

            # Parse file
            parser = LegalDocumentParser(file_path)
            parsed_data = parser.parse_file()

            print(f"   📊 Parsed: {len(parsed_data['items'])} items")

            # Import vào Neo4J
            await importer.import_insurance_document(parsed_data)

        # Tạo indexes
        await importer.create_indexes()

        # Thống kê cuối cùng
        stats = await importer.get_statistics()

        print("\n" + "=" * 60)
        print("✅ IMPORT HOÀN THÀNH!")
        print("=" * 60)
        print(f"📄 Insurance Documents: {stats['documents']}")
        print(f"📋 Legal Articles: {stats['articles']}")
        print(f"📚 Glossary Terms: {stats['terms']}")
        print("=" * 60)

        # Query examples
        print("🔍 Query examples có thể thử:")
        print("  - MATCH (d:InsuranceDocument)-[:HAS_ARTICLE]->(a:InsuranceArticle) WHERE d.title CONTAINS 'MIC' RETURN d.title, a.title LIMIT 5")
        print("  - MATCH (d:InsuranceDocument)-[:HAS_TERM]->(t:GlossaryTerm) WHERE t.term CONTAINS 'bảo hiểm' RETURN t.term, t.definition LIMIT 3")
        print("  - MATCH (d:InsuranceDocument {filename: '04-2021-TTBTC_Bảo hiểm bắt buộc xe cơ giơi.md'})-[:HAS_ARTICLE]->(a:InsuranceArticle) RETURN a.title")

    except Exception as e:
        print(f"❌ Lỗi import: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        await importer.close()

def run_main():
    """Wrapper để chạy main với asyncio"""
    asyncio.run(main())

if __name__ == "__main__":
    run_main()
