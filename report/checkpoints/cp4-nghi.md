# CP4 — Nghỉ 15 phút (02:00–02:15)

Không có việc code. Theo HTML checkpoint plan:

- Vai trò 5 (eval): nghỉ, sau đó dùng lại `data/eval/test_set.json` đã khóa (không tạo lại) cho
  vòng evaluate corrupted/repaired ở CP5–CP6.
- Vai trò 6 (observe): nghỉ, sau đó dự báo tín hiệu quality/freshness baseline
  (`passed=true`, `is_fresh=true`, 0 stale) sẽ đổi thế nào khi corruption chạy — dùng làm giả thuyết
  đối chiếu với số liệu thật ở CP5.

Baseline checklist trước khi nghỉ (đã đủ, xem CP3): `baseline_metrics.json`, `baseline_answers.json`,
`quality_report_baseline.json`, `freshness_report.json`, `phase1_report.md`.
