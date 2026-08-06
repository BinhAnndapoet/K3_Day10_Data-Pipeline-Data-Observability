# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên          | Đinh Lê Bình An            |
| MSSV               | 2A202601519                |
| Khóa/Lớp           | K3                         |
| Tên nhóm           | Nxust                      |
| Vai trò chính      | Ingestion & Data Preparation owner (vai trò 2 + phụ cleaning/testset) |
| Repository         | https://github.com/BinhAnndapoet/K3_Day10_Data-Pipeline-Data-Observability |
| Ngày hoàn thành    | 2026-08-06                 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| ------------------ | --------------------- | ---------------- | ----------------- | ---------- |
| Crossref ingestion | `src/ingestion/crossref.py` — `fetch_source_records`, `parse_crossref_payload`, `load_raw_records` | `Settings` (query/filter/rows) | `data/raw/crossref_response.json` (raw HTTP), `data/raw/crossref_records.json` (24 PaperRecord phẳng) | Hoàn thành |
| Cleaning & data modeling | `src/ingestion/cleaning.py` — `build_clean_dataframe` | `list[PaperRecord]` + `run_date` | `data/clean/papers_clean.csv`, `papers_clean.json` (24 dòng × 16 cột) | Hoàn thành |
| Frozen evaluation set | `src/evaluation/testset.py` — `build_test_set` | Clean dataframe + `output_path` | `data/eval/test_set.json` (10 câu) | Hoàn thành |
| Data contract xuyên suốt | `text_for_embedding`, `age_days`, `authors_joined`/`categories_joined`, `paper_id` ổn định (DOI) | — | Cột do cleaning sinh ra, dùng bởi `index.py`, `qa.py`, `quality.py` | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| --------- | ------------------------------- | -------- |
| Cung cấp raw snapshot đáng tin cho repair | `src/ingestion/corruption.py`, `src/pipelines/corruption_flow.py` (Khải — corruption owner) | Repair re-run `build_clean_dataframe` từ `data/raw/crossref_records.json` → `papers_clean_repaired.*` phục hồi 24 dòng, không sửa tay |
| Data contract cho retrieval | `src/retrieval/index.py`, `src/retrieval/qa.py` (RAG owner) | Clean row có đủ `paper_id`, `title`, `text_for_embedding`, `authors_joined`, `categories_joined`, `published` mà `LocalEmbeddingIndex._build_documents` và `_extract_answer` cần |
| Tài liệu phân tích dữ liệu | Toàn repo | `DATA_ANALYSIS.md` (đặc tính dữ liệu, phát hiện, luồng xử lý) để cả nhóm đối chiếu |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| Fetch Crossref có retry/backoff | `src/ingestion/crossref.py` — `_get_with_retry` | `200 OK`, `total-results=100916`, lấy 24 records | `data/raw/crossref_response.json` có `message.items` dài 24 |
| Lưu raw 2 dạng (audit + flat) | `fetch_source_records` | response nguyên bản + 24 PaperRecord | `crossref_response.json` (~245 KB), `crossref_records.json` (~63 KB) |
| Làm sạch + tạo cột ngữ nghĩa | `build_clean_dataframe` | 24 dòng × 16 cột; 0 record bị drop; 0 duplicate | `papers_clean.csv`: không còn thẻ `<jats:*>`, `summary_chars ≥ 826` |
| Tính freshness field | `age_days` từ `published` | `age_days` 5–175 (median 66), 0 null | `freshness_report.json`: `is_fresh=true`, 0 stale |
| Chốt test set đóng băng | `build_test_set` | 10 câu (4 authors, 4 summary, 2 date) | `test_set.json`; 10/10 tiêu đề khớp exact clean data |

Nêu một output cụ thể mà phần việc của bạn tạo ra hoặc giúp xác minh:

`data/eval/test_set.json` — bộ 10 câu hỏi đóng băng, mỗi câu có `ground_truth_doc_ids = [paper_id]` thật (không bịa) và tiêu đề được bọc trong dấu nháy đơn `'...'`. Thiết kế này là điều kiện tiên quyết để `retrieval_hit_rate = 1.0` ở baseline: câu hỏi trích đúng tiêu đề → `qa.py` gọi `lookup_paper` khớp exact → đúng document luôn nằm top-k. Quan trọng hơn, vì 2 trong 10 câu (q1 → `10.2118/234689-pa`, q9 → `10.47576/2949-1894.2026.7.7.023`) trúng đúng 2 paper bị `drop_latest` xoá (đối chiếu `corruption_log.json`), test set này biến corruption thành tín hiệu đo được: hit rate `1.0 → 0.8` chính là 2/10 câu mất ground-truth paper.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Phần đầu pipeline phải trả lời 3 câu: (1) lấy metadata Crossref ổn định dù API thỉnh thoảng rate-limit (429/503); (2) biến raw nested (title là list, author là list-of-dict, `date-parts` lồng, abstract đầy thẻ JATS) về dạng phẳng, sạch, sẵn sàng embedding; (3) chốt một bộ câu hỏi cố định, công bằng cho 3 trạng thái baseline/corrupted/repaired — đổi test set thì delta metric không còn do corruption.

### Cách triển khai

- **Ingestion:** `fetch_source_records` dựng params từ `Settings`, gọi `_get_with_retry` — vòng lặp thử lại tối đa 4 lần, backoff `1.5 × 2^attempt + jitter`, **đọc header `Retry-After`** của Crossref khi 429; status không retryable raise ngay, retryable (429/5xx) và lỗi kết nối mới backoff. Response nguyên bản lưu trước khi parse (audit nguồn).
- **Parse:** `parse_crossref_payload` làm phẳng `message.items`: `title[0]`, tác giả ghép `given + family`, ngày dàn từ `date-parts: [[Y,M,D]]` theo thứ tự `published → published-online → published-print → issued → posted`, `pdf_url` lấy từ `link`/`resource`. Bộ lọc ingestion bỏ bản ghi thiếu DOI/title/abstract.
- **Clean:** `build_clean_dataframe` strip thẻ `<[^>]+>` + `html.unescape()`, join `authors/categories`, parse `published → YYYY-MM-DD` (pad `01` khi thiếu tháng/ngày), tính `age_days` (chuẩn hoá `run_date` về naive để trừ datetime), dựng `text_for_embedding = "Title: … | Authors: … | Summary: …"`, drop title/summary rỗng, `summary_chars < 100`, trùng `paper_id`/`title`.
- **Testset:** `build_test_set` chọn paper tươi nhất có authors + summary + tiêu đề "quotable" (không chứa `'` ASCII/newline), sinh câu hỏi xoay vòng `authors/summary/date/categories`, phrasing căn chỉnh đúng bộ trích đáp án trong `qa.py` (`"Who authored"`→tác giả, `"When was … published"`→ngày, `"What categories"`→chủ đề, còn lại→câu đầu summary).

### Input, output và contract

| Thành phần | Mô tả |
| ---------- | ----- |
| Input | `Settings` (cho ingestion); `list[PaperRecord]` + `run_date` (cho cleaning); clean DataFrame + `output_path` (cho testset) |
| Output | Raw JSON 2 dạng; clean DataFrame 16 cột; `test_set.json` schema `{id, question_type, question, ground_truth, ground_truth_doc_ids}` |
| Module phụ thuộc | `core.config.Settings`, `core.utils` (`read_json/write_json/normalize_whitespace/first_sentence`), `requests` |
| Module sử dụng output | `index.py` (đọc `text_for_embedding`/metadata), `qa.py` (đọc `authors_joined`/`published`/`summary`), `metrics.py` (đọc test set), `corruption_flow.py` (re-run cleaning từ raw để repair) |
| Điều kiện lỗi cần xử lý | API 429/503 (retry); `date-parts` chỉ có năm (pad `01`); `run_date` aware vs naive (TypeError); tiêu đề chứa `'` ASCII (vỡ regex lookup); thiếu `subject` (categories rỗng) |

### Cách xác minh

```bash
PYTHONPATH=src python -c "
from core.config import load_settings
from ingestion.crossref import fetch_source_records, load_raw_records
from ingestion.cleaning import build_clean_dataframe
from evaluation.testset import build_test_set
from core.utils import now_utc
s = load_settings()
recs = fetch_source_records(s)                 # hoặc load_raw_records(s.paths.raw_records_json)
df  = build_clean_dataframe(recs, now_utc())   # -> papers_clean.csv/json (do pipeline ghi)
ts  = build_test_set(df, s.paths.eval_testset) # -> test_set.json
print(len(recs), len(df), len(ts))
"
```

- **Kết quả mong đợi:** `24 24 10`.
- **Kết quả thực tế:** `24 24 10` — khớp.
- **Artifact/log:** `data/raw/crossref_{response,records}.json`, `data/clean/papers_clean.{csv,json}`, `data/eval/test_set.json` (không chứa secret).

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Cần một test set mà ở baseline agent trả lời đúng 10/10 (để mọi sụt giảm sau này chắc chắn do corruption, không do test khó), đồng thời truy ngược được từng câu về `paper_id` cụ thể.
- **Các phương án đã cân nhắc:** (1) câu hỏi mở, trả lời tự do, chấm bằng LLM judge; (2) câu hỏi dạng "liệt kê paper về chủ đề X" — ground truth là tập paper; (3) câu hỏi neo vào đúng một paper, bọc tiêu đề trong `'...'` để kích hoạt `lookup_paper` exact match.
- **Phương án đã chọn:** (3) — mỗi câu gắn `ground_truth_doc_ids = [paper_id]`, tiêu đề trong `'...'`, phrasing khớp keyword mà `_extract_answer` đã định nghĩa.
- **Lý do:** Neo vào một paper + exact lookup cho `retrieval_hit_rate = 1.0` xác định ở baseline (đã verify), nên delta metric có ý nghĩa nhân quả. Ground truth trích nguyên văn từ clean row nên `mean_token_f1 = 1.0` khi retrieval đúng. Phương án (1) phụ thuộc chất lượng judge (lab đang dùng model free fallback heuristic), (2) khó cô lập 1 paper → khó giải thích vì sao metric đổi.
- **Bằng chứng quyết định phù hợp:** baseline `retrieval_hit_rate = 1.0`, `mean_token_f1 = 1.0`; sau corruption, đúng 2 câu (q1, q9) có ground-truth paper nằm trong `drop_latest` → hit rate `1.0 → 0.8` — sụt giảm giải thích được trọn vẹn bằng dữ liệu, không phải noise.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** khi xác minh dữ liệu trên Windows, script thoát với `UnicodeEncodeError: 'charmap' codec can't encode character '‐' ...` ở dòng in tiêu đề bài báo — pipeline chạy đúng nhưng bước in/kiểm tra bị crash.
- **Lệnh hoặc bước tái hiện:** `.venv/Scripts/python.exe -c "print(...tiêu đề bài có ký tự ngoài ASCII...)"` trên console Windows mặc định `cp1252`.
- **Nguyên nhân gốc:** dữ liệu Crossref thật **không thuần ASCII** — 1 tiêu đề tiếng Nga (Cyrillic), dấu nháy cong `'` (U+2019), gạch nối Unicode `‐` (U+2010). Console Windows mặc định `cp1252` không encode được các ký tự này, nên mọi bước log/in/debug đều có thể vỡ nếu không ép UTF-8.
- **Cách xử lý:** chạy xác minh với `PYTHONIOENCODING=utf-8 PYTHONUTF8=1`; file JSON được ghi bằng `write_json` với `encoding="utf-8"` (đã đúng từ đầu) nên bản thân artifact không hỏng — chỉ tầng hiển thị cần ép UTF-8.
- **Cách xác minh sau khi sửa:** in được đầy đủ 10 câu hỏi + tiêu đề Cyrillic; `papers_clean.json` đọc lại đúng, `test_set.json` round-trip OK.
- **Điều học được:** với dữ liệu thật, **không bao giờ giả định ASCII**. Ký tự ngoài ASCII ảnh hưởng nhiều điểm: encoding khi ghi/đọc, regex (dấu `'` cong `’` không khớp `'` ASCII trong regex lookup của `qa.py`), và hiển thị. Đây cũng là lý do `_is_quotable_title` lọc tiêu đề chứa `'` ASCII — để regex `'([^']+)'` trích đúng tiêu đề.

## 7. Hiểu biết về luồng end-to-end

**Câu trả lời:**

1. **Dữ liệu từ Crossref đến vector index:** `crossref.py` gọi `/works` với retry/backoff (429/503), lưu raw response rồi parse thành `PaperRecord` với `paper_id = DOI` ổn định. `cleaning.py` strip JATS, join authors/categories, parse ngày, tính `age_days`, ghép `text_for_embedding`. `index.py` embedding MiniLM qua Chroma cosine, collection riêng mỗi trạng thái (`papers-baseline/corrupted/repaired`) + manifest JSON.
2. **Evaluation set và ground-truth doc IDs:** `testset.py` chọn 10 paper từ clean data; mỗi câu (`authors/summary/date/categories`) kèm `ground_truth` trích nguyên văn từ clean row và `ground_truth_doc_ids = [paper_id]` thật. `qa.py` retrieval top-k rồi trả lời theo keyword; `retrieval_hit` = ground-truth doc có trong top-k; token F1 so answer với ground truth; judge chấm đúng/sai.
3. **Quality checks khác freshness monitoring:** quality đo cấu trúc tĩnh — row count, null, duplicate, missing title/summary, duplicate rows. Freshness đo chiều thời gian — `age_days` có vượt 180 ngày không, dữ liệu mới/cũ nhất. Corruption `blank_summary` đánh vào quality, còn `old_date` đánh vào freshness — 2 signal bắt 2 loại hỏng khác nhau.
4. **Phải dùng cùng test set:** test set gắn ground truth vào `paper_id` cụ thể; đổi câu hỏi/ground truth giữa các phase thì chênh lệch metric là do test set, không do corruption. Giữ nguyên `data/eval/test_set.json` (build một lần, chỉ rebuild khi `REFRESH_TEST_SET=1`) là điều kiện để delta baseline→corrupted→repaired có ý nghĩa nhân quả.
5. **Repair thành công dựa trên:** repaired metrics khôi phục về baseline (`retrieval_hit_rate` 0.8→1.0, `mean_token_f1` 0.8→1.0, `judge_accuracy` 0.8→1.0, `mean_judge_score` 4.2→5) đồng thời `quality_report_repaired.json` pass và `freshness_report_repaired.json` fresh (0 stale, 24 dòng). Quan trọng: repaired data tái dựng từ `data/raw/crossref_records.json` bằng cùng đường cleaning — không sửa tay answers.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ------------- | -------: | --------: | -------: | -------------------- |
| `retrieval_hit_rate` | 1.000 | 0.800 | 1.000 | 2/10 câu miss vì q1+q9 trúng 2 paper bị `drop_latest` |
| `mean_token_f1` | 1.000 | 0.800 | 1.000 | F1 = 0 đúng tại 2 câu miss; câu khác vẫn 1.0 |
| `judge_accuracy` | 1.000 | 0.800 | 1.000 | Judge fallback heuristic nên chấm theo F1 |
| `mean_judge_score` | 5 | 4.200 | 5 | 2 câu miss kéo trung bình xuống 0.8 điểm |
| Quality checks | pass | fail | pass | Corrupted: `summary` fail (missing 1) + `freshness` fail (stale 2) |
| Freshness status | fresh | stale (2) | fresh | Oldest published corrupted là `2010-01-01` |

### Kết luận từ số liệu

1. **`drop_latest` xoá 4 records trong đó có 2 paper thuộc test set** (`10.2118/234689-pa` ở q1, `10.47576/2949-1894.2026.7.7.023` ở q9 — đối chiếu `corruption_log.json` với `test_set.json`) → row count 24→21 → `retrieval_hit_rate` 1.0→0.8 và `mean_token_f1` 1.0→0.8. Cùng lúc `blank_summary` + `old_date` → quality fail (summary missing 1) và freshness stale 2.
2. **Repair re-run cleaning từ raw snapshot** → `papers_clean_repaired.csv` 24 dòng, summary đủ, `age_days` đúng → `quality_report_repaired.json` pass, `freshness_report_repaired.json` fresh (0 stale) → retrieval + answer khôi phục đúng baseline (hit 1.0, F1 1.0, judge 1.0, score 5). Phục hồi 100% vì raw snapshot không bị corrupt.

**Corruption nào ảnh hưởng rõ nhất và vì sao?** `drop_latest` — vì nó là corruption duy nhất làm thay đổi metric agent (2 câu miss retrieval); các loại khác (blank_summary, old_date) chỉ làm fail quality/freshness signals, còn `inject_noise`/`truncate_title` trượt qua vì 2 paper bị tác động không nằm trong test set. Lý do: test set chọn paper theo "freshest first", nên paper mới nhất bị drop đúng trúng ground-truth docs — đây là hệ quả trực tiếp của thiết kế test set của tôi.

**Kết quả nào khác với kỳ vọng ban đầu?** Tác động của data quality lên RAG **không tuyến tính**: chỉ 2/24 record (8%) bị xoá mà `retrieval_hit_rate` sụt 20% (2/10 câu), vì độ phủ giữa dữ liệu hỏng và test set cao. Ngoài ra `duplicate_rows` đổi `paper_id` thành hậu tố `_dup` nên lọt qua check duplicate theo ID — giới hạn của quality check, không phải của phần ingestion/cleaning.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. **Data pipeline:** raw nested của Crossref (list, dict, `date-parts`) cần "làm phẳng" nhất quán ngay từ ingestion; mọi cột dẫn xuất (`age_days`, `summary_chars`, `text_for_embedding`) phải tái tính sau mỗi biến đổi để downstream đọc đúng trạng thái.
2. **Data contract:** test set phải neo ground truth vào `paper_id` ổn định (DOI) và trích nguyên văn từ clean row — đây là chân lý cho mọi metric; nếu ground truth bịa, toàn bộ delta baseline/corrupted/repaired vô nghĩa.
3. **Ảnh hưởng của data đến RAG agent:** tác động không tuyến tính — 8% record hỏng có thể gây 20% sụt hit rate nếu trúng đúng paper trong test set. Điều này giải thích vì sao cần observability: phát hiện hỏng trước khi nó chạm tới người dùng.

### Nếu có thêm thời gian

Bổ sung category thật (Crossref `subject` = 0/24) từ nguồn khác (ví dụ phân loại từ `container-title`/tên tạp chí bằng classifier) để test được kỹ năng `categories` của agent. Ngoài ra, mở rộng test set lên 20–30 câu và tăng `max_results` để giảm phương sai metric — hiện 2/10 câu dính `drop_latest` khiến delta bị chi phối bởi 1 loại corruption.

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi "đã chạy thành công" cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Đinh Lê Bình An
**Ngày xác nhận:** 2026-08-06
