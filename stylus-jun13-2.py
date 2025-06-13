import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime

# ----------------------------------------------------------------------------------
# Page configuration
# ----------------------------------------------------------------------------------
st.set_page_config(page_title="stylus | Financial Forecast", layout="wide")

# ----------------------------------------------------------------------------------
# Title & lead‑in
# ----------------------------------------------------------------------------------
st.title("**stylus** | Financial Forecast")
st.caption("Three‑year forecast with two‑quarter run‑in (Q3 2025 – Q4 2028)")

# ----------------------------------------------------------------------------------
# Default parameters (pulled together for neatness)
# ----------------------------------------------------------------------------------
DEFAULTS = dict(
    starting_uk_schools=25,
    hyper_growth_factor=3.0,
    taper_growth_rate=0.20,
    mat_trials_per_quarter=10,
    mat_conversion_rate=0.70,
    schools_per_mat=10,
    mat_annual_churn=0.20,
    us_launch_quarter="Q1 2027",
    districts_per_quarter=5,
    eal_launch_quarter="Q1 2028",
    initial_eal_learners=0.10 * 1_000_000,
    eal_growth_multiplier=1.30,
    initial_employees=3,
    q4_2025_hires=4,
    quarterly_hires=2,
    avg_new_hire_salary=80_000,
    salary_inflation=0.04,
    sales_marketing_pct=0.12,
    api_cost_year1=0.15,
    api_cost_year2=0.10,
    api_cost_year3=0.05,
    infrastructure_pct=0.03,
    support_pct=0.02,
    payment_processing_pct=0.025,
    other_variable_pct=0.02,
    office_rent_monthly=5_000,
    other_opex_monthly=10_000,
    operational_inflation=0.05,
    rd_quarterly=150_000,
    us_launch_cost=500_000,
    eal_launch_cost=250_000,
)

# ----------------------------------------------------------------------------------
# Sidebar – tweakables (all collapsed by default)
# ----------------------------------------------------------------------------------
st.sidebar.header("Adjust the levers — if you must")

with st.sidebar.expander("Revenue Parameters", expanded=False):
    st.subheader("UK Schools")
    starting_uk_schools = st.number_input("Starting UK schools (Q3 2025)", value=DEFAULTS["starting_uk_schools"], min_value=1, step=5)
    hyper_growth_factor = st.number_input("Hyper‑growth factor (first 2 yrs)", value=DEFAULTS["hyper_growth_factor"], min_value=1.0, max_value=5.0, step=0.05, format="%.2f")
    taper_growth_rate = st.number_input("Annual growth after 2 yrs (%)", value=int(DEFAULTS["taper_growth_rate"]*100), min_value=0, max_value=100, step=5) / 100

    st.subheader("MATs")
    mat_trials_per_quarter = st.number_input("MAT trials per quarter", value=DEFAULTS["mat_trials_per_quarter"], min_value=0, step=5)
    mat_conversion_rate = st.number_input("MAT conversion rate (%)", value=int(DEFAULTS["mat_conversion_rate"]*100), min_value=0, max_value=100, step=1) / 100
    schools_per_mat = st.number_input("Schools per MAT", value=DEFAULTS["schools_per_mat"], min_value=1, step=1)
    mat_annual_churn = st.number_input("MAT annual churn (%)", value=int(DEFAULTS["mat_annual_churn"]*100), min_value=0, max_value=50, step=1) / 100

    st.subheader("US Districts")
    us_launch_quarter = st.selectbox("US launch quarter", ["Q1 2027", "Q2 2027", "Q3 2027"], index=["Q1 2027", "Q2 2027", "Q3 2027"].index(DEFAULTS["us_launch_quarter"]))
    districts_per_quarter = st.number_input("New districts per quarter", value=DEFAULTS["districts_per_quarter"], min_value=0, step=1)

    st.subheader("EAL")
    eal_launch_quarter = st.selectbox("EAL launch quarter", ["Q1 2028", "Q2 2028", "Q3 2028"], index=["Q1 2028", "Q2 2028", "Q3 2028"].index(DEFAULTS["eal_launch_quarter"]))
    initial_eal_learners = st.number_input("Initial EAL learners (millions)", value=DEFAULTS["initial_eal_learners"] / 1_000_000, min_value=0.01, step=0.01, format="%.2f") * 1_000_000
    eal_growth_multiplier = st.number_input("EAL quarterly growth multiplier", value=DEFAULTS["eal_growth_multiplier"], min_value=1.0, step=0.05, format="%.2f")

with st.sidebar.expander("Headcount", expanded=False):
    initial_employees = st.number_input("Initial employees", value=DEFAULTS["initial_employees"], min_value=1, step=1)
    q4_2025_hires = st.number_input("Q4 2025 hires", value=DEFAULTS["q4_2025_hires"], min_value=0, step=1)
    quarterly_hires = st.number_input("Quarterly hires from Q1 2026", value=DEFAULTS["quarterly_hires"], min_value=0, step=1)
    avg_new_hire_salary = st.number_input("Avg new‑hire salary (£k)", value=DEFAULTS["avg_new_hire_salary"]//1_000, min_value=0, step=10) * 1_000
    salary_inflation = st.number_input("Salary inflation (% p.a.)", value=int(DEFAULTS["salary_inflation"]*100), min_value=0, max_value=20, step=1) / 100

with st.sidebar.expander("Variable Costs", expanded=False):
    sales_marketing_pct = st.number_input("Sales & Marketing (% of revenue)", value=int(DEFAULTS["sales_marketing_pct"]*100), min_value=0, max_value=50, step=1) / 100

with st.sidebar.expander("COGS Breakdown", expanded=False):
    st.markdown("**API / AI (% of revenue)**")
    api_cost_year1 = st.number_input("Year 1", value=int(DEFAULTS["api_cost_year1"]*100), min_value=0, max_value=50, step=1) / 100
    api_cost_year2 = st.number_input("Year 2", value=int(DEFAULTS["api_cost_year2"]*100), min_value=0, max_value=50, step=1) / 100
    api_cost_year3 = st.number_input("Year 3+", value=int(DEFAULTS["api_cost_year3"]*100), min_value=0, max_value=50, step=1) / 100

    st.markdown("**Other variable (% of revenue)**")
    infrastructure_pct = st.number_input("Infrastructure / Hosting", value=int(DEFAULTS["infrastructure_pct"]*100), min_value=0, max_value=20, step=1) / 100
    support_pct = st.number_input("Customer Support", value=int(DEFAULTS["support_pct"]*100), min_value=0, max_value=20, step=1) / 100
    payment_processing_pct = st.number_input("Payment Processing", value=DEFAULTS["payment_processing_pct"]*100, min_value=0.0, max_value=10.0, step=0.5, format="%.2f") / 100
    other_variable_pct = st.number_input("Other variable", value=int(DEFAULTS["other_variable_pct"]*100), min_value=0, max_value=20, step=1) / 100

with st.sidebar.expander("Fixed Costs", expanded=False):
    office_rent_monthly = st.number_input("Office rent per month (£k)", value=DEFAULTS["office_rent_monthly"]//1_000, min_value=0, step=1) * 1_000
    other_opex_monthly = st.number_input("Other OpEx per month (£k)", value=DEFAULTS["other_opex_monthly"]//1_000, min_value=0, step=1) * 1_000
    operational_inflation = st.number_input("Operational inflation (% p.a.)", value=int(DEFAULTS["operational_inflation"]*100), min_value=0, max_value=20, step=1) / 100
    rd_quarterly = st.number_input("R&D per quarter (£k)", value=DEFAULTS["rd_quarterly"]//1_000, min_value=0, step=10) * 1_000

with st.sidebar.expander("Expansion Costs", expanded=False):
    us_launch_cost = st.number_input("US launch cost (£k)", value=DEFAULTS["us_launch_cost"]//1_000, min_value=0, step=50) * 1_000
    eal_launch_cost = st.number_input("EAL launch cost (£k)", value=DEFAULTS["eal_launch_cost"]//1_000, min_value=0, step=50) * 1_000

# ----------------------------------------------------------------------------------
# Helper bits
# ----------------------------------------------------------------------------------

def quarter_to_date(qstr: str):
    q, year = qstr.split()
    month = (int(q[1]) - 1) * 3 + 1
    return pd.Timestamp(f"{year}-{month:02d}-01")

def date_to_quarter(date: pd.Timestamp) -> str:
    return f"Q{((date.month - 1)//3) + 1} {date.year}"

# Timeline (fixed 14 quarters)
base_date = pd.Timestamp("2025-07-01")
quarters = [date_to_quarter(base_date + pd.DateOffset(months=3*i)) for i in range(14)]

# ----------------------------------------------------------------------------------
# Revenue calcs
# ----------------------------------------------------------------------------------

def calc_uk():
    schools, rev = [], []
    for i in range(len(quarters)):
        if i < 8:
            count = starting_uk_schools * (hyper_growth_factor ** (i/4))
        else:
            count = schools[-1] * ((1 + taper_growth_rate) ** 0.25)
        schools.append(int(count))
        year = i//4 + 1
        price = 5_000 if year == 1 else 10_000 if year == 2 else 15_000
        rev.append((count * price)/4)
    return schools, rev


def calc_mat():
    trials, conv, rev, active, cohorts = [], [], [], [], []
    churn_q = 1 - (1 - mat_annual_churn) ** 0.25
    for i in range(len(quarters)):
        for c in cohorts:
            c["current"] *= (1 - churn_q)

        trials.append(mat_trials_per_quarter)
        new_conv = 0 if i < 2 else int(trials[i-2] * mat_conversion_rate)
        conv.append(new_conv)
        if new_conv:
            cohorts.append({"q": i, "current": new_conv})

        rev_q, active_now = 0, 0
        for c in cohorts:
            active_now += c["current"]
            yrs = (i - c["q"]) // 4 + 1
            price = 5_000 if yrs == 1 else 10_000 if yrs == 2 else 15_000
            rev_q += (c["current"] * schools_per_mat * price)/4
        rev.append(rev_q)
        active.append(int(active_now))
    return trials, conv, rev, active


def calc_us():
    districts, rev, cohorts = [], [], []
    launch_idx = quarters.index(us_launch_quarter)
    for i in range(len(quarters)):
        if i < launch_idx:
            districts.append(0)
            rev.append(0)
            continue
        if i == launch_idx:
            districts.append(1)
            cohorts.append({"q": i, "districts": 1})
        else:
            districts.append(districts[-1] + districts_per_quarter)
            cohorts.append({"q": i, "districts": districts_per_quarter})
        rev_q = 0
        for c in cohorts:
            yrs = (i - c["q"]) // 4
            price = 100_000 if yrs == 0 else 150_000
            rev_q += (c["districts"] * price)/4
        rev.append(rev_q)
    return districts, rev


def calc_eal():
    learners, rev = [], []
    try:
        launch_idx = quarters.index(eal_launch_quarter)
    except ValueError:
        return [0]*len(quarters), [0]*len(quarters)
    for i in range(len(quarters)):
        if i < launch_idx:
            learners.append(0)
            rev.append(0)
            continue
        delta = i - launch_idx
        lrn = initial_eal_learners * (eal_growth_multiplier ** delta)
        learners.append(int(lrn))
        rev.append((lrn * 30)/4)
    return learners, rev

uk_schools, uk_rev = calc_uk()
mat_trials, mat_conv, mat_rev, active_mats = calc_mat()
districts, us_rev = calc_us()
learners, eal_rev = calc_eal()

quarterly_rev = [sum(x) for x in zip(uk_rev, mat_rev, us_rev, eal_rev)]

revenue_df = pd.DataFrame({
    "Quarter": quarters,
    "UK Schools": [r*4 for r in uk_rev],
    "MATs": [r*4 for r in mat_rev],
    "US Districts": [r*4 for r in us_rev],
    "EAL": [r*4 for r in eal_rev],
})
revenue_df["Total"] = revenue_df.drop(columns=["Quarter"]).sum(axis=1)

# ----------------------------------------------------------------------------------
# Revenue section
# ----------------------------------------------------------------------------------
st.header("Revenue Forecast (ARR)")

col1, col2, col3, col4 = st.columns(4)
col1.metric("UK Schools (latest)", f"{uk_schools[-1]:,}")
col2.metric("Active MATs", f"{active_mats[-1]:,}")
col3.metric("US Districts (latest)", f"{districts[-1]:,}")
col4.metric("EAL learners (latest)", f"{learners
