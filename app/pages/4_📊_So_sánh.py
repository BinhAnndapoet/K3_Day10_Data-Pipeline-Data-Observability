"""So sánh — baseline / corrupted / repaired, delta và phục hồi."""

from __future__ import annotations

import sys
from pathlib import Path

_APP = Path(__file__).resolve().parents[1]
if str(_APP) not in sys.path:
    sys.path.insert(0, str(_APP))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from shared import (
    ANSWERS,
    CSS,
    METRICS,
    METRIC_LABELS,
    SETTINGS,
    STATES,
    STATE_COLOR,
    STATE_LABEL,
    TYPE_VI,
    page_header,
    qa_answer_rows,
    qa_sheet,
    read_text,
    rule,
    sheet,
)

st.set_page_config(page_title="So sánh · Pipeline Ledger", page_icon="▤", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)

P = SETTINGS.paths

page_header(
    "Phase 6 · Repair & Comparison",
    "Phục hồi về vạch xuất phát",
    '<span class="no">03</span>trạng thái · 1 bảng delta',
    "Repair bằng cách chạy lại cleaning từ raw snapshot — không sửa tay answers hay metrics. "
    "So sánh ba trạng thái trên cùng metric, cùng test set, cùng evaluator.",
)

rule("Ba trạng thái song song")

cols = st.columns(3, gap="medium")
for col, state in zip(cols, STATES):
    col.markdown(sheet(state), unsafe_allow_html=True)

rule("Bảng delta — sụt giảm và phục hồi")

metric_keys = ("retrieval_hit_rate", "mean_token_f1", "judge_accuracy", "mean_judge_score")

delta_data = []
for key in metric_keys:
    base = METRICS["baseline"][key]
    corr = METRICS["corrupted"][key]
    rep = METRICS["repaired"][key]
    delta_corruption = corr - base
    delta_repair = rep - corr
    delta_data.append(
        {
            "Chỉ số": METRIC_LABELS[key],
            "Baseline": round(base, 3),
            "Corrupted": round(corr, 3),
            "Repaired": round(rep, 3),
            "Δ corruption": round(delta_corruption, 3),
            "Δ repair": round(delta_repair, 3),
        }
    )

delta_df = pd.DataFrame(delta_data)

def _style(v, colname):
    if colname == "Δ corruption":
        return "color:#dc2626;font-weight:600" if v < 0 else "color:#17181a"
    if colname == "Δ repair":
        return "color:#16a34a;font-weight:600" if v > 0 else "color:#17181a"
    return ""

st.dataframe(
    delta_df.style.map(lambda v: "", subset=["Baseline", "Corrupted", "Repaired"])
    .map(lambda v: "color:#dc2626;font-weight:600" if v < 0 else "color:#17181a", subset=["Δ corruption"])
    .map(lambda v: "color:#16a34a;font-weight:600" if v > 0 else "color:#17181a", subset=["Δ repair"]),
    use_container_width=True,
    hide_index=True,
)

rule("Biến động qua 3 trạng thái")

fig = go.Figure()
for key in metric_keys:
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
fig.add_vline(x=1, line_dash="dash", line_color="#c9c2b5", annotation_text=" corruption", annotation_position="top right")
fig.update_layout(
    xaxis=dict(tickvals=[0, 1, 2], ticktext=[f"<b>{STATE_LABEL[s]}</b>" for s in STATES], gridcolor="#f0ece3"),
    yaxis=dict(title="Giá trị", gridcolor="#f0ece3"),
    plot_bgcolor="#faf8f4",
    paper_bgcolor="#faf8f4",
    font=dict(family="IBM Plex Sans", color="#4a4f57", size=12),
    legend=dict(orientation="h", yanchor="bottom", y=1.04, xanchor="left", x=0),
    height=360,
    margin=dict(l=40, r=20, t=10, b=30),
)
st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

rule("Trả lời từng câu hỏi — 3 trạng thái cạnh nhau")

for question_id, per_state in qa_answer_rows().items():
    sample = per_state["baseline"]
    type_vi = TYPE_VI.get(sample["question_type"], sample["question_type"])
    st.markdown(
        f'<div class="rule" style="margin-top:18px"><span class="rule-label" style="font-size:17px">{question_id} · {type_vi}</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown(f'<div class="ledger-note" style="margin-bottom:8px">{sample["question"]}</div>', unsafe_allow_html=True)
    qa_cols = st.columns(3, gap="medium")
    for qa_col, state in zip(qa_cols, STATES):
        answer = per_state.get(state)
        if answer:
            qa_col.markdown(qa_sheet(question_id, state, answer, sample["ground_truth"]), unsafe_allow_html=True)
        else:
            qa_col.markdown(f'<div class="qa-sheet"><div class="q-line">{STATE_LABEL[state]}: n/a</div></div>', unsafe_allow_html=True)

rule("Báo cáo so sánh (markdown)")

report_text = read_text(P.comparison_report)
if report_text:
    st.markdown(report_text)

st.markdown(
    '<div class="foot">Ưu tiên evidence: report phải khớp artifact thật, không tô đẹp số liệu để demo. '
    "Chỉ công bố recovery khi số liệu và report chứng minh.</div>",
    unsafe_allow_html=True,
)
