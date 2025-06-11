"""
Streamlit interactive revenue model for Stylus Education
========================================================

Paste this file into a GitHub repo (e.g. stylus‑forecast) and deploy on
[https://share.streamlit.io](https://share.streamlit.io) – investors get a live playground with sliders.
"""

import streamlit as st
import pandas as pd
import altair as alt

st.set\_page\_config(page\_title="Stylus Forecast Model", layout="wide")
st.title("📈 Stylus Education – Interactive Revenue Forecast")

# ────────────────────────────────────────────

# Sidebar – assumption sliders

# ────────────────────────────────────────────

st.sidebar.header("Adjust assumptions")

# UK schools

start\_uk = st.sidebar.number\_input("Starting UK schools (Q3 ’25)", 10, 1000, 100, step=10)
uk\_growth\_fast = st.sidebar.slider("Initial ‘hyper‑growth’ factor (× over first 2 years)", 1.0, 10.0, 5.0, 0.5)
uk\_growth\_taper = st.sidebar.slider("Annual growth after taper (‑%)", 0.0, 100.0, 20.0, 5.0) / 100

# MATs

trials\_q = st.sidebar.number\_input("MAT trials per quarter (after Q4 ’25)", 1, 100, 25)
conv\_rate = st.sidebar.slider("MAT conversion rate", 0.0, 1.0, 0.70, 0.05)
mat\_multiplier = st.sidebar.number\_input("Average schools per MAT", 5, 25, 10)

# US districts

dist\_add\_q = st.sidebar.number\_input("US districts per quarter (steady‑state)", 1, 50, 15)
dist\_start\_q = st.sidebar.selectbox("US launch quarter", \["2027Q1", "2027Q2", "2027Q3"], index=0)

# EAL market

eal\_start\_q = st.sidebar.selectbox("EAL launch quarter", \["2028Q1", "2028Q2", "2028Q3"], index=0)
eal\_start\_learners = st.sidebar.number\_input("EAL learners at launch (m)", 0.1, 10.0, 1.0, 0.1) \* 1\_000\_000
eal\_quarterly\_multiplier = st.sidebar.slider("EAL learner growth per quarter (×)", 1.0, 4.0, 2.0, 0.25)

# Pricing (annual)

school\_price\_y1 = st.sidebar.number\_input("School price Y1 (£k)", 1, 50, 5) \* 1\_000
school\_price\_y2 = st.sidebar.number\_input("School price Y2 (£k)", 1, 50, 10) \* 1\_000
school\_price\_y3 = st.sidebar.number\_input("School price Y3 (£k)", 1, 50, 15) \* 1\_000

dist\_price\_y1 = st.sidebar.number\_input("District price Y1 (£k)", 10, 500, 100) \* 1\_000
dist\_price\_y2 = st.sidebar.number\_input("District price Y2+ (£k)", 10, 500, 150) \* 1\_000

eal\_price\_annual = 30  # fixed £/learner/year

# ────────────────────────────────────────────

# Helper to equalise list lengths

# ────────────────────────────────────────────

def pad\_or\_trim(seq, n):
"""Return seq exactly length n (pad with zeros or trim)."""
return (seq + \[0] \* n)\[:n]

# ────────────────────────────────────────────

# Build forecast

# ────────────────────────────────────────────

periods = pd.period\_range("2025Q3", periods=12, freq="Q")
labels = periods.astype(str)

# UK school count generator

def build\_uk\_counts():
counts = \[]
half\_targets = \[start\_uk]
\# four half‑years of hyper‑growth, then taper
for i in range(1, 6):
if i <= 4:
target = int(round(start\_uk \* (uk\_growth\_fast \*\* i)))
else:
target = int(round(half\_targets\[-1] \* (1 + uk\_growth\_taper \* 2)))
half\_targets.append(target)
\# 40/60 split into quarters
for h in range(len(half\_targets) - 1):
base, nxt = half\_targets\[h], half\_targets\[h + 1]
delta = nxt - base
counts.extend(\[base + int(round(delta \* 0.4)), nxt])
return counts\[:12]

uk\_counts = build\_uk\_counts()

# Quarterly prices for schools

ann\_price\_map = {
2025: school\_price\_y1,
2026: school\_price\_y2 \* 0.75 + school\_price\_y1 \* 0.25,
2027: school\_price\_y2,
2028: school\_price\_y3,
}
school\_price\_q = \[ann\_price\_map\[p.year] / 4 for p in periods]
uk\_rev = \[c \* p for c, p in zip(uk\_counts, school\_price\_q)]

# MATs

trial\_schedule = \[trials\_q \* 2] + \[trials\_q] \* 11  # first half‑year had 72 → 36/q
mat\_conv = \[0] \* 12
for i in range(2, 12):
mat\_conv\[i] = int(round(trial\_schedule\[i - 2] \* conv\_rate))
mat\_cum = pd.Series(mat\_conv).cumsum()
mat\_price\_q = \[ann\_price\_map\[p.year] \* mat\_multiplier / 4 for p in periods]
mat\_rev = \[c \* p for c, p in zip(mat\_cum, mat\_price\_q)]

# US districts

first\_dist\_idx = labels.tolist().index(dist\_start\_q)
dist\_adds = \[0] \* 12
for i in range(first\_dist\_idx, 12):
dist\_adds\[i] = dist\_add\_q
if i == first\_dist\_idx:
dist\_adds\[i] = 1  # launch with 1 district

dist\_cum = pd.Series(dist\_adds).cumsum()
dist\_price\_q = \[
0 if p.year < 2027 else (dist\_price\_y1 if p.year == 2027 else dist\_price\_y2) / 4
for p in periods
]
dist\_rev = \[c \* p for c, p in zip(dist\_cum, dist\_price\_q)]

# EAL market

first\_eal\_idx = labels.tolist().index(eal\_start\_q)
eal\_learners = \[0] \* 12
if first\_eal\_idx < 12:
learners = eal\_start\_learners
for i in range(first\_eal\_idx, 12):
eal\_learners\[i] = learners
learners \*= eal\_quarterly\_multiplier

eal\_rev = \[n \* (eal\_price\_annual / 4) for n in eal\_learners]

# ────────────────────────────────────────────

# Assemble DataFrame (pad/trim to safety)

# ────────────────────────────────────────────

n = len(labels)
uk\_rev = pad\_or\_trim(uk\_rev, n)
mat\_rev = pad\_or\_trim(mat\_rev, n)
dist\_rev = pad\_or\_trim(dist\_rev, n)
eal\_rev = pad\_or\_trim(eal\_rev, n)

forecast = pd.DataFrame(
{
"UK Schools": uk\_rev,
"MATs": mat\_rev,
"US Districts": dist\_rev,
"EAL": eal\_rev,
},
index=labels,
)
forecast\["Total"] = forecast.sum(axis=1)

# ────────────────────────────────────────────

# Display

# ────────────────────────────────────────────

st.subheader("Quarterly Revenue (£)")
st.dataframe(forecast.style.format("{:.0f}"))

st.subheader("Revenue trajectory")
chart = (
alt.Chart(forecast.reset\_index().melt("index", var\_name="Segment", value\_name="Revenue"))
.mark\_line(point=True)
.encode(
x="index\:N",
y=alt.Y("Revenue\:Q", title="£ per quarter", stack=None),
color="Segment\:N",
)
.properties(width=900, height=400)
)
st.altair\_chart(chart, use\_container\_width=True)

st.caption(
"Adjust the sliders on the left to explore upside & downside scenarios. "
"All figures represent recognised revenue per quarter (not ARR)."
)
