from __future__ import annotations

from typing import Any

from core.utils import write_text


def _format_value(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.3f}"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if value is None:
        return "n/a"
    return str(value)


def _kv_table(payload: dict[str, Any]) -> str:
    lines = ["| Field | Value |", "| --- | --- |"]
    for key, value in payload.items():
        lines.append(f"| `{key}` | {_format_value(value)} |")
    return "\n".join(lines)


def _quality_checks_table(quality: dict[str, Any]) -> str:
    checks = quality.get("checks", {})
    lines = ["| Check | Passed | Detail |", "| --- | --- | --- |"]
    for name, result in checks.items():
        passed = _format_value(result.get("passed"))
        detail = ", ".join(f"{key}={_format_value(value)}" for key, value in result.items() if key != "passed")
        lines.append(f"| `{name}` | {passed} | {detail} |")
    return "\n".join(lines)


def generate_phase1_report(
    report_path,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> None:
    """Render the baseline (phase 1) markdown report from real evaluation/quality artifacts."""
    metric_fields = {key: value for key, value in metrics.items() if key != "ragas"}
    lines = [
        "# Phase 1 Baseline Report",
        "",
        "## Source summary",
        "",
        _kv_table(source_summary),
        "",
        "## Evaluation metrics",
        "",
        _kv_table(metric_fields),
        "",
        f"Ragas: `{metrics.get('ragas')}`",
        "",
        "## Data quality",
        "",
        f"Overall passed: **{_format_value(quality.get('passed'))}** "
        f"(`{quality.get('report_name')}`, {quality.get('row_count')} rows, generated {quality.get('generated_at')})",
        "",
        _quality_checks_table(quality),
        "",
        "## Freshness",
        "",
        _kv_table(freshness),
        "",
    ]
    write_text(report_path, "\n".join(lines))


def _metric_row(name: str, baseline: dict[str, Any], corrupted: dict[str, Any], repaired: dict[str, Any]) -> str:
    base_value = baseline.get(name)
    corrupted_value = corrupted.get(name)
    repaired_value = repaired.get(name)
    delta_corruption = (
        corrupted_value - base_value
        if isinstance(base_value, (int, float)) and isinstance(corrupted_value, (int, float))
        else None
    )
    delta_repair = (
        repaired_value - corrupted_value
        if isinstance(corrupted_value, (int, float)) and isinstance(repaired_value, (int, float))
        else None
    )
    return (
        f"| `{name}` | {_format_value(base_value)} | {_format_value(corrupted_value)} | {_format_value(repaired_value)} "
        f"| {_format_value(delta_corruption)} | {_format_value(delta_repair)} |"
    )


def generate_corruption_report(
    report_path,
    baseline_metrics: dict[str, Any],
    corrupted_metrics: dict[str, Any],
    repaired_metrics: dict[str, Any],
    corrupted_quality: dict[str, Any],
    repaired_quality: dict[str, Any],
    corrupted_freshness: dict[str, Any],
    repaired_freshness: dict[str, Any],
) -> None:
    """Render the baseline vs corrupted vs repaired comparison markdown report."""
    metric_names = ("retrieval_hit_rate", "mean_token_f1", "judge_accuracy", "mean_judge_score")
    lines = [
        "# Corruption Impact & Repair Comparison Report",
        "",
        "## Evaluation metrics: baseline vs corrupted vs repaired",
        "",
        "| Metric | Baseline | Corrupted | Repaired | Delta corruption | Delta repair |",
        "| --- | --- | --- | --- | --- | --- |",
        *[_metric_row(name, baseline_metrics, corrupted_metrics, repaired_metrics) for name in metric_names],
        "",
        "## Data quality: corrupted vs repaired",
        "",
        "| State | Passed | Row count |",
        "| --- | --- | --- |",
        f"| corrupted | {_format_value(corrupted_quality.get('passed'))} | {_format_value(corrupted_quality.get('row_count'))} |",
        f"| repaired | {_format_value(repaired_quality.get('passed'))} | {_format_value(repaired_quality.get('row_count'))} |",
        "",
        "## Freshness: corrupted vs repaired",
        "",
        "| State | Is fresh | Stale rows | Total rows |",
        "| --- | --- | --- | --- |",
        f"| corrupted | {_format_value(corrupted_freshness.get('is_fresh'))} "
        f"| {_format_value(corrupted_freshness.get('stale_rows'))} | {_format_value(corrupted_freshness.get('total_rows'))} |",
        f"| repaired | {_format_value(repaired_freshness.get('is_fresh'))} "
        f"| {_format_value(repaired_freshness.get('stale_rows'))} | {_format_value(repaired_freshness.get('total_rows'))} |",
        "",
    ]
    write_text(report_path, "\n".join(lines))
