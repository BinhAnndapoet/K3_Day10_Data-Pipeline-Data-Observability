# CP0 — Vai trò 6: Observability owner (Nhóm 6 người)

> Checkpoint: `00:00–00:30` · Phạm vi phụ trách: `src/observability/` · `data/quality/`
> Mục tiêu CP0: **đọc và thiết kế**, chưa viết code. Quality/freshness checks thật sự chỉ chạy được
> sau khi có dữ liệu clean thật (CP1) và baseline metrics (CP3).

## 1. Liệt kê artifact phải có sau baseline flow và corruption flow

Dựa theo `src/core/config.py::Paths` (đường dẫn đã cấu hình sẵn, không hard-code) và
`report/README.md` mục 7 "Cách xác minh bài làm".

### Sau baseline (CP3 — `uv run python script/run_phase1.py`)

| Artifact | Đường dẫn (`settings.paths.*`) | Sinh ra bởi |
| --- | --- | --- |
| Data quality results | `quality_dir` = `data/quality/` | `run_data_quality_checks()` — mình implement |
| Freshness report | `freshness_report` = `data/quality/freshness_report.json` | `build_freshness_report()` — mình implement |
| Baseline report (markdown) | `baseline_report` = `data/reports/phase1_report.md` | `generate_phase1_report()` — mình implement |
| (đầu vào cần đọc, không phải mình tạo) | `data/results/baseline_metrics.json`, `baseline_answers.json` | `evaluate_pipeline()` (vai trò 5) |

### Sau corruption flow (CP5–CP6 — `uv run python script/run_corruption_flow.py`)

| Artifact | Đường dẫn | Sinh ra bởi |
| --- | --- | --- |
| Corruption log | `corruption_log` = `data/results/corruption_log.json` | `corrupt_clean_dataframe()` (vai trò 3) |
| Quality/freshness — corrupted | `quality_dir` (report riêng theo `report_name`), freshness report riêng | `run_data_quality_checks()` / `build_freshness_report()` chạy lại trên corrupted dataframe |
| Quality/freshness — repaired | tương tự, path/tên báo cáo riêng | chạy lại trên repaired dataframe |
| Comparison report (markdown) | `comparison_report` = `data/reports/corruption_report.md` | `generate_corruption_report()` — mình implement |
| (đầu vào cần đọc) | `corrupted_metrics.json`, `repaired_metrics.json` + các file `*_answers.json` tương ứng | `evaluate_pipeline()` (vai trò 5), chạy lại 2 lần |

**Nguyên tắc xuyên suốt (đã ghi trong đề bài):** báo cáo/artifact của baseline, corrupted và
repaired phải nằm ở path/tên riêng biệt — không được ghi đè lên baseline khi chạy corruption flow.

## 2. Định nghĩa signals

Theo đúng pseudo-code trong `src/observability/quality.py`:

| Signal | Cách đo | Mục đích |
| --- | --- | --- |
| Row count | `len(df)` | Phát hiện record bị drop bất thường (vd. corruption "xoá latest records") |
| Null / thiếu `paper_id` | `df["paper_id"].isna().sum()` | `paper_id` là document identity — không được null |
| Duplicate `paper_id` | `df["paper_id"].duplicated().sum()` | Phát hiện corruption "thêm duplicate rows"; unique là điều kiện bắt buộc |
| Null `title` | `df["title"].isna().sum()` | Title rỗng → agent không trả lời được câu hỏi `authors`/`date`/`categories` (exact lookup theo title trong `qa.py` sẽ fail) |
| Độ dài `summary` | ví dụ `summary_chars` hoặc `len(summary)` trung bình / số dòng dưới ngưỡng | Phát hiện corruption "blank summary" / "add noise" — summary quá ngắn hoặc bất thường |
| `age_days` / freshness | so `age_days` với `settings.freshness_threshold_days` (=180) | Phát hiện corruption "làm stale publication date"; đếm `stale_rows`, tính `is_fresh` |
| Source timestamp | thời điểm raw response được fetch (so với `run_date` dùng để tính `age_days` trong `cleaning.py`) | Biết dữ liệu được coi là "mới" tính từ mốc thời gian nào, tránh nhầm freshness với "ngày hiện tại" |

`build_freshness_report()` cần trả về đúng payload theo docstring: `latest_published`,
`oldest_published`, `stale_rows`, `total_rows`, `is_fresh`.

## 3. Phác thảo report chứng minh data xấu làm RAG kém đi

### `phase1_report.md` (baseline) — nội dung dự kiến

1. **Source summary** — nguồn Crossref, số record raw/clean, thời điểm fetch.
2. **Evaluation metrics** — bảng `retrieval_hit_rate`, `mean_token_f1`, `judge_accuracy`,
   `mean_judge_score` (đọc từ `baseline_metrics.json`, không tự chế số).
3. **Data quality** — kết quả từng check (row count, null, duplicate) pass/fail.
4. **Freshness** — `latest_published`/`oldest_published`/`stale_rows`/`is_fresh`.

### `corruption_report.md` (so sánh) — nội dung dự kiến

1. Bảng so sánh 3 cột **baseline vs corrupted vs repaired** cho từng metric + quality + freshness
   (đọc từ `baseline_metrics.json`, `corrupted_metrics.json`, `repaired_metrics.json` và các quality/
   freshness report tương ứng — tất cả evaluate trên **cùng một `test_set.json`**).
2. Tối thiểu 2 chuỗi nhân quả có bằng chứng, đúng theo mẫu `group_report.md` mục 10:
   - `[Loại corruption]` → `[quality/freshness signal đổi]` → `[metric agent đổi]`
     (vd: xoá/blank summary → `summary` null tăng, `text_for_embedding` nghèo → `retrieval_hit_rate`
     và `mean_token_f1` giảm với câu hỏi `question_type=summary`).
   - `[Repair]` → `[signal phục hồi]` → `[metric phục hồi hoặc chưa phục hồi, nêu rõ]`.
3. Không kết luận "corruption có tác động" nếu số liệu thật không cho thấy thay đổi.

## 4. Artifact sẽ bàn giao & phụ thuộc

| Việc | Trạng thái CP0 | Sẵn sàng thật sự khi nào |
| --- | --- | --- |
| `run_data_quality_checks`, `build_freshness_report` | Chỉ đọc pseudo-code + định nghĩa signal ở trên, chưa code | Implement từ CP1 (áp bảng signal lên dataframe clean thật) |
| `generate_phase1_report` | Đã phác outline ở trên | Implement/verify ở CP3, sau khi có `baseline_metrics.json` thật |
| `generate_corruption_report` | Đã phác outline ở trên | Implement ở CP6, sau khi có đủ 3 bộ metrics/quality/freshness |

**Phụ thuộc chặn (blocker):** cần vai trò 3 hoàn thành `cleaning.py` (CP1) để có `age_days`,
`text_for_embedding` thật; cần vai trò 5 hoàn thành `build_test_set` + chạy `evaluate_pipeline`
(CP2–CP3) để có metrics thật đối chiếu trong report.
