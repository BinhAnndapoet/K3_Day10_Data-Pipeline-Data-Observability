# CP5 — Vai trò 5: Evaluation owner (Nhóm 6 người)

> Checkpoint: `02:15–03:15` · Pass: corruption log, corrupted clean/index/answers/metrics/quality và
> report có đủ; baseline không bị ghi đè.
> **Blocker ngoài phạm vi:** `src/ingestion/corruption.py` (vai trò 3) và
> `src/pipelines/corruption_flow.py` (vai trò lead) vẫn `NotImplementedError` tại thời điểm viết ghi
> chú này → chưa có `data/clean/papers_clean_corrupted.csv` để evaluate. Đây là ghi chú **thiết kế
> sẵn**, chạy được ngay khi corrupted dataframe tồn tại, không cần sửa gì thêm ở phía evaluation.

## 1. Kế hoạch evaluate corrupted (đã sẵn sàng chạy)

Không cần thay đổi `evaluate_pipeline()` — hàm đã tổng quát theo `index`/`test_set_path`/output
paths, chỉ cần trỏ đúng artifact corrupted:

```python
corrupted_index = LocalEmbeddingIndex.build(
    corrupted_df, settings, embeddings_output_path=settings.paths.corrupted_embeddings_json,
)  # tự động đặt tên collection "papers-corrupted" qua _derive_collection_name()

evaluate_pipeline(
    settings=settings, index=corrupted_index,
    test_set_path=settings.paths.eval_testset,      # CÙNG test set đã khoá từ CP1/CP2
    metrics_output_path=settings.paths.corrupted_metrics,
    answers_output_path=settings.paths.corrupted_answers,
)
```

Điểm mấu chốt: `test_set_path` giữ nguyên `settings.paths.eval_testset` — không build lại test set,
đúng nguyên tắc "dùng cùng evaluation set cho baseline/corrupted/repaired".

## 2. So answer/metric với baseline — tìm case xấu đi có evidence

Sau khi có `data/results/corrupted_metrics.json` và `corrupted_answers.json`, đối chiếu từng `id`
với `data/results/baseline_answers.json` (đã có từ CP3):

- Lọc các câu mà `retrieval_hit` chuyển từ `true` (baseline) → `false` (corrupted), hoặc `token_f1`
  giảm mạnh.
- Ưu tiên chọn ví dụ mà `ground_truth_doc_ids` của câu đó trùng với record bị corruption log ghi
  nhận đã tác động (blank summary / drop / duplicate...) — để chuỗi nhân quả "corruption → miss" có
  bằng chứng trực tiếp, không suy đoán.

## 3. Evaluator không được silently fallback thành "success" giả

Đã kiểm tra code hiện có (không cần sửa) đảm bảo điều này đúng ngay cả khi dữ liệu hỏng nặng:

- `qa.py::answer_question`: nếu `index.search()` không trả kết quả nào, trả lời cố định
  `"I don't know from the indexed corpus."` — không bịa câu trả lời.
- `metrics.py::_judge_answer`: khi không có credential LLM, heuristic fallback dùng `token_f1` thật
  của câu trả lời đó, **không** mặc định `correct=True`. Với câu `"I don't know..."` so với ground
  truth thật, `token_f1` gần như luôn `< 0.5` → `score=1`, `correct=False` — đúng hành vi mong muốn
  (thất bại phải hiện ra ở metric, không bị che).
- `retrieval_hit` tính trực tiếp từ `retrieved_doc_ids`, không có nhánh nào gán `True` mặc định.

→ Không cần patch gì thêm cho yêu cầu "evaluator không silently fallback"; chỉ cần xác nhận lại bằng
số liệu thật sau khi corrupted data có sẵn.

## 4. Blocker cụ thể

| Cần | Trạng thái | Ai sở hữu |
| --- | --- | --- |
| `corrupt_clean_dataframe()` → `data/clean/papers_clean_corrupted.csv/json` | `NotImplementedError` | Vai trò 3 (Cleaning & corruption owner) |
| `data/results/corruption_log.json` | Chưa tồn tại | Vai trò 3 |
| Entrypoint `uv run python script/run_corruption_flow.py` | `NotImplementedError` (`pipelines/corruption_flow.py`) | Vai trò lead |

Khi 1 trong 3 mục trên sẵn sàng, mục 1–3 phía trên chạy được ngay không cần chỉnh sửa thêm.
