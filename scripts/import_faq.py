import sys
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.rag import get_store


def parse_faq_file(filepath: Path) -> list[dict]:
    """Parse a FAQ markdown file, extracting Q&A pairs."""
    qa_pairs = []
    text = filepath.read_text(encoding="utf-8")
    source_id = filepath.stem

    # Pattern: **question** followed by answer text
    # Split by lines starting with **
    pattern = r'\*\*(.+?)\*\*\s*\n(.*?)(?=\n\*\*|\Z)'
    matches = re.findall(pattern, text, re.DOTALL)

    for question, answer in matches:
        question = question.strip()
        answer = answer.strip()
        if question and answer:
            qa_pairs.append(
                {
                    "question": question,
                    "answer": answer,
                    "source_id": source_id,
                    "title": source_id,
                }
            )

    return qa_pairs


def main():
    faq_dir = Path(__file__).parent.parent / "实训文档"
    if not faq_dir.exists():
        print(f"[ERROR] FAQ 文档目录不存在: {faq_dir}")
        return 1

    all_pairs = []
    for md_file in sorted(faq_dir.glob("*.md")):
        print(f"[INFO] 解析文件: {md_file.name}")
        pairs = parse_faq_file(md_file)
        print(f"       提取到 {len(pairs)} 条 Q&A")
        all_pairs.extend(pairs)

    if not all_pairs:
        print("[ERROR] 未提取到任何 Q&A 对")
        return 1

    print(f"\n[INFO] 共提取 {len(all_pairs)} 条 Q&A，开始导入向量数据库...")

    store = get_store()
    # Skip delete_all if collection is empty/doesn't exist
    if store.count() > 0:
        store.delete_all()
    count = store.add_qa_pairs(all_pairs)
    print(f"[SUCCESS] 已导入 {count} 条记录")

    # Verify
    db_count = store.count()
    print(f"[INFO] 数据库当前记录数: {db_count}")
    if db_count == len(all_pairs):
        print("[SUCCESS] 导入数量验证通过")
    else:
        print(f"[WARN] 导入数量不匹配: 预期 {len(all_pairs)}, 实际 {db_count}")

    return 0


if __name__ == "__main__":
    exit(main())
