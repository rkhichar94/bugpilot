import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from config import settings
from rag.embedder import embed

VECTOR_SIZE = 384

_client: QdrantClient | None = None


def _get_client() -> QdrantClient:
    global _client
    if _client is None:
        _client = QdrantClient(url=settings.qdrant_url)
        _ensure_collection(_client)
    return _client


def _ensure_collection(client: QdrantClient) -> None:
    existing = [c.name for c in client.get_collections().collections]
    if settings.qdrant_collection not in existing:
        print(f"[retriever] Creating Qdrant collection '{settings.qdrant_collection}'")
        client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )


def upsert(issue_key: str, text: str, metadata: dict) -> None:
    client = _get_client()
    vector = embed(text)
    point = PointStruct(
        id=str(uuid.uuid5(uuid.NAMESPACE_DNS, issue_key)),
        vector=vector,
        payload={"issue_key": issue_key, **metadata},
    )
    client.upsert(collection_name=settings.qdrant_collection, points=[point])
    print(f"[retriever] Upserted issue {issue_key} into Qdrant")


def search(query_text: str, top_k: int = 3) -> list[dict]:
    client = _get_client()
    vector = embed(query_text)

    # Return empty list gracefully if collection is empty
    collection_info = client.get_collection(settings.qdrant_collection)
    if collection_info.points_count == 0:
        print("[retriever] Collection is empty — no similar issues found")
        return []

    results = client.search(
        collection_name=settings.qdrant_collection,
        query_vector=vector,
        limit=top_k,
        with_payload=True,
    )
    return [
        {
            "issue_key": r.payload.get("issue_key", ""),
            "summary": r.payload.get("summary", ""),
            "resolution": r.payload.get("resolution", ""),
            "score": round(r.score, 4),
        }
        for r in results
    ]
