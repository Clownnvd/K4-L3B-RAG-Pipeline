# Handoff cho Dương Thị Ngân — Lab 8 RAG Pipeline

## Thông tin thành viên

- Họ và tên: Dương Thị Ngân
- MSSV: `2A2026022808`
- Lớp/nhóm: `K4-L3B`
- Vai trò: Data & Provenance
- Phạm vi: kiểm chứng dữ liệu và khả năng tái tạo; không nhận là tác giả các commit do thành viên khác đã tạo.

## Mục tiêu bàn giao

Ngân tiếp nhận bộ dữ liệu nền đã có và tạo bằng chứng cá nhân cho bốn việc:

1. Đối chiếu 3 PDF pháp luật với manifest và `data/sources.csv`.
2. Kiểm tra 8 bài news có đủ URL, tiêu đề, ngày crawl và nội dung Markdown.
3. Chạy lại bước chuẩn hóa, kiểm tra ít nhất 3 file đầu ra với nguồn landing.
4. Chạy acceptance test, ghi một lỗi hoặc rủi ro dữ liệu thực tế và cách xử lý.

Không đổi retrieval, generation, UI hoặc số liệu A/B nếu chưa phát hiện lỗi có bằng chứng.

## Cấu trúc cần đọc trước

- `README.md`: sản phẩm phải nộp và cách chạy.
- `docs/GRADING_RUBRIC.md`: thang điểm.
- `docs/MODULE_CONTRACTS.md`: schema và interface không được phá vỡ.
- `TEAMMATES.md`: phân công nhóm.
- `reports/K4-L3B-2A2026022808-DuongThiNgan.md`: báo cáo cần bổ sung bằng chứng.
- `data/sources.csv`, `data/landing/`, `data/standardized/`: dữ liệu cần kiểm tra.

## Các bước trên Windows

### 1. Giải nén và mở thư mục

Giải nén ZIP vào một thư mục riêng, ví dụ:

```powershell
cd C:\AI20K\K4-L3B-RAG-Pipeline-Ngan
```

Không dùng hoặc chia sẻ file `.env` từ máy người khác. Gói bàn giao không chứa `.env`, API key, Git history, ChromaDB hay cache.

### 2. Tạo môi trường

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e ".[dev]"
```

Nếu chỉ kiểm tra dữ liệu và acceptance test thì không cần API key.

### 3. Chạy mốc ban đầu

```powershell
python -m pytest tests/test_acceptance.py -q
```

Kết quả kỳ vọng: `5 passed`. Nếu fail, giữ nguyên log lỗi trước khi sửa.

### 4. Kiểm tra legal corpus

- Mở `data/landing/legal/manifest.json` và `data/sources.csv`.
- Xác nhận đủ 3 PDF, tên file đúng và mỗi file mở được.
- Đối chiếu URL nguồn chính thức trong manifest/sources.
- Tính lại checksum nếu manifest có trường checksum; không tự thay checksum nếu chưa xác định file nguồn đúng.
- Mở Markdown tương ứng trong `data/standardized/legal/` và kiểm tra tiêu đề, nguồn, nội dung mẫu.

### 5. Kiểm tra news corpus

Với cả 8 file `data/landing/news/news_*.json`, xác nhận các trường sau không rỗng:

```text
url
title
date_crawled
content_markdown
```

Mở ít nhất 5 URL; kiểm tra sâu ít nhất 3 bài bằng cách so nội dung trang với file JSON và file Markdown chuẩn hóa. Không vượt captcha hoặc cơ chế chặn crawler; nếu URL không truy cập được, ghi rõ ngày kiểm tra và trạng thái.

### 6. Chạy lại chuẩn hóa

```powershell
python -m src.task3_convert_markdown
python -m pytest tests/test_acceptance.py -q
```

So sánh thay đổi trước/sau. Không chấp nhận việc script làm mất `title`, `source`, `url` hoặc rút nội dung xuống dưới 200 ký tự.

### 7. Điền báo cáo cá nhân

Cập nhật `reports/K4-L3B-2A2026022808-DuongThiNgan.md` bằng:

- ngày và máy đã kiểm tra;
- danh sách file/URL đã đối chiếu;
- lệnh test và kết quả thực tế;
- ít nhất một lỗi hoặc rủi ro đã phát hiện;
- cách xử lý và file đã sửa;
- commit hash của chính Ngân nếu làm việc trong Git repository.

Không ghi `Done` nếu chưa có bằng chứng tương ứng.

### 8. Chạy kiểm tra cuối

```powershell
python -m pytest tests/test_contracts.py -q
python -m pytest tests/test_acceptance.py -q
python -m pytest -q
```

Trước khi gửi lại, kiểm tra không có secret/cache trong danh sách file:

```powershell
Get-ChildItem -Force
```

Không gửi `.env`, API key, `chroma_db/`, `.venv/`, `.pytest_cache/`, `__pycache__/` hoặc `pageindex_doc_ids.json`.

## Prompt gửi cho trợ lý AI trên máy Ngân

Sao chép nguyên khối dưới đây cho trợ lý AI sau khi đã giải nén repo:

```text
Bạn đang hỗ trợ Dương Thị Ngân, MSSV 2A2026022808, hoàn thành phần Data & Provenance của Lab 8 K4-L3B.

Hãy đọc toàn bộ các file sau trước khi sửa: README.md, docs/GRADING_RUBRIC.md, docs/MODULE_CONTRACTS.md, docs/STEP_BY_STEP.md, TEAMMATES.md, NGAN_HANDOFF.md và reports/K4-L3B-2A2026022808-DuongThiNgan.md.

Nhiệm vụ:
1) kiểm tra 3 PDF legal với manifest và data/sources.csv;
2) kiểm tra đủ metadata của 8 news JSON, mở ít nhất 5 URL và đối chiếu sâu ít nhất 3 bài;
3) chạy lại python -m src.task3_convert_markdown;
4) chạy acceptance test trước và sau thay đổi;
5) ghi bằng chứng thật, một lỗi/rủi ro thật và cách xử lý vào báo cáo cá nhân của Ngân;
6) cuối cùng chạy contract test, acceptance test và toàn bộ pytest.

Không nhận là tác giả commit của Nguyễn Văn Duy. Không sửa retrieval/generation/UI nếu không có lỗi có thể tái hiện. Không đọc, in, commit hoặc gửi .env/API key. Không push và không nộp bài nếu Ngân chưa yêu cầu rõ. Mọi kết luận hoàn thành phải kèm lệnh test và output mới nhất.
```

## Kết quả cần gửi lại cho Duy

- Báo cáo cá nhân của Ngân đã có bằng chứng thật.
- Các file dữ liệu sửa đổi, nếu có.
- Log ba lệnh test cuối.
- Commit hash/patch của phần Ngân làm.
- Danh sách vấn đề còn mở; nếu không có, ghi rõ `Không còn vấn đề đã biết trong phạm vi Data & Provenance`.
