"""
portfolio_view.py  ▸ Streamlit panel: “Portfolio View”
"""

import textwrap
import pandas as pd
import streamlit as st

# ── CONFIG ────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Portfolio View", layout="wide")
st.title("Portfolio View")

CSV_PATH = "dataset.csv"  # adjust if renamed

# ── DATA LOAD ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)

    # keep only the columns we need
    cols = [
        "Pupil Name",
        "Judgement (%)",
        "KS2 Standard",
        "KS2 Statement",
        "Purpose",
        "Criterion",
        "🤖 REASON",
        "criteria guidance",
    ]
    df = df[cols]

    # make a numeric copy for aggregation
    df["Judgement_num"] = (
        df["Judgement (%)"].astype(str).str.rstrip("%").replace("", pd.NA).astype(float)
    )

    return df

df = load_data(CSV_PATH)

# ── PUPIL FILTER ──────────────────────────────────────────────────────────────
pupils = sorted(df["Pupil Name"].dropna().unique())
selected = st.selectbox("Select pupil", pupils, index=0, key="pupil_select")
df_view = df[df["Pupil Name"] == selected].copy()

# ── PIVOT TABLE (numeric) ─────────────────────────────────────────────────────
pivot_vals = (
    df_view.pivot_table(
        index=["KS2 Standard", "KS2 Statement", "Criterion"],
        columns="Purpose",
        values="Judgement_num",
        aggfunc="mean",
    )
    .round(0)
    .sort_index()
)

# same‑shape frame of “reasons” for tooltips
pivot_reasons = df_view.pivot_table(
    index=["KS2 Standard", "KS2 Statement", "Criterion"],
    columns="Purpose",
    values="🤖 REASON",
    aggfunc=lambda x: " | ".join(x.astype(str).unique()),
).reindex(pivot_vals.index)

# guidance per Criterion
criterion_guidance = (
    df_view.groupby(["KS2 Standard", "KS2 Statement", "Criterion"])["criteria guidance"]
    .first()
)

# ── UTILITIES ─────────────────────────────────────────────────────────────────
def colour_scale(v: float):
    if pd.isna(v):
        return ""
    if v >= 80:
        return "background-color:#4caf50;"
    if v >= 50:
        return "background-color:#ffeb3b;"
    if v <= 20:
        return "background-color:#f44336;"
    return "background-color:#ffb74d;"

def wrap(text, width=36, max_lines=2):
    wrapped = textwrap.fill(str(text), width=width)
    lines = wrapped.split("\n")[:max_lines]
    out = "\n".join(lines)
    if len(lines) == max_lines and len(wrapped.split("\n")) > max_lines:
        out += "…"
    return out

# tidy up deepest index level for display
new_index = [
    (*idx[:2], wrap(idx[2]))  # idx = (KS2 Standard, KS2 Statement, Criterion)
    for idx in pivot_vals.index.to_list()
]
pivot_vals.index = pd.MultiIndex.from_tuples(
    new_index, names=["KS2 Standard", "KS2 Statement", "Criterion"]
)

# map wrapped criterion → guidance for tooltip
criterion_tooltips = {wrap(k): g for (_, _, k), g in criterion_guidance.items()}

# ── STYLE & TOOLTIP SET‑UP ────────────────────────────────────────────────────
pivot_display = pivot_vals.reset_index()
pivot_display["Criterion ⓘ"] = pivot_display["Criterion"]
pivot_display = pivot_display.drop(columns="Criterion").set_index(
    ["KS2 Standard", "KS2 Statement", "Criterion ⓘ"]
)

tooltip_df = pivot_reasons.reset_index()
tooltip_df["Criterion ⓘ"] = pivot_display.index.get_level_values("Criterion ⓘ")
tooltip_df = tooltip_df.set_index(
    ["KS2 Standard", "KS2 Statement", "Criterion ⓘ"]
)

# add row‑label tooltips
for lvl in ["Criterion ⓘ"]:
    tooltip_df[lvl] = tooltip_df.index.get_level_values(lvl).map(
        lambda w: criterion_tooltips.get(w, "")
    )

styler = (
    pivot_display.style
    .applymap(colour_scale)
    .format("{:.0f}%")
    .set_tooltips(tooltip_df)
)

# ── RENDER ────────────────────────────────────────────────────────────────────
st.dataframe(styler, use_container_width=True)
