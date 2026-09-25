"""Task 8 — PageIndex vectorless fallback with a local document-ID cache."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv


load_dotenv()

ROOT = Path(__file__).parent.parent
LEGAL_DIR = ROOT / "data" / "landing" / "legal"
CACHE_PATH = ROOT / "pageindex_doc_ids.json"
PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "").strip()
PAGEINDEX_API_URL = os.getenv("PAGEINDEX_API_URL", "https://api.pageindex.ai").rstrip("/")
REQUEST_TIMEOUT_SECONDS = float(os.getenv("PAGEINDEX_REQUEST_TIMEOUT_SECONDS", "30"))
POLL_TIMEOUT_SECONDS = float(os.getenv("PAGEINDEX_POLL_TIMEOUT_SECONDS", "60"))
POLL_INTERVAL_SECONDS = float(os.getenv("PAGEINDEX_POLL_INTERVAL_SECONDS", "2"))


def _headers() -> dict[str, str]:
    if not PAGEINDEX_API_KEY:
        raise RuntimeError("PAGEINDEX_API_KEY chưa được cấu hình")
    return {"api_key": PAGEINDEX_API_KEY}


def _load_cache() -> dict[str, Any]:
    if not CACHE_PATH.exists():
        return {"version": 1, "documents": {}}
    try:
        payload = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"version": 1, "documents": {}}
    if not isinstance(payload, dict) or not isinstance(payload.get("documents"), dict):
        return {"version": 1, "documents": {}}
    return payload


def _save_cache(cache: dict[str, Any]) -> None:
    temporary = CACHE_PATH.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(CACHE_PATH)


def _response_json(response: requests.Response, action: str) -> dict[str, Any]:
    if response.status_code != 200:
        raise RuntimeError(f"PageIndex {action} thất bại: HTTP {response.status_code}")
    payload = response.json()
    if not isinstance(payload, dict):
        raise RuntimeError(f"PageIndex {action} trả về dữ liệu không hợp lệ")
    return payload


def upload_documents() -> None:
    """Upload legal PDFs once and cache PageIndex document IDs locally."""
    headers = _headers()
    documents = sorted(LEGAL_DIR.glob("*.pdf"))
    if not documents:
        raise RuntimeError(f"Không tìm thấy PDF trong {LEGAL_DIR}")

    cache = _load_cache()
    entries = cache.setdefault("documents", {})
    changed = False
    for path in documents:
        cached = entries.get(path.name, {})
        if isinstance(cached, dict) and str(cached.get("doc_id", "")).strip():
            continue
        with path.open("rb") as handle:
            response = requests.post(
                f"{PAGEINDEX_API_URL}/doc/",
                headers=headers,
                files={"file": (path.name, handle, "application/pdf")},
                data={"if_retrieval": "true"},
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
        payload = _response_json(response, f"upload {path.name}")
        doc_id = str(payload.get("doc_id", "")).strip()
        if not doc_id:
            raise RuntimeError(f"PageIndex không trả doc_id cho {path.name}")
        entries[path.name] = {"doc_id": doc_id, "source": path.name}
        changed = True
        _save_cache(cache)

    if changed:
        _save_cache(cache)


def _query_document(doc_id: str, query: str) -> dict[str, Any]:
    response = requests.post(
        f"{PAGEINDEX_API_URL}/retrieval/",
        headers=_headers(),
        json={"doc_id": doc_id, "query": query, "thinking": False},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    submitted = _response_json(response, "submit retrieval")
    retrieval_id = str(submitted.get("retrieval_id", "")).strip()
    if not retrieval_id:
        raise RuntimeError("PageIndex không trả retrieval_id")

    deadline = time.monotonic() + POLL_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        response = requests.get(
            f"{PAGEINDEX_API_URL}/retrieval/{retrieval_id}/",
            headers=_headers(),
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        payload = _response_json(response, "poll retrieval")
        status = str(payload.get("status", "")).casefold()
        if status in {"completed", "complete", "succeeded", "success"}:
            return payload
        if status in {"failed", "error", "cancelled", "canceled"}:
            raise RuntimeError(f"PageIndex retrieval kết thúc với trạng thái {status}")
        time.sleep(POLL_INTERVAL_SECONDS)
    raise TimeoutError(f"PageIndex retrieval quá {POLL_TIMEOUT_SECONDS:g} giây")


def _retrieved_nodes(payload: dict[str, Any]) -> list[dict[str, Any]]:
    candidates: Any = payload.get("retrieved_nodes")
    if candidates is None and isinstance(payload.get("result"), dict):
        candidates = payload["result"].get("retrieved_nodes")
    if candidates is None and isinstance(payload.get("data"), dict):
        candidates = payload["data"].get("retrieved_nodes")
    return [node for node in (candidates or []) if isinstance(node, dict)]


def _parse_retrieval(
    payload: dict[str, Any],
    *,
    doc_id: str,
    source: str,
) -> list[dict]:
    """Convert PageIndex retrieval nodes into the shared SearchResult contract."""
    results: list[dict] = []
    seen_content: set[str] = set()
    for node_rank, node in enumerate(_retrieved_nodes(payload), start=1):
        node_id = str(node.get("node_id") or node.get("id") or node_rank)
        title = str(node.get("title") or node.get("name") or source)
        node_score = node.get("score")
        contents = node.get("relevant_contents") or node.get("contents") or []
        if isinstance(contents, (str, dict)):
            contents = [contents]
        for content_rank, item in enumerate(contents):
            item_dict = item if isinstance(item, dict) else {}
            text = (
                item_dict.get("relevant_content")
                or item_dict.get("content")
                or item_dict.get("text")
                or (item if isinstance(item, str) else "")
            )
            text = str(text).strip()
            if not text or text in seen_content:
                continue
            seen_content.add(text)
            raw_score = item_dict.get("score", node_score)
            try:
                score = float(raw_score)
            except (TypeError, ValueError):
                score = 1.0 / (node_rank + content_rank)
            raw_page = item_dict.get("page_index", item_dict.get("page", node_rank - 1))
            try:
                chunk_index = int(raw_page)
            except (TypeError, ValueError):
                chunk_index = node_rank - 1
            results.append(
                {
                    "id": f"pageindex::{doc_id}::{node_id}::{content_rank}",
                    "content": text,
                    "score": score,
                    "metadata": {
                        "source": source,
                        "title": title,
                        "doc_type": "legal",
                        "url": None,
                        "chunk_index": chunk_index,
                    },
                    "retrieval_method": "pageindex",
                }
            )
    return sorted(results, key=lambda result: result["score"], reverse=True)


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """Return PageIndex results; degrade to an empty list when unavailable."""
    if not query.strip() or top_k <= 0 or not PAGEINDEX_API_KEY:
        return []
    cache = _load_cache()
    entries = cache.get("documents", {})
    if not isinstance(entries, dict) or not entries:
        return []

    results: list[dict] = []
    for filename, entry in entries.items():
        if not isinstance(entry, dict):
            continue
        doc_id = str(entry.get("doc_id", "")).strip()
        if not doc_id:
            continue
        source = str(entry.get("source") or filename)
        try:
            payload = _query_document(doc_id, query)
            results.extend(_parse_retrieval(payload, doc_id=doc_id, source=source))
        except (requests.RequestException, RuntimeError, TimeoutError, ValueError):
            continue

    unique: list[dict] = []
    seen_ids: set[str] = set()
    for result in sorted(results, key=lambda item: item["score"], reverse=True):
        if result["id"] in seen_ids:
            continue
        seen_ids.add(result["id"])
        unique.append(result)
        if len(unique) >= top_k:
            break
    return unique


if __name__ == "__main__":
    upload_documents()
