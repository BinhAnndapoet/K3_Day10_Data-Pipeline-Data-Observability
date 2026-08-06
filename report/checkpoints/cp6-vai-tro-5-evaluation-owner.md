# CP6 — Vai trò 5: Evaluation owner (Nhóm 6 người)

> Checkpoint: `03:15–04:00` · Pass: repaired artifacts và comparison report có
> baseline–corrupted–repaired/delta; repo không có secret; demo dùng artifact thật.
> **Blocker ngoài phạm vi:** cần repaired dataframe (vai trò 3 re-run cleaning từ raw) và
> `corruption_flow.py` (vai trò lead) hoàn tất trước. Ghi chú thiết kế sẵn, chạy ngay khi có dữ liệu.

## 1. Evaluate repaired — cùng pattern đã dùng cho baseline/corrupted

```python
repaired_index = LocalEmbeddingIndex.build(
    repaired_df, settings, embeddings_output_path=settings.paths.repaired_embeddings_json,
)  # collection "papers-repaired"

evaluate_pipeline(
    settings=settings, index=repaired_index,
    test_set_path=settings.paths.eval_testset,   # vẫn cùng test set đã khoá từ CP1
    metrics_output_path=settings.paths.repaired_metrics,
    answers_output_path=settings.paths.repaired_answers,
)
```

Theo shared rule "repair bằng cách chạy lại từ raw/source đáng tin" — `repaired_df` phải là kết quả
của `build_clean_dataframe(raw_records, run_date)` chạy lại từ `data/raw/crossref_records.json`
(nguồn gốc, không đổi), **không** phải sửa tay `papers_clean_corrupted.csv`. Việc xác minh điều này
thuộc vai trò 3/ingest, nhưng evaluation owner cần biết để không "chấp nhận" một repaired dataset
build sai cách.

## 2. Tính delta 3 trạng thái và giải thích bằng answers thực tế

Với mỗi metric (`retrieval_hit_rate`, `mean_token_f1`, `judge_accuracy`, `mean_judge_score`), so:

```
delta_corruption = corrupted[metric] - baseline[metric]
delta_repair     = repaired[metric]  - corrupted[metric]
```

Với từng câu hỏi bị miss ở corrupted (đã liệt kê ở CP5 mục 2), kiểm tra lại đúng `id` đó trong
`repaired_answers.json`:

- Nếu `retrieval_hit` quay lại `true` và `answer` khớp `ground_truth` như baseline → **phục hồi**.
- Nếu vẫn `false`/sai → **chưa phục hồi**, cần nêu nguyên nhân cụ thể (vd. record đó vốn không có
  trong raw nữa, hoặc `paper_id` đổi khi rebuild khiến `ground_truth_doc_ids` cũ không còn khớp).

Không làm tròn hoặc suy diễn "đã phục hồi" nếu số liệu thật chưa về đúng baseline.

## 3. Chuẩn bị một hit/miss tiêu biểu để demo trung thực

Ưu tiên chọn đúng ví dụ đã dùng xuyên suốt CP3 (`q1`, câu hỏi `authors` về paper SafeRAG) nếu nó có
nằm trong tập bị corruption tác động — kể chuyện: baseline hit → corrupted miss (kèm answer sai thật)
→ repaired hit trở lại (kèm answer đúng thật). Nếu ví dụ này không bị corruption chạm tới, chọn ví dụ
khác dựa trên `corruption_log.json` thay vì tự dựng kịch bản.

## 4. Blocker

| Cần | Trạng thái |
| --- | --- |
| `repaired_df` (re-run `cleaning.build_clean_dataframe` từ raw) | Phụ thuộc `corruption_flow.py` (vai trò lead) |
| `data/results/repaired_metrics.json`, `repaired_answers.json` | Chưa tồn tại |

Mục 1–3 chạy ngay bằng `evaluate_pipeline()` đã có sẵn, không cần code thêm phía evaluation.
