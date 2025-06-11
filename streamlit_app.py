"""
Streamlit interactive revenue + cash-flow model for Stylus Education
===================================================================
Copy into a GitHub repo (e.g. stylus-forecast) and deploy on
https://share.streamlit.io – investors get a live playground.
"""

import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="Stylus Forecast Model", layout="wide")

# ──────────────────── NAV ────────────────────
page = st.sidebar.radio("Choose view", ["Revenue", "Cash-flow"], index=0)

# ───────────— Shared revenue assumptions ───────────—
st.sidebar.header("Growth assumptions")

# UK schools
start_uk        = st.sidebar.number_input("Starting UK schools (Q3 ’25)", 10, 2_000, 100, 10)
uk_growth_fast  = st.sidebar.slider("Hyper-growth factor (× over first 2 yrs)", 1.0, 10.0, 5.0, 0.5)
uk_growth_taper = st.sidebar.slider("Annual growth after taper (-%)", 0, 100, 20, 5) / 100

# MATs
trials_q       = st.sidebar.number_input("MAT trials / quarter", 1, 100, 25)
conv_rate      = st.sidebar.slider("MAT conversion rate", 0.0, 1.0, 0.70, 0.05)
mat_multiplier = st.sidebar.number_input("Schools per MAT", 5, 25, 10)

# US districts
dist_add_q   = st.sidebar.number_input("US districts added / quarter", 1, 50, 15)
dist_start_q = st.sidebar.selectbox("US launch quarter",
                                    ["2027Q1", "2027Q2", "2027Q3"], index=0)

# EAL
eal_start_q        = st.sidebar.selectbox("EAL launch quarter",
                                          ["2028Q1", "2028Q2", "2028Q3"], 0)
eal_start_learners = st.sidebar.number_input("EAL learners at launch (m)",
                                             0.1, 10.0, 1.0, 0.1) * 1_000_000
eal_q_mult         = st.sidebar.slider("EAL learner growth / qtr (×)",
                                       1.0, 4.0, 2.0, 0.25)

# Pricing (annual)
school_price_y1 = st.sidebar.number_input("School price Y1 (£k)", 1, 50, 5)*1_000
school_price_y2 = st.sidebar.number_input("School price Y2 (£k)", 1, 50, 10)*1_000
school_price_y3 = st.sidebar.number_input("School price Y3 (£k)", 1, 50, 15)*1_000
dist_price_y1   = st.sidebar.number_input("District price Y1 (£k)", 10, 500, 100)*1_000
dist_price_y2   = st.sidebar.number_input("District price Y2+ (£k)", 10, 500, 150)*1_000
eal_price_yr    = 30     # £ / learner / yr

# ───────────— Cash-flow specific sliders ───────────—
with st.sidebar.expander("Cash-flow assumptions"):

    # head-count
    hires_per_q = st.slider("New FT hires each quarter (from 2026Q1)", 0, 10, 2)
    salary_new  = st.number_input("Avg salary new hire (£k)", 50, 150, 80)*1_000

    # overheads
    office_rent_m   = st.number_input("Office rent (£k / m)", 1, 50, 5)*1_000
    other_opex_m    = st.number_input("Other OpEx (£k / m)", 1, 50, 10)*1_000
    opex_inf_y2_y3  = st.slider("OpEx annual inflation after Year 1 (%)", 0, 20, 5)/100

    # COGS %
    cogs_y1 = st.slider("COGS % Year 1", 0, 100, 25) / 100
    cogs_y2 = st.slider("COGS % Year 2", 0, 100, 20) / 100
    cogs_y3 = st.slider("COGS % Year 3", 0, 100, 15) / 100

# ───────────— Helpers ───────────—
def pad(seq, n): return (seq + [0]*n)[:n]

# ───────────— Build 3-yr (14 qtrs) revenue forecast ───────────—
periods = pd.period_range("2025Q3", periods=14, freq="Q")
labels  = periods.astype(str)

# UK counts (s-curve)
def uk_counts():
    counts, half_targets = [], [start_uk]
    while len(counts) < 14:
        i = len(half_targets)
        target = (start_uk * (uk_growth_fast**i) if i <= 4
                  else half_targets[-1] * (1 + uk_growth_taper*2))
        half_targets.append(round(target))
        base, nxt = half_targets[-2], half_targets[-1]
        delta = nxt - base
        counts += [base + round(delta*0.4), nxt]
    return counts[:14]

uk = uk_counts()

# price maps
ann_price = {2025: school_price_y1,
             2026: school_price_y2*0.75 + school_price_y1*0.25,
             2027: school_price_y2,
             2028: school_price_y3}
school_price_q = [ann_price.get(p.year, school_price_y3)/4 for p in periods]
uk_rev = [c*p for c,p in zip(uk, school_price_q)]

# MATs
trials = [trials_q*2]+[trials_q]*13
mat_conv = [0]*14
for i in range(2,14):
    mat_conv[i] = round(trials[i-2]*conv_rate)
mat_cum = pd.Series(mat_conv).cumsum()
mat_price_q = [ann_price.get(p.year, school_price_y3)*mat_multiplier/4 for p in periods]
mat_rev = [c*p for c,p in zip(mat_cum, mat_price_q)]

# ensure forecast runs far enough to include chosen launch quarters
all_needed = {dist_start_q, eal_start_q}
while max(all_needed) > labels[-1]:
    periods = periods.append(periods[-1] + 1)       # add another quarter
    labels  = periods.astype(str)

# US districts
idx0 = list(labels).index(dist_start_q)
dist_add = [0]*14
for i in range(idx0,14):
    dist_add[i] = dist_add_q if i>idx0 else 1
dist_cum = pd.Series(dist_add).cumsum()
dist_price_q = [0 if p.year<2027 else
                (dist_price_y1 if p.year==2027 else dist_price_y2)/4
                for p in periods]
dist_rev = [c*p for c,p in zip(dist_cum, dist_price_q)]

# EAL
idx_eal = list(labels).index(eal_start_q)
eal_learn = [0]*14
if idx_eal<14:
    n = eal_start_learners
    for i in range(idx_eal,14):
        eal_learn[i]=n
        n*=eal_q_mult
eal_rev = [n*(eal_price_yr/4) for n in eal_learn]

revenue_df = pd.DataFrame({
    "UK Schools": pad(uk_rev,14),
    "MATs":       pad(mat_rev,14),
    "US Dist":    pad(dist_rev,14),
    "EAL":        pad(eal_rev,14)
}, index=labels)
revenue_df["Total"] = revenue_df.sum(axis=1)

# ───────────— Cash-flow calcs ───────────—
if page=="Cash-flow":

    # head-count schedule
    ft_head = []
    ft = 3                            # founding FT staff
    for i, lab in enumerate(labels):
        if lab=="2025Q4":             # immediate +4 hires post-raise
            ft += 4
        if i>=2:                      # from 2026Q1 onwards
            ft += hires_per_q
        ft_head.append(ft)

    avg_existing_salary = (100_000+100_000+90_000)/3       # first 3 founders ≈ £96k
    salary_ft = [avg_existing_salary]*3 + [90_000,90_000,75_000,75_000]  # first 7
    avg_new = salary_new

    ft_payroll = []
    headcount_so_far = 0
    for q, head in enumerate(ft_head):
        if q==0: headcount_so_far = head
        new_hires = head - headcount_so_far
        headcount_so_far = head
        # first 7 hires have known salaries; subsequent hires use avg_new
        if head <= 7:
            cost = sum(salary_ft[:head])
        else:
            cost = sum(salary_ft) + (head-7)*avg_new
        ft_payroll.append(cost/4)    # quarterly
    # add on-costs
    ft_payroll = [p*1.15 for p in ft_payroll]

    # contractors & PT (fixed)
    contract_annual = (90_000+60_000)
    part_time_annual= (60_000+50_000+45_000+45_000)*1.15
    contract_q = contract_annual/4
    pt_q       = part_time_annual/4

    payroll_q = [ft_payroll[i]+contract_q+pt_q for i in range(14)]

    # overheads (with inflation after year 1)
    office_q = office_rent_m*3
    other_q_base = other_opex_m*3
    other_q = []
    for p in periods:
        mult = 1.0 if p.year==2025 else (1+opex_inf_y2_y3)**(p.year-2025)
        other_q.append(other_q_base*mult)

    # COGS %
    cogs_pct = [cogs_y1 if p.year==2025 else
                cogs_y2 if p.year==2026 else
                cogs_y3 for p in periods]
    cogs = revenue_df["Total"]*cogs_pct

    cash_df = pd.DataFrame({
        "Revenue":      revenue_df["Total"],
        "COGS":         cogs,
        "Gross Profit": revenue_df["Total"]-cogs,
        "Payroll":      payroll_q,
        "Office":       office_q,
        "Other OpEx":   other_q,
    }, index=labels)
    cash_df["Operating Cash"] = (cash_df["Gross Profit"] -
                                 cash_df["Payroll"] -
                                 cash_df["Office"] -
                                 cash_df["Other OpEx"])
    cash_df["Cum Cash"] = cash_df["Operating Cash"].cumsum()

# ───────────— DISPLAY —──────────—
st.title("📈 Stylus Education – Interactive Financial Model")

if page=="Revenue":
    st.subheader("Quarterly Revenue (£)")
    st.dataframe(revenue_df.style.format("{:,.0f}"))

    chart = (
        alt.Chart(revenue_df.reset_index().melt("index",
                                                var_name="Segment",
                                                value_name="Revenue"))
        .mark_line(point=True)
        .encode(x="index:N",
                y=alt.Y("Revenue:Q", title="£ per quarter", stack=None),
                color="Segment:N")
        .properties(width=900, height=400)
    )
    st.altair_chart(chart, use_container_width=True)

else:
    st.subheader("Quarterly Cash-flow (£)")
    st.dataframe(cash_df.style.format("{:,.0f}"))

    cash_chart = (
        alt.Chart(cash_df.reset_index())
        .mark_area(opacity=0.6)
        .encode(x="index:N",
                y=alt.Y("Cum Cash:Q", title="£ cumulative"))
        .properties(width=900, height=350)
    )
    st.altair_chart(cash_chart, use_container_width=True)

st.caption("Sliders left → play with growth, hiring and cost levers; figures are per quarter.")
