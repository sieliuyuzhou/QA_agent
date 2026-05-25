import os
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv

from retriever import get_pipeline, RetrieverException
from rag import get_store
from .schemas import SearchRequest, SearchResponse, SearchResult, HealthResponse

load_dotenv()

app = FastAPI(
    title="RAG Search API",
    description="FAQ retrieval service with query rewriting",
    version="1.0.0",
)

pipeline = get_pipeline()
store = get_store()


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="ok",
        document_count=store.count(),
    )


@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="question is required")

    try:
        result = pipeline.retrieve(
            question=request.question,
            enable_rewrite=request.enable_rewrite,
        )

        results = [
            SearchResult(
                id=r.id,
                question=r.metadata.get("question", ""),
                answer=r.metadata.get("answer", ""),
                source=r.metadata.get("source", ""),
                distance=r.distance,
            )
            for r in result.results[:request.top_k]
        ]

        return SearchResponse(
            original_question=result.original_question,
            rewritten_query=result.rewritten_query,
            enable_rewrite=result.enable_rewrite,
            results=results,
        )
    except RetrieverException as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    return {"message": "RAG Search API", "docs": "/docs"}
