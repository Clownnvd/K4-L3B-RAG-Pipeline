# Individual contribution report — Dương Thị Ngân

## Thông tin

- Họ và tên: Dương Thị Ngân
- Mã học viên: 2A2026022808
- Nhóm: K4-L3B
- Vai trò được giao: Data & Provenance

## Trạng thái

Đã được giao phần Data & Provenance trên bộ dữ liệu nền hiện có. Ngân chịu trách nhiệm kiểm tra lại tính truy xuất nguồn và khả năng tái tạo dữ liệu; chỉ chuyển trạng thái sang hoàn thành sau khi có checklist và commit riêng.

## Phạm vi được giao

| Hạng mục | Việc cần thực hiện | File/bằng chứng đầu ra |
|---|---|---|
| Legal corpus | Mở và đối chiếu 3 văn bản pháp luật với nguồn trong manifest; kiểm tra tên, kích thước và checksum | `data/landing/legal/manifest.json`, `data/sources.csv` |
| News corpus | Kiểm tra 8 JSON có đủ `url`, `title`, `date_crawled`, `content_markdown`; mở URL mẫu để đối chiếu nội dung | `data/landing/news/*.json`, `data/landing/web_manifest.json` |
| Chuẩn hóa | Chạy lại Task 3 và so sánh Markdown với nguồn landing; xác nhận không mất tiêu đề hoặc URL | `data/standardized/legal/`, `data/standardized/news/` |
| Kiểm thử dữ liệu | Chạy acceptance test và lưu kết quả pass | `python -m pytest tests/test_acceptance.py -q` |
| Nhật ký lỗi | Ghi ít nhất một lỗi hoặc rủi ro dữ liệu đã phát hiện, cách xử lý và file liên quan | Bổ sung vào báo cáo này |

## Bằng chứng cần bổ sung trước khi nộp

- Commit/PR của Ngân cho phần kiểm tra nguồn và `data/sources.csv`.
- Checklist đối chiếu đủ 3 legal và ít nhất 5/8 news; kiểm tra sâu tối thiểu 3 file Markdown với nguồn gốc.
- Log `tests/test_acceptance.py` pass sau lượt kiểm tra của Ngân.
- Một lỗi hoặc rủi ro dữ liệu đã phát hiện, kèm cách xử lý.

## Tiêu chí hoàn thành

- Không có URL nguồn trống hoặc metadata bắt buộc bị thiếu.
- Checksum/file nguồn khớp manifest hiện hành.
- Markdown chuẩn hóa giữ được tiêu đề, URL và nội dung có thể đối chiếu.
- Acceptance test pass và không commit `.env`, API key hoặc cache.
