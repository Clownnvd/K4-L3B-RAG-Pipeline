"""Streamlit interface for the Vietnamese drug-news and law RAG system."""

import streamlit as st
from dotenv import load_dotenv

from src.task10_generation import generate_with_citation


load_dotenv()

st.set_page_config(page_title="DrugLaw RAG", page_icon="⚖️", layout="wide")

st.markdown(
    """
    <style>
    .block-container {max-width: none; padding-top: 1.5rem;}
    [data-testid="stSidebar"] {border-right: 1px solid #dbe4ef;}
    .source-card {padding: .85rem 1rem; border: 1px solid #dbe4ef; border-radius: .8rem; margin: .45rem 0;}
    .source-meta {color: #64748b; font-size: .82rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.title("⚖️ DrugLaw RAG")
    st.caption("Tin tức ma túy ↔ văn bản pháp luật Việt Nam")
    top_k = st.slider("Số đoạn căn cứ", 3, 10, 6)
    st.divider()
    st.markdown("**Kho tri thức**")
    st.markdown("- 📰 Tin tức vụ việc\n- ⚖️ Luật và nghị định\n- 🔎 Hybrid: Dense + BM25 + RRF")
    st.info("Hệ thống giữ nguyên trạng thái nguồn như “nghi”, “đang điều tra”, “khởi tố”; không tự kết luận tội danh.")

st.title("Hỏi đáp tin tức và pháp luật về ma túy")
st.caption("Câu trả lời chỉ dựa trên corpus đã kiểm chứng và luôn hiển thị nguồn dùng để trả lời.")

with st.expander("Câu hỏi gợi ý", expanded=False):
    st.markdown(
        "- Miu Lê được đưa về làm việc tại đâu và hành vi sử dụng trái phép chất ma túy bị xử lý thế nào?\n"
        "- Phân biệt sử dụng, tàng trữ và tổ chức sử dụng trái phép chất ma túy.\n"
        "- Vụ án tại Viện Pháp y tâm thần liên quan những tội danh ma túy nào?"
    )


def render_sources(sources: list[dict]) -> None:
    if not sources:
        return
    st.markdown("#### Nguồn đã dùng")
    for index, source in enumerate(sources, 1):
        metadata = source["metadata"]
        label = metadata.get("citation_id", f"S{index}")
        with st.expander(f"[{label}] {metadata['title']}"):
            st.markdown(
                f"**Kho:** `{metadata.get('knowledge_base', 'unknown')}` · "
                f"**Phương pháp:** `{source['retrieval_method']}` · "
                f"**Điểm:** `{source['score']:.4f}`"
            )
            if metadata.get("claim_status") not in {None, "", "not_applicable"}:
                st.caption(f"Trạng thái khẳng định của nguồn: {metadata['claim_status']}")
            if metadata.get("url"):
                st.link_button("Mở nguồn gốc", metadata["url"])
            st.markdown(source["content"])


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            render_sources(message.get("sources", []))

query = st.chat_input("Nhập câu hỏi về vụ việc, địa điểm, hành vi hoặc quy định pháp luật…")

if query:
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)
    with st.chat_message("assistant"):
        with st.spinner("Đang tìm trong News và Law, sau đó kiểm tra căn cứ…"):
            result = generate_with_citation(query, top_k)
        st.markdown(result["answer"])
        render_sources(result["sources"])
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": result["answer"],
            "sources": result["sources"],
        }
    )
