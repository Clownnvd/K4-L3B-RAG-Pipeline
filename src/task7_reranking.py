"""Task 7 — Reciprocal Rank Fusion without mutating input rankings."""

from __future__ import annotations

from copy import deepcopy


def rerank_rrf(
    ranked_lists: list[list[dict]],
    top_k: int = 5,
    k: int = 60,
) -> list[dict]:
    """Fuse rankings by reciprocal rank and return unique hybrid results."""
    if top_k <= 0:
        return []
    scores: dict[str, float] = {}
    items: dict[str, dict] = {}
    for ranked_list in ranked_lists:
        seen_in_list = set()
        for rank, item in enumerate(ranked_list, 1):
            item_id = item["id"]
            if item_id in seen_in_list:
                continue
            seen_in_list.add(item_id)
            scores[item_id] = scores.get(item_id, 0.0) + 1.0 / (k + rank)
            items.setdefault(item_id, deepcopy(item))
    ranked_ids = sorted(scores, key=lambda item_id: (-scores[item_id], item_id))
    results = []
    for item_id in ranked_ids[:top_k]:
        result = deepcopy(items[item_id])
        result["score"] = float(scores[item_id])
        result["retrieval_method"] = "hybrid"
        results.append(result)
    return results


if __name__ == "__main__":
    print("Run pytest tests/test_contracts.py -q")
