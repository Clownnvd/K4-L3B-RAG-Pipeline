# TEAMMATES — K4-L3B RAG Pipeline

| Thành viên | Mã học viên | Vai trò | Branch/phần việc | Bằng chứng hiện tại |
|---|---|---|---|---|
| Nguyễn Văn Duy | 2A202602729 | Integration & Evaluation | `main-l3b`; data contracts, query planning, generation safety, A/B | `src/`, `scripts/evaluate_pipeline.py`, `group_project/evaluation/` |
| Dương Thị Ngân | 2A2026022808 | Data & Provenance | Rà 3 legal + 8 news; đối chiếu URL, metadata, checksum và `sources.csv`; chạy lại chuẩn hóa + acceptance test | Đã có dữ liệu nền; Ngân cần xác nhận bằng checklist và commit riêng trước khi nộp |
| Lục Tiến Đạt | 2A202602969 | Retrieval | Chunking, Dense/BM25/RRF, threshold calibration | Đã phân công; bổ sung commit cá nhân trước khi nộp |
| Nguyễn Thanh Bình | 2A202602777 | Generation & UI | Citation mapping, safe refusal, Streamlit demo | Đã phân công; bổ sung commit cá nhân trước khi nộp |

## Quy tắc nghiệm thu nội bộ

- Chỉ đánh dấu hoàn thành khi có file, commit, test hoặc kết quả evaluation đối chiếu được.
- Câu hỏi về người có tên thật cần ít nhất hai nguồn tin độc lập.
- Không dùng RRF score để quyết định fallback.
- Không commit `.env`, API key hoặc Chroma cache.
