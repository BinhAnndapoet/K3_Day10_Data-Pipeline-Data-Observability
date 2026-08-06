from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pandas as pd

from core.config import Settings
from core.utils import write_json

logger = logging.getLogger(__name__)


def _sync_summary_chars(df: pd.DataFrame) -> pd.DataFrame:
    """Recompute ``summary_chars`` after summary mutations."""
    mutated = df.copy()
    if "summary" in mutated.columns:
        mutated["summary_chars"] = mutated["summary"].fillna("").astype(str).str.len()
    return mutated


def _recompute_age_days(df: pd.DataFrame) -> pd.DataFrame:
    """Recompute ``age_days`` from ``published`` using today as the reference."""
    mutated = df.copy()
    if "published" not in mutated.columns:
        return mutated
    parsed = pd.to_datetime(mutated["published"], errors="coerce")
    reference = pd.Timestamp.today().normalize()
    mutated["age_days"] = (reference - parsed).dt.days
    return mutated


def _apply_window(df: pd.DataFrame, window: pd.DataFrame, operation: str) -> pd.DataFrame:
    """Apply a row-level mutation to the rows whose paper_id is in ``window``."""
    mutated = df.copy()
    ids = set(window["paper_id"])
    mask = mutated["paper_id"].isin(ids)
    if operation == "blank_summary":
        mutated.loc[mask, "summary"] = ""
    elif operation == "inject_noise":
        summary = mutated.loc[mask, "summary"].fillna("").astype(str)
        mutated.loc[mask, "summary"] = summary.map(
            lambda value: f"zzzz {value}" if value else value
        )
    elif operation == "truncate_title":
        titles = mutated.loc[mask, "title"].fillna("").astype(str)
        mutated.loc[mask, "title"] = titles.map(
            lambda value: value[:20] if len(value) > 20 else value
        )
    elif operation == "old_date":
        mutated.loc[mask, "published"] = "2010-01-01"
    return mutated


def corrupt_clean_dataframe(df: pd.DataFrame, settings: Settings, output_log_path: Path) -> pd.DataFrame:
    """Simulate deliberate data corruption on the baseline clean dataset.

    Every corruption is logged (type, parameter, affected paper ids) so the
    observability role can tie quality/freshness signal changes back to the
    exact records that were damaged. Each corruption consumes a distinct
    window of the shuffled row order so the damage types never overlap.
    """
    log_entries: list[dict[str, Any]] = []

    # Work on a copy so the baseline dataframe stays untouched.
    mutated = df.copy()
    # Shuffle so "latest" corruption does not always hit the same rows.
    mutated = mutated.sample(frac=1.0, random_state=42).reset_index(drop=True)

    total = len(mutated)
    if total == 0:
        raise ValueError("Cannot corrupt an empty dataframe.")

    offset = 0

    def take(count: int) -> pd.DataFrame:
        """Consume the next ``count`` rows (by position) as a window.

        Raises when the dataset is too small to cover all corruption steps so
        an empty window never gets logged silently.
        """
        nonlocal offset
        window = mutated.iloc[offset : offset + count]
        if len(window) < count:
            raise ValueError(
                f"Corruption window underflow: needed {count} rows at offset "
                f"{offset} but only {len(window)} remain. Dataset too small."
            )
        offset += count
        return window

    # 1. Drop a slice of records (drop_latest). Kept in the log for repair.
    drop_count = max(1, round(0.15 * total))
    dropped_window = take(drop_count)
    dropped_ids = [str(paper_id) for paper_id in dropped_window["paper_id"]]
    log_entries.append(
        {
            "type": "drop_latest",
            "parameter": {"count": drop_count},
            "paper_ids": dropped_ids,
            "before_count": total,
            "after_count": total - drop_count,
        }
    )
    mutated = mutated[~mutated["paper_id"].isin(dropped_ids)].reset_index(drop=True)
    total = len(mutated)

    # 2. Blank summaries.
    window = take(1)
    mutated = _apply_window(mutated, window, "blank_summary")
    mutated = _sync_summary_chars(mutated)
    log_entries.append(
        {"type": "blank_summary", "parameter": {"count": 1}, "paper_ids": [str(paper_id) for paper_id in window["paper_id"]]}
    )

    # 3. Inject noise into summaries.
    window = take(2)
    mutated = _apply_window(mutated, window, "inject_noise")
    mutated = _sync_summary_chars(mutated)
    log_entries.append(
        {"type": "inject_noise", "parameter": {"count": 2}, "paper_ids": [str(paper_id) for paper_id in window["paper_id"]]}
    )

    # 4. Truncate titles.
    window = take(2)
    mutated = _apply_window(mutated, window, "truncate_title")
    log_entries.append(
        {"type": "truncate_title", "parameter": {"count": 2}, "paper_ids": [str(paper_id) for paper_id in window["paper_id"]]}
    )

    # 5. Age published dates. age_days is recomputed so freshness checks
    #    reflect the stale date instead of the original publication date.
    window = take(2)
    mutated = _apply_window(mutated, window, "old_date")
    log_entries.append(
        {
            "type": "old_date",
            "parameter": {"count": 2, "target_date": "2010-01-01"},
            "paper_ids": [str(paper_id) for paper_id in window["paper_id"]],
        }
    )
    mutated = _recompute_age_days(mutated)

    # 6. Add duplicate rows (reinsert a slice under a _dup suffix).
    duplicate_window = take(1)
    duplicate_ids = [str(paper_id) for paper_id in duplicate_window["paper_id"]]
    rows_to_duplicate = mutated[mutated["paper_id"].isin(duplicate_ids)]
    duplicates = rows_to_duplicate.copy()
    duplicates["paper_id"] = duplicates["paper_id"] + "_dup"
    mutated = pd.concat([mutated, duplicates], ignore_index=True)
    log_entries.append(
        {
            "type": "duplicate_rows",
            "parameter": {"count": len(duplicates)},
            "paper_ids": duplicate_ids,
        }
    )

    # 7. Rebuild text_for_embedding so the corrupted semantics flow downstream.
    mutated["text_for_embedding"] = mutated.apply(
        lambda row: (
            f"Title: {row['title']} | Authors: {row['authors_joined']} "
            f"| Summary: {row['summary']}"
        ),
        axis=1,
    )

    write_json(output_log_path, {"corruptions": log_entries})
    logger.info(
        "Corruption applied: %d -> %d rows; log written to %s.",
        len(df),
        len(mutated),
        output_log_path,
    )
    return mutated
