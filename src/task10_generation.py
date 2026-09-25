"""Task 10 — Source-grounded generation with conservative claim handling."""

from __future__ import annotations

import os
import re
import unicodedata
from copy import deepcopy

from dotenv import load_dotenv

from .task9_retrieval_pipeline import _aggregation_numbers, retrieve


load_dotenv()

TOP_K = 6
TOP_P = 0.9
TEMPERATURE = 0.15

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").casefold()
LLM_MODEL = os.getenv("LLM_MODEL", "")

SAFE_REFUSAL = (
    "Tôi chưa thể xác minh câu hỏi này từ các nguồn hiện có. "
    "Vui lòng hỏi trong phạm vi corpus hoặc cung cấp thêm nguồn đáng tin cậy."
)

SYSTEM_PROMPT = """Bạn là trợ lý hỏi đáp về tin tức và pháp luật ma túy tại Việt Nam.
Chỉ sử dụng EVIDENCE được cung cấp; không dùng trí nhớ để thêm tình tiết.
Mọi khẳng định thực tế và pháp lý phải có citation dạng [S1], [S2].
Giữ đúng mức độ chắc chắn của nguồn: nghi vấn, đang điều tra, bị khởi tố và bị kết án là các trạng thái khác nhau.
Với người có tên thật, chỉ khẳng định sự kiện khi có ít nhất hai nguồn tin độc lập trong context.
Phân biệt sử dụng, tàng trữ, mua bán và tổ chức sử dụng trái phép chất ma túy.
Không tự động gọi hành vi sử dụng là tội hình sự. Nêu xử phạt hành chính khi evidence hỗ trợ; đồng thời kiểm tra Điều 256a Bộ luật Hình sự cho các trường hợp sử dụng đặc biệt trong thời hạn cai nghiện/quản lý nếu context có căn cứ.
Điều 255 là tội tổ chức sử dụng trái phép chất ma túy, không đồng nhất với hành vi một người tự sử dụng.
Nếu evidence thiếu hoặc mâu thuẫn, nói rõ phần chưa xác minh thay vì đoán.
Khi nhiều vụ có cùng con số, phải gắn mỗi số với đúng tiêu đề, địa điểm và nguồn; không biến số người thuộc một nhóm con thành tên của toàn bộ vụ án.
Kết thúc bằng câu: “Thông tin pháp lý chỉ mang tính tham khảo.”"""


def reorder_for_llm(chunks: list[dict]) -> list[dict]:
    """Place high-ranked evidence at both edges without mutating input."""
    copied = [deepcopy(chunk) for chunk in chunks]
    if len(copied) <= 2:
        return copied
    reordered: list[dict] = []
    left = copied[::2]
    right = copied[1::2][::-1]
    for index in range(max(len(left), len(right))):
        if index < len(left):
            reordered.append(left[index])
        if index < len(right):
            reordered.append(right[index])
    return reordered


def format_context(chunks: list[dict]) -> str:
    """Create source-labelled context whose citations map to SearchResults."""
    parts = []
    for index, chunk in enumerate(chunks, 1):
        metadata = chunk["metadata"]
        citation_id = metadata.get("citation_id", f"S{index}")
        parts.append(
            "\n".join(
                [
                    f"[{citation_id}]",
                    f"Title: {metadata['title']}",
                    f"Source: {metadata['source']}",
                    f"URL: {metadata.get('url') or 'N/A'}",
                    f"Knowledge base: {metadata.get('knowledge_base', 'unknown')}",
                    f"Claim status: {metadata.get('claim_status', 'not_applicable')}",
                    f"Content:\n{chunk['content']}",
                ]
            )
        )
    return "\n\n---\n\n".join(parts)


def call_llm(system_prompt: str, user_message: str) -> str:
    """Dispatch to Gemini, OpenAI or Anthropic and return plain text."""
    if LLM_PROVIDER == "gemini":
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured")
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=LLM_MODEL or "gemini-2.5-flash",
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=TEMPERATURE,
                top_p=TOP_P,
            ),
        )
        return response.text or ""
    if LLM_PROVIDER == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured")
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=LLM_MODEL or "gpt-4.1-mini",
            temperature=TEMPERATURE,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
        )
        return response.choices[0].message.content or ""
    if LLM_PROVIDER == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not configured")
        from anthropic import Anthropic

        client = Anthropic(api_key=api_key)
        response = client.messages.create(
            model=LLM_MODEL or "claude-sonnet-4-5",
            max_tokens=1200,
            temperature=TEMPERATURE,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        return "".join(block.text for block in response.content if hasattr(block, "text"))
    raise ValueError(f"Unsupported LLM_PROVIDER: {LLM_PROVIDER}")


def _significant_tokens(text: str) -> set[str]:
    text = _ascii_fold(text).replace("mai thuy", "ma tuy")
    stop = {"va", "la", "co", "dau", "nao", "gi", "cho", "cua", "mot", "nhung"}
    return {
        token for token in re.findall(r"\w+", text, flags=re.UNICODE)
        if len(token) >= 3 and token not in stop
    }


def _ascii_fold(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text.casefold())
    return "".join(char for char in normalized if unicodedata.category(char) != "Mn").replace("đ", "d")


def _is_domain_query(query: str) -> bool:
    folded = _ascii_fold(query).replace("mai thuy", "ma tuy")
    domain_terms = (
        "ma tuy", "chat cam", "miu le", "le anh nhat", "methamphetamine",
        "ketamine", "mdma", "cai nghien", "tang tru", "to chuc su dung",
        "mua ban", "nghi dinh 144", "dieu 249", "dieu 255", "dieu 256a",
        "phong chong ma tuy", "bai tam tung thu", "bay hien",
        "48 doi tuong", "53 doi tuong", "65 doi tuong", "vien phap y tam than",
    )
    return any(term in folded for term in domain_terms)


def _has_unresolved_reference(query: str) -> bool:
    folded = _ascii_fold(query)
    pronouns = ("co ay", "anh ay", "nguoi do", "vu do", "o do", "ho co")
    has_reference = any(pronoun in folded for pronoun in pronouns)
    has_named_entity = any(name in folded for name in ("miu le", "le anh nhat", "le duy linh", "tang nhat tue"))
    return has_reference and not has_named_entity


def _has_enough_evidence(query: str, chunks: list[dict]) -> bool:
    if not chunks:
        return False
    query_tokens = _significant_tokens(query)
    context_tokens = _significant_tokens(" ".join(chunk["content"] for chunk in chunks))
    if not query_tokens or len(query_tokens & context_tokens) < min(2, len(query_tokens)):
        return False
    if "miu lê" in query.casefold() or "lê ánh nhật" in query.casefold():
        news_sources = {
            chunk["metadata"].get("source")
            for chunk in chunks
            if chunk["metadata"].get("knowledge_base") == "news"
            and ("miu lê" in chunk["content"].casefold() or "lê ánh nhật" in chunk["content"].casefold())
        }
        return len(news_sources) >= 2
    return True


def _extractive_fallback(query: str, chunks: list[dict]) -> str:
    query_tokens = _significant_tokens(query)
    bullets = []
    for index, chunk in enumerate(chunks, 1):
        citation_id = chunk["metadata"].get("citation_id", f"S{index}")
        sentences = re.split(r"(?<=[.!?])\s+|\n+", chunk["content"])
        ranked = sorted(
            (sentence.strip() for sentence in sentences if len(sentence.strip()) >= 40),
            key=lambda sentence: len(_significant_tokens(sentence) & query_tokens),
            reverse=True,
        )
        if ranked:
            bullets.append(f"- {ranked[0]} [{citation_id}]")
        if len(bullets) >= 4:
            break
    if not bullets:
        return SAFE_REFUSAL
    return (
        "Các căn cứ truy xuất được:\n" + "\n".join(bullets)
        + "\n\nCần đối chiếu tình tiết cụ thể trước khi kết luận trách nhiệm pháp lý. "
        "Thông tin pháp lý chỉ mang tính tham khảo."
    )


def generate_with_citation(query: str, top_k: int = TOP_K) -> dict:
    """Retrieve evidence, generate a cited answer, or abstain safely."""
    if not _is_domain_query(query):
        return {"answer": SAFE_REFUSAL, "sources": [], "retrieval_source": "none"}
    if _has_unresolved_reference(query):
        return {
            "answer": "Tôi chưa thể xác định đại từ trong câu hỏi đang chỉ ai hoặc vụ việc nào. Vui lòng nêu rõ tên người hoặc vụ việc cần kiểm tra.",
            "sources": [],
            "retrieval_source": "none",
        }
    chunks = retrieve(query, top_k=top_k)
    if not _has_enough_evidence(query, chunks):
        return {"answer": SAFE_REFUSAL, "sources": [], "retrieval_source": "none"}
    labeled_chunks = []
    for index, chunk in enumerate(chunks, 1):
        labeled = deepcopy(chunk)
        labeled["metadata"] = {**labeled["metadata"], "citation_id": f"S{index}"}
        labeled_chunks.append(labeled)
    reordered = reorder_for_llm(labeled_chunks)
    context = format_context(reordered)
    special_instruction = ""
    ambiguity_appendix = ""
    aggregation_numbers = _aggregation_numbers(query)
    if aggregation_numbers:
        duplicate_notes = []
        for number in aggregation_numbers:
            matches = [
                f"[{chunk['metadata']['citation_id']}] {chunk['metadata']['title']}"
                for chunk in labeled_chunks
                if number in chunk["metadata"]["title"]
            ]
            if len(matches) > 1:
                duplicate_notes.append(
                    f"Con số {number} xuất hiện trong {len(matches)} vụ riêng: " + " | ".join(matches)
                )
        duplicate_text = "\n".join(duplicate_notes)
        if duplicate_notes:
            ambiguity_appendix = (
                "\n\n**Lưu ý mơ hồ trong corpus:** "
                + " ".join(duplicate_notes)
                + ". Đây là các vụ riêng, không được ghép tình tiết."
            )
        special_instruction = (
            "\nSPECIAL INSTRUCTION: Nếu cùng một con số xuất hiện trong nhiều tiêu đề nguồn, "
            "đó là các vụ khác nhau. Hãy nêu rõ câu hỏi đang mơ hồ, tách từng vụ theo tiêu đề/địa điểm "
            "và tuyệt đối không ghép tình tiết của hai nguồn thành một vụ. Không được cite hai vụ trong cùng một bullet.\n"
            + duplicate_text
            + "\n"
        )
    user_message = f"EVIDENCE:\n{context}{special_instruction}\nQUESTION: {query}"
    try:
        answer = call_llm(SYSTEM_PROMPT, user_message).strip()
    except Exception:
        answer = _extractive_fallback(query, reordered)
    if not answer or "[S" not in answer:
        answer = _extractive_fallback(query, reordered)
    if ambiguity_appendix:
        cited_ids = set(re.findall(r"\[(S\d+)\]", answer))
        required_ids = set(re.findall(r"\[(S\d+)\]", ambiguity_appendix))
        if not required_ids <= cited_ids:
            answer += ambiguity_appendix
    retrieval_method = chunks[0]["retrieval_method"]
    retrieval_source = retrieval_method if retrieval_method in {"hybrid", "pageindex"} else "hybrid"
    return {"answer": answer, "sources": labeled_chunks, "retrieval_source": retrieval_source}


if __name__ == "__main__":
    print(generate_with_citation("Miu Lê sử dụng ma túy ở đâu và vi phạm quy định nào?"))
