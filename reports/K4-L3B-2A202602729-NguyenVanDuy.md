# Individual contribution report — Nguyễn Văn Duy

## Thông tin

- Họ và tên: Nguyễn Văn Duy
- Mã học viên: 2A202602729
- Nhóm: K4-L3B
- Repository/branch: `K4-L3B-RAG-Pipeline` / `duy/lab08-submission`

## Phần việc đã thực hiện

| Module/deliverable | Việc trực tiếp làm | File/bằng chứng | Trạng thái |
|---|---|---|---|
| Data pipeline | Chọn chủ đề ma túy, nguồn chính thức, crawl có checksum, chuẩn hóa 3 legal + 8 news | `src/task1_*`, `task2_*`, `task3_*`, `data/sources.csv` | Done |
| Retrieval | Markdown-aware chunking, multilingual dense, BM25, RRF, query routing News/Law | `src/task4_*` đến `task9_*` | Done |
| Safety & generation | Citation mapping, hai nguồn cho người có tên thật, safe refusal | `src/task10_generation.py` | Done |
| Evaluation | 18 golden cases; A/B dense-only và hybrid | `scripts/evaluate_pipeline.py`, `group_project/evaluation/` | Done |
| UI | Giao diện Streamlit hiển thị nguồn, score và trạng thái claim | `app.py` | Done |

## Quyết định kỹ thuật quan trọng

1. **Tách câu hỏi nhiều bước thành event subquery và law subquery.**  
   **Lý do/evidence:** Dense-only context recall đạt 0.500; cấu hình hybrid có routing đạt 1.000 trên cùng 18 case.  
   **Trade-off:** Latency retrieval tăng khoảng 17 ms trung bình trong baseline cục bộ.

2. **Không tự động coi sử dụng trái phép chất ma túy là tội hình sự.**  
   **Lý do/evidence:** Nghị định 144 quy định xử phạt hành chính; trách nhiệm hình sự cần hành vi và yếu tố cấu thành khác.  
   **Trade-off:** Câu trả lời thận trọng hơn và có thể dài hơn.

## Kiểm thử và kết quả

- `pytest -q`: 29 passed.
- Context recall: 0.500 → 1.000.
- Context precision: 0.343 → 0.630.
- Câu Miu Lê lấy ba nguồn tin và ba nguồn luật, không kết luận tội danh khi nguồn chưa xác nhận khởi tố.

## Điều còn hạn chế

- Evaluation hiện dùng metric proxy cục bộ; cần thêm lượt LLM judge có ghi model/version.
- Nếu có thêm thời gian, thay đổi đầu tiên là thử cross-encoder reranker và chỉ giữ khi A/B tăng precision mà không giảm recall.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể chạy lại trong buổi demo.

- Ngày: 21/09/2026
- Tên thành viên: Nguyễn Văn Duy
