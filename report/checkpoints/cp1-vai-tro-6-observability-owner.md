# CP1 — Vai trò 6: Observability owner (Nhóm 6 người)

> Checkpoint: `00:30–01:05` · Pass: clean CSV/JSON đọc được, `paper_id` unique, `text_for_embedding`
> và `age_days` có mặt, count/lý do record bị loại có thể truy vết.
> CP1 là mốc bắt đầu **viết code thật** cho vai trò này (khác CP0 chỉ đọc/thiết kế), vì `cleaning.py`
> đã hoàn thành và dữ liệu clean thật đã tồn tại (`data/clean/papers_clean.csv`).

## 1. Đã implement `src/observability/quality.py`

Cả hai hàm trong `src/observability/quality.py` đã được viết đầy đủ, thay cho `NotImplementedError`:

### `run_data_quality_checks(df, settings, report_name) -> dict`

6 check, đúng theo pseudo-code gốc + danh sách signal đã định nghĩa ở CP0:

| Check | Cách đo | Điều kiện pass |
| --- | --- | --- |
| `row_count` | `len(df)` | `> 0` |
| `paper_id` | null count + duplicate count trên cột `paper_id` | cả hai `== 0` |
| `title` | số dòng title rỗng/toàn khoảng trắng | `== 0` |
| `summary` | số dòng rỗng + số dòng ngắn hơn `MIN_SUMMARY_CHARS=40` | `missing_count == 0` |
| `duplicate_rows` | duplicate trên subset `(paper_id, title)` | `== 0` |
| `freshness` | số dòng có `age_days > freshness_threshold_days` (180) | `stale_count == 0` |

Kết quả tổng hợp: `{report_name, generated_at, row_count, passed, checks}`, ghi ra
`data/quality/quality_report_{report_name}.json` (dùng `settings.paths.quality_dir`, không
hard-code path). `passed` tổng = AND của toàn bộ 6 check — cho phép nhìn nhanh dataset có "sạch" hay
không mà vẫn giữ chi tiết từng check để debug.

### `build_freshness_report(df, settings, report_path) -> dict`

Trả về đúng payload đã thiết kế ở CP0: `latest_published`, `oldest_published`, `stale_rows`,
`total_rows`, `freshness_threshold_days`, `is_fresh` (= `total_rows > 0 and stale_rows == 0`).
`report_path` do caller truyền vào (ví dụ `settings.paths.freshness_report` cho baseline, path riêng
cho corrupted/repaired) — đúng nguyên tắc "dùng path riêng cho ba trạng thái, không ghi đè baseline".

Cả hai hàm chỉ dùng cột đã có sẵn trong clean schema (`paper_id`, `title`, `summary`, `published`,
`age_days`) — không giả định thêm cột nào ngoài contract cleaning đã công bố.

## 2. `age_days`/`published` thay vì ngày hiện tại giả định

Không dùng `datetime.now()` để tính freshness trong quality module — `age_days` đã được
`cleaning.py` tính sẵn tại thời điểm `run_date` (khi ingest chạy), nên freshness ở đây phản ánh đúng
độ mới tại lúc pipeline chạy, không lệch nếu report được đọc lại sau này.

## 3. Quality report đầu tiên — evidence baseline

Chạy thử `run_data_quality_checks` và `build_freshness_report` trực tiếp trên
`data/clean/papers_clean.csv` (dữ liệu clean thật, không phải dữ liệu giả) để có bằng chứng đầu
tiên trước khi CP3 chạy toàn bộ `phase1.py`. Kết quả cụ thể (số liệu thật) được ghi trong mục 4.

## 4. Kết quả chạy thật (evidence)

Chạy `run_data_quality_checks(df, settings, "baseline")` và `build_freshness_report(...)` trực tiếp
trên `data/clean/papers_clean.csv` (24 dòng, output của `cleaning.py` đã commit). Artifact:

- `data/quality/quality_report_baseline.json`
- `data/quality/freshness_report.json`

| Check | Kết quả thật |
| --- | --- |
| `row_count` | 24 |
| `paper_id` null/duplicate | 0 / 0 |
| `title` missing | 0 |
| `summary` missing/short (`< 40` ký tự) | 0 / 0 |
| `duplicate_rows` (subset `paper_id`+`title`) | 0 |
| `freshness` stale (`age_days > 180`) | 0 |
| **Tổng `passed`** | **true** |

| Freshness | Giá trị thật |
| --- | --- |
| `latest_published` | `2026-08-01` |
| `oldest_published` | `2026-02-12` |
| `stale_rows` / `total_rows` | 0 / 24 |
| `is_fresh` | `true` |

Nhận xét: dataset baseline sạch tuyệt đối trên cả 6 check — hợp lý vì `source_filter` trong
`core/config.py` đã lọc Crossref theo `from-pub-date` trong 180 ngày gần nhất ngay từ lúc fetch, nên
baseline gần như chắc chắn fresh. Đây chính là báo cáo quality **baseline** — sau khi vai trò 3 chạy
corruption ở CP5 (làm stale date, blank summary, duplicate rows...), chạy lại đúng 2 hàm này trên
corrupted dataframe sẽ cho `passed=false` và `is_fresh=false`, dùng để chứng minh corruption tác
động tới data quality (nối tiếp vào `corruption_report.md` ở CP6).

Script chạy thử là ad-hoc (không phải phần pipeline chính thức — `phase1.py` do vai trò lead
implement ở CP3 mới là nơi gọi hai hàm này trong luồng end-to-end thật).
