# CP6 — Vai trò 6: Observability owner (Nhóm 6 người)

> Checkpoint: `03:15–04:00` · Pass: repaired artifacts và comparison report có
> baseline–corrupted–repaired/delta; repo không có secret; demo dùng artifact thật.
> **Blocker ngoài phạm vi:** cần `corrupted_metrics`/`repaired_metrics`/quality/freshness thật từ
> CP5 (phụ thuộc vai trò 3 + lead). `generate_corruption_report()` đã implement xong ở CP2 — chỉ còn
> chờ input thật để gọi.

## 1. Generate comparison report — đã sẵn hàm, chỉ chờ input

```python
generate_corruption_report(
    settings.paths.comparison_report,
    baseline_metrics=baseline_summary,        # đã có thật từ CP3
    corrupted_metrics=corrupted_summary,      # CP5
    repaired_metrics=repaired_summary,        # CP6 mục eval
    corrupted_quality=corrupted_quality,      # CP5
    repaired_quality=repaired_quality,        # CP6, chạy run_data_quality_checks(repaired_df, settings, "repaired")
    corrupted_freshness=corrupted_freshness,  # CP5, path riêng (xem lưu ý CP5)
    repaired_freshness=repaired_freshness,    # CP6, path riêng khác nữa — không trùng corrupted/baseline
)
```

Hàm tự render 3 bảng markdown: metric baseline/corrupted/repaired kèm delta corruption và delta
repair; quality corrupted vs repaired; freshness corrupted vs repaired. Không cần sửa
`reporting.py` thêm — đã viết tổng quát theo đúng chữ ký hàm trong pseudo-code gốc.

## 2. Nêu rõ nếu recovery chưa hoàn toàn

Theo "Nguyên tắc báo cáo trung thực" (`report/README.md` mục 9): nếu bất kỳ metric/signal nào sau
repair chưa quay lại đúng giá trị baseline, phải ghi rõ "chưa phục hồi hoàn toàn" kèm số liệu thật —
không làm tròn hay diễn giải tích cực hơn thực tế. Áp dụng cụ thể: so từng dòng trong bảng delta của
`generate_corruption_report`, nếu `delta_repair` không đưa metric về đúng baseline (delta_repair +
corrupted != baseline), gắn cờ "partial recovery" trong phần diễn giải của `group_report.md`.

## 3. Giới hạn cần nêu khi demo

- `judge_accuracy`/`mean_judge_score` ở cả 3 trạng thái đều dùng **cùng cơ chế fallback heuristic**
  (chưa có `LLM_API_KEY` — xem ghi chú CP3 vai trò 5) nếu đến CP6 `.env` vẫn chưa được điền. Nếu vậy,
  phải nói rõ trong demo: 2 metric này hiện đang đo lại đúng thông tin của `token_f1` dưới tên khác,
  không phải LLM-as-judge độc lập — tránh trình bày như một tín hiệu thứ hai độc lập với
  `mean_token_f1`.
- Quality checks hiện tại không bắt được 2 loại corruption "noise vào summary" và "truncate title"
  (đã ghi ở CP5 mục 2b) — nếu demo cho thấy metric agent giảm nhưng quality report vẫn "pass", đây
  là giới hạn thật của bộ check, không phải lỗi đo — cần nói rõ thay vì im lặng bỏ qua.

## 4. Blocker

| Cần | Trạng thái |
| --- | --- |
| `corrupted_metrics.json`, `corrupted quality/freshness` | CP5, chưa có (chờ vai trò 3) |
| `repaired_metrics.json`, `repaired quality/freshness` | CP6, chưa có (chờ vai trò 3 + lead) |
| `data/reports/corruption_report.md` | Chưa tồn tại — hàm sẵn sàng, chỉ thiếu input |

Khi đủ 7 input, chỉ cần 1 lệnh gọi `generate_corruption_report(...)` là ra file — không có việc code
nào còn lại phía vai trò 6 ngoài việc này.
