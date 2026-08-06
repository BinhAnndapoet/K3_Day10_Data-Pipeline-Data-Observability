from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pandas as pd

from core.utils import first_sentence, write_json

logger = logging.getLogger(__name__)

# Hard bounds for the frozen evaluation set.
MIN_QUESTIONS = 5
TARGET_QUESTIONS = 10

# Rotate through these question types so the set covers several skills.
QUESTION_TYPES = ("authors", "summary", "date", "categories", "summary")


def _is_quotable_title(title: Any) -> bool:
    """Title is safe to embed inside single quotes in a question.

    The QA layer extracts the title via a ``'([^']+)'`` regex, so titles that
    themselves contain a single quote (or a newline) would break the lookup.
    """
    if not isinstance(title, str) or not title.strip():
        return False
    return "'" not in title and "\n" not in title


def _make_question(question_type: str, title: str) -> str:
    """Build a question whose phrasing the QA answer-extractor can route on.

    Phrasings are deliberately aligned with ``retrieval/qa.py``:
      * "Who authored"    -> authors_joined
      * "When was ... published" -> published date
      * "What categories" -> categories_joined
      * anything else     -> first sentence of the summary
    The title is wrapped in single quotes so the exact-title lookup tool fires
    and the right document is guaranteed to be retrieved at baseline.
    """
    if question_type == "authors":
        return f"Who authored the paper '{title}'?"
    if question_type == "date":
        return f"When was the paper '{title}' published?"
    if question_type == "categories":
        return f"What categories are listed for the paper '{title}'?"
    return f"What is the main contribution described in the paper '{title}'?"


def _ground_truth(question_type: str, row: pd.Series) -> str:
    """Pull the gold answer directly from the cleaned row."""
    if question_type == "authors":
        return str(row["authors_joined"])
    if question_type == "date":
        return str(row["published"])
    if question_type == "categories":
        return str(row["categories_joined"])
    return first_sentence(str(row["summary"]))


def build_test_set(df: pd.DataFrame, output_path) -> list[dict[str, Any]]:
    """Create a frozen evaluation set from the cleaned dataframe.

    Each sample follows the schema:
      {
        "id": "q1",
        "question_type": "authors" | "summary" | "date" | "categories",
        "question": "...",
        "ground_truth": "<verbatim answer from clean data>",
        "ground_truth_doc_ids": ["<paper_id>"]
      }
    """
    if df is None or len(df) == 0:
        raise ValueError("Cannot build a test set from an empty dataframe.")

    candidates = df[
        df["authors_joined"].astype(bool)
        & df["summary"].astype(bool)
        & df["title"].apply(_is_quotable_title)
    ].copy()

    if len(candidates) < MIN_QUESTIONS:
        raise ValueError(
            f"Need at least {MIN_QUESTIONS} quotable papers with authors and a "
            f"summary; found {len(candidates)}."
        )

    # Prefer the freshest papers; keep a pool so we can skip a type when a
    # candidate has no categories.
    candidates = candidates.sort_values(by="age_days", ascending=True, na_position="last")
    pool = candidates.head(TARGET_QUESTIONS * 2)

    questions: list[dict[str, Any]] = []
    seen_paper_ids: set[str] = set()

    for _, row in pool.iterrows():
        if len(questions) >= TARGET_QUESTIONS:
            break

        question_type = QUESTION_TYPES[len(questions) % len(QUESTION_TYPES)]
        if question_type == "categories" and not str(row["categories_joined"]).strip():
            question_type = "authors"

        paper_id = str(row["paper_id"])
        if paper_id in seen_paper_ids:
            continue

        ground_truth = _ground_truth(question_type, row)
        if not ground_truth.strip():
            continue

        questions.append(
            {
                "id": f"q{len(questions) + 1}",
                "question_type": question_type,
                "question": _make_question(question_type, str(row["title"])),
                "ground_truth": ground_truth,
                "ground_truth_doc_ids": [paper_id],
            }
        )
        seen_paper_ids.add(paper_id)

    if len(questions) < MIN_QUESTIONS:
        raise ValueError(
            f"Could only generate {len(questions)} questions; minimum is {MIN_QUESTIONS}."
        )

    output = Path(output_path)
    write_json(output, questions)
    logger.info("Wrote %d frozen evaluation questions to %s.", len(questions), output)
    return questions
