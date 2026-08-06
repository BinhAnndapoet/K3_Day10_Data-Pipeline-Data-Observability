"""Dữ liệu — browse artifacts: raw, clean, corrupted, repaired, embeddings."""

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
    SETTINGS,
    page_header,
    read,
    rule,
)

st.set_page_config(page_title="Dữ liệu · Pipeline Ledger", page_icon="▤", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)

P = SETTINGS.paths

page_header(
    "Kho dữ liệu",
    "Artifacts trong data/ — nhìn thật, không tóm tắt",
    '<span class="no">03</span>trạng thái · 6 thư mục',
    "Mỗi bảng dưới đây đọc nguyên file artifact trên đĩa. Dùng để kiểm tra chéo giữa "
    "con số hiển thị và dữ liệu gốc.",
)

DATASETS = [
    ("Raw records (Crossref)", P.raw_records_json, "raw"),
    ("Clean — baseline", P.clean_json, "clean"),
    ("Clean — corrupted", P.corrupted_clean_json, "clean"),
    ("Clean — repaired", P.repaired_clean_json, "clean"),
    ("Answers — baseline", P.baseline_answers, "answers"),
    ("Answers — corrupted", P.corrupted_answers, "answers"),
    ("Answers — repaired", P.repaired_answers, "answers"),
]

for label, path, kind in DATASETS:
    payload = read(path)
    rule(label)
    if not payload:
        st.markdown(f'<div class="ledger-note">Không tìm thấy {path}.</div>', unsafe_allow_html=True)
        continue
    if kind == "raw":
        df = pd.json_normalize(payload)
        st.dataframe(df, use_container_width=True, height=300)
    elif kind == "clean":
        df = pd.DataFrame(payload)
        cols = [c for c in ["paper_id", "title", "published", "age_days", "authors_joined", "categories_joined", "summary_chars"] if c in df.columns]
        st.dataframe(df[cols], use_container_width=True, height=300)
        with st.expander("toàn bộ cột"):
            st.dataframe(df, use_container_width=True, height=400)
    else:
        df = pd.json_normalize(payload)
        cols = [c for c in ["id", "question_type", "retrieval_hit", "token_f1", "judge.correct", "judge.score"] if c in df.columns]
        st.dataframe(df[cols], use_container_width=True, height=300)
        with st.expander("toàn bộ cột"):
            st.dataframe(df, use_container_width=True, height=400)

rule("Embedding manifest")

for label, path in [
    ("Baseline embeddings", P.embeddings_json),
    ("Corrupted embeddings", P.corrupted_embeddings_json),
    ("Repaired embeddings", P.repaired_embeddings_json),
]:
    payload = read(path)
    if not payload:
        continue
    st.markdown(
        f'<div class="corrupt-entry" style="border-left-color:#0f62fe"><span class="ct">{label}</span>'
        f'<span class="cn">collection: {payload.get("collection_name", "n/a")} · {len(payload.get("documents", []))} docs · {payload.get("embedding_model", "n/a")}</span></div>',
        unsafe_allow_html=True,
    )

st.markdown(
    '<div class="foot">Dữ liệu trên đĩa là nguồn chân lý duy nhất — UI chỉ phản chiếu, không thay thế.</div>',
    unsafe_allow_html=True,
)
