# Báo cáo Baseline (Phase 1)

## Tóm tắt nguồn dữ liệu

| Trường | Giá trị |
| --- | --- |
| `mode` | loaded_from_snapshot |
| `source` | Crossref REST API |
| `record_count` | 24 |

## Chỉ số đánh giá

| Trường | Giá trị |
| --- | --- |
| `samples` | 10 |
| `retrieval_hit_rate` | 1.000 |
| `mean_token_f1` | 1.000 |
| `judge_accuracy` | 1.000 |
| `mean_judge_score` | 5 |

Ragas: `{'skipped': 'Set RUN_RAGAS=1 to enable the slower Ragas pass.'}`

## Chất lượng dữ liệu

Tổng quan đạt: **có** (`baseline`, 24 dòng, tạo lúc 2026-08-06T04:53:40.901640+00:00)

| Kiểm tra | Đạt | Chi tiết |
| --- | --- | --- |
| Số dòng | có | row_count=24 |
| Mã bài báo (paper_id) | có | null_count=0, duplicate_count=0 |
| Tiêu đề | có | missing_count=0 |
| Tóm tắt | có | missing_count=0, short_count=0, min_chars=40 |
| Dòng trùng lặp | có | subset=['paper_id', 'title'], duplicate_rows=0 |
| Độ mới (freshness) | có | threshold_days=180, stale_count=0, unknown_count=0 |

## Độ mới của dữ liệu (Freshness)

| Trường | Giá trị |
| --- | --- |
| `latest_published` | 2026-08-01 |
| `oldest_published` | 2026-02-12 |
| `stale_rows` | 0 |
| `total_rows` | 24 |
| `freshness_threshold_days` | 180 |
| `is_fresh` | có |
