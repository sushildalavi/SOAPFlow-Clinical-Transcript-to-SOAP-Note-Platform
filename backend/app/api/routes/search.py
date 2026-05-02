"""
Semantic search endpoint — POST /api/v1/search
RAG-powered retrieval of similar past SOAP notes using Qdrant + ClinicalBERT.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

from app.services.search import search_similar_notes, SearchResult

router = APIRouter()


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=10, description="Clinical query or transcript excerpt")
    top_k: int = Field(default=5, ge=1, le=20)
    score_threshold: float = Field(default=0.5, ge=0.0, le=1.0)


class SearchResultItem(BaseModel):
    note_id: int
    title: str
    score: float
    snippet: str
    mode: str
    created_at: Optional[str]


class SearchResponse(BaseModel):
    success: bool = True
    query: str
    results: list[SearchResultItem]
    total: int
    engine: str = "qdrant+clinicalbert"


@router.post("/search", response_model=SearchResponse, tags=["Search"])
async def semantic_search(request: SearchRequest) -> SearchResponse:
    """
    Retrieve semantically similar past SOAP notes using RAG.

    Uses ClinicalBERT (S-PubMedBert-MS-MARCO) embeddings stored in Qdrant
    to find the most relevant historical clinical notes for a given query.

    Use cases:
    - Find similar patient presentations before generating a new note
    - Retrieve reference notes for evaluation
    - Clinical decision support context retrieval

    Returns up to top_k results sorted by cosine similarity score.
    """
    results: list[SearchResult] = search_similar_notes(
        query=request.query,
        top_k=request.top_k,
        score_threshold=request.score_threshold,
    )

    return SearchResponse(
        query=request.query,
        results=[
            SearchResultItem(
                note_id=r.note_id,
                title=r.title,
                score=r.score,
                snippet=r.snippet,
                mode=r.mode,
                created_at=r.created_at,
            )
            for r in results
        ],
        total=len(results),
    )
