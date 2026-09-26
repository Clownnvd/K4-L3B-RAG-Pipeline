# TEAMMATES — K4-L3B RAG Pipeline

| Thành viên | Mã học viên | Vai trò | Branch/phần việc | Bằng chứng hiện tại |
|---|---|---|---|---|
| Nguyễn Văn Duy | 2A202602729 | Integration & Evaluation | Data contracts, retrieval/query planning, generation safety, A/B evaluation và tích hợp demo | Commit `2bc2287`; `src/`, `scripts/evaluate_pipeline.py`, `group_project/evaluation/`, báo cáo cá nhân |
| Dương Thị Ngân | 2A2026022808 | Data & Provenance | Rà 3 legal + 8 news; đối chiếu URL, metadata, checksum, chuẩn hóa Markdown và acceptance test | Commit `7471c0b`; nhánh `ngan/data-provenance-lab8`; pull request đã hợp nhất và báo cáo cá nhân |

## Quy tắc nghiệm thu nội bộ

- Chỉ đánh dấu hoàn thành khi có file, commit, test hoặc kết quả evaluation đối chiếu được.
- Câu hỏi về người có tên thật cần ít nhất hai nguồn tin độc lập.
- Không dùng RRF score để quyết định fallback.
- Không commit `.env`, API key hoặc Chroma cache.
