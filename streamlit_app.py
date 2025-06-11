"""
Streamlit interactive revenue + cash-flow model for Stylus Education
===================================================================
Copy this file into a GitHub repo (e.g. stylus-forecast) and deploy on
https://share.streamlit.io – investors get a live playground with sliders.
"""

import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="Stylus Forecast Model", layout="wide")

# ────────────────────────────────────────────
# Navigation
# ────────────────────────────────────────────
page = st.sidebar.radio("Choose view", ["Revenue", "Cash-flow"], index=0)

# ────────────────────────────────────────────
# Assumption sliders (shared by both pages)
# ────────────────────────────────────────────
st.sidebar.header("Adjust assumptions")

## UK schools
start_uk        = st.sidebar.number_input("Starting UK schools (Q3 ’25)", 10, 1000, 100, step=10)
uk_growth_fast  = st.sidebar.slider("Hyper-growth factor (× over first 2 yrs)", 1.0, 10.0, 5.0, 0.5)
uk_growth_taper = st.sidebar.slider("Annual growth after taper (-%)", 0.0, 100.0, 20.0, 5.0) / 100

## MATs
trials_q       = st.sidebar.number_input("MAT trials / quarter (after Q4 ’25)", 1, 100, 25)
conv_rate      = st.sidebar.slider("MAT conversion rate", 0.0, 1.0, 0.70, 0.05)
mat_multiplier = st.sidebar.number_input("Schools per MAT (avg)", 5, 25, 10)

## US districts
dist_add_q   = st.sidebar.number_input("US districts added / quarter", 1, 50, 15)
dist_start_q = st.sidebar.selectbox("US launch quarter", ["2027Q1", "2027Q2", "2027Q3"], index=0)

## EAL market
eal_start_q            = st.sidebar.selectbox("EAL launch quarter", ["2028Q1", "2028Q2", "2028Q3"], index=0)
eal_start_learners     = st.sidebar.number_input("EAL learners at launch (m)", 0.1, 10.0, 1.0, 0.1) * 1_000_000
eal_quarterly_mult     = st.sidebar.slider("EAL learner growth / quarter (×)", 1.0, 4.0, 2.0, 0.25)

## Pricing (annual)
school_price_y1 = st.sidebar.number_input("School price Y1 (£k)", 1, 50, 5) * 1_000
school_price_y2 = st.sidebar.number_input("School price Y2 (£k)", 1, 50, 10) * 1_000
school_price_y3 = st.sidebar.number_input("School price Y3 (£k)", 1, 50, 15) * 1_000

dist_price_y1   = st.sidebar.number_input("District price Y1 (£k)", 10, 500, 100) * 1_000
dist_price_y2   = st.sidebar.number_input("District price Y2+ (£k)", 10, 500, 150) * 1_000

eal_price_annual = 30  # £/learner/year

# ────────────────────────────────────────────
# Helper
# ────────────────────────────────────────────
def pad_or_trim(seq, n):
    """Return list exactly length n."""
    return (seq + [0] * n)[:n]

# ────────────────────────────────────────────
# Build 3-year forecast (14 quarters: 2025Q3-2028Q4)
# ────────────────────────────────────────────
periods = pd.period_range("2025Q3", periods=14, freq="Q")
labels  = periods.astype(str)

### UK SCHOOL COUNTS ###
def build_uk_counts():
    counts, half_targets = [], [start_uk]
    while len(counts) < 14:
        i = len(half_targets)
        if i <= 4:  # hyper-growth half-years
            target = round(start_uk * (uk_growth_fast ** i))
        else:       # taper half-years
            target = round(half_targets[-1] * (1 + uk_growth_taper * 2))
        half_targets.append(target)
        base, nxt = half_targets[-2], half_targets[-1]
        delta = nxt - base
        counts.extend([base + round(delta * 0.4), nxt])  # 40 / 60 split
    return counts[:14]

uk_counts = build_uk_counts()

### Quarterly pricing maps ###
ann_price_map = {
    2025: school_price_y1,
    2026: school_price_y2 * 0.75 + school_price_y1 * 0.25,
    2027: school_price_y2,
    2028: school_price_y3,
}
school_price_q = [ann_price_map.get(p.year, school_price_y3) / 4 for p in periods]
uk_rev = [c * p for c, p in zip(uk_counts, school_price_q)]

### MATs ###
trial_schedule = [trials_q * 2] + [trials_q] * 13  # first half-year trial = 72 → 36/q
mat_conv = [0] * 14
for i in range(2, 14):
    mat_conv[i] = round(trial_schedule[i - 2] * conv_rate)
mat_cum = pd.Series(mat_conv).cumsum()
mat_price_q = [ann_price_map.get(p.year, school_price_y3) * mat_multiplier / 4 for p in periods]
mat_rev = [c * p for c, p in zip(mat_cum, mat_price_q)]

### US districts ###
first_dist_idx = labels.tolist().index(dist_start_q)
dist_adds = [0] * 14
for i in range(first_dist_idx, 14):
    dist_adds[i] = dist_add_q
    if i == first_dist_idx:
        dist_adds[i] = 1
dist_cum = pd.Series(dist_adds).cumsum()
def dist_price(p):
    if p.year < 2027:
        return 0
    return ((dist_price_y1 if p.year == 2027 else dist_price_y2) / 4)
dist_price_q = [dist_price(p) for p in periods]
dist_rev = [c * p for c, p in zip(dist_cum, dist_price_q)]

### EAL ###
first_eal_idx = labels.tolist().index(eal_start_q)
eal_learners = [0] * 14
if first_eal_idx < 14:
    learners = eal_start_learners
    for i in range(first_eal_idx, 14):
        eal_learners[i] = learners
        learners *= eal_quarterly_mult
eal_rev = [n * (eal_price_annual / 4) for n in eal_learners]

### Assemble revenue DF ###
revenue_df = pd.DataFrame({
    "UK Schools":   pad_or_trim(uk_rev, 14),
    "MATs":         pad_or_trim(mat_rev, 14),
    "US Districts": pad_or_trim(dist_rev, 14),
    "EAL":          pad_or_trim(eal_rev, 14),
}, index=labels)
revenue_df["Total"] = revenue_df.sum(axis=1)

# ────────────────────────────────────────────
# Cash-flow model
# ────────────────────────────────────────────
if page == "Cash-flow":
    ## Payroll (3 existing FT + 4 hires in 2025Q4) ##
    salaries_ft       = [100_000, 100_000, 90_000, 90_000, 90_000, 75_000, 75_000]  # 7 FT after hire
    salaries_contract = [90_000, 60_000]
    salaries_pt       = [60_000, 50_000, 45_000, 45_000]

    on_cost       = 0.15
    ft_cost       = sum(salaries_ft)       * (1 + on_cost)
    pt_cost       = sum(salaries_pt)       * (1 + on_cost)
    contract_cost = sum(salaries_contract)                       # assume inclusive

    annual_payroll = ft_cost + pt_cost + contract_cost
    payroll_q      = annual_payroll / 4

    ## Overheads ##
    office_rent_q  = 5_000 * 3  # £5k / m
    other_opex_base_q = 10_000 * 3

    other_opex_q = []
    for p in periods:
        if p.year == 2025:
            other_opex_q.append(other_opex_base_q)
        elif p.year == 2026:
            other_opex_q.append(other_opex_base_q * 1.05)
        else:
            other_opex_q.append(other_opex_base_q * 1.10)  # compounding (simple)

    ## COGS ##
    cogs_pct = [0.25 if p.year == 2025 else 0.20 if p.year == 2026 else 0.15 for p in periods]
    cogs = revenue_df["Total"] * cogs_pct

    ## Cash-flow table ##
    cash_df = pd.DataFrame({
        "Revenue":          revenue_df["Total"],
        "COGS":             cogs,
        "Gross Profit":     revenue_df["Total"] - cogs,
        "Payroll":          payroll_q,
        "Office":           office_rent_q,
        "Other OpEx":       other_opex_q,
    }, index=labels)
    cash_df["Operating Cash"] = (
        cash_df["Gross Profit"] -
        cash_df["Payroll"] -
        cash_df["Office"] -
        cash_df["Other OpEx"]
    )
    cash_df["Cum Cash"] = cash_df["Operating Cash"].cumsum()

# ────────────────────────────────────────────
# DISPLAY
# ────────────────────────────────────────────
st.title("📈 Stylus Education – Interactive Revenue & Cash-flow Forecast")

if page == "Revenue":
    st.subheader("Quarterly Revenue (£)")
    st.dataframe(revenue_df.style.format("{:,.0f}"))

    st.subheader("Revenue trajectory")
    chart = (
        alt.Chart(revenue_df.reset_index().melt("index",
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

else:  # Cash-flow view
    st.subheader("Quarterly Cash-flow (£)")
    st.dataframe(cash_df.style.format("{:,.0f}"))

    st.subheader("Cumulative Cash position")
    cash_chart = (
        alt.Chart(cash_df.reset_index())
        .mark_area(opacity=0.6)
        .encode(
            x="index:N",
            y=alt.Y("Cum Cash:Q", title="£ cumulative"),
        )
        .properties(width=900, height=350)
    )
    st.altair_chart(cash_chart, use_container_width=True)

st.caption(
    "Use the sliders to explore revenue growth, costs and cash burn. "
    "All figures are recognised amounts per quarter."
)
