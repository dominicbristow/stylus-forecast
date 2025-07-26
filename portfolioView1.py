"""
portfolio_view.py — Stylus “Portfolio View” panel
Run with:  streamlit run portfolio_view.py
No extra libraries needed.
"""

import textwrap
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# ── CONFIG ────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Portfolio View", layout="wide")
st.title("Portfolio View")

DATA_PATH = "dataset.csv"      # rename if needed

# ── LOAD & PREP ───────────────────────────────────────────────────────────────
@st.cache_data
def load_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str)
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
    df["Judgement_num"] = (
        df["Judgement (%)"].str.rstrip("%").replace("", pd.NA).astype(float)
    )
    return df

df = load_csv(DATA_PATH)

# ── UI ────────────────────────────────────────────────────────────────────────
pupil = st.selectbox("Select pupil", sorted(df["Pupil Name"].dropna().unique()))
view  = df[df["Pupil Name"] == pupil].copy()

# ── PIVOT (numeric) ───────────────────────────────────────────────────────────
pivot = (
    view.pivot_table(
        index=["KS2 Standard", "KS2 Statement", "Criterion"],
        columns="Purpose",
        values="Judgement_num",
        aggfunc="mean",
    )
    .round(0)
    .sort_index()
)

# identical‑shape frame of reasons
reasons = view.pivot_table(
    index=["KS2 Standard", "KS2 Statement", "Criterion"],
    columns="Purpose",
    values="🤖 REASON",
    aggfunc=lambda s: " | ".join(s.unique()),
).reindex(pivot.index)

# guidance for each Criterion (for the row‑label tooltip)
guidance = (
    view.groupby(["KS2 Standard", "KS2 Statement", "Criterion"])["criteria guidance"]
    .first()
)

# ── SMALL HELPERS ─────────────────────────────────────────────────────────────
def wrap(txt: str, width: int = 28, lines: int = 2) -> str:
    """Wrap & crop, but keep the full text as a tooltip via <span title="">."""
    if pd.isna(txt):
        return ""
    wrapped = textwrap.fill(txt, width=width)
    out_lines = wrapped.split("\n")[:lines]
    display  = "\n".join(out_lines)
    if len(out_lines) < len(wrapped.split("\n")):
        display += "…"
    # embed HTML so the full text shows on hover
    return f'<span title="{txt}">{display}</span>'

def colour(v: float) -> str:
    """Red→Yellow→Green smooth gradient for 0‑100."""
    if pd.isna(v):
        return ""
    v = max(0, min(100, v))
    if v <= 50:              # red‑>yellow
        f = v / 50
        r, g, b = 244 + (11 * f), 67 + (168 * f), 54 + (5 * f)
    else:                    # yellow‑>green
        f = (v - 50) / 50
        r, g, b = 255 + (-179 * f), 235 + (-60 * f), 59 + (21 * f)
    return f"background-color:#{int(r):02x}{int(g):02x}{int(b):02x};"

# ── BUILD DISPLAY FRAME ───────────────────────────────────────────────────────
# 1) make prettier index with inline tooltips
pivot.index = pd.MultiIndex.from_tuples(
    [
        (wrap(a), wrap(b), wrap(c))   # full text preserved in title attr
        for a, b, c in pivot.index
    ],
    names=["KS2 Standard", "KS2 Statement", "Criterion"]
)

# 2) collapse index into columns so Styler can attach tooltips easily
disp = pivot.reset_index()
disp["Criterion ⓘ"] = disp["Criterion"]          # show criterion as a column
disp = disp.drop(columns="Criterion").set_index(
    ["KS2 Standard", "KS2 Statement", "Criterion ⓘ"]
)

reas = reasons.reset_index()
reas["Criterion ⓘ"] = disp.index.get_level_values("Criterion ⓘ")
reas = reas.set_index(
    ["KS2 Standard", "KS2 Statement", "Criterion ⓘ"]
)

# attach criterion‑level guidance tooltip to the index column itself
reas["Criterion ⓘ"] = reas.index.get_level_values("Criterion ⓘ").map(
    lambda x: guidance.get(x.strip("<span title=\"").split("\">")[0], "")
)

# ── STYLE ─────────────────────────────────────────────────────────────────────
styler = (
    disp.style
    .applymap(colour)
    .format("{:.0f}%")
    .set_tooltips(reas)            # cell reasons + row‑label guidance
    .set_table_styles([            # keep left margin narrow & wrapped
        {"selector":"th",
         "props":[("max-width","180px"),("white-space","pre-wrap")]}
    ])
    .hide(axis="index", level=0)   # hide top‑level index header row
    .format(escape=False)          # allow our inline HTML tooltips
)

# ── RENDER ────────────────────────────────────────────────────────────────────
html = styler.to_html()
components.html(html, height=600, scrolling=True)
