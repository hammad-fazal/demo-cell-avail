import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import datetime

# 1. Page Config
st.set_page_config(page_title="Network Performance Insights", layout="wide")

# 2. ADVANCED CUSTOM CSS
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #fcfcfd; }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] { background-color: #0f172a; border-right: 1px solid #e2e8f0; }
    [data-testid="stSidebar"] label { color: #f8fafc !important; font-weight: 600; font-size: 0.9rem; }
    [data-testid="stSidebar"] input { color: #1e293b !important; border-radius: 8px; }
    div[data-baseweb="select"] * { color: #1e293b !important; }
    
    /* Advanced Metric Card */
    div[data-testid="stMetric"] {
        background: white;
        padding: 24px !important;
        border-radius: 16px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
        border: 1px solid #f1f5f9;
    }
    
    /* Graph Container - Reduced padding to increase graph width */
    .graph-container {
        background: white;
        padding: 15px; /* Reduced from 40px */
        border-radius: 20px;
        box-shadow: 0 10px 25px -5px rgba(0,0,0,0.04);
        margin-bottom: 40px;
        border: 1px solid #f1f5f9;
    }

    /* Detail Card */
    .detail-card {
        background-color: #ffffff;
        padding: 12px;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        margin-bottom: 10px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.02);
    }
    .detail-label { color: #64748b; font-size: 0.7rem; text-transform: uppercase; font-weight: 700; margin-bottom: 4px; }
    .detail-value { color: #0f172a; font-size: 0.9rem; font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)

DATA_PATH = "data/current_availability.csv"

if not os.path.exists(DATA_PATH):
    st.title("📊 Performance Dashboard")
    st.warning("⚠️ Data source not found. Please upload data via Admin Panel.")
else:
    df = pd.read_csv(DATA_PATH)
    
    # Identify Column Groups
    date_cols = [col for col in df.columns if '-' in col and col[0].isdigit() and len(col.split('-')) == 3]
    tch_cols = [col for col in df.columns if 'TCH%' in col]
    fuel_cols = [col for col in df.columns if '(Fuel)' in col]
    
    latest_date = date_cols[-1] if date_cols else None
    latest_month_tch = tch_cols[-1] if tch_cols else None

    # --- SIDEBAR FILTERS ---
    st.sidebar.header("🛠️ Filters")
    all_sids = ["All Sites"] + sorted(df['SID'].astype(str).unique().tolist())
    search_sid = st.sidebar.selectbox("Select Station ID", all_sids)
    sel_region = st.sidebar.multiselect("Region Filter", options=sorted(df['Region'].dropna().unique()))
    sel_tgl = st.sidebar.multiselect("TGL Filter", options=sorted(df['TGL'].dropna().unique()))

    # Filter Logic
    filt_df = df.copy()
    filters_active = False
    if search_sid != "All Sites":
        filt_df = filt_df[filt_df['SID'].astype(str) == search_sid]
        filters_active = True
    if sel_region:
        filt_df = filt_df[filt_df['Region'].isin(sel_region)]
        filters_active = True
    if sel_tgl:
        filt_df = filt_df[filt_df['TGL'].isin(sel_tgl)]
        filters_active = True

    st.markdown('<h1 style="color: #0f172a; margin-bottom: 30px;">Network Intelligence Portal</h1>', unsafe_allow_html=True)

    # Updated Chart Function
    def create_advanced_chart(x_data, y_data, title, color, x_label, y_label, is_percent=True):
            # 1. Clean X-Axis Labels (Format Date Strings to "10-Feb")
            x_clean = []
            for x in x_data:
                s = str(x).replace('\n', ' ').strip()
                try:
                    date_obj = datetime.strptime(s, '%Y-%m-%d')
                    x_clean.append(date_obj.strftime('%d-%b'))
                except ValueError:
                    x_clean.append(s.replace(' TCH%', '').split(' (Fuel)')[0])

            # 2. Prepare Data Labels
            text_labels = [f"{v:.1f}%" if is_percent else f"{v:.0f}" for v in y_data]
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=x_clean, y=y_data,
                mode='lines+markers+text',
                text=text_labels,
                textposition="top center",
                # cliponaxis=False ensures labels aren't cut by the plot borders
                cliponaxis=False, 
                textfont=dict(color='#1e293b', size=13, weight=600, family="Inter"),
                line=dict(width=4, color=color, shape='spline'),
                fill='tozeroy',
                fillcolor=f'rgba{tuple(list(int(color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4)) + [0.1])}',
                marker=dict(size=10, color='white', line=dict(color=color, width=3)),
                hovertemplate=f"<b>%{{x}}</b><br>{y_label}: %{{y:.2f}}<extra></extra>"
            ))
            
            # Calculate Y-Range with padding
            y_max = max(y_data) if len(y_data) > 0 else 100
            y_min = min(y_data) if len(y_data) > 0 else 0
            range_padding = (y_max - y_min) * 0.25 if y_max != y_min else y_max * 0.1
            y_range = [y_min - (range_padding/2), y_max + range_padding]

            fig.update_layout(
                title=dict(text=title, font=dict(size=20, color='#1e293b'), x=0, y=0.98),
                plot_bgcolor='rgba(0,0,0,0)', 
                paper_bgcolor='rgba(0,0,0,0)',
                height=450, 
                # Increased L and R margins significantly to 100
                margin=dict(l=100, r=100, t=100, b=80),
                xaxis_title=dict(text=x_label, font=dict(size=12, color='#64748b')),
                yaxis_title=dict(text=y_label, font=dict(size=12, color='#64748b')),
                xaxis=dict(
                    type='category', 
                    showgrid=False, 
                    linecolor='#cbd5e1', 
                    tickfont=dict(size=12, color='#475569'),
                    # Adds a half-category buffer on both sides so labels have room
                    range=[-0.1, len(x_clean) - 0.96] 
                ), 
                yaxis=dict(
                    showgrid=True, 
                    gridcolor='#f1f5f9', 
                    zeroline=False,
                    range=y_range
                ),
                hovermode="x unified"
            )
            return fig

    # --- CONDITIONAL DISPLAY: ONLY IF NO FILTERS ARE SELECTED ---
    if not filters_active:
        # 1. Summary Metrics
        m1, m2, m3 = st.columns(3)
        
        # Get today's date formatted as "11 February 2026"
        display_date = datetime.now().strftime("%d %B %Y")
        
        with m1:
            if latest_date:
                val = pd.to_numeric(df[latest_date], errors='coerce').mean()
                # Title: Average Cell Availability + Date
                st.metric(f"Average Cell Availability {display_date}", f"{val:.2f}%")
                
        with m2:
            if latest_month_tch:
                val = pd.to_numeric(df[latest_month_tch], errors='coerce').mean()
                # Title: Date + Average TCH%
                st.metric(f"{display_date} Average TCH%", f"{val:.2f}%")
                
        with m3:
            st.metric("Total Active Sites", len(df))
            
            st.markdown("<br>", unsafe_allow_html=True)

        # 2. Daily Availability Trend (Excluding today)
        if len(date_cols) > 1:
            st.markdown('<div class="graph-container">', unsafe_allow_html=True)
            trend_days = date_cols[-7:-1] if len(date_cols) >= 7 else date_cols[:-1]
            day_values = df[trend_days].apply(pd.to_numeric, errors='coerce').mean()
            fig1 = create_advanced_chart(trend_days, day_values, "📈 Availability Trend (Daily History)", "#3b82f6", "Date", "Availability (%)", is_percent=True)
            st.plotly_chart(fig1, use_container_width=True, config={'displayModeBar': False})
            st.markdown('</div>', unsafe_allow_html=True)

        # 3. Monthly TCH% Trend
        if tch_cols:
            st.markdown('<div class="graph-container">', unsafe_allow_html=True)
            trend_months = tch_cols[-6:]
            month_values = df[trend_months].apply(pd.to_numeric, errors='coerce').mean()
            fig2 = create_advanced_chart(trend_months, month_values, "📅 Monthly Efficiency History", "#10b981", "Month", "TCH %", is_percent=True)
            st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})
            st.markdown('</div>', unsafe_allow_html=True)

        # 4. Monthly Fuel Trend
        if fuel_cols:
            st.markdown('<div class="graph-container">', unsafe_allow_html=True)
            trend_fuel = fuel_cols[-6:]
            fuel_values = df[trend_fuel].apply(pd.to_numeric, errors='coerce').mean()
            fig3 = create_advanced_chart(trend_fuel, fuel_values, "⛽ Fuel Consumption History", "#f59e0b", "Month", "Avg Liters", is_percent=False)
            st.plotly_chart(fig3, use_container_width=True, config={'displayModeBar': False})
            st.markdown('</div>', unsafe_allow_html=True)

    # --- DETAILED SITE CARDS (Shown when 1 SID is selected) ---
    if len(filt_df) == 1:
        st.markdown(f'<h3 style="color: #0f172a;">📍 Details for SID: {filt_df.iloc[0]["SID"]}</h3>', unsafe_allow_html=True)
        site_data = filt_df.iloc[0]
        detail_cols = ['SID', 'Region', 'TGL', 'Grid ', 'Technology', 'Site Category', 'Revenue Cat', 'OnAirDate', 'Solar Sites', 'Li-Ion Sites']
        
        cols = st.columns(5)
        for i, col_name in enumerate(detail_cols):
            with cols[i % 5]:
                val = site_data[col_name]
                st.markdown(f"""
                    <div class="detail-card">
                        <div class="detail-label">{col_name}</div>
                        <div class="detail-value">{val if pd.notna(val) else "-"}</div>
                    </div>
                """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

    # --- DATA TABLE (Always shown) ---
    st.subheader(f"📋 Site Inventory ({len(filt_df)} Results)")
    main_cols = ['SID', 'Region', 'TGL', 'Grid ', 'Technology', 'Site Category']
    if latest_month_tch: main_cols.append(latest_month_tch)
    if latest_date: main_cols.append(latest_date)
    
    st.dataframe(filt_df[main_cols], use_container_width=True)