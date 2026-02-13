import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# 1. PAGE CONFIGURATION
st.set_page_config(page_title="Network Performance Insights", layout="wide")

# 2. CUSTOM CSS
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #fcfcfd; }
    [data-testid="stSidebar"] { background-color: #0f172a; border-right: 1px solid #e2e8f0; }
    [data-testid="stSidebar"] label { color: #f8fafc !important; font-weight: 600; font-size: 0.9rem; }
    div[data-testid="stMetric"] {
        background: white;
        padding: 20px !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        border: 1px solid #f1f5f9;
    }
    .graph-container {
        background: white;
        padding: 20px;
        border-radius: 16px;
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.05);
        margin-bottom: 30px;
        border: 1px solid #f1f5f9;
    }
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
    df = conn.read(ttl=0) 
    
    # FIX: Robust cleaning for ALL columns to remove invisible spaces and standardize case
    df.columns = [str(c).strip().upper() for c in df.columns]
    
    if st.sidebar.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()
    
    st.sidebar.success("📡 Live Google Sheet Connected")

except Exception as e:
    st.error(f"⚠️ Connection Error: {e}")
    st.stop()

# 4. DATA PROCESSING
date_cols = [col for col in df.columns if '-' in col and col[0].isdigit()]
tch_cols = [col for col in df.columns if 'TCH%' in col]
fuel_cols = [col for col in df.columns if '(FUEL)' in col]

latest_date_col = date_cols[-1] if date_cols else None
latest_tch_col = tch_cols[-1] if tch_cols else None

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

# --- NEW USF FILTER ---
usf_options = sorted(df['NEW USF SITES'].dropna().unique()) if 'NEW USF SITES' in df.columns else []
sel_usf = st.sidebar.multiselect("New USF Sites Filter", options=usf_options)

# --- STEP 4 UPDATE: Add TCH Detection ---
date_cols = [col for col in df.columns if '-' in col and col[0].isdigit()]
# Search for the most recent TCH% column
tch_cols = [col for col in df.columns if 'TCH%' in col]
latest_date_col = date_cols[-1] if date_cols else None
latest_tch_col = tch_cols[-1] if tch_cols else None

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
if sel_usf:
    filt_df = filt_df[filt_df['NEW USF SITES'].isin(sel_usf)]  
    filters_active = True  

# 6. CHART FUNCTION
# def create_advanced_chart(x_data, y_data, title, color, y_label, is_percent=True):
#     x_clean = []
#     for x in x_data:
#         try:
#             x_clean.append(datetime.strptime(str(x), '%Y-%m-%d').strftime('%d-%b'))
#         except:
#             x_clean.append(str(x).replace(' TCH%', '').split(' (FUEL)')[0])

#     fig = go.Figure()
#     fig.add_trace(go.Scatter(
#         x=x_clean, y=y_data,
#         mode='lines+markers+text',
#         text=[f"{v:.1f}%" if is_percent else f"{v:.0f}" for v in y_data],
#         textposition="top center",
#         cliponaxis=False,
#         line=dict(width=4, color=color, shape='spline'),
#         marker=dict(size=10, color='white', line=dict(color=color, width=3)),
#         fill='tozeroy',
#         fillcolor=f'rgba{tuple(list(int(color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4)) + [0.05])}'
#     ))

#     fig.update_layout(
#         title=dict(text=title, font=dict(size=18)),
#         margin=dict(l=60, r=60, t=80, b=60),
#         height=400,
#         xaxis=dict(type='category', range=[-0.5, len(x_clean)-0.5]),
#         yaxis=dict(showgrid=True, gridcolor='#f1f5f9', zeroline=False),
#         plot_bgcolor='white'
#     )
#     return fig

def create_advanced_chart(x_data, y_data, title, color, y_label, is_percent=True):
    # 1. Clean up labels for the X-axis
    x_clean = []
    for x in x_data:
        try:
            x_clean.append(datetime.strptime(str(x), '%Y-%m-%d').strftime('%d-%b'))
        except:
            x_clean.append(str(x).replace(' TCH%', '').split(' (FUEL)')[0])

    fig = go.Figure()

    # 2. Create the smoothed trend line with 2-decimal visible text labels
    fig.add_trace(go.Scatter(
        x=x_clean, 
        y=y_data,
        mode='lines+markers+text', 
        # Update :.1f to :.2f for two decimal places
        text=[f"{v:.2f}%" if is_percent else f"{v:.2f}" for v in y_data], 
        textposition="top center", 
        cliponaxis=False, 
        line=dict(width=4, color=color, shape='spline'), 
        marker=dict(
            size=10, 
            color='white', 
            line=dict(color=color, width=3)
        ),
        fill='tozeroy',
        fillcolor=f'rgba{tuple(list(int(color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4)) + [0.1])}',
        hoverinfo="x+y"
    ))

    # 3. Optimize Layout
    fig.update_layout(
        title=dict(
            text=f"<b>{title}</b>", 
            font=dict(size=20, color='#1e293b', family="Inter, sans-serif")
        ),
        margin=dict(l=40, r=40, t=100, b=40),
        height=450,
        xaxis=dict(
            title="<b>Timeline (Dates)</b>",
            showline=True, 
            linecolor='#e2e8f0', 
            showgrid=False,
            type='category'
        ),
        yaxis=dict(
            title="<b>Availability Percentage (%)</b>",  # Y-axis Label
            showgrid=True, 
            gridcolor='#f1f5f9', 
            zeroline=False,
            dtick=0.5,
            # Adjust range slightly to accommodate the longer 2-decimal labels
            range=[max(0, min(y_data) - 0.5), min(100, max(y_data) + 1.2)] if len(y_data) > 0 else None
        ),
        plot_bgcolor='white',
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=False
    )
    
    return fig

# 7. DASHBOARD UI
st.markdown('<h1 style="color: #0f172a;">Network Intelligence Portal</h1>', unsafe_allow_html=True)

# --- TOP 3 METRIC CARDS ---
# These now update based on your Region, TGL, and New USF Sites selections
m1, m2, m3 = st.columns(3)

with m1:
    if latest_date_col:
        # Average Availability for selected USF/Non-USF sites
        val = pd.to_numeric(filt_df[latest_date_col], errors='coerce').mean()
        st.metric(f"Average Cell Availability {display_date}", f"{val:.2f}%")

with m2:
    if latest_tch_col:
        # Average TCH% for selected USF/Non-USF sites
        val = pd.to_numeric(filt_df[latest_tch_col], errors='coerce').mean()
        st.metric(f"{display_date} Average TCH%", f"{val:.2f}%")

with m3:
    # Total count of active sites in the current filter
    st.metric("Total Active Sites", len(filt_df))

# --- TREND GRAPH ---
# Keeping current graph logic but ensuring it stays visible and updates with filters
if len(date_cols) > 1:
    st.markdown('<div class="graph-container">', unsafe_allow_html=True)
    trend_days = date_cols[-7:]
    # Linked to filt_df so the trend reflects your USF selection
    day_values = filt_df[trend_days].apply(pd.to_numeric, errors='coerce').mean()
    st.plotly_chart(create_advanced_chart(trend_days, day_values, "📈 Daily Availability Trend", "#3b82f6", "Availability"), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)


        

# 7. DETAILED SITE CARDS (Enhanced to handle 10 columns)
if len(filt_df) == 1:
    st.markdown(f"### SITE: {filt_df.iloc[0]['SID']}")
    site = filt_df.iloc[0]
    
    # We use 5 columns per row. With 10 items, it will create 2 rows automatically.
    cols = st.columns(5)
    
    # Updated list containing all 10 columns (Standardized to Uppercase to match Step 3)
    details = [
        'REGION', 'TGL', 'GRID', 'TECHNOLOGY', 'SITE CATEGORY', 
        'CO', 'SUB CITIES', 'DEPENDANCY', 'NPS SITES', 'SITE IMPORTANCE',
        'REVENUE CAT',	'ONAIRDATE', 'NEW USF SITES', 'SHARING STATUS', 'SHARED WITH',
        'OMO SITE ID', 'LOCKED SITE EXPIRE DATE', 'DG OPERTATIONAL STATUS (696 UPDATE)',
        'SOLAR SITES', 'LI-ION SITES' 
    ]
    
    for i, d in enumerate(details):
        with cols[i % 5]:
            # Ensure the column exists in Uppercase
            display_val = site[d] if d in site else "N/A"
            st.markdown(f"""
                <div class="detail-card">
                    <div class="detail-label">{d}</div>
                    <div class="detail-value">{display_val}</div>
                </div>
            """, unsafe_allow_html=True)

