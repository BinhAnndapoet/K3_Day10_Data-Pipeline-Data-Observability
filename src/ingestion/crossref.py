from __future__ import annotations

import dataclasses
import logging
import os
import random
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests

from core.config import Settings
from core.utils import normalize_whitespace, read_json, write_json

logger = logging.getLogger(__name__)

# Crossref REST endpoint for the /works collection.
CROSSREF_API_URL = "https://api.crossref.org/works"

# Transient HTTP statuses that should trigger a retry with backoff.
# 429 = rate limited, 5xx = upstream temporarily unavailable.
RETRYABLE_STATUS_CODES = frozenset({429, 500, 502, 503, 504})

# How many times to retry a transient failure before giving up.
DEFAULT_MAX_RETRIES = 4
# Base seconds for exponential backoff (delay = base * 2**attempt + jitter).
DEFAULT_BACKOFF_FACTOR = 1.5
REQUEST_TIMEOUT = 30.0


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


def record_to_dict(record: PaperRecord) -> dict[str, Any]:
    """Serialize a PaperRecord into a plain dict for JSON storage."""
    return dataclasses.asdict(record)


def record_from_dict(payload: dict[str, Any]) -> PaperRecord:
    """Reconstruct a PaperRecord from a serialized dict.

    Unknown/missing keys are ignored so older snapshots stay loadable.
    """
    fields = {field.name for field in dataclasses.fields(PaperRecord)}
    return PaperRecord(**{key: value for key, value in payload.items() if key in fields})


def _first(value: Any) -> str:
    """Return the first element of a Crossref list field, or empty string."""
    if isinstance(value, list) and value:
        first = value[0]
        return first if isinstance(first, str) else str(first or "")
    if isinstance(value, str):
        return value
    return ""


def _format_author(author: dict[str, Any]) -> str:
    """Render one Crossref author entry as 'Given Family' (or org name)."""
    given = (author.get("given") or "").strip()
    family = (author.get("family") or "").strip()
    if given and family:
        return f"{given} {family}"
    name = (author.get("name") or "").strip()
    return family or given or name


def _iso_from_date_parts(date_obj: dict[str, Any]) -> str:
    """Convert a Crossref date object to a zero-padded ``YYYY-MM-DD`` string.

    Crossref stores dates as ``{"date-parts": [[Y, M, D], ...]}`` where the
    month and day are optional. Missing components default to 01 so we always
    emit a valid ISO date that downstream freshness logic can parse.
    """
    parts = date_obj.get("date-parts") or []
    if not parts or not parts[0]:
        return ""
    components = parts[0]
    year = int(components[0]) if len(components) > 0 and components[0] else 0
    if year == 0:
        return ""
    month = int(components[1]) if len(components) > 1 and components[1] else 1
    day = int(components[2]) if len(components) > 2 and components[2] else 1
    try:
        return f"{year:04d}-{month:02d}-{day:02d}"
    except (TypeError, ValueError):
        return ""


def _resolve_date(item: dict[str, Any], keys: tuple[str, ...]) -> str:
    """Return the first parseable ISO date among the candidate date fields."""
    for key in keys:
        candidate = item.get(key)
        if isinstance(candidate, dict):
            iso = _iso_from_date_parts(candidate)
            if iso:
                return iso
    return ""


def _extract_pdf_url(item: dict[str, Any]) -> str:
    """Best-effort extraction of a full-text PDF link from a Crossref item."""
    links = item.get("link")
    if isinstance(links, list):
        for link in links:
            url = (link.get("URL") or link.get("url") or "").strip() if isinstance(link, dict) else ""
            content_type = (link.get("content-type") or "").lower() if isinstance(link, dict) else ""
            if url and "pdf" in content_type:
                return url
        for link in links:
            url = (link.get("URL") or link.get("url") or "").strip() if isinstance(link, dict) else ""
            if url:
                return url
    resource = item.get("resource")
    if isinstance(resource, dict):
        url = (resource.get("primary", {}).get("URL") or resource.get("URL") or "").strip()
        if url:
            return url
    return ""


def _has_abstract(item: dict[str, Any]) -> bool:
    abstract = item.get("abstract")
    if abstract and normalize_whitespace(re.sub(r"<[^>]+>", " ", abstract)):
        return True
    description = item.get("description")
    if isinstance(description, list) and any(
        isinstance(d, dict) and d.get("value") for d in description
    ):
        return True
    return False


def parse_crossref_payload(payload: dict[str, Any]) -> list[PaperRecord]:
    """Parse a Crossref ``/works`` payload into a flat list of PaperRecord.

    Only records that have both a non-empty title and an abstract/description
    are kept (ingestion-level filter). Tag stripping is intentionally left to
    the cleaning stage so the raw record mirrors the source faithfully.
    """
    items = ((payload or {}).get("message") or {}).get("items") or []
    records: list[PaperRecord] = []

    for item in items:
        paper_id = (item.get("DOI") or "").strip()
        title = normalize_whitespace(_first(item.get("title")))
        summary = (item.get("abstract") or "").strip()
        if not summary:
            description = item.get("description")
            if isinstance(description, list):
                summary = " ".join(
                    (d.get("value") or "") for d in description if isinstance(d, dict)
                ).strip()

        # Ingestion filter: keep only complete records (title + abstract).
        if not paper_id or not title or not _has_abstract(item):
            continue

        authors = [_format_author(a) for a in (item.get("author") or []) if isinstance(a, dict)]
        authors = [author for author in authors if author]

        categories = [str(subject).strip() for subject in (item.get("subject") or []) if subject]
        primary_category = categories[0] if categories else ""

        published = _resolve_date(
            item,
            ("published", "published-online", "published-print", "issued", "posted"),
        )
        updated = _resolve_date(item, ("deposited", "indexed", "created"))

        abs_url = (item.get("URL") or "").strip()
        pdf_url = _extract_pdf_url(item)

        container = item.get("container-title")
        comment = _first(container) or (item.get("publisher") or "")

        records.append(
            PaperRecord(
                paper_id=paper_id,
                title=title,
                summary=summary,
                authors=authors,
                categories=categories,
                primary_category=primary_category,
                published=published,
                updated=updated,
                abs_url=abs_url,
                pdf_url=pdf_url,
                comment=comment,
            )
        )

    logger.info("Parsed %d valid records from %d Crossref items.", len(records), len(items))
    return records


def _get_with_retry(
    session: requests.Session,
    url: str,
    params: dict[str, Any],
    *,
    max_retries: int = DEFAULT_MAX_RETRIES,
    backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
) -> requests.Response:
    """GET with retry + exponential backoff for transient failures.

    Honours the ``Retry-After`` header (Crossref sends it on 429), adds jitter
    to avoid stampeding the API, and re-raises the last error once retries are
    exhausted. Non-retryable HTTP errors are raised immediately.
    """
    last_response: requests.Response | None = None
    last_exc: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            response = session.get(url, params=params, timeout=REQUEST_TIMEOUT)
        except requests.RequestException as exc:
            last_exc = exc
            last_response = None
            response = None
        else:
            last_exc = None
            if response.status_code == 200:
                return response
            last_response = response
            if response.status_code not in RETRYABLE_STATUS_CODES:
                response.raise_for_status()

        if attempt == max_retries:
            break

        # Compute the backoff delay (respect Retry-After when provided).
        retry_after_header = None
        if last_response is not None:
            retry_after_header = last_response.headers.get("Retry-After")
        if retry_after_header:
            try:
                delay = float(retry_after_header)
            except (TypeError, ValueError):
                delay = backoff_factor * (2 ** attempt)
        else:
            delay = backoff_factor * (2 ** attempt)
        delay += random.uniform(0.0, 0.5)  # full jitter to spread load

        logger.warning(
            "Crossref request failed (attempt %d/%d); retrying in %.2fs. status=%s exc=%s",
            attempt + 1,
            max_retries + 1,
            delay,
            last_response.status_code if last_response is not None else "n/a",
            last_exc,
        )
        time.sleep(delay)

    if last_exc is not None:
        raise last_exc
    if last_response is not None:
        last_response.raise_for_status()
    raise RuntimeError("Crossref request failed after exhausting retries.")


def _build_headers() -> dict[str, str]:
    """Polite-pool headers; mailto is read from env when provided."""
    mailto = os.getenv("CROSSREF_MAILTO", "").strip()
    user_agent = "Day10DataObservabilityLab/0.1"
    if mailto:
        user_agent += f" (mailto:{mailto})"
    return {"User-Agent": user_agent}


def _build_params(settings: Settings) -> dict[str, Any]:
    """Translate settings into Crossref query parameters."""
    params: dict[str, Any] = {
        "query": settings.source_query,
        "rows": settings.max_results,
    }
    if settings.source_filter:
        params["filter"] = settings.source_filter
    return params


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    """Call Crossref, persist the raw HTTP response, and return parsed records.

    Two raw artifacts are written for auditability:
      * ``crossref_response.json`` - the verbatim HTTP response body.
      * ``crossref_records.json`` - the flat, parsed PaperRecord snapshot.
    """
    params = _build_params(settings)
    headers = _build_headers()

    session = requests.Session()
    session.headers.update(headers)
    logger.info(
        "Fetching Crossref works: query=%r filter=%r rows=%s",
        settings.source_query,
        settings.source_filter,
        settings.max_results,
    )
    response = _get_with_retry(session, CROSSREF_API_URL, params)
    payload = response.json()

    write_json(settings.paths.raw_api_response, payload)

    records = parse_crossref_payload(payload)
    write_json(settings.paths.raw_records_json, [record_to_dict(record) for record in records])
    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    """Read a serialized record snapshot and map it back to PaperRecord."""
    payload = read_json(path)
    if isinstance(payload, dict):
        # Tolerate an accidental wrapper around the records list.
        payload = payload.get("records") or payload.get("items") or []
    return [record_from_dict(item) for item in payload if isinstance(item, dict)]
