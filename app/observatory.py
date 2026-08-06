"""Pipeline Ledger — Streamlit multi-page app.

Entry point. Pages under app/pages/:
  1. 🔍 Tổng quan   — 3 trạng thái song song + delta chart
  2. ⚙️ Baseline    — phase 1 chi tiết
  3. 🩹 Corruption  — 6 loại hư hỏng + tác động
  4. 📊 So sánh     — baseline / corrupted / repaired + bảng delta
  5. 🗄️ Dữ liệu     — browse artifacts trong data/

Chạy:  streamlit run app/observatory.py
"""

from __future__ import annotations

import streamlit as st

st.set_page_config(page_title="Pipeline Ledger", page_icon="▤", layout="wide")

st.markdown(
    """
    <style>
    .stApp { background: #faf8f4; }
    #MainMenu, footer, header { visibility: hidden; }
    .block-container { padding-top: 4rem; max-width: 760px; }
    @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=IBM+Plex+Sans:wght@400;500&family=IBM+Plex+Mono:wght@400;600&display=swap');
    .landing { border-bottom: 2px solid #17181a; padding-bottom: 18px; margin-bottom: 24px; }
    .landing .kicker { font-family: 'IBM Plex Mono', monospace; font-size: 11px; letter-spacing: 2.5px; text-transform: uppercase; color: #0f62fe; margin-bottom: 8px; }
    .landing h1 { font-family: 'Fraunces', Georgia, serif; font-size: 46px; font-weight: 600; color: #17181a; margin: 0; line-height: 1.04; }
    .landing .sub { font-family: 'IBM Plex Sans', sans-serif; font-size: 13.5px; color: #4a4f57; margin-top: 10px; line-height: 1.55; }
    .menu { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 18px; }
    .menu .item { background: #ffffff; border: 1px solid #e2ddd4; border-radius: 2px; padding: 16px 18px; font-family: 'IBM Plex Sans', sans-serif; }
    .menu .item .n { font-family: 'IBM Plex Mono', monospace; font-size: 10px; color: #8b909a; letter-spacing: 1.5px; }
    .menu .item .t { font-family: 'Fraunces', serif; font-size: 17px; font-weight: 600; color: #17181a; margin: 4px 0 3px; }
    .menu .item .d { font-size: 12px; color: #4a4f57; line-height: 1.5; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="landing">
      <div class="kicker">Day 10 · Data Pipeline &amp; Observability</div>
      <h1>Pipeline Ledger</h1>
      <div class="sub">
        Ba trạng thái của một luồng dữ liệu — <b>baseline</b>, <b>corrupted</b>, <b>repaired</b> —
        đo bằng cùng test set đóng băng, trình bày như sổ cái khảo sát.
        Chọn trang từ menu bên trái.
      </div>
    </div>
    <div class="menu">
      <div class="item"><div class="n">PAGE 01</div><div class="t">Tổng quan</div><div class="d">3 trạng thái song song, delta chart, sự cố đã ghi.</div></div>
      <div class="item"><div class="n">PAGE 02</div><div class="t">Baseline</div><div class="d">Phase 1 chi tiết: nguồn, clean, quality, freshness, answers.</div></div>
      <div class="item"><div class="n">PAGE 03</div><div class="t">Corruption</div><div class="d">6 loại hư hỏng, nhật ký chi tiết, tác động lên metric.</div></div>
      <div class="item"><div class="n">PAGE 04</div><div class="t">So sánh</div><div class="d">Bảng delta, biểu đồ phục hồi, answers 3 trạng thái.</div></div>
      <div class="item"><div class="n">PAGE 05</div><div class="t">Dữ liệu</div><div class="d">Browse artifact thật trong data/ — raw, clean, answers, embeddings.</div></div>
    </div>
    """,
    unsafe_allow_html=True,
)
