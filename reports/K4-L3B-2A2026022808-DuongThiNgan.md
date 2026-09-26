# Individual contribution report — Dương Thị Ngân

## Thông tin

- Họ và tên: Dương Thị Ngân
- Mã học viên: 2A2026022808
- Nhóm: K4-L3B
- Vai trò: Data & Provenance
- Ngày kiểm tra: 25/09/2026
- Bản bàn giao được kiểm tra: `K4-L3B-Lab8-Duy-Ngan-20260925.zip`
- SHA-256 của ZIP: `c628e8eca4a3d9d815b43cb8b69b64d288723a7fc677cd06cc57f93b4f521eeb`

## Trạng thái

**Hoàn thành.** Phạm vi của Ngân chỉ gồm dữ liệu nguồn, provenance, chuẩn hóa Markdown và kiểm thử dữ liệu. Báo cáo này không nhận công phần retrieval, generation hoặc UI của thành viên khác.

## 1. Kiểm tra legal corpus

Đã mở được cả 3 PDF bằng `pypdf`, xác nhận header `%PDF`, số trang, kích thước và SHA-256 khớp đồng thời với `data/landing/legal/manifest.json` và `data/sources.csv`.

| File | Trang | Kích thước (byte) | SHA-256 | Kết quả |
|---|---:|---:|---|---|
| `bo-luat-hinh-su-vbhn-135-2025.pdf` | 277 | 2,658,760 | `ce7f1dc86e2f40c102f26e5d6980519d51842f864070a979939e182125400155` | Khớp |
| `luat-phong-chong-ma-tuy-vbhn-117-2025.pdf` | 27 | 982,042 | `4bb235aa172021d65a92a73a4224e5d00a8b719b9db9b69081df424b75268e09` | Khớp |
| `nghi-dinh-144-2021-xu-phat-an-ninh-trat-tu.pdf` | 91 | 4,541,775 | `7baad192cc56050a3d07e1261ab04642e5ff873cd9f1969ca29234ac432e7d96` | Khớp |

Nguồn của cả ba văn bản là trang văn bản chính thức của Chính phủ (`vanban.chinhphu.vn`); URL trang nguồn và URL tải PDF đều có trong manifest.

## 2. Kiểm tra news corpus

- Đủ 8/8 JSON trong `data/landing/news/`.
- 8/8 file có giá trị không rỗng cho `url`, `title`, `date_crawled`, `content_markdown`, `source_domain` và `content_sha256`.
- 8/8 checksum của `content_markdown` khớp `content_sha256`, khớp `data/sources.csv` và có bản ghi tương ứng trong `data/landing/web_manifest.json`.
- Đã mở trực tiếp 8/8 URL ngày 25/09/2026; tất cả còn truy cập được.

Đối chiếu sâu ba bài:

| File | Nội dung đã đối chiếu với trang gốc | Kết quả |
|---|---|---|
| `news_01.json` | Tiêu đề; Miu Lê 35 tuổi; sự việc ngày 10/5 tại Hải Phòng; ba loại chất cấm; các mốc phim và âm nhạc | Khớp |
| `news_05.json` | 65 bị can; 48 cán bộ/nhân viên y tế; 9 tội danh; tên và vai trò Nguyễn Thị Mai Anh, Lê Văn Đông; các điều luật được nêu | Khớp |
| `news_06.json` | Trương Hữu Tùng; mạng lưới xuyên biên giới; 65 đối tượng; hơn 10 kg Methamphetamine; địa bàn TP.HCM, Tây Ninh, Vĩnh Long, Cần Thơ | Khớp |

## 3. Lỗi/rủi ro phát hiện và cách xử lý

### Thiếu provenance của nguồn luật

Trước khi sửa, ba dòng legal trong `data/sources.csv` bị trống `source_domain`, `source_tier` và `claim_status`, dù manifest có URL chính thức. Điều này làm giảm khả năng phân biệt nguồn luật chính thức với nguồn báo chí ở các bước sau.

Đã sửa `src/task3_convert_markdown.py` để Task 3 tự sinh:

- `source_domain: vanban.chinhphu.vn`
- `source_tier: official_legal_source`
- `claim_status: official_legal_text`

### Tiêu đề H1 bị lặp

Một số `content_markdown` đã chứa H1; Task 3 lại thêm H1 chuẩn hóa, khiến `news_01`, `news_02`, `news_04`, `news_05` và `news_08` có hai tiêu đề cấp 1. Đã thêm bước bỏ H1 đầu tiên của nội dung nguồn trước khi chèn H1 chuẩn hóa. Acceptance test hiện yêu cầu mỗi Markdown chỉ có đúng một H1 chính.

Đã bổ sung kiểm thử provenance yêu cầu mọi dòng `data/sources.csv` có `title`, `url`, `source`, `source_domain`, `sha256`, `standardized_file` không rỗng và file chuẩn hóa phải tồn tại.

## 4. Chạy lại chuẩn hóa

Lệnh:

```powershell
python -m src.task3_convert_markdown
```

Kết quả: chuẩn hóa thành công 11 nguồn gồm 3 legal và 8 news. Tiêu đề, URL và nội dung đối chiếu được giữ lại trong Markdown. Chạy Task 3 thêm một lần và so sánh SHA-256 của 12 đầu ra (11 Markdown + `data/sources.csv`) cho kết quả `changed=0`, xác nhận quá trình tái lập ổn định.

## 5. Kết quả kiểm thử

Baseline trước thay đổi:

```text
tests/test_acceptance.py: 5 passed in 0.09s
```

Sau khi sửa và chuẩn hóa lại:

```text
tests/test_contracts.py:  15 passed in 0.20s
tests/test_acceptance.py:  6 passed in 0.06s
toàn bộ test suite:        30 passed in 0.27s
```

## 6. File bằng chứng

- `src/task3_convert_markdown.py`
- `tests/test_acceptance.py`
- `data/landing/legal/manifest.json`
- `data/landing/web_manifest.json`
- `data/sources.csv`
- `data/standardized/legal/`
- `data/standardized/news/`

Phần việc được tích hợp vào repo GitHub `Clownnvd/K4-L3B-RAG-Pipeline` trên nhánh `ngan/data-provenance-lab8`; mã commit được lưu trong lịch sử Git của nhánh.

## 7. Kiểm tra an toàn trước khi nộp

- Không có URL nguồn trống hoặc metadata provenance bắt buộc bị thiếu.
- Không thay đổi phần retrieval, generation hoặc UI.
- Không đưa `.env`, API key, virtual environment hoặc cache Python vào bản nộp.
