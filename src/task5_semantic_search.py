"""Task 5 — Dense semantic search using the shared embedding function."""

from .task4_chunking_indexing import embed_texts, get_collection


def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    """Return unique dense SearchResults sorted by cosine similarity."""
    if top_k <= 0 or not query.strip():
        return []
    query_vector = embed_texts([query])[0]
    collection = get_collection()
    count = collection.count() if hasattr(collection, "count") else top_k
    if count == 0:
        return []
    response = collection.query(
        query_embeddings=[query_vector],
        n_results=min(top_k, count),
        include=["documents", "metadatas", "distances"],
    )
    results = []
    seen = set()
    for item_id, content, metadata, distance in zip(
        response["ids"][0],
        response["documents"][0],
        response["metadatas"][0],
        response["distances"][0],
    ):
        if item_id in seen:
            continue
        seen.add(item_id)
        results.append(
            {
                "id": item_id,
                "content": content,
                "score": float(1.0 - distance),
                "metadata": metadata,
                "retrieval_method": "dense",
            }
        )
    return sorted(results, key=lambda item: item["score"], reverse=True)[:top_k]


if __name__ == "__main__":
    for result in semantic_search("Miu Lê sử dụng ma túy ở đâu?", top_k=3):
        print(result["score"], result["metadata"]["title"])
