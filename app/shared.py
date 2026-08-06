"""Shared data loading, styles and helpers for the Pipeline Ledger app."""

from __future__ import annotations

import json
from pathlib import Path
import sys

# Make app/ and src/ importable regardless of how the app is launched.
_APP = Path(__file__).resolve().parent
_SRC = _APP.parent / "src"
for _path in (_APP, _SRC):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from core.config import load_settings  # noqa: E402

SETTINGS = load_settings()
P = SETTINGS.paths


def read(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


def read_text(path: Path) -> str | None:
    """Read a file as raw text (markdown reports, etc.)."""
    if not path.exists():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


METRICS = {
    "baseline": read(P.baseline_metrics),
    "corrupted": read(P.corrupted_metrics),
    "repaired": read(P.repaired_metrics),
}
QUALITY = {
    "baseline": read(P.quality_dir / "quality_report_baseline.json"),
    "corrupted": read(P.quality_dir / "quality_report_corrupted.json"),
    "repaired": read(P.quality_dir / "quality_report_repaired.json"),
}
FRESHNESS = {
    "baseline": read(P.freshness_report),
    "corrupted": read(P.quality_dir / "freshness_report_corrupted.json"),
    "repaired": read(P.quality_dir / "freshness_report_repaired.json"),
}
ANSWERS = {
    "baseline": read(P.baseline_answers),
    "corrupted": read(P.corrupted_answers),
    "repaired": read(P.repaired_answers),
}
CORRUPTION_LOG = read(P.corruption_log)

STATES = ["baseline", "corrupted", "repaired"]
STATE_LABEL = {"baseline": "Baseline", "corrupted": "Corrupted", "repaired": "Repaired"}
STATE_COLOR = {"baseline": "#b45309", "corrupted": "#dc2626", "repaired": "#16a34a"}
STATE_SUBTITLE = {
    "baseline": "Nguồn tin cậy · đo trước khi hư hỏng",
    "corrupted": "Dữ liệu bị bóp méo có chủ đích",
    "repaired": "Tái dựng từ raw snapshot",
}
METRIC_LABELS = {
    "retrieval_hit_rate": "Retrieval hit rate",
    "mean_token_f1": "Token F1",
    "judge_accuracy": "Judge accuracy",
    "mean_judge_score": "Judge score (1–5)",
}
TYPE_VI = {
    "authors": "tác giả",
    "summary": "tóm tắt",
    "date": "ngày xuất bản",
    "categories": "danh mục",
}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

:root {
  --paper: #faf8f4;
  --paper-2: #ffffff;
  --ink: #17181a;
  --ink-2: #4a4f57;
  --muted: #8b909a;
  --line: #e2ddd4;
  --line-strong: #c9c2b5;
  --amber: #b45309;
  --red: #dc2626;
  --green: #16a34a;
  --blue: #0f62fe;
  --serif: 'Fraunces', Georgia, serif;
  --sans: 'IBM Plex Sans', sans-serif;
  --mono: 'IBM Plex Mono', monospace;
}

.stApp { background: var(--paper); color: var(--ink); }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 2.2rem; padding-bottom: 4rem; max-width: 1380px; }

/* masthead */
.ledger-head { border-bottom: 2px solid var(--ink); padding-bottom: 16px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: flex-end; }
.ledger-head .kicker { font-family: var(--mono); font-size: 11px; letter-spacing: 2.5px; text-transform: uppercase; color: var(--blue); margin-bottom: 8px; }
.ledger-head h1 { font-family: var(--serif); font-size: 42px; font-weight: 600; letter-spacing: -0.5px; margin: 0; line-height: 1.04; color: var(--ink); }
.ledger-head .edition { font-family: var(--mono); font-size: 11px; color: var(--muted); text-align: right; white-space: nowrap; }
.ledger-head .edition .no { font-size: 20px; color: var(--ink); display: block; font-weight: 600; }

.ledger-note { font-family: var(--sans); font-size: 13.5px; color: var(--ink-2); max-width: 760px; margin-bottom: 24px; line-height: 1.55; }
.ledger-note b { color: var(--ink); }

/* sheets */
.sheet { background: var(--paper-2); border: 1px solid var(--line); box-shadow: 0 1px 2px rgba(23,24,26,.04); border-radius: 2px; padding: 0; }
.sheet .sh-head { padding: 14px 18px 12px; border-bottom: 1px solid var(--line); display: flex; justify-content: space-between; align-items: baseline; }
.sheet .sh-name { font-family: var(--serif); font-size: 20px; font-weight: 600; color: var(--ink); display: flex; align-items: center; gap: 9px; }
.sheet .sh-name .mark { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
.sheet .sh-rows { font-family: var(--mono); font-size: 12px; color: var(--muted); }
.sheet .sh-sub { font-family: var(--sans); font-size: 11.5px; color: var(--muted); padding: 9px 18px; border-bottom: 1px solid var(--line); font-style: italic; }
.sheet .sh-body { padding: 16px 18px 18px; }

.stat-row { display: flex; justify-content: space-between; align-items: baseline; padding: 9px 0; border-bottom: 1px dotted var(--line-strong); }
.stat-row:last-child { border-bottom: none; }
.stat-row .label { font-family: var(--sans); font-size: 12px; color: var(--ink-2); }
.stat-row .value { font-family: var(--mono); font-size: 15px; font-weight: 500; color: var(--ink); }
.stat-row .value .unit { font-size: 11px; color: var(--muted); font-weight: 400; }
.stat-row .delta { font-family: var(--mono); font-size: 11px; margin-left: 8px; padding: 1px 6px; border-radius: 3px; }
.stat-row .delta.down { color: var(--red); background: rgba(220,38,38,.08); }
.stat-row .delta.up { color: var(--green); background: rgba(22,163,74,.08); }

.verdict { display: flex; gap: 6px; margin-top: 14px; flex-wrap: wrap; }
.verdict .tag { font-family: var(--mono); font-size: 10px; letter-spacing: .5px; padding: 4px 9px; border: 1px solid var(--line-strong); border-radius: 3px; color: var(--ink-2); }
.verdict .tag.ok { color: var(--green); border-color: rgba(22,163,74,.5); }
.verdict .tag.fail { color: var(--red); border-color: rgba(220,38,38,.55); font-weight: 600; }

/* rules */
.rule { display: flex; align-items: center; gap: 14px; margin: 30px 0 14px; }
.rule .rule-label { font-family: var(--serif); font-size: 22px; font-weight: 600; color: var(--ink); white-space: nowrap; }
.rule .rule-line { flex: 1; height: 1px; background: var(--line-strong); }

/* corruption ledger */
.corrupt-entry { display: flex; justify-content: space-between; align-items: center; padding: 9px 14px; border-left: 3px solid var(--red); background: var(--paper-2); border-bottom: 1px solid var(--line); font-family: var(--mono); font-size: 12px; }
.corrupt-entry .ct { color: var(--ink); }
.corrupt-entry .cn { color: var(--muted); }

/* qa sheets */
.qa-sheet { background: var(--paper-2); border: 1px solid var(--line); border-radius: 2px; padding: 13px 16px; margin-bottom: 10px; }
.qa-sheet .q-line { font-family: var(--sans); font-size: 13px; color: var(--ink); margin-bottom: 7px; }
.qa-sheet .q-line .tag { font-family: var(--mono); font-size: 10px; padding: 2px 7px; border-radius: 3px; margin-right: 6px; }
.qa-sheet .pair { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.qa-sheet .cell .k { font-family: var(--mono); font-size: 9.5px; letter-spacing: 1.2px; text-transform: uppercase; color: var(--muted); margin-bottom: 3px; }
.qa-sheet .cell .v { font-size: 12px; color: var(--ink-2); line-height: 1.45; }
.qa-sheet .f1 { font-family: var(--mono); font-size: 10.5px; margin-top: 7px; }
.qa-sheet .f1.hit { color: var(--green); }
.qa-sheet .f1.miss { color: var(--red); font-weight: 600; }

/* pipeline diagram */
.flow { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; font-family: var(--mono); font-size: 11.5px; margin: 6px 0 4px; }
.flow .node { background: var(--paper-2); border: 1px solid var(--line-strong); border-radius: 3px; padding: 5px 11px; color: var(--ink); }
.flow .node.hot { border-color: var(--blue); color: var(--blue); }
.flow .arrow { color: var(--muted); }

.foot { font-family: var(--mono); font-size: 10px; color: var(--muted); border-top: 1px solid var(--line); padding-top: 10px; margin-top: 34px; line-height: 1.6; }

/* dataframe polish */
[data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 2px; }
[data-testid="stDataFrame"] thead th { font-family: var(--mono); font-size: 11px; background: #f3efe7; color: var(--ink-2); }
[data-testid="stDataFrame"] tbody td { font-size: 12px; font-family: var(--sans); }

/* sidebar */
[data-testid="stSidebar"] { background: var(--paper-2); border-right: 1px solid var(--line); }
[data-testid="stSidebar"] * { font-family: var(--sans); }
[data-testid="stSidebar"] .stButton button { font-family: var(--mono); font-size: 12px; }
</style>
"""


def page_header(kicker: str, title: str, edition: str, note: str | None = None) -> None:
    import streamlit as st

    st.markdown(
        f"""
        <div class="ledger-head">
          <div>
            <div class="kicker">{kicker}</div>
            <h1>{title}</h1>
          </div>
          <div class="edition">{edition}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if note:
        st.markdown(f'<div class="ledger-note">{note}</div>', unsafe_allow_html=True)


def rule(label: str) -> None:
    import streamlit as st

    st.markdown(
        f'<div class="rule"><span class="rule-label">{label}</span><span class="rule-line"></span></div>',
        unsafe_allow_html=True,
    )


def sheet(state: str) -> str:
    """Render one state sheet (baseline/corrupted/repaired) as HTML."""
    metrics = METRICS[state]
    quality = QUALITY[state]
    freshness = FRESHNESS[state]
    color = STATE_COLOR[state]

    rows_html = []
    for key, label in METRIC_LABELS.items():
        value = metrics[key]
        unit = "/ 5" if key == "mean_judge_score" else "/ 1.000"
        delta_html = ""
        if state == "corrupted":
            d = metrics[key] - METRICS["baseline"][key]
            if abs(d) > 1e-9:
                sign = "−" if d < 0 else "+"
                delta_html = f'<span class="delta down">{sign}{abs(d):.2f}</span>'
        elif state == "repaired":
            d = metrics[key] - METRICS["corrupted"][key]
            if abs(d) > 1e-9:
                sign = "+" if d > 0 else "−"
                cls = "up" if d > 0 else "down"
                delta_html = f'<span class="delta {cls}">{sign}{abs(d):.2f}</span>'
        rows_html.append(
            f'<div class="stat-row"><span class="label">{label}</span>'
            f'<span class="value">{value:.3f}<span class="unit"> {unit}</span>{delta_html}</span></div>'
        )

    tags = []
    tags.append(
        f'<span class="tag {"ok" if quality["passed"] else "fail"}">quality '
        f'{"đạt" if quality["passed"] else "KHÔNG đạt"}</span>'
    )
    tags.append(
        f'<span class="tag {"ok" if freshness["is_fresh"] else "fail"}">freshness '
        f'{"mới" if freshness["is_fresh"] else "cũ"}</span>'
    )
    tags.append(f'<span class="tag">stale {freshness["stale_rows"]}</span>')

    return f"""
    <div class="sheet">
      <div class="sh-head">
        <span class="sh-name"><span class="mark" style="background:{color}"></span>{STATE_LABEL[state]}</span>
        <span class="sh-rows">{quality["row_count"]} dòng</span>
      </div>
      <div class="sh-sub">{STATE_SUBTITLE[state]}</div>
      <div class="sh-body">
        {''.join(rows_html)}
        <div class="verdict">{''.join(tags)}</div>
      </div>
    </div>
    """


def qa_sheet(question_id: str, state: str, answer: dict, ground_truth: str) -> str:
    """Render one per-state answer sheet for a question."""
    hit = answer["retrieval_hit"]
    f1_cls = "hit" if hit else "miss"
    f1_txt = "HIT" if hit else "MISS"
    return f"""
    <div class="qa-sheet">
      <div class="q-line">
        <span class="tag" style="background:{STATE_COLOR[state]};color:#fff">{STATE_LABEL[state]}</span>
        <span>{question_id}</span>
      </div>
      <div class="pair">
        <div class="cell"><div class="k">Ground truth</div><div class="v">{ground_truth[:150]}</div></div>
        <div class="cell"><div class="k">Trả lời</div><div class="v">{answer["answer"][:150]}</div></div>
      </div>
      <div class="f1 {f1_cls}">retrieval {f1_txt} · token F1 {answer["token_f1"]:.2f}</div>
    </div>
    """


def qa_answer_rows() -> dict[str, dict[str, dict]]:
    """Group answers by question id, keyed by state."""
    answers_by_id: dict[str, dict[str, dict]] = {}
    for state in STATES:
        for answer in ANSWERS[state] or []:
            answers_by_id.setdefault(answer["id"], {})[state] = answer
    return answers_by_id
