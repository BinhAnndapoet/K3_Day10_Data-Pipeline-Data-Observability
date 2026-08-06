# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Phạm Văn Tâm             |
| MSSV               | 2A202601047                     |
| Khóa/Lớp         | K3              |
| Tên nhóm         | Nxust     |
| Vai trò chính    | Observability owner (vai trò 6)                 |
| Repository         | https://github.com/BinhAnndapoet/K3_Day10_Data-Pipeline-Data-Observability |
| Ngày hoàn thành | 2026-08-06               |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao  | Trạng thái                                 |
| ------------------ | --------------------- | ---------------- | ----------------- | -------------------------------------------- |
| Data quality checks | `src/observability/quality.py` — `run_data_quality_checks` | Clean/corrupted/repaired dataframe + `Settings` + `report_name` | `data/quality/quality_report_{baseline,corrupted,repaired}.json` | Hoàn thành |
| Freshness report | `src/observability/quality.py` — `build_freshness_report` | Dataframe (`published`/`age_days`) + `Settings` | `data/quality/freshness_report{,_corrupted,_repaired}.json` | Hoàn thành |
| Baseline report (tiếng Việt) | `src/observability/reporting.py` — `generate_phase1_report` | `source_summary`, metrics, quality, freshness | `data/reports/phase1_report.md` | Hoàn thành |
| Corruption comparison report | `src/observability/reporting.py` — `generate_corruption_report` | Metrics/quality/freshness của 3 trạng thái | `data/reports/corruption_report.md` | Hoàn thành |
| Corruption log dùng cho truy vết | Phối hợp với `src/ingestion/corruption.py` — format log (type, parameter, paper_ids) | Clean dataframe + `Settings` | `data/results/corruption_log.json` | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động                         | Thành viên/module được hỗ trợ | Kết quả                    |
| ------------------------------------ | ------------------------------------ | ---------------------------- |
| Fix freshness sai sau corruption | `src/ingestion/corruption.py` (clean/corruption owner) | Thêm `_recompute_age_days` tính lại `age_days` sau khi đẩy `published` về 2010-01-01; `_sync_summary_chars` re-sync `summary_chars` sau blank/noise — freshness/quality phản ánh đúng damage (stale 2, summary missing 1) |
| Streamlit dashboard thể hiện quality/freshness | Lead — toàn bộ repo | Trang So sánh hiển thị verdict quality/freshness 3 trạng thái đọc trực tiếp từ `data/quality/` |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao       | Cách xác minh         |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| Chạy quality checks baseline | `data/quality/quality_report_baseline.json` | pass — 24 dòng, 0 null/dup/missing, 0 stale | Đọc JSON: `passed: true`, 6/6 checks pass |
| Chạy quality checks corrupted | `data/quality/quality_report_corrupted.json` | fail — summary missing 1, freshness stale 2 | Đọc JSON: `passed: false`, 2 checks fail |
| Chạy quality checks repaired | `data/quality/quality_report_repaired.json` | pass — 24 dòng, mọi check sạch | Đọc JSON: `passed: true` |
| Freshness baseline/corrupted/repaired | `freshness_report.json`, `freshness_report_corrupted.json`, `freshness_report_repaired.json` | baseline fresh (0 stale), corrupted stale 2 (oldest 2010-01-01), repaired fresh | `is_fresh: true/false/true`; `oldest_published` |
| Sinh báo cáo tiếng Việt | `data/reports/phase1_report.md`, `corruption_report.md` | 2 report tiếng Việt, số khớp JSON artifact | So khớp số trong report với `data/results/*_metrics.json` |

Nêu một output cụ thể mà phần việc của bạn tạo ra hoặc giúp xác minh:

`data/quality/quality_report_corrupted.json` — báo cáo duy nhất bắt được 2 tín hiệu quality suy giảm sau corruption: `summary.missing_count = 1` (blank_summary) và `freshness.stale_count = 2` (old_date). Đây là bằng chứng quan trọng cho chuỗi nhân quả "data xấu → quality signal xấu → agent metric xấu" và được trích dẫn trong `corruption_report.md`.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Vai trò observability phải trả lời: làm sao chứng minh "dữ liệu xấu làm RAG kém đi" bằng số liệu? Cần định nghĩa các tín hiệu (signals) đo được trước corruption (baseline), sau corruption và sau repair — và phải tách riêng artifact cho 3 trạng thái để so sánh công bằng, không ghi đè lẫn nhau.

### Cách triển khai

- `run_data_quality_checks(df, settings, report_name)` chạy 6 check cấu trúc: `row_count`, `paper_id` (null + duplicate), `title` missing, `summary` missing/short (ngưỡng 40 ký tự), `duplicate_rows` (theo subset paper_id+title), `freshness` (age_days > 180). Mỗi check trả `passed` bool; report tổng `passed` = all(checks). Tham số `report_name` ghi vào tên file (`quality_report_{report_name}.json`) nên baseline/corrupted/repaired không bao giờ ghi đè nhau.
- `build_freshness_report` đọc `published` (parse thành datetime) và `age_days` từ chính dataframe — không giả định ngày hiện tại; xuất `latest_published`, `oldest_published`, `stale_rows`, `is_fresh`.
- `generate_phase1_report`/`generate_corruption_report` đọc số liệu từ các JSON artifact thật, render markdown tiếng Việt (tiêu đề, bảng, nhãn check được dịch; bool `có`/`không`). Metric names giữ nguyên tên kỹ thuật để đối chiếu dễ.

### Input, output và contract

| Thành phần                   | Mô tả                                     |
| ------------------------------ | ------------------------------------------- |
| Input                          | Dataframe clean/corrupted/repaired (cột bắt buộc: `paper_id`, `title`, `summary`, `published`, `age_days`, `text_for_embedding`) + `Settings` + `report_name` |
| Output                         | JSON: `{report_name, generated_at, row_count, passed, checks{...}}` cho quality; `{latest_published, oldest_published, stale_rows, total_rows, freshness_threshold_days, is_fresh}` cho freshness; markdown tiếng Việt cho report |
| Module phụ thuộc             | `src/ingestion/cleaning.py` (tạo `age_days`, `summary_chars`), `src/pipelines/phase1.py` và `corruption_flow.py` (gọi quality/freshness theo từng state) |
| Module sử dụng output        | `src/pipelines/*` (truyền vào report), dashboard Streamlit `app/` (đọc trực tiếp JSON) |
| Điều kiện lỗi cần xử lý | Thiếu cột → check trả `passed: false` kèm count thay vì crash; `published` sai định dạng → `pd.to_datetime(errors="coerce")` thành NaT, đếm vào `unknown` |

### Cách xác minh

```bash
PYTHONPATH=src python -c "
from core.config import load_settings
from observability.quality import run_data_quality_checks, build_freshness_report
s = load_settings()
# baseline / corrupted / repaired dataframes
q = run_data_quality_checks(df_corrupted, s, 'corrupted')
f = build_freshness_report(df_corrupted, s, s.paths.quality_dir / 'freshness_report_corrupted.json')
print(q['passed'], f['stale_rows'])
"
```

- **Kết quả mong đợi:** corrupted → `passed=False`, `stale_rows=2`.
- **Kết quả thực tế:** `False 2` — khớp.
- **Artifact/log:** `data/quality/quality_report_corrupted.json`, `data/quality/freshness_report_corrupted.json` (không chứa secret).

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Freshness report của corrupted ban đầu báo `is_fresh = true` dù 2 dòng đã bị đẩy `published` về `2010-01-01` — dữ liệu cũ trôi qua mà observability không bắt được.
- **Các phương án đã cân nhắc:** (1) Sửa check freshness để tính trực tiếp từ `published` mỗi lần chạy, bỏ qua cột `age_days`; (2) Yêu cầu corruption tính lại `age_days` sau khi đổi `published` — giữ `age_days` là nguồn chân lý duy nhất.
- **Phương án đã chọn:** (2) — thêm `_recompute_age_days()` trong `src/ingestion/corruption.py`, gọi ngay sau bước `old_date`.
- **Lý do:** Giữ contract "`age_days` phản ánh `published` hiện tại" làm bất biến (invariant) — mọi nơi đọc `age_days` (quality check, freshness, report) đều đúng mà không phải sửa 4 nơi; đồng thời repair chạy lại cleaning từ raw cũng tự khôi phục `age_days` đúng. Phương án (1) tách logic freshness khỏi cột chuẩn, dễ lệch giữa các module.
- **Bằng chứng quyết định phù hợp:** sau fix, `freshness_report_corrupted.json` có `is_fresh=false`, `oldest_published=2010-01-01`, `stale_rows=2`; quality check `freshness.passed=false` — khớp tín hiệu kỳ vọng từ log corruption.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** corruption flow báo `Freshness report: is_fresh=True stale_rows=0/21` dù log corruption ghi `old_date` cho 2 paper với `target_date: "2010-01-01"` — báo cáo comparison không thấy dấu hiệu dữ liệu cũ.
- **Lệnh hoặc bước tái hiện:** `PYTHONPATH=src python script/run_corruption_flow.py` rồi đọc `data/quality/freshness_report_corrupted.json`.
- **Nguyên nhân gốc:** corruption `old_date` chỉ sửa cột `published`; cột `age_days` giữ giá trị cũ. Quality check `freshness` đọc `age_days` nên không phát hiện 2 dòng đã thành stale. Cùng nhóm lỗi: blank/noise đổi `summary` nhưng `summary_chars` không re-sync.
- **Cách xử lý:** thêm `_recompute_age_days(df)` (tính lại `age_days` từ `published` theo ngày chạy) gọi sau bước `old_date`, và `_sync_summary_chars(df)` gọi sau `blank_summary`/`inject_noise` trong `src/ingestion/corruption.py`.
- **Cách xác minh sau khi sửa:** chạy lại corruption flow → `Freshness report: is_fresh=False stale_rows=2/21`; quality corrupted `passed=False`; `corruption_report.md` cập nhật bảng freshness corrupted `no / 2 / 21`.
- **Điều học được:** quality checks chỉ tốt bằng dữ liệu chúng đọc — khi corruption sửa một cột, mọi cột dẫn xuất (age_days, summary_chars, text_for_embedding) phải được tái tính, nếu không observability báo "mọi thứ ổn" trong khi dữ liệu đã hỏng. Đây chính là lý do lab yêu cầu "signal kỳ vọng trước, đo sau".

## 7. Hiểu biết về luồng end-to-end

**Câu trả lời:**

1. **Dữ liệu từ Crossref đến vector index:** `crossref.py` fetch API Crossref (retry/backoff 429/503), lưu raw response + parse thành `PaperRecord` với `paper_id` ổn định (DOI). `cleaning.py` chuẩn hoá title/summary/authors/categories, dedupe, tính `age_days`, ghép `text_for_embedding`. `index.py` embedding bằng MiniLM qua Chroma cosine — collection riêng cho từng trạng thái (`papers-baseline`/`-corrupted`/`-repaired`), kèm manifest JSON.
2. **Evaluation set và ground-truth doc IDs:** `testset.py` chọn 10 paper từ clean data, mỗi câu hỏi (`authors`/`summary`/`date`/`categories`) kèm `ground_truth` trích nguyên văn từ clean row và `ground_truth_doc_ids` = `paper_id` thật (không bịa). `qa.py` retrieval top-k rồi trả lời; `retrieval_hit` = ground-truth doc có trong top-k; token F1 so answer với ground truth; judge chấm đúng/sai.
3. **Quality checks khác freshness monitoring:** quality checks đo cấu trúc/tính hợp lệ tĩnh — row count, null, duplicate, missing title/summary, duplicate rows. Freshness đo chiều thời gian — `age_days` có vượt ngưỡng 180 ngày không, dữ liệu mới nhất/cũ nhất. Trong lab, corruption `blank_summary` đánh vào quality còn `old_date` đánh vào freshness — 2 loại tín hiệu bắt 2 loại hư hỏng khác nhau.
4. **Phải dùng cùng test set:** test set gắn ground truth vào `paper_id` cụ thể; nếu đổi câu hỏi hay ground truth giữa các phase thì chênh lệch metric là do test set, không còn do corruption. Giữ nguyên (file `data/eval/test_set.json` chỉ build một lần) là điều kiện để delta baseline→corrupted→repaired có ý nghĩa nhân quả.
5. **Repair thành công dựa trên:** repaired metrics khôi phục về baseline (`retrieval_hit_rate` 0.8→1.0, `mean_token_f1` 0.8→1.0, `judge_accuracy` 0.8→1.0, `mean_judge_score` 4.2→5) đồng thời `quality_report_repaired.json` pass và `freshness_report_repaired.json` fresh (0 stale, 24 dòng). Quan trọng: repaired data được tái dựng từ raw snapshot bằng cùng đường cleaning — không sửa tay answers.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal          | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | ------------------------- |
| `retrieval_hit_rate` |  1.000 |  0.800 |  1.000 | 2/10 câu miss vì paper ground-truth bị drop_latest — thấy rõ qua answers |
| `mean_token_f1`      |  1.000 |  0.800 |  1.000 | F1 0 đúng tại 2 câu miss; câu khác vẫn 1.0 |
| `judge_accuracy`     |  1.000 |  0.800 |  1.000 | Judge fallback heuristic nên chấm theo F1 |
| `mean_judge_score`   |  5 |  4.200 |  5 | 2 câu miss kéo trung bình xuống 0.8 điểm |
| Quality checks         |  pass |  fail |  pass | Corrupted: summary missing 1 + freshness stale 2 — chính là blank_summary + old_date |
| Freshness status       |  fresh |  stale (2) |  fresh | Oldest published corrupted là 2010-01-01 — tín hiệu dữ liệu cũ rõ ràng |

### Kết luận từ số liệu

1. **`drop_latest` xoá 4 records trong đó có 2 paper thuộc test set** (`10.2118/234689-pa` ở q1, `10.47576/2949-1894.2026.7.7.023` ở q9 — đối chiếu `corruption_log.json` với `test_set.json`) → quality `row_count` 24→21 → `retrieval_hit_rate` 1.0→0.8 và `mean_token_f1` 1.0→0.8. Cùng lúc `blank_summary` + `old_date` → quality fail (summary missing 1) và freshness stale 2.
2. **Repair re-run cleaning từ raw snapshot** → `papers_clean_repaired.csv` 24 dòng, summary đủ, `age_days` đúng → `quality_report_repaired.json` pass, `freshness_report_repaired.json` fresh (0 stale) → retrieval + answer khôi phục đúng baseline (hit 1.0, F1 1.0, judge 1.0, score 5). Phục hồi 100% vì raw snapshot không bị corrupt.

**Corruption nào ảnh hưởng rõ nhất và vì sao?** `drop_latest` — vì nó là corruption duy nhất làm thay đổi metric agent (2 câu miss retrieval), còn các loại khác (blank_summary, old_date) chỉ làm fail quality/freshness signals. Lý do: test set chọn paper theo "freshest first", nên paper mới nhất bị drop đúng trúng ground-truth docs. Ảnh hưởng lớn nhất cũng vì nó xoá dữ liệu hoàn toàn, không thể "sửa" một cột như các loại khác.

**Kết quả nào khác với kỳ vọng ban đầu?** `inject_noise` và `truncate_title` không làm metric hay quality fail — vì 2 paper bị noise/truncate không nằm trong test set và quality check không đo nội dung. Giả thuyết: corruption chỉ ảnh hưởng observable khi chạm đúng record được đo. Đã kiểm tra bằng cách đối chiếu `paper_ids` trong `corruption_log.json` với `ground_truth_doc_ids` trong `test_set.json` — chỉ `drop_latest` có giao khác rỗng. Ngoài ra duplicate `_dup` lọt qua check `paper_id` (suffix khác ID) — giới hạn của check, ghi vào hướng cải thiện.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. **Data pipeline:** mọi biến đổi dữ liệu phải tái tính cột dẫn xuất (age_days, summary_chars, text_for_embedding) — nếu không các check sau nguồn sẽ đọc giá trị cũ và báo sai trạng thái.
2. **Data quality/observability:** quality check và freshness đo 2 chiều khác nhau — cấu trúc vs thời gian; cần cả hai để bắt đủ 6 loại corruption. Log corruption với `paper_ids` cụ thể là cầu nối giữa "dữ liệu bị gì" và "metric đổi vì sao".
3. **Ảnh hưởng của data đến RAG agent:** chỉ cần 2/24 record (8%) bị xoá mà trúng paper trong test set là retrieval hit rate sụt 20% — tác động của data quality lên RAG là không tuyến tính và phụ thuộc độ phủ giữa dữ liệu hỏng và câu hỏi.

### Nếu có thêm thời gian

Thêm check content-based: đếm token độc đáo của `text_for_embedding` để bắt `inject_noise`/`truncate_title` (hiện 2 corruption này trôi qua). Cách đo: chạy corruption từng loại riêng lẻ, kiểm tra check mới phát hiện đúng corruption tương ứng (precision/recall trên 6 loại), rồi cô lập delta metric từng loại.

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi "đã chạy thành công" cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Phạm Văn Tâm
**Ngày xác nhận:** 2026-08-06
