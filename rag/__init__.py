from .embedding import EmbeddingService
from .store import VectorStore
from .exceptions import (
    RAGException,
    EmbeddingError,
    VectorStoreError,
)

__all__ = [
    "EmbeddingService",
    "VectorStore",
    "RAGException",
    "EmbeddingError",
    "VectorStoreError",
]

_store_instance = None


def get_store() -> VectorStore:
    global _store_instance
    if _store_instance is None:
        _store_instance = VectorStore()
    return _store_instance
