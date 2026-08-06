# CP1 — Vai trò 5: Evaluation owner (Nhóm 6 người)

> Checkpoint: `00:30–01:05` · Pass: clean CSV/JSON đọc được, `paper_id` unique, `text_for_embedding`
> và `age_days` có mặt, count/lý do record bị loại có thể truy vết.

## Cập nhật quan trọng: `testset.py` đã được implement (không phải bởi mình)

Commit `6b9ae5f "fish crossref, clean & test set"` trên `main` đã hoàn thiện cả
`src/ingestion/crossref.py`, `src/ingestion/cleaning.py` và `src/evaluation/testset.py`, đồng thời
sinh dữ liệu thật:

- `data/raw/crossref_response.json`, `data/raw/crossref_records.json`
- `data/clean/papers_clean.csv`, `data/clean/papers_clean.json`
- `data/eval/test_set.json` (10 câu hỏi)

Vì vậy phần việc CP1 của vai trò 5 lúc này không phải "viết draft" từ đầu nữa mà là **đối chiếu
test set đã có với contract mà `qa.py`/`metrics.py` yêu cầu** (đã ghi ở CP0), để phát hiện sớm nếu
có lệch schema trước khi CP2/CP3 chạy evaluation thật.

## 1. Đối chiếu test set với cleaned dataframe (không dùng raw chưa clean)

Kiểm tra: mọi `ground_truth_doc_ids` trong `data/eval/test_set.json` đều là DOI xuất hiện trong cột
`paper_id` của `data/clean/papers_clean.csv`, ví dụ:

| `id` trong test set | `ground_truth_doc_ids` | Có trong `papers_clean.csv`? |
| --- | --- | --- |
| `q1` | `10.2118/234689-pa` | Có — hàng đầu tiên của clean CSV |
| `q3` | `10.21203/rs.3.rs-10178277/v1` | Có |
| `q9` | `10.47576/2949-1894.2026.7.7.023` | Có |

→ Test set được build từ cleaned dataframe thật (đúng contract "chờ `paper_id` stable trước khi
ghi test set" ở CP0), không lấy từ raw payload.

## 2. Draft question/ground truth có thể kiểm chứng bằng nội dung paper

`testset.py` (`_make_question`, `_ground_truth`) sinh đúng 4 loại câu hỏi đã thiết kế ở CP0, và mỗi
`ground_truth` lấy verbatim từ cột clean tương ứng — khớp với template đã phác thảo trước:

| `question_type` | Template thực tế trong code | Nguồn `ground_truth` |
| --- | --- | --- |
| `authors` | `Who authored the paper '{title}'?` | `authors_joined` |
| `date` | `When was the paper '{title}' published?` | `published` |
| `categories` | `What categories are listed for the paper '{title}'?` | `categories_joined` |
| `summary` (mặc định) | `What is the main contribution described in the paper '{title}'?` | `first_sentence(summary)` |

Một khác biệt nhỏ so với draft CP0: câu hỏi `summary` dùng phrasing "What is the main contribution
described in..." thay vì "What is ... about?" — vẫn rơi vào nhánh mặc định của `_extract_answer`
trong `qa.py` (không match `who authored`/`when was`/`what categories`) nên vẫn trả lời đúng bằng
`first_sentence(summary)`. Không cần sửa.

Code cũng tự loại các title chứa dấu nháy đơn (`_is_quotable_title`) — đúng lưu ý đã ghi ở CP0 rằng
`qa.py` dùng regex `'([^']+)'` để exact-lookup, nếu không kiểm tra sẽ có câu hỏi lookup sai document.

## 3. `ground_truth_doc_ids` lấy từ `paper_id` clean — đã đúng, không tự bịa ID

`build_test_set` gán `"ground_truth_doc_ids": [paper_id]` trực tiếp từ `row["paper_id"]` của
dataframe clean (dòng 106+120 trong `testset.py`), đúng quy tắc đã nêu ở CP0.

## 4. Việc còn lại của vai trò 5 trước CP2/CP3

- Test set đã đủ điều kiện dùng ngay cho `evaluate_pipeline()` — không cần build lại trừ khi
  `cleaning.py` thay đổi và làm `paper_id` không còn khớp.
- Cần vai trò 6 (mình) hỗ trợ chạy thử `run_data_quality_checks`/`build_freshness_report` trên
  đúng `data/clean/papers_clean.csv` này để xác nhận không có row bị duplicate/null trước khi coi
  dữ liệu "ổn định" cho baseline evaluation ở CP3.
- Artifact bàn giao ở CP1: không tạo file mới; xác nhận bằng bảng đối chiếu ở mục 1–3 phía trên.
