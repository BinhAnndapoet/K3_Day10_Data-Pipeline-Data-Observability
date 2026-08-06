# CP0 — Vai trò 5: Evaluation owner (Nhóm 6 người)

> Checkpoint: `00:00–00:30` · Phạm vi phụ trách: `src/evaluation/` · `data/eval/`
> Mục tiêu CP0: **đọc và thiết kế**, chưa viết code. `src/ingestion/cleaning.py` (owner: vai trò 3)
> vẫn là stub nên chưa có `paper_id`/`text_for_embedding` thật — việc build `build_test_set()` thật
> sự chỉ bắt đầu ở CP2 sau khi clean schema ổn định (CP1).

## 1. Đọc `testset.py`, `qa.py`, `metrics.py` để hiểu format answer và metric

### `src/evaluation/testset.py` — hiện là stub

`build_test_set(df, output_path) -> list[dict]`. Theo docstring, mỗi record test set cần đúng 5
trường:

| Trường | Ý nghĩa |
| --- | --- |
| `id` | ID duy nhất của câu hỏi |
| `question_type` | một trong `summary` / `authors` / `date` / `categories` |
| `question` | câu hỏi tiếng Anh (agent trả lời bằng tiếng Anh, xem `qa.py`) |
| `ground_truth` | câu trả lời đúng, lấy trực tiếp từ dữ liệu clean |
| `ground_truth_doc_ids` | list `paper_id` chứng minh cho câu trả lời |

Kết quả ghi ra `output_path` = `settings.paths.eval_testset` = `data/eval/test_set.json`.

### `src/retrieval/qa.py` — đã implement, đây là "API" mà test set phải tương thích

`answer_question(question, settings, index, top_k=None) -> AnswerResult` với
`AnswerResult(question, answer, retrieved_doc_ids, retrieved_contexts, retrieved_titles)`.

Cơ chế trả lời (`_extract_answer`) chỉ nhìn vào **kết quả top 1** và match theo từ khoá trong câu hỏi:

| Từ khoá trong `question` (không phân biệt hoa/thường) | Trường trả về |
| --- | --- |
| `"who authored"` hoặc `"list the authors"` | `metadata["authors_joined"]` |
| `"when was"` / `"publication date"` / `"published on"` | `metadata["published"]` |
| `"what categories"` | `metadata["categories_joined"]` |
| còn lại (mặc định) | câu đầu tiên của `metadata["summary"]` (dùng cho câu hỏi kiểu `summary`) |

Ngoài ra, nếu câu hỏi chứa tiêu đề trong dấu nháy đơn `'...'` (regex `r"'([^']+)'"`), `qa.py` sẽ
làm **exact lookup theo title trước**, rồi mới bổ sung bằng semantic search. → Câu hỏi test set nên
luôn đặt tên paper trong dấu nháy đơn để agent chắc chắn trả lời đúng document, tránh phụ thuộc vào
độ chính xác của semantic search.

### `src/evaluation/metrics.py` — đã implement đầy đủ, không cần sửa

`evaluate_pipeline(settings, index, test_set_path, metrics_output_path, answers_output_path) -> EvaluationBundle`:

1. Đọc `test_set_path` (chính là file `build_test_set()` sẽ tạo).
2. Với mỗi item: gọi `answer_question(...)`, so khớp bằng `_judge_answer` (LLM judge trả về
   `JudgeVerdict{score:1-5, correct:bool, reasoning}`, có fallback heuristic theo token F1 nếu LLM
   lỗi) và tính `retrieval_hit` = có ít nhất 1 `retrieved_doc_ids` nằm trong `ground_truth_doc_ids`.
3. Ghi `answers_output_path` (per-question chi tiết) và `metrics_output_path` (summary:
   `samples`, `retrieval_hit_rate`, `mean_token_f1`, `judge_accuracy`, `mean_judge_score`, `ragas`
   — Ragas chỉ chạy khi `RUN_RAGAS=1`).

**Kết luận quan trọng:** `retrieval_hit_rate` phụ thuộc 100% vào việc `ground_truth_doc_ids` đúng
với dữ liệu thật trong index — nếu test set bịa ID, mọi metric sẽ sai lệch dù agent trả lời đúng.

## 2. Thiết kế 4 loại câu hỏi từ dữ liệu thật

Thiết kế template câu hỏi theo đúng 4 nhánh mà `_extract_answer` trong `qa.py` nhận diện được, mỗi
câu hỏi luôn chứa `'{title}'` để kích hoạt exact lookup:

| `question_type` | Template câu hỏi | `ground_truth` lấy từ cột clean |
| --- | --- | --- |
| `summary` | `What is the paper '{title}' about?` | câu đầu tiên của `summary` (dùng `first_sentence`, giống logic `qa.py` dùng để trả lời) |
| `authors` | `Who authored the paper '{title}'?` | `authors_joined` |
| `date` | `When was the paper '{title}' published?` | `published` |
| `categories` | `What categories does the paper '{title}' belong to?` | `categories_joined` |

Ghi chú khi implement ở CP2:

- Chọn ngẫu nhiên/đại diện một số paper trong cleaned dataframe (không dùng toàn bộ, tránh test set
  quá dài); đảm bảo mỗi paper được chọn có đủ `title`, `summary`, `authors_joined`,
  `categories_joined`, `published` không rỗng.
- Sinh đủ cả 4 `question_type` cho từng paper (hoặc rải đều) để evaluation bao phủ mọi nhánh của
  `_extract_answer`, không chỉ toàn câu hỏi `summary`.

## 3. `ground_truth_doc_ids` phải lấy từ `paper_id` clean, không tự bịa

- Nguồn duy nhất hợp lệ: cột `paper_id` trong dataframe đã qua `cleaning.py` (tức file
  `data/clean/papers_clean.json` / `.csv`), vì đây chính là ID được `retrieval/index.py` dùng làm
  `paper_id` khi build metadata trong Chroma.
- `ground_truth_doc_ids` cho mỗi câu hỏi = `[paper_id]` của đúng paper đang được hỏi (list vì
  `metrics.py` cho phép nhiều ID đúng, nhưng ở đây thường chỉ có 1).
- Không tự đặt ID kiểu `"paper-1"`, `"doc_001"`... vì `retrieval_hit` so khớp trực tiếp với
  `retrieved_doc_ids` — ID không khớp với index thật sẽ khiến `retrieval_hit_rate` luôn bằng 0 dù
  agent hoạt động đúng.

## 4. Artifact sẽ bàn giao & phụ thuộc

| Artifact | Trạng thái CP0 | Sẵn sàng thật sự khi nào |
| --- | --- | --- |
| `data/eval/test_set.json` | Chưa tạo (đúng vì CP0 chỉ đọc/thiết kế) | Sau CP1 (clean schema ổn định) → build ở CP2 |
| `data/results/baseline_metrics.json`, `baseline_answers.json` | Hiểu format, không tự tạo (do `evaluate_pipeline` ghi ra khi chạy `phase1.py`) | CP3, khi chạy `uv run python script/run_phase1.py` |

**Phụ thuộc chặn (blocker) trước CP2:** cần vai trò 3 (Cleaning & corruption owner) hoàn thành
`cleaning.py` để có `paper_id`, `title`, `summary`, `authors_joined`, `categories_joined`,
`published` thật trong dataframe clean.
