"""
portfolio_view.py  –  Stylus “Portfolio View” (Streamlit)
Run with:  streamlit run portfolio_view.py
"""

import textwrap
import pandas as pd
import streamlit as st

# ── CONFIG ────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Portfolio View", layout="wide")
st.title("Portfolio View")

CSV_PATH = "dataset.csv"   # change if renamed

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

    df["Judgement_num"] = (
        df["Judgement (%)"].astype(str).str.rstrip("%").replace("", pd.NA).astype(float)
    )
    return df

df = load_data(CSV_PATH)

# ── UI – PUPIL FILTER ─────────────────────────────────────────────────────────
pupils = sorted(df["Pupil Name"].dropna().unique())
pupil = st.selectbox("Select pupil", pupils, 0)
view = df[df["Pupil Name"] == pupil].copy()

# ── PIVOT TABLE ───────────────────────────────────────────────────────────────
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
def wrap(text: str, width: int = 24, lines: int = 2) -> str:
    """Wrap to width, crop after `lines` lines with an ellipsis."""
    wrapped = textwrap.fill(str(text), width=width)
    bits = wrapped.split("\n")[:lines]
    return "\n".join(bits) + ("…" if len(bits) < len(wrapped.split("\n")) else "")

def gradient_colour(v: float) -> str:
    """Red→Yellow→Green gradient for 0‑100."""
    if pd.isna(v):
        return ""
    v = max(0, min(100, float(v)))
    if v <= 50:            # red (0) → yellow (50)
        f = v / 50
        r, g, b = int(244 + (255 - 244) * f), int(67 + (235 - 67) * f), int(54 + (59 - 54) * f)
    else:                  # yellow (50) → green (100)
        f = (v - 50) / 50
        r, g, b = int(255 + (76 - 255) * f), int(235 + (175 - 235) * f), int(59 + (80 - 59) * f)
    return f"background-color:#{r:02x}{g:02x}{b:02x};"

# wrap index labels for a narrower left column
pivot.index = pd.MultiIndex.from_tuples(
    [(wrap(a), wrap(b), wrap(c)) for a, b, c in pivot.index],
    names=["KS2 Standard", "KS2 Statement", "Criterion"],
)

# tooltips for criterion guidance
crit_tooltip_map = {wrap(k): v for (_, _, k), v in guidance.items()}

# convert for styling
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

for lvl in ["Criterion ⓘ"]:
    reasons_disp[lvl] = reasons_disp.index.get_level_values(lvl).map(
        crit_tooltip_map.get
    )

# ── STYLING ───────────────────────────────────────────────────────────────────
styler = (
    pivot_disp.style
    .applymap(gradient_colour)
    .format("{:.0f}%")
    .set_table_styles(
        {"": {"selector": "th.row_heading", "props": "max-width: 200px; white-space: pre-wrap;"}}
    )
    .set_tooltips(reasons_disp)
)

# ── RENDER ────────────────────────────────────────────────────────────────────
st.dataframe(styler, use_container_width=True)
