from __future__ import annotations

from typing import Any

from core.utils import write_text


def _format_value(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.3f}"
    if isinstance(value, bool):
        return "có" if value else "không"
    if value is None:
        return "n/a"
    return str(value)


def _kv_table(payload: dict[str, Any]) -> str:
    lines = ["| Trường | Giá trị |", "| --- | --- |"]
    for key, value in payload.items():
        lines.append(f"| `{key}` | {_format_value(value)} |")
    return "\n".join(lines)


# Map check names (keys in quality reports) to Vietnamese labels.
CHECK_LABELS = {
    "row_count": "Số dòng",
    "paper_id": "Mã bài báo (paper_id)",
    "title": "Tiêu đề",
    "summary": "Tóm tắt",
    "duplicate_rows": "Dòng trùng lặp",
    "freshness": "Độ mới (freshness)",
}


def _quality_checks_table(quality: dict[str, Any]) -> str:
    checks = quality.get("checks", {})
    lines = ["| Kiểm tra | Đạt | Chi tiết |", "| --- | --- | --- |"]
    for name, result in checks.items():
        passed = _format_value(result.get("passed"))
        detail = ", ".join(f"{key}={_format_value(value)}" for key, value in result.items() if key != "passed")
        label = CHECK_LABELS.get(name, name)
        lines.append(f"| {label} | {passed} | {detail} |")
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
        "# Báo cáo Baseline (Phase 1)",
        "",
        "## Tóm tắt nguồn dữ liệu",
        "",
        _kv_table(source_summary),
        "",
        "## Chỉ số đánh giá",
        "",
        _kv_table(metric_fields),
        "",
        f"Ragas: `{metrics.get('ragas')}`",
        "",
        "## Chất lượng dữ liệu",
        "",
        f"Tổng quan đạt: **{_format_value(quality.get('passed'))}** "
        f"(`{quality.get('report_name')}`, {quality.get('row_count')} dòng, tạo lúc {quality.get('generated_at')})",
        "",
        _quality_checks_table(quality),
        "",
        "## Độ mới của dữ liệu (Freshness)",
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
        "# Báo cáo tác động Corruption & So sánh phục hồi",
        "",
        "## Chỉ số đánh giá: baseline so với corrupted so với repaired",
        "",
        "| Chỉ số | Baseline | Corrupted | Repaired | Delta corruption | Delta repair |",
        "| --- | --- | --- | --- | --- | --- |",
        *[_metric_row(name, baseline_metrics, corrupted_metrics, repaired_metrics) for name in metric_names],
        "",
        "## Chất lượng dữ liệu: corrupted so với repaired",
        "",
        "| Trạng thái | Đạt | Số dòng |",
        "| --- | --- | --- |",
        f"| corrupted | {_format_value(corrupted_quality.get('passed'))} | {_format_value(corrupted_quality.get('row_count'))} |",
        f"| repaired | {_format_value(repaired_quality.get('passed'))} | {_format_value(repaired_quality.get('row_count'))} |",
        "",
        "## Độ mới (Freshness): corrupted so với repaired",
        "",
        "| Trạng thái | Còn mới | Số dòng cũ | Tổng dòng |",
        "| --- | --- | --- | --- |",
        f"| corrupted | {_format_value(corrupted_freshness.get('is_fresh'))} "
        f"| {_format_value(corrupted_freshness.get('stale_rows'))} | {_format_value(corrupted_freshness.get('total_rows'))} |",
        f"| repaired | {_format_value(repaired_freshness.get('is_fresh'))} "
        f"| {_format_value(repaired_freshness.get('stale_rows'))} | {_format_value(repaired_freshness.get('total_rows'))} |",
        "",
    ]
    write_text(report_path, "\n".join(lines))
