# Báo cáo cá nhân — Thành viên 4

## Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                                                          |
| ------------------ | ------------------------------------------------------------------ |
| Họ và tên       | Nguyễn Quang Khải                                                |
| MSSV               | 2A202601309                                                        |
| Khóa/Lớp         | K3 / E402                                                          |
| Tên nhóm         | Nxust                                                              |
| Vai trò chính    | Corruption & Repair owner                                          |
| Repository         | `D:\AI_in_Action\Labs\K3_Day10_Data-Pipeline-Data-Observability` |
| Ngày hoàn thành | 2026-08-06                                                         |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable                     | File/hàm phụ trách                                                                                                     | Input nhận vào                                  | Output bàn giao                                                                   | Trạng thái |
| -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------- | ---------------------------------------------------------------------------------- | ------------ |
| Mô phỏng corruption có kiểm soát  | `src/ingestion/corruption.py` — `corrupt_clean_dataframe`                                                            | Baseline clean`DataFrame` gồm 24 paper records | Corrupted`DataFrame` và `data/results/corruption_log.json`                    | Hoàn thành |
| Kiểm tra dữ liệu corrupted/repaired | `data/clean/papers_clean_corrupted.*`, `data/clean/papers_clean_repaired.*`; đối chiếu quality/freshness artifacts | Dữ liệu baseline, corrupted và repaired        | Bằng chứng 21 dòng corrupted, 24 dòng repaired; quality/freshness tương ứng | Hoàn thành |

`phase1.py` và `corruption_flow.py` là phần orchestration/integration của thành viên 5. Tôi cung cấp contract và artifact corruption để thành viên 5 sử dụng trong flow; tôi không nhận ownership cho toàn bộ hai file đó.

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động                                                 | Thành viên/module được hỗ trợ                                                                  | Kết quả                                                                                                                               |
| ------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| Phối hợp contract giữa corruption và pipeline downstream | `src/pipelines/corruption_flow.py`, `src/observability/quality.py`, `src/evaluation/metrics.py` | Corrupted dataset được ghi riêng, embedding/index dùng collection riêng, log chỉ rõ loại lỗi và`paper_id` bị ảnh hưởng |
| Đối chiếu kết quả repair                                | Thành viên 5 và các artifact trong`data/`                                                       | Xác nhận repair được dựng lại từ raw snapshot, không sửa thủ công corrupted dataset                                         |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện                               | File/hàm/artifact liên quan                                                         | Kết quả bàn giao                                                                                                           | Cách xác minh                                                                                    |
| --------------------------------------------------------- | ------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| Tạo các kịch bản làm hỏng dữ liệu có chủ đích | `src/ingestion/corruption.py` — `_apply_window`, `corrupt_clean_dataframe`     | 6 loại corruption:`drop_latest`, `blank_summary`, `inject_noise`, `truncate_title`, `old_date`, `duplicate_rows` | Đọc`data/results/corruption_log.json` và kiểm tra từng entry                                |
| Giữ các corruption có thể tái lập và truy vết     | `corrupt_clean_dataframe`, `data/results/corruption_log.json`                     | Shuffle cố định`random_state=42`, cửa sổ tác động riêng, log `parameter` và danh sách `paper_ids`            | Log có 6 entry, tổng số dòng từ 24 giảm còn 21 sau drop và tăng lại 1 dòng do duplicate |
| Đồng bộ dữ liệu dẫn xuất sau mutation              | `_sync_summary_chars`, `_recompute_age_days`; cột `text_for_embedding`         | `summary_chars`, `age_days` và nội dung embedding phản ánh dữ liệu corrupted                                        | `data/clean/papers_clean_corrupted.csv/json` và freshness/quality reports                       |
| Kiểm tra dữ liệu sau repair                            | `data/clean/papers_clean_repaired.*`, `data/quality/quality_report_repaired.json` | Repair từ raw snapshot phục hồi 24 dòng, quality đạt và freshness đạt                                                | `passed=true`, `stale_count=0`, `is_fresh=true`; metrics repaired trở về baseline          |

Output cụ thể nhất là `data/results/corruption_log.json`. Log ghi rõ 4 paper bị drop, 1 summary bị blank, 2 summary bị inject noise, 2 title bị truncate, 2 ngày xuất bản bị đổi thành `2010-01-01` và 1 row được nhân bản với hậu tố `_dup`.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Pipeline cần chứng minh dữ liệu lỗi có thể làm giảm chất lượng retrieval/RAG và có thể được phát hiện bằng observability signals. Vì vậy, corruption phải đủ đa dạng để tác động vào completeness, nội dung summary/title, freshness và document count; đồng thời mọi thay đổi phải truy vết được để repair và đối chiếu.

### Cách triển khai

`corrupt_clean_dataframe` không sửa trực tiếp baseline mà tạo một bản sao. Các dòng được xáo trộn bằng `random_state=42`, sau đó lấy theo các cửa sổ riêng để các loại lỗi không cố ý chồng lấn. Với dataset hiện tại, hàm thực hiện:

| Loại corruption   | Cách tác động                                                           | Số lượng hiện tại |
| ------------------ | --------------------------------------------------------------------------- | ---------------------: |
| `drop_latest`    | Xóa một cửa sổ record và lưu lại các`paper_id` bị xóa trong log |                      4 |
| `blank_summary`  | Đặt`summary` thành chuỗi rỗng                                        |                      1 |
| `inject_noise`   | Thêm tiền tố`zzzz` vào summary không rỗng                           |                      2 |
| `truncate_title` | Cắt title tối đa còn 20 ký tự                                         |                      2 |
| `old_date`       | Đổi`published` thành `2010-01-01`                                    |                      2 |
| `duplicate_rows` | Nhân bản một dòng và thêm hậu tố`_dup` vào `paper_id`          |                      1 |

Sau khi thay đổi summary, hàm tính lại `summary_chars`; sau khi thay đổi ngày, hàm tính lại `age_days`. Cuối cùng, `text_for_embedding` được dựng lại từ title, authors và summary corrupted để dữ liệu lỗi thực sự đi vào index downstream. Log được ghi cùng output corrupted để observability có thể nối quality/freshness signal với record bị tác động.

Repair không phục hồi bằng cách sửa thủ công từng dòng corrupted. `corruption_flow.py` đọc lại raw snapshot đáng tin cậy rồi gọi lại cleaning để tạo repaired dataset. Cách này giảm nguy cơ mang lỗi từ corrupted dataset sang repaired dataset.

### Input, output và contract

| Thành phần                   | Mô tả                                                                                                                                                        |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Input                          | Baseline clean`DataFrame`, có tối thiểu `paper_id`, `title`, `summary`, `published`, `authors_joined`; `Settings` và đường dẫn log       |
| Output                         | Corrupted`DataFrame` giữ schema clean, có `text_for_embedding` được dựng lại; log JSON chứa `corruptions`                                        |
| Module phụ thuộc             | `pandas`, `core.config.Settings`, `core.utils.write_json`                                                                                                |
| Module sử dụng output        | `src/pipelines/corruption_flow.py`, `src/observability/quality.py`, `src/evaluation/metrics.py`, `src/retrieval/index.py`                              |
| Điều kiện lỗi cần xử lý | Dataset rỗng và dataset quá nhỏ để cấp đủ các cửa sổ corruption; hai trường hợp này phải dừng bằng`ValueError`, không ghi log rỗng giả |

### Cách xác minh

```bash
uv run python script/run_phase1.py
uv run python script/run_corruption_flow.py
```

- **Kết quả mong đợi:** Có corrupted/repaired datasets, corruption log, metrics và comparison report; corrupted quality/freshness fail còn repaired phục hồi.
- **Kết quả thực tế từ artifacts:** Baseline có 24 dòng; corrupted có 21 dòng và quality fail; repaired có 24 dòng, quality pass và freshness pass.
- **Artifact/log:** `data/results/corruption_log.json`, `data/clean/papers_clean_corrupted.csv`, `data/clean/papers_clean_repaired.csv`, `data/quality/quality_report_corrupted.json`, `data/quality/quality_report_repaired.json`, `data/reports/corruption_report.md`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Cần chọn cách phân bổ các dòng bị corruption sao cho kết quả có thể tái lập, không phụ thuộc vào thứ tự hiện tại của dataset và có thể truy ngược chính xác.
- **Các phương án đã cân nhắc:** (1) chọn dòng bằng điều kiện cố định như “4 dòng đầu” hoặc theo ngày; (2) chọn ngẫu nhiên nhưng không đặt seed; (3) shuffle với seed cố định rồi tiêu thụ các cửa sổ riêng.
- **Phương án đã chọn:** Shuffle bằng `random_state=42`, sau đó dùng `take(count)` để cấp cửa sổ theo vị trí và log `paper_ids`.
- **Lý do:** Phương án này cân bằng giữa tính đại diện của corruption và reproducibility. Cửa sổ riêng giúp giảm chồng lấn; log paper IDs giúp downstream kiểm tra đúng record, trong khi baseline vẫn không bị mutate.
- **Bằng chứng quyết định phù hợp:** `corruption_log.json` luôn chứa loại lỗi, tham số và record bị tác động; cùng artifact hiện tại cho kết quả ổn định 24 → 21 → 24 dòng.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** `Student task: implement corruption flow.`
- **Lệnh hoặc bước tái hiện:** Chạy corruption flow khi `corrupt_clean_dataframe` còn là stub sẽ dừng tại bước corruption vì hàm chưa tạo corrupted dataframe và log.
- **Nguyên nhân gốc:** Hàm ban đầu chưa có logic mutation, không có log per-type, không đồng bộ các cột dẫn xuất và chưa xây dựng lại `text_for_embedding`.
- **Cách xử lý:** Bổ sung sáu corruption scenarios, copy dataframe trước khi mutate, seed shuffle cố định, guard cho dataset rỗng/thiếu dòng, cập nhật `summary_chars`/`age_days`, dựng lại text embedding và ghi JSON log.
- **Cách xác minh sau khi sửa:** Đối chiếu `data/results/corruption_log.json` với dữ liệu corrupted; quality report cho thấy `summary.missing_count=1`, `freshness.stale_count=2`, còn repaired report cho thấy `passed=true` và `stale_count=0`.
- **Điều học được:** Một corruption function chỉ có giá trị trong pipeline quan sát được khi mutation, log, các cột dẫn xuất và artifact downstream cùng nhất quán.

Một giới hạn còn lại: `duplicate_rows` đổi `paper_id` thành hậu tố `_dup`, trong khi quality check kiểm tra trùng theo `paper_id` và `title`. Vì vậy artifact hiện tại ghi `duplicate_rows=0` dù có một bản sao theo nội dung. Đây là cải thiện cần làm tiếp: kiểm tra thêm duplicate theo canonical ID hoặc fingerprint của nội dung, không chỉ theo khóa đã bị biến đổi.

## 7. Hiểu biết về luồng end-to-end

1. **Từ Crossref đến vector index:** Crossref trả raw records và lưu snapshot trong `data/raw/`. `cleaning.py` chuẩn hóa thành clean dataframe, tạo `text_for_embedding`, sau đó `LocalEmbeddingIndex` sinh embedding và lưu index/embedding artifacts. Corruption được áp dụng sau baseline clean; corrupted text được index trong collection riêng.
2. **Evaluation set và ground-truth document IDs:** `testset.py` tạo các câu hỏi từ clean dataset, mỗi câu có ground-truth document ID. Evaluator so sánh các document IDs được retrieval với ground truth để tính `retrieval_hit_rate`, rồi so sánh answer với ground truth để tính `mean_token_f1`, `judge_accuracy` và `mean_judge_score`.
3. **Quality checks và freshness monitoring:** Quality checks kiểm tra tính hợp lệ của schema/nội dung như row count, null/blank summary, title, paper ID và duplicate rows. Freshness tập trung vào tuổi của `published`, đếm stale/unknown rows theo ngưỡng 180 ngày. Hai signal bổ sung cho nhau: dữ liệu có thể đủ dòng nhưng vẫn cũ, hoặc còn mới nhưng thiếu summary.
4. **Lý do dùng cùng test set:** Baseline, corrupted và repaired phải trả lời cùng 10 câu hỏi và cùng ground-truth IDs. Nếu test set thay đổi, metric có thể thay đổi do độ khó câu hỏi chứ không phải do chất lượng dữ liệu.
5. **Tiêu chí repair thành công:** Repaired dataset phải được tạo lại từ raw snapshot, có 24 dòng, quality `passed=true`, freshness `is_fresh=true`, không có stale rows; đồng thời metrics phải phục hồi về baseline trên cùng test set. Artifact hiện tại đáp ứng các tiêu chí này.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal          |       Baseline |          Corrupted |       Repaired | Nhận xét của cá nhân                                                                      |
| ---------------------- | -------------: | -----------------: | -------------: | ---------------------------------------------------------------------------------------------- |
| `retrieval_hit_rate` |          1.000 |              0.800 |          1.000 | Giảm 0.200 khi document/summary bị hỏng, phục hồi hoàn toàn sau repair.                 |
| `mean_token_f1`      |          1.000 |              0.800 |          1.000 | Answer bị lệch ở các câu chịu ảnh hưởng retrieval; trở lại mức baseline.           |
| `judge_accuracy`     |          1.000 |              0.800 |          1.000 | Tỷ lệ đúng giảm cùng retrieval hit rate.                                                 |
| `mean_judge_score`   |          5.000 |              4.200 |          5.000 | Điểm đánh giá giảm 0.8 rồi phục hồi 0.8 điểm.                                       |
| Quality checks         | Pass, 24 dòng |     Fail, 21 dòng | Pass, 24 dòng | Corrupted có 1 summary thiếu và 2 stale rows; repaired không còn lỗi quality/freshness.  |
| Freshness status       |          Fresh | Not fresh, 2 stale |          Fresh | `old_date` tạo tín hiệu freshness rõ ràng và được loại bỏ khi dựng lại từ raw. |

### Kết luận từ số liệu

1. **`drop_latest`/summary corruption** → corrupted dataset còn 21 dòng và có `summary.missing_count=1`; `retrieval_hit_rate`, `mean_token_f1` và `judge_accuracy` đều giảm từ 1.0 xuống 0.8.
2. **Repair từ raw snapshot** → dataset trở lại 24 dòng, quality pass, `stale_count=0`, freshness pass; bốn metrics chính phục hồi về baseline 1.0/1.0/1.0/5.0.

Corruption ảnh hưởng rõ nhất ở cấp agent là mất hoặc làm sai thông tin dùng để retrieval. Bằng chứng là cả `retrieval_hit_rate` và các metric answer đều giảm 20%; tuy nhiên artifact chưa cô lập được đóng góp riêng của từng loại corruption vì flow áp dụng sáu loại lỗi trong cùng một lượt. `old_date` ảnh hưởng rõ nhất ở observability vì tạo trực tiếp 2 stale rows, nhưng không nhất thiết làm hỏng answer nếu document vẫn được retrieval.

Kết quả cần lưu ý khác với kỳ vọng là quality check không phát hiện `duplicate_rows` trong artifact: log có scenario nhân bản, nhưng `paper_id` của bản sao đã đổi thành `_dup`, nên phép kiểm tra theo `paper_id`/`title` ghi `duplicate_rows=0`. Điều này cho thấy thiết kế corruption và rule quality phải thống nhất với nhau; đây không nên được diễn giải là hệ thống đã phát hiện duplicate thành công.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. **Về data pipeline:** Corruption cần giữ schema và cập nhật các cột dẫn xuất, nếu không downstream sẽ đo một trạng thái không nhất quán với dữ liệu thực tế.
2. **Về data quality/observability:** Log theo `paper_id`, loại lỗi và tham số biến mutation thành sự kiện có thể truy vết; quality và freshness phải được đọc cùng nhau để xác định phạm vi ảnh hưởng.
3. **Về ảnh hưởng của dữ liệu đến RAG agent:** Chỉ một phần nhỏ dữ liệu bị hỏng cũng có thể làm retrieval hit rate và answer quality giảm từ 1.0 xuống 0.8 trên test set cố định.

### Nếu có thêm thời gian

Tôi sẽ bổ sung fingerprint nội dung/canonical `paper_id` để quality check phát hiện bản sao dù ID đã bị đổi hậu tố, đồng thời tạo test riêng cho từng corruption type. Cải thiện sẽ được đo bằng `duplicate_rows`, missing/short summary, stale count và metric baseline/corrupted/repaired trên cùng test set.

## 10. Cam kết của thành viên

- [X] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [X] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [X] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [X] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [X] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [X] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** [Điền họ và tên]

**Ngày xác nhận:** 2026-08-06
