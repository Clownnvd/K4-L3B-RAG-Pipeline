"""Task 6 — Dependency-free BM25 lexical retrieval over the shared chunks."""

from __future__ import annotations

import math
import re
from collections import Counter


CORPUS: list[dict] = []
_BM25_CACHE: tuple[int, int, "BM25Index"] | None = None


def _tokenize(text: str) -> list[str]:
    return re.findall(r"\w+", text.casefold(), flags=re.UNICODE)


class BM25Index:
    def __init__(self, corpus: list[dict], k1: float = 1.5, b: float = 0.75):
        self.corpus = corpus
        self.k1 = k1
        self.b = b
        self.tokens = [_tokenize(item["content"]) for item in corpus]
        self.lengths = [len(tokens) for tokens in self.tokens]
        self.avgdl = sum(self.lengths) / len(self.lengths) if self.lengths else 1.0
        self.term_counts = [Counter(tokens) for tokens in self.tokens]
        document_frequency = Counter()
        for tokens in self.tokens:
            document_frequency.update(set(tokens))
        total = max(len(self.tokens), 1)
        self.idf = {
            term: math.log(1.0 + (total - freq + 0.5) / (freq + 0.5))
            for term, freq in document_frequency.items()
        }

    def get_scores(self, query_tokens: list[str]) -> list[float]:
        scores = []
        for counts, length in zip(self.term_counts, self.lengths):
            score = 0.0
            norm = self.k1 * (1 - self.b + self.b * length / self.avgdl)
            for term in query_tokens:
                frequency = counts.get(term, 0)
                if not frequency:
                    continue
                score += self.idf.get(term, 0.0) * (
                    frequency * (self.k1 + 1) / (frequency + norm)
                )
            scores.append(score)
        return scores


def build_bm25_index(corpus: list[dict]):
    return BM25Index(corpus)


def _ensure_corpus() -> list[dict]:
    if CORPUS:
        return CORPUS
    from .task4_chunking_indexing import chunk_documents, load_documents

    CORPUS.extend(chunk_documents(load_documents()))
    return CORPUS


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """Return BM25 SearchResults sorted by a comparable within-list score."""
    if top_k <= 0 or not query.strip():
        return []
    corpus = _ensure_corpus()
    if not corpus:
        return []
    global _BM25_CACHE
    cache_key = (id(corpus), len(corpus))
    if _BM25_CACHE is None or _BM25_CACHE[:2] != cache_key:
        _BM25_CACHE = (*cache_key, build_bm25_index(corpus))
    bm25 = _BM25_CACHE[2]
    scores = bm25.get_scores(_tokenize(query))
    indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    results = []
    for index in indices:
        if scores[index] <= 0 or len(results) >= top_k:
            break
        item = corpus[index]
        results.append(
            {
                "id": item["id"],
                "content": item["content"],
                "score": float(scores[index]),
                "metadata": dict(item["metadata"]),
                "retrieval_method": "bm25",
            }
        )
    return results


if __name__ == "__main__":
    for result in lexical_search("Miu Lê Cát Bà ma túy", top_k=3):
        print(result["score"], result["metadata"]["title"])
