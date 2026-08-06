from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from core.config import Settings
from core.utils import now_utc, write_json

logger = logging.getLogger(__name__)

# A summary shorter than this (after cleaning) is too thin to be useful context.
MIN_SUMMARY_CHARS = 40


def _check_row_count(df: pd.DataFrame) -> dict[str, Any]:
    row_count = len(df)
    return {"row_count": row_count, "passed": row_count > 0}


def _check_paper_id(df: pd.DataFrame) -> dict[str, Any]:
    if "paper_id" not in df.columns:
        return {"null_count": len(df), "duplicate_count": 0, "passed": False}
    null_count = int(df["paper_id"].isna().sum())
    duplicate_count = int(df["paper_id"].duplicated().sum())
    return {
        "null_count": null_count,
        "duplicate_count": duplicate_count,
        "passed": null_count == 0 and duplicate_count == 0,
    }


def _check_title(df: pd.DataFrame) -> dict[str, Any]:
    if "title" not in df.columns:
        return {"missing_count": len(df), "passed": False}
    missing_count = int((~df["title"].fillna("").astype(str).str.strip().astype(bool)).sum())
    return {"missing_count": missing_count, "passed": missing_count == 0}


def _check_summary(df: pd.DataFrame, min_chars: int = MIN_SUMMARY_CHARS) -> dict[str, Any]:
    if "summary" not in df.columns:
        return {"missing_count": len(df), "short_count": 0, "min_chars": min_chars, "passed": False}
    lengths = df["summary"].fillna("").astype(str).str.len()
    missing_count = int((lengths == 0).sum())
    short_count = int(((lengths > 0) & (lengths < min_chars)).sum())
    return {
        "missing_count": missing_count,
        "short_count": short_count,
        "min_chars": min_chars,
        "passed": missing_count == 0,
    }


def _check_duplicate_rows(df: pd.DataFrame) -> dict[str, Any]:
    subset = [column for column in ("paper_id", "title") if column in df.columns] or list(df.columns)
    duplicate_rows = int(df.duplicated(subset=subset).sum())
    return {"subset": subset, "duplicate_rows": duplicate_rows, "passed": duplicate_rows == 0}


def _check_freshness(df: pd.DataFrame, settings: Settings) -> dict[str, Any]:
    if "age_days" not in df.columns:
        return {"stale_count": len(df), "unknown_count": len(df), "passed": False}
    age_days = pd.to_numeric(df["age_days"], errors="coerce")
    unknown_count = int(age_days.isna().sum())
    stale_count = int((age_days > settings.freshness_threshold_days).sum())
    return {
        "threshold_days": settings.freshness_threshold_days,
        "stale_count": stale_count,
        "unknown_count": unknown_count,
        "passed": stale_count == 0,
    }


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    """Run structural + freshness checks on a cleaned dataframe and persist the report.

    ``report_name`` distinguishes baseline/corrupted/repaired runs so their
    reports never overwrite each other under ``data/quality/``.
    """
    checks = {
        "row_count": _check_row_count(df),
        "paper_id": _check_paper_id(df),
        "title": _check_title(df),
        "summary": _check_summary(df),
        "duplicate_rows": _check_duplicate_rows(df),
        "freshness": _check_freshness(df, settings),
    }
    report = {
        "report_name": report_name,
        "generated_at": now_utc().isoformat(),
        "row_count": checks["row_count"]["row_count"],
        "passed": all(check["passed"] for check in checks.values()),
        "checks": checks,
    }
    report_path = settings.paths.quality_dir / f"quality_report_{report_name}.json"
    write_json(report_path, report)
    logger.info(
        "Data quality report '%s': passed=%s (%d rows).",
        report_name,
        report["passed"],
        report["row_count"],
    )
    return report


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path) -> dict[str, Any]:
    """Summarize publication recency for a cleaned dataframe and persist the report."""
    total_rows = len(df)
    published = pd.to_datetime(df.get("published"), errors="coerce").dropna() if "published" in df.columns else pd.Series(dtype="datetime64[ns]")
    age_days = pd.to_numeric(df.get("age_days"), errors="coerce") if "age_days" in df.columns else pd.Series(dtype=float)
    stale_rows = int((age_days > settings.freshness_threshold_days).sum())

    report = {
        "latest_published": published.max().date().isoformat() if not published.empty else None,
        "oldest_published": published.min().date().isoformat() if not published.empty else None,
        "stale_rows": stale_rows,
        "total_rows": total_rows,
        "freshness_threshold_days": settings.freshness_threshold_days,
        "is_fresh": total_rows > 0 and stale_rows == 0,
    }
    write_json(report_path, report)
    logger.info(
        "Freshness report: is_fresh=%s stale_rows=%d/%d.",
        report["is_fresh"],
        stale_rows,
        total_rows,
    )
    return report
