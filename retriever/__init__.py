from .rewriter import QueryRewriter
from .pipeline import RetrievalPipeline, SearchResult, RetrievalResult
from .exceptions import RetrieverException, RewriteError

__all__ = [
    "QueryRewriter",
    "RetrievalPipeline",
    "SearchResult",
    "RetrievalResult",
    "RetrieverException",
    "RewriteError",
]

_pipeline_instance = None


def get_pipeline() -> RetrievalPipeline:
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = RetrievalPipeline()
    return _pipeline_instance
