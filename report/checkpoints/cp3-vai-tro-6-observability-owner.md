# CP3 — Vai trò 6: Observability owner (Nhóm 6 người)

> Checkpoint: `01:35–02:00` · Pass: `baseline_metrics.json`, answers, quality/freshness và
> `phase1_report.md` tồn tại; team giải thích được ít nhất một hit/miss bằng artifact.

## 1. Run quality, freshness và `generate_phase1_report`

Chạy lại `run_data_quality_checks(df, settings, "baseline")` và `build_freshness_report(...)` trên
đúng `data/clean/papers_clean.csv` (kết quả giống hệt CP1 vì dữ liệu clean chưa đổi — xem
[cp1-vai-tro-6-observability-owner.md](cp1-vai-tro-6-observability-owner.md)), sau đó gọi
`generate_phase1_report()` (vừa implement ở CP2) với 4 input thật:

- `source_summary`: `source_api`, `source_query`, `source_filter` (từ `Settings`), `raw_records`
  (24, đếm từ `crossref_records.json`), `clean_records` (24, `len(df)`).
- `metrics`: `bundle.summary` thật từ `evaluate_pipeline()` (vai trò 5 vừa chạy ở CP3).
- `quality`, `freshness`: 2 report vừa chạy lại ở trên.

Kết quả: `data/reports/phase1_report.md` (xem file thật trong repo) — 4 section: Source summary,
Evaluation metrics, Data quality (bảng 6 check), Freshness.

## 2. Đối chiếu report với JSON/CSV thật

| Trong report | Trong artifact JSON | Khớp? |
| --- | --- | --- |
| `retrieval_hit_rate = 1.000` | `data/results/baseline_metrics.json` → `1.0` | Có |
| `clean_records = 24` | `len(pd.read_csv(papers_clean.csv))` | Có (24 dòng) |
| Data quality "Overall passed: yes" | `data/quality/quality_report_baseline.json` → `"passed": true` | Có |
| Freshness `is_fresh = yes` | `data/quality/freshness_report.json` → `"is_fresh": true` | Có |

Report không tự chế số — mọi giá trị trong markdown đều truyền trực tiếp từ dict trả về của
`evaluate_pipeline`/`run_data_quality_checks`/`build_freshness_report`, không hard-code.

## 3. Baseline signals/metrics làm mốc sau nghỉ (CP4)

Ghi lại làm điểm neo để so sánh sau corruption (CP5–CP6):

| Signal/metric | Baseline |
| --- | --- |
| `retrieval_hit_rate` | 1.000 |
| `mean_token_f1` | 1.000 |
| `judge_accuracy` (heuristic fallback, xem lưu ý vai trò 5) | 1.000 |
| `mean_judge_score` | 5 |
| Quality `passed` | true (6/6 check) |
| Freshness `is_fresh` | true (0/24 stale) |

Baseline "sạch tuyệt đối" trên mọi trục — điều này làm cho corruption ở CP5 dễ chứng minh nhân quả:
bất kỳ suy giảm nào ở các con số trên sau corruption đều có thể quy trực tiếp cho corruption, không
lẫn với nhiễu sẵn có.

## 4. Việc còn lại

`generate_corruption_report()` đã implement sẵn (cùng lúc với `generate_phase1_report` ở CP2) nhưng
chưa gọi — cần `corrupted_metrics`/`repaired_metrics`/`corrupted_quality`/... thật từ CP5–CP6, phụ
thuộc `src/ingestion/corruption.py` (vai trò 3) hiện vẫn là `NotImplementedError`.
