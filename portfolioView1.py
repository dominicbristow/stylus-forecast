"""
portfolio_view.py
Streamlit front‑end for Stylus “Portfolio View” analytics panel
----------------------------------------------------------------
Drop this file (and the CSV) in the same repo, then
    streamlit run portfolio_view.py
"""

import textwrap
import pandas as pd
import streamlit as st

# ─── CONFIG ─────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Portfolio View", layout="wide")
st.title("Portfolio View")

CSV_PATH = "St Bedes - Moderation check - Cropped.csv"  # adjust if you rename

# ─── DATA LOAD ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    # keep only the columns we need for this panel
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
    return df[cols]

df = load_data(CSV_PATH)

# ─── UI – PUPIL FILTER ─────────────────────────────────────────────────────────
pupils = sorted(df["Pupil Name"].dropna().unique())
selected = st.selectbox("Select pupil", pupils, index=0, key="pupil_select")

df_view = df[df["Pupil Name"] == selected].copy()

# ─── PIVOT FOR DISPLAY ─────────────────────────────────────────────────────────
val_col = "Judgement (%)"
pivot_vals = (
    df_view.pivot_table(
        index=["KS2 Standard", "KS2 Statement", "Criterion"],
        columns="Purpose",
        values=val_col,
        aggfunc="mean",
    )
    .round(0)
    .sort_index()
)

# same‑shape frame of reasons for tooltips
pivot_reasons = (
    df_view.pivot_table(
        index=["KS2 Standard", "KS2 Statement", "Criterion"],
        columns="Purpose",
        values="🤖 REASON",
        aggfunc=lambda x: " | ".join(x.astype(str).unique()),
    )
    .reindex(pivot_vals.index)
)

# guidance for the Criterion label tooltip
criterion_guidance = (
    df_view.groupby(["KS2 Standard", "KS2 Statement", "Criterion"])["criteria guidance"]
    .first()
)

# ─── UTILITIES ─────────────────────────────────────────────────────────────────
def colour_scale(v):
    if pd.isna(v):
        return ""
    v = float(v)
    if v >= 80:
        return "background-colour:#4caf50;"   # green
    if v >= 50:
        return "background-colour:#ffeb3b;"   # yellow
    if v <= 20:
        return "background-colour:#f44336;"   # red
    return "background-colour:#ffb74d;"       # amber mid‑range

def wrap(text, width=36, max_lines=2):
    wrapped = textwrap.fill(str(text), width=width)
    lines = wrapped.split("\n")[:max_lines]
    out = "\n".join(lines)
    if len(lines) == max_lines and len(wrapped.split("\n")) > max_lines:
        out += "…"
    return out

# replace deepest index level (“Criterion”) with a wrapped version so it looks neat
new_index = [
    (*idx[:2], wrap(idx[2]))
    for idx in pivot_vals.index.to_list()
]
pivot_vals.index = pd.MultiIndex.from_tuples(
    new_index, names=["KS2 Standard", "KS2 Statement", "Criterion"]
)
# tooltips need original label text, so build mapping:
criterion_tooltips = {
    wrap(k): g for (_, _, k), g in criterion_guidance.items()
}

# ─── STYLING ───────────────────────────────────────────────────────────────────
styler = (
    pivot_vals.style
    .applymap(colour_scale)
    .format("{:.0f}")
    .set_tooltips(pivot_reasons)                    # cell‑level reasons
)

# add row‑label tooltip (pandas doesn’t natively support index tooltips, so
# turn index into a normal column, then hide it visually but keep tooltip)
pivot_display = pivot_vals.reset_index()
pivot_display["Criterion ⓘ"] = pivot_display["Criterion"].map(wrap)
tooltip_df = pivot_reasons.reset_index()
tooltip_df["Criterion ⓘ"] = pivot_display["Criterion"].map(
    lambda w: criterion_tooltips.get(w, "")
)
pivot_display = pivot_display.drop(columns="Criterion").set_index(
    ["KS2 Standard", "KS2 Statement", "Criterion ⓘ"]
)
tooltip_df = tooltip_df.drop(columns="Criterion").set_index(
    ["KS2 Standard", "KS2 Statement", "Criterion ⓘ"]
)
styler = (
    pivot_display.style
    .applymap(colour_scale)
    .format("{:.0f}")
    .set_tooltips(tooltip_df)
)

# ─── RENDER ────────────────────────────────────────────────────────────────────
st.dataframe(styler, use_container_width=True)
