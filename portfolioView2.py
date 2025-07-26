# portfolio_view.py
#
# streamlit ‑ draft “Portfolio View” panel
# ------------------------------------------------
#  1.  pip install streamlit pandas numpy
#  2.  streamlit run portfolio_view.py
#  3.  ‑‑ csv file must sit beside this script (or change CSV_PATH)
# ------------------------------------------------

import textwrap
import numpy as np
import pandas as pd
import streamlit as st

CSV_PATH = "dataset.csv"   # <- update if needed
PAGE_TITLE = "Portfolio View"
TRAFFIC = {  # RGB hex
    "green": "#63be7b",
    "yellow": "#ffeb84",
    "red": "#f8696b",
}


# ---------- helpers ---------- #
@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    return pd.read_csv(path)


def wrap_crop(s: str, *, width: int = 34, max_lines: int = 2) -> str:
    if pd.isna(s):
        return ""
    wrapped = textwrap.fill(str(s), width=width)
    lines = wrapped.split("\n")
    if len(lines) > max_lines:
        return " ".join(lines[:max_lines]) + "…"
    return " ".join(lines)


def traffic_colour(val) -> str:
    if pd.isna(val):
        return ""
    try:
        v = float(str(val).rstrip("%"))
    except ValueError:
        return ""
    if v >= 80:
        return f"background-color:{TRAFFIC['green']};color:black"
    if v <= 20:
        return f"background-color:{TRAFFIC['red']};color:white"
    return f"background-color:{TRAFFIC['yellow']};color:black"


# ---------- app ---------- #
st.set_page_config(page_title=PAGE_TITLE, layout="wide")
st.title(PAGE_TITLE)

df = load_data(CSV_PATH)

# pupil picker
pupil = st.selectbox("Pupil Name", sorted(df["Pupil Name"].dropna().unique()))
p_df = df.loc[df["Pupil Name"] == pupil].copy()

# tidy labels for display
for col, w in [("KS2 Standard", 26), ("KS2 Statement", 30), ("Criterion", 34)]:
    p_df[col] = p_df[col].apply(lambda x: wrap_crop(x, width=w))

# pivot core data
pivot = (
    p_df.pivot_table(
        index=["KS2 Standard", "KS2 Statement", "Criterion"],
        columns="Purpose",
        values="Judgement (%)",
        aggfunc="first",
    )
    .astype("string")
    .replace("nan", np.nan)
)

# pivot tool‑tip data (🤖 REASON)
reason = (
    p_df.pivot_table(
        index=["KS2 Standard", "KS2 Statement", "Criterion"],
        columns="Purpose",
        values="🤖 REASON",
        aggfunc="first",
    )
    .fillna("")
)

# map Criterion‑level guidance
guidance_lookup = (
    p_df.drop_duplicates(
        ["KS2 Standard", "KS2 Statement", "Criterion", "criteria guidance"]
    )
    .set_index(["KS2 Standard", "KS2 Statement", "Criterion"])["criteria guidance"]
    .to_dict()
)

# replace index with HTML span that carries guidance tooltip
pivot_reset = pivot.reset_index()
pivot_reset["Criterion"] = pivot_reset.apply(
    lambda r: f'<span title="{guidance_lookup.get((r["KS2 Standard"], r["KS2 Statement"], r["Criterion"]), "")}">{r["Criterion"]}</span>',
    axis=1,
)
pivot_reset.set_index(["KS2 Standard", "KS2 Statement", "Criterion"], inplace=True)
pivot = pivot_reset

# style table
styler = (
    pivot.style.format(na_rep="")
    .applymap(traffic_colour)
    .set_tooltips(reason)   # cell‑level tooltips
)

# show
st.markdown(
    styler.to_html(escape=False), unsafe_allow_html=True
)
