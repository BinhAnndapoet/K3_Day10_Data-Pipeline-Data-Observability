"""Baseline — phase 1 end-to-end: raw → clean → index → test set → evaluate → report."""

from __future__ import annotations

import sys
from pathlib import Path

_APP = Path(__file__).resolve().parents[1]
if str(_APP) not in sys.path:
    sys.path.insert(0, str(_APP))

import json

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from shared import (
    ANSWERS,
    CSS,
    FRESHNESS,
    METRICS,
    QUALITY,
    SETTINGS,
    STATE_LABEL,
    TYPE_VI,
    page_header,
    qa_answer_rows,
    qa_sheet,
    read,
    read_text,
    rule,
)

st.set_page_config(page_title="Baseline · Pipeline Ledger", page_icon="▤", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)

P = SETTINGS.paths

page_header(
    "Phase 1 · Baseline",
    "Điểm chuẩn trước khi hư hỏng",
    '<span class="no">01</span>lần chạy gốc',
    "Raw Crossref (24 bản ghi) → clean (24 dòng) → index <b style='font-family:IBM Plex Mono'>papers-baseline</b> → "
    "test set đóng băng (10 câu) → evaluate → quality/freshness → báo cáo tiếng Việt.",
)

quality = QUALITY["baseline"]
freshness = FRESHNESS["baseline"]
metrics = METRICS["baseline"]

# ---- info strip ----
raw_records = read(P.raw_records_json) or []
info_cols = st.columns(4, gap="medium")
info_items = [
    ("Nguồn", SETTINGS.source_api, ""),
    ("Raw records", str(len(raw_records)), "bản ghi"),
    ("Clean rows", f'{quality["row_count"]}', "dòng"),
    ("Câu hỏi test set", "10", "câu"),
]
for col, (label, value, unit) in zip(info_cols, info_items):
    col.markdown(
        f"""
        <div class="sheet">
          <div class="sh-head"><span class="sh-name" style="font-size:15px">{label}</span></div>
          <div class="sh-body"><div class="stat-row"><span class="label">—</span>
          <span class="value" style="font-size:20px">{value}<span class="unit"> {unit}</span></span></div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

rule("Thông số nguồn (settings)")

st.code(
    json.dumps(
        {
            "source_query": SETTINGS.source_query,
            "source_filter": SETTINGS.source_filter,
            "max_results": SETTINGS.max_results,
            "top_k": SETTINGS.top_k,
            "embedding_model": SETTINGS.embedding_model,
            "collection": SETTINGS.baseline_collection_name,
            "freshness_threshold_days": SETTINGS.freshness_threshold_days,
        },
        ensure_ascii=False,
        indent=2,
    ),
    language="json",
)

rule("Chỉ số đánh giá")

metric_keys = ("retrieval_hit_rate", "mean_token_f1", "judge_accuracy", "mean_judge_score")
bar_cols = st.columns(4, gap="medium")
for col, key in zip(bar_cols, metric_keys):
    value = metrics[key]
    width = value / 5 * 100 if key == "mean_judge_score" else value * 100
    col.markdown(
        f"""
        <div class="sheet">
          <div class="sh-head"><span class="sh-name" style="font-size:15px">{key}</span></div>
          <div class="sh-body">
            <div class="stat-row"><span class="value" style="font-size:26px">{value:.3f}<span class="unit"> {'/ 5' if key=='mean_judge_score' else '/ 1.000'}</span></span></div>
            <div style="height:6px;background:#f0ece3;border-radius:3px;margin-top:10px;overflow:hidden">
              <div style="height:100%;width:{width:.1f}%;background:{'#b45309'};border-radius:3px"></div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

rule("Chất lượng dữ liệu & độ mới")

left, right = st.columns(2, gap="medium")
with left:
    checks = quality.get("checks", {})
    check_labels = {
        "row_count": "Số dòng",
        "paper_id": "Mã bài báo (paper_id)",
        "title": "Tiêu đề",
        "summary": "Tóm tắt",
        "duplicate_rows": "Dòng trùng lặp",
        "freshness": "Độ mới (freshness)",
    }
    rows = []
    for name, result in checks.items():
        passed = "đạt" if result.get("passed") else "KHÔNG đạt"
        detail = ", ".join(f"{k}={v}" for k, v in result.items() if k != "passed")
        rows.append(
            f'<div class="stat-row"><span class="label">{check_labels.get(name, name)}</span>'
            f'<span class="value" style="font-size:12px">{passed} <span class="unit">{detail}</span></span></div>'
        )
    st.markdown(
        f"""<div class="sheet"><div class="sh-head"><span class="sh-name">Quality checks</span>
        <span class="sh-rows">{'đạt' if quality['passed'] else 'KHÔNG đạt'}</span></div>
        <div class="sh-body">{''.join(rows)}</div></div>""",
        unsafe_allow_html=True,
    )
with right:
    freshness_rows = [
        ("Latest published", str(freshness.get("latest_published", "n/a"))),
        ("Oldest published", str(freshness.get("oldest_published", "n/a"))),
        ("Stale rows", str(freshness.get("stale_rows", "n/a"))),
        ("Threshold", f'{freshness.get("freshness_threshold_days", "n/a")} ngày'),
        ("Kết luận", "mới" if freshness.get("is_fresh") else "CŨ"),
    ]
    rows = "".join(
        f'<div class="stat-row"><span class="label">{label}</span><span class="value" style="font-size:12px">{value}</span></div>'
        for label, value in freshness_rows
    )
    st.markdown(
        f"""<div class="sheet"><div class="sh-head"><span class="sh-name">Freshness</span></div>
        <div class="sh-body">{rows}</div></div>""",
        unsafe_allow_html=True,
    )

rule("Báo cáo & answers")

report_text = read_text(P.baseline_report)
if report_text:
    st.markdown(report_text)

answers = ANSWERS["baseline"]
with st.expander("Toàn bộ answers (baseline)", expanded=False):
    st.json(answers)

rule("Trả lời từng câu hỏi")

for question_id, per_state in qa_answer_rows().items():
    sample = per_state["baseline"]
    type_vi = TYPE_VI.get(sample["question_type"], sample["question_type"])
    st.markdown(
        f'<div class="rule" style="margin-top:18px"><span class="rule-label" style="font-size:17px">{question_id} · {type_vi}</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown(f'<div class="ledger-note" style="margin-bottom:8px">{sample["question"]}</div>', unsafe_allow_html=True)
    col = st.columns(1)[0]
    col.markdown(qa_sheet(question_id, "baseline", sample, sample["ground_truth"]), unsafe_allow_html=True)

st.markdown(
    '<div class="foot">Baseline chỉ hoàn tất khi artifacts, metrics và report khớp nhau — không chỉ khi script exit code 0.</div>',
    unsafe_allow_html=True,
)
