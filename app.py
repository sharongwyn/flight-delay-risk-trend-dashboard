import streamlit as st
import pandas as pd
from pymongo import MongoClient
import plotly.express as px
import plotly.graph_objects as go
from scripts.config import MONGO_CONFIG

# =====================================================
# CONNECT MONGODB
# =====================================================
client = MongoClient(MONGO_CONFIG["uri"])
db = client[MONGO_CONFIG["database"]]

st.set_page_config(page_title="Flight Delay Dashboard", layout="wide")

st.title("✈ Flight Delay Risk & Trend Analysis Dashboard")

# =====================================================
# LOAD DATA FROM MONGO (3 COLLECTION ONLY)
# =====================================================
delay_time = pd.DataFrame(list(db.delay_time_analysis.find()))
airline_perf = pd.DataFrame(list(db.airline_performance.find()))
delay_cause = pd.DataFrame(list(db.delay_cause_distribution.find()))

# remove mongo _id biar clean
for df in [delay_time, airline_perf, delay_cause]:
    if "_id" in df.columns:
        df.drop(columns=["_id"], inplace=True)

# =====================================================
# SIDEBAR FILTER (SESUI PROPOSAL)
# =====================================================
st.sidebar.header("Input Parameter")

year = st.sidebar.selectbox("Year", sorted(delay_time["year"].dropna().unique()))
month = st.sidebar.selectbox("Month", sorted(delay_time["month"].dropna().unique()))

region_list = sorted(delay_time["region"].dropna().unique())
region = st.sidebar.selectbox("Region", region_list)

carrier_list = sorted(airline_perf["carrier"].dropna().unique())
carrier = st.sidebar.selectbox("Airline (Carrier)", carrier_list)

# =====================================================
# FILTER DATA
# =====================================================
filtered_time = delay_time[
    (delay_time["year"] == year) &
    (delay_time["region"] == region)
]

filtered_airline = airline_perf[
    (airline_perf["year"] == year) &
    (airline_perf["carrier"] == carrier)
]

filtered_cause = delay_cause[
    (delay_cause["year"] == year) &
    (delay_cause["month"] == month) &
    (delay_cause["region"] == region)
]

