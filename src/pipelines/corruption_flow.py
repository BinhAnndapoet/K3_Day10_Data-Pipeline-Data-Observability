from __future__ import annotations

import pandas as pd
from datetime import datetime, UTC

from core.config import load_settings
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import load_raw_records
from ingestion.cleaning import build_clean_dataframe
from retrieval.index import LocalEmbeddingIndex
from evaluation.metrics import evaluate_pipeline
from observability.quality import run_data_quality_checks, build_freshness_report
from observability.reporting import generate_corruption_report
from core.utils import read_json

def main() -> None:
    print("1. Load baseline metrics va clean dataset.")
    settings = load_settings()
    baseline_metrics = read_json(settings.paths.baseline_metrics)
    clean_df = pd.read_csv(settings.paths.clean_csv)

    print("2. Tao corrupted dataframe.")
    corrupted_df = corrupt_clean_dataframe(
        clean_df.copy(), 
        output_log_path=settings.paths.corruption_log
    )

    print("3. Save corrupted artifacts.")
    corrupted_df.to_csv(settings.paths.corrupted_clean_csv, index=False)
    corrupted_df.to_json(settings.paths.corrupted_clean_json, orient="records", indent=2)

    print("4. Rebuild index va evaluate.")
    corrupted_index = LocalEmbeddingIndex.build(
        df=corrupted_df,
        settings=settings,
        embeddings_output_path=settings.paths.corrupted_embeddings_json,
    )
    
    corrupted_eval_bundle = evaluate_pipeline(
        settings=settings,
        index=corrupted_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.corrupted_metrics,
        answers_output_path=settings.paths.corrupted_answers,
    )

    print("5. Run quality checks/freshness tren corrupted data.")
    corrupted_quality = run_data_quality_checks(corrupted_df, settings, "corrupted")
    corrupted_freshness = build_freshness_report(
        corrupted_df, 
        settings, 
        settings.paths.quality_dir / "freshness_corrupted.json"
    )

    print("6. Repair lai tu raw records.")
    raw_records = load_raw_records(settings.paths.raw_records_json)
    repaired_df = build_clean_dataframe(raw_records, run_date=datetime.now(UTC))
    
    repaired_df.to_csv(settings.paths.repaired_clean_csv, index=False)
    repaired_df.to_json(settings.paths.repaired_clean_json, orient="records", indent=2)

    repaired_index = LocalEmbeddingIndex.build(
        df=repaired_df,
        settings=settings,
        embeddings_output_path=settings.paths.repaired_embeddings_json,
    )

    print("7. Evaluate repaired dataset.")
    repaired_eval_bundle = evaluate_pipeline(
        settings=settings,
        index=repaired_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.repaired_metrics,
        answers_output_path=settings.paths.repaired_answers,
    )
    
    repaired_quality = run_data_quality_checks(repaired_df, settings, "repaired")
    repaired_freshness = build_freshness_report(
        repaired_df, 
        settings, 
        settings.paths.quality_dir / "freshness_repaired.json"
    )

    print("8. Tao comparison report.")
    generate_corruption_report(
        report_path=settings.paths.comparison_report,
        baseline_metrics=baseline_metrics,
        corrupted_metrics=corrupted_eval_bundle.summary,
        repaired_metrics=repaired_eval_bundle.summary,
        corrupted_quality=corrupted_quality,
        repaired_quality=repaired_quality,
        corrupted_freshness=corrupted_freshness,
        repaired_freshness=repaired_freshness,
    )
    
    print("Corruption flow pipeline completed successfully.")

if __name__ == "__main__":
    main()
