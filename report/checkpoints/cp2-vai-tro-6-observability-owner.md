# CP2 — Vai trò 6: Observability owner (Nhóm 6 người)

> Checkpoint: `01:05–01:35` · Pass: `test_set.json`, embedding manifest và collection baseline tồn
> tại; semantic search, exact lookup và agent đều trả về kết quả có nguồn.

## 1. Audit embedding manifest, collection name và document count

Chạy `LocalEmbeddingIndex.build()` trên `data/clean/papers_clean.csv` (code có sẵn ở
`retrieval/index.py`, không thuộc phạm vi mình sửa) và đọc lại manifest ghi ra:

```json
{
  "backend": "chroma",
  "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
  "collection_name": "papers-baseline",
  "persist_path": "data/chroma",
  "document_count": 24
}
```

Có thể audit được: `document_count` (24) khớp đúng số dòng `papers_clean.csv` (24) — không có
document nào bị rơi giữa cleaning và index. `collection_name` = `papers-baseline`, đúng tên baseline
riêng biệt trong `settings.baseline_collection_name` (không lẫn với `papers-corrupted`/
`papers-repaired` sẽ dùng sau).

## 2. Ghi baseline quality/freshness signals để đối chiếu sau corruption

Baseline signals đã có từ CP1 (`data/quality/quality_report_baseline.json`,
`data/quality/freshness_report.json`) — đây chính là mốc dùng để so sánh khi corruption chạy ở CP5:

| Signal | Baseline |
| --- | --- |
| `passed` (tổng quality) | `true` |
| `paper_id` null/duplicate | 0 / 0 |
| `duplicate_rows` | 0 |
| `stale_rows` / `total_rows` | 0 / 24 |
| `is_fresh` | `true` |

Không cần chạy lại ở CP2 — giữ nguyên làm baseline reference; sẽ chạy lại đúng 2 hàm này trên
corrupted dataframe ở CP5 để có bộ số liệu so sánh.

## 3. Chuẩn bị khuôn `phase1_report.md`

Đã implement đầy đủ `src/observability/reporting.py::generate_phase1_report()`:

- Section "Source summary" (render từ dict tuỳ ý caller truyền — `source_api`, `source_query`,
  `source_filter`, số raw/clean records).
- Section "Evaluation metrics" (mọi field trong `metrics` trừ `ragas`, in riêng dòng `ragas`).
- Section "Data quality" (dòng tổng `passed` + bảng chi tiết từng check từ `quality["checks"]`).
- Section "Freshness" (bảng key-value từ `freshness`).

Hàm chỉ *render* — chưa gọi thật ở CP2 vì chưa có `metrics` thật (evaluate_pipeline chạy ở CP3).
Khuôn đã sẵn sàng, CP3 chỉ cần truyền đúng 4 dict đầu vào là ra `data/reports/phase1_report.md`.

Cũng đã implement `generate_corruption_report()` cùng file (dùng ở CP6) — viết cùng lúc vì cùng
thuộc file `reporting.py` do vai trò 6 sở hữu, tránh phải mở lại file nhiều lần; chưa gọi vì chưa có
metrics corrupted/repaired.
