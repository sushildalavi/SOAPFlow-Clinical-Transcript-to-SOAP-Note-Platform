"""
Semantic search service using Qdrant vector store + ClinicalBERT embeddings.
Enables RAG over past SOAP notes — retrieve similar clinical cases.

Embedding model: pritamdeka/S-PubMedBert-MS-MARCO (clinical domain)
Fallback: sentence-transformers/all-MiniLM-L6-v2 (general purpose)

Architecture:
    SOAP note text → SentenceTransformer → 768-dim vector → Qdrant upsert
    Query text → SentenceTransformer → 768-dim vector → Qdrant search → top-k results
"""
import uuid
import structlog
from typing import Optional
from dataclasses import dataclass

log = structlog.get_logger("soapflow.search")

COLLECTION_NAME = "soapflow_notes"
VECTOR_DIM = 768
TOP_K_DEFAULT = 5

# Preferred clinical embedding model; fallback to general-purpose
EMBEDDING_MODELS = [
    "pritamdeka/S-PubMedBert-MS-MARCO",   # Clinical domain, 768-dim
    "sentence-transformers/all-MiniLM-L6-v2",  # General, 384-dim
]

_encoder = None
_qdrant = None


def _get_encoder():
    global _encoder
    if _encoder is None:
        try:
            from sentence_transformers import SentenceTransformer
            for model_name in EMBEDDING_MODELS:
                try:
                    _encoder = SentenceTransformer(model_name)
                    log.info("encoder_loaded", model=model_name)
                    break
                except Exception:
                    continue
        except ImportError:
            log.warning("sentence_transformers_unavailable")
    return _encoder


def _get_qdrant():
    global _qdrant
    if _qdrant is None:
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams
            _qdrant = QdrantClient(host="localhost", port=6333, timeout=5)
            # Create collection if it doesn't exist
            existing = [c.name for c in _qdrant.get_collections().collections]
            if COLLECTION_NAME not in existing:
                _qdrant.create_collection(
                    collection_name=COLLECTION_NAME,
                    vectors_config=VectorParams(
                        size=VECTOR_DIM,
                        distance=Distance.COSINE,
                    ),
                )
                log.info("qdrant_collection_created", name=COLLECTION_NAME)
            else:
                log.info("qdrant_connected", collection=COLLECTION_NAME)
        except Exception as e:
            log.warning("qdrant_unavailable", error=str(e))
    return _qdrant


@dataclass
class SearchResult:
    note_id: int
    title: str
    score: float
    snippet: str
    mode: str
    created_at: Optional[str]


def embed_text(text: str) -> Optional[list[float]]:
    """Convert text to embedding vector using ClinicalBERT."""
    encoder = _get_encoder()
    if not encoder:
        return None
    try:
        vector = encoder.encode(text, normalize_embeddings=True)
        return vector.tolist()
    except Exception as e:
        log.error("embed_error", error=str(e))
        return None


def index_note(note_id: int, title: str, soap_note: dict, mode: str, created_at: str) -> Optional[str]:
    """
    Embed and index a SOAP note into Qdrant.
    Returns the Qdrant point ID (UUID string) or None on failure.
    """
    qdrant = _get_qdrant()
    if not qdrant:
        return None

    # Combine SOAP sections for embedding
    text = f"{title}. {soap_note.get('subjective', '')} {soap_note.get('assessment', '')} {soap_note.get('plan', '')}"
    vector = embed_text(text)
    if not vector:
        return None

    point_id = str(uuid.uuid4())
    try:
        from qdrant_client.models import PointStruct
        qdrant.upsert(
            collection_name=COLLECTION_NAME,
            points=[
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={
                        "note_id": note_id,
                        "title": title,
                        "mode": mode,
                        "created_at": created_at,
                        "snippet": text[:300],
                    },
                )
            ],
        )
        log.info("note_indexed", note_id=note_id, point_id=point_id)
        return point_id
    except Exception as e:
        log.error("index_error", note_id=note_id, error=str(e))
        return None


def search_similar_notes(
    query: str,
    top_k: int = TOP_K_DEFAULT,
    score_threshold: float = 0.5,
) -> list[SearchResult]:
    """
    Retrieve the top-k most semantically similar SOAP notes for a query.
    Uses cosine similarity over ClinicalBERT embeddings in Qdrant.
    """
    qdrant = _get_qdrant()
    if not qdrant:
        return []

    vector = embed_text(query)
    if not vector:
        return []

    try:
        results = qdrant.search(
            collection_name=COLLECTION_NAME,
            query_vector=vector,
            limit=top_k,
            score_threshold=score_threshold,
        )
        return [
            SearchResult(
                note_id=r.payload.get("note_id"),
                title=r.payload.get("title", "Untitled"),
                score=round(r.score, 4),
                snippet=r.payload.get("snippet", ""),
                mode=r.payload.get("mode", "unknown"),
                created_at=r.payload.get("created_at"),
            )
            for r in results
        ]
    except Exception as e:
        log.error("search_error", error=str(e))
        return []


def delete_note_vector(point_id: str) -> None:
    """Remove a note's vector from Qdrant when the note is deleted."""
    qdrant = _get_qdrant()
    if not qdrant or not point_id:
        return
    try:
        qdrant.delete(
            collection_name=COLLECTION_NAME,
            points_selector=[point_id],
        )
    except Exception:
        pass
