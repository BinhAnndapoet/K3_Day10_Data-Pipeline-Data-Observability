from __future__ import annotations

import logging
from datetime import datetime

import pandas as pd

from core.config import Settings, load_settings, require_llm_credentials
from core.utils import read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from ingestion.cleaning import build_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_corruption_report
from retrieval.index import LocalEmbeddingIndex

logger = logging.getLogger(__name__)


def _load_baseline(settings: Settings) -> pd.DataFrame:
    """Read the baseline clean dataframe; the corruption flow needs it intact."""
    path = settings.paths.clean_csv
    if not path.exists():
        raise FileNotFoundError(
            f"Baseline clean dataset missing at {path}. Run phase1 first."
        )
    return pd.read_csv(path)


def _repair_from_raw(settings: Settings) -> pd.DataFrame:
    """Repair by re-running cleaning from the trusted raw snapshot."""
    records = load_raw_records(settings.paths.raw_records_json)
    if not records:
        raise RuntimeError("No raw records available to repair from.")
    return build_clean_dataframe(records, run_date=datetime.now())


def main() -> None:
    """Corruption -> evaluate -> repair -> compare flow with isolated paths."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    settings = load_settings()
    require_llm_credentials(settings)

    baseline_df = _load_baseline(settings)
    baseline_metrics = read_json(settings.paths.baseline_metrics)
    logger.info("Baseline loaded: %d rows.", len(baseline_df))

    # --- Corrupt ---
    corrupted_df = corrupt_clean_dataframe(
        baseline_df, settings, settings.paths.corruption_log
    )
    write_csv(corrupted_df, settings.paths.corrupted_clean_csv)
    write_json(settings.paths.corrupted_clean_json, corrupted_df.to_dict(orient="records"))

    # --- Rebuild corrupted index (isolated collection) and evaluate ---
    corrupted_index = LocalEmbeddingIndex.build(
        corrupted_df, settings, settings.paths.corrupted_embeddings_json
    )
    corrupted_bundle = evaluate_pipeline(
        settings,
        corrupted_index,
        settings.paths.eval_testset,
        settings.paths.corrupted_metrics,
        settings.paths.corrupted_answers,
    )
    logger.info("Corrupted metrics: %s", {k: v for k, v in corrupted_bundle.summary.items() if k != "ragas"})

    corrupted_quality = run_data_quality_checks(corrupted_df, settings, report_name="corrupted")
    corrupted_freshness = build_freshness_report(
        corrupted_df, settings, settings.paths.quality_dir / "freshness_report_corrupted.json"
    )

    # --- Repair from raw and evaluate ---
    repaired_df = _repair_from_raw(settings)
    write_csv(repaired_df, settings.paths.repaired_clean_csv)
    write_json(settings.paths.repaired_clean_json, repaired_df.to_dict(orient="records"))

    repaired_index = LocalEmbeddingIndex.build(
        repaired_df, settings, settings.paths.repaired_embeddings_json
    )
    repaired_bundle = evaluate_pipeline(
        settings,
        repaired_index,
        settings.paths.eval_testset,
        settings.paths.repaired_metrics,
        settings.paths.repaired_answers,
    )
    logger.info("Repaired metrics: %s", {k: v for k, v in repaired_bundle.summary.items() if k != "ragas"})

    repaired_quality = run_data_quality_checks(repaired_df, settings, report_name="repaired")
    repaired_freshness = build_freshness_report(
        repaired_df, settings, settings.paths.quality_dir / "freshness_report_repaired.json"
    )

    # --- Compare ---
    generate_corruption_report(
        settings.paths.comparison_report,
        baseline_metrics,
        corrupted_bundle.summary,
        repaired_bundle.summary,
        corrupted_quality,
        repaired_quality,
        corrupted_freshness,
        repaired_freshness,
    )
    logger.info("Comparison report written to %s.", settings.paths.comparison_report)
