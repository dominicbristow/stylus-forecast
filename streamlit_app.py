"""
streamlit_app.py
Stylus Education – interactive revenue & cash-flow model
"""

import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="Stylus Forecast Model", layout="wide")

# ─────── NAV ───────
page = st.sidebar.radio("Choose view", ["Revenue", "Cash-flow"], index=0)

# ─────── REVENUE INPUTS ───────
if page == "Revenue":
    st.sidebar.header("Growth assumptions")

else:  # page == Cash-flow
    with st.sidebar.expander("Growth assumptions", expanded=False):
        st.markdown("*Revenue drivers live here – tweak if you fancy*")

# shared revenue sliders (appear in Revenue; hidden in expander on Cash-flow)
with (st.sidebar if page == "Revenue" else st.sidebar.expander("Revenue knobs", expanded=False)):
    # UK
    start_uk        = st.number_input("Starting UK schools (Q3 ’25)", 1, 2_000, 25)
    uk_growth_fast  = st.slider("Hyper-growth factor (× over first 2 yrs)", 1.0, 10.0, 3.0, .5)
    uk_growth_taper = st.slider("Annual growth after taper (-%)", 0, 100, 20, 5) / 100

    # MATs
    trials_q       = st.number_input("MAT trials each quarter", 1, 100, 20)
    conv_rate      = st.slider("MAT conversion rate", 0.0, 1.0, .70, .05)
    mat_multiplier = st.number_input("Schools per MAT", 1, 30, 10)

    # US
    dist_start_q   = st.selectbox("US launch quarter", ["2027Q1", "2027Q2", "2027Q3"], 0)
    dist_add_q     = st.number_input("US districts added / quarter", 1, 50, 15)

    # EAL
    eal_start_q        = st.selectbox("EAL launch quarter", ["2028Q1", "2028Q2", "2028Q3"], 0)
    eal_start_learners = st.number_input("EAL learners at launch (m)", .1, 20.0, 1.0, .1) * 1_000_000
    eal_q_mult         = st.slider("EAL learner growth each quarter (×)", 1.0, 4.0, 2.0, .25)

    # Pricing (annual)
    school_price_y1 = st.number_input("School price Y1 (£k)", 1, 50, 5) * 1_000
    school_price_y2 = st.number_input("School price Y2 (£k)", 1, 50, 10) * 1_000
    school_price_y3 = st.number_input("School price Y3+ (£k)", 1, 50, 15) * 1_000
    dist_price_y1   = st.number_input("District price Y1 (£k)", 10, 500, 100) * 1_000
    dist_price_y2   = st.number_input("District price Y2+ (£k)", 10, 500, 150) * 1_000
    eal_price_yr    = 30  # fixed

# ─────── COST INPUTS ───────
if page == "Cash-flow":
    st.sidebar.header("Cost levers")

    hires_per_q   = st.slider("New FT hires / quarter (from 2026Q1)", 0, 10, 2)
    salary_new    = st.number_input("Avg salary new hire (£k)", 40, 200, 80) * 1_000
    salary_infl   = st.slider("Salary inflation / year (%)", 0, 20, 4) / 100

    sm_pct_rev    = st.slider("Sales & marketing (% of revenue)", 0, 100, 12) / 100

    office_rent_m = st.number_input("Office rent (£k / m)", 1, 100, 5) * 1_000
    other_opex_m  = st.number_input("Other OpEx base (£k / m)", 1, 200, 10) * 1_000
    opex_inf      = st.slider("OpEx inflation / year (%)", 0, 20, 5) / 100
    rnd_q         = st.number_input("R&D spend / quarter (£k)", 0, 1_000, 150) * 1_000

    cogs_y1 = st.slider("COGS % Year 1", 0, 100, 25) / 100
    cogs_y2 = st.slider("COGS % Year 2", 0, 100, 20) / 100
    cogs_y3 = st.slider("COGS % Year 3+", 0, 100, 15) / 100

    us_launch_cost  = st.number_input("US launch one-off (£k)", 0, 5_000, 500) * 1_000
    eal_launch_cost = st.number_input("EAL launch one-off (£k)", 0, 5_000, 250) * 1_000
else:
    # placeholders so maths below doesn’t explode
    hires_per_q = salary_new = salary_infl = sm_pct_rev = 0
    office_rent_m = other_opex_m = opex_inf = rnd_q = 0
    cogs_y1 = cogs_y2 = cogs_y3 = 0
    us_launch_cost = eal_launch_cost = 0

# ─────── TIME GRID ───────
periods = pd.period_range("2025Q3", periods=14, freq="Q")
labels  = periods.astype(str)
for q in (dist_start_q, eal_start_q):
    while q not in labels:
        periods = periods.append(periods[-1] + 1)
        labels  = periods.astype(str)

def pad(seq, n): return (seq + [0]*n)[:n]

# ─────── REVENUE ENGINE ───────
def uk_counts():
    counts = []
    for i in range(len(labels)):
        if i < 8:
            val = start_uk * (uk_growth_fast ** (i/4))
        else:
            val = counts[-1] * (1 + uk_growth_taper/4)
        counts.append(round(val))
    return counts

uk = uk_counts()

ann_price = {2025: school_price_y1,
             2026: school_price_y2,
             2027: school_price_y2,
             2028: school_price_y3}
school_price_q = [ann_price.get(p.year, school_price_y3)/4 for p in periods]
uk_rev = [c*p for c,p in zip(uk, school_price_q)]

trials = [trials_q*2] + [trials_q]*(len(labels)-1)
mat_conv = [0]*len(labels)
for i in range(2, len(labels)):
    mat_conv[i] = round(trials[i-2]*conv_rate)
mat_cum = pd.Series(mat_conv).cumsum()
mat_price_q = [ann_price.get(p.year, school_price_y3)*mat_multiplier/4 for p in periods]
mat_rev = [c*p for c,p in zip(mat_cum, mat_price_q)]

idx_us   = labels.index(dist_start_q)
dist_add = [0]*len(labels)
for i in range(idx_us, len(labels)):
    dist_add[i] = dist_add_q if i > idx_us else 1
dist_cum = pd.Series(dist_add).cumsum()
dist_price_q = [(dist_price_y1/4 if p.year == 2027 else
                 dist_price_y2/4 if p.year >= 2028 else 0) for p in periods]
dist_rev = [c*p for c,p in zip(dist_cum, dist_price_q)]

idx_eal  = labels.index(eal_start_q)
eal_learn = [0]*len(labels)
n = eal_start_learners
for i in range(idx_eal, len(labels)):
    eal_learn[i] = n
    n *= eal_q_mult
eal_rev = [n * (eal_price_yr/4) for n in eal_learn]

revenue_df = pd.DataFrame({
    "UK Schools": uk_rev,
    "MATs":       mat_rev,
    "US Dist":    dist_rev,
    "EAL":        eal_rev
}, index=labels)
revenue_df["Total"] = revenue_df.sum(axis=1)

# ─────── CASH-FLOW ENGINE ───────
if page == "Cash-flow":
    # Head-count & payroll
    ft_head = []
    ft_total = 3
    for i, lbl in enumerate(labels):
        if lbl == "2025Q4":
            ft_total += 4
        if i >= 2:
            ft_total += hires_per_q
        ft_head.append(ft_total)

    payroll_q = []
    founder_block = [100_000, 100_000, 90_000, 90_000]
    heads_so_far = 0
    for q_idx, head in enumerate(ft_head):
        yr = q_idx // 4
        infl = (1 + salary_infl) ** yr
        new = max(head - len(founder_block), 0)
        base_cost = sum(founder_block[:min(head, len(founder_block))]) * infl
        extra_cost = new * salary_new * infl
        payroll_q.append((base_cost + extra_cost) / 4 * 1.15)

    # Variable S&M
    sm_cost = revenue_df["Total"] * sm_pct_rev

    # Overheads
    infl_mult = [(1 + opex_inf) ** (p.year - 2025) for p in periods]
    office_q = [office_rent_m * 3 * m for m in infl_mult]
    other_q  = [other_opex_m * 3 * m for m in infl_mult]

    # One-off expansions
    expansion = [0]*len(labels)
    expansion[idx_us]  += us_launch_cost
    expansion[idx_eal] += eal_launch_cost

    # COGS
    cogs_pct = [cogs_y1 if p.year == 2025 else
                cogs_y2 if p.year == 2026 else
                cogs_y3 for p in periods]
    cogs = revenue_df["Total"] * cogs_pct

    cash_df = pd.DataFrame({
        "Revenue":      revenue_df["Total"],
        "COGS":         cogs,
        "Gross Profit": revenue_df["Total"] - cogs,
        "Payroll":      payroll_q,
        "Sales & Mktg": sm_cost,
        "Office":       office_q,
        "Other OpEx":   other_q,
        "R&D":          rnd_q,
        "Expansion":    expansion
    }, index=labels)

    cash_df["Operating Cash"] = cash_df["Gross Profit"] - cash_df[[
        "Payroll","Sales & Mktg","Office","Other OpEx","R&D","Expansion"]].sum(axis=1)
    cash_df["Cum Cash"] = cash_df["Operating Cash"].cumsum()

# ─────── UI ───────
st.title("📈 stylus – interactive financial model")

if page == "Revenue":
    st.subheader("Quarterly revenue (£)")
    st.dataframe(revenue_df.style.format("{:,.0f}"), use_container_width=True)

    chart = (alt.Chart(revenue_df.reset_index().melt("index", var_name="Segment",
                                                     value_name="Revenue"))
             .mark_line(point=True)
             .encode(x="index:N",
                     y=alt.Y("Revenue:Q", title="£ / quarter", stack=None),
                     color="Segment:N")
             .properties(width=900, height=400))
    st.altair_chart(chart, use_container_width=True)

else:
    st.subheader("Quarterly cash-flow (£)")
    st.dataframe(cash_df.style.format("{:,.0f}"), use_container_width=True)

    chart = (alt.Chart(cash_df.reset_index())
             .mark_area(opacity=0.6)
             .encode(x="index:N",
                     y=alt.Y("Cum Cash:Q", title="£ cumulative"))
             .properties(width=900, height=350))
    st.altair_chart(chart, use_container_width=True)

st.caption("Tweak sliders, watch the numbers dance. Figures are per quarter unless stated.")
