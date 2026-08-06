# Corruption Impact & Repair Comparison Report

## Evaluation metrics: baseline vs corrupted vs repaired

| Metric | Baseline | Corrupted | Repaired | Delta corruption | Delta repair |
| --- | --- | --- | --- | --- | --- |
| `retrieval_hit_rate` | 1.000 | 0.800 | 1.000 | -0.200 | 0.200 |
| `mean_token_f1` | 1.000 | 0.800 | 1.000 | -0.200 | 0.200 |
| `judge_accuracy` | 1.000 | 0.800 | 1.000 | -0.200 | 0.200 |
| `mean_judge_score` | 5 | 4.200 | 5 | -0.800 | 0.800 |

## Data quality: corrupted vs repaired

| State | Passed | Row count |
| --- | --- | --- |
| corrupted | no | 21 |
| repaired | yes | 24 |

## Freshness: corrupted vs repaired

| State | Is fresh | Stale rows | Total rows |
| --- | --- | --- | --- |
| corrupted | no | 2 | 21 |
| repaired | yes | 0 | 24 |
