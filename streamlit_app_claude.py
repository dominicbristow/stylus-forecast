import streamlit as st
import pandas as pd
import altair as alt
import numpy as np
from datetime import datetime

# Page configuration
st.set_page_config(page_title="Stylus Forecast Model", layout="wide")

# Title
st.title("Stylus Education Financial Forecast")

# Initialize session state
if 'view' not in st.session_state:
    st.session_state.view = "Revenue"

# Navigation
view = st.sidebar.radio("Select View", ["Revenue", "Cash-flow"], index=0 if st.session_state.view == "Revenue" else 1)
st.session_state.view = view

# Initialize default values for all parameters
starting_uk_schools = 25
hyper_growth_factor = 3.0
taper_growth_rate = 0.20
mat_trials_per_quarter = 20
mat_conversion_rate = 0.70
schools_per_mat = 10
mat_annual_churn = 0.10
us_launch_quarter = "Q1 2027"
districts_per_quarter = 15
eal_launch_quarter = "Q1 2028"
initial_eal_learners = 1_000_000
eal_growth_multiplier = 2.0

# Default cost parameters
initial_employees = 3
q4_2025_hires = 4
quarterly_hires = 2
avg_new_hire_salary = 80000
salary_inflation = 0.04
sales_marketing_pct = 0.12
# COGS breakdown
api_cost_year1 = 0.15
api_cost_year2 = 0.10
api_cost_year3 = 0.05
infrastructure_pct = 0.03
support_pct = 0.02
payment_processing_pct = 0.025
other_variable_pct = 0.02
# Fixed costs
office_rent_monthly = 5000
other_opex_monthly = 10000
operational_inflation = 0.05
rd_quarterly = 150000
us_launch_cost = 500000
eal_launch_cost = 250000

# Sidebar inputs - Revenue parameters
if view == "Revenue":
    st.sidebar.header("Revenue Parameters")
    revenue_params = st.sidebar.container()
else:
    revenue_params = st.sidebar.expander("Revenue Parameters", expanded=False)

with revenue_params:
    st.subheader("UK Schools")
    starting_uk_schools = st.number_input("Starting UK schools (Q3 2025)", value=25, min_value=1, step=5, key="uk_schools")
    hyper_growth_factor = st.number_input("Hyper-growth factor (first 2 years)", value=3.0, min_value=1.0, max_value=5.0, step=0.1, key="growth_factor")
    taper_growth_rate = st.number_input("Annual growth rate after 2 years (%)", value=20, min_value=0, max_value=100, step=5, key="taper_rate") / 100
    
    st.subheader("MATs")
    mat_trials_per_quarter = st.number_input("MAT trials per quarter", value=20, min_value=0, step=5, key="mat_trials")
    mat_conversion_rate = st.number_input("MAT conversion rate (%)", value=70, min_value=0, max_value=100, step=5, key="mat_conv") / 100
    schools_per_mat = st.number_input("Schools per MAT", value=10, min_value=1, step=5, key="schools_mat")
    mat_annual_churn = st.number_input("MAT annual churn rate (%)", value=10, min_value=0, max_value=50, step=5, key="mat_churn") / 100
    
    st.subheader("US Districts")
    us_launch_options = ["Q1 2027", "Q2 2027", "Q3 2027"]
    us_launch_quarter = st.selectbox("US launch quarter", us_launch_options, index=0, key="us_launch")
    districts_per_quarter = st.number_input("New districts per quarter (after launch)", value=15, min_value=0, step=5, key="districts_q")
    
    st.subheader("EAL")
    eal_launch_options = ["Q1 2028", "Q2 2028", "Q3 2028"]
    eal_launch_quarter = st.selectbox("EAL launch quarter", eal_launch_options, index=0, key="eal_launch")
    initial_eal_learners = st.number_input("Initial EAL learners (millions)", value=1.0, min_value=0.1, step=0.1, key="eal_learners") * 1_000_000
    eal_growth_multiplier = st.number_input("EAL quarterly growth multiplier", value=2.0, min_value=1.0, step=0.1, key="eal_growth")

# Cost parameters - only in Cash-flow view
if view == "Cash-flow":
    st.sidebar.header("Cost Parameters")
    
    st.sidebar.subheader("Headcount")
    initial_employees = st.sidebar.number_input("Initial employees", value=3, min_value=1, step=1, key="init_emp")
    q4_2025_hires = st.sidebar.number_input("Q4 2025 hires", value=4, min_value=0, step=1, key="q4_hires")
    quarterly_hires = st.sidebar.number_input("Quarterly hires from Q1 2026", value=2, min_value=0, step=1, key="q_hires")
    avg_new_hire_salary = st.sidebar.number_input("Average new hire salary (£k)", value=80, min_value=0, step=10, key="avg_salary") * 1000
    salary_inflation = st.sidebar.number_input("Annual salary inflation (%)", value=4, min_value=0, max_value=20, step=1, key="sal_infl") / 100
    
    st.sidebar.subheader("Variable Costs")
    sales_marketing_pct = st.sidebar.number_input("Sales & Marketing (% of revenue)", value=12, min_value=0, max_value=50, step=1, key="sales_mkt") / 100
    
    st.sidebar.subheader("COGS Breakdown")
    st.sidebar.markdown("##### API/AI Costs (% of revenue)")
    api_cost_year1 = st.sidebar.number_input("Year 1", value=15, min_value=0, max_value=50, step=1, key="api_y1") / 100
    api_cost_year2 = st.sidebar.number_input("Year 2", value=10, min_value=0, max_value=50, step=1, key="api_y2") / 100
    api_cost_year3 = st.sidebar.number_input("Year 3+", value=5, min_value=0, max_value=50, step=1, key="api_y3") / 100
    
    st.sidebar.markdown("##### Other Variable Costs (% of revenue)")
    infrastructure_pct = st.sidebar.number_input("Infrastructure/Hosting", value=3, min_value=0, max_value=20, step=1, key="infra") / 100
    support_pct = st.sidebar.number_input("Customer Support", value=2, min_value=0, max_value=20, step=1, key="support") / 100
    payment_processing_pct = st.sidebar.number_input("Payment Processing", value=2.5, min_value=0.0, max_value=10.0, step=0.5, key="payment") / 100
    other_variable_pct = st.sidebar.number_input("Other Variable", value=2, min_value=0, max_value=20, step=1, key="other_var") / 100
    
    st.sidebar.subheader("Fixed Costs")
    office_rent_monthly = st.sidebar.number_input("Office rent per month (£k)", value=5, min_value=0, step=1, key="office") * 1000
    other_opex_monthly = st.sidebar.number_input("Other OpEx per month (£k)", value=10, min_value=0, step=5, key="opex") * 1000
    operational_inflation = st.sidebar.number_input("Annual operational inflation (%)", value=5, min_value=0, max_value=20, step=1, key="op_infl") / 100
    rd_quarterly = st.sidebar.number_input("R&D per quarter (£k)", value=150, min_value=0, step=50, key="rd") * 1000
    
    st.sidebar.subheader("Expansion Costs")
    us_launch_cost = st.sidebar.number_input("US launch cost (£k)", value=500, min_value=0, step=100, key="us_cost") * 1000
    eal_launch_cost = st.sidebar.number_input("EAL launch cost (£k)", value=250, min_value=0, step=50, key="eal_cost") * 1000

# Helper functions
def quarter_to_date(year_quarter):
    # Handle format "Q1 2027"
    parts = year_quarter.split(" ")
    quarter = int(parts[0][1])  # Extract number from "Q1"
    year = int(parts[1])
    quarter_start_month = (quarter - 1) * 3 + 1
    return pd.Timestamp(f"{year}-{quarter_start_month:02d}-01")

def date_to_quarter(date):
    return f"Q{(date.month - 1) // 3 + 1} {date.year}"

def get_quarter_index(base_date, target_date):
    return (target_date.year - base_date.year) * 4 + (target_date.quarter - base_date.quarter)

# Create timeline
base_date = pd.Timestamp("2025-07-01")  # Q3 2025
us_launch_date = quarter_to_date(us_launch_quarter)
eal_launch_date = quarter_to_date(eal_launch_quarter)

# Determine number of quarters needed
min_quarters = 14
us_quarters_needed = get_quarter_index(base_date, us_launch_date) + 8
eal_quarters_needed = get_quarter_index(base_date, eal_launch_date) + 8
num_quarters = max(min_quarters, us_quarters_needed, eal_quarters_needed)

# Generate quarters
quarters = []
for i in range(num_quarters):
    date = base_date + pd.DateOffset(months=i*3)
    quarters.append(date_to_quarter(date))

# Calculate UK Schools revenue
def calculate_uk_schools(quarters, starting_schools, hyper_growth_factor, taper_growth_rate):
    schools = []
    for i, q in enumerate(quarters):
        if i < 8:  # Hyper-growth phase (first 2 years)
            target = starting_schools * (hyper_growth_factor ** (i / 4))
            schools.append(int(target))
        else:  # Taper phase
            quarterly_growth = (1 + taper_growth_rate) ** 0.25
            prev_schools = schools[-1]
            schools.append(int(prev_schools * quarterly_growth))
    
    # Calculate revenue based on pricing tiers
    revenue = []
    for i, school_count in enumerate(schools):
        year = i // 4 + 1
        if year == 1:
            annual_price = 5000
        elif year == 2:
            annual_price = 10000
        else:
            annual_price = 15000
        quarterly_revenue = (school_count * annual_price) / 4
        revenue.append(quarterly_revenue)
    
    return schools, revenue

# Calculate MAT revenue
def calculate_mat_revenue(quarters, trials_per_q, conversion_rate, schools_per_mat, annual_churn):
    mat_trials = []
    mat_conversions = []
    mat_cohorts = []  # Track when each cohort of MATs converted
    mat_revenue = []
    active_mats = []  # Track total active MATs per quarter
    
    # Convert annual churn to quarterly
    quarterly_churn = 1 - (1 - annual_churn) ** 0.25
    
    for i, q in enumerate(quarters):
        # Apply churn to existing cohorts at the beginning of each quarter (except the first)
        if i > 0:
            for cohort in mat_cohorts:
                cohort['current_mats'] *= (1 - quarterly_churn)
        
        # Trials - double in first quarter
        if i == 0:
            mat_trials.append(trials_per_q * 2)
        else:
            mat_trials.append(trials_per_q)
        
        # Conversions - 2 quarter lag
        if i < 2:
            new_conversions = 0
        else:
            new_conversions = int(mat_trials[i-2] * conversion_rate)
        mat_conversions.append(new_conversions)
        
        # Add new cohort if there are conversions
        if new_conversions > 0:
            mat_cohorts.append({
                'quarter_converted': i,
                'initial_mats': new_conversions,
                'current_mats': new_conversions
            })
        
        # Calculate revenue and count active MATs
        quarterly_revenue = 0
        total_active_mats = 0
        
        for cohort in mat_cohorts:
            total_active_mats += cohort['current_mats']
            
            # Calculate revenue for this cohort based on their tenure
            quarters_since_conversion = i - cohort['quarter_converted']
            year_of_service = quarters_since_conversion // 4 + 1
            
            if year_of_service == 1:
                annual_price = 5000
            elif year_of_service == 2:
                annual_price = 10000
            else:
                annual_price = 15000
            
            # Revenue for this cohort
            cohort_revenue = (cohort['current_mats'] * schools_per_mat * annual_price) / 4
            quarterly_revenue += cohort_revenue
        
        mat_revenue.append(quarterly_revenue)
        active_mats.append(int(total_active_mats))
    
    return mat_trials, mat_conversions, mat_revenue, active_mats

# Calculate US Districts revenue
def calculate_us_revenue(quarters, launch_quarter, districts_per_q):
    us_revenue = []
    us_districts = []
    us_districts_by_cohort = []  # Track when each cohort of districts started
    launch_idx = quarters.index(launch_quarter)
    
    for i, q in enumerate(quarters):
        if i < launch_idx:
            us_districts.append(0)
            us_revenue.append(0)
        elif i == launch_idx:
            us_districts.append(1)
            us_districts_by_cohort.append({'quarter_started': i, 'districts': 1})
            # Year 1 pricing
            us_revenue.append(100000 / 4)  # Quarterly revenue
        else:
            # Add new districts
            new_districts = districts_per_q
            us_districts.append(us_districts[-1] + new_districts)
            us_districts_by_cohort.append({'quarter_started': i, 'districts': new_districts})
            
            # Calculate revenue for each cohort based on their tenure
            quarterly_revenue = 0
            for cohort in us_districts_by_cohort:
                quarters_since_start = i - cohort['quarter_started']
                if quarters_since_start < 4:  # Year 1
                    quarterly_revenue += cohort['districts'] * 100000 / 4
                else:  # Year 2+
                    quarterly_revenue += cohort['districts'] * 150000 / 4
            
            us_revenue.append(quarterly_revenue)
    
    return us_districts, us_revenue

# Calculate EAL revenue
def calculate_eal_revenue(quarters, launch_quarter, initial_learners, growth_multiplier):
    eal_revenue = []
    eal_learners = []
    launch_idx = quarters.index(launch_quarter)
    
    for i, q in enumerate(quarters):
        if i < launch_idx:
            eal_learners.append(0)
            eal_revenue.append(0)
        else:
            quarters_since_launch = i - launch_idx
            learners = initial_learners * (growth_multiplier ** quarters_since_launch)
            eal_learners.append(int(learners))
            
            # £30 per learner per year
            quarterly_revenue = (learners * 30) / 4
            eal_revenue.append(quarterly_revenue)
    
    return eal_learners, eal_revenue

# Calculate all revenue streams
uk_schools, uk_revenue = calculate_uk_schools(quarters, starting_uk_schools, hyper_growth_factor, taper_growth_rate)
mat_trials, mat_conversions, mat_revenue, active_mats = calculate_mat_revenue(quarters, mat_trials_per_quarter, mat_conversion_rate, schools_per_mat, mat_annual_churn)
us_districts, us_revenue = calculate_us_revenue(quarters, us_launch_quarter, districts_per_quarter)
eal_learners, eal_revenue = calculate_eal_revenue(quarters, eal_launch_quarter, initial_eal_learners, eal_growth_multiplier)

# Calculate total quarterly revenue (not ARR) for cost calculations
total_quarterly_revenue = [uk + mat + us + eal for uk, mat, us, eal in zip(uk_revenue, mat_revenue, us_revenue, eal_revenue)]

# Create revenue dataframe with ARR for display
revenue_df = pd.DataFrame({
    'Quarter': quarters,
    'UK Schools': [rev * 4 for rev in uk_revenue],  # Convert to ARR
    'MATs': [rev * 4 for rev in mat_revenue],
    'US Districts': [rev * 4 for rev in us_revenue],
    'EAL': [rev * 4 for rev in eal_revenue],
})
revenue_df['Total'] = revenue_df['UK Schools'] + revenue_df['MATs'] + revenue_df['US Districts'] + revenue_df['EAL']

if view == "Revenue":
    # Display revenue view
    st.header("Revenue Forecast (ARR)")
    
    # Add key metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("UK Schools (Latest)", f"{uk_schools[-1]:,}")
    with col2:
        # Show active MATs accounting for churn
        st.metric("Active MATs", f"{active_mats[-1]:,}")
    with col3:
        st.metric("US Districts (Latest)", f"{us_districts[-1]:,}")
    with col4:
        st.metric("EAL Learners (Latest)", f"{eal_learners[-1]:,}")
    
    # Format and display revenue table
    revenue_display = revenue_df.copy()
    for col in ['UK Schools', 'MATs', 'US Districts', 'EAL', 'Total']:
        revenue_display[col] = revenue_display[col].apply(lambda x: f"£{x:,.0f}")
    
    st.dataframe(revenue_display, use_container_width=True)
    
    # Create stacked area chart
    # Prepare data for stacked area chart
    revenue_long = pd.melt(revenue_df, id_vars=['Quarter'], 
                          value_vars=['UK Schools', 'MATs', 'US Districts', 'EAL'],
                          var_name='Revenue Stream', value_name='ARR')
    
    # Define the order for stacking (bottom to top)
    stream_order = ['UK Schools', 'MATs', 'US Districts', 'EAL']
    
    chart = alt.Chart(revenue_long).mark_area(
        opacity=0.8
    ).encode(
        x=alt.X('Quarter:O', 
                sort=quarters,
                axis=alt.Axis(labelAngle=-45, title='Quarter')),
        y=alt.Y('ARR:Q', 
                axis=alt.Axis(format=',.0f', title='Annual Recurring Revenue (£)'),
                stack='zero'),
        color=alt.Color('Revenue Stream:N',
                       scale=alt.Scale(
                           domain=stream_order,
                           range=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
                       ),
                       legend=alt.Legend(orient='top', title=None)),
        tooltip=[
            alt.Tooltip('Quarter:N'),
            alt.Tooltip('Revenue Stream:N'),
            alt.Tooltip('ARR:Q', format=',.0f', title='ARR (£)')
        ]
    ).properties(
        width=800,
        height=400,
        title='Annual Recurring Revenue by Segment (Stacked)'
    )
    
    st.altair_chart(chart, use_container_width=True)

else:  # Cash-flow view
    st.header("Cash-flow Analysis")
    st.caption("ARR (Annual Recurring Revenue) is shown for reference. All costs and cash calculations are based on actual quarterly revenue.")
    
    # Calculate costs
    # Known salaries for first 4 employees
    known_salaries = [100000, 100000, 90000, 90000]
    
    # Calculate headcount and payroll
    headcount = []
    payroll = []
    
    for i, q in enumerate(quarters):
        if i == 0:  # Q3 2025
            headcount.append(initial_employees)
            # First 3 known salaries
            base_salaries = sum(known_salaries[:initial_employees])
        elif i == 1:  # Q4 2025
            headcount.append(initial_employees + q4_2025_hires)
            # All 4 known salaries + additional at average
            if initial_employees + q4_2025_hires <= 4:
                base_salaries = sum(known_salaries[:initial_employees + q4_2025_hires])
            else:
                base_salaries = sum(known_salaries) + (initial_employees + q4_2025_hires - 4) * avg_new_hire_salary
        else:  # Q1 2026 onwards
            prev_headcount = headcount[-1]
            headcount.append(prev_headcount + quarterly_hires)
            
            # Calculate base salaries
            if prev_headcount <= 4:
                base_salaries = sum(known_salaries[:prev_headcount]) + quarterly_hires * avg_new_hire_salary
            else:
                base_salaries = sum(known_salaries) + (prev_headcount - 4 + quarterly_hires) * avg_new_hire_salary
        
        # Apply salary inflation
        years_elapsed = i / 4
        inflation_multiplier = (1 + salary_inflation) ** years_elapsed
        
        # Quarterly payroll with NI and pension (15%)
        quarterly_payroll = (base_salaries * inflation_multiplier * 1.15) / 4
        payroll.append(quarterly_payroll)
    
    # Calculate COGS with detailed breakdown
    cogs = []
    api_costs = []
    infrastructure_costs = []
    support_costs = []
    payment_costs = []
    other_variable_costs = []
    
    for i, rev in enumerate(total_quarterly_revenue):
        year = i // 4 + 1
        
        # API costs (decreasing over time)
        if year == 1:
            api_rate = api_cost_year1
        elif year == 2:
            api_rate = api_cost_year2
        else:
            api_rate = api_cost_year3
        
        api_cost = rev * api_rate
        api_costs.append(api_cost)
        
        # Other variable costs (constant % of revenue)
        infra_cost = rev * infrastructure_pct
        infrastructure_costs.append(infra_cost)
        
        support_cost = rev * support_pct
        support_costs.append(support_cost)
        
        payment_cost = rev * payment_processing_pct
        payment_costs.append(payment_cost)
        
        other_cost = rev * other_variable_pct
        other_variable_costs.append(other_cost)
        
        # Total COGS
        total_cogs = api_cost + infra_cost + support_cost + payment_cost + other_cost
        cogs.append(total_cogs)
    
    # Calculate gross profit
    gross_profit = [rev - cog for rev, cog in zip(total_quarterly_revenue, cogs)]
    
    # Calculate other costs
    sales_marketing = [rev * sales_marketing_pct for rev in total_quarterly_revenue]
    
    # Fixed costs with inflation
    office_rent = []
    other_opex = []
    rd_costs = []
    
    for i in range(len(quarters)):
        years_elapsed = i / 4
        inflation_multiplier = (1 + operational_inflation) ** years_elapsed
        
        # Quarterly costs (3 months)
        office_rent.append(office_rent_monthly * 3 * inflation_multiplier)
        other_opex.append(other_opex_monthly * 3 * inflation_multiplier)
        rd_costs.append(rd_quarterly)
    
    # Expansion costs
    expansion_costs = []
    us_launch_idx = quarters.index(us_launch_quarter)
    eal_launch_idx = quarters.index(eal_launch_quarter)
    
    for i in range(len(quarters)):
        cost = 0
        if i == us_launch_idx:
            cost += us_launch_cost
        if i == eal_launch_idx:
            cost += eal_launch_cost
        expansion_costs.append(cost)
    
    # Calculate operating cash
    operating_cash = []
    cumulative_cash = []
    
    for i in range(len(quarters)):
        op_cash = (gross_profit[i] - payroll[i] - sales_marketing[i] - 
                  office_rent[i] - other_opex[i] - rd_costs[i] - expansion_costs[i])
        operating_cash.append(op_cash)
        
        if i == 0:
            cumulative_cash.append(op_cash)
        else:
            cumulative_cash.append(cumulative_cash[-1] + op_cash)
    
    # Add key metrics (now that all calculations are done)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        latest_arr = revenue_df['Total'].iloc[-1]
        st.metric("Latest ARR", f"£{latest_arr:,.0f}")
    with col2:
        latest_gross_margin = (gross_profit[-1] / total_quarterly_revenue[-1] * 100) if total_quarterly_revenue[-1] > 0 else 0
        st.metric("Gross Margin", f"{latest_gross_margin:.1f}%")
    with col3:
        latest_burn = operating_cash[-1]
        st.metric("Quarterly Burn/Profit", f"£{latest_burn:,.0f}")
    with col4:
        latest_cash = cumulative_cash[-1]
        st.metric("Cash Position", f"£{latest_cash:,.0f}")
    
    # Create cash-flow dataframe
    cashflow_df = pd.DataFrame({
        'Quarter': quarters,
        'ARR': [rev * 4 for rev in total_quarterly_revenue],  # Display as ARR
        'Quarterly Revenue': total_quarterly_revenue,  # Actual quarterly revenue
        'API/AI Costs': api_costs,
        'Infrastructure': infrastructure_costs,
        'Customer Support': support_costs,
        'Payment Processing': payment_costs,
        'Other Variable': other_variable_costs,
        'Total COGS': cogs,
        'Gross Profit': gross_profit,
        'Payroll': payroll,
        'Sales & Marketing': sales_marketing,
        'Office Rent': office_rent,
        'Other OpEx': other_opex,
        'R&D': rd_costs,
        'Expansion Costs': expansion_costs,
        'Operating Cash': operating_cash,
        'Cumulative Cash': cumulative_cash
    })
    
    # Format and display cash-flow table
    cashflow_display = cashflow_df.copy()
    for col in cashflow_display.columns[1:]:
        cashflow_display[col] = cashflow_display[col].apply(lambda x: f"£{x:,.0f}")
    
    st.dataframe(cashflow_display, use_container_width=True)
    
    # Create cumulative cash chart
    cash_chart = alt.Chart(cashflow_df).mark_area(
        line={'color':'darkblue'},
        color='lightblue',
        opacity=0.7
    ).encode(
        x=alt.X('Quarter:O', 
                sort=quarters,
                axis=alt.Axis(labelAngle=-45)),
        y=alt.Y('Cumulative Cash:Q', 
                axis=alt.Axis(format=',.0f', title='Cumulative Cash Position (£)'),
                scale=alt.Scale(zero=False)),
        tooltip=[
            alt.Tooltip('Quarter:N'),
            alt.Tooltip('Cumulative Cash:Q', format=',.0f', title='Cash Position (£)')
        ]
    ).properties(
        width=800,
        height=400,
        title='Cumulative Cash Position'
    )
    
    st.altair_chart(cash_chart, use_container_width=True)
    
    st.caption("All figures shown are quarterly except ARR. COGS breakdown: API costs decrease from 15% to 5% over 3 years, while other costs remain constant as % of revenue.")
