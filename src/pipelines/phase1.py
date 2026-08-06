from __future__ import annotations

from datetime import datetime, UTC
import pandas as pd

from core.config import load_settings
from ingestion.crossref import fetch_source_records, load_raw_records
from ingestion.cleaning import build_clean_dataframe
from retrieval.index import LocalEmbeddingIndex
from evaluation.testset import build_test_set
from evaluation.metrics import evaluate_pipeline
from observability.quality import run_data_quality_checks, build_freshness_report
from observability.reporting import generate_phase1_report
from retrieval.qa import answer_question
from core.utils import write_json, read_json

def main() -> None:
    print("1. Load settings.")
    settings = load_settings()

    print("2. Load hoac fetch raw records.")
    if settings.refresh_source:
        records = fetch_source_records(settings)
    else:
        if not settings.paths.raw_records_json.exists():
            records = fetch_source_records(settings)
        else:
            records = load_raw_records(settings.paths.raw_records_json)

    print("3. Clean data.")
    df = build_clean_dataframe(records, run_date=datetime.now(UTC))

    print("4. Save clean CSV/JSON.")
    settings.paths.clean_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(settings.paths.clean_csv, index=False)
    df.to_json(settings.paths.clean_json, orient="records", indent=2)

    print("5. Build Chroma index.")
    index = LocalEmbeddingIndex.build(
        df=df,
        settings=settings,
        embeddings_output_path=settings.paths.embeddings_json,
    )

    print("6. Tao hoac load evaluation set.")
    if settings.refresh_test_set or not settings.paths.eval_testset.exists():
        test_set = build_test_set(df, settings.paths.eval_testset)
    else:
        test_set = read_json(settings.paths.eval_testset)

    print("7. Evaluate.")
    eval_bundle = evaluate_pipeline(
        settings=settings,
        index=index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.baseline_metrics,
        answers_output_path=settings.paths.baseline_answers,
    )

    print("8. Run quality checks va freshness report.")
    quality = run_data_quality_checks(df, settings, "baseline")
    freshness = build_freshness_report(df, settings, settings.paths.freshness_report)

    print("9. Tao markdown report.")
    source_summary = {
        "raw_records": len(records),
        "clean_records": len(df),
    }
    generate_phase1_report(
        report_path=settings.paths.baseline_report,
        source_summary=source_summary,
        metrics=eval_bundle.summary,
        quality=quality,
        freshness=freshness,
    )

    print("10. Co the demo agent tren vai sample question.")
    sample_questions = [
        "What are the main approaches in agentic RAG?",
        "How do language models use external memory?"
    ]
    demo_results = []
    for q in sample_questions:
        ans = answer_question(q, settings, index)
        demo_results.append({"question": q, "answer": ans.answer})
    
    write_json(settings.paths.demo_answers, demo_results)
    print("Phase 1 pipeline completed successfully.")

if __name__ == "__main__":
    main()
