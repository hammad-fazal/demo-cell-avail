import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# 1. PAGE CONFIGURATION
st.set_page_config(page_title="Network Performance Insights", layout="wide")

# 2. CUSTOM CSS (Enhanced for width and readability)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #fcfcfd; }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] { background-color: #0f172a; border-right: 1px solid #e2e8f0; }
    [data-testid="stSidebar"] label { color: #f8fafc !important; font-weight: 600; font-size: 0.9rem; }
    
    /* Metric Card Styling */
    div[data-testid="stMetric"] {
        background: white;
        padding: 20px !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        border: 1px solid #f1f5f9;
    }
    
    /* Graph Container */
    .graph-container {
        background: white;
        padding: 20px;
        border-radius: 16px;
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.05);
        margin-bottom: 30px;
        border: 1px solid #f1f5f9;
    }

    /* Detail Card for Site Info */
    .detail-card {
        background-color: #ffffff;
        padding: 12px;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        margin-bottom: 10px;
    }
    .detail-label { color: #64748b; font-size: 0.7rem; text-transform: uppercase; font-weight: 700; }
    .detail-value { color: #0f172a; font-size: 0.9rem; font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)

# 3. GOOGLE SHEETS CONNECTION
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    # Fetch data - ttl=0 allows manual refresh to pull live data
    df = conn.read(ttl=0) 
    
    # CRITICAL: Clean column names to prevent KeyError: 'SID'
    df.columns = df.columns.str.strip().str.upper()
    
    if st.sidebar.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()
    
    st.sidebar.success("📡 Live Google Sheet Connected")

except Exception as e:
    st.error(f"⚠️ Connection Error: {e}")
    st.stop()

# 4. DATA PROCESSING & DATE LOGIC
# Identify column groups based on naming patterns
date_cols = [col for col in df.columns if '-' in col and col[0].isdigit()]
tch_cols = [col for col in df.columns if 'TCH%' in col]
fuel_cols = [col for col in df.columns if '(FUEL)' in col]

latest_date_col = date_cols[-1] if date_cols else None
latest_tch_col = tch_cols[-1] if tch_cols else None

# Format the date for display (e.g., "11 February 2026")
if latest_date_col:
    try:
        display_date = datetime.strptime(latest_date_col, '%Y-%m-%d').strftime("%d %B %Y")
    except:
        display_date = latest_date_col
else:
    display_date = datetime.now().strftime("%d %B %Y")

# 5. SIDEBAR FILTERS
st.sidebar.header("🛠️ Dashboard Filters")
all_sids = ["All Sites"] + sorted(df['SID'].astype(str).unique().tolist())
search_sid = st.sidebar.selectbox("Select Station ID", all_sids)
sel_region = st.sidebar.multiselect("Region Filter", options=sorted(df['REGION'].dropna().unique()))
sel_tgl = st.sidebar.multiselect("TGL Filter", options=sorted(df['TGL'].dropna().unique()))

# Filter Logic
filt_df = df.copy()
filters_active = False
if search_sid != "All Sites":
    filt_df = filt_df[filt_df['SID'].astype(str) == search_sid]
    filters_active = True
if sel_region:
    filt_df = filt_df[filt_df['REGION'].isin(sel_region)]
    filters_active = True
if sel_tgl:
    filt_df = filt_df[filt_df['TGL'].isin(sel_tgl)]
    filters_active = True

# 6. CHART FUNCTION (Optimized for no clipping)
def create_advanced_chart(x_data, y_data, title, color, y_label, is_percent=True):
    # Format dates for X-axis display
    x_clean = []
    for x in x_data:
        try:
            x_clean.append(datetime.strptime(str(x), '%Y-%m-%d').strftime('%d-%b'))
        except:
            x_clean.append(str(x).replace(' TCH%', '').split(' (FUEL)')[0])

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x_clean, y=y_data,
        mode='lines+markers+text',
        text=[f"{v:.1f}%" if is_percent else f"{v:.0f}" for v in y_data],
        textposition="top center",
        cliponaxis=False, # FIX: Prevents top labels from being cut off
        line=dict(width=4, color=color, shape='spline'),
        marker=dict(size=10, color='white', line=dict(color=color, width=3)),
        fill='tozeroy',
        fillcolor=f'rgba{tuple(list(int(color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4)) + [0.05])}'
    ))

    fig.update_layout(
        title=dict(text=title, font=dict(size=18)),
        margin=dict(l=60, r=60, t=80, b=60), # Generous margins for labels
        height=400,
        xaxis=dict(type='category', range=[-0.5, len(x_clean)-0.5]), # Padding on sides
        yaxis=dict(showgrid=True, gridcolor='#f1f5f9', zeroline=False),
        plot_bgcolor='white'
    )
    return fig

# 7. DASHBOARD UI
st.markdown('<h1 style="color: #0f172a;">Network Intelligence Portal</h1>', unsafe_allow_html=True)

if not filters_active:
    # Summary Metrics
    m1, m2, m3 = st.columns(3)
    with m1:
        if latest_date_col:
            val = pd.to_numeric(df[latest_date_col], errors='coerce').mean()
            st.metric(f"Average Cell Availability {display_date}", f"{val:.2f}%")
    with m2:
        if latest_tch_col:
            val = pd.to_numeric(df[latest_tch_col], errors='coerce').mean()
            st.metric(f"{display_date} Average TCH%", f"{val:.2f}%")
    with m3:
        st.metric("Total Active Sites", len(df))

    # Trends
    if len(date_cols) > 1:
        st.markdown('<div class="graph-container">', unsafe_allow_html=True)
        trend_days = date_cols[-7:]
        day_values = df[trend_days].apply(pd.to_numeric, errors='coerce').mean()
        st.plotly_chart(create_advanced_chart(trend_days, day_values, "📈 Daily Availability Trend", "#3b82f6", "Availability"), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    if tch_cols:
        st.markdown('<div class="graph-container">', unsafe_allow_html=True)
        trend_months = tch_cols[-6:]
        month_values = df[trend_months].apply(pd.to_numeric, errors='coerce').mean()
        st.plotly_chart(create_advanced_chart(trend_months, month_values, "📅 Monthly Efficiency (TCH%)", "#10b981", "TCH%"), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

# Detailed Site Cards
if len(filt_df) == 1:
    st.markdown(f"### 📍 Details: {filt_df.iloc[0]['SID']}")
    site = filt_df.iloc[0]
    cols = st.columns(5)
    details = ['REGION', 'TGL', 'GRID ', 'TECHNOLOGY', 'SITE CATEGORY']
    for i, d in enumerate(details):
        with cols[i % 5]:
            st.markdown(f'<div class="detail-card"><div class="detail-label">{d}</div><div class="detail-value">{site[d]}</div></div>', unsafe_allow_html=True)

# Data Table
st.subheader(f"📋 Site Inventory ({len(filt_df)} Results)")
display_cols = ['SID', 'REGION', 'TGL', 'TECHNOLOGY']
if latest_date_col: display_cols.append(latest_date_col)
st.dataframe(filt_df[display_cols], use_container_width=True)