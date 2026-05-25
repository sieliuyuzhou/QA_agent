from pydantic import BaseModel
from typing import List, Optional, Any, Dict


class SearchRequest(BaseModel):
    question: str
    enable_rewrite: bool = False
    top_k: int = 5


class SearchResult(BaseModel):
    id: str
    question: str
    answer: str
    source: str
    distance: float


class SearchResponse(BaseModel):
    original_question: str
    rewritten_query: Optional[str] = None
    enable_rewrite: bool
    results: List[SearchResult]


class HealthResponse(BaseModel):
    status: str
    document_count: int
