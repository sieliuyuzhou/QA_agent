import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

from rag import get_store
from .rewriter import QueryRewriter
from .exceptions import RetrieverException

load_dotenv()


@dataclass
class SearchResult:
    id: str
    content: str
    metadata: Dict[str, Any]
    distance: float


@dataclass
class RetrievalResult:
    original_question: str
    rewritten_query: Optional[str]
    results: List[SearchResult]
    enable_rewrite: bool


class RetrievalPipeline:
    top_k: int
    _rewriter: Optional[QueryRewriter] = None

    def __init__(
        self,
        top_k: Optional[int] = None,
        rewriter: Optional[QueryRewriter] = None,
    ):
        self.top_k = top_k or int(os.getenv("RETRIEVER_TOP_K", "5"))
        self._rewriter = rewriter

    @property
    def rewriter(self) -> QueryRewriter:
        if self._rewriter is None:
            self._rewriter = QueryRewriter()
        return self._rewriter

    def retrieve(
        self,
        question: str,
        enable_rewrite: bool = False,
    ) -> RetrievalResult:
        store = get_store()
        rewritten_query = None

        if enable_rewrite:
            rewritten_query = self.rewriter.rewrite(question)
            query_to_search = rewritten_query
        else:
            query_to_search = question

        raw_results = store.search(query_to_search, top_k=self.top_k)
        results = [
            SearchResult(
                id=r["id"],
                content=r["content"],
                metadata=r["metadata"],
                distance=r["distance"],
            )
            for r in raw_results
        ]

        return RetrievalResult(
            original_question=question,
            rewritten_query=rewritten_query,
            results=results,
            enable_rewrite=enable_rewrite,
        )

    def to_dict(self, result: RetrievalResult) -> Dict[str, Any]:
        return {
            "original_question": result.original_question,
            "rewritten_query": result.rewritten_query,
            "enable_rewrite": result.enable_rewrite,
            "results": [
                {
                    "id": r.id,
                    "question": r.metadata.get("question", ""),
                    "answer": r.metadata.get("answer", ""),
                    "source": r.metadata.get("source", ""),
                    "distance": r.distance,
                }
                for r in result.results
            ],
        }
