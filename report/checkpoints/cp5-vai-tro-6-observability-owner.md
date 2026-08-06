# CP5 — Vai trò 6: Observability owner (Nhóm 6 người)

> Checkpoint: `02:15–03:15` · Pass: corruption log, corrupted clean/index/answers/metrics/quality và
> report có đủ; baseline không bị ghi đè.
> **Blocker ngoài phạm vi:** giống vai trò 5 — `corruption.py` (vai trò 3) chưa xong nên chưa có
> corrupted dataframe để chạy quality/freshness thật. Ghi chú này là thiết kế sẵn, chạy ngay được
> khi có dữ liệu.

## 1. Quality/freshness cho corrupted dataset — path riêng, không đụng baseline

`run_data_quality_checks()` đã tự namespace theo `report_name` (không cần sửa):

```python
corrupted_quality = run_data_quality_checks(corrupted_df, settings, report_name="corrupted")
# -> data/quality/quality_report_corrupted.json (khác hẳn quality_report_baseline.json)
```

**Lưu ý quan trọng phát hiện khi đọc lại `core/config.py::Paths`:** chỉ có DUY NHẤT một field
`freshness_report` (không có `corrupted_freshness_report`/`repaired_freshness_report` được định
nghĩa sẵn). Nếu gọi `build_freshness_report(corrupted_df, settings, settings.paths.freshness_report)`
sẽ **ghi đè** freshness report của baseline — vi phạm nguyên tắc "không ghi đè baseline". Cần người
gọi hàm (vai trò lead trong `corruption_flow.py`) tự tạo path riêng, ví dụ:

```python
build_freshness_report(
    corrupted_df, settings,
    settings.paths.quality_dir / "freshness_report_corrupted.json",
)
```

Đã ghi rõ điểm này để nhắc vai trò lead khi implement `corruption_flow.py`, tránh lỗi ghi đè âm thầm.

## 2. Nối corruption log với quality signal và metric change

Khi có `data/results/corruption_log.json` (mỗi entry gồm record ID, loại corruption, tham số,
before/after count — theo pseudo-code `corruption.py`), đối chiếu:

| Loại corruption (dự kiến) | Quality check kỳ vọng bị fail | Metric agent kỳ vọng giảm |
| --- | --- | --- |
| Drop latest records | `row_count` giảm (không hẳn "fail", nhưng số liệu đổi) | `retrieval_hit_rate` giảm nếu record bị xoá nằm trong `ground_truth_doc_ids` |
| Blank summary | `summary.missing_count > 0` → fail | `summary`-type questions: `token_f1`/`judge` giảm vì `text_for_embedding` mất nội dung |
| Noise vào summary | `summary` vẫn "pass" theo check hiện tại (không đo nhiễu ký tự) — **giới hạn cần nêu rõ** | `retrieval_hit_rate` có thể giảm do embedding lệch |
| Truncate title | `title` vẫn không rỗng nên `title.missing_count` không bắt được — **giới hạn cần nêu rõ** | Exact-title lookup trong `qa.py` (regex `'...'`) có thể fail vì title không khớp nữa |
| Stale publication date | `freshness.stale_count > 0` → fail, `is_fresh=false` | `date`-type questions: `ground_truth` (published cũ) có thể vẫn đúng theo dữ liệu corrupted, nhưng freshness signal vẫn phải giảm |
| Duplicate rows | `duplicate_rows.duplicate_rows > 0` → fail | Không nhất thiết ảnh hưởng metric agent (chỉ ảnh hưởng data quality) |

Đây là **giả thuyết dự kiến dựa trên 6 check hiện có**, không phải kết luận — mục 3 dưới đây yêu cầu
đúng là phải kiểm chứng bằng số liệu thật, không suy đoán quá mức.

## 2b. Giới hạn hiện tại của `run_data_quality_checks` cần bổ sung nếu muốn bắt đủ mọi corruption

Check `summary` hiện chỉ đo *rỗng* hoặc *ngắn hơn ngưỡng*, không đo "nhiễu" (noise chèn thêm ký tự
lạ) hay title bị truncate. Nếu muốn 2 loại corruption này hiện rõ trên quality report (thay vì chỉ
hiện qua metric agent), cần vai trò 3 thêm: so sánh `summary`/`title` với bản gốc (cần lưu snapshot
baseline để so), hoặc thêm check "ký tự bất thường" (tỷ lệ ký tự không phải chữ/số/khoảng trắng cao
bất thường). Đây là đề xuất cải tiến, chưa implement — ghi vào `group_report.md` mục "Giới hạn và
hướng cải thiện" nếu nhóm không có thời gian làm.

## 3. Signal nào KHÔNG đổi — tránh kết luận quá mức

Nguyên tắc: chỉ báo "corruption có tác động X" khi số liệu thật cho thấy thay đổi. Ví dụ dự kiến:
corruption loại "duplicate rows" khó có khả năng làm thay đổi `paper_id` null-check hay
`retrieval_hit_rate` với các câu hỏi không liên quan tới record bị duplicate — cần nêu rõ những
signal này giữ nguyên trong báo cáo, không gộp chung "mọi thứ đều tệ đi".

## 4. Blocker

Giống vai trò 5: chờ `src/ingestion/corruption.py` (vai trò 3) và `src/pipelines/corruption_flow.py`
(vai trò lead). Khi có, mục 1–3 chạy ngay bằng các hàm đã implement + test ở CP1–CP3, chỉ thêm việc
gọi đúng path/report_name cho trạng thái `corrupted`.
