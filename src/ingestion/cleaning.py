from __future__ import annotations

import html
import logging
import re
from datetime import datetime

import pandas as pd

from core.utils import normalize_whitespace
from ingestion.crossref import PaperRecord

logger = logging.getLogger(__name__)

# Records with a summary shorter than this are treated as junk and dropped.
MIN_SUMMARY_CHARS = 100

# Matches XML/HTML tags such as <jats:p>, <jats:title>, <b>, </italic>, ...
_TAG_RE = re.compile(r"<[^>]+>")


def _strip_tags(value: str) -> str:
    """Remove XML/HTML markup, decode entities, and collapse whitespace."""
    if not value:
        return ""
    without_tags = _TAG_RE.sub(" ", value)
    unescaped = html.unescape(without_tags)
    return normalize_whitespace(unescaped)


def _parse_date(value: str) -> datetime | None:
    """Parse a ``YYYY-MM-DD`` string into a naive datetime, or None."""
    if not value:
        return None
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d")
    except (TypeError, ValueError):
        return None


def _row_from_record(record: PaperRecord, run_date: datetime) -> dict:
    """Flatten + normalize one PaperRecord into a clean dataframe row."""
    title = _strip_tags(record.title)
    summary = _strip_tags(record.summary)

    authors = [author for author in record.authors if author]
    categories = [category for category in record.categories if category]
    authors_joined = ", ".join(authors)
    categories_joined = ", ".join(categories)

    published = record.published or ""
    published_dt = _parse_date(published)
    reference_dt = run_date.replace(tzinfo=None) if run_date.tzinfo is not None else run_date
    if published_dt is not None:
        age_days = int((reference_dt - published_dt).days)
    else:
        age_days = None  # freshness check will flag this as unknown.

    text_for_embedding = (
        f"Title: {title} | Authors: {authors_joined} | Summary: {summary}"
    )

    return {
        "paper_id": record.paper_id,
        "title": title,
        "summary": summary,
        "authors": authors,
        "categories": categories,
        "primary_category": record.primary_category,
        "authors_joined": authors_joined,
        "categories_joined": categories_joined,
        "published": published,
        "updated": record.updated or "",
        "age_days": age_days,
        "summary_chars": len(summary),
        "abs_url": record.abs_url,
        "pdf_url": record.pdf_url,
        "comment": record.comment or "",
        "text_for_embedding": text_for_embedding,
    }


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    """Clean raw records into a dataframe ready for embedding.

    Steps:
      1. Strip XML/HTML tags from title/summary and join authors/categories.
      2. Parse the publication date and compute ``age_days`` (freshness).
      3. Build the ``text_for_embedding`` semantic column.
      4. Drop junk rows (no title, or summary under MIN_SUMMARY_CHARS) and
         duplicates.
      5. Sort newest-first so freshness reports reflect reality.
    """
    rows = [_row_from_record(record, run_date) for record in records]
    df = pd.DataFrame(rows)

    if df.empty:
        logger.warning("No records supplied to cleaning stage.")
        return df

    initial_count = len(df)

    # Drop junk rows: missing title or summary, or summary too short.
    df = df[df["title"].astype(bool)]
    df = df[df["summary"].astype(bool)]
    df = df[df["summary_chars"] >= MIN_SUMMARY_CHARS]

    # Drop duplicates (same paper_id, or same title after normalization).
    df = df.drop_duplicates(subset=["paper_id"])
    df = df.drop_duplicates(subset=["title"])

    # Sort newest-first; rows with unknown age go to the end.
    df = df.sort_values(by="age_days", ascending=True, na_position="last").reset_index(drop=True)

    logger.info(
        "Cleaning complete: %d -> %d rows (dropped %d).",
        initial_count,
        len(df),
        initial_count - len(df),
    )
    return df
