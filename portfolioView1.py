"""
portfolio_view.py  –  Stylus “Portfolio View” (Streamlit)
"""

import textwrap
import pandas as pd
import streamlit as st
from matplotlib.colors import LinearSegmentedColormap

# ── CONFIG ────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Portfolio View", layout="wide")
st.title("Portfolio View")

CSV_PATH = "dataset.csv"   # adjust if renamed

# ── DATA LOAD ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)

    keep = [
        "Pupil Name",
        "Judgement (%)",
        "KS2 Standard",
        "KS2 Statement",
        "Purpose",
        "Criterion",
        "🤖 REASON",
        "criteria guidance",
    ]
    df = df[keep]

    # numeric version for aggregation / colour‑mapping
    df["Judgement_num"] = (
        df["Judgement (%)"].astype(str).str.rstrip("%").replace("", pd.NA).astype(float)
    )
    return df

df = load_data(CSV_PATH)

# ── UI – PUPIL FILTER ─────────────────────────────────────────────────────────
pupils = sorted(df["Pupil Name"].dropna().unique())
pupil = st.selectbox("Select pupil", pupils, 0)
df_view = df[df["Pupil Name"] == pupil].copy()

# ── PIVOT (numeric) ───────────────────────────────────────────────────────────
pivot = (
    df_view.pivot_table(
        index=["KS2 Standard", "KS2 Statement", "Criterion"],
        columns="Purpose",
        values="Judgement_num",
        aggfunc="mean",
    )
    .round(0)
    .sort_index()
)

# reasons (same shape) for tooltips
reasons = (
    df_view.pivot_table(
        index=["KS2 Standard", "KS2 Statement", "Criterion"],
        columns="Purpose",
        values="🤖 REASON",
        aggfunc=lambda x: " | ".join(x.astype(str).unique()),
    )
    .reindex(pivot.index)
)

# criterion‑level guidance
guidance = (
    df_view.groupby(["KS2 Standard", "KS2 Statement", "Criterion"])["criteria guidance"]
    .first()
)

# ── HELPERS ───────────────────────────────────────────────────────────────────
def wrap(text: str, width: int = 28, lines: int = 2) -> str:
    wrapped = textwrap.fill(str(text), width=width)
    bits = wrapped.split("\n")[:lines]
    return "\n".join(bits) + ("…" if len(bits) < len(wrapped.split("\n")) else "")

# wrap every index level for a neater, narrower left column
pivot.index = pd.MultiIndex.from_tuples(
    [
        (wrap(a), wrap(b), wrap(c))
        for a, b, c in pivot.index.to_list()
    ],
    names=["KS2 Standard", "KS2 Statement", "Criterion"],
)

# build row‑label tooltip map
criterion_tooltip_map = {
    wrap(k): v for (_, _, k), v in guidance.items()
}

# convert to DataFrame (so we can attach tooltips on index labels)
pivot_disp = pivot.reset_index()
pivot_disp["Criterion ⓘ"] = pivot_disp["Criterion"]

pivot_disp = (
    pivot_disp.drop(columns="Criterion")
    .set_index(["KS2 Standard", "KS2 Statement", "Criterion ⓘ"])
)

reasons_disp = reasons.reset_index()
reasons_disp["Criterion ⓘ"] = pivot_disp.index.get_level_values("Criterion ⓘ")
reasons_disp = reasons_disp.set_index(
    ["KS2 Standard", "KS2 Statement", "Criterion ⓘ"]
)

# attach row‑label guidance
for lvl in ["Criterion ⓘ"]:
    reasons_disp[lvl] = reasons_disp.index.get_level_values(lvl).map(
        criterion_tooltip_map.get
    )

# ── COLOUR GRADIENT ───────────────────────────────────────────────────────────
traffic = LinearSegmentedColormap.from_list(
    "traffic", ["#f44336", "#ffeb3b", "#4caf50"], N=256
)

styler = (
    pivot_disp.style
    .background_gradient(cmap=traffic, vmin=0, vmax=100)
    .format("{:.0f}%")
    .set_tooltips(reasons_disp)
)

# ── RENDER ────────────────────────────────────────────────────────────────────
st.dataframe(styler, use_container_width=True)
