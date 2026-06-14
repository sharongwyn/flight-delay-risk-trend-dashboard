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

# 1. Filter Makro Regional (utk KPI Summary, Heatmap, dan Line Graph Regional)
filtered_time = delay_time[
    (delay_time["year"] == year) &
    (delay_time["region"] == region)
].sort_values("month")

# 2. Filter Mikro Maskapai (utk Line Graph Maskapai untuk komparasi)
filtered_airline = airline_perf[
    (airline_perf["year"] == year) &
    (airline_perf["carrier"] == airline)
].sort_values("month")

# 3. Filter Distribusi Penyebab Regional (utk Pie Chart)
filtered_cause = delay_cause[
    (delay_cause["year"] == year) &
    (delay_cause["region"] == region) &
    (delay_cause["month"] == month)
]

# =====================================================
# KPI SUMMARY 
# =====================================================
st.subheader("📊 Summary Insight")

insight_data = filtered_time[filtered_time["month"] == month]

if not insight_data.empty:
    row = insight_data.iloc[0]

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Flights", int(row["total_flights"]))
    col2.metric("Weather Delay %", f"{round(row['weather_delay_percentage_total'], 2)}%")
    col3.metric("Risk Level", row["risk_level"])
    col4.metric("Weather Share %", f"{round(row['weather_risk_share'], 2)}%")

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
st.subheader("📈 Monthly Trend (Region vs Airline Weather Performance)")

if not filtered_time.empty and not filtered_airline.empty:

    # 1. Ambil rata-rata tren cuaca regional per bulan
    region_line = filtered_time.groupby("month")["weather_delay_percentage_total"].mean().reset_index()

    # 2. Hitung tren murni faktor cuaca milik maskapai pilihan
    airline_line = filtered_airline.copy()
    
    # Hitung rumus: (weather_delay_count / total_flights) * 100
    if "weather_delay_count" in airline_line.columns and "total_flights" in airline_line.columns:
        airline_line["airline_weather_percentage"] = (airline_line["weather_delay_count"] / airline_line["total_flights"]) * 100
    else:
        airline_line["airline_weather_percentage"] = airline_line["delay_percentage"]

    airline_line = airline_line.groupby("month")["airline_weather_percentage"].mean().reset_index()

    fig = go.Figure()

    # Regional Weather Delay %
    fig.add_trace(go.Scatter(
        x=region_line["month"],
        y=region_line["weather_delay_percentage_total"],
        mode="lines+markers",
        name="Regional Weather Delay %",
        line=dict(color="#1f77b4")
    ))

    # Maskapai Pilihan 
    fig.add_trace(go.Scatter(
        x=airline_line["month"],
        y=airline_line["airline_weather_percentage"],
        mode="lines+markers",
        name=f"Airline {airline} Weather Delay %",
        line=dict(color="#a6cee3")
    ))

    fig.add_vline(x=month, line_dash="dash", line_color="black")
    
    fig.update_layout(
        xaxis=dict(tickmode='linear', tick0=1, dtick=1),
        xaxis_title="Month",
        yaxis_title="Percentage (%)",
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
    )

    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Data tren bulanan untuk maskapai atau wilayah ini tidak ditemukan.")

# =====================================================
# AIRLINE PERFORMANCE 
# =====================================================
st.subheader("✈ Airline Performance Ranking")

df_air = airline_perf[
    (airline_perf["year"] == year) &
    (airline_perf["month"] == month)
].copy()

df_air = df_air.groupby("carrier", as_index=False).agg({
    "total_flights": "sum",
    "total_delay_flights": "sum",
    "delay_percentage": "mean"
})

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
        f"Tidak ada data delay cause untuk {region} pada {month}/{year}."
    )

else:
    row = filtered_cause.iloc[0]

    # raw OLAP metrics
    cause_df = pd.DataFrame({
        "cause": ["Carrier", "Weather", "NAS", "Security", "Late Aircraft"],
        "value": [
            row.get("carrier_ct", 0),
            row.get("weather_ct", 0),
            row.get("nas_ct", 0),
            row.get("security_ct", 0),
            row.get("late_aircraft_ct", 0)
        ]
    })

    # total normalization 
    total_value = cause_df["value"].sum()

    if total_value == 0:
        st.info("Tidak ada delay tercatat pada periode ini.")
    else:
        cause_df["percentage"] = (cause_df["value"] / total_value) * 100

        fig_pie = px.pie(
            cause_df,
            names="cause",
            values="percentage",
            title=f"Delay Cause Distribution ({region} - {month}/{year})",
            hole=0.35
        )

        st.plotly_chart(fig_pie, use_container_width=True)

        # dominant factor 
        dominant_row = cause_df.loc[cause_df["value"].idxmax()]

        st.info(
            f"Pada region **{region}** di bulan **{month}/{year}**, "
            f"penyebab delay paling dominan adalah **{dominant_row['cause']}** "
            f"dengan kontribusi sekitar **{dominant_row['percentage']:.2f}%** "
            f"terhadap total delay di region tersebut."
        )

# =====================================================
# PIE CHART - DELAY IMPACT
# =====================================================
st.subheader("⏱ Delay Impact Distribution (Minutes)")

if filtered_cause.empty:
    st.warning(
        f"Tidak ada data delay untuk {region} pada {month}/{year}."
    )

else:
    row = filtered_cause.iloc[0]

    cause_df = pd.DataFrame({
        "cause": ["Carrier", "Weather", "NAS", "Security", "Late Aircraft"],
        "value": [
            row.get("carrier_delay", 0),
            row.get("weather_delay", 0),
            row.get("nas_delay", 0),
            row.get("security_delay", 0),
            row.get("late_aircraft_delay", 0)
        ]
    })

    # total delay minutes
    total_value = cause_df["value"].sum()

    if total_value == 0:
        st.info("Tidak ada delay minutes tercatat pada periode ini.")
    else:
        # convert to percentage
        cause_df["percentage"] = (cause_df["value"] / total_value) * 100

        # pie chart
        fig_pie_delay = px.pie(
            cause_df,
            names="cause",
            values="percentage",
            title=f"Delay Impact Distribution (Minutes) - {region} ({month}/{year})",
            hole=0.35
        )

        st.plotly_chart(fig_pie_delay, use_container_width=True)

        # dominant factor based on delay minutes
        dominant_row = cause_df.loc[cause_df["value"].idxmax()]

        st.info(
            f"Pada region **{region}** di bulan **{month}/{year}**, "
            f"penyebab delay paling berdampak (berdasarkan durasi) adalah **{dominant_row['cause']}** "
            f"dengan total sekitar **{dominant_row['value']:.0f} menit delay** "
            f"({dominant_row['percentage']:.2f}% dari total delay)."
        )
# =====================================================
# STACKED BAR CHART 
# =====================================================
st.subheader("📊 Delay Cause Comparison Across Regions")

stacked_df = delay_cause[
    (delay_cause["year"] == year) &
    (delay_cause["month"] == month)
]

if stacked_df.empty:
    st.warning(f"Tidak ada data stacked bar untuk {month}/{year}.")

else:


    agg_df = stacked_df.groupby("region", as_index=False).agg({
        "carrier_ct": "sum",
        "weather_ct": "sum",
        "nas_ct": "sum",
        "security_ct": "sum",
        "late_aircraft_ct": "sum"
    })


    long_df = pd.melt(
        agg_df,
        id_vars=["region"],
        value_vars=[
            "carrier_ct",
            "weather_ct",
            "nas_ct",
            "security_ct",
            "late_aircraft_ct"
        ],
        var_name="cause",
        value_name="count"
    )

    long_df["cause"] = long_df["cause"].replace({
        "carrier_ct": "Carrier",
        "weather_ct": "Weather",
        "nas_ct": "NAS",
        "security_ct": "Security",
        "late_aircraft_ct": "Late Aircraft"
    })

    fig_stack = px.bar(
        long_df,
        x="region",
        y="count",
        color="cause",
        barmode="stack",
        title=f"Delay Cause Distribution Across Regions ({month}/{year})"
    )

    st.plotly_chart(fig_stack, use_container_width=True)

# =====================================================
# GROUPED BAR CHART - YEAR OVER YEAR CAUSE TREND
# =====================================================
st.write("---")  # Pembatas visual
st.subheader("📊 Year-over-Year Delay Cause Trends")

# Mengambil semua data histori untuk region yang dipilih (tidak difilter berdasarkan tahun tertentu)
yoy_cause_df = delay_cause[delay_cause["region"] == region]

if yoy_cause_df.empty:
    st.warning(f"Tidak ada data tren tahunan (YoY) untuk region {region}.")
else:
    # 1. Agregasikan data berdasarkan tahun untuk menjumlahkan semua metrik count faktor delay
    agg_yoy = yoy_cause_df.groupby("year", as_index=False).agg({
        "carrier_ct": "sum",
        "weather_ct": "sum",
        "nas_ct": "sum",
        "security_ct": "sum",
        "late_aircraft_ct": "sum"
    })

    # 2. Transformasi bentuk dataframe dari wide ke long format agar bisa dibaca Plotly Express
    long_yoy = pd.melt(
        agg_yoy,
        id_vars=["year"],
        value_vars=[
            "carrier_ct",
            "weather_ct",
            "nas_ct",
            "security_ct",
            "late_aircraft_ct"
        ],
        var_name="cause",
        value_name="count"
    )

    # 3. Merapikan penamaan label faktor penyebab agar lebih profesional
    long_yoy["cause"] = long_yoy["cause"].replace({
        "carrier_ct": "Carrier",
        "weather_ct": "Weather",
        "nas_ct": "NAS",
        "security_ct": "Security",
        "late_aircraft_ct": "Late Aircraft"
    })

    # Sort berdasarkan tahun agar urutan sumbu X rapi dari tahun terlama ke terbaru
    long_yoy = long_yoy.sort_values("year")

    # PALET WARNA KONSISTEN SESUAI PERMINTAAN
    COLOR_MAP = {
        "Carrier": "#1f77b4",       # Biru Tua
        "Weather": "#a6cee3",       # Biru Muda
        "NAS": "#d62728",           # Merah
        "Security": "#ff7f0e",      # Oranye / Jingga
        "Late Aircraft": "#2ca02c"  # Hijau
    }

    # 4. Membuat Grouped Bar Chart menggunakan barmode="group" dan color_discrete_map
    fig_grouped = px.bar(
        long_yoy,
        x="year",
        y="count",
        color="cause",
        barmode="group",
        title=f"Perbandingan Kontribusi Faktor Delay dari Tahun ke Tahun (Region: {region})",
        labels={"year": "Tahun", "count": "Jumlah Kejadian Delay", "cause": "Faktor Penyebab"},
        color_discrete_map=COLOR_MAP
    )

    # Memastikan sumbu X menampilkan angka tahun secara diskrit (tidak menjadi format desimal)
    fig_grouped.update_layout(
        xaxis=dict(type='category'),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    st.plotly_chart(fig_grouped, use_container_width=True)

    # =====================================================
    # AUTOMATED INSIGHT GENERATOR FOR YOY TREND (CARRIER & LATE AIRCRAFT)
    # =====================================================
    # Mendapatkan tahun awal dan akhir yang tersedia di data
    latest_year = int(agg_yoy["year"].max())
    earliest_year = int(agg_yoy["year"].min())
    
    latest_data = agg_yoy[agg_yoy["year"] == latest_year].iloc[0]
    earliest_data = agg_yoy[agg_yoy["year"] == earliest_year].iloc[0]

    # Menghitung total delay untuk membandingkan porsi proporsional
    total_earliest = earliest_data[["carrier_ct", "weather_ct", "nas_ct", "security_ct", "late_aircraft_ct"]].sum()
    total_latest = latest_data[["carrier_ct", "weather_ct", "nas_ct", "security_ct", "late_aircraft_ct"]].sum()

    # Hitung rasio kontribusi Carrier Delay
    carrier_share_earliest = (earliest_data["carrier_ct"] / total_earliest) * 100 if total_earliest > 0 else 0
    carrier_share_latest = (latest_data["carrier_ct"] / total_latest) * 100 if total_latest > 0 else 0
    
    # Hitung perubahan total kasus Late Aircraft (Efek Domino)
    late_earliest = earliest_data["late_aircraft_ct"]
    late_latest = latest_data["late_aircraft_ct"]

    # Membuat teks insight operasional maskapai (Carrier)
    if carrier_share_latest < carrier_share_earliest:
        carrier_insight = f"Manajemen internal maskapai (**Carrier Delay**) membaik, di mana porsi kontribusinya menepis dari **{carrier_share_earliest:.1f}%** pada tahun {earliest_year} menjadi **{carrier_share_latest:.1f}%** di tahun {latest_year}."
    else:
        carrier_insight = f"Kendala manajemen internal maskapai (**Carrier Delay**) mengalami peningkatan porsi kontribusi, dari **{carrier_share_earliest:.1f}%** di tahun {earliest_year} naik menjadi **{carrier_share_latest:.1f}%** pada tahun {latest_year}."

    # Membuat teks insight efek domino jadwal (Late Aircraft)
    if late_latest > late_earliest:
        diff_late = late_latest - late_earliest
        late_insight = f"Sementara itu, efek domino keterlambatan pesawat (**Late Aircraft Delay**) membengkak sebanyak **{int(diff_late):,} kasus lebih banyak** dibanding awal periode. Ini mengindikasikan masalah krusial pada penyusunan jadwal (*scheduling*) atau *turnaround time* pesawat yang terlalu ketat di region **{region}**."
    else:
        diff_late = earliest_year - latest_year
        late_insight = f"Kabar baiknya, keterlambatan akibat pesawat yang datang terlambat (**Late Aircraft Delay**) berhasil ditekan, memperkecil risiko efek domino penundaan penerbangan berantai di region **{region}**."

    st.info(
        f"**Analisis Tren  ({earliest_year} - {latest_year}):**  \n"
        f"1. {carrier_insight}  \n"
        f"2. {late_insight}"
    )

# =====================================================
# RAW DATA TABLE
# =====================================================
st.subheader("📋 Summary Data View")
st.dataframe(filtered_time)