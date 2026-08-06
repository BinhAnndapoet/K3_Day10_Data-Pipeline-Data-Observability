# CP2 — Vai trò 5: Evaluation owner (Nhóm 6 người)

> Checkpoint: `01:05–01:35` · Pass: `test_set.json`, embedding manifest và collection baseline tồn
> tại; semantic search, exact lookup và agent đều trả về kết quả có nguồn.

## 1. `build_test_set` — đã implement sẵn, không cần làm lại

Xem [cp1-vai-tro-5-evaluation-owner.md](cp1-vai-tro-5-evaluation-owner.md): teammate đã hoàn thiện
`testset.py` và commit `data/eval/test_set.json` (10 câu hỏi) trước cả CP1. Không có việc code mới
ở đây.

## 2. Kiểm tra ID trong test set đều tồn tại trong index

Build index baseline thật từ `data/clean/papers_clean.csv` bằng
`LocalEmbeddingIndex.build(df, settings)` (code có sẵn ở `retrieval/index.py`, không sửa gì):

- Collection: `papers-baseline`, 24 documents, embedding model
  `sentence-transformers/all-MiniLM-L6-v2`.
- Manifest ghi ở `data/embeddings/papers_embeddings.json`; Chroma persist tại `data/chroma/`.

Đối chiếu toàn bộ `ground_truth_doc_ids` của 10 câu hỏi trong `test_set.json` với `index.lookup()`:

| Kết quả | Số lượng |
| --- | --- |
| ID resolve được (`OK`) | 10 / 10 |
| ID thiếu (`MISSING`) | 0 |

→ Không có ID "ma" — mọi ground truth đều trỏ tới document thật trong index, đúng tiêu chí CP0 đã
đặt ra ("không tự bịa ID").

## 3. Semantic search smoke test

Query mẫu = câu hỏi `q1` ("Who authored the paper 'SafeRAG...'?") trả về đúng `paper_id`
`10.2118/234689-pa` ở vị trí đầu với score `0.721`, các kết quả tiếp theo là các paper RAG khác có
liên quan ngữ nghĩa (score thấp hơn rõ rệt: `0.485`, `0.484`) — cho thấy embedding phân biệt được
paper đúng chứ không trả ngẫu nhiên.

## 4. Test set cố định — sẵn sàng cho CP3

Không refresh test set (giữ đúng 10 câu đã có, đúng `paper_id` ổn định). File này sẽ được
`evaluate_pipeline()` (đã implement sẵn trong `metrics.py`) đọc trực tiếp ở CP3.

## 5. Lưu ý về agent/LLM

`.env` hiện chưa cấu hình API key nào (`GOOGLE_API_KEY` rỗng) → không chạy được `build_agent()`
thật (cần LLM). Điều này không chặn CP2 của vai trò 5 vì agent thuộc phạm vi vai trò `rag`; việc của
mình (kiểm tra index/test set) đã xác minh bằng `search()`/`lookup()` trực tiếp, không cần agent.
Ảnh hưởng duy nhất tới vai trò 5: ở CP3, `_judge_answer()` trong `metrics.py` sẽ tự động fallback
sang heuristic token-F1 thay vì LLM judge thật (đã có sẵn cơ chế try/except trong code, không phải
lỗi) — cần ghi rõ điều này khi đọc `judge_accuracy`/`mean_judge_score` để không hiểu nhầm là LLM
đánh giá thật.
