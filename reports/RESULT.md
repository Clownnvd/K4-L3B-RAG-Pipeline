# Evaluation result — bản chỉ dẫn

Báo cáo đánh giá chính thức của nhóm nằm tại
[`group_project/evaluation/RESULT.md`](../group_project/evaluation/RESULT.md).
File này được giữ lại để tránh nhầm với template cũ của starter repository.

## Kết quả chính

| Metric | Dense-only | Hybrid + RRF | Chênh lệch |
|---|---:|---:|---:|
| Faithfulness | 1.000 | 1.000 | +0.000 |
| Answer relevance | 0.474 | 0.493 | +0.018 |
| Context recall | 0.500 | 1.000 | +0.500 |
| Context precision | 0.343 | 0.630 | +0.287 |

Các giả định, worst performers, nguyên nhân lỗi và khuyến nghị được ghi đầy đủ trong
báo cáo chính thức nêu trên. Không chỉnh số liệu tại file chỉ dẫn này; hãy chạy lại
`python scripts/evaluate_pipeline.py` rồi cập nhật báo cáo chính thức nếu corpus hoặc
retrieval strategy thay đổi.
