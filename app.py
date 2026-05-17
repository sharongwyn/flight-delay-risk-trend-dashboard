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
st.title("✈ Flight Delay Risk & Analysis Dashboard")

# =====================================================
# LOAD DATA
# =====================================================
delay_time = pd.DataFrame(list(db.delay_time_analysis.find()))
airline_perf = pd.DataFrame(list(db.airline_performance.find()))
delay_cause = pd.DataFrame(list(db.delay_cause_distribution.find()))

for df in [delay_time, airline_perf, delay_cause]:
    if "_id" in df.columns:
        df.drop(columns=["_id"], inplace=True)

# =====================================================
# SIDEBAR FILTER
# =====================================================
st.sidebar.header("Filter")

year = st.sidebar.selectbox("Year", sorted(delay_time["year"].unique()))
region = st.sidebar.selectbox("Region", sorted(delay_time["region"].dropna().unique()))
month = st.sidebar.selectbox("Month", sorted(delay_time["month"].unique()))

airline = st.sidebar.selectbox(
    "Airline",
    sorted(airline_perf["carrier"].dropna().unique())
)

# =====================================================
# FILTER DATA
# =====================================================
filtered_time = delay_time[
    (delay_time["year"] == year) &
    (delay_time["region"] == region)
].sort_values("month")

filtered_airline = airline_perf[
    airline_perf["year"] == year
]

filtered_cause = delay_cause[
    (delay_cause["year"] == year) &
    (delay_cause["region"] == region) &
    (delay_cause["month"] == month)
]

# =====================================================
# KPI SUMMARY (RINGKASAN ATAS)
# =====================================================
st.subheader("📊 Summary Insight")

# =====================================================
# FILTER 
# =====================================================
insight_data = filtered_time[filtered_time["month"] == month]

if not insight_data.empty:
    row = insight_data.iloc[0]

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Flights", int(row["total_flights"]))
    col2.metric("Weather Delay %", f"{round(row['weather_delay_percentage_total'], 2)}%")
    col3.metric("Risk Level", row["risk_level"])
    col4.metric("Weather Share %", f"{round(row['weather_risk_share'], 2)}%")

    # Mengubah angka bulan menjadi nama bulan teks agar user-friendly
    import calendar
    month_name = calendar.month_name[int(month)]

    st.info(
        f"Pada tahun **{year}** bulan **{month_name}** di region **{region}**, "
        f"risiko delay cuaca berada di level **{row['risk_level']}** "
        f"dengan kontribusi cuaca sebesar **{round(row['weather_risk_share'], 2)}%** dari seluruh kejadian delay."
    )
else:
    import calendar
    month_name = calendar.month_name[int(month)] if 1 <= int(month) <= 12 else month
    st.warning(f"Data tidak ditemukan untuk Region {region} pada tahun {year} bulan {month_name}.")

# =====================================================
# HEATMAP 
# =====================================================
st.subheader("🔥 Weather Delay Heatmap (Region vs Month)")

if not delay_time.empty:

    heatmap_filtered = delay_time[
        delay_time["year"] == year
    ]

    # agregasi region vs month
    heatmap_df = heatmap_filtered.groupby(
        ["region", "month"]
    )["weather_delay_percentage_total"].mean().reset_index()

    fig_heat = px.density_heatmap(
        heatmap_df,
        x="month",
        y="region",
        z="weather_delay_percentage_total",
        color_continuous_scale="Reds",
        title=f"Weather Delay Hotspot ({year})"
    )

    st.plotly_chart(fig_heat, use_container_width=True)

# =====================================================
# LINE CHART 
# =====================================================
st.subheader("📈 Monthly Trend (Region vs Airline)")

if not filtered_time.empty:

    region_line = filtered_time.groupby("month")["weather_delay_percentage_total"].mean().reset_index()

    airline_line = filtered_airline.copy()
    if "month" not in airline_line.columns:
        airline_line["month"] = year

    airline_line = airline_line.groupby("month")["delay_percentage"].mean().reset_index()

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=region_line["month"],
        y=region_line["weather_delay_percentage_total"],
        mode="lines+markers",
        name="Regional Weather Delay %"
    ))

    fig.add_trace(go.Scatter(
        x=airline_line["month"],
        y=airline_line["delay_percentage"],
        mode="lines+markers",
        name=f"Airline {airline} Delay %"
    ))

    fig.add_vline(x=month, line_dash="dash")

    st.plotly_chart(fig, use_container_width=True)

# =====================================================
# AIRLINE PERFORMANCE 
# =====================================================
st.subheader("✈ Airline Performance Ranking")

# filter sesuai user (year + month)
df_air = airline_perf[
    (airline_perf["year"] == year) &
    (airline_perf["month"] == month)
].copy()

# agregasi safety
df_air = df_air.groupby("carrier", as_index=False).agg({
    "total_flights": "sum",
    "total_delay_flights": "sum",
    "delay_percentage": "mean"
})

# ranking global
df_air = df_air.sort_values("delay_percentage", ascending=True)
df_air["rank"] = range(1, len(df_air) + 1)

top5 = df_air.head(5)

# =====================================================
# BAR CHART
# =====================================================
fig = px.bar(
    top5,
    x="delay_percentage",
    y="carrier",
    orientation="h",
    text="rank",
    title=f"Top 5 Airline Performance ({year}/{month})"
)

st.plotly_chart(fig, use_container_width=True)

# INSIGHT AIRLINE 
user_air = df_air[df_air["carrier"] == airline]

if not user_air.empty:
    r = user_air.iloc[0]

    st.success(
        f"✈ Airline **{airline}** berada di rank **{int(r['rank'])}** "
        f"dengan delay percentage **{round(r['delay_percentage'],2)}%** pada {year}/{month}."
    )
else:
    st.warning("Airline yang dipilih tidak ada di data bulan ini.")

# =====================================================
# PIE CHART
# =====================================================
st.subheader("⚠ Delay Cause Distribution")

if filtered_cause.empty:
    st.warning(
        f"Tidak ada data delay cause untuk {region} pada {month}/{year}. "
        "Silakan cek apakah data sudah ter-aggregate di MongoDB."
    )

else:
    row = filtered_cause.iloc[0]

    cause_df = pd.DataFrame({
        "cause": ["Carrier", "Weather", "NAS", "Security", "Late Aircraft"],
        "value": [
            row["carrier_ct"],
            row["weather_ct"],
            row["nas_ct"],
            row["security_ct"],
            row["late_aircraft_ct"]
        ]
    })

    fig_pie = px.pie(
        cause_df,
        names="cause",
        values="value",
        title=f"Delay Cause Distribution ({region} - {month}/{year})"
    )

    st.plotly_chart(fig_pie, use_container_width=True)

    # INSIGHT ANALYSIS
    total_value = cause_df["value"].sum()

    if total_value == 0:
        st.info("Tidak ada delay tercatat pada periode ini.")
    else:
        dominant_cause = cause_df.loc[cause_df["value"].idxmax(), "cause"]
        dominant_value = cause_df["value"].max()
        dominant_percent = (dominant_value / total_value) * 100

        st.info(
            f"Pada region **{region}** di bulan **{month} tahun {year}**, "
            f"penyebab delay paling dominan adalah **{dominant_cause}** "
            f"dengan kontribusi sekitar **{dominant_percent:.2f}%** terhadap total delay."
        )

# =====================================================
# RAW DATA TABLE
# =====================================================
st.subheader("📋 Summary Data View")
st.dataframe(filtered_time)