#!/usr/bin/env python3
"""
Script import Quy tắc bảo hiểm với cấu trúc Roman numerals (I., II., III.)

Handle files như quytac-bh-nha-tu-nhan-vni-2019.md
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

class InsuranceRulesParser:
    """Parser cho Quy tắc bảo hiểm với cấu trúc Roman numerals"""

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

    def parse_roman_sections(self, content: str) -> Tuple[str, List[Dict[str, Any]]]:
        """Parse sections với Roman numerals (I., II., III.)"""
        sections = []

        # Pattern cho Roman numeral sections
        # ## I. Định nghĩa
        # ## II. Hợp đồng bảo hiểm
        # ## III. Hiệu lực bảo hiểm và phí bảo hiểm
        section_pattern = r'##\s+([IVXLCDM]+)\.\s*(.*?)(?=\n##\s+[IVXLCDM]+\.|\n##\s+\d+\.|\n###|\n---|\Z)'

        matches = re.findall(section_pattern, content, re.DOTALL | re.MULTILINE)

        for match in matches:
            roman_num, section_title = match
            section_content = match[1] + match[2] if len(match) > 2 else match[1]

            # Extract sub-items (numbered lists)
            sub_items = self.extract_sub_items(section_content)

            sections.append({
                'roman_number': roman_num,
                'title': section_title.strip(),
                'content': section_content.strip(),
                'sub_items': sub_items,
                'type': 'insurance_rule_section'
            })

        return "insurance_rules", sections

    def extract_sub_items(self, content: str) -> List[Dict[str, Any]]:
        """Extract sub-items từ numbered lists"""
        sub_items = []

        # Pattern cho numbered items: 1. 2. 3. hoặc a) b) c)
        item_patterns = [
            (r'(\d+)\.\s*(.*?)(?=\n\d+\.\s|\n[a-z]\)|\n[A-Z]\.|\n##|\n---|\Z)', 'numbered'),
            (r'([a-z])\)\s*(.*?)(?=\n[a-z]\)|\n[A-Z]\.|\n\d+\.\s|\n##|\n---|\Z)', 'lettered'),
            (r'([A-Z])\.\s*(.*?)(?=\n[A-Z]\.|\n[a-z]\)|\n\d+\.\s|\n##|\n---|\Z)', 'capital')
        ]

        for pattern, item_type in item_patterns:
            matches = re.findall(pattern, content, re.DOTALL | re.MULTILINE)
            for match in matches:
                number, item_content = match
                sub_items.append({
                    'number': number,
                    'type': item_type,
                    'content': item_content.strip()
                })

        return sub_items

    def parse_file(self) -> Dict[str, Any]:
        """Parse file theo loại"""
        with open(self.file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse frontmatter
        frontmatter = self.parse_frontmatter(content)

        # Parse với Roman numerals structure
        doc_type, sections = self.parse_roman_sections(content)

        return {
            'metadata': frontmatter,
            'doc_type': doc_type,
            'sections': sections,
            'full_content': content,
            'filename': self.filename
        }

class Neo4JInsuranceRulesImporter:
    """Import Quy tắc bảo hiểm vào Neo4J"""

    def __init__(self):
        self.driver = AsyncGraphDatabase.driver(
            os.environ["NEO4J_URI"],
            auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"])
        )

    async def clear_existing_rules(self):
        """Xóa dữ liệu Quy tắc bảo hiểm cũ"""
        print("🧹 Đang xóa dữ liệu Quy tắc bảo hiểm cũ...")
        async with self.driver.session() as session:
            await session.run("MATCH (n:InsuranceRulesDocument) DETACH DELETE n")
            await session.run("MATCH (n:InsuranceRuleSection) DETACH DELETE n")
            await session.run("MATCH (n:InsuranceRuleItem) DETACH DELETE n")
        print("✅ Đã xóa dữ liệu Quy tắc bảo hiểm cũ")

    async def import_insurance_rules(self, parsed_data: Dict[str, Any]):
        """Import Quy tắc bảo hiểm"""
        print(f"📄 Đang import: {parsed_data['filename']}")

        async with self.driver.session() as session:
            metadata = parsed_data['metadata']

            # Tạo document node
            doc_result = await session.run("""
                CREATE (d:InsuranceRulesDocument {
                    title: $title,
                    source_title: $source_title,
                    source: $source,
                    language: $language,
                    encoding: $encoding,
                    doc_type: $doc_type,
                    issuer: $issuer,
                    jurisdiction: $jurisdiction,
                    created_at: $created_at,
                    effective_date: $effective_date,
                    category: $category,
                    dataset_id: $dataset_id,
                    integrity: $integrity,
                    format: $format,
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
                effective_date=metadata.get('effective_date', ''),
                category=metadata.get('category', ''),
                dataset_id=metadata.get('dataset_id', ''),
                integrity=metadata.get('integrity', ''),
                format=metadata.get('format', ''),
                filename=parsed_data['filename'],
                full_content=parsed_data['full_content']
            )

            doc_record = await doc_result.single()
            doc_id = doc_record['doc_id']

            print(f"✅ Đã tạo document node với ID: {doc_id}")

            # Import sections
            await self._import_sections(session, doc_id, parsed_data['sections'])

    async def _import_sections(self, session, doc_id: int, sections: List[Dict[str, Any]]):
        """Import các sections"""
        for section in sections:
            # Tạo section node
            section_result = await session.run("""
                MATCH (d:InsuranceRulesDocument)
                WHERE id(d) = $doc_id
                CREATE (d)-[:HAS_RULE_SECTION]->(s:InsuranceRuleSection {
                    roman_number: $roman_number,
                    title: $title,
                    content: $content,
                    type: $type
                })
                RETURN id(s) as section_id
                """,
                doc_id=doc_id,
                roman_number=section['roman_number'],
                title=section['title'],
                content=section['content'],
                type=section['type']
            )

            section_record = await section_result.single()
            section_id = section_record['section_id']

            # Import sub-items
            for sub_item in section['sub_items']:
                await session.run("""
                    MATCH (s:InsuranceRuleSection)
                    WHERE id(s) = $section_id
                    CREATE (s)-[:HAS_RULE_ITEM]->(i:InsuranceRuleItem {
                        number: $number,
                        content: $content,
                        item_type: $item_type
                    })
                    """,
                    section_id=section_id,
                    number=sub_item['number'],
                    content=sub_item['content'],
                    item_type=sub_item['type']
                )

        print(f"✅ Đã import {len(sections)} sections")

    async def create_indexes(self):
        """Tạo indexes cho performance"""
        print("🔍 Đang tạo indexes cho Quy tắc bảo hiểm...")

        async with self.driver.session() as session:
            await session.run("CREATE INDEX insurance_rules_doc_title IF NOT EXISTS FOR (d:InsuranceRulesDocument) ON (d.title)")
            await session.run("CREATE INDEX insurance_rule_section_roman IF NOT EXISTS FOR (s:InsuranceRuleSection) ON (s.roman_number)")
            await session.run("CREATE INDEX insurance_rule_item IF NOT EXISTS FOR (i:InsuranceRuleItem) ON (i.number)")

        print("✅ Đã tạo indexes")

    async def get_statistics(self):
        """Lấy thống kê dữ liệu đã import"""
        async with self.driver.session() as session:
            # Đếm số lượng documents
            doc_result = await session.run("MATCH (d:InsuranceRulesDocument) RETURN count(d) as count")
            doc_count = (await doc_result.single())['count']

            # Đếm số lượng sections
            section_result = await session.run("MATCH (s:InsuranceRuleSection) RETURN count(s) as count")
            section_count = (await section_result.single())['count']

            # Đếm số lượng items
            item_result = await session.run("MATCH (i:InsuranceRuleItem) RETURN count(i) as count")
            item_count = (await item_result.single())['count']

            return {
                'documents': doc_count,
                'sections': section_count,
                'items': item_count
            }

    async def close(self):
        """Đóng connection"""
        await self.driver.close()

async def main():
    """Main async function"""
    print("🏛️  Import Quy tắc bảo hiểm với cấu trúc Roman numerals vào Neo4J")
    print("=" * 70)

    # File cần import
    rules_file = "/Volumes/data/MINIRAG/data/dataw/quytac-bh-nha-tu-nhan-vni-2019.md"

    if not os.path.exists(rules_file):
        print(f"❌ Không tìm thấy file: {rules_file}")
        return

    print(f"📁 File cần import: {os.path.basename(rules_file)}")

    # Khởi tạo importer
    importer = Neo4JInsuranceRulesImporter()

    try:
        # Clear dữ liệu cũ
        await importer.clear_existing_rules()

        # Parse file
        parser = InsuranceRulesParser(rules_file)
        parsed_data = parser.parse_file()

        print(f"📊 Parsed: {len(parsed_data['sections'])} sections")

        # Import vào Neo4J
        await importer.import_insurance_rules(parsed_data)

        # Tạo indexes
        await importer.create_indexes()

        # Thống kê cuối cùng
        stats = await importer.get_statistics()

        print("\n" + "=" * 70)
        print("✅ IMPORT HOÀN THÀNH!")
        print("=" * 70)
        print(f"📄 Insurance Rules Documents: {stats['documents']}")
        print(f"🏗️  Rule Sections: {stats['sections']}")
        print(f"📋 Rule Items: {stats['items']}")
        print("=" * 70)

        # Query examples
        print("🔍 Query examples có thể thử:")
        print("  - MATCH (d:InsuranceRulesDocument)-[:HAS_RULE_SECTION]->(s:InsuranceRuleSection) WHERE d.filename CONTAINS 'vni' RETURN d.title, s.title")
        print("  - MATCH (s:InsuranceRuleSection)-[:HAS_RULE_ITEM]->(i:InsuranceRuleItem) WHERE s.roman_number='I' RETURN s.title, i.number, i.content LIMIT 5")
        print("  - MATCH (d:InsuranceRulesDocument {filename: 'quytac-bh-nha-tu-nhan-vni-2019.md'})-[:HAS_RULE_SECTION]->(s:InsuranceRuleSection) RETURN s.roman_number, s.title")

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
