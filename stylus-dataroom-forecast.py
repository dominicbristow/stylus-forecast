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
st.caption("Three‑year forecast with two‑quarter run‑in (Q3 2025 – Q4 2028)")

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
# Timeline (fixed 14 quarters: Q3 2025 – Q4 2028)
# ----------------------------------------------------------------------------------
base_date = pd.Timestamp("2025-07-01")
num_quarters = 14
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
            revenue.append(0)
            continue
        quarters_since = i - launch_idx
        lrn = initial_eal_learners * (eal_growth_multiplier ** quarters_since)
        learners.append(int(lrn))
        revenue.append((lrn * 30)/4)
    return learners, revenue

# run calculations
uk_schools, uk_rev = calc_uk_schools(quarters)
mat_trials, mat_conversions, mat_rev, active_mats = calc_mat_revenue(quarters)
districts, us_rev = calc_us_revenue(quarters)
learners, eal_rev = calc_eal_revenue(quarters)

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
# Revenue section – looks like a report
# ----------------------------------------------------------------------------------
st.header("Revenue Forecast (ARR)")

col1, col2, col3, col4 = st.columns(4)
col1.metric("UK Schools (latest)", f"{uk_schools[-1]:,}")
col2.metric("Active MATs", f"{active_mats[-1]:,}")
col3.metric("US Districts (latest)", f"{districts[-1]:,}")
col4.metric("EAL learners (latest)", f"{learners[-1]:,}")

formatted_rev = revenue_df.copy()
for c in ["UK Schools", "MATs", "US Districts", "EAL", "Total"]:
    formatted_rev[c] = formatted_rev[c].apply(lambda v: f"£{v:,.0f}")

st.dataframe(formatted_rev, use_container_width=True)

# Fix: Exclude "Total" column when melting the dataframe
rev_long = pd.melt(revenue_df[["Quarter", "UK Schools", "MATs", "US Districts", "EAL"]], 
                   id_vars=["Quarter"], var_name="Stream", value_name="ARR")
order = ["UK Schools", "MATs", "US Districts", "EAL"]
chart = alt.Chart(rev_long).mark_area(opacity=0.8).encode(
    x=alt.X("Quarter:O", sort=quarters, axis=alt.Axis(labelAngle=-45)),
    y=alt.Y("ARR:Q", stack="zero", axis=alt.Axis(format=",.0f", title="Annual Recurring Revenue (£)")),
    color=alt.Color("Stream:N", scale=alt.Scale(domain=order, range=["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"])),
    tooltip=[alt.Tooltip("Quarter:N"), alt.Tooltip("Stream:N"), alt.Tooltip("ARR:Q", format=",.0f", title="ARR (£)")],
).properties(width=800, height=400, title="ARR by Segment (stacked)")

st.altair_chart(chart, use_container_width=True)

# ----------------------------------------------------------------------------------
# Cash‑flow section (immediately below)
# ----------------------------------------------------------------------------------
st.divider()
st.header("Cash‑flow Analysis")
st.caption("ARR shown for reference; all costs and cash figures are quarterly.")

# Headcount & payroll
known_salaries = [100_000, 100_000, 90_000, 90_000]
headcount, payroll = [], []
for i in range(len(quarters)):
    if i == 0:
        hc = initial_employees
    elif i == 1:
        hc = headcount[-1] + q4_2025_hires
    else:
        hc = headcount[-1] + quarterly_hires
    headcount.append(hc)

    # salary base
    if hc <= 4:
        base = sum(known_salaries[:hc])
    else:
        base = sum(known_salaries) + (hc - 4) * avg_new_hire_salary
    infl = (1 + salary_inflation) ** (i/4)
    payroll.append((base * infl * 1.15)/4)  # NI + pension assumed 15 %

# COGS components
api_costs, infra_costs, support_costs, payment_costs, other_var_costs, cogs = [], [], [], [], [], []
for i, rev in enumerate(quarterly_rev):
    yr = i//4 + 1
    api_rate = api_cost_year1 if yr == 1 else api_cost_year2 if yr == 2 else api_cost_year3
    api = rev * api_rate
    infra = rev * infrastructure_pct
    sup = rev * support_pct
    pay = rev * payment_processing_pct
    oth = rev * other_variable_pct
    total = api + infra + sup + pay + oth

    api_costs.append(api)
    infra_costs.append(infra)
    support_costs.append(sup)
    payment_costs.append(pay)
    other_var_costs.append(oth)
    cogs.append(total)

# Gross profit
gross_profit = [r - c for r, c in zip(quarterly_rev, cogs)]

# Variable S&M
sales_marketing = [r * sales_marketing_pct for r in quarterly_rev]

# Fixed costs (inflated)
office_rent, other_opex, rd_costs = [], [], []
for i in range(len(quarters)):
    infl = (1 + operational_inflation) ** (i/4)
    office_rent.append(office_rent_monthly * 3 * infl)
    other_opex.append(other_opex_monthly * 3 * infl)
    rd_costs.append(rd_quarterly)

# Expansion costs
expansion_costs = [0]*len(quarters)
expansion_costs[quarters.index(us_launch_quarter)] += us_launch_cost
expansion_costs[quarters.index(eal_launch_quarter)] += eal_launch_cost

# Operating cash & cumulative
operating_cash, cumulative_cash = [], []
for i in range(len(quarters)):
    op = gross_profit[i] - payroll[i] - sales_marketing[i] - office_rent[i] - other_opex[i] - rd_costs[i] - expansion_costs[i]
    operating_cash.append(op)
    cumulative_cash.append(op if i == 0 else cumulative_cash[-1] + op)

# Key cash metrics
c1, c2, c3, c4 = st.columns(4)
c1.metric("Latest ARR", f"£{revenue_df['Total'].iloc[-1]:,.0f}")
margin = (gross_profit[-1]/quarterly_rev[-1])*100 if quarterly_rev[-1] else 0
c2.metric("Gross margin", f"{margin:.1f}%")
c3.metric("Quarterly burn / profit", f"£{operating_cash[-1]:,.0f}")
c4.metric("Cash position", f"£{cumulative_cash[-1]:,.0f}")

cash_df = pd.DataFrame({
    "Quarter": quarters,
    "ARR": [r*4 for r in quarterly_rev],
    "Quarterly Revenue": quarterly_rev,
    "API / AI": api_costs,
    "Infrastructure": infra_costs,
    "Support": support_costs,
    "Payment Processing": payment_costs,
    "Other Variable": other_var_costs,
    "Total COGS": cogs,
    "Gross Profit": gross_profit,
    "Payroll": payroll,
    "Sales & Marketing": sales_marketing,
    "Office Rent": office_rent,
    "Other OpEx": other_opex,
    "R&D": rd_costs,
    "Expansion": expansion_costs,
    "Operating Cash": operating_cash,
    "Cumulative Cash": cumulative_cash,
})

formatted_cash = cash_df.copy()
for col in formatted_cash.columns[1:]:
    formatted_cash[col] = formatted_cash[col].apply(lambda v: f"£{v:,.0f}")

st.dataframe(formatted_cash, use_container_width=True)

cash_chart = alt.Chart(cash_df).mark_area(line={"color": "darkblue"}, color="lightblue", opacity=0.7).encode(
    x=alt.X("Quarter:O", sort=quarters, axis=alt.Axis(labelAngle=-45)),
    y=alt.Y("Cumulative Cash:Q", axis=alt.Axis(format=",.0f", title="Cumulative Cash (£)"), scale=alt.Scale(zero=False)),
    tooltip=[alt.Tooltip("Quarter:N"), alt.Tooltip("Cumulative Cash:Q", format=",.0f", title="Cash (£)")],
).properties(width=800, height=400, title="Cumulative Cash Position")

st.altair_chart(cash_chart, use_container_width=True)

st.caption(f"API costs decline from {int(api_cost_year1*100)} % to {int(api_cost_year3*100)} % of revenue over three years; other variable‑cost ratios remain constant.")
