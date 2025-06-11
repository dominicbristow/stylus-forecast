"""
Streamlit interactive revenue model for Stylus Education
=======================================================
Paste this file into a GitHub repo (e.g. stylus-forecast) and deploy on
https://share.streamlit.io – investors get a live playground with sliders.
"""

import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="Stylus Forecast Model", layout="wide")
st.title("📈 Stylus Education – Interactive Revenue Forecast")

# ────────────────────────────────────────────
# Sidebar – assumption sliders
# ────────────────────────────────────────────

st.sidebar.header("Adjust assumptions")

# UK schools
start_uk = st.sidebar.number_input("Starting UK schools (Q3 ’25)", 10, 1000, 100, step=10)
uk_growth_fast = st.sidebar.slider("Initial ‘hyper-growth’ factor (× over first 2 years)",
                                   1.0, 10.0, 5.0, 0.5)
uk_growth_taper = st.sidebar.slider("Annual growth after taper (-%)",
                                    0.0, 100.0, 20.0, 5.0) / 100

# MATs
trials_q      = st.sidebar.number_input("MAT trials per quarter (after Q4 ’25)", 1, 100, 25)
conv_rate     = st.sidebar.slider("MAT conversion rate", 0.0, 1.0, 0.70, 0.05)
mat_multiplier= st.sidebar.number_input("Average schools per MAT", 5, 25, 10)

# US districts
dist_add_q    = st.sidebar.number_input("US districts per quarter (steady-state)", 1, 50, 15)
dist_start_q  = st.sidebar.selectbox("US launch quarter",
                                     ["2027Q1", "2027Q2", "2027Q3"], index=0)

# EAL market
eal_start_q            = st.sidebar.selectbox("EAL launch quarter",
                                              ["2028Q1", "2028Q2", "2028Q3"], index=0)
eal_start_learners     = st.sidebar.number_input("EAL learners at launch (m)",
                                                 0.1, 10.0, 1.0, 0.1) * 1_000_000
eal_quarterly_multiplier = st.sidebar.slider("EAL learner growth per quarter (×)",
                                             1.0, 4.0, 2.0, 0.25)

# Pricing (annual)
school_price_y1 = st.sidebar.number_input("School price Y1 (£k)", 1, 50, 5)  * 1_000
school_price_y2 = st.sidebar.number_input("School price Y2 (£k)", 1, 50, 10) * 1_000
school_price_y3 = st.sidebar.number_input("School price Y3 (£k)", 1, 50, 15) * 1_000

dist_price_y1   = st.sidebar.number_input("District price Y1 (£k)", 10, 500, 100) * 1_000
dist_price_y2   = st.sidebar.number_input("District price Y2+ (£k)", 10, 500, 150) * 1_000

eal_price_annual = 30  # £ per learner per year

# ────────────────────────────────────────────
# Helper
# ────────────────────────────────────────────

def pad_or_trim(seq, n):
    """Return seq exactly length n (pad with zeros or trim)."""
    return (seq + [0]*n)[:n]

# ────────────────────────────────────────────
# Build forecast
# ────────────────────────────────────────────

periods = pd.period_range("2025Q3", periods=12, freq="Q")
labels  = periods.astype(str)

# UK school count generator
def build_uk_counts():
    counts = []
    half_targets = [start_uk]
    for i in range(1, 6):                      # 5 half-years ahead
        if i <= 4:                             # hyper-growth phase
            target = round(start_uk * (uk_growth_fast ** i))
        else:                                  # taper phase
            target = round(half_targets[-1] * (1 + uk_growth_taper*2))
        half_targets.append(target)
    for h in range(len(half_targets)-1):       # 40/60 split per half-year
        base, nxt = half_targets[h], half_targets[h+1]
        delta     = nxt - base
        counts.extend([base + round(delta*0.4), nxt])
    return counts[:12]

uk_counts = build_uk_counts()

ann_price_map = {
    2025: school_price_y1,
    2026: school_price_y2*0.75 + school_price_y1*0.25,
    2027: school_price_y2,
    2028: school_price_y3,
}
school_price_q = [ann_price_map[p.year]/4 for p in periods]
uk_rev = [c*p for c,p in zip(uk_counts, school_price_q)]

# MATs
trial_schedule = [trials_q*2] + [trials_q]*11      # 72 in first half-year → 36/q
mat_conv = [0]*12
for i in range(2, 12):
    mat_conv[i] = round(trial_schedule[i-2]*conv_rate)
mat_cum = pd.Series(mat_conv).cumsum()
mat_price_q = [ann_price_map[p.year]*mat_multiplier/4 for p in periods]
mat_rev = [c*p for c,p in zip(mat_cum, mat_price_q)]

# US districts
first_dist_idx     = labels.tolist().index(dist_start_q)
dist_adds          = [0]*12
for i in range(first_dist_idx, 12):
    dist_adds[i] = dist_add_q
    if i == first_dist_idx:
        dist_adds[i] = 1                         # launch with 1 district
dist_cum = pd.Series(dist_adds).cumsum()
dist_price_q = [0 if p.year < 2027 else
                (dist_price_y1 if p.year == 2027 else dist_price_y2)/4
                for p in periods]
dist_rev = [c*p for c,p in zip(dist_cum, dist_price_q)]

# EAL learners
first_eal_idx = labels.tolist().index(eal_start_q)
eal_learners  = [0]*12
if first_eal_idx < 12:
    learners = eal_start_learners
    for i in range(first_eal_idx, 12):
        eal_learners[i] = learners
        learners *= eal_quarterly_multiplier
eal_rev = [n*(eal_price_annual/4) for n in eal_learners]

# Safeguard equal lengths
n = len(labels)
uk_rev  = pad_or_trim(uk_rev, n)
mat_rev = pad_or_trim(mat_rev, n)
dist_rev= pad_or_trim(dist_rev, n)
eal_rev = pad_or_trim(eal_rev, n)

forecast = pd.DataFrame({
    "UK Schools":   uk_rev,
    "MATs":         mat_rev,
    "US Districts": dist_rev,
    "EAL":          eal_rev
}, index=labels)
forecast["Total"] = forecast.sum(axis=1)

# ────────────────────────────────────────────
# Display
# ────────────────────────────────────────────

st.subheader("Quarterly Revenue (£)")
st.dataframe(forecast.style.format("{:,.0f}"))

st.subheader("Revenue trajectory")
chart = (
    alt.Chart(forecast.reset_index().melt("index",
                                          var_name="Segment",
                                          value_name="Revenue"))
    .mark_line(point=True)
    .encode(
        x="index:N",
        y=alt.Y("Revenue:Q", title="£ per quarter", stack=None),
        color="Segment:N"
    )
    .properties(width=900, height=400)
)
st.altair_chart(chart, use_container_width=True)

st.caption(
    "Adjust the sliders on the left to explore upside & downside scenarios. "
    "All figures represent recognised revenue per quarter (not ARR)."
)
