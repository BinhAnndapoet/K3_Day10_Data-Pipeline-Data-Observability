# CP3 — Vai trò 5: Evaluation owner (Nhóm 6 người)

> Checkpoint: `01:35–02:00` · Pass: `baseline_metrics.json`, answers, quality/freshness và
> `phase1_report.md` tồn tại; team giải thích được ít nhất một hit/miss bằng artifact.

## 1. Chạy evaluator tạo `answers` và `baseline_metrics.json`

`phase1.py` (vai trò lead) vẫn là stub nên chưa có entrypoint chính thức
`uv run python script/run_phase1.py`. Để có artifact thật cho CP3 (thay vì chờ), gọi trực tiếp hàm
đã implement sẵn `evaluate_pipeline()` (`src/evaluation/metrics.py`, không sửa gì) trên index +
test set đã build ở CP2:

```python
evaluate_pipeline(
    settings=settings, index=index,
    test_set_path=settings.paths.eval_testset,
    metrics_output_path=settings.paths.baseline_metrics,
    answers_output_path=settings.paths.baseline_answers,
)
```

Kết quả ghi thật ra `data/results/baseline_metrics.json` và `data/results/baseline_answers.json`.

## 2. Số liệu baseline thật

| Metric | Giá trị |
| --- | --- |
| `samples` | 10 |
| `retrieval_hit_rate` | **1.000** |
| `mean_token_f1` | **1.000** |
| `judge_accuracy` | **1.000** |
| `mean_judge_score` | **5** |
| `ragas` | skipped (`RUN_RAGAS` chưa bật) |

**0 miss / 10 câu** — baseline đạt điểm tuyệt đối. Đây là kết quả hợp lý, không phải dấu hiệu đo sai:
`testset.py::_ground_truth` lấy `ground_truth` trực tiếp từ đúng cột (`authors_joined`, `published`,
`categories_joined`, `first_sentence(summary)`) mà `qa.py::_extract_answer` cũng dùng để trả lời —
nên khi retrieval đúng document (đã xác nhận ở CP2: 10/10 ID resolve), câu trả lời gần như khớp
verbatim với ground truth.

## 3. Đọc một hit cụ thể — bằng chứng

```json
{
  "id": "q1",
  "question": "Who authored the paper 'SafeRAG: ...'?",
  "ground_truth": "Qianwen Cao, Chiyu Zhang, Junxiong Ning, Gongru Li",
  "answer": "Qianwen Cao, Chiyu Zhang, Junxiong Ning, Gongru Li",
  "retrieval_hit": true,
  "token_f1": 1.0
}
```

`retrieved_doc_ids` của câu này chứa đúng `10.2118/234689-pa` (khớp `ground_truth_doc_ids` đã xác
minh tồn tại trong index ở CP2) → không có miss nào để phân tích ở baseline; điều này sẽ dùng làm
mốc so sánh — kỳ vọng metric giảm rõ sau khi corruption chạy ở CP5.

## 4. Giải thích các metric

- **`retrieval_hit_rate`**: tỉ lệ câu hỏi mà `retrieved_doc_ids` (top-k từ semantic/exact-lookup
  search) chứa ít nhất 1 ID nằm trong `ground_truth_doc_ids`. Đo đúng khả năng của tầng retrieval,
  không phụ thuộc câu trả lời cuối có đúng chữ hay không.
- **`mean_token_f1`**: F1 theo tập token (không theo thứ tự) giữa `answer` và `ground_truth` — nhạy
  với câu trả lời gần đúng nhưng không phạt khác biệt định dạng nhỏ.
- **`judge_accuracy` / `mean_judge_score`**: từ `JudgeVerdict` (LLM chấm 1–5 + đúng/sai). **Ở baseline
  này, `.env` chưa có `GOOGLE_API_KEY`/provider nào khác → `_judge_answer()` tự động fallback sang
  heuristic dựa trên `token_f1`** (`score=5` khi `token_f1>=0.95`), không phải LLM thật đang chấm.
  Cần nêu rõ điều này trong `group_report.md` để không hiểu nhầm `judge_accuracy=1.0` là LLM-as-judge
  xác nhận — thực chất đang trùng với `mean_token_f1` do dùng cùng cơ chế fallback.

## 5. Việc cần làm tiếp (ngoài phạm vi vai trò 5)

Để `judge_accuracy`/`mean_judge_score`/`ragas` phản ánh đúng LLM thật, cần vai trò lead hoặc chủ sở
hữu `.env` điền `GOOGLE_API_KEY` (hoặc provider khác) — không phải việc của evaluation owner, chỉ ghi
nhận blocker ở đây để nhóm biết.
