# Phase 1 Baseline Report

## Source summary

| Field | Value |
| --- | --- |
| `mode` | loaded_from_snapshot |
| `source` | Crossref REST API |
| `raw_records` | crossref_records.json |
| `record_count` | 24 |
| `fetched_at` | n/a (snapshot) |

## Evaluation metrics

| Field | Value |
| --- | --- |
| `samples` | 10 |
| `retrieval_hit_rate` | 1.000 |
| `mean_token_f1` | 1.000 |
| `judge_accuracy` | 1.000 |
| `mean_judge_score` | 5 |

Ragas: `{'skipped': 'Set RUN_RAGAS=1 to enable the slower Ragas pass.'}`

## Data quality

Overall passed: **yes** (`baseline`, 24 rows, generated 2026-08-06T04:53:40.901640+00:00)

| Check | Passed | Detail |
| --- | --- | --- |
| `row_count` | yes | row_count=24 |
| `paper_id` | yes | null_count=0, duplicate_count=0 |
| `title` | yes | missing_count=0 |
| `summary` | yes | missing_count=0, short_count=0, min_chars=40 |
| `duplicate_rows` | yes | subset=['paper_id', 'title'], duplicate_rows=0 |
| `freshness` | yes | threshold_days=180, stale_count=0, unknown_count=0 |

## Freshness

| Field | Value |
| --- | --- |
| `latest_published` | 2026-08-01 |
| `oldest_published` | 2026-02-12 |
| `stale_rows` | 0 |
| `total_rows` | 24 |
| `freshness_threshold_days` | 180 |
| `is_fresh` | yes |
