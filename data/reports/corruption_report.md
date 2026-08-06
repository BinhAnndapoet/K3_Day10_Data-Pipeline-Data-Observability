# Báo cáo tác động Corruption & So sánh phục hồi

## Chỉ số đánh giá: baseline so với corrupted so với repaired

| Chỉ số | Baseline | Corrupted | Repaired | Delta corruption | Delta repair |
| --- | --- | --- | --- | --- | --- |
| `retrieval_hit_rate` | 1.000 | 0.800 | 1.000 | -0.200 | 0.200 |
| `mean_token_f1` | 1.000 | 0.800 | 1.000 | -0.200 | 0.200 |
| `judge_accuracy` | 1.000 | 0.800 | 1.000 | -0.200 | 0.200 |
| `mean_judge_score` | 5 | 4.200 | 5 | -0.800 | 0.800 |

## Chất lượng dữ liệu: corrupted so với repaired

| Trạng thái | Đạt | Số dòng |
| --- | --- | --- |
| corrupted | không | 21 |
| repaired | có | 24 |

## Độ mới (Freshness): corrupted so với repaired

| Trạng thái | Còn mới | Số dòng cũ | Tổng dòng |
| --- | --- | --- | --- |
| corrupted | không | 2 | 21 |
| repaired | có | 0 | 24 |
