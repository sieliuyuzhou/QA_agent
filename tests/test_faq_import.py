from pathlib import Path

from infrastructure.rag.store import VectorStore
from scripts.import_faq import parse_faq_file


def test_parse_faq_file_preserves_document_source(tmp_path: Path):
    source = tmp_path / "Doc1-X1智能门锁FAQ.md"
    source.write_text("**怎么重置 WiFi？**\n长按设置键。\n", encoding="utf-8")

    result = parse_faq_file(source)

    assert result == [
        {
            "question": "怎么重置 WiFi？",
            "answer": "长按设置键。",
            "source_id": "Doc1-X1智能门锁FAQ",
            "title": "Doc1-X1智能门锁FAQ",
        }
    ]


def test_add_qa_pairs_preserves_source_metadata(monkeypatch):
    captured = {}
    store = VectorStore()

    def capture_documents(documents, ids):
        captured["documents"] = documents
        captured["ids"] = ids
        return len(documents)

    monkeypatch.setattr(store, "add_documents", capture_documents)

    count = store.add_qa_pairs(
        [
            {
                "question": "怎么重置 WiFi？",
                "answer": "长按设置键。",
                "source_id": "Doc1-X1智能门锁FAQ",
                "title": "Doc1-X1智能门锁FAQ",
            }
        ]
    )

    assert count == 1
    assert captured["documents"][0]["metadata"]["source_id"] == "Doc1-X1智能门锁FAQ"
    assert captured["documents"][0]["metadata"]["title"] == "Doc1-X1智能门锁FAQ"
