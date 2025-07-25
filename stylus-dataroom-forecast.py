import streamlit as st
import pandas as pd
import altair as alt
import numpy as np
from datetime import datetime

# ----------------------------------------------------------------------------------
# Page configuration
# ----------------------------------------------------------------------------------
st.set_page_config(page_title="stylus | Financial Forecast", layout="wide")

# ----------------------------------------------------------------------------------
# Title & lead‑in
# ----------------------------------------------------------------------------------
st.title("**stylus** | Financial Forecast")
st.caption("Three‑year forecast with a one‑quarter run‑in (Q4 2025 – Q4 2028)")

# ----------------------------------------------------------------------------------
# Default parameters
# ----------------------------------------------------------------------------------
# Revenue defaults
defaults = {
    "starting_uk_schools": 25,
    "hyper_growth_factor": 4.0,
    "taper_growth_rate": 0.50,
    "mat_trials_per_quarter": 20,
    "mat_conversion_rate": 0.70,
    "schools_per_mat": 10,
    "mat_annual_churn": 0.20,
    "us_launch_quarter": "Q1 2027",
    "districts_per_quarter": 5,
    "eal_launch_quarter": "Q1 2028",
    "initial_eal_learners": 0.03 * 1_000_000,
    "eal_growth_multiplier": 1.75,
    # Cost defaults
    "initial_employees": 3,
    "q4_2025_hires": 4,
    "quarterly_hires": 3,
    "avg_new_hire_salary": 80_000,
    "salary_inflation": 0.04,
    "sales_marketing_pct": 0.15,
    "api_cost_year1": 0.25,
    "api_cost_year2": 0.20,
    "api_cost_year3": 0.15,
    "infrastructure_pct": 0.02,
    "support_pct": 0.05,
    "payment_processing_pct": 0.02,
    "other_variable_pct": 0.00,
    "office_rent_monthly": 10_000,
    "other_opex_monthly": 10_000,
    "operational_inflation": 0.20,
    "rd_quarterly": 100_000,
    "us_launch_cost": 250_000,
    "eal_launch_cost": 750_000,
}

# ----------------------------------------------------------------------------------
# Sidebar: tweakables – collapsible, shut by default
# ----------------------------------------------------------------------------------
st.sidebar.header("Adjust the levers (optional)")

# Revenue parameters
with st.sidebar.expander("Revenue Parameters", expanded=False):
    st.subheader("UK Schools")
    starting_uk_schools = st.number_input("Starting UK schools (Q3 2025)", value=defaults["starting_uk_schools"], min_value=1, step=5)
    hyper_growth_factor = st.number_input("Hyper‑growth factor (first 2 years)", value=defaults["hyper_growth_factor"], min_value=1.0, max_value=5.0, step=0.05, format="%.2f")
    taper_growth_rate = st.number_input("Annual growth after 2 years (%)", value=int(defaults["taper_growth_rate"]*100), min_value=0, max_value=100, step=5) / 100.0

    st.subheader("MATs")
    mat_trials_per_quarter = st.number_input("MAT trials per quarter", value=defaults["mat_trials_per_quarter"], min_value=0, step=5)
    mat_conversion_rate = st.number_input("MAT conversion rate (%)", value=int(defaults["mat_conversion_rate"]*100), min_value=0, max_value=100, step=1) / 100.0
    schools_per_mat = st.number_input("Schools per MAT", value=defaults["schools_per_mat"], min_value=1, step=1)
    mat_annual_churn = st.number_input("MAT annual churn (%)", value=int(defaults["mat_annual_churn"]*100), min_value=0, max_value=50, step=1) / 100.0

    st.subheader("US Districts")
    us_launch_quarter = st.selectbox("US launch quarter", ["Q1 2027", "Q2 2027", "Q3 2027"], index=["Q1 2027", "Q2 2027", "Q3 2027"].index(defaults["us_launch_quarter"]))
    districts_per_quarter = st.number_input("New districts per quarter", value=defaults["districts_per_quarter"], min_value=0, step=1)

    st.subheader("EAL")
    eal_launch_quarter = st.selectbox("EAL launch quarter", ["Q1 2028", "Q2 2028", "Q3 2028"], index=["Q1 2028", "Q2 2028", "Q3 2028"].index(defaults["eal_launch_quarter"]))
    initial_eal_learners = st.number_input("Initial EAL learners (millions)", value=defaults["initial_eal_learners"] / 1_000_000, min_value=0.01, step=0.01, format="%.2f") * 1_000_000
    eal_growth_multiplier = st.number_input("EAL quarterly growth multiplier", value=defaults["eal_growth_multiplier"], min_value=1.0, step=0.05, format="%.2f")

# Headcount
with st.sidebar.expander("Headcount", expanded=False):
    initial_employees = st.number_input("Initial employees", value=defaults["initial_employees"], min_value=1, step=1)
    q4_2025_hires = st.number_input("Q4 2025 hires", value=defaults["q4_2025_hires"], min_value=0, step=1)
    quarterly_hires = st.number_input("Quarterly hires from Q1 2026", value=defaults["quarterly_hires"], min_value=0, step=1)
    avg_new_hire_salary = st.number_input("Average new‑hire salary (£k)", value=defaults["avg_new_hire_salary"]//1000, min_value=0, step=10) * 1_000
    salary_inflation = st.number_input("Annual salary inflation (%)", value=int(defaults["salary_inflation"]*100), min_value=0, max_value=20, step=1) / 100.0

# Variable costs
with st.sidebar.expander("Variable Costs", expanded=False):
    sales_marketing_pct = st.number_input("Sales & Marketing (as % of revenue)", value=int(defaults["sales_marketing_pct"]*100), min_value=0, max_value=50, step=1) / 100.0

# COGS
with st.sidebar.expander("COGS Breakdown", expanded=False):
    st.markdown("**API / AI costs (% of revenue)**")
    api_cost_year1 = st.number_input("Year 1", value=int(defaults["api_cost_year1"]*100), min_value=0, max_value=50, step=1) / 100.0
    api_cost_year2 = st.number_input("Year 2", value=int(defaults["api_cost_year2"]*100), min_value=0, max_value=50, step=1) / 100.0
    api_cost_year3 = st.number_input("Year 3+", value=int(defaults["api_cost_year3"]*100), min_value=0, max_value=50, step=1) / 100.0

    st.markdown("**Other variable costs (% of revenue)**")
    infrastructure_pct = st.number_input("Infrastructure / Hosting", value=int(defaults["infrastructure_pct"]*100), min_value=0, max_value=20, step=1) / 100.0
    support_pct = st.number_input("Customer Support", value=int(defaults["support_pct"]*100), min_value=0, max_value=20, step=1) / 100.0
    payment_processing_pct = st.number_input("Payment Processing", value=defaults["payment_processing_pct"]*100, min_value=0.0, max_value=10.0, step=0.5, format="%.2f") / 100.0
    other_variable_pct = st.number_input("Other Variable", value=int(defaults["other_variable_pct"]*100), min_value=0, max_value=20, step=1) / 100.0

# Fixed costs
with st.sidebar.expander("Fixed Costs", expanded=False):
    office_rent_monthly = st.number_input("Office rent per month (£k)", value=defaults["office_rent_monthly"]//1000, min_value=0, step=1) * 1_000
    other_opex_monthly = st.number_input("Other OpEx per month (£k)", value=defaults["other_opex_monthly"]//1000, min_value=0, step=1) * 1_000
    operational_inflation = st.number_input("Operational inflation (% p.a.)", value=int(defaults["operational_inflation"]*100), min_value=0, max_value=20, step=1) / 100.0
    rd_quarterly = st.number_input("R&D spend per quarter (£k)", value=defaults["rd_quarterly"]//1000, min_value=0, step=10) * 1_000

# Expansion costs
with st.sidebar.expander("Expansion Costs", expanded=False):
    us_launch_cost = st.number_input("US launch cost (£k)", value=defaults["us_launch_cost"]//1000, min_value=0, step=50) * 1_000
    eal_launch_cost = st.number_input("EAL launch cost (£k)", value=defaults["eal_launch_cost"]//1000, min_value=0, step=50) * 1_000

# ----------------------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------------------

def quarter_to_date(qstr: str) -> pd.Timestamp:
    q, year = qstr.split()
    month = (int(q[1]) - 1) * 3 + 1
    return pd.Timestamp(f"{year}-{month:02d}-01")

def date_to_quarter(date: pd.Timestamp) -> str:
    return f"Q{((date.month - 1)//3) + 1} {date.year}"

# ----------------------------------------------------------------------------------
# Timeline (fixed 13 quarters: Q4 2025 – Q4 2028)
# ----------------------------------------------------------------------------------
base_date = pd.Timestamp("2025-10-01")
num_quarters = 13
quarters = [date_to_quarter(base_date + pd.DateOffset(months=3*i)) for i in range(num_quarters)]

# ----------------------------------------------------------------------------------
# Revenue calculations
# ----------------------------------------------------------------------------------

def calc_uk_schools(qtrs):
    schools, revenue = [], []
    for i in range(len(qtrs)):
        if i < 8:  # hyper‑growth for 2 years
            count = starting_uk_schools * (hyper_growth_factor ** (i/4))
        else:
            growth_q = (1 + taper_growth_rate) ** 0.25
            count = schools[-1] * growth_q
        schools.append(int(count))

        # pricing tiers by year of service
        year = i//4 + 1
        annual_price = 5_000 if year == 1 else 10_000 if year == 2 else 15_000
        revenue.append((count * annual_price)/4)
    return schools, revenue


def calc_mat_revenue(qtrs):
    trials, conversions, revenue, active = [], [], [], []
    cohorts = []
    churn_q = 1 - (1 - mat_annual_churn) ** 0.25

    for i in range(len(qtrs)):
        # churn existing
        for cohort in cohorts:
            cohort["current"] *= (1 - churn_q)

        trials.append(mat_trials_per_quarter)
        new_conv = 0 if i < 2 else int(trials[i-2] * mat_conversion_rate)
        conversions.append(new_conv)
        if new_conv:
            cohorts.append({"q": i, "initial": new_conv, "current": new_conv})

        rev_q = 0
        active_mats = 0
        for cohort in cohorts:
            active_mats += cohort["current"]
            yrs = (i - cohort["q"])//4 + 1
            price = 5_000 if yrs == 1 else 10_000 if yrs == 2 else 15_000
            rev_q += (cohort["current"] * schools_per_mat * price)/4
        revenue.append(rev_q)
        active.append(int(active_mats))
    return trials, conversions, revenue, active


def calc_us_revenue(qtrs):
    districts, revenue = [], []
    cohorts = []
    launch_idx = qtrs.index(us_launch_quarter)

    for i in range(len(qtrs)):
        if i < launch_idx:
            districts.append(0)
            revenue.append(0)
            continue
        if i == launch_idx:
            districts.append(1)
            cohorts.append({"q": i, "districts": 1})
        else:
            districts.append(districts[-1] + districts_per_quarter)
            cohorts.append({"q": i, "districts": districts_per_quarter})

        rev_q = 0
        for cohort in cohorts:
            yrs = (i - cohort["q"])//4
            price = 100_000 if yrs == 0 else 150_000
            rev_q += (cohort["districts"] * price)/4
        revenue.append(rev_q)
    return districts, revenue


def calc_eal_revenue(qtrs):
    learners, revenue = [], []
    try:
        launch_idx = qtrs.index(eal_launch_quarter)
    except ValueError:
        return [0]*len(qtrs), [0]*len(qtrs)

    for i in range(len(qtrs)):
        if i < launch_idx:
            learners.append(0)
