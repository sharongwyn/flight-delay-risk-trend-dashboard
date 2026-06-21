import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pymongo import MongoClient
from scripts.config import MONGO_CONFIG

# PAGE CONFIG
st.set_page_config(
    page_title="Flight Delay Intelligence",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #F8FAFC;
    color: #1E293B;
}
.main .block-container {
    padding: 1.2rem 1.8rem 3rem 1.8rem;
    max-width: 1440px;
    background: #F8FAFC;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: #FFFFFF;
    border-right: 1px solid #E2E8F0;
}
section[data-testid="stSidebar"] .block-container { padding: 1.2rem 1rem; }

/* ── Hero ── */
.hero-banner {
    background: linear-gradient(120deg, #0F2744 0%, #1E3A5F 55%, #0F2744 100%);
    border-radius: 14px; padding: 1.5rem 2rem;
    margin-bottom: 1.2rem; position: relative; overflow: hidden;
}
.hero-banner::after {
    content: '✈'; position: absolute; right: 2rem; top: 50%;
    transform: translateY(-50%) rotate(10deg);
    font-size: 5.5rem; opacity: 0.07; pointer-events: none;
}
.hero-title {
    font-family: 'Space Grotesk', sans-serif; font-size: 1.7rem; font-weight: 700;
    color: #F0F9FF; margin: 0 0 0.2rem; letter-spacing: -0.025em;
}
.hero-sub { font-size: 0.75rem; color: #7DD3FC; margin: 0;
            font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase; }
.hero-dot { color: #38BDF8; margin: 0 5px; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 2px; background: #E2E8F0; border-radius: 10px;
    padding: 3px; border: 1px solid #CBD5E1; margin-bottom: 0.3rem;
}
.stTabs [data-baseweb="tab"] {
    background: transparent; border-radius: 7px; color: #64748B;
    font-weight: 500; font-size: 0.84rem; padding: 0.42rem 1.1rem;
    border: none; transition: all 0.15s;
}
.stTabs [aria-selected="true"] { background: #0F2744 !important; color: #7DD3FC !important; }
.stTabs [data-baseweb="tab"]:hover:not([aria-selected="true"]) { background: #CBD5E1; color: #1E293B; }

/* ── Sidebar section label ── */
.sb-section {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.72rem; font-weight: 700; color: #0F2744;
    text-transform: uppercase; letter-spacing: 0.1em;
    background: #EFF6FF; border-left: 3px solid #0EA5E9;
    padding: 5px 10px; border-radius: 0 6px 6px 0;
    margin: 0.8rem 0 0.5rem;
}
.sb-note {
    font-size: 0.7rem; color: #94A3B8; line-height: 1.5;
    background: #F8FAFC; border: 1px solid #E2E8F0;
    border-radius: 6px; padding: 6px 9px; margin-bottom: 0.4rem;
}

/* ── Tab-local filter panel ── */
.tab-filter-panel {
    background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px;
    padding: 0.9rem 1.2rem 0.7rem; margin-bottom: 1.1rem;
    box-shadow: 0 1px 3px rgba(15,39,68,0.05);
}
.tab-filter-title {
    font-family: 'Space Grotesk', sans-serif; font-size: 0.72rem; font-weight: 700;
    color: #0F2744; text-transform: uppercase; letter-spacing: 0.09em;
    margin-bottom: 0.6rem; display: flex; align-items: center; gap: 6px;
}
.tab-filter-note {
    font-size: 0.7rem; color: #94A3B8; margin-bottom: 0.5rem; font-style: italic;
}

/* ── Active-filter pill strip ── */
.pill-strip { display: flex; flex-wrap: wrap; gap: 5px; margin-bottom: 0.9rem; align-items: center; }
.pill { background: #EFF6FF; border: 1px solid #BAE6FD; color: #0369A1;
        border-radius: 20px; font-size: 0.68rem; font-weight: 600;
        padding: 2px 9px; white-space: nowrap; }
.pill-scope { background: #F0FDF4; border: 1px solid #BBF7D0; color: #15803D;
              border-radius: 20px; font-size: 0.68rem; font-weight: 700;
              padding: 2px 9px; white-space: nowrap; }
.pill-label { font-size: 0.67rem; font-weight: 700; color: #94A3B8;
              text-transform: uppercase; letter-spacing: 0.08em; }

/* ── KPI Cards ── */
.kpi-grid { display: grid; gap: 0.75rem; margin-bottom: 1.2rem; }
.kpi-card {
    background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px;
    padding: 0.95rem 1.1rem 0.85rem; position: relative; overflow: hidden;
    box-shadow: 0 1px 3px rgba(15,39,68,0.05);
    transition: box-shadow 0.18s, transform 0.15s;
}
.kpi-card:hover { box-shadow: 0 4px 12px rgba(15,39,68,0.09); transform: translateY(-2px); }
.kpi-accent { position: absolute; left:0; top:0; bottom:0; width: 4px; border-radius: 4px 0 0 4px; }
.kpi-label { font-size: 0.66rem; font-weight: 700; color: #94A3B8;
             text-transform: uppercase; letter-spacing: 0.09em; margin-bottom: 0.28rem; }
.kpi-value { font-family: 'Space Grotesk', sans-serif; font-size: 1.55rem;
             font-weight: 700; color: #0F172A; line-height: 1; margin-bottom: 0.15rem; }
.kpi-sub   { font-size: 0.72rem; color: #94A3B8; }
.card-high   { border-left: 4px solid #DC2626; background: linear-gradient(135deg,#FFF5F5,#FFF); }
.card-medium { border-left: 4px solid #D97706; background: linear-gradient(135deg,#FFFBEB,#FFF); }
.card-low    { border-left: 4px solid #16A34A; background: linear-gradient(135deg,#F0FDF4,#FFF); }
.kpi-badge { display:inline-block; padding:2px 8px; border-radius:20px;
             font-size:0.66rem; font-weight:700; margin-left:5px; vertical-align:middle; }
.badge-high   { background:#FEE2E2; color:#B91C1C; }
.badge-medium { background:#FEF3C7; color:#92400E; }
.badge-low    { background:#DCFCE7; color:#15803D; }

/* ── Section Header ── */
.sec-hdr { display:flex; align-items:center; gap:7px; margin:1.1rem 0 0.5rem; }
.sec-hdr-dot { width:6px; height:6px; border-radius:50%; background:#0EA5E9; flex-shrink:0; }
.sec-hdr-text { font-family:'Space Grotesk',sans-serif; font-size:0.88rem;
                font-weight:600; color:#1E293B; margin:0; }

/* ── Insight Box ── */
.insight-box {
    background: #EFF6FF; border: 1px solid #BAE6FD; border-left: 4px solid #0EA5E9;
    border-radius: 0 10px 10px 0; padding: 0.8rem 1.1rem; margin: 0.2rem 0 1rem;
    font-size: 0.84rem; color: #0C4A6E; line-height: 1.65;
}
.insight-tag { font-size: 0.65rem; font-weight: 700; color: #0284C7;
               text-transform: uppercase; letter-spacing: 0.09em;
               display: block; margin-bottom: 0.25rem; }

/* ── No-data ── */
.no-data { background: #FFFBEB; border: 1px solid #FDE68A; border-radius: 10px;
           padding: 1.2rem 1.5rem; font-size: 0.875rem; color: #92400E; text-align: center; }

/* ── Streamlit overrides ── */
.stCheckbox { margin-bottom: 0.05rem !important; }
.stMultiSelect [data-baseweb="tag"] { background: #0F2744 !important; }
.stButton > button {
    background: linear-gradient(135deg, #0F2744 0%, #1D4ED8 100%);
    color: #fff; border: none; border-radius: 8px; font-weight: 600;
    font-size: 0.84rem; padding: 0.45rem 1.2rem; transition: all 0.18s;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #1D4ED8 0%, #3B82F6 100%);
    box-shadow: 0 4px 12px rgba(29,78,216,0.22); transform: translateY(-1px);
}
.stDataFrame { border-radius: 10px; overflow: hidden; }
hr { border-color: #E2E8F0; margin: 1.2rem 0; }
</style>
""", unsafe_allow_html=True)

# MONGODB
@st.cache_resource
def get_db():
    client = MongoClient(MONGO_CONFIG["uri"])
    return client[MONGO_CONFIG["database"]]

db = get_db()

@st.cache_data(ttl=300)
def load_delay_time():
    return pd.DataFrame(list(db.delay_time_analysis.find({}, {"_id": 0})))

@st.cache_data(ttl=300)
def load_airline_perf():
    return pd.DataFrame(list(db.airline_performance.find({}, {"_id": 0})))

@st.cache_data(ttl=300)
def load_delay_cause():
    return pd.DataFrame(list(db.delay_cause_distribution.find({}, {"_id": 0})))

# CHART CONSTANTS
BG      = "#FFFFFF"
PLOT_BG = "#F8FAFC"
GRID    = "#E2E8F0"
TXT     = "#64748B"
TITLE_C = "#1E293B"
ACCENT  = "#0EA5E9"
PALETTE = ["#0EA5E9","#6366F1","#10B981","#F59E0B","#EC4899","#8B5CF6",
           "#14B8A6","#F97316","#A855F7","#EF4444"]
CAUSE_C = ["#0EA5E9","#F59E0B","#10B981","#EC4899","#6366F1"]

MONTHS   = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
            7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}
MON_LIST = [MONTHS[i] for i in range(1, 13)]

def base_layout(title="", height=360):
    return dict(
        title=dict(text=title, font=dict(color=TITLE_C, size=12, family="Space Grotesk"),
                   x=0, xanchor="left", pad=dict(l=4)),
        paper_bgcolor=BG, plot_bgcolor=PLOT_BG,
        font=dict(color=TXT, family="Inter", size=11),
        height=height, margin=dict(l=10, r=10, t=42, b=10),
        xaxis=dict(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID, tickfont=dict(color=TXT)),
        yaxis=dict(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID, tickfont=dict(color=TXT)),
        hovermode="closest",
    )

DEFAULT_LEGEND = dict(
    bgcolor="rgba(255,255,255,0.85)", bordercolor=GRID, borderwidth=1,
    font=dict(size=10, color=TXT),
)

def cat_vline(fig, x_val, color="#F59E0B", label=None):
    fig.add_shape(type="line", xref="x", yref="paper",
                  x0=x_val, x1=x_val, y0=0, y1=1,
                  line=dict(color=color, width=1.5, dash="dash"))
    if label:
        fig.add_annotation(xref="x", yref="paper", x=x_val, y=0.97,
                           text=label, showarrow=False,
                           font=dict(color=color, size=10),
                           xanchor="left", xshift=6)

def sec(title):
    st.markdown(
        f'<div class="sec-hdr"><div class="sec-hdr-dot"></div>'
        f'<p class="sec-hdr-text">{title}</p></div>',
        unsafe_allow_html=True)

def pill_strip(global_filters: dict, local_filters: dict = None):
    pills = ""
    for label, vals in global_filters.items():
        for v in vals:
            pills += f'<span class="pill">{v}</span>'
    local_pills = ""
    if local_filters:
        for label, vals in local_filters.items():
            for v in vals:
                local_pills += f'<span class="pill-scope">{v}</span>'
    content = ""
    if pills:
        content += f'<span class="pill-label">Global:</span>{pills}'
    if local_pills:
        content += f'&nbsp;&nbsp;<span class="pill-label">This tab:</span>{local_pills}'
    if content:
        st.markdown(f'<div class="pill-strip">{content}</div>', unsafe_allow_html=True)

def no_data():
    st.markdown(
        '<div class="no-data">⚠️ No data matches the selected filters. Try selecting more options.</div>',
        unsafe_allow_html=True)

def make_pie(labs, vals, title):
    fig = go.Figure(go.Pie(
        labels=labs, values=vals, hole=0.5,
        marker=dict(colors=CAUSE_C, line=dict(color="#FFFFFF", width=2)),
        textinfo="label+percent", textfont=dict(size=10, color="#1E293B"),
        hovertemplate="<b>%{label}</b><br>%{value:,.0f} (%{percent})<extra></extra>",
        sort=False,
    ))
    fig.update_layout(
        title=dict(text=title, font=dict(color=TITLE_C, size=12, family="Space Grotesk"),
                   x=0, xanchor="left"),
        paper_bgcolor=BG, plot_bgcolor=PLOT_BG,
        font=dict(color=TXT, family="Inter", size=11),
        height=300, margin=dict(l=10, r=10, t=42, b=10),
        showlegend=True,
        legend=dict(orientation="v", x=1.02, y=0.5,
                    bgcolor="rgba(255,255,255,0.85)", bordercolor=GRID, borderwidth=1,
                    font=dict(size=10, color=TXT)),
    )
    return fig

# LOAD ALL DATA
df_dt = load_delay_time()
df_ap = load_airline_perf()
df_dc = load_delay_cause()

# SIDEBAR — GLOBAL FILTERS (Year + Month)
with st.sidebar:
    st.markdown("""
    <div style="font-family:'Space Grotesk',sans-serif;font-size:1.05rem;font-weight:700;
    color:#0F2744;margin-bottom:0.15rem;">Global Filters</div>
    """, unsafe_allow_html=True)

    all_years = sorted(set(
        list(df_dt["year"].dropna().unique() if not df_dt.empty else []) +
        list(df_ap["year"].dropna().unique() if not df_ap.empty else []) +
        list(df_dc["year"].dropna().unique() if not df_dc.empty else [])
    ), reverse=True)

    st.markdown('<div class="sb-section">📅 Year</div>', unsafe_allow_html=True)
    sel_years = []
    for y in all_years:
        if st.checkbox(str(int(y)), value=(y == all_years[0]), key=f"yr_{y}"):
            sel_years.append(int(y))

    st.markdown('<div class="sb-section">🗓️ Month</div>', unsafe_allow_html=True)
    col_m1, col_m2 = st.columns(2)
    sel_months = []
    for i, (num, name) in enumerate(MONTHS.items()):
        col = col_m1 if i < 6 else col_m2
        if col.checkbox(name, value=True, key=f"mo_{num}"):
            sel_months.append(num)

    st.markdown("---")

# Fallback guards
if not sel_years:  sel_years  = [int(all_years[0])] if all_years else []
if not sel_months: sel_months = list(range(1, 13))

# HERO
yrs_str = ", ".join(str(y) for y in sorted(sel_years))
mo_str  = ", ".join(MONTHS[m] for m in sorted(sel_months)[:4])
if len(sel_months) > 4: mo_str += f" +{len(sel_months)-4} more"
st.markdown(f"""
<div class="hero-banner">
  <div class="hero-title">Flight Delay Intelligence</div>
  <div class="hero-sub">
    U.S. Airport Delay Analysis
    <span class="hero-dot">·</span>OLAP
    <span class="hero-dot">·</span>MySQL × MongoDB
  </div>
</div>
""", unsafe_allow_html=True)

# TABS
tab1, tab2, tab3 = st.tabs([
    "🌦️  Weather Risk & Seasonal Trends",
    "🏆  Airline Performance",
    "📊  Delay Cause Distribution",
])

# TAB 1 — WEATHER RISK
# Tab-local filter: Region
with tab1:
    if df_dt.empty:
        st.warning("No data in `delay_time_analysis`.")
        st.stop()

    all_regions_t1 = sorted(df_dt["region"].dropna().unique())

    # Tab-local filter: Region ──
    st.markdown("""
    <div class="tab-filter-panel">
      <div class="tab-filter-title">🗺️ Region Filter <span style="font-weight:400;color:#94A3B8;font-size:0.68rem;text-transform:none;letter-spacing:0">&nbsp;</span></div>
      <div class="tab-filter-note">Select one or more regions to include in the charts below.</div>
    </div>
    """, unsafe_allow_html=True)

    reg_cols = st.columns(len(all_regions_t1))
    sel_regions_t1 = []
    for i, reg in enumerate(all_regions_t1):
        if reg_cols[i].checkbox(reg, value=True, key=f"t1_reg_{reg}"):
            sel_regions_t1.append(reg)

    if not sel_regions_t1:
        sel_regions_t1 = all_regions_t1

    st.markdown("<div style='margin-bottom:0.8rem'></div>", unsafe_allow_html=True)

    pill_strip(
        {"Years": [str(y) for y in sorted(sel_years)],
         "Months": [MONTHS[m] for m in sorted(sel_months)]},
        {"Regions": sorted(sel_regions_t1)},
    )

    # Apply filters
    df1 = df_dt[
        df_dt["year"].isin(sel_years) &
        df_dt["month"].isin(sel_months) &
        df_dt["region"].isin(sel_regions_t1)
    ].copy()

    if df1.empty:
        no_data()
    else:
        # KPIs
        tot_f   = int(df1["total_flights"].sum())
        tot_wd  = int(df1["weather_delay_count"].sum())
        avg_pct = float(df1["weather_delay_percentage_total"].mean())
        avg_rs  = float(df1["weather_risk_share"].mean())
        avg_dur = float(df1["avg_delay"].mean())

        risk_mode    = df1["risk_level"].str.capitalize().mode()
        risk_overall = risk_mode.iloc[0] if not risk_mode.empty else "Low"
        risk_card    = {"High":"card-high","Medium":"card-medium","Low":"card-low"}.get(risk_overall,"card-low")
        badge_cls    = f"badge-{risk_overall.lower()}"
        acc_color    = {"High":"#DC2626","Medium":"#D97706","Low":"#16A34A"}.get(risk_overall,"#16A34A")

        y_label   = ", ".join(str(y) for y in sorted(sel_years))
        reg_label = ", ".join(sorted(sel_regions_t1)[:2])
        if len(sel_regions_t1) > 2: reg_label += f" +{len(sel_regions_t1)-2}"

        st.markdown(f"""
        <div class="kpi-grid" style="grid-template-columns:repeat(5,1fr);">
          <div class="kpi-card {risk_card}">
            <div class="kpi-accent" style="background:{acc_color}"></div>
            <div class="kpi-label">Overall Risk Level</div>
            <div class="kpi-value" style="font-size:1.1rem;line-height:1.2">{y_label}</div>
            <div class="kpi-sub">{reg_label}&nbsp;<span class="kpi-badge {badge_cls}">{risk_overall}</span></div>
          </div>
          <div class="kpi-card">
            <div class="kpi-accent" style="background:#0EA5E9"></div>
            <div class="kpi-label">Avg Weather Delay Prob.</div>
            <div class="kpi-value">{avg_pct:.2f}%</div>
            <div class="kpi-sub">of all flights affected</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-accent" style="background:#6366F1"></div>
            <div class="kpi-label">Avg Weather Risk Share</div>
            <div class="kpi-value">{avg_rs:.1f}%</div>
            <div class="kpi-sub">among delayed flights</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-accent" style="background:#10B981"></div>
            <div class="kpi-label">Avg Delay Duration</div>
            <div class="kpi-value">{avg_dur:.0f} min</div>
            <div class="kpi-sub">per weather-delayed flight</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-accent" style="background:#F59E0B"></div>
            <div class="kpi-label">Total Flights</div>
            <div class="kpi-value">{tot_f:,}</div>
            <div class="kpi-sub">{tot_wd:,} weather delays</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        mo_label = ", ".join(MONTHS[m] for m in sorted(sel_months)[:3])
        if len(sel_months) > 3: mo_label += f" +{len(sel_months)-3}"
        st.markdown(f"""
        <div class="insight-box">
          <span class="insight-tag">💡 Auto Insight</span>
          Across <strong>{", ".join(str(y) for y in sorted(sel_years))}</strong>
          ({mo_label}) in the <strong>{reg_label}</strong> region(s), the average weather delay
          probability is <strong>{avg_pct:.2f}%</strong>. Weather accounts for
          <strong>{avg_rs:.1f}%</strong> of all delays, with typical disruptions of
          <strong>{avg_dur:.0f} minutes</strong>. Dominant risk tier: <strong>{risk_overall}</strong>.
        </div>
        """, unsafe_allow_html=True)

        y_str = "/".join(str(y) for y in sorted(sel_years))

        # Row 1: Heatmap | Line
        l1, r1 = st.columns([1.1, 1], gap="medium")

        with l1:
            sec("Regional Heatmap — Weather Risk by Month")
            piv = df1.pivot_table(
                index="region", columns="month",
                values="weather_delay_percentage_total", aggfunc="mean",
            ).reindex(columns=range(1, 13))
            piv.columns = MON_LIST
            for col in MON_LIST:
                m_num = [k for k,v in MONTHS.items() if v==col][0]
                if m_num not in sel_months:
                    piv[col] = None

            fig_hm = go.Figure(go.Heatmap(
                z=piv.values, x=MON_LIST, y=list(piv.index),
                colorscale=[[0,"#EFF6FF"],[0.33,"#BAE6FD"],[0.66,"#F59E0B"],[1,"#DC2626"]],
                showscale=True,
                colorbar=dict(thickness=10, len=0.75,
                              tickfont=dict(color=TXT, size=9),
                              title=dict(text="%", font=dict(color=TXT, size=10))),
                hovertemplate="<b>%{y}</b> · %{x}<br>Risk: <b>%{z:.2f}%</b><extra></extra>",
            ))
            for m_sel in sel_months:
                xi = MON_LIST.index(MONTHS[m_sel])
                fig_hm.add_shape(type="rect",
                    x0=xi-0.5, x1=xi+0.5, y0=-0.5, y1=len(piv.index)-0.5,
                    line=dict(color="#0EA5E9", width=1, dash="dot"),
                    fillcolor="rgba(14,165,233,0.04)")
            ly = base_layout(f"Weather Delay % · {y_str}", height=300)
            ly["xaxis"]["side"] = "bottom"
            ly["margin"]["b"] = 20
            ly["legend"] = DEFAULT_LEGEND
            fig_hm.update_layout(**ly)
            st.plotly_chart(fig_hm, use_container_width=True, config={"displayModeBar": False})

        with r1:
            sec("Seasonal Trend — Monthly Line by Region")
            trend1  = df1.groupby(["month","region"])["weather_delay_percentage_total"].mean().reset_index()
            nat1    = df1.groupby("month")["weather_delay_percentage_total"].mean().reset_index()

            fig_ln = go.Figure()
            fig_ln.add_trace(go.Scatter(
                x=[MONTHS[m] for m in nat1["month"]],
                y=nat1["weather_delay_percentage_total"],
                mode="lines", name="All-Region Avg",
                line=dict(color="#CBD5E1", width=1.8, dash="dot"),
                hovertemplate="Avg · %{x}: <b>%{y:.2f}%</b><extra></extra>",
            ))
            for i, reg in enumerate(sorted(sel_regions_t1)):
                sub = trend1[trend1["region"] == reg].sort_values("month")
                if sub.empty: continue
                fig_ln.add_trace(go.Scatter(
                    x=[MONTHS[m] for m in sub["month"]],
                    y=sub["weather_delay_percentage_total"],
                    mode="lines+markers", name=reg,
                    line=dict(color=PALETTE[i % len(PALETTE)], width=2.2),
                    marker=dict(size=5, line=dict(color="#FFFFFF", width=1.2)),
                    hovertemplate=f"{reg} · %{{x}}: <b>%{{y:.2f}}%</b><extra></extra>",
                ))
            ly2 = base_layout(f"Weather Delay Probability · {y_str}", height=300)
            ly2["yaxis"]["ticksuffix"] = "%"
            ly2["xaxis"]["categoryorder"] = "array"
            ly2["xaxis"]["categoryarray"] = MON_LIST
            ly2["hovermode"] = "x unified"
            ly2["legend"] = DEFAULT_LEGEND
            fig_ln.update_layout(**ly2)
            st.plotly_chart(fig_ln, use_container_width=True, config={"displayModeBar": False})

        # Row 2: Risk bar | Donut 
        l2, r2 = st.columns([1.4, 1], gap="medium")

        with l2:
            sec("Monthly Risk Profile — Grouped by Risk Level")
            df1b = df1.copy()
            df1b["risk_cap"] = df1b["risk_level"].str.capitalize()
            df1b["mon_name"] = df1b["month"].map(MONTHS)
            rb_agg = df1b.groupby(["mon_name","risk_cap"])["weather_delay_percentage_total"].mean().reset_index()
            RCOLS  = {"Low":"#10B981","Medium":"#F59E0B","High":"#DC2626"}
            fig_rb = go.Figure()
            for rcat, rcol in RCOLS.items():
                sub = rb_agg[rb_agg["risk_cap"] == rcat]
                fig_rb.add_trace(go.Bar(
                    x=sub["mon_name"], y=sub["weather_delay_percentage_total"],
                    name=rcat, marker_color=rcol, opacity=0.88,
                    hovertemplate=f"<b>{rcat}</b> · %{{x}}: <b>%{{y:.2f}}%</b><extra></extra>",
                ))
            ly3 = base_layout(f"Delay % by Month & Risk · {y_str}", height=290)
            ly3["barmode"] = "group"
            ly3["yaxis"]["ticksuffix"] = "%"
            ly3["xaxis"]["categoryorder"] = "array"
            ly3["xaxis"]["categoryarray"] = MON_LIST
            ly3["legend"] = DEFAULT_LEGEND
            fig_rb.update_layout(**ly3)
            st.plotly_chart(fig_rb, use_container_width=True, config={"displayModeBar": False})

        with r2:
            sec("Risk Level Distribution")
            df1c = df1.copy()
            df1c["risk_cap"] = df1c["risk_level"].str.capitalize()
            rc    = df1c["risk_cap"].value_counts()
            order = [o for o in ["Low","Medium","High"] if o in rc.index]
            rc    = rc.reindex(order)
            fig_dn = go.Figure(go.Pie(
                labels=rc.index, values=rc.values, hole=0.56,
                marker=dict(colors=["#10B981","#F59E0B","#DC2626"],
                            line=dict(color="#FFFFFF", width=2)),
                textinfo="label+percent", textfont=dict(size=10, color="#1E293B"),
                hovertemplate="<b>%{label}</b>: %{value} records (%{percent})<extra></extra>",
                sort=False,
            ))
            ly4 = base_layout(f"Risk Spread · {y_str}", height=290)
            ly4["showlegend"] = False
            ly4["annotations"] = [dict(
                text=f"<b>{y_str}</b>", x=0.5, y=0.5, showarrow=False,
                font=dict(size=13, color="#0F172A", family="Space Grotesk"),
            )]
            fig_dn.update_layout(**ly4)
            st.plotly_chart(fig_dn, use_container_width=True, config={"displayModeBar": False})

        # Year-over-Year (only when multiple years selected)
        if len(sel_years) > 1:
            sec("Year-over-Year — Avg Weather Delay % by Region")
            yoy1 = df1.groupby(["year","month"])["weather_delay_percentage_total"].mean().reset_index()
            fig_yoy = go.Figure()
            for i, yr in enumerate(sorted(sel_years)):
                sub = yoy1[yoy1["year"] == yr].sort_values("month")
                fig_yoy.add_trace(go.Scatter(
                    x=[MONTHS[m] for m in sub["month"]],
                    y=sub["weather_delay_percentage_total"],
                    mode="lines+markers", name=str(int(yr)),
                    line=dict(color=PALETTE[i % len(PALETTE)], width=2.2),
                    marker=dict(size=5, line=dict(color="#FFFFFF", width=1)),
                    hovertemplate=f"<b>{int(yr)}</b> · %{{x}}: <b>%{{y:.2f}}%</b><extra></extra>",
                ))
            ly_yoy = base_layout("Year-over-Year Weather Delay Trend", height=300)
            ly_yoy["yaxis"]["ticksuffix"] = "%"
            ly_yoy["xaxis"]["categoryorder"] = "array"
            ly_yoy["xaxis"]["categoryarray"] = MON_LIST
            ly_yoy["hovermode"] = "x unified"
            ly_yoy["legend"] = DEFAULT_LEGEND
            fig_yoy.update_layout(**ly_yoy)
            st.plotly_chart(fig_yoy, use_container_width=True, config={"displayModeBar": False})


# TAB 2 — AIRLINE PERFORMANCE
# Tab-local filter: Airline
with tab2:
    if df_ap.empty:
        st.warning("No data in `airline_performance`.")
        st.stop()

    all_carriers = sorted(df_ap["carrier"].dropna().unique().tolist())

    # Tab-local filter: Airline 
    st.markdown("""
    <div class="tab-filter-panel">
      <div class="tab-filter-title">✈️ Airline Filter <span style="font-weight:400;color:#94A3B8;font-size:0.68rem;text-transform:none;letter-spacing:0">&nbsp;</span></div>
      <div class="tab-filter-note">Select which airlines to include.</div>
    </div>
    """, unsafe_allow_html=True)

    # Build label map: "AA — American Airlines"
    carrier_labels = {}
    for code in all_carriers:
        row = df_ap[df_ap["carrier"] == code]["carrier_name"].values
        carrier_labels[code] = f"{code} — {row[0]}" if len(row) else code

    sel_carrier_labels = st.multiselect(
        "Airlines",
        options=[carrier_labels[c] for c in all_carriers],
        default=[carrier_labels[c] for c in all_carriers],
        key="t2_airlines",
        label_visibility="collapsed",
    )
    # Map back to codes
    label_to_code = {v: k for k, v in carrier_labels.items()}
    sel_carriers = [label_to_code[l] for l in sel_carrier_labels if l in label_to_code]
    if not sel_carriers: sel_carriers = all_carriers

    pill_strip(
        {"Years": [str(y) for y in sorted(sel_years)],
         "Months": [MONTHS[m] for m in sorted(sel_months)]},
        {"Airlines": sorted(sel_carriers)},
    )

    df2 = df_ap[
        df_ap["year"].isin(sel_years) &
        df_ap["month"].isin(sel_months) &
        df_ap["carrier"].isin(sel_carriers)
    ].copy()

    if df2.empty:
        no_data()
    else:
        # Aggregate for KPIs
        kpi2 = df2.groupby("carrier").agg(
            carrier_name=("carrier_name","first"),
            total_flights=("total_flights","sum"),
            total_delay_flights=("total_delay_flights","sum"),
            avg_delay=("avg_delay","mean"),
        ).reset_index()
        kpi2["delay_pct"] = kpi2["total_delay_flights"] / kpi2["total_flights"].replace(0,1) * 100
        kpi2 = kpi2.sort_values("delay_pct")

        best   = kpi2.iloc[0]
        worst  = kpi2.iloc[-1]
        avg_p  = float(kpi2["delay_pct"].mean())
        tot_f2 = int(kpi2["total_flights"].sum())
        n_air  = len(kpi2)
        y_str2 = "/".join(str(y) for y in sorted(sel_years))

        st.markdown(f"""
        <div class="kpi-grid" style="grid-template-columns:repeat(5,1fr);">
          <div class="kpi-card card-low">
            <div class="kpi-accent" style="background:#16A34A"></div>
            <div class="kpi-label">Best Performer</div>
            <div class="kpi-value" style="font-size:0.92rem;line-height:1.3">{best['carrier_name']}</div>
            <div class="kpi-sub">{best['delay_pct']:.1f}% delay rate</div>
          </div>
          <div class="kpi-card card-high">
            <div class="kpi-accent" style="background:#DC2626"></div>
            <div class="kpi-label">Worst Performer</div>
            <div class="kpi-value" style="font-size:0.92rem;line-height:1.3">{worst['carrier_name']}</div>
            <div class="kpi-sub">{worst['delay_pct']:.1f}% delay rate</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-accent" style="background:#0EA5E9"></div>
            <div class="kpi-label">Industry Avg Delay</div>
            <div class="kpi-value">{avg_p:.1f}%</div>
            <div class="kpi-sub">{y_str2}</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-accent" style="background:#6366F1"></div>
            <div class="kpi-label">Airlines Tracked</div>
            <div class="kpi-value">{n_air}</div>
            <div class="kpi-sub">carriers selected</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-accent" style="background:#F59E0B"></div>
            <div class="kpi-label">Total Flights</div>
            <div class="kpi-value">{tot_f2:,}</div>
            <div class="kpi-sub">{y_str2}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Row 1: Horizontal bar | Bubble 
        b1, b2 = st.columns([1.1, 1], gap="medium")

        with b1:
            sec("Delay Rate by Airline — Ranked")
            bar_colors = [
                "#DC2626" if v > avg_p * 1.15 else
                "#F59E0B" if v > avg_p else "#10B981"
                for v in kpi2["delay_pct"]
            ]
            fig_hb = go.Figure(go.Bar(
                x=kpi2["delay_pct"], y=kpi2["carrier_name"], orientation="h",
                marker=dict(color=bar_colors, line=dict(width=0)),
                text=[f"{v:.1f}%" for v in kpi2["delay_pct"]],
                textposition="outside", textfont=dict(color=TXT, size=9.5),
                hovertemplate="<b>%{y}</b><br>Delay Rate: <b>%{x:.2f}%</b><extra></extra>",
                cliponaxis=False,
            ))
            fig_hb.add_vline(x=avg_p, line_dash="dot", line_color="#94A3B8", line_width=1.5,
                             annotation_text=f"Avg {avg_p:.1f}%",
                             annotation_font_color="#94A3B8", annotation_position="top right")
            h_hb = max(320, len(kpi2) * 28 + 60)
            ly5 = base_layout(f"Delay Rate · {y_str2}", height=h_hb)
            ly5["xaxis"]["ticksuffix"] = "%"
            ly5["yaxis"]["autorange"]  = "reversed"
            ly5["xaxis"]["range"]      = [0, kpi2["delay_pct"].max() * 1.2]
            ly5["legend"] = DEFAULT_LEGEND
            fig_hb.update_layout(**ly5)
            st.plotly_chart(fig_hb, use_container_width=True, config={"displayModeBar": False})

        with b2:
            sec("Flight Volume vs Delay Rate")
            max_del = kpi2["total_delay_flights"].max() or 1
            bsz = (kpi2["total_delay_flights"] / max_del * 28 + 7).tolist()
            fig_sc = go.Figure(go.Scatter(
                x=kpi2["total_flights"], y=kpi2["delay_pct"],
                mode="markers+text", text=kpi2["carrier"],
                textposition="top center", textfont=dict(size=8.5, color=TXT),
                marker=dict(
                    size=bsz,
                    color=kpi2["delay_pct"],
                    colorscale=[[0,"#10B981"],[0.5,"#F59E0B"],[1,"#DC2626"]],
                    showscale=True,
                    colorbar=dict(thickness=9, len=0.65, ticksuffix="%",
                                  tickfont=dict(color=TXT, size=9),
                                  title=dict(text="Delay%", font=dict(color=TXT, size=9))),
                    line=dict(color="#FFFFFF", width=1), opacity=0.88,
                ),
                customdata=kpi2["carrier_name"],
                hovertemplate="<b>%{customdata}</b><br>Flights: %{x:,}<br>Delay Rate: <b>%{y:.1f}%</b><extra></extra>",
            ))
            ly6 = base_layout("Volume vs Delay Rate  (bubble = delayed flights)", height=380)
            ly6["xaxis"]["title"] = dict(text="Total Flights", font=dict(color=TXT, size=10))
            ly6["yaxis"]["title"] = dict(text="Delay Rate (%)", font=dict(color=TXT, size=10))
            ly6["yaxis"]["ticksuffix"] = "%"
            fig_sc.update_layout(**ly6)
            st.plotly_chart(fig_sc, use_container_width=True, config={"displayModeBar": False})

        # Row 2: Monthly trend
        sec("Monthly Delay Trend by Airline")
        trend2 = df2.groupby(["carrier","carrier_name","month","year"])["delay_percentage"].mean().reset_index()
        fig_tr = go.Figure()
        for i, code in enumerate(sorted(sel_carriers)):
            sub = trend2[trend2["carrier"] == code].sort_values(["year","month"])
            if sub.empty: continue
            cname = sub["carrier_name"].iloc[0]
            sub = sub.copy()
            sub["x_label"] = (sub["year"].astype(int).astype(str) + "-" + sub["month"].map(MONTHS)
                              if len(sel_years) > 1 else sub["month"].map(MONTHS))
            fig_tr.add_trace(go.Scatter(
                x=sub["x_label"], y=sub["delay_percentage"],
                mode="lines+markers", name=cname,
                line=dict(color=PALETTE[i % len(PALETTE)], width=2),
                marker=dict(size=4, line=dict(color="#FFFFFF", width=1)),
                hovertemplate=f"<b>{cname}</b> · %{{x}}: <b>%{{y:.1f}}%</b><extra></extra>",
            ))
        ly7 = base_layout(f"Delay Rate Trend · {y_str2}", height=320)
        ly7["yaxis"]["ticksuffix"] = "%"
        ly7["hovermode"] = "x unified"
        ly7["legend"] = DEFAULT_LEGEND
        fig_tr.update_layout(**ly7)
        st.plotly_chart(fig_tr, use_container_width=True, config={"displayModeBar": False})

        # Year-over-year
        if len(sel_years) > 1:
            sec("Year-over-Year Avg Delay Rate by Airline")
            yoy2 = df2.groupby(["year","carrier","carrier_name"])["delay_percentage"].mean().reset_index()
            fig_yoy2 = go.Figure()
            for i, code in enumerate(sorted(sel_carriers)):
                sub = yoy2[yoy2["carrier"] == code].sort_values("year")
                if sub.empty: continue
                cname = sub["carrier_name"].iloc[0]
                fig_yoy2.add_trace(go.Scatter(
                    x=sub["year"].astype(int).astype(str), y=sub["delay_percentage"],
                    mode="lines+markers", name=cname,
                    line=dict(color=PALETTE[i % len(PALETTE)], width=2),
                    marker=dict(size=8, line=dict(color="#FFFFFF", width=1.5)),
                    hovertemplate=f"<b>{cname}</b> · %{{x}}: <b>%{{y:.1f}}%</b><extra></extra>",
                ))
            ly_yoy2 = base_layout("YoY Avg Delay Rate per Airline", height=300)
            ly_yoy2["xaxis"] = ly_yoy2.get("xaxis", {})
            ly_yoy2["xaxis"]["type"] = "category"
            ly_yoy2["yaxis"]["ticksuffix"] = "%"
            ly_yoy2["hovermode"] = "x unified"
            ly_yoy2["legend"] = DEFAULT_LEGEND
            fig_yoy2.update_layout(**ly_yoy2)
            st.plotly_chart(fig_yoy2, use_container_width=True, config={"displayModeBar": False})

        # Summary Table
        sec("Summary Table")
        tbl = kpi2.sort_values("delay_pct").copy()
        tbl["rank"] = range(1, len(tbl)+1)
        tbl = tbl[["rank","carrier","carrier_name","total_flights","total_delay_flights","delay_pct","avg_delay"]]
        tbl.columns = ["Rank","Code","Airline","Total Flights","Delayed Flights","Delay %","Avg Delay (min)"]
        tbl["Delay %"]         = tbl["Delay %"].round(2).astype(str) + "%"
        tbl["Avg Delay (min)"] = tbl["Avg Delay (min)"].round(1)
        st.dataframe(tbl.reset_index(drop=True), use_container_width=True, hide_index=True,
                     column_config={
                         "Rank":            st.column_config.NumberColumn(width="small"),
                         "Total Flights":   st.column_config.NumberColumn(format="%d"),
                         "Delayed Flights": st.column_config.NumberColumn(format="%d"),
                     })


# TAB 3 — DELAY CAUSE DISTRIBUTION
# Tab-local filter: Region
with tab3:
    if df_dc.empty:
        st.warning("No data in `delay_cause_distribution`.")
        st.stop()

    CAUSE_CT  = {"carrier_ct":"Carrier","weather_ct":"Weather","nas_ct":"NAS",
                 "security_ct":"Security","late_aircraft_ct":"Late Aircraft"}
    CAUSE_MIN = {"carrier_delay":"Carrier","weather_delay":"Weather","nas_delay":"NAS",
                 "security_delay":"Security","late_aircraft_delay":"Late Aircraft"}

    all_regions_t3 = sorted(df_dc["region"].dropna().unique())

    # Tab-local filter: Region
    st.markdown("""
    <div class="tab-filter-panel">
      <div class="tab-filter-title">🗺️ Region Filter <span style="font-weight:400;color:#94A3B8;font-size:0.68rem;text-transform:none;letter-spacing:0">&nbsp;</span></div>
      <div class="tab-filter-note">Select one or more regions to analyse below.</div>
    </div>
    """, unsafe_allow_html=True)

    reg_cols3 = st.columns(len(all_regions_t3))
    sel_regions_t3 = []
    for i, reg in enumerate(all_regions_t3):
        if reg_cols3[i].checkbox(reg, value=True, key=f"t3_reg_{reg}"):
            sel_regions_t3.append(reg)
    if not sel_regions_t3: sel_regions_t3 = all_regions_t3

    st.markdown("<div style='margin-bottom:0.8rem'></div>", unsafe_allow_html=True)

    pill_strip(
        {"Years": [str(y) for y in sorted(sel_years)],
         "Months": [MONTHS[m] for m in sorted(sel_months)]},
        {"Regions": sorted(sel_regions_t3)},
    )

    df3 = df_dc[
        df_dc["year"].isin(sel_years) &
        df_dc["month"].isin(sel_months) &
        df_dc["region"].isin(sel_regions_t3)
    ].copy()

    if df3.empty:
        no_data()
    else:
        agg3 = {}
        for c in list(CAUSE_CT.keys()) + list(CAUSE_MIN.keys()):
            agg3[c] = float(df3[c].astype(float).sum())

        dom_ct      = max(CAUSE_CT,  key=lambda c: agg3[c])
        dom_del     = max(CAUSE_MIN, key=lambda c: agg3[c])
        dom_ct_lbl  = CAUSE_CT[dom_ct]
        dom_del_lbl = CAUSE_MIN[dom_del]
        tot_ct  = sum(agg3[c] for c in CAUSE_CT)
        tot_min = sum(agg3[c] for c in CAUSE_MIN)
        y_str3  = "/".join(str(y) for y in sorted(sel_years))
        reg_lbl = ", ".join(sorted(sel_regions_t3)[:2])
        if len(sel_regions_t3) > 2: reg_lbl += f" +{len(sel_regions_t3)-2}"

        st.markdown(f"""
        <div class="kpi-grid" style="grid-template-columns:repeat(4,1fr);">
          <div class="kpi-card">
            <div class="kpi-accent" style="background:#0EA5E9"></div>
            <div class="kpi-label">Dominant — Frequency</div>
            <div class="kpi-value" style="font-size:1.3rem">{dom_ct_lbl}</div>
            <div class="kpi-sub">most frequent cause · {reg_lbl}</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-accent" style="background:#F59E0B"></div>
            <div class="kpi-label">Dominant — Duration</div>
            <div class="kpi-value" style="font-size:1.3rem">{dom_del_lbl}</div>
            <div class="kpi-sub">longest total minutes · {reg_lbl}</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-accent" style="background:#10B981"></div>
            <div class="kpi-label">Total Delay Events</div>
            <div class="kpi-value">{tot_ct:,.0f}</div>
            <div class="kpi-sub">all causes · {y_str3}</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-accent" style="background:#6366F1"></div>
            <div class="kpi-label">Total Delay Minutes</div>
            <div class="kpi-value">{tot_min/1_000_000:.2f}M</div>
            <div class="kpi-sub">minutes · {reg_lbl}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        same = dom_ct_lbl == dom_del_lbl
        st.markdown(f"""
        <div class="insight-box">
          <span class="insight-tag">💡 Auto Insight</span>
          Across <strong>{y_str3}</strong> in the <strong>{reg_lbl}</strong> region(s),
          there were <strong>{tot_ct:,.0f}</strong> delay events totalling
          <strong>{tot_min/1_000_000:.2f}M minutes</strong>.
          Most frequent cause: <strong>{dom_ct_lbl}</strong>.
          Greatest duration: <strong>{dom_del_lbl}</strong> —
          {"both point to the same bottleneck." if same
           else "less-frequent events can carry outsized time impact."}
        </div>
        """, unsafe_allow_html=True)

        # Row 1: Pie × 2
        p1, p2 = st.columns(2, gap="medium")
        with p1:
            sec("Delay Frequency — by Count (Aggregated)")
            vals_ct = [agg3[c] for c in CAUSE_CT]
            st.plotly_chart(
                make_pie(list(CAUSE_CT.values()), vals_ct, f"Count · {reg_lbl} · {y_str3}"),
                use_container_width=True, config={"displayModeBar": False})
        with p2:
            sec("Delay Impact — by Duration (Aggregated)")
            vals_min = [agg3[c] for c in CAUSE_MIN]
            st.plotly_chart(
                make_pie(list(CAUSE_MIN.values()), vals_min, f"Minutes · {reg_lbl} · {y_str3}"),
                use_container_width=True, config={"displayModeBar": False})

        # Row 2: Stacked bars
        sec("Regional Comparison — Delay Frequency (Stacked)")
        reg_agg = df3.groupby("region")[[*CAUSE_CT.keys()]].sum().reset_index()
        fig_sb1 = go.Figure()
        for i, (col_k, label) in enumerate(CAUSE_CT.items()):
            fig_sb1.add_trace(go.Bar(
                name=label, x=reg_agg["region"], y=reg_agg[col_k].astype(float),
                marker_color=CAUSE_C[i],
                hovertemplate=f"<b>{label}</b> · %{{x}}: <b>%{{y:,.0f}} events</b><extra></extra>",
            ))
        ly_s1 = base_layout(f"Delay Count by Cause & Region · {y_str3}", height=320)
        ly_s1["barmode"] = "stack"
        ly_s1["legend"] = dict(orientation="h", y=1.08, bgcolor="rgba(255,255,255,0)",
                               font=dict(size=10, color=TXT))
        fig_sb1.update_layout(**ly_s1)
        st.plotly_chart(fig_sb1, use_container_width=True, config={"displayModeBar": False})

        sec("Regional Comparison — Delay Duration (Stacked)")
        reg_agg2 = df3.groupby("region")[[*CAUSE_MIN.keys()]].sum().reset_index()
        fig_sb2 = go.Figure()
        for i, (col_k, label) in enumerate(CAUSE_MIN.items()):
            fig_sb2.add_trace(go.Bar(
                name=label, x=reg_agg2["region"], y=reg_agg2[col_k].astype(float),
                marker_color=CAUSE_C[i],
                hovertemplate=f"<b>{label}</b> · %{{x}}: <b>%{{y:,.0f}} min</b><extra></extra>",
            ))
        ly_s2 = base_layout(f"Delay Duration by Cause & Region · {y_str3}", height=320)
        ly_s2["barmode"] = "stack"
        ly_s2["yaxis"]["ticksuffix"] = " min"
        ly_s2["legend"] = dict(orientation="h", y=1.08, bgcolor="rgba(255,255,255,0)",
                               font=dict(size=10, color=TXT))
        fig_sb2.update_layout(**ly_s2)
        st.plotly_chart(fig_sb2, use_container_width=True, config={"displayModeBar": False})

        # Row 3: Monthly cause trend
        sec("Monthly Cause Trend (Avg across Selected Regions & Years)")
        mo_agg = df3.groupby("month")[[*CAUSE_CT.keys()]].mean().reset_index()
        fig_ct = go.Figure()
        for i, (col_k, label) in enumerate(CAUSE_CT.items()):
            fig_ct.add_trace(go.Scatter(
                x=[MONTHS[m] for m in mo_agg["month"]],
                y=mo_agg[col_k].astype(float),
                mode="lines+markers", name=label,
                line=dict(color=CAUSE_C[i], width=2),
                marker=dict(size=5, line=dict(color="#FFFFFF", width=1)),
                hovertemplate=f"<b>{label}</b> · %{{x}}: <b>%{{y:,.0f}}</b><extra></extra>",
            ))
        ly_ct = base_layout(f"Cause Trend by Month · {y_str3}", height=320)
        ly_ct["xaxis"]["categoryorder"] = "array"
        ly_ct["xaxis"]["categoryarray"] = MON_LIST
        ly_ct["hovermode"] = "x unified"
        ly_ct["legend"] = DEFAULT_LEGEND
        fig_ct.update_layout(**ly_ct)
        st.plotly_chart(fig_ct, use_container_width=True, config={"displayModeBar": False})

        # YoY cause comparison
        if len(sel_years) > 1:
            sec("Year-over-Year Cause Comparison")
            yoy3 = df3.groupby("year")[[*CAUSE_CT.keys()]].sum().reset_index()
            fig_yoy3 = go.Figure()
            for i, (col_k, label) in enumerate(CAUSE_CT.items()):
                fig_yoy3.add_trace(go.Bar(
                    name=label, x=yoy3["year"].astype(int).astype(str),
                    y=yoy3[col_k].astype(float), marker_color=CAUSE_C[i],
                    hovertemplate=f"<b>{label}</b> · %{{x}}: <b>%{{y:,.0f}} events</b><extra></extra>",
                ))
            ly_yoy3 = base_layout("Total Delay Events by Cause per Year", height=300)
            ly_yoy3["barmode"] = "group"
            ly_yoy3["legend"] = dict(orientation="h", y=1.08, bgcolor="rgba(255,255,255,0)",
                                     font=dict(size=10, color=TXT))
            fig_yoy3.update_layout(**ly_yoy3)
            st.plotly_chart(fig_yoy3, use_container_width=True, config={"displayModeBar": False})

# FOOTER
st.markdown("""
<hr>
<div style="text-align:center;font-size:0.72rem;color:#94A3B8;padding-bottom:1rem;">
  Flight Delay Intelligence Dashboard &nbsp;·&nbsp;
  Sharon Gwyneth C14240061 &nbsp;·&nbsp; Felita Gazella C14240095 &nbsp;·&nbsp; Giza Angelica C14240107
</div>
""", unsafe_allow_html=True)