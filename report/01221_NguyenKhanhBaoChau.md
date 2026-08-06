# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin       | Nội dung                                                                   |
| --------------- | -------------------------------------------------------------------------- |
| Họ và tên       | Nguyễn Khánh Bảo Châu                                                      |
| MSSV            | 2A202601221                                                                |
| Khóa/Lớp        | K3                                                                         |
| Tên nhóm        | Nxust                                                                      |
| Vai trò chính   | Vai trò 1 — Lead: định hướng, tích hợp & review (release owner)            |
| Repository      | https://github.com/BinhAnndapoet/K3_Day10_Data-Pipeline-Data-Observability |
| Ngày hoàn thành | 2026-08-06                                                                 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| ------------------ | ------------------ | -------------- | --------------- | ---------- |
| Định hướng kiến trúc & phân công theo deliverable | `README.md` (report/), bảng phân công trong `group_report.md` §1 và §3 | Guide.md, Rubric.md, số lượng thành viên (6) | Bảng 7 khối × owner × input/output/cách xác minh; thứ tự phụ thuộc ingestion → cleaning → testset → baseline → corruption | Hoàn thành |
| Chốt contract dùng chung giữa các module | `src/core/config.py` (paths/collections), schema clean, schema test set | Đề xuất của vai trò 2/3/5/6 | Quy ước: `paper_id` = DOI xuyên suốt; artifact 3 trạng thái tách file (`*_baseline/_corrupted/_repaired`); test set đóng băng | Hoàn thành |
| Kiểm tra tính nhất quán report ↔ artifact | `report/*.md`, `data/results/*`, `data/quality/*`, `data/reports/*` | 1 group report + 4 report cá nhân | 6 finding review (mục 5, 6, 8) — 3 finding về số liệu/lập luận, 3 finding về thủ tục nộp bài | Hoàn thành |
| Review checklist trước nộp (release gate) | `group_report.md` §13, `README.md` §8 Definition of Done | Toàn repo | Kết luận pass/fail từng mục + danh sách việc phải sửa trước khi nộp | Hoàn thành |
| Kiểm tra an toàn secret trong repo | `.gitignore`, `.env.example`, toàn bộ report/log | Repo trạng thái nộp | Xác nhận `.env` nằm trong `.gitignore`, không có key trong report/artifact | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| --------- | ----------------------------- | ------- |
| Rà soát luồng `corruption_flow.py` có dùng đúng một test set cho cả 3 trạng thái | Vai trò 3 (corruption) + vai trò 5 (evaluation) | Xác nhận cả 3 lần gọi `evaluate_pipeline()` đều truyền `settings.paths.eval_testset` (`src/pipelines/corruption_flow.py:63,85`) — điều kiện tiên quyết để so sánh có nghĩa |
| Đối chiếu `corruption_log.json` × `test_set.json` để kiểm chứng chuỗi nhân quả nhóm viết trong report | Vai trò 2, 5, 6 | Phát hiện 4/10 câu hỏi trỏ vào paper bị corruption nhưng vẫn hit — sửa lại lập luận nhân quả của nhóm (chi tiết mục 5) |
| Kiểm tra reproducibility | Vai trò 3 (orchestration `phase1.py`/`corruption_flow.py`) | Xác nhận `phase1.py` đọc snapshot khi `refresh_source=false` (`_load_or_fetch_records`) và tái dùng test set khi `refresh_test_set=false` → chạy lại không làm trôi số liệu |

**Ghi chú minh bạch về ownership:** tôi **không** implement `phase1.py`, `corruption_flow.py`, `corruption.py`, `quality.py`, `reporting.py`, `cleaning.py`, `crossref.py` hay `testset.py`. Vai trò của tôi là định hướng phân chia deliverable, chốt contract giữa các module, và kiểm tra/review kết quả so với artifact thật trước khi nhóm nộp. Mọi kết luận ở mục 5, 6 và 8 dưới đây đều do tôi tự chạy đối chiếu trên artifact trong `data/`, không lấy lại kết luận của thành viên khác.

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --------------------- | --------------------------- | ---------------- | ------------- |
| Chia việc theo deliverable (không chia theo file) | `report/README.md` §4, `group_report.md` §3 | 7 khối, mỗi khối có owner + input + output + cách xác minh | Đối chiếu bảng phân công với file thật: mọi khối đều có artifact tương ứng trong `data/` |
| Chốt quy tắc "3 trạng thái, 3 bộ artifact riêng" | `src/core/config.py`, `data/clean/`, `data/quality/`, `data/results/` | 0 file bị ghi đè giữa baseline/corrupted/repaired | `ls data/clean` → 3 cặp csv/json; `ls data/quality` → 3 quality + 3 freshness report |
| Kiểm chứng metric trong report khớp JSON | `baseline_metrics.json`, `corrupted_metrics.json`, `repaired_metrics.json` | 4/4 metric × 3 trạng thái khớp bảng §10 group report | Đọc trực tiếp JSON (kết quả ở mục 8) |
| Kiểm chứng chuỗi nhân quả "corruption → metric" ở mức từng câu hỏi | `corrupted_answers.json` × `test_set.json` × `corruption_log.json` | Xác nhận đúng q1 và q9 miss, và đây là 2 câu duy nhất trỏ vào paper bị `drop_latest` | Script đối chiếu ở mục 4 |
| Review 4 report cá nhân + group report | `report/*.md` | 6 finding (3 nội dung, 3 thủ tục) kèm mức nghiêm trọng và cách sửa | Bảng finding ở mục 6 |
| Kiểm tra secret | `.gitignore`, `.env.example` | `.env` được ignore; repo chỉ có `.env.example`; không có key trong report/artifact | `cat .gitignore` → có dòng `.env`; `ls -a` → không có file `.env` được commit |

Nêu một output cụ thể mà phần việc của tôi tạo ra hoặc giúp xác minh:

Bảng review ở **mục 6** — cụ thể nhất là finding R1: ba văn bản của nhóm (`group_report.md` §9, `01047_PhamVanTam.md` §8, `01039_NguyenTienDat.md` §8) đều khẳng định "chỉ `drop_latest` có giao khác rỗng với test set" hoặc "paper bị `inject_noise`/`old_date` không nằm trong test set". Đối chiếu artifact cho thấy khẳng định này **sai**: 4/10 câu hỏi (q3, q4, q5, q6) trỏ đúng vào paper bị `inject_noise` và `old_date`. Kết luận đúng phải là: các corruption đó *có* chạm test set nhưng *không* đổi metric vì loại câu hỏi không đọc trường bị hỏng. Đây là finding buộc nhóm sửa lại lập luận nhân quả, không phải sửa số liệu.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Vai trò lead ở lab này có hai rủi ro chính, và cả hai đều không phải rủi ro code:

1. **Rủi ro tích hợp:** 6 người làm song song trên các module phụ thuộc trực tiếp vào schema của nhau (`paper_id`, `age_days`, `text_for_embedding`, `ground_truth_doc_ids`). Nếu không chốt contract trước, mỗi người sửa một cột thì downstream đo sai trạng thái mà không ai biết — đúng như lỗi `age_days` không được tính lại sau `old_date` mà vai trò 6 phát hiện.
2. **Rủi ro báo cáo sai sự thật:** Rubric và `README.md` §9 yêu cầu mọi kết luận phải có artifact. Nguy hiểm nhất không phải số sai — số của nhóm khớp artifact — mà là **lập luận nhân quả nghe hợp lý nhưng không được artifact hỗ trợ**. Kiểu lỗi này lan rất nhanh vì các thành viên chép lại kết luận của nhau.

### Cách triển khai

**(a) Định hướng — chia việc theo deliverable.** Tôi chia 7 khối (ingestion, cleaning, testset, quality/freshness, reporting, corruption/repair, orchestration) thay vì chia theo package. Mỗi khối bắt buộc khai báo 4 thứ: owner, input nhận vào, output bàn giao, cách xác minh. Thứ tự phụ thuộc được chốt cứng: ingestion → cleaning → testset → baseline → corruption → repair → compare; không ai được build index trước khi schema clean chốt xong.

**(b) Contract dùng chung.** Ba invariant tôi yêu cầu giữ:

- `paper_id` = DOI, ổn định xuyên suốt raw → clean → index → test set. Không sinh ID mới, không đổi ID (đây chính là lý do quality check bắt hụt duplicate `_dup` — xem finding R3).
- Artifact của 3 trạng thái phải tách đường dẫn/collection (`papers-baseline` / `-corrupted` / `-repaired`), không ghi đè, để so sánh sau này còn bằng chứng.
- Test set build **một lần** rồi đóng băng; chỉ rebuild khi bật `REFRESH_TEST_SET=1`.

**(c) Review — đối chiếu artifact thay vì đọc report.** Nguyên tắc tôi áp dụng: mọi câu trong report có dạng "X gây ra Y" đều phải truy được về một file trong `data/`. Tôi kiểm ba tầng: (1) số trong report ↔ số trong JSON; (2) chuỗi nhân quả ở mức tổng ↔ ở mức từng record/từng câu hỏi; (3) mọi ownership tuyên bố trong report ↔ file thật tồn tại trong repo.

### Input, output và contract

| Thành phần | Mô tả |
| ---------- | ----- |
| Input | `data/results/*.json`, `data/quality/*.json`, `data/reports/*.md`, `report/*.md`, `src/pipelines/*.py`, `.gitignore` |
| Output | Bảng phân công + contract (§1, §3 group report); 6 finding review (mục 6); kết luận release gate (mục 8) |
| Module phụ thuộc | Không sở hữu code runtime — phụ thuộc artifact do vai trò 2/3/5/6 sinh ra |
| Module sử dụng output | `group_report.md` (bảng phân công, §11 vấn đề tích hợp, §12 giới hạn); các report cá nhân phải sửa theo finding |
| Điều kiện lỗi cần xử lý | Report mô tả không khớp artifact; ownership tuyên bố cho file không tồn tại; placeholder chưa điền; secret lọt vào repo |

### Cách xác minh

Lệnh tôi dùng để kiểm chuỗi nhân quả ở mức từng câu hỏi (không sửa code, chỉ đọc artifact):

```bash
python -c "
import json
ts  = json.load(open('data/eval/test_set.json', encoding='utf-8'))
log = json.load(open('data/results/corruption_log.json', encoding='utf-8'))
ans = json.load(open('data/results/corrupted_answers.json', encoding='utf-8'))
affected = {c['type']: set(c['paper_ids']) for c in log['corruptions']}
hit = {a['id']: a['retrieval_hit'] for a in ans}
for q in ts:
    ids  = set(q['ground_truth_doc_ids'])
    tags = [t for t, s in affected.items() if ids & s]
    print(q['id'], q['question_type'], 'hit=' + str(hit[q['id']]), tags)
"
```

- **Kết quả mong đợi (theo report của nhóm):** chỉ q1 và q9 giao với corruption, và cả hai đều `hit=False`.
- **Kết quả thực tế:**

  | Câu | Loại | `retrieval_hit` (corrupted) | Corruption chạm vào paper |
  | --- | ---- | --------------------------- | ------------------------- |
  | q1 | authors | False | `drop_latest` |
  | q2 | summary | True | — |
  | q3 | date | True | `inject_noise` |
  | q4 | authors | True | `old_date` |
  | q5 | summary | True | `old_date` |
  | q6 | authors | True | `inject_noise` |
  | q7 | summary | True | — |
  | q8 | date | True | — |
  | q9 | authors | False | `drop_latest` |
  | q10 | summary | True | — |

  Phần "chỉ q1, q9 miss" **khớp**. Phần "chỉ `drop_latest` giao với test set" **không khớp** — 4 câu nữa cũng chạm corruption. Đây là finding R1.
- **Artifact/log:** `data/eval/test_set.json`, `data/results/corruption_log.json`, `data/results/corrupted_answers.json` (không chứa secret).

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Khi review, tôi thấy cả group report lẫn hai report cá nhân đều dùng chung một lập luận: "`inject_noise`/`truncate_title` không làm hỏng metric vì paper bị tác động không nằm trong test set". Lập luận này gọn, nghe hợp lý, và đã được viết vào 3 văn bản. Câu hỏi đặt ra: chấp nhận cho qua (số liệu vẫn đúng) hay bắt sửa (tốn công sửa 3 file sát giờ nộp)?
- **Các phương án đã cân nhắc:** (1) giữ nguyên, vì bảng metric không sai và giám khảo có thể không kiểm tới mức từng câu hỏi; (2) chỉ ghi chú thêm ở mục "Giới hạn" của group report; (3) bắt sửa lập luận ở cả 3 văn bản và ghi rõ cơ chế thật.
- **Phương án đã chọn:** (3), kèm ghi rõ cơ chế thay thế trong mục 8 của report này để nhóm có sẵn câu chữ đúng để dùng.
- **Lý do:** `README.md` §9 và Rubric đều chấm "kết luận dựa trên artifact", không chấm "kết luận nghe hợp lý". Một lập luận sai về *cơ chế* nguy hiểm hơn một con số sai, vì nó dạy cả nhóm một mô hình sai: "corruption chỉ nguy hiểm khi trúng test set". Mô hình đúng là: **corruption chỉ đo được khi trúng đúng trường mà loại câu hỏi đọc tới** — q3 hỏi ngày trong khi noise nằm ở summary, q4/q5 có `published` bị đẩy về 2010 nhưng câu hỏi đọc `authors`/`summary` nên answer vẫn đúng. Hệ quả thực tế cũng khác nhau: mô hình sai dẫn tới "mở rộng test set là đủ", mô hình đúng dẫn tới "phải phủ đủ *cặp* (trường bị hỏng × loại câu hỏi)".
- **Bằng chứng quyết định phù hợp:** bảng 10 câu ở mục 4 — 4 câu (q3, q4, q5, q6) trỏ vào paper có trong `corruption_log.json` mà vẫn `retrieval_hit=True`, `token_f1=1.0`, `judge score=5`. Nếu lập luận cũ đúng thì 4 câu này không được phép tồn tại.

## 6. Một lỗi hoặc blocker đã xử lý

Ở vai trò review, "lỗi" tôi xử lý là lỗi ở tầng báo cáo và thủ tục nộp bài. Dưới đây là toàn bộ finding, xếp theo mức nghiêm trọng.

| ID | Finding | Bằng chứng | Mức | Cách sửa |
| -- | ------- | ---------- | --- | -------- |
| R1 | 3 văn bản khẳng định "chỉ `drop_latest` giao với test set" / "paper bị noise không nằm trong test set" — sai | `corruption_log.json` × `test_set.json`: q3, q6 trỏ vào paper `inject_noise`; q4, q5 trỏ vào paper `old_date` | Cao | Thay bằng: các corruption đó *có* chạm test set nhưng không đổi metric vì loại câu hỏi không đọc trường bị hỏng (mục 8) |
| R2 | Con số "corrupted 21 dòng" bị hiểu là hệ quả của riêng `drop_latest` | `corruption_log.json`: `drop_latest` ghi `before=24, after=20`; `duplicate_rows` thêm 1 → 21. Quality report corrupted `row_count=21` | Trung bình | Ghi rõ 24 − 4 + 1 = 21, tránh đọc nhầm là "xoá 3 dòng" |
| R3 | Quality check báo `duplicate_rows=0` dù có 1 bản sao nội dung | `quality_report_corrupted.json`: `duplicate_rows.duplicate_rows=0`, subset `[paper_id, title]`; log có `duplicate_rows` cho `10.35314/3y9hy151` với hậu tố `_dup` | Trung bình (đã được nhóm ghi nhận) | Giữ trong mục Giới hạn; không được diễn giải là "đã phát hiện duplicate" — cả 3 report đã ghi đúng, xác nhận pass |
| R4 | `01047_PhamVanTam.md` §2 khai một Streamlit dashboard `app/` | `ls` tại repo root: không có thư mục `app/` | Trung bình | Xoá dòng đó hoặc commit code dashboard — vi phạm `README.md` §9 "không nhận ownership cho file mình không trực tiếp thực hiện / chưa có output kiểm chứng" |
| R5 | `2A202601309_NguyenQuangKhai.md` để Repository là đường dẫn máy cá nhân `D:\AI_in_Action\...` và dòng ký tên còn `[Điền họ và tên]` | Đọc file, dòng 14 và 160 | Thấp | Thay bằng URL GitHub của nhóm; điền tên |
| R6 | Tên nhóm không thống nhất: `group_report.md` ghi "Nhóm 6", các report cá nhân ghi "Nxust"; bảng thành viên trong group report vẫn còn `[Họ tên]`/`[MSSV]` | `group_report.md` §1 | Thấp (nhưng chặn nộp) | Chốt một tên nhóm; điền đủ 6 dòng thành viên — đây là mục đầu tiên của Definition of Done |

Chi tiết một finding đã xử lý trọn vẹn (R1):

- **Triệu chứng:** report của nhóm giải thích được vì sao metric giảm, nhưng phần giải thích "vì sao các corruption khác *không* làm giảm" dựa trên tiền đề chưa ai kiểm.
- **Bước tái hiện:** chạy script ở mục 4.
- **Nguyên nhân gốc:** kết luận được suy từ một mẫu nhỏ (2 paper `truncate_title` thật sự không nằm trong test set) rồi khái quát cho cả 4 loại corruption còn lại, và sau đó được chép qua giữa các report thay vì mỗi người tự kiểm.
- **Cách xử lý:** đưa bảng 10 câu × corruption tag làm bằng chứng, đề xuất câu chữ thay thế, gửi lại cho vai trò 5 và 6 sửa mục 8 của họ.
- **Cách xác minh sau khi sửa:** chạy lại script; bất kỳ câu nào có tag corruption mà `hit=True` phải được giải thích bằng cặp (trường bị hỏng, trường câu hỏi đọc), không được giải thích bằng "không nằm trong test set".
- **Điều học được:** trong nhóm 6 người, kết luận lan nhanh hơn bằng chứng. Vai trò review phải kiểm **tiền đề của lập luận**, không chỉ kiểm con số — vì con số thì mọi người đều copy từ cùng một JSON nên luôn "khớp", còn tiền đề thì không ai kiểm.

## 7. Hiểu biết về luồng end-to-end

1. **Dữ liệu từ Crossref đến vector index:** `crossref.py` gọi Crossref REST `/works` với retry/backoff cho 429/503, lưu raw response nguyên bản (audit) rồi parse thành `PaperRecord` với `paper_id` = DOI. `cleaning.py::build_clean_dataframe` strip thẻ JATS, join authors/categories, parse `published`, tính `age_days`, dựng `text_for_embedding`, drop record thiếu title/summary và dedupe. `retrieval/index.py::LocalEmbeddingIndex.build` embed bằng `all-MiniLM-L6-v2` và ghi vào Chroma (cosine) với collection riêng cho từng trạng thái, kèm manifest JSON trong `data/embeddings/`.
2. **Evaluation set và ground-truth document IDs:** `testset.py::build_test_set` chọn 10 paper từ clean dataframe, sinh câu hỏi 4 loại (`authors`/`summary`/`date`/`categories`) khớp với nhánh route trong `qa.py::_extract_answer`, và gán `ground_truth_doc_ids = [paper_id]` lấy trực tiếp từ dataframe — không bịa ID. Nhờ vậy `retrieval_hit` đo đúng việc index có tìm lại đúng document hay không, còn `token_f1` đo answer so với ground truth trích nguyên văn từ chính row đó.
3. **Quality checks khác freshness monitoring:** quality checks (`run_data_quality_checks`) đo tính toàn vẹn **cấu trúc tại một thời điểm** — row count, null/duplicate `paper_id`, missing title, missing/short summary, duplicate rows. Freshness (`build_freshness_report`) đo **chiều thời gian** — `age_days` so với ngưỡng 180 ngày, `latest/oldest_published`, `stale_rows`. Hai chiều độc lập: dataset có thể đủ dòng, không null, mà vẫn toàn dữ liệu cũ. Trong lab này `blank_summary` đánh vào quality còn `old_date` đánh vào freshness — cần cả hai signal mới phủ hết 6 loại corruption.
4. **Vì sao phải dùng cùng test set:** ground truth gắn cứng vào `paper_id`; nếu đổi câu hỏi hoặc đổi ground truth giữa các phase thì delta metric không còn quy được về corruption. Đây là contract tôi chốt cứng ngay từ đầu và đã verify trong code: cả ba lần gọi `evaluate_pipeline()` trong `corruption_flow.py` đều truyền cùng `settings.paths.eval_testset`, và `phase1.py` chỉ rebuild test set khi `refresh_test_set` bật.
5. **Repair được coi là thành công dựa trên:** ba điều kiện đồng thời, không chỉ nhìn số trung bình. (a) Repaired dataset phải được **tái dựng từ raw snapshot** (`_repair_from_raw` đọc `data/raw/crossref_records.json` rồi gọi lại `build_clean_dataframe`), không sửa tay corrupted data hay answers; (b) quality + freshness của repaired phải pass (`quality_report_repaired.json` `passed=true`, `freshness_report_repaired.json` `is_fresh=true`, 24 dòng, 0 stale); (c) **từng câu** bị miss ở corrupted phải quay lại `retrieval_hit=true` — tôi kiểm ở mức record chứ không chỉ mức trung bình, để loại trừ trường hợp trung bình đúng do bù trừ.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ------------- | -------: | --------: | -------: | -------------------- |
| `retrieval_hit_rate` | 1.000 | 0.800 | 1.000 | Đã verify ở mức từng câu: đúng q1, q9 `retrieval_hit=false`, 8 câu còn lại `true` — trung bình không che giấu gì |
| `mean_token_f1` | 1.000 | 0.800 | 1.000 | `corrupted_answers.json`: `token_f1=0.0` đúng tại q1, q9; 8 câu còn lại đúng 1.0 — phân bố nhị phân, không có câu "gần đúng" |
| `judge_accuracy` | 1.000 | 0.800 | 1.000 | Trùng khít `mean_token_f1` vì judge đang chạy fallback heuristic — phải đọc kèm cảnh báo ở §12 group report, không được trình bày như LLM chấm độc lập |
| `mean_judge_score` | 5 | 4.200 | 5 | Kiểm lại bằng tay: 8 câu × 5 + 2 câu × 1 = 42 → 4.2. Khớp |
| Quality checks | pass (24 dòng) | fail (21 dòng) | pass (24 dòng) | Corrupted fail đúng 2/6 check: `summary.missing_count=1`, `freshness.stale_count=2`. 4 check còn lại pass |
| Freshness status | fresh (0/24 stale) | stale (2/21) | fresh (0/24) | `freshness_report_corrupted.json`: `oldest_published=2010-01-01`, `is_fresh=false` |

Kết quả kiểm chứng của tôi: **4/4 metric × 3 trạng thái trong `group_report.md` §10 khớp đúng file JSON trong `data/results/`; bảng quality/freshness khớp `data/quality/`; `corruption_report.md` khớp cả hai.** Không có số nào bị làm tròn sai hướng hay chép nhầm. Mục 13 checklist của group report ở phần số liệu là hợp lệ.

### Kết luận từ số liệu

1. **`drop_latest` → mất document khỏi index → sụt metric, và đây là cơ chế duy nhất có bằng chứng.** `corruption_log.json` ghi 4 paper bị xoá, trong đó `10.2118/234689-pa` (ground truth của q1) và `10.47576/2949-1894.2026.7.7.023` (ground truth của q9). Hai câu này là đúng 2 câu có `retrieval_hit=false` trong `corrupted_answers.json`, kéo `retrieval_hit_rate` và `mean_token_f1` từ 1.0 → 0.8 và `mean_judge_score` 5 → 4.2. Song song, `blank_summary` (1 record) và `old_date` (2 record) làm `quality_report_corrupted.json` `passed=false` — đúng 2 check fail, không nhiều hơn.
2. **Repair từ raw snapshot → phục hồi 100%, và phục hồi này có tính nhân quả chứ không phải trùng hợp.** `_repair_from_raw` không đụng tới corrupted data mà chạy lại `build_clean_dataframe` trên `data/raw/crossref_records.json` — file không hề bị corruption chạm vào giữa các phase. Kết quả: 24 dòng, quality pass, freshness fresh, và ở mức từng câu thì q1/q9 quay lại `retrieval_hit=true` với answer khớp verbatim. Vì repaired được dựng độc lập với corrupted, mức phục hồi 100% phản ánh chất lượng nguồn, không phải việc vá kết quả.

**Corruption nào ảnh hưởng rõ nhất và vì sao — có sửa lại lập luận của nhóm:** rõ nhất ở tầng agent là `drop_latest`, vì nó xoá hẳn document khỏi index nên không tầng nào phía sau cứu được. Nhưng lý do 5 loại còn lại "vô hình" **không phải** vì chúng không chạm test set — bằng chứng ở mục 4 cho thấy 4/10 câu hỏi trỏ đúng vào paper bị `inject_noise` và `old_date`. Cơ chế thật là **không trùng trường**: q3 hỏi ngày xuất bản trong khi noise nằm ở `summary`; q6 hỏi tác giả trong khi noise cũng ở `summary`; q4/q5 có `published` bị đẩy về 2010-01-01 nhưng câu hỏi đọc `authors`/`summary` nên answer vẫn đúng nguyên văn. Nói cách khác, một corruption chỉ trở thành *observable* ở tầng agent khi trúng cả hai: (a) record nằm trong test set, **và** (b) trường bị hỏng đúng là trường mà loại câu hỏi đọc tới. `old_date` là ví dụ đẹp cho việc quality/freshness bắt được thứ mà evaluation hoàn toàn không thấy — đây chính là lý do lab bắt làm cả hai tầng signal thay vì chỉ chạy metric.

**Kết quả nào khác với kỳ vọng ban đầu?** Kỳ vọng của tôi khi phân công là "corrupt càng nhiều loại thì metric càng tệ". Thực tế: 6 loại corruption chạm 12 record (một nửa dataset) nhưng chỉ 1 loại làm đổi metric. Điều này lật ngược một giả định nguy hiểm — **metric agent im lặng không có nghĩa dữ liệu lành**. Nếu nhóm chỉ theo dõi `retrieval_hit_rate`, ta sẽ kết luận "dataset còn tốt 80%" trong khi thực tế 1 summary rỗng, 2 record cũ 16 năm, 2 title bị cắt và 1 dòng nhân bản đã trôi vào production index. Đúng nghĩa của observability trong lab này: quality/freshness là tầng bắt lỗi *trước khi* nó chạm tới người dùng, còn eval metric là tầng bắt lỗi *sau khi* đã chạm. Ngoài ra, giới hạn `duplicate_rows` (finding R3) là ví dụ ngược lại: check tồn tại nhưng khoá kiểm tra bị chính corruption làm biến dạng — check chỉ tốt bằng giả định về khoá của nó.

### Kết luận release gate (Definition of Done)

| Mục | Trạng thái | Ghi chú |
| --- | ---------- | ------- |
| Danh sách thành viên, vai trò, output từng người | **Chưa đạt** | `group_report.md` §1 còn `[Họ tên]`/`[MSSV]`; tên nhóm chưa thống nhất (R6) |
| Mỗi deliverable có owner và output rõ ràng | Đạt | 7 khối trong §3 đều có artifact tương ứng tồn tại thật |
| Chạy lại toàn bộ pipeline từ hướng dẫn chung | Đạt | `uv sync` → `run_phase1.py` → `run_corruption_flow.py`; snapshot mode giữ số liệu ổn định |
| Group report khớp code/artifact/metrics | Đạt về số liệu, **cần sửa lập luận** | Số 4/4 × 3 trạng thái khớp; §9 cần sửa theo R1, R2 |
| Mỗi thành viên có report riêng | Đạt sau khi thêm file này | 6/6 vai trò đã có report; cần sửa R4, R5 |
| Mọi thành viên giải thích được end-to-end | Đạt | 5/5 câu ở mục 7 của các report đều có nội dung riêng, không sao chép nguyên văn |
| Không có `.env`/API key/secret | Đạt | `.gitignore` có `.env`; repo chỉ có `.env.example`; không tìm thấy key trong `report/`, `data/`, log |

Kết luận của tôi với tư cách release owner: **chưa được nộp cho tới khi R6 (điền thành viên, chốt tên nhóm) và R1 (sửa lập luận nhân quả) được xử lý**; R4, R5 nên sửa cùng lượt. R2, R3 chỉ cần ghi chú, không chặn.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. **Về data pipeline:** contract quan trọng hơn code. Gần như mọi sự cố tích hợp của nhóm đều là cùng một lỗi — một cột bị sửa mà cột dẫn xuất không được tính lại (`published` → `age_days`, `summary` → `summary_chars` → `text_for_embedding`). Bài học cho lần sau: khi chốt schema, chốt luôn danh sách **cột dẫn xuất và hàm tái tính** của từng cột gốc, coi đó là một phần của contract chứ không phải chi tiết cài đặt.
2. **Về data quality/observability:** không được kết luận "dữ liệu lành" từ việc metric agent không đổi. 12/24 record bị corruption mà `retrieval_hit_rate` chỉ giảm vì 1 loại — quality và freshness là hai tầng độc lập bắt đúng những gì eval không thấy. Ngược lại, mỗi check cũng chỉ tốt bằng giả định về khoá của nó (`duplicate_rows` mù trước hậu tố `_dup`).
3. **Về vai trò review trong nhóm:** con số luôn "khớp" vì mọi người copy từ cùng một JSON; thứ cần kiểm là **tiền đề của lập luận** và **ownership tuyên bố**. Ba finding có giá trị nhất của tôi (R1, R4, R5) đều không phát hiện được nếu chỉ so bảng metric — phải mở artifact ra đối chiếu ở mức từng record và mở repo ra kiểm file có tồn tại thật không.

### Nếu có thêm thời gian

Tôi sẽ xây một **script kiểm tra nhất quán tự động** (`script/check_report_consistency.py`) chạy trước khi nộp, làm 3 việc: (1) parse mọi bảng metric trong `report/*.md` và `data/reports/*.md` rồi so với `data/results/*.json`, fail nếu lệch; (2) sinh bảng "câu hỏi × corruption tag × hit" như ở mục 4 để mọi lập luận nhân quả buộc phải đối chiếu với nó; (3) quét placeholder chưa điền (`[Họ tên]`, `[MSSV]`, `[Điền...]`) và đường dẫn máy cá nhân (`C:\`, `D:\`) trong `report/`. Cách đo hiệu quả: chạy script trên bản repo hiện tại, nó phải bắt được đúng R2, R5, R6 mà tôi đang phải tìm bằng tay — nếu bắt đủ thì lần sau khâu review tốn vài giây thay vì cả buổi, và quan trọng hơn là không phụ thuộc vào việc người review có chịu mở artifact ra hay không.

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi "đã chạy thành công" cho phần chưa được kiểm chứng.
- [x] Tôi không nhận ownership cho file hoặc hàm mà mình không trực tiếp thực hiện (xem ghi chú minh bạch ở mục 2).
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Nguyễn Khánh Bảo Châu
**Ngày xác nhận:** 2026-08-06
