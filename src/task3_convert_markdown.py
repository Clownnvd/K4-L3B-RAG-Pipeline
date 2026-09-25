"""Task 3 — Normalize law, news and card-product sources to Markdown."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).parent.parent
LANDING_DIR = ROOT / "data" / "landing"
OUTPUT_DIR = ROOT / "data" / "standardized"
SOURCES_CSV = ROOT / "data" / "sources.csv"

LEGAL_TEXT_FALLBACKS = {
    "nghi-dinh-144-2021-xu-phat-an-ninh-trat-tu.pdf": """
## Trích Điều 23. Vi phạm các quy định về phòng, chống và kiểm soát ma túy

### Khoản 1 — Hành vi sử dụng trái phép chất ma túy

Phạt cảnh cáo hoặc phạt tiền từ 1.000.000 đồng đến 2.000.000 đồng đối với hành vi sử dụng trái phép chất ma túy.

### Khoản 2 — Hành vi liên quan nhưng chưa đến mức truy cứu trách nhiệm hình sự

Phạt tiền từ 2.000.000 đồng đến 5.000.000 đồng đối với hành vi tàng trữ, vận chuyển trái phép hoặc chiếm đoạt chất ma túy nhưng không bị truy cứu trách nhiệm hình sự; các hành vi liên quan đến tiền chất và phương tiện, dụng cụ dùng vào việc sản xuất hoặc sử dụng trái phép chất ma túy theo quy định tại khoản này.

### Khoản 4 và khoản 5 — Trách nhiệm của người quản lý, hành vi giúp sức và cung cấp địa điểm

Nghị định quy định mức phạt cao hơn đối với người có trách nhiệm quản lý cơ sở hoặc phương tiện nhưng để xảy ra hoạt động tàng trữ, mua bán, sử dụng trái phép chất ma túy; hành vi môi giới, giúp sức; và hành vi cung cấp địa điểm, phương tiện cho người khác sử dụng, tàng trữ hoặc mua bán trái phép chất ma túy.

**Lưu ý phạm vi:** Đây là trích đoạn phục vụ truy xuất câu hỏi về hành vi sử dụng trái phép chất ma túy. Khi xác định trách nhiệm cụ thể cần đọc toàn văn Nghị định và đối chiếu tình tiết, chứng cứ cùng quyết định của cơ quan có thẩm quyền.
""".strip(),
}


def _frontmatter(metadata: dict) -> str:
    lines = ["---"]
    for key, value in metadata.items():
        lines.append(f"{key}: {json.dumps(value, ensure_ascii=False)}")
    lines.extend(["---", ""])
    return "\n".join(lines)


def _clean_extracted_text(text: str) -> str:
    text = text.replace("\x00", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _clean_web_markdown(text: str) -> str:
    """Drop recommendation/navigation blocks that look like factual evidence."""
    blocks = [block.strip() for block in re.split(r"\n{2,}", text) if block.strip()]
    while blocks and blocks[-1].lstrip().startswith("### "):
        blocks.pop()
    cleaned = []
    for block in blocks:
        normalized = block.lstrip("#- ").strip().casefold()
        if normalized.startswith(("tham khảo thêm", "xem thêm", "tin liên quan", "đọc thêm")):
            continue
        cleaned.append(block.strip())
    return "\n\n".join(block for block in cleaned if block)


def convert_legal_docs() -> list[dict]:
    legal_dir = LANDING_DIR / "legal"
    output_dir = OUTPUT_DIR / "legal"
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = legal_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    by_name = {item["filename"]: item for item in manifest}
    records = []
    for path in sorted(legal_dir.glob("*.pdf")):
        source = by_name[path.name]
        reader = PdfReader(str(path))
        pages = []
        for index, page in enumerate(reader.pages, 1):
            page_text = _clean_extracted_text(page.extract_text() or "")
            if page_text:
                pages.append(f"## Trang {index}\n\n{page_text}")
        content = "\n\n".join(pages)
        extraction_method = "pypdf"
        if len(content) < 500:
            content = LEGAL_TEXT_FALLBACKS.get(path.name, "")
            extraction_method = "curated_official_excerpt"
        if len(content) < 500:
            raise ValueError(f"PDF extraction too short and no fallback: {path.name}")
        metadata = {
            "title": source["title"], "source": path.name,
            "url": source["source_page"], "download_url": source["url"],
            "doc_type": "legal", "knowledge_base": "law",
            "authority": source["authority"], "issued_date": source["issued_date"],
            "effective_date": source["effective_date"], "sha256": source["sha256"],
            "extraction_method": extraction_method,
        }
        output = output_dir / f"{path.stem}.md"
        output.write_text(
            _frontmatter(metadata) + f"# {source['title']}\n\n" + content,
            encoding="utf-8",
        )
        records.append({**metadata, "standardized_file": str(output.relative_to(ROOT))})
        print(f"Standardized: {output.name} ({len(reader.pages)} pages)")
    return records


def _convert_web_knowledge_base(knowledge_base: str) -> list[dict]:
    input_dir = LANDING_DIR / knowledge_base
    output_dir = OUTPUT_DIR / knowledge_base
    output_dir.mkdir(parents=True, exist_ok=True)
    records = []
    for path in sorted(input_dir.glob("*.json")):
        item = json.loads(path.read_text(encoding="utf-8"))
        metadata = {
            "title": item["title"], "source": path.name, "url": item["url"],
            "doc_type": item["doc_type"], "knowledge_base": item["knowledge_base"],
            "source_domain": item["source_domain"], "date_crawled": item["date_crawled"],
            "source_tier": item.get("source_tier", "public_source"),
            "claim_status": item.get("claim_status", "not_applicable"),
            "sha256": item["content_sha256"],
        }
        output = output_dir / f"{path.stem}.md"
        content = _clean_web_markdown(item["content_markdown"])
        output.write_text(
            _frontmatter(metadata) + f"# {item['title']}\n\n" + content + "\n",
            encoding="utf-8",
        )
        records.append({**metadata, "standardized_file": str(output.relative_to(ROOT))})
        print(f"Standardized: {output.relative_to(ROOT)}")
    return records


def convert_news_articles() -> list[dict]:
    return _convert_web_knowledge_base("news")


def convert_card_products() -> list[dict]:
    return _convert_web_knowledge_base("cards")


def _write_sources_csv(records: list[dict]) -> None:
    fields = [
        "knowledge_base", "doc_type", "title", "url", "download_url",
        "source", "source_domain", "authority", "issued_date",
        "effective_date", "date_crawled", "source_tier", "claim_status",
        "extraction_method", "sha256", "standardized_file",
    ]
    SOURCES_CSV.parent.mkdir(parents=True, exist_ok=True)
    with SOURCES_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for record in records:
            writer.writerow({field: record.get(field, "") for field in fields})


def convert_all() -> list[dict]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    records = convert_legal_docs() + convert_news_articles() + convert_card_products()
    _write_sources_csv(records)
    print(f"Saved {len(records)} standardized sources; manifest: {SOURCES_CSV}")
    return records


if __name__ == "__main__":
    convert_all()
