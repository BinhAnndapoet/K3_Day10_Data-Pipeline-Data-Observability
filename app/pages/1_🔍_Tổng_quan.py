"""Tổng quan — 3 trạng thái pipeline trên một trang."""

from __future__ import annotations

import sys
from pathlib import Path

_APP = Path(__file__).resolve().parents[1]
if str(_APP) not in sys.path:
    sys.path.insert(0, str(_APP))

import json

import streamlit as st

from shared import (
    ANSWERS,
    CORRUPTION_LOG,
    CSS,
    METRICS,
    METRIC_LABELS,
    STATES,
    STATE_COLOR,
    STATE_LABEL,
    page_header,
    rule,
    sheet,
)

st.set_page_config(page_title="Tổng quan · Pipeline Ledger", page_icon="▤", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)

page_header(
    "Day 10 · Data Pipeline & Observability — Bản ghi khảo sát",
    "Ba trạng thái của một luồng dữ liệu",
    '<span class="no">03</span>phiên bản · cùng test set',
    "Cùng một <b>test set đóng băng</b> (10 câu hỏi), cùng một evaluator, cùng một nguồn raw — "
    "chỉ dữ liệu thay đổi giữa ba lần chạy. Số liệu đọc trực tiếp từ artifact trong "
    "<b style='font-family:IBM Plex Mono;font-size:12px'>data/</b>, không tính lại, không tô vẽ.",
)

# pipeline diagram
flow_nodes = ["Raw Crossref", "Clean", "Index", "Test set", "Evaluate", "Quality", "Report"]
flow_html = '<div class="flow">' + '<span class="arrow">→</span>'.join(
    f'<span class="node">{node}</span>' for node in flow_nodes
) + "</div>"
st.markdown(flow_html, unsafe_allow_html=True)

cols = st.columns(3, gap="medium")
for col, state in zip(cols, STATES):
    col.markdown(sheet(state), unsafe_allow_html=True)

rule("Biến động chỉ số")

import plotly.graph_objects as go  # noqa: E402

fig = go.Figure()
for key in ("retrieval_hit_rate", "mean_token_f1", "judge_accuracy", "mean_judge_score"):
    fig.add_trace(
        go.Scatter(
            x=[0, 1, 2],
            y=[METRICS[s][key] for s in STATES],
            mode="lines+markers",
            name=METRIC_LABELS[key],
            line=dict(width=2.2),
            marker=dict(size=7),
            hovertemplate="%{y:.3f}<extra></extra>",
        )
    )
fig.update_layout(
    xaxis=dict(tickvals=[0, 1, 2], ticktext=[f"<b>{STATE_LABEL[s]}</b>" for s in STATES], gridcolor="#f0ece3"),
    yaxis=dict(title="Giá trị", gridcolor="#f0ece3"),
    plot_bgcolor="#faf8f4",
    paper_bgcolor="#faf8f4",
    font=dict(family="IBM Plex Sans", color="#4a4f57", size=12),
    legend=dict(orientation="h", yanchor="bottom", y=1.04, xanchor="left", x=0),
    height=330,
    margin=dict(l=40, r=20, t=10, b=30),
)
st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

rule("Sự cố đã ghi nhận")

if CORRUPTION_LOG:
    entries = CORRUPTION_LOG.get("corruptions", [])
    cols = st.columns(3, gap="medium")
    for i, entry in enumerate(entries):
        type_label = entry["type"].replace("_", " ").title()
        count = len(entry.get("paper_ids", []))
        detail = ", ".join(entry.get("paper_ids", [])[:3])
        cols[i % 3].markdown(
            f'<div class="corrupt-entry" style="margin-bottom:8px"><span class="ct">{type_label}</span>'
            f'<span class="cn">{count} dòng</span></div>',
            unsafe_allow_html=True,
        )
        with cols[i % 3].expander("chi tiết"):
            st.code(json.dumps(entry, ensure_ascii=False, indent=2))

st.markdown(
    '<div class="foot">Số liệu đọc từ data/results · data/quality · data/clean — không tính lại. '
    "Judge dùng fallback heuristic khi model free không hỗ trợ structured output.</div>",
    unsafe_allow_html=True,
)
