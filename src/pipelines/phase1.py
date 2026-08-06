from __future__ import annotations

import logging
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

from core.config import Settings, load_settings, require_llm_credentials
from core.utils import now_utc, read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import fetch_source_records, load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_phase1_report
from retrieval.agent import build_agent, run_agent_question
from retrieval.index import LocalEmbeddingIndex

logger = logging.getLogger(__name__)


def _load_or_fetch_records(settings: Settings) -> tuple[list, dict]:
    """Return (records, source_summary), fetching from Crossref only when required."""
    raw_records_path = settings.paths.raw_records_json
    if not settings.refresh_source and raw_records_path.exists():
        records = load_raw_records(raw_records_path)
        source_summary = {
            "mode": "loaded_from_snapshot",
            "source": settings.source_api,
            "raw_records": raw_records_path.name,
            "record_count": len(records),
            "fetched_at": "n/a (snapshot)",
        }
        logger.info("Loaded %d raw records from existing snapshot.", len(records))
        return records, source_summary

    records = fetch_source_records(settings)
    source_summary = {
        "mode": "fetched_live",
        "source": settings.source_api,
        "query": settings.source_query,
        "filter": settings.source_filter,
        "record_count": len(records),
        "fetched_at": now_utc().isoformat(),
    }
    return records, source_summary


def main() -> None:
    """Baseline end-to-end: raw -> clean -> index -> test set -> evaluate -> quality -> report."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    settings = load_settings()
    require_llm_credentials(settings)

    records, source_summary = _load_or_fetch_records(settings)
    if not records:
        raise RuntimeError("No raw records available; cannot build a baseline.")

    clean_df = build_clean_dataframe(records, run_date=datetime.now())
    write_csv(clean_df, settings.paths.clean_csv)
    write_json(settings.paths.clean_json, clean_df.to_dict(orient="records"))
    logger.info("Saved clean dataset: %d rows.", len(clean_df))

    index = LocalEmbeddingIndex.build(clean_df, settings, settings.paths.embeddings_json)

    test_set_path = settings.paths.eval_testset
    if not settings.refresh_test_set and test_set_path.exists():
        test_set = read_json(test_set_path)
        logger.info("Reusing existing test set: %d questions.", len(test_set))
    else:
        build_test_set(clean_df, test_set_path)

    bundle = evaluate_pipeline(
        settings,
        index,
        test_set_path,
        settings.paths.baseline_metrics,
        settings.paths.baseline_answers,
    )
    metrics = bundle.summary
    logger.info("Baseline metrics: %s", {k: v for k, v in metrics.items() if k != "ragas"})

    quality = run_data_quality_checks(clean_df, settings, report_name="baseline")
    freshness = build_freshness_report(clean_df, settings, settings.paths.freshness_report)

    generate_phase1_report(
        settings.paths.baseline_report,
        source_summary,
        metrics,
        quality,
        freshness,
    )
    logger.info("Baseline report written to %s.", settings.paths.baseline_report)

    # Optional live agent demo on a few test-set questions.
    demo_questions = [item["question"] for item in read_json(test_set_path)][:3]
    agent = build_agent(settings, index)
    demo = [
        {"question": question, "answer": run_agent_question(agent, question)}
        for question in demo_questions
    ]
    write_json(settings.paths.demo_answers, demo)
    logger.info("Agent demo answers written to %s.", settings.paths.demo_answers)
