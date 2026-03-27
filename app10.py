import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import streamlit.components.v1 as components


# --- LOGIN FUNCTION (Improved Logic, Same UI) ---
def check_password():
    """Returns True if the user had the correct password."""

    # 1. If already authenticated, return True immediately
    if st.session_state.get("password_correct"):
        return True

    # 2. Show the UI you liked
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("https://cdn-icons-png.flaticon.com/512/6195/6195699.png", width=100) 
        st.title("Network Portal Login")
        
        # We use a form so the 'Enter' key works and state is handled together
        with st.form("login_form"):
            user = st.text_input("Username")
            pas = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login", use_container_width=True)
            
            if submit:
                if user == "admin" and pas == "admin":
                    st.session_state["password_correct"] = True
                    st.rerun() # Refresh to show the portal
                else:
                    st.session_state["password_correct"] = False
                    st.error("❌ Incorrect Username or Password")

    return False
# --- START THE LOGIN CHECK ---
if not check_password():
    st.stop()  # Do not run the rest of the script if not logged in


# 1. PAGE CONFIGURATION
st.set_page_config(page_title="Network Performance Insights", layout="wide")

# 2. CUSTOM CSS
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* Global styles */
    .stApp {
        background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
        font-family: 'Inter', sans-serif;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0f172a !important;
        border-right: 1px solid #1e293b;
    }
    section[data-testid="stSidebar"] .stMarkdown h2, 
    section[data-testid="stSidebar"] label {
        color: #f1f5f9 !important;
        font-weight: 500;
    }

    /* Professional Metric Cards */
    div[data-testid="stMetric"] {
        background: white;
        padding: 24px !important;
        border-radius: 16px !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
        border: 1px solid rgba(226, 232, 240, 0.8);
        transition: transform 0.2s ease-in-out;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-4px);
        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.08);
    }
    
    /* Typography for Metrics */
    div[data-testid="stMetricValue"] {
        color: #0f172a !important;
        font-weight: 700 !important;
        font-size: 2.2rem !important;
    }
    div[data-testid="stMetricLabel"] {
        color: #64748b !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* Graph Container */
    .graph-container {
        background: white;
        padding: 25px;
        border-radius: 20px;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.03);
        border: 1px solid #e2e8f0;
        margin-top: 25px;
    }

    /* Site Detail Cards */
    .detail-card {
        background: #f8fafc;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        transition: all 0.3s;
    }
    .detail-card:hover {
        background: white;
        border-color: #3b82f6;
    }
    .detail-label { 
        color: #94a3b8; 
        font-size: 0.65rem; 
        text-transform: uppercase; 
        font-weight: 800; 
        margin-bottom: 4px;
    }
    .detail-value { 
        color: #1e293b; 
        font-size: 0.95rem; 
        font-weight: 600; 
    }
    </style>
    """, unsafe_allow_html=True)

# 3. OPTIMIZED GOOGLE SHEETS CONNECTION
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl="15m")
def load_all_network_data():
    sheet_links = {
        "SITE_AVAIL": st.secrets["connections"]["gsheets"]["url_site"],
        "AVAILABILITY": st.secrets["connections"]["gsheets"]["url_avail"],
        "2G": st.secrets["connections"]["gsheets"]["url_2g"],
        "3G": st.secrets["connections"]["gsheets"]["url_3g"],
        "4G": st.secrets["connections"]["gsheets"]["url_4g"]
    }
    
    loaded_tech_dfs = {}
    for name, link in sheet_links.items():
        temp_df = conn.read(spreadsheet=link, ttl=0)
        temp_df.columns = [str(c).strip().upper() for c in temp_df.columns]
        loaded_tech_dfs[name] = temp_df
    return loaded_tech_dfs

try:
    tech_dfs = load_all_network_data()
    df = tech_dfs.get("AVAILABILITY")
    
    # --- UPDATED BUTTON LOGIC ---
    if st.sidebar.button("Clear Filters", use_container_width=True):
        # REMOVED: st.cache_data.clear() <- This was causing the slow reload
        
        # We only clear the UI selections
        keys_to_reset = ["sid_filter", "region_filter", "tgl_filter", "usf_filter", "rev_filter", "date_filter"]
        for key in keys_to_reset:
            if key in st.session_state:
                st.session_state[key] = "All Sites" if key == "sid_filter" else []
        
        # Rerun to apply the UI changes using the data ALREADY in memory
        st.rerun()

except Exception as e:
    st.error(f"⚠️ Connection Error: {e}")
    st.stop()

try:
    # Call the cached function
    tech_dfs = load_all_network_data()
    
    # Assign your main dataframe for filters
    df = tech_dfs.get("AVAILABILITY")
    
    st.sidebar.success("Connected to Live Data")

except Exception as e:
    st.error(f"⚠️ Error loading data: {e}")
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
# --- NEW DATE FILTER ---
selected_date = st.sidebar.selectbox(
    "Availibility Date", 
    options=date_cols[::-1], # Reverses the list so the newest date is on top
    key="date_filter"
)
all_sids = ["All Sites"] + sorted(df['SID'].astype(str).unique().tolist())
search_sid = st.sidebar.selectbox("Select Station ID", all_sids, key="sid_filter")
sel_region = st.sidebar.multiselect("Region Filter", options=sorted(df['REGION'].dropna().unique()), key="region_filter")
sel_tgl = st.sidebar.multiselect("TGL Filter", options=sorted(df['TGL'].dropna().unique()), key="tgl_filter")
# sharing_status = st.sidebar.selectbox("Sharing Status", options=sorted(df['SHARING STATUS'].dropna().unique()), key="sh_filter")

# --- NEW USF FILTER ---
usf_options = sorted(df['NEW USF SITES'].dropna().unique()) if 'NEW USF SITES' in df.columns else []
sel_usf = st.sidebar.multiselect("New USF Sites Filter", options=usf_options, key="usf_filter")

# --- REVENUE CAT FILTER ---
rev_options = sorted(df['REVENUE CAT'].dropna().unique()) if 'REVENUE CAT' in df.columns else []
sel_rev = st.sidebar.multiselect("Revenue Category Filter", options=rev_options, key="rev_filter")

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
# if sharing_status:
#     filt_df = filt_df[filt_df['SHARING STATUS'].isin(sharing_status)]
#     filters_active = True
if sel_rev:
    filt_df = filt_df[filt_df['REVENUE CAT'].isin(sel_rev)]
    filters_active = True 
# 6. CHART FUNCTION - FIXED PROPERTY PATHS
def create_advanced_chart(x_data, y_data, title, color, y_label, is_percent=True):
    x_clean = []
    for x in x_data:
        try:
            x_clean.append(datetime.strptime(str(x), '%Y-%m-%d').strftime('%d-%b'))
        except:
            x_clean.append(str(x).replace(' TCH%', '').split(' (FUEL)')[0])

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=x_clean, 
        y=y_data,
        mode='lines+markers+text', 
        text=[f"<b>{v:.2f}%</b>" if is_percent else f"<b>{v:.2f}</b>" for v in y_data], 
        textposition="top center", 
        textfont=dict(
            family="Inter, sans-serif",
            size=12,          
            color="#000000"   
        ),
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

    fig.update_layout(
        title=dict(
            text=f"<b>{title}</b>", 
            font=dict(size=20, color='#1e293b', family="Inter, sans-serif")
        ),
        margin=dict(l=40, r=40, t=100, b=40),
        height=450,
        # --- FIXED X-AXIS ---
        xaxis=dict(
            title=dict(
                text="<b>Timeline (Dates)</b>",
                font=dict(color="#000000", size=14) # Correct path
            ),
            tickfont=dict(color="#000000", size=11, family="Inter, sans-serif"),
            showline=True, 
            linecolor='#e2e8f0', 
            showgrid=False,
            type='category'
        ),
        # --- FIXED Y-AXIS ---
        yaxis=dict(
            title=dict(
                text="<b>Average A Per(%)</b>",
                font=dict(color="#000000", size=14) # Correct path
            ),
            tickfont=dict(color="#000000", size=11, family="Inter, sans-serif"),
            showgrid=True, 
            gridcolor='#f1f5f9', 
            zeroline=False,
            dtick=1,
            range=[max(0, min(y_data) - 0.5), min(100, max(y_data) + 1.5)] if len(y_data) > 0 else None
        ),
        plot_bgcolor='white',
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=False
    )
    
    return fig

# 7. DASHBOARD UI
st.markdown('<h1 style="color: #0f172a;">Network Intelligence Portal</h1>', unsafe_allow_html=True)

def create_tech_comparison_chart(tech_dict, dates):
    fig = go.Figure()
    # Colors: Zong Purple, Zong Green, Zong Blue
    colors = {"2G": "#7030a0", "3G": "#92d050", "4G": "#2e75b6"}
    
    for tech, t_df in tech_dict.items():
        # Find dates that exist in THIS specific sheet
        valid_dates = [d for d in dates if d in t_df.columns]
        if not valid_dates: continue
        
        # Calculate the average availability for the whole sheet for those dates
        y_values = t_df[valid_dates].apply(pd.to_numeric, errors='coerce').mean()
        
        fig.add_trace(go.Scatter(
            x=[str(d).split(' ')[0] for d in valid_dates], 
            y=y_values,
            name=tech,
            mode='lines+markers',
            line=dict(width=3, color=colors.get(tech, "#000")),
            hovertemplate=f"<b>{tech}</b>: %{{y:.2f}}%<extra></extra>"
        ))

    fig.update_layout(
        title="<b>2G / 3G / 4G Availability Comparison</b>",
        height=400,
        xaxis=dict(type='category', showgrid=False),
        yaxis=dict(title="Avg Avail %", range=[90, 100.5]),
        legend=dict(orientation="h", y=1.1, x=1, xanchor='right'),
        plot_bgcolor='white',
        hovermode="x unified"
    )
    return fig   

# --- TOP 3 METRIC CARDS (With Delta Analysis) ---
m1, m2, m3 = st.columns(3)

with m1:
    if selected_date and selected_date in filt_df.columns:
        # 1. Calculate Current Average
        current_val = pd.to_numeric(filt_df[selected_date], errors='coerce').mean()
        
        # 2. Delta Logic: Find the previous day's data
        delta_label = None
        try:
            # Find where the selected date sits in the list
            date_idx = date_cols.index(selected_date)
            if date_idx > 0:
                prev_date_col = date_cols[date_idx - 1]
                prev_val = pd.to_numeric(filt_df[prev_date_col], errors='coerce').mean()
                
                # Calculate the difference
                diff = current_val - prev_val
                delta_label = f"{diff:+.2f}% vs Prev. Day"
        except Exception:
            delta_label = "No prev. data"

        # 3. Display Metric with Delta
        st.metric(
            label=f"Avg Cell Availability ({selected_date})", 
            value=f"{current_val:.2f}%",
            delta=delta_label
        )
    else:
        st.metric("Availability Data", "N/A")

with m2:
    if latest_tch_col:
        # Average TCH% for selected USF/Non-USF sites
        val = pd.to_numeric(filt_df[latest_tch_col], errors='coerce').mean()
        st.metric(f"{display_date.split('-')[1]} Average TCH%", f"{val:.2f}%")

with m3:
    # Total count of active sites in the current filter
    st.metric("Total Active Sites", len(filt_df))

# --- TREND GRAPHS (TABBED INTERFACE) ---
if len(date_cols) > 1:
    st.markdown('<div class="graph-container">', unsafe_allow_html=True)
    
    # 1. Header and Range Selector (Common for all tabs)
    head_col, select_col = st.columns([4, 1])
    with head_col:
        st.markdown('<h3 style="color: #1e293b; margin-top: 0;">Performance Analytics</h3>', unsafe_allow_html=True)
    with select_col:
        num_days = st.selectbox(
            "Display Range",
            options=[7, 14, 21, 30],
            index=0,
            key="graph_duration_selector",
            label_visibility="collapsed"
        )

    # 2. Define the Tabs
    tab_site, tab_avail, tab_2g, tab_3g, tab_4g = st.tabs([
        "Site Availability", "Cell Availability", "2G Cell Availability", "3G Cell Availability", "4G Cell Availability"
    ])

    # 3. Helper Function to Process & Render each tech
    def render_tech_chart(tab_obj, tech_key, color, y_label):
        with tab_obj:
            t_df = tech_dfs.get(tech_key)
            if t_df is not None:
                # Apply Global Sidebar Filters to this specific tech dataframe
                t_filt = t_df.copy()
                if search_sid != "All Sites":
                    t_filt = t_filt[t_filt['SID'].astype(str) == search_sid]
                if sel_region:
                    t_filt = t_filt[t_filt['REGION'].isin(sel_region)]
                
                # Identify date columns for this sheet
                t_dates = [c for c in t_filt.columns if '-' in c and c[0].isdigit()]
                t_trend_days = t_dates[-num_days:]
                
                if t_trend_days:
                    # Calculate means
                    t_values = t_filt[t_trend_days].apply(pd.to_numeric, errors='coerce').mean()
                    
                    # Create the chart using your existing custom function
                    fig = create_advanced_chart(
                        t_trend_days, 
                        t_values, 
                        f"{tech_key} Trend (Last {len(t_trend_days)} Days)", 
                        color, 
                        y_label,
                        is_percent=(tech_key in ["AVAILABILITY", "SITE_AVAIL"])
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info(f"No date-based records found for {tech_key}")

    # 4. Fill the Tabs (Using Zong Purple & Green theme)
    render_tech_chart(tab_site, "SITE_AVAIL", "#0ea5e9", "Avail %")
    render_tech_chart(tab_avail, "AVAILABILITY", "#3b82f6", "Avail %") # Professional Blue
    render_tech_chart(tab_2g, "2G", "#7030a0", "Erlangs")             # Zong Purple
    render_tech_chart(tab_3g, "3G", "#92d050", "GBs")                 # Zong Green
    render_tech_chart(tab_4g, "4G", "#2e75b6", "GBs")                 # Tech Blue

    st.markdown('</div>', unsafe_allow_html=True)

# --- 8. SITE SPECIFIC DETAILS & MAP ---
if search_sid != "All Sites" and len(filt_df) == 1:
    st.write("---")
    row = filt_df.iloc[0]
    
    # DISPLAY SITE METADATA USING YOUR CUSTOM CSS
    st.markdown(f"### 📋 Site Information: {row['SID']}")
    
    # Row 1 of Details
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="detail-card"><div class="detail-label">Region</div><div class="detail-value">{row.get("REGION", "N/A")}</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="detail-card"><div class="detail-label">TGL</div><div class="detail-value">{row.get("TGL", "N/A")}</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="detail-card"><div class="detail-label">Site Category</div><div class="detail-value">{row.get("SITE CATEGORY", "N/A")}</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="detail-card"><div class="detail-label">Revenue Category</div><div class="detail-value">{row.get("REVENUE CAT", "N/A")}</div></div>', unsafe_allow_html=True)

    # Row 2 of Details
    st.markdown("<br>", unsafe_allow_html=True)
    c5, c6, c7, c8 = st.columns(4)
    with c5:
        st.markdown(f'<div class="detail-card"><div class="detail-label">On-Air Date</div><div class="detail-value">{row.get("ONAIRDATE", "N/A")}</div></div>', unsafe_allow_html=True)
    with c6:
        st.markdown(f'<div class="detail-card"><div class="detail-label">USF Status</div><div class="detail-value">{row.get("NEW USF SITES", "Non-USF")}</div></div>', unsafe_allow_html=True)
    with c7:
        st.markdown(f'<div class="detail-card"><div class="detail-label">Site Importance</div><div class="detail-value">{row.get("SITE IMPORTANCE", "N/A")}</div></div>', unsafe_allow_html=True)
    with c8:
        st.markdown(f'<div class="detail-card"><div class="detail-label">Sharing Status</div><div class="detail-value">{row.get("SHARING STATUS", "N/A")}</div></div>', unsafe_allow_html=True)

    # MAP SECTION
    st.markdown("### 📍 Geographic Location")
    lat = row.get('LATITUDE')
    lon = row.get('LONGITUDE')
    
    if pd.notnull(lat) and pd.notnull(lon):
        # Using a more robust Google Maps embed link
        map_url = f"https://www.google.com/maps?q={lat},{lon}&hl=en&z=15&output=embed"
        components.html(
            f'<iframe width="100%" height="450" frameborder="0" src="{map_url}"></iframe>',
            height=460,
        )
        st.link_button("🚀 Open in Google Maps App", f"https://www.google.com/maps/search/?api=1&query={lat},{lon}")
    else:
        st.warning("Coordinates not available for this site.")