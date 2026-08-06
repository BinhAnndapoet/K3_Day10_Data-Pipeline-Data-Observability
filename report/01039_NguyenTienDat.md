# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin       | Nội dung                                                                   |
| --------------- | -------------------------------------------------------------------------- |
| Họ và tên       | Nguyễn Tiến Đạt                                                            |
| MSSV            | 2A202601039                                                                |
| Khóa/Lớp        | K3                                                                         |
| Tên nhóm        | Nhóm 6 người                                                               |
| Vai trò chính   | Vai trò 5 — Evaluation owner                                               |
| Repository      | https://github.com/BinhAnndapoet/K3_Day10_Data-Pipeline-Data-Observability |
| Ngày hoàn thành | 2026-08-06                                                                 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable                                                                                           | File/hàm phụ trách                                                              | Input nhận vào                          | Output bàn giao                                                                                                   | Trạng thái |
| ------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------- | --------------------------------------- | ----------------------------------------------------------------------------------------------------------------- | ---------- |
| Xác minh contract test set ↔ QA layer                                                                        | `src/evaluation/testset.py`, `src/retrieval/qa.py`, `src/evaluation/metrics.py` | Docstring/contract của 3 module         | Bảng đối chiếu template câu hỏi ↔ nhánh`_extract_answer` (`report/checkpoints/cp0-vai-tro-5-evaluation-owner.md`) | Hoàn thành |
| Xác minh test set khớp cleaned dataframe                                                                     | `data/eval/test_set.json`, `data/clean/papers_clean.csv`                        | Test set 10 câu hỏi                     | Đối chiếu 10/10`ground_truth_doc_ids` tồn tại trong `paper_id` clean và trong index baseline                      | Hoàn thành |
| Chạy evaluation baseline lần đầu                                                                             | `evaluate_pipeline()` (`src/evaluation/metrics.py`, không sửa code)             | Index`papers-baseline`, `test_set.json` | `data/results/baseline_metrics.json`, `baseline_answers.json`                                                     | Hoàn thành |
| Đọc/giải thích kết quả corrupted và repaired sau khi teammate hoàn thành`corruption.py`/`corruption_flow.py` | `data/results/corrupted_*.json`, `repaired_*.json`                              | Metrics 3 trạng thái                    | Bảng so sánh + chuỗi nhân–quả có bằng chứng (mục 8 bên dưới)                                                      | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động                                                               | Thành viên/module được hỗ trợ                | Kết quả                                                                                                                   |
| ----------------------------------------------------------------------- | -------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| Implement`run_data_quality_checks` và `build_freshness_report`          | `src/observability/quality.py` (vai trò 6)   | Quality/freshness report chạy thật cho baseline, dùng làm input đối chiếu ở mục 8                                         |
| Implement`generate_phase1_report` và khung `generate_corruption_report` | `src/observability/reporting.py` (vai trò 6) | `data/reports/phase1_report.md` bản đầu (sau đó teammate `Twilight` viết lại bản tiếng Việt cuối cùng đang có trong repo) |
| Viết checkpoint notes CP0–CP6 cho cả vai trò 5 và vai trò 6             | Toàn nhóm                                    | `report/checkpoints/cp*-vai-tro-5-evaluation-owner.md`, `cp*-vai-tro-6-observability-owner.md`                            |

Ghi chú minh bạch: `src/evaluation/testset.py` và `src/evaluation/metrics.py` **không phải do tôi implement** — `testset.py` được hoàn thiện bởi teammate trong commit `6b9ae5f "fish crossref, clean & test set"`, `metrics.py` đã có sẵn hoàn chỉnh từ đầu. Phần việc thật của tôi ở vai trò 5 là đọc hiểu contract, xác minh test set không có ID bịa, chạy evaluator và diễn giải số liệu — đúng như đã ghi trong `report/checkpoints/cp1-vai-tro-5-evaluation-owner.md` mục "Cập nhật quan trọng: testset.py đã được implement (không phải bởi mình)". Tương tự, `src/ingestion/corruption.py`, `src/pipelines/phase1.py` và `src/pipelines/corruption_flow.py` do teammate khác (`Nguyễn Trần Hội Thắng`, `Twilight`) implement.

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện                                    | File/hàm/artifact liên quan                                    | Kết quả bàn giao                                                                                          | Cách xác minh                                                                |
| -------------------------------------------------------- | -------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| Đối chiếu 4 loại câu hỏi với`qa.py::_extract_answer`     | `report/checkpoints/cp0-vai-tro-5-evaluation-owner.md`         | Bảng template câu hỏi ↔ nhánh trả lời, tránh sai lệch metric do câu hỏi không đúng cụm từ                 | Đọc trực tiếp`src/retrieval/qa.py`                                           |
| Xác minh 10/10`ground_truth_doc_ids` tồn tại trong index | `report/checkpoints/cp2-vai-tro-5-evaluation-owner.md`         | 0 ID "ma"                                                                                                 | `LocalEmbeddingIndex.lookup()` trên `data/embeddings/papers_embeddings.json` |
| Baseline evaluation                                      | `data/results/baseline_metrics.json`                           | `retrieval_hit_rate=1.0`, `mean_token_f1=1.0`, `judge_accuracy=1.0`, `mean_judge_score=5` (10/10 samples) | `cat data/results/baseline_metrics.json`                                     |
| So sánh baseline–corrupted–repaired                      | `data/results/corrupted_metrics.json`, `repaired_metrics.json` | Xác nhận`retrieval_hit_rate` giảm còn 0.8 sau corruption và phục hồi về 1.0 sau repair                    | Mục 8 bên dưới                                                               |

Output cụ thể: `data/results/baseline_answers.json` (10 câu trả lời có nguồn, mỗi câu kèm `retrieved_doc_ids` và `token_f1`) chứng minh baseline retrieval hoạt động đúng trước khi so sánh với corrupted/repaired.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Phần việc của tôi đảm bảo evaluation set và metrics phản ánh đúng chất lượng retrieval/agent, không bị lỗi do test set tự bịa ID hoặc câu hỏi sai định dạng mà `qa.py` không nhận diện được.

### Cách triển khai

`src/retrieval/qa.py::_extract_answer` chỉ route câu trả lời theo cụm từ tiếng Anh cố định (`"who authored"`, `"when was"`, `"what categories"`, mặc định là câu đầu `summary`) và kích hoạt exact-lookup khi title nằm trong dấu nháy đơn. Tôi đối chiếu 10 câu hỏi thật trong `data/eval/test_set.json` với các nhánh này, xác nhận `testset.py::_make_question`/`_ground_truth` sinh đúng theo contract đã thiết kế ở CP0 (chỉ khác nhỏ về phrasing câu `summary`, không ảnh hưởng routing). Sau đó tôi chạy `evaluate_pipeline()` (đã implement sẵn, không sửa) trên index `papers-baseline` để tạo `baseline_metrics.json`/`baseline_answers.json` thật, và sau khi teammate hoàn thành corruption/repair, tôi đọc lại `corrupted_metrics.json`/`repaired_metrics.json` để dựng chuỗi nhân–quả corruption → metric.

### Input, output và contract

| Thành phần              | Mô tả                                                                                                                                            |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| Input                   | `data/clean/papers_clean.csv` (từ vai trò cleaning), `LocalEmbeddingIndex` đã build (vai trò RAG)                                                |
| Output                  | `data/eval/test_set.json` (đã có sẵn, tôi xác minh); `data/results/{baseline,corrupted,repaired}_{metrics,answers}.json`                         |
| Module phụ thuộc        | `src/retrieval/qa.py`, `src/retrieval/index.py`                                                                                                  |
| Module sử dụng output   | `src/observability/reporting.py` (viết report), `report/group_report.md`                                                                         |
| Điều kiện lỗi cần xử lý | `ground_truth_doc_ids` không khớp `paper_id` trong index → `retrieval_hit_rate` sai lệch dù agent đúng; đã kiểm tra không xảy ra (10/10 resolve) |

### Cách xác minh

```bash
uv run python -c "from core.config import load_settings; from retrieval.index import LocalEmbeddingIndex; from evaluation.metrics import evaluate_pipeline; s=load_settings(); idx=LocalEmbeddingIndex.load(s); evaluate_pipeline(s, idx, s.paths.eval_testset, s.paths.baseline_metrics, s.paths.baseline_answers)"
```

- **Kết quả mong đợi:** ghi `baseline_metrics.json` với 10 samples.
- **Kết quả thực tế:** đúng như mong đợi — `retrieval_hit_rate=1.0`, `mean_token_f1=1.0`, `judge_accuracy=1.0`, `mean_judge_score=5`.
- **Artifact/log:** `data/results/baseline_metrics.json`, `data/results/baseline_answers.json`. Không chứa secret.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** `.env` không có `GOOGLE_API_KEY` (hoặc provider LLM nào khác được cấu hình), nên `_judge_answer()` trong `metrics.py` không gọi được LLM thật.
- **Các phương án đã cân nhắc:** (1) chặn CP3 lại chờ nhóm cấu hình API key; (2) chấp nhận chạy với fallback heuristic (token-F1 threshold) đã có sẵn trong code, miễn là ghi rõ trong report để không hiểu nhầm là LLM-judge thật.
- **Phương án đã chọn:** (2) — chạy bằng fallback, không chặn tiến độ pipeline.
- **Lý do:** Fallback là cơ chế `try/except` đã có sẵn trong code (không phải lỗi phát sinh), và việc có API key thuộc phạm vi cấu hình chung của Lead/`.env`, không thuộc vai trò evaluation. Chặn CP3 lại sẽ làm nhóm mất mốc thời gian mà không giải quyết được root cause.
- **Bằng chứng quyết định phù hợp:** kiểm tra cả 3 file `baseline_answers.json`, `corrupted_answers.json`, `repaired_answers.json` — toàn bộ record có `judge.reasoning = "Fallback heuristic judge used because the LLM evaluator was unavailable."`, xác nhận `judge_accuracy`/`mean_judge_score` trùng với `mean_token_f1` do dùng chung cơ chế fallback, không phải LLM đánh giá độc lập.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** Ở thời điểm viết CP5, `src/ingestion/corruption.py` và `src/pipelines/corruption_flow.py` còn `raise NotImplementedError("Student task: ...")`, nên chưa có `data/clean/papers_clean_corrupted.csv` để evaluate.
- **Lệnh hoặc bước tái hiện:** `rg -n "NotImplementedError" src/ingestion/corruption.py src/pipelines/corruption_flow.py` (thời điểm đó khớp).
- **Nguyên nhân gốc:** hai file thuộc phạm vi vai trò khác (Cleaning & corruption owner, Lead), chưa hoàn thành tại checkpoint đó.
- **Cách xử lý:** thay vì chờ, tôi viết sẵn kế hoạch evaluate corrupted/repaired trong `cp5`/`cp6-vai-tro-5-evaluation-owner.md` (dùng lại `evaluate_pipeline()` có sẵn, chỉ đổi `index`/output path, giữ nguyên `test_set_path`), để chạy được ngay khi dữ liệu corrupted sẵn sàng.
- **Cách xác minh sau khi sửa:** sau khi teammate hoàn thành corruption/repair, tôi đọc `data/results/corrupted_metrics.json` và `repaired_metrics.json` — kế hoạch chạy đúng như dự kiến, không cần sửa code evaluation.
- **Điều học được:** khi bị block bởi module khác, vẫn có thể tạo giá trị bằng cách viết sẵn kế hoạch/kiểm tra logic ràng buộc (contract) thay vì chờ bị động.

## 7. Hiểu biết về luồng end-to-end

1. **Crossref → vector index:** `crossref.py` fetch raw response/records theo `source_query`/`source_filter`, lưu `data/raw/`. `cleaning.py` chuẩn hoá thành `papers_clean.csv/json` với `paper_id` (DOI), `text_for_embedding`, `age_days`. `retrieval/index.py::LocalEmbeddingIndex.build()` embed bằng MiniLM và ghi vào Chroma collection tương ứng (`papers-baseline`/`-corrupted`/`-repaired`), đồng thời ghi manifest JSON.
2. **Evaluation set & ground-truth doc IDs:** `testset.py::build_test_set` chọn paper từ cleaned dataframe (ưu tiên mới nhất, đủ `authors`/`summary`, title không chứa dấu `'`), sinh câu hỏi theo 4 loại khớp `qa.py::_extract_answer`, và gán `ground_truth_doc_ids=[paper_id]` trực tiếp từ cột `paper_id` — vì vậy retrieval hit/miss đo đúng khả năng index tìm lại đúng document, không phải suy đoán.
3. **Quality checks khác freshness ở điểm:** quality checks (`run_data_quality_checks`) đo tính toàn vẹn cấu trúc tại một thời điểm (null, duplicate, độ dài field), còn freshness (`build_freshness_report`) đo tính cập nhật theo thời gian dựa trên `published`/`age_days` so với ngưỡng 180 ngày — một dataset có thể "sạch cấu trúc" nhưng vẫn "cũ" (stale), hai chiều độc lập nhau.
4. **Vì sao dùng cùng test set:** nếu đổi câu hỏi/ground truth giữa các trạng thái thì chênh lệch metric có thể do test set khác nhau, không phải do data corruption — mất tính so sánh được. Giữ nguyên `data/eval/test_set.json` cho cả ba lần `evaluate_pipeline()` loại bỏ biến nhiễu này.
5. **Repair được xem là thành công khi:** metric của trạng thái repaired quay về bằng (hoặc gần bằng) baseline trên cùng test set, VÀ từng câu hỏi bị miss ở corrupted quay lại `retrieval_hit=true` với answer đúng — không chỉ nhìn con số trung bình mà phải soi lại record cụ thể để loại trừ trùng hợp ngẫu nhiên.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal                       |                           Baseline |                                                                      Corrupted |                           Repaired | Nhận xét của cá nhân                                                                                                                                         |
| ----------------------------------- | ---------------------------------: | -----------------------------------------------------------------------------: | ---------------------------------: | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `retrieval_hit_rate`                |                              1.000 |                                                                          0.800 |                              1.000 | Giảm đúng 2/10 câu (q1, q9) — cả hai đều có`ground_truth_doc_ids` trùng paper bị `drop_latest` xoá khỏi corrupted clean data; phục hồi hoàn toàn sau repair. |
| `mean_token_f1`                     |                              1.000 |                                                                          0.800 |                              1.000 | Đi cùng chiều với`retrieval_hit_rate` vì answer sai hoàn toàn khi miss (token_f1=0.0 cho 2 câu đó).                                                          |
| `judge_accuracy`                    |                              1.000 |                                                                          0.800 |                              1.000 | Trùng số với`mean_token_f1` — do đang dùng fallback heuristic (không có API key), không phải LLM chấm độc lập; cần đọc cùng lưu ý ở mục 5.                   |
| `mean_judge_score`                  |                              5.000 |                                                                          4.200 |                              5.000 | 2 câu miss nhận`score=1` (fallback: `token_f1<0.5`), kéo trung bình từ 5 xuống 4.2.                                                                          |
| Quality checks (`quality_report_*`) |            `passed=true` (24 rows) | `passed=false`: `summary.missing_count=1`, `freshness.stale_count=2` (21 rows) |            `passed=true` (24 rows) | Khớp đúng loại corruption đã log:`blank_summary` (1) và `old_date` (2, nhưng 1 record đã bị tính stale trùng lúc `drop_latest`).                             |
| Freshness status                    | `is_fresh=true`, `stale_rows=0/24` |                                            `is_fresh=false`, `stale_rows=2/21` | `is_fresh=true`, `stale_rows=0/24` | Phục hồi hoàn toàn vì repair re-run cleaning từ raw gốc, không kế thừa`published` đã bị `old_date` sửa.                                                      |

### Kết luận từ số liệu

1. **[Data corruption] → [quality/freshness signal thay đổi] → [agent metric thay đổi]:** `corruption_log.json` ghi `drop_latest` xoá 4 record gồm `10.2118/234689-pa` (paper của câu `q1`) và `10.47576/2949-1894.2026.7.7.023` (paper của câu `q9`) → hai document này không còn trong index `papers-corrupted` → `retrieved_doc_ids` của `q1`/`q9` không còn chứa ground-truth ID → `retrieval_hit` chuyển `true → false`, `answer` sai hẳn tên tác giả (baseline: "Qianwen Cao, Chiyu Zhang, Junxiong Ning, Gongru Li"; corrupted: "Hyewon Lee, Sungsu Lim" — lấy nhầm từ document gần nhất khác) → kéo `retrieval_hit_rate`, `mean_token_f1`, `judge_accuracy` từ 1.0 xuống 0.8.
2. **[Repair action] → [quality/freshness signal phục hồi] → [agent metric phục hồi]:** Repair re-run `cleaning.build_clean_dataframe()` từ `data/raw/crossref_records.json` gốc (24 record đầy đủ, không kế thừa các sửa đổi của corruption) → `papers-repaired` có lại đủ 24 document, `quality_report_repaired.passed=true`, `freshness_repaired.is_fresh=true` → evaluate lại `q1`/`q9` cho `retrieval_hit=true`, answer khớp verbatim với ground truth → cả 4 metric quay về đúng bằng baseline (1.0/1.0/1.0/5).

Corruption ảnh hưởng rõ nhất là **`drop_latest`** (xoá thẳng document khỏi index) vì nó tác động trực tiếp đến tầng retrieval — hai câu hỏi bị miss đều truy ngược được về đúng corruption này qua `paper_id` trùng khớp trong `corruption_log.json`. Các corruption còn lại (`blank_summary`, `inject_noise`, `truncate_title`, `old_date`, `duplicate_rows`) làm quality/freshness report báo `passed=false` nhưng không tạo thêm miss nào trong 10 câu hỏi test set — không có nghĩa chúng vô hại, chỉ là test set 10 câu hiện tại không phủ trúng các record mà 5 loại corruption đó tác động; đây là giới hạn của test set, không nên suy ra "chỉ drop_latest mới nguy hiểm".

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Test set phải bám `paper_id` thật của dữ liệu clean — chỉ cần một ID bịa hoặc lệch template câu hỏi so với logic route của tầng QA là toàn bộ `retrieval_hit_rate` mất ý nghĩa dù hệ thống hoạt động đúng.
2. `judge_accuracy`/`mean_judge_score` không tự động là "LLM đánh giá" — phải luôn kiểm tra field `reasoning` trong answers để biết đang đọc số liệu từ LLM thật hay từ fallback heuristic, tránh báo cáo sai bản chất metric.
3. Data corruption chỉ "đo được" tác động khi trúng đúng record nằm trong test set — cùng một loại lỗi dữ liệu có thể vô hình với evaluation nếu test set không phủ tới record đó, nên coverage của test set cũng là một chỉ số quality cần quan tâm.

### Nếu có thêm thời gian

Cấu hình `GOOGLE_API_KEY` thật để chạy lại cả ba trạng thái với LLM-as-judge thật, so sánh xem `judge_accuracy` có lệch khỏi `mean_token_f1` hay không (hiện tại hai số trùng nhau do dùng chung fallback, chưa chứng minh được judge có giá trị bổ sung gì so với token-F1 đơn thuần) — đo bằng cách so sánh `judge.reasoning` giữa hai lần chạy trên cùng answers.

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi "đã chạy thành công" cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Nguyễn Tiến Đạt
**Ngày xác nhận:** 2026-08-06
