"""
portfolio_view.py  –  Stylus “Portfolio View” (Streamlit)
Run:  streamlit run portfolio_view.py
"""

import textwrap
import pandas as pd
import streamlit as st

# ── CONFIG ────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Portfolio View", layout="wide")
st.title("Portfolio View")

CSV_PATH = "dataset.csv"   # update if renamed

# ── DATA LOAD ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str)                      # read everything as str
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
        df["Judgement (%)"]
        .str.rstrip("%")
        .replace("", pd.NA)
        .astype(float)
    )
    return df

df = load_data(CSV_PATH)

# ── UI – PUPIL FILTER ─────────────────────────────────────────────────────────
pupil = st.selectbox("Select pupil", sorted(df["Pupil Name"].dropna().unique()))
view  = df.loc[df["Pupil Name"] == pupil].copy()

# ── PIVOT ─────────────────────────────────────────────────────────────────────
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

reasons = (
    view.pivot_table(
        index=["KS2 Standard", "KS2 Statement", "Criterion"],
        columns="Purpose",
        values="🤖 REASON",
        aggfunc=lambda x: " | ".join(x.astype(str).unique()),
    )
    .reindex(pivot.index)
)

guidance = (
    view.groupby(["KS2 Standard", "KS2 Statement", "Criterion"])["criteria guidance"]
    .first()
)

# ── HELPERS ───────────────────────────────────────────────────────────────────
def wrap(txt: str, width: int = 24, lines: int = 2) -> str:
    wrapped = textwrap.fill(str(txt), width=width)
    bits    = wrapped.split("\n")[:lines]
    return "\n".join(bits) + ("…" if len(bits) < len(wrapped.split("\n")) else "")

def gradient(v: float) -> str:
    if pd.isna(v):
        return ""
    v = max(0, min(100, float(v)))              # clamp 0‑100
    if v <= 50:                                 # red → yellow
        f = v / 50
        r = int(244 + (255 - 244) * f)
        g = int(67  + (235 - 67)  * f)
        b = int(54  + (59  - 54)  * f)
    else:                                       # yellow → green
        f = (v - 50) / 50
        r = int(255 + (76  - 255) * f)
        g = int(235 + (175 - 235) * f)
        b = int(59  + (80  - 59)  * f)
    return f"background-color:#{r:02x}{g:02x}{b:02x};"

# tidy index
pivot.index = pd.MultiIndex.from_tuples(
    [(wrap(a), wrap(b), wrap(c)) for a, b, c in pivot.index],
    names=["KS2 Standard", "KS2 Statement", "Criterion"],
)

crit_tooltip = {wrap(k): v for (_, _, k), v in guidance.items()}

# convert for styler
disp = pivot.reset_index()
disp["Criterion ⓘ"] = disp["Criterion"]
disp = disp.drop(columns="Criterion").set_index(
    ["KS2 Standard", "KS2 Statement", "Criterion ⓘ"]
)

reas = reasons.reset_index()
reas["Criterion ⓘ"] = disp.index.get_level_values("Criterion ⓘ")
reas = reas.set_index(
    ["KS2 Standard", "KS2 Statement", "Criterion ⓘ"]
)
reas["Criterion ⓘ"] = reas.index.get_level_values("Criterion ⓘ").map(
    crit_tooltip.get
)

# ── STYLE & RENDER ────────────────────────────────────────────────────────────
styler = (
    disp.style
    .applymap(gradient)
    .format("{:.0f}%")
    .set_tooltips(reas)
)

st.dataframe(styler, use_container_width=True)
