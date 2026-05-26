import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import chromadb
from dotenv import load_dotenv

from .embedding import EmbeddingService
from .exceptions import VectorStoreError

load_dotenv()


class VectorStore:
    persist_dir: str
    collection_name: str
    _embedding_service: Optional[EmbeddingService] = None
    _client: Optional[chromadb.Client] = None
    _collection: Optional[chromadb.Collection] = None

    def __init__(
        self,
        persist_dir: Optional[str] = None,
        collection_name: Optional[str] = None,
        embedding_service: Optional[EmbeddingService] = None,
    ):
        self.persist_dir = persist_dir or os.getenv("RAG_PERSIST_DIR", "./data/chroma")
        self.collection_name = collection_name or os.getenv("RAG_COLLECTION_NAME", "faq_collection")
        self._embedding_service = embedding_service

    @property
    def embedding_service(self) -> EmbeddingService:
        if self._embedding_service is None:
            self._embedding_service = EmbeddingService()
        return self._embedding_service

    @property
    def client(self) -> chromadb.Client:
        if self._client is None:
            persist_path = Path(self.persist_dir)
            persist_path.mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(
                path=str(persist_path),
            )
        return self._client

    @property
    def collection(self) -> chromadb.Collection:
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name=self.collection_name,
            )
        return self._collection

    def add_documents(
        self,
        documents: List[Dict[str, Any]],
        ids: Optional[List[str]] = None,
    ) -> int:
        if not documents:
            return 0

        texts = [doc.get("content", "") for doc in documents]
        metadatas = [doc.get("metadata", {}) for doc in documents]

        if ids is None:
            ids = [str(i) for i in range(len(documents))]

        try:
            embeddings = self.embedding_service.embed_batch(texts)
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
            )
            return len(documents)
        except Exception as e:
            raise VectorStoreError(f"文档入库失败: {e}")

    def add_qa_pairs(
        self,
        qa_pairs: List[Dict[str, str]],
    ) -> int:
        documents = []
        ids = []
        for i, qa in enumerate(qa_pairs):
            question = qa.get("question", "")
            answer = qa.get("answer", "")
            content = f"问题: {question}\n答案: {answer}"
            documents.append({
                "content": content,
                "metadata": {
                    "question": question,
                    "answer": answer,
                    "type": "qa",
                },
            })
            ids.append(f"qa_{i}")
        return self.add_documents(documents, ids)

    def search(
        self,
        query: str,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        try:
            query_embedding = self.embedding_service.embed(query)
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
            )

            search_results = []
            if results["ids"] and results["ids"][0]:
                for i, doc_id in enumerate(results["ids"][0]):
                    distance = results["distances"][0][i] if results["distances"] else 0
                    document = results["documents"][0][i] if results["documents"] else ""
                    metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                    search_results.append({
                        "id": doc_id,
                        "content": document,
                        "metadata": metadata,
                        "distance": distance,
                    })
            return search_results
        except Exception as e:
            raise VectorStoreError(f"检索失败: {e}")

    def count(self) -> int:
        return self.collection.count()

    def delete_all(self) -> None:
        try:
            self.client.delete_collection(self.collection_name)
            self._collection = None
            self._client = None
        except Exception as e:
            raise VectorStoreError(f"清空集合失败: {e}")
