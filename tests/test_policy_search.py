from infrastructure.rag.store import VectorStore
from tools import policy_search


class FakeStore:
    def __init__(self, results):
        self.results = results
        self.calls = []

    def search(self, query, top_k=5, source_id=None):
        self.calls.append((query, top_k, source_id))
        return self.results


def test_policy_search_requests_only_after_sales_policy_and_returns_citation(monkeypatch):
    store = FakeStore(
        [
            {
                "id": "qa_policy",
                "metadata": {
                    "question": "保修条款",
                    "answer": "所有智能硬件产品享有一年免费保修服务。",
                    "source_id": "Doc5-售后与保修政策",
                    "title": "Doc5-售后与保修政策",
                },
            }
        ]
    )
    monkeypatch.setattr(policy_search, "get_store", lambda: store)

    result = policy_search.retrieve_policy("一年内坏了怎么处理")

    assert store.calls == [("一年内坏了怎么处理", 5, "Doc5-售后与保修政策")]
    assert result.citations[0].source_id == "Doc5-售后与保修政策"
    assert result.citations[0].section == "保修条款"


def test_policy_search_ignores_non_policy_results_even_if_store_returns_them(monkeypatch):
    store = FakeStore(
        [
            {
                "id": "qa_product",
                "metadata": {
                    "question": "怎么重置 WiFi？",
                    "answer": "长按设置键。",
                    "source_id": "Doc1-X1智能门锁FAQ",
                    "title": "Doc1-X1智能门锁FAQ",
                },
            }
        ]
    )
    monkeypatch.setattr(policy_search, "get_store", lambda: store)

    result = policy_search.retrieve_policy("维修政策")

    assert result.citations == []


def test_policy_search_without_policy_result_preserves_empty_citations(monkeypatch):
    store = FakeStore([])
    monkeypatch.setattr(policy_search, "get_store", lambda: store)

    result = policy_search.retrieve_policy("无法确认的政策")

    assert result.citations == []


class FakeCollection:
    def __init__(self):
        self.arguments = None

    def query(self, **kwargs):
        self.arguments = kwargs
        return {"ids": [[]], "distances": [[]], "documents": [[]], "metadatas": [[]]}


class FakeEmbedding:
    def embed(self, text):
        return [0.1]


def test_vector_store_passes_source_restriction_to_collection():
    collection = FakeCollection()
    store = VectorStore(embedding_service=FakeEmbedding())
    store._collection = collection

    store.search("维修政策", source_id="Doc5-售后与保修政策")

    assert collection.arguments["where"] == {"source_id": "Doc5-售后与保修政策"}
