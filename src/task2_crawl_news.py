"""Task 2 — Crawl public reporting about drug cases and drug-law guidance."""

from __future__ import annotations

import asyncio
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


ROOT = Path(__file__).parent.parent
LANDING_DIR = ROOT / "data" / "landing"

ARTICLE_URLS = [
    "https://vnexpress.net/20-nam-hoat-dong-cua-miu-le-truoc-khi-bi-bat-qua-tang-dung-ma-tuy-5072922.html",
    "https://thanhnien.vn/cuoc-song-cua-miu-le-truoc-khi-bi-dieu-tra-lien-quan-den-ma-tuy-185260512025301291.htm",
    "https://vtv.vn/miu-le-truoc-khi-bi-bat-qua-tang-su-dung-ma-tuy-100260512123207532.htm",
    "https://baochinhphu.vn/xu-ly-nghiem-48-doi-tuong-mua-ban-to-chuc-su-dung-va-tang-tru-trai-phep-chat-ma-tuy-102260703085404331.htm",
    "https://baochinhphu.vn/truy-to-65-bi-can-trong-vu-dai-an-xay-ra-tai-vien-phap-y-tam-than-trung-uong-102260805113852704.htm",
    "https://vtv.vn/triet-pha-duong-day-ma-tuy-xuyen-bien-gioi-bat-giu-65-doi-tuong-10kg-chat-cam-100260626210515558.htm",
    "https://vtv.vn/chuyen-an-0526m-bat-giu-53-doi-tuong-lien-quan-den-ma-tuy-tai-phuong-bay-hien-100260617150637534.htm",
    "https://baochinhphu.vn/huong-dan-ap-dung-mot-so-quy-dinh-cua-bo-luat-hinh-su-ve-cac-toi-pham-ma-tuy-102231006155917048.htm",
]

CARD_URLS: list[str] = []

CLAIM_STATUS_BY_URL = {
    ARTICLE_URLS[0]: "reported_by_media_as_caught",
    ARTICLE_URLS[1]: "reported_as_under_investigation",
    ARTICLE_URLS[2]: "reported_by_media_as_caught",
}

NOISE_SELECTORS = [
    "script", "style", "noscript", "svg", "nav", "footer", "header", "form",
    ".breadcrumb", ".breadcrumbs", ".related", ".social", ".share", ".advertisement",
]


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _html_to_markdown(html: str) -> tuple[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    for selector in NOISE_SELECTORS:
        for node in soup.select(selector):
            node.decompose()
    title_node = soup.select_one('meta[property="og:title"]')
    title = title_node.get("content", "") if title_node else ""
    if not title:
        heading = soup.find("h1")
        title = heading.get_text(" ", strip=True) if heading else ""
    if not title and soup.title:
        title = soup.title.get_text(" ", strip=True)
    title = _clean_text(title) or "Untitled source"

    root = soup.find("article") or soup.find("main") or soup.body or soup
    blocks: list[str] = []
    seen: set[str] = set()
    for node in root.find_all(["h1", "h2", "h3", "p", "li", "table"]):
        text = _clean_text(node.get_text(" ", strip=True))
        if len(text) < 20 or text in seen:
            continue
        if text.casefold().startswith(("tham khảo thêm", "xem thêm", "tin liên quan", "đọc thêm")):
            continue
        seen.add(text)
        if node.name in {"h1", "h2", "h3"}:
            blocks.append(f"{'#' * int(node.name[1])} {text}")
        elif node.name == "li":
            blocks.append(f"- {text}")
        else:
            blocks.append(text)
    markdown = "\n\n".join(blocks)
    if len(markdown) < 400:
        raise ValueError("Extracted content is too short")
    return title, markdown


def _crawl_sync(url: str, knowledge_base: str) -> dict:
    response = requests.get(
        url,
        timeout=(15, 60),
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; AI20K-Day08-RAG-Lab/1.0)",
            "Accept-Language": "vi,en;q=0.8",
        },
    )
    response.raise_for_status()
    response.encoding = response.apparent_encoding or response.encoding
    title, markdown = _html_to_markdown(response.text)
    return {
        "url": url,
        "title": title,
        "date_crawled": datetime.now(timezone.utc).isoformat(),
        "content_markdown": markdown,
        "knowledge_base": knowledge_base,
        "doc_type": "news" if knowledge_base == "news" else "card",
        "source_domain": urlparse(url).netloc.lower(),
        "source_tier": (
            "government_or_public_broadcaster"
            if urlparse(url).netloc.lower() in {"baochinhphu.vn", "vtv.vn"}
            else "major_news_outlet"
        ),
        "claim_status": CLAIM_STATUS_BY_URL.get(url, "official_case_report"),
        "content_sha256": hashlib.sha256(markdown.encode("utf-8")).hexdigest(),
    }


async def crawl_article(url: str, knowledge_base: str = "news") -> dict:
    """Crawl a public page without bypassing authentication or anti-bot controls."""
    return await asyncio.to_thread(_crawl_sync, url, knowledge_base)


async def _crawl_collection(urls: list[str], knowledge_base: str) -> list[dict]:
    output_dir = LANDING_DIR / knowledge_base
    output_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict] = []
    for index, url in enumerate(urls, 1):
        try:
            item = await crawl_article(url, knowledge_base)
            output = output_dir / f"{knowledge_base}_{index:02d}.json"
            output.write_text(
                json.dumps(item, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            records.append(item)
            print(f"Saved: {output.name} — {item['title']}")
        except Exception as error:
            print(f"Failed: {url} — {error}")
    return records


async def crawl_all() -> dict[str, list[dict]]:
    news = await _crawl_collection(ARTICLE_URLS, "news")
    cards = await _crawl_collection(CARD_URLS, "cards")
    summary = {"news": news, "cards": cards}
    manifest = LANDING_DIR / "web_manifest.json"
    manifest.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Manifest: {manifest}")
    return summary


if __name__ == "__main__":
    asyncio.run(crawl_all())
