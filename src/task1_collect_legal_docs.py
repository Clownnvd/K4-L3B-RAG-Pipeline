"""Task 1 — Download authoritative Vietnamese legal documents."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import requests


ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data" / "landing" / "legal"
MANIFEST_PATH = DATA_DIR / "manifest.json"

LEGAL_DOCUMENTS = [
    {
        "filename": "luat-phong-chong-ma-tuy-vbhn-117-2025.pdf",
        "title": "Văn bản hợp nhất Luật Phòng, chống ma túy số 117/VBHN-VPQH",
        "url": "https://datafiles.chinhphu.vn/cpp/files/vbpq/2025/9/117-vbhn-vpqha.pdf",
        "source_page": "https://vanban.chinhphu.vn/?docid=215316&pageid=27160",
        "issued_date": "2025-08-27", "effective_date": None,
        "authority": "Văn phòng Quốc hội", "knowledge_base": "law",
    },
    {
        "filename": "bo-luat-hinh-su-vbhn-135-2025.pdf",
        "title": "Văn bản hợp nhất Bộ luật Hình sự số 135/VBHN-VPQH",
        "url": "https://datafiles.chinhphu.vn/cpp/files/vbpq/2025/9/135-vbhn-vpqh.pdf",
        "source_page": "https://vanban.chinhphu.vn/?docid=215260&pageid=27160",
        "issued_date": "2025-09-05", "effective_date": None,
        "authority": "Văn phòng Quốc hội", "knowledge_base": "law",
    },
    {
        "filename": "nghi-dinh-144-2021-xu-phat-an-ninh-trat-tu.pdf",
        "title": "Nghị định 144/2021/NĐ-CP về xử phạt hành chính an ninh, trật tự",
        "url": "https://datafiles.chinhphu.vn/cpp/files/vbpq/2022/01/144.signed.pdf",
        "source_page": "https://vanban.chinhphu.vn/?classid=1&docid=204979&pageid=27160&typegroupid=4",
        "issued_date": "2021-12-31", "effective_date": "2022-01-01",
        "authority": "Chính phủ", "knowledge_base": "law",
    },
]


def setup_directory() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _download_pdf(item: dict, session: requests.Session) -> dict:
    target = DATA_DIR / item["filename"]
    response = session.get(item["url"], timeout=(15, 120))
    response.raise_for_status()
    content = response.content
    if not content.startswith(b"%PDF"):
        raise ValueError(f"Expected PDF from {item['url']}")
    if len(content) <= 1024:
        raise ValueError(f"Downloaded PDF is unexpectedly small: {item['url']}")
    target.write_bytes(content)
    return {
        **item,
        "bytes": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
        "downloaded_at": datetime.now(timezone.utc).isoformat(),
    }


def download_documents() -> list[dict]:
    """Download declared PDFs and write a reproducible provenance manifest."""
    setup_directory()
    session = requests.Session()
    session.headers.update({"User-Agent": "AI20K-Day08-RAG-Lab/1.0"})
    records = []
    for item in LEGAL_DOCUMENTS:
        record = _download_pdf(item, session)
        records.append(record)
        print(f"Saved: {record['filename']} ({record['bytes']:,} bytes)")
    MANIFEST_PATH.write_text(
        json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Manifest: {MANIFEST_PATH}")
    return records


if __name__ == "__main__":
    download_documents()
