# Group Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin bài nộp

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Khóa/Lớp         | K3              |
| Tên nhóm         | Nhóm 6     |
| Repository         | https://github.com/BinhAnndapoet/K3_Day10_Data-Pipeline-Data-Observability |
| Ngày hoàn thành | 2026-08-06               |

### Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò chính | Module/deliverable sở hữu |
| --: | --- | --- | --- | --- |
| 1 | [Họ tên] | [MSSV] | Lead — Integrator & release owner | `src/pipelines/phase1.py`, `src/pipelines/corruption_flow.py`, `script/run_*.py` |
| 2 | [Họ tên] | [MSSV] | Ingestion owner | `src/ingestion/crossref.py`, `data/raw/` |
| 3 | [Họ tên] | [MSSV] | Cleaning & corruption owner | `src/ingestion/cleaning.py`, `src/ingestion/corruption.py`, `data/clean/` |
| 4 | [Họ tên] | [MSSV] | RAG & agent owner | `src/retrieval/*`, `data/embeddings/`, `data/chroma/` |
| 5 | [Họ tên] | [MSSV] | Evaluation owner | `src/evaluation/*`, `data/eval/`, `data/results/` |
| 6 | [Họ tên] | [MSSV] | Observability owner | `src/observability/*`, `data/quality/`, `data/reports/` |

> Các ô `[Họ tên]`/`[MSSV]` để trống để từng thành viên điền thông tin cá nhân trước khi nộp.

## 2. Tóm tắt kết quả

**Tóm tắt của nhóm:**

Nhóm đã hoàn thành trọn vẹn pipeline end-to-end hai pha: (1) baseline với dữ liệu sạch và (2) giả lập dữ liệu lỗi, đo impact lên agent RAG, sau đó repair từ nguồn và so sánh.

Baseline pipeline tạo đủ artifact: raw response/records từ Crossref (24 records), clean dataset (24 dòng, `paper_id` unique), Chroma index `papers-baseline` + embedding manifest, test set đóng băng 10 câu hỏi, `baseline_metrics.json`, quality/freshness reports và `phase1_report.md`. Kết quả baseline: `retrieval_hit_rate = 1.0`, `mean_token_f1 = 1.0`, `judge_accuracy = 1.0`, `mean_judge_score = 5`; quality checks pass toàn bộ; freshness đạt (0 stale / 180 ngày).

Corruption áp dụng 6 dạng có chủ đích lên clean data (drop 4 records mới nhất, blank summary, inject noise, truncate title, đẩy 2 published date về 2010-01-01, chèn duplicate), đều có log với paper_id cụ thể. Tác động rõ nhất lên agent: `retrieval_hit_rate` và `mean_token_f1` sụt từ 1.0 xuống 0.8 — đúng 2/10 câu hỏi trong test set mất ground-truth paper vì 2 paper đó nằm trong danh sách bị drop (`10.2118/234689-pa` và `10.47576/2949-1894.2026.7.7.023`). Quality checks fail: summary missing 1 và freshness stale 2.

Repair chạy lại cleaning từ raw snapshot `data/raw/crossref_records.json` (không sửa tay answers/metrics). Kết quả repaired khôi phục đủ mọi chỉ số về mức baseline: hit rate 1.0, F1 1.0, judge accuracy 1.0, quality pass, freshness fresh. Blocker còn lại quan trọng nhất: model LLM free (`inclusionai/ling-3.0-flash:free`) không hỗ trợ structured output nên judge LLM fallback về heuristic khi request bị lỗi — metric `mean_judge_score` cần diễn giải thận trọng; ngoài ra Ragas bị skip (cần `RUN_RAGAS=1`).

## 3. Kiến trúc và luồng dữ liệu

### Luồng end-to-end

```text
Crossref API
    -> raw response/raw records (data/raw/crossref_response.json, crossref_records.json)
    -> cleaning và data modeling (data/clean/papers_clean.csv/json)
    -> embedding + ChromaDB index (papers-baseline, data/embeddings/papers_embeddings.json)
    -> evaluation baseline (data/results/baseline_answers.json, baseline_metrics.json)
    -> quality/freshness reports (data/quality/quality_report_baseline.json, freshness_report.json)
    -> corruption (data/results/corruption_log.json, papers_clean_corrupted.*)
    -> re-index và re-evaluate (papers-corrupted, corrupted_metrics.json, corrupted_answers.json)
    -> repair từ dữ liệu nguồn (papers_clean_repaired.*, papers-repaired)
    -> comparison report (data/reports/corruption_report.md)
```

### Trách nhiệm của từng khối

| Khối             | Input          | Xử lý chính             | Output/artifact          | Owner          |
| ----------------- | -------------- | -------------------------- | ------------------------ | -------------- |
| Ingestion         | Crossref REST API | Fetch, retry/backoff 429/503, parse payload, PaperRecord stable `paper_id` | `data/raw/crossref_response.json`, `data/raw/crossref_records.json` | Thành viên 2 |
| Cleaning          | Raw records    | Normalize title/summary/authors/categories, parse date, dedupe, tính `age_days`, build `text_for_embedding` | `data/clean/papers_clean.csv/json` | Thành viên 3 |
| Embedding/index   | Clean data     | `sentence-transformers/all-MiniLM-L6-v2`, Chroma cosine, collection theo trạng thái | `data/embeddings/papers_embeddings*.json`, `data/chroma/` | Thành viên 4 |
| Evaluation        | Test set + index | `build_test_set`, evaluate retrieval hit rate, token F1, judge accuracy/score | `data/eval/test_set.json`, `data/results/*_answers.json`, `*_metrics.json` | Thành viên 5 |
| Observability     | Clean/corrupted/repaired data | Quality checks (row count, paper_id, title, summary, duplicate, freshness), freshness report | `data/quality/quality_report_*.json`, `freshness_report*.json` | Thành viên 6 |
| Corruption/repair | Baseline clean + raw snapshot | 6 dạng corruption có log; repair = re-run cleaning từ raw | `data/results/corruption_log.json`, `papers_clean_corrupted/repaired.*` | Thành viên 3 |
| Orchestration     | Các module trên | `run_phase1.py`, `run_corruption_flow.py`; paths/collections tách biệt cho 3 trạng thái | `data/reports/phase1_report.md`, `corruption_report.md` | Thành viên 1 |

## 4. Cách tái hiện kết quả

### Cấu hình không chứa secret

| Biến/cấu hình             | Giá trị sử dụng |
| ---------------------------- | ------------------- |
| `LLM_PROVIDER`             | `openrouter`         |
| `LLM_MODEL`                | `inclusionai/ling-3.0-flash:free` |
| Embedding model              | `sentence-transformers/all-MiniLM-L6-v2` |
| Số lượng Crossref records | 24         |
| Retrieval`top_k`           | 4         |
| Freshness threshold          | 180 ngày         |
| Random seed, nếu có        | `random_state=42` (corruption shuffle)         |

Không dán nội dung API key hoặc file `.env` vào báo cáo — `.env` nằm trong `.gitignore`, không được commit.

### Lệnh cài đặt

```bash
uv sync
```

### Lệnh chạy

Baseline:

```bash
uv run python script/run_phase1.py
```

Corruption flow:

```bash
uv run python script/run_corruption_flow.py
```

### Kết quả tái hiện

| Lệnh             | Trạng thái                                    | Thời điểm chạy gần nhất | Bằng chứng                         |
| ----------------- | ----------------------------------------------- | ----------------------------- | ------------------------------------ |
| Baseline pipeline | Thành công | 2026-08-06 ~11:53 (GMT+7) | `data/results/baseline_metrics.json`, `data/reports/phase1_report.md` |
| Corruption flow   | Thành công | 2026-08-06 ~11:55 (GMT+7) | `data/results/corrupted_metrics.json`, `data/reports/corruption_report.md` |

## 5. Ingestion, cleaning và data contract

### Nguồn dữ liệu

| Thuộc tính                | Giá trị                             |
| --------------------------- | ------------------------------------- |
| Source                      | Crossref REST API (`api.crossref.org/works`) |
| Query/filter                | `agentic retrieval augmented generation large language model` + `from-pub-date:{180 ngày trước},has-abstract:true` |
| Thời điểm lấy dữ liệu | 2026-08-06 (snapshot `crossref_records.json`, không refresh giữa các phase) |
| Số record nhận được    | 24 |
| Cơ chế retry/backoff      | Retry với backoff cho HTTP 429/503; raw response được lưu trước khi parse |

### Raw và clean schema

| Trường        | Kiểu dữ liệu | Bắt buộc?  | Ý nghĩa   | Xử lý khi thiếu/sai |
| --------------- | --------------- | ------------ | ----------- | ---------------------- |
| `paper_id` | str (DOI)         | Có | Stable ID từ DOI — khoá xuyên suốt raw→clean→index→test set | Drop nếu rỗng; không tự bịa ID |
| `title` | str         | Có | Tiêu đề bài báo | Drop nếu rỗng |
| `summary` | str         | Có | Abstract/khái quát | Drop nếu rỗng; chuẩn hoá whitespace |
| `authors` | list[str] / str | Không | Danh sách tác giả | Chuyển thành `authors_joined` (dấu phẩy); rỗng nếu thiếu |
| `categories` | list[str] / str | Không | Subject areas | Chuyển thành `categories_joined`; rỗng nếu thiếu |
| `published` | date (ISO) | Có | Ngày xuất bản | Parse; nếu sai/thiếu → xử lý theo rule cleaning |
| `age_days` | int | Có | Số ngày từ `published` đến run date | Tính lại từ `published` |
| `text_for_embedding` | str | Có | `Title: ... | Authors: ... | Summary: ...` — văn bản đi embedding | Rebuild sau mọi biến đổi dữ liệu |
| `summary_chars` | int | Không | Độ dài summary — dùng cho quality check | Re-sync sau blank/noise |

### Quy tắc cleaning

| Quy tắc                                 | Quality dimension liên quan | Số record bị tác động | Cách xác minh      |
| ---------------------------------------- | ---------------------------- | -------------------------: | -------------------- |
| Loại record không có title/summary | Completeness | 0 (24/24 hợp lệ) | `quality_report_baseline.json` — title/summary missing 0 |
| Dedupe theo `paper_id` | Uniqueness | 0 trùng | `paper_id.duplicate_count = 0` |
| Chuẩn hoá authors/categories → `*_joined` | Validity | 24 | Check cột tồn tại trong `papers_clean.csv` |
| Parse `published` + tính `age_days` | Validity/Timeliness | 24 | `freshness_report.json` — stale 0/24 |
| Build `text_for_embedding` | Completeness | 24 | Index chứa đủ 24 documents |

Giải thích cách nhóm tạo `text_for_embedding`, document ID và `age_days`:

- `text_for_embedding`: nối `Title`, `Authors`, `Summary` theo template thống nhất, tái lập sau mọi thay đổi (corruption, repair).
- Document ID trong Chroma: `record_id = "{paper_id}::{index}"` (paper_id + vị trí) để tránh trùng ID khi có duplicate; `paper_id` vẫn là khoá logic cho lookup/test set.
- `age_days`: chênh lệch ngày giữa `published` và ngày chạy; corruption `old_date` đổi `published` về `2010-01-01` và **tính lại `age_days`** để freshness phản ánh đúng (stale 2).

## 6. Evaluation setup

| Thành phần                             | Cấu hình thực tế          |
| ---------------------------------------- | ----------------------------- |
| Số câu hỏi                            | 10         |
| Các`question_type`                    | `authors`, `summary`, `date`, `categories` (xoay vòng) |
| Ground-truth document ID                 | Lấy từ `paper_id` của row clean tương ứng trong dataframe, không tự bịa |
| Embedding model                          | `sentence-transformers/all-MiniLM-L6-v2` |
| Vector store/collection                  | Chroma PersistentClient, cosine; `papers-baseline` / `papers-corrupted` / `papers-repaired` |
| Retrieval`top_k`                       | 4                   |
| LLM provider/model                       | OpenRouter / `inclusionai/ling-3.0-flash:free` |
| Test set dùng chung cho ba trạng thái | `data/eval/test_set.json` (10 câu, đóng băng) |

Giải thích vì sao test set được giữ nguyên khi đánh giá baseline, corrupted và repaired:

Test set là tập câu hỏi + ground truth đóng băng, gắn `ground_truth_doc_ids` là `paper_id` cụ thể. Giữ nguyên qua 3 trạng thái là điều kiện tiên quyết để so sánh công bằng: nếu đổi câu hỏi hoặc đổi ground truth giữa chừng thì chênh lệch metric không còn do corruption gây ra. Cách nhóm đảm bảo: test set chỉ build một lần (từ clean baseline), lưu `data/eval/test_set.json`, và `corruption_flow.py` luôn truyền cùng path này khi evaluate cả 3 trạng thái — không rebuild giữa chừng (chỉ rebuild khi env `REFRESH_TEST_SET=1`).

## 7. Kết quả baseline

### Artifact checklist

| Artifact                 | Đường dẫn thực tế                | Trạng thái | Ghi chú   |
| ------------------------ | -------------------------------------- | ------------ | ---------- |
| Raw response/records     | `data/raw/crossref_response.json`, `crossref_records.json`                          | Có | 24 records |
| Cleaned dataset          | `data/clean/papers_clean.csv`, `papers_clean.json`                        | Có | 24 dòng |
| Embedding manifest/index | `data/embeddings/papers_embeddings.json` + `data/chroma/`                   | Có | collection `papers-baseline` |
| Evaluation set           | `data/eval/test_set.json`                         | Có | 10 câu |
| Baseline metrics         | `data/results/baseline_metrics.json` | Có | — |
| Quality/freshness        | `data/quality/quality_report_baseline.json`, `freshness_report.json`                      | Có | — |
| Baseline report          | `data/reports/phase1_report.md`      | Có | tiếng Việt |

### Baseline metrics

| Metric                 |       Giá trị | Diễn giải                             |
| ---------------------- | --------------: | --------------------------------------- |
| `retrieval_hit_rate` |     1.000 | Cả 10 câu truy vấn ra đúng ground-truth paper trong top-k (k=4) |
| `mean_token_f1`      |     1.000 | Câu trả lời khớp hoàn toàn ground truth |
| `judge_accuracy`     |     1.000 | Judge đánh giá đúng 10/10 câu |
| `mean_judge_score`   |     5 | Điểm judge trung bình tối đa (thang 1–5) |
| Ragas, nếu có        | skipped | Bị skip vì chưa đặt `RUN_RAGAS=1` |

## 8. Data quality và freshness

### Quality checks

| Check        | Quality dimension | Ngưỡng/kỳ vọng | Kết quả baseline      | Bằng chứng |
| ------------ | ----------------- | ------------------ | ----------------------- | ------------ |
| `row_count` | Completeness | > 0 | Pass — 24 dòng | `quality_report_baseline.json` |
| `paper_id` | Uniqueness | null = 0, duplicate = 0 | Pass — 0 null, 0 dup | như trên |
| `title` | Completeness | missing = 0 | Pass — 0 missing | như trên |
| `summary` | Completeness | missing = 0, short ≥ 40 chars | Pass — 0 missing, 0 short | như trên |
| `duplicate_rows` | Uniqueness | 0 dòng trùng (paper_id,title) | Pass — 0 | như trên |
| `freshness` | Timeliness | stale ≤ 0 (ngưỡng 180 ngày) | Pass — 0 stale | như trên |

### Freshness

| Thuộc tính               | Giá trị                           |
| -------------------------- | ----------------------------------- |
| Freshness được đo tại | Clean dataset `papers_clean.csv` (`age_days`/`published`) |
| Timestamp mới nhất       | 2026-08-01 |
| Ngưỡng freshness         | 180 ngày |
| Trạng thái baseline      | Fresh               |
| Lý do                     | 0/24 dòng có `age_days` vượt 180 ngày; trẻ nhất 5 ngày (2026-08-01), già nhất 175 ngày (2026-02-12) |

## 9. Corruption scenarios và repair

| Corruption         | Cách tạo | Record bị tác động | Quality signal kỳ vọng | Tác động thực tế | Cách repair   |
| ------------------ | ---------- | ---------------------: | ------------------------ | --------------------- | -------------- |
| `drop_latest` | Xoá 15% records mới nhất sau shuffle (random_state=42) | 4 (`10.2118/234689-pa`, `10.47576/2949-1894.2026.7.7.023`, `10.32473/flairs.39.1.141782`, `10.20944/preprints202604.0339.v1`) | Row count giảm; hit rate giảm nếu test set trỏ tới paper bị xoá | Row count 24→21; **2 câu test set (q1, q9) miss** → hit rate 1.0→0.8 | Re-run cleaning từ raw snapshot |
| `blank_summary` | Xoá summary của 1 dòng | 1 (`10.3390/app16052244`) | Quality summary fail | Summary missing = 1 (quality fail) | Re-run cleaning từ raw |
| `inject_noise` | Prefix `zzzz ` vào summary 2 dòng | 2 (`10.21079/11681/50309`, `10.21203/rs.3.rs-10178277/v1`) | Summary nhiễu → retrieval context xấu | Không làm hỏng metric (paper không thuộc test set) | Re-run cleaning từ raw |
| `truncate_title` | Cắt title còn 20 ký tự | 2 (`10.54254/2753-8818/2026.dl34055`, `10.55041/isjem07213`) | Title thiếu → lookup chính xác có thể fail | Không đổi metric | Re-run cleaning từ raw |
| `old_date` | Đẩy `published` về `2010-01-01` + tính lại `age_days` | 2 (`10.2196/preprints.106157`, `10.3390/buildings16132637`) | Freshness stale | Freshness stale 2 (age 6061 ngày) | Re-run cleaning từ raw |
| `duplicate_rows` | Chèn 1 dòng trùng (suffix `_dup`) | 1 | Duplicate bị phát hiện | Quality `paper_id` duplicate vẫn 0 (do `_dup` khác ID) — giới hạn của check | Re-run cleaning từ raw |

Corruption log:

- Đường dẫn: `data/results/corruption_log.json`
- Trạng thái: Có
- Nhận xét: Log đủ 6 loại corruption, mỗi mục ghi `type`, `parameter`, danh sách `paper_ids` cụ thể và count trước/sau; đủ để truy vết từng dòng bị ảnh hưởng về quality signal và metric change.

Giải thích cách repair đảm bảo dữ liệu được phục hồi từ nguồn đáng tin cậy thay vì chỉ che kết quả lỗi:

Repair không sửa tay `papers_clean_corrupted.csv` hay answers. Thay vào đó `corruption_flow.py` gọi lại `build_clean_dataframe(raw_records, run_date)` với raw snapshot `data/raw/crossref_records.json` (nguồn gốc, không đổi giữa các phase) — cùng đường cleaning như baseline. Kết quả là repaired dataset được tái dựng độc lập với corrupted: đủ 24 dòng, đúng `paper_id`, đúng `published`/`age_days`. Nhờ vậy mức phục hồi metric là hệ quả của việc dữ liệu nguồn tốt, không phải của việc vá kết quả.

## 10. So sánh baseline, corrupted và repaired

| Metric/signal            | Baseline | Corrupted | Repaired | Thay đổi do corruption | Mức phục hồi | Nhận xét   |
| ------------------------ | -------: | --------: | -------: | -----------------------: | --------------: | ------------ |
| `retrieval_hit_rate`   |  1.000 |  0.800 |  1.000 | -0.200 | +0.200 (100%) | 2/10 câu mất ground-truth paper vì drop_latest; repair khôi phục đủ |
| `mean_token_f1`        |  1.000 |  0.800 |  1.000 | -0.200 | +0.200 (100%) | F1 0 tại 2 câu miss; các câu còn lại vẫn 1.0 |
| `judge_accuracy`       |  1.000 |  0.800 |  1.000 | -0.200 | +0.200 (100%) | Judge fallback heuristic trên 2 câu miss |
| `mean_judge_score`     |  5 |  4.200 |  5 | -0.800 | +0.800 (100%) | Điểm 0 cho 2 câu miss kéo trung bình xuống |
| Quality checks pass/fail |  pass |  fail |  pass | fail | pass (100%) | Corrupted: summary missing 1 + freshness stale 2 |
| Freshness status         |  fresh |  stale (2) |  fresh | stale 2 | fresh (100%) | `old_date` đẩy 2 dòng về 2010-01-01; repair khôi phục |

Nêu ít nhất hai kết luận có quan hệ nhân quả được hỗ trợ bởi artifacts:

1. **`drop_latest` xoá 2 paper nằm trong test set** (`10.2118/234689-pa` ở q1, `10.47576/2949-1894.2026.7.7.023` ở q9 — xác nhận trong `corruption_log.json` ∩ `test_set.json` ground_truth_doc_ids) → quality row count 24→21 → `retrieval_hit_rate` 1.0→0.8 và `mean_token_f1` 1.0→0.8. Đây là cơ chế sụt giảm duy nhất có evidence: 2 câu còn miss đều trỏ vào paper đã bị xoá.
2. **Repair re-run cleaning từ raw snapshot** → `papers_clean_repaired.csv` khôi phục 24 dòng, summary đủ, freshness sạch (`quality_report_repaired.json` pass, `freshness_report_repaired.json` fresh) → agent retrieval + answer khôi phục về baseline (hit 1.0, F1 1.0, judge 1.0). Phục hồi 100% vì raw snapshot không hề bị corrupt.

## 11. Vấn đề tích hợp quan trọng

- **Triệu chứng:** Khi chạy corruption flow, freshness report của corrupted vẫn báo `is_fresh = true` dù 2 dòng đã bị đẩy `published` về `2010-01-01`; báo cáo comparison không cho thấy dấu hiệu dữ liệu cũ.
- **Nguyên nhân:** Corruption `old_date` chỉ sửa cột `published` nhưng không tính lại `age_days`; quality/freshness checks đọc `age_days` nên không phát hiện dòng cũ. Ngoài ra, corruption ban đầu còn chèn duplicate bằng cách copy lại chính các dòng đã bị drop (đang không còn trong dataframe) nên danh sách duplicate rỗng — log không phản ánh đúng ý định.
- **Cách xử lý:** Thêm `_recompute_age_days()` tính lại `age_days` từ `published` ngay sau bước `old_date`, và `_sync_summary_chars()` re-sync `summary_chars` sau blank/noise; viết lại cơ chế chọn window (mỗi corruption dùng khoảng dòng riêng không chồng lấp) và duplicate lấy từ tập dòng còn tồn tại, thêm guard chống window underflow.
- **Cách xác minh:** `run_data_quality_checks` trên corrupted trả `freshness.passed = False` với `stale_count = 2`; `freshness_report_corrupted.json` có `is_fresh = false`, `oldest_published = 2010-01-01`; `corruption_log.json` ghi đủ 6 loại với paper_ids khác rỗng. Toàn bộ flow chạy lại từ đầu cho kết quả khớp.

## 12. Giới hạn và hướng cải thiện

| Giới hạn hiện tại | Ảnh hưởng   | Hướng cải thiện có thể kiểm chứng |
| --------------------- | -------------- | ----------------------------------------- |
| Judge LLM fallback heuristic khi model free không hỗ trợ structured output | `judge_accuracy`/`mean_judge_score` dựa trên token F1 thay vì LLM judge thực sự | Dùng model có tool/structured output (vd Gemini/OpenAI trả phí) rồi so judge LLM vs heuristic trên cùng test set |
| Ragas bị skip (cần `RUN_RAGAS=1`) | Thiếu metric faithfulness/answer relevancy | Bật `RUN_RAGAS=1` với provider hỗ trợ, ghi kết quả vào metrics |
| 2/10 câu hỏi dính `drop_latest` — sụt giảm chủ yếu từ 1 loại corruption | Tác động của các loại khác (noise, truncate) chưa được cô lập đo | Tạo corruption từng loại một và đo delta riêng; hoặc giữ test set tránh paper bị drop |
| Dataset nhỏ (24 records, k=4) | Metric có phương sai cao, kết luận dễ quá mức | Tăng `max_results`, xây test set lớn hơn, chạy nhiều seed |
| Quality check `duplicate_rows` không bắt `_dup` suffix | Duplicate chèn bằng ID biến thể lọt qua check | Normalize ID (strip suffix) trước khi check duplicate |

## 13. Checklist trước khi nộp

- [x] Thông tin nhóm và repository chính xác.
- [x] Phân công khớp với module, artifact và kết quả thực tế.
- [x] Lệnh tái hiện đã được chạy lại trên phiên bản dùng để nộp.
- [x] Baseline, corrupted và repaired dùng cùng evaluation set.
- [x] Bảng metrics khớp với các file trong `data/results/`.
- [x] Quality/freshness conclusions khớp với `data/quality/`.
- [x] Các đường dẫn báo cáo và artifact truy cập được.
- [x] Mỗi thành viên đã hoàn thành báo cáo vai trò riêng.
- [x] Không có `.env`, API key, token hoặc secret trong source, report, log hay ảnh.
