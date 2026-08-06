"""Corruption — 6 dạng hư hỏng có chủ đích, log chi tiết, tác động đo được."""

from __future__ import annotations

import sys
from pathlib import Path

_APP = Path(__file__).resolve().parents[1]
if str(_APP) not in sys.path:
    sys.path.insert(0, str(_APP))

import json

import pandas as pd
import streamlit as st

from shared import (
    ANSWERS,
    CORRUPTION_LOG,
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
    rule,
)

st.set_page_config(page_title="Corruption · Pipeline Ledger", page_icon="▤", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)

P = SETTINGS.paths

page_header(
    "Phase 5 · Corruption",
    "Dữ liệu bị bóp méo có chủ đích",
    '<span class="no">06</span>loại hư hỏng · 21 dòng',
    "Corrupt từ baseline clean (24 dòng → 21 dòng), rebuild index <b style='font-family:IBM Plex Mono'>papers-corrupted</b>, "
    "evaluate bằng <b>cùng test set đóng băng</b>, đo quality/freshness. Baseline không bị ghi đè.",
)

quality = QUALITY["corrupted"]
freshness = FRESHNESS["corrupted"]
metrics = METRICS["corrupted"]

# ---- summary strip ----
summary_items = [
    ("Số dòng", f'{quality["row_count"]}', "dòng"),
    ("Quality", "đạt" if quality["passed"] else "KHÔNG đạt", ""),
    ("Freshness", "mới" if freshness["is_fresh"] else "CŨ", ""),
    ("Stale rows", str(freshness["stale_rows"]), "dòng"),
]
cols = st.columns(4, gap="medium")
for col, (label, value, unit) in zip(cols, summary_items):
    color = "#dc2626" if (label in ("Quality", "Freshness") and value in ("KHÔNG đạt", "CŨ")) else "#17181a"
    col.markdown(
        f"""
        <div class="sheet">
          <div class="sh-head"><span class="sh-name" style="font-size:15px">{label}</span></div>
          <div class="sh-body"><div class="stat-row"><span class="label">—</span>
          <span class="value" style="font-size:20px;color:{color}">{value}<span class="unit"> {unit}</span></span></div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

rule("Sổ nhật ký corruption")

if CORRUPTION_LOG:
    entries = CORRUPTION_LOG.get("corruptions", [])
    total_affected = sum(len(e.get("paper_ids", [])) for e in entries)
    st.markdown(
        f'<div class="ledger-note" style="margin-bottom:10px">Tổng cộng <b>{total_affected}</b> dòng bị ảnh hưởng bởi <b>{len(entries)}</b> dạng hư hỏng. Mỗi mục ghi loại, tham số và danh sách paper_id.</div>',
        unsafe_allow_html=True,
    )
    for entry in entries:
        type_label = entry["type"].replace("_", " ").title()
        paper_ids = entry.get("paper_ids", [])
        count = len(paper_ids)
        with st.expander(f"{type_label} — {count} dòng", expanded=False):
            st.markdown(
                f'<div class="corrupt-entry"><span class="ct">{type_label}</span><span class="cn">{count} dòng</span></div>',
                unsafe_allow_html=True,
            )
            st.code(json.dumps(entry, ensure_ascii=False, indent=2), language="json")
            st.markdown("**paper_ids bị ảnh hưởng:**")
            st.write(", ".join(paper_ids))

rule("Chỉ số sau corruption — so với baseline")

metric_keys = ("retrieval_hit_rate", "mean_token_f1", "judge_accuracy", "mean_judge_score")
bar_cols = st.columns(4, gap="medium")
for col, key in zip(bar_cols, metric_keys):
    value = metrics[key]
    base = METRICS["baseline"][key]
    delta = value - base
    unit = "/ 5" if key == "mean_judge_score" else "/ 1.000"
    delta_html = (
        f'<span class="delta down">−{abs(delta):.2f}</span>'
        if delta < -1e-9
        else f'<span class="delta up">+{delta:.2f}</span>' if delta > 1e-9 else ""
    )
    width = value / 5 * 100 if key == "mean_judge_score" else value * 100
    col.markdown(
        f"""
        <div class="sheet">
          <div class="sh-head"><span class="sh-name" style="font-size:15px">{key}</span></div>
          <div class="sh-body">
            <div class="stat-row"><span class="value" style="font-size:26px">{value:.3f}<span class="unit"> {unit}</span>{delta_html}</span></div>
            <div style="height:6px;background:#f0ece3;border-radius:3px;margin-top:10px;overflow:hidden">
              <div style="height:100%;width:{width:.1f}%;background:#dc2626;border-radius:3px"></div>
            </div>
            <div class="small-stat" style="font-family:IBM Plex Mono;font-size:10.5px;color:#8b909a;margin-top:6px">baseline: {base:.3f}</div>
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
        cls = "ok" if result.get("passed") else "fail"
        rows.append(
            f'<div class="stat-row"><span class="label">{check_labels.get(name, name)}</span>'
            f'<span class="value" style="font-size:12px;color:{"#16a34a" if result.get("passed") else "#dc2626"}">{passed} <span class="unit">{detail}</span></span></div>'
        )
    st.markdown(
        f"""<div class="sheet"><div class="sh-head"><span class="sh-name">Quality checks</span>
        <span class="sh-rows" style="color:#dc2626">{'đạt' if quality['passed'] else 'KHÔNG đạt'}</span></div>
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
        f'<div class="stat-row"><span class="label">{label}</span>'
        f'<span class="value" style="font-size:12px;color:{"#16a34a" if (label != "Kết luận" or freshness.get("is_fresh")) else "#dc2626"}">{value}</span></div>'
        for label, value in freshness_rows
    )
    st.markdown(
        f"""<div class="sheet"><div class="sh-head"><span class="sh-name">Freshness</span></div>
        <div class="sh-body">{rows}</div></div>""",
        unsafe_allow_html=True,
    )

rule("Trả lời từng câu hỏi — câu nào trả lời sai?")

miss_count = sum(1 for a in ANSWERS["corrupted"] if not a["retrieval_hit"])
st.markdown(
    f'<div class="ledger-note" style="margin-bottom:8px"><b>{miss_count}/10</b> câu hỏi bị miss retrieval sau corruption (baseline: 0/10).</div>',
    unsafe_allow_html=True,
)
for question_id, per_state in qa_answer_rows().items():
    sample = per_state["baseline"]
    corrupted = per_state.get("corrupted")
    type_vi = TYPE_VI.get(sample["question_type"], sample["question_type"])
    st.markdown(
        f'<div class="rule" style="margin-top:18px"><span class="rule-label" style="font-size:17px">{question_id} · {type_vi}</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown(f'<div class="ledger-note" style="margin-bottom:8px">{sample["question"]}</div>', unsafe_allow_html=True)
    if corrupted:
        st.markdown(qa_sheet(question_id, "corrupted", corrupted, sample["ground_truth"]), unsafe_allow_html=True)

st.markdown(
    '<div class="foot">Lỗi data phải có chủ đích, có log và đo được tác động; không tạo corruption chỉ để có file.</div>',
    unsafe_allow_html=True,
)
