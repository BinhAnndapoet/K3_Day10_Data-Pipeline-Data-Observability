"""Streamlit dashboard: 3 trạng thái pipeline — baseline / corrupted / repaired.

Industrial observatory style. Reads real artifacts under data/ — metrics,
quality, freshness, answers, corruption log. No fake numbers, no recompute.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core.config import load_settings

st.set_page_config(page_title="Pipeline Observatory", page_icon="◈", layout="wide")

# ---------------------------------------------------------------- artifacts
SETTINGS = load_settings()
P = SETTINGS.paths


def read(path: Path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


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
STATE_LABEL = {
    "baseline": "Baseline",
    "corrupted": "Corrupted",
    "repaired": "Repaired",
}
STATE_COLOR = {"baseline": "#f5b942", "corrupted": "#e5484d", "repaired": "#46a758"}
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

# ---------------------------------------------------------------- styles
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;600&display=swap');

:root {
  --bg: #0b0e13;
  --panel: #12161e;
  --panel-2: #171c26;
  --line: #232b3a;
  --ink: #e8ecf2;
  --muted: #8a94a6;
  --amber: #f5b942;
  --red: #e5484d;
  --green: #46a758;
  --cyan: #4cc2ff;
  --mono: 'IBM Plex Mono', monospace;
}

.stApp { background: var(--bg); }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 2.2rem; padding-bottom: 4rem; max-width: 1400px; }

/* title block */
.vault-head { border-left: 3px solid var(--cyan); padding-left: 18px; margin-bottom: 26px; }
.vault-head .kicker { font-family: var(--mono); font-size: 11px; letter-spacing: 3px; color: var(--cyan); text-transform: uppercase; margin-bottom: 6px; }
.vault-head h1 { font-family: 'Space Grotesk', sans-serif; font-size: 42px; font-weight: 600; color: var(--ink); letter-spacing: -1px; margin: 0; line-height: 1.05; }
.vault-head .sub { font-family: 'IBM Plex Sans', sans-serif; font-size: 14px; color: var(--muted); margin-top: 8px; }

/* state columns */
.state-col { background: var(--panel); border: 1px solid var(--line); border-radius: 10px; padding: 0; overflow: hidden; }
.state-col .head { padding: 14px 16px; border-bottom: 1px solid var(--line); display: flex; align-items: center; justify-content: space-between; }
.state-col .name { font-family: 'Space Grotesk', sans-serif; font-size: 17px; font-weight: 600; color: var(--ink); display: flex; align-items: center; gap: 8px; }
.state-col .dot { width: 9px; height: 9px; border-radius: 50%; display: inline-block; }
.state-col .sub { font-family: 'IBM Plex Sans', sans-serif; font-size: 11.5px; color: var(--muted); padding: 8px 16px; border-bottom: 1px solid var(--line); }
.state-col .body { padding: 14px 16px; }

.metric-block { margin-bottom: 14px; }
.metric-block .m-label { font-family: var(--mono); font-size: 10.5px; letter-spacing: 1.2px; text-transform: uppercase; color: var(--muted); margin-bottom: 4px; display: flex; justify-content: space-between; }
.metric-block .m-bar { height: 7px; background: #0a0d12; border-radius: 4px; overflow: hidden; }
.metric-block .m-fill { height: 100%; border-radius: 4px; transition: width 900ms cubic-bezier(.2,.8,.2,1); }
.metric-block .m-val { font-family: var(--mono); font-size: 13px; color: var(--ink); margin-top: 5px; display: flex; justify-content: space-between; align-items: baseline; }

.delta { font-family: var(--mono); font-size: 11px; padding: 2px 7px; border-radius: 4px; }
.delta.bad { color: var(--red); background: rgba(229,72,77,.12); }
.delta.good { color: var(--green); background: rgba(70,167,88,.12); }
.delta.flat { color: var(--muted); background: rgba(138,148,166,.1); }

.big-stat { font-family: 'Space Grotesk', sans-serif; font-size: 34px; font-weight: 600; line-height: 1; }
.small-stat { font-family: var(--mono); font-size: 11.5px; color: var(--muted); }

.chip-row { display: flex; gap: 6px; margin-top: 10px; }
.chip { font-family: var(--mono); font-size: 10px; padding: 4px 9px; border-radius: 5px; border: 1px solid var(--line); color: var(--muted); }
.chip.ok { color: var(--green); border-color: rgba(70,167,88,.4); }
.chip.fail { color: var(--red); border-color: rgba(229,72,77,.45); }

.section-kicker { font-family: var(--mono); font-size: 10.5px; letter-spacing: 2.5px; text-transform: uppercase; color: var(--muted); margin: 30px 0 12px; display: flex; align-items: center; gap: 10px; }
.section-kicker::after { content: ''; flex: 1; height: 1px; background: var(--line); }

.qa-row { background: var(--panel-2); border: 1px solid var(--line); border-radius: 8px; padding: 12px 14px; margin-bottom: 10px; }
.qa-row .q { font-family: 'IBM Plex Sans', sans-serif; font-size: 13.5px; color: var(--ink); margin-bottom: 6px; }
.qa-row .qa-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.qa-row .cell { font-size: 12px; color: var(--muted); }
.qa-row .cell b { display: block; font-family: var(--mono); font-size: 10px; letter-spacing: 1px; color: var(--muted); margin-bottom: 3px; text-transform: uppercase; }
.qa-row .cell .txt { color: #b9c2d0; font-size: 12px; }
.qa-row .badge { display: inline-block; font-family: var(--mono); font-size: 10px; padding: 2px 8px; border-radius: 4px; margin-top: 6px; }
.qa-row .badge.hit { color: var(--green); background: rgba(70,167,88,.12); }
.qa-row .badge.miss { color: var(--red); background: rgba(229,72,77,.12); }

.corrupt-row { display: flex; justify-content: space-between; align-items: center; padding: 10px 14px; border-left: 2px solid var(--red); background: var(--panel-2); margin-bottom: 8px; border-radius: 0 8px 8px 0; }
.corrupt-row .type { font-family: var(--mono); font-size: 12px; color: var(--ink); }
.corrupt-row .count { font-family: var(--mono); font-size: 12px; color: var(--muted); }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ---------------------------------------------------------------- header
st.markdown(
    f"""
    <div class="vault-head">
      <div class="kicker">Day 10 · Data Pipeline Observatory</div>
      <h1>Ba trạng thái, một luồng dữ liệu</h1>
      <div class="sub">Baseline → Corruption → Repair. Cùng test set đóng băng, cùng evaluator — chỉ dữ liệu thay đổi. Số liệu dưới đây đọc trực tiếp từ artifacts trong <span style="font-family:'IBM Plex Mono';color:var(--cyan)">data/</span>.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------- 3 columns
cols = st.columns(3, gap="small")

for col, state in zip(cols, STATES):
    metrics = METRICS[state]
    quality = QUALITY[state]
    freshness = FRESHNESS[state]
    color = STATE_COLOR[state]

    deltas: dict[str, str] = {}
    if state == "corrupted":
        for key in ("retrieval_hit_rate", "mean_token_f1", "judge_accuracy"):
            d = metrics[key] - METRICS["baseline"][key]
            deltas[key] = f"−{abs(d):.2f}" if d < 0 else f"+{d:.2f}"
    elif state == "repaired":
        for key in ("retrieval_hit_rate", "mean_token_f1", "judge_accuracy"):
            d = metrics[key] - METRICS["corrupted"][key]
            deltas[key] = f"+{d:.2f}" if d > 0 else f"{d:.2f}"

    metric_rows = []
    for key, label in METRIC_LABELS.items():
        value = metrics[key]
        width = min(100.0, (value / 5.0) * 100 if key == "mean_judge_score" else value * 100)
        delta_html = ""
        if key in deltas:
            cls = "good" if state == "repaired" else "bad"
            delta_html = f'<span class="delta {cls}">{deltas[key]}</span>'
        metric_rows.append(
            f"""
            <div class="metric-block">
              <div class="m-label"><span>{label}</span>{delta_html}</div>
              <div class="m-bar"><div class="m-fill" style="width:{width:.1f}%;background:{color}"></div></div>
              <div class="m-val"><span>{value:.3f}</span><span class="small-stat">/ 1.000</span></div>
            </div>
            """
        )
    metric_rows[-1] = metric_rows[-1].replace("/ 1.000", "/ 5")

    quality_pass = quality["passed"]
    freshness_fresh = freshness["is_fresh"]
    chips = (
        f'<span class="chip {"ok" if quality_pass else "fail"}">quality: {"đạt" if quality_pass else "KHÔNG đạt"}</span>'
        f'<span class="chip {"ok" if freshness_fresh else "fail"}">freshness: {"mới" if freshness_fresh else "cũ"}</span>'
        f'<span class="chip">stale {freshness["stale_rows"]}</span>'
    )

    col.markdown(
        f"""
        <div class="state-col">
          <div class="head">
            <span class="name"><span class="dot" style="background:{color};box-shadow:0 0 12px {color}66"></span>{STATE_LABEL[state]}</span>
            <span class="big-stat" style="color:{color}">{quality["row_count"]}</span>
          </div>
          <div class="sub">{STATE_SUBTITLE[state]}</div>
          <div class="body">
            {''.join(metric_rows)}
            <div class="chip-row">{chips}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------- metric delta chart
st.markdown('<div class="section-kicker">Biến động chỉ số · delta theo trạng thái</div>', unsafe_allow_html=True)

chart_cols = st.columns([2, 1])
with chart_cols[0]:
    chart_keys = ("retrieval_hit_rate", "mean_token_f1", "judge_accuracy", "mean_judge_score")
    fig = go.Figure()
    x_positions = [0, 1, 2]
    for key in chart_keys:
        fig.add_trace(
            go.Scatter(
                x=x_positions,
                y=[METRICS[s][key] for s in STATES],
                mode="lines+markers",
                name=METRIC_LABELS[key],
                line=dict(width=2.5),
                marker=dict(size=8),
                hovertemplate="%{y:.3f}<extra></extra>",
            )
        )
    fig.update_layout(
        xaxis=dict(tickvals=x_positions, ticktext=[STATE_LABEL[s] for s in STATES], title=""),
        yaxis=dict(title="Giá trị", gridcolor="#232b3a"),
        plot_bgcolor="#0b0e13",
        paper_bgcolor="#0b0e13",
        font=dict(family="IBM Plex Sans", color="#8a94a6", size=12),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        height=340,
        margin=dict(l=40, r=20, t=10, b=30),
    )
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

with chart_cols[1]:
    st.markdown(
        """
        <div style="background:#12161e;border:1px solid #232b3a;border-radius:10px;padding:16px;height:100%">
          <div class="small-stat" style="margin-bottom:8px">CHÚ THÍCH</div>
          <div style="font-size:12px;color:#b9c2d0;line-height:1.7">
            <b style="color:#f5b942">Baseline</b> — điểm chuẩn tin cậy.<br>
            <b style="color:#e5484d">Corrupted</b> — 6 dạng hư hỏng chủ đích: drop latest, blank summary, noise, truncate title, date cũ, duplicate.<br>
            <b style="color:#46a758">Repaired</b> — tái dựng từ raw snapshot, không sửa tay.
          </div>
          <div class="small-stat" style="margin-top:14px;margin-bottom:6px">SỰ CỐ ĐÃ GHI</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if CORRUPTION_LOG:
        for entry in CORRUPTION_LOG.get("corruptions", []):
            type_label = entry["type"].replace("_", " ").title()
            count = len(entry.get("paper_ids", []))
            st.markdown(
                f'<div class="corrupt-row"><span class="type">{type_label}</span><span class="count">{count} dòng</span></div>',
                unsafe_allow_html=True,
            )

# ---------------------------------------------------------------- answers comparison
st.markdown('<div class="section-kicker">So sánh câu trả lời · cùng câu hỏi, ba trạng thái</div>', unsafe_allow_html=True)

answers_by_id: dict[str, dict[str, dict]] = {}
for state in STATES:
    for answer in ANSWERS[state] or []:
        answers_by_id.setdefault(answer["id"], {})[state] = answer

for question_id, per_state in answers_by_id.items():
    sample = per_state["baseline"]
    type_vi = {
        "authors": "tác giả",
        "summary": "tóm tắt",
        "date": "ngày xuất bản",
        "categories": "danh mục",
    }.get(sample["question_type"], sample["question_type"])
    qa_cols = st.columns(3, gap="small")
    for qa_col, state in zip(qa_cols, STATES):
        answer = per_state.get(state)
        if not answer:
            qa_col.markdown(f'<div class="qa-row"><div class="q">{question_id}</div></div>', unsafe_allow_html=True)
            continue
        hit = answer["retrieval_hit"]
        badge = (
            f'<span class="badge {"hit" if hit else "miss"}">retrieval {"HIT" if hit else "MISS"} · f1 {answer["token_f1"]:.2f}</span>'
        )
        qa_col.markdown(
            f"""
            <div class="qa-row">
              <div class="q">{question_id} · <span style="color:{STATE_COLOR[state]}">{STATE_LABEL[state]}</span> — {type_vi}</div>
              <div class="qa-grid">
                <div class="cell"><b>Ground truth</b><span class="txt">{sample["ground_truth"][:160]}</span></div>
                <div class="cell"><b>Trả lời</b><span class="txt">{answer["answer"][:160]}</span></div>
              </div>
              {badge}
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown(
    '<div style="font-family:IBM Plex Mono;font-size:10px;color:#5b6472;margin-top:30px;border-top:1px solid #232b3a;padding-top:10px">'
    "Số liệu đọc từ data/results · data/quality · data/clean — không tính lại, không bịa. "
    "Judge dùng fallback heuristic khi model free không hỗ trợ structured output.</div>",
    unsafe_allow_html=True,
)
