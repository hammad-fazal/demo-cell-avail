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
    st.stop() # Stops the rest of the page (Data/CSS/Charts) from loading

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


# 3. GOOGLE SHEETS CONNECTION
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    # Read the data from Google Sheets
    df = conn.read(ttl=0) 
    
    # Standardize column names (Fixes KeyError for 'GRID ' or 'REVENUE CAT ')
    df.columns = [str(c).strip().upper() for c in df.columns]
    
    # --- UPDATED REFRESH LOGIC ---
    if st.sidebar.button("Clear Filters", use_container_width=True):
        # 1. Clear the streamlit cache to pull fresh data from the sheet
        st.cache_data.clear()
        
        # 2. Clear filter keys from session state so the UI resets
        keys_to_reset = ["sid_filter", "region_filter", "tgl_filter", "usf_filter", "rev_filter", "date_filter"]
        for key in keys_to_reset:
            if key in st.session_state:
                st.session_state[key] = "All Sites" if key == "sid_filter" else []
        
        # 3. Rerun the app to show updated numbers in the 3 cards
        st.rerun()
    
    st.sidebar.success("📡 Connected to Live Data")

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
            dtick=0.5,
            range=[max(0, min(y_data) - 0.5), min(100, max(y_data) + 1.5)] if len(y_data) > 0 else None
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

# --- TOP 3 METRIC CARDS ---
m1, m2, m3 = st.columns(3)

with m1:
    # Uses the selected date from the sidebar for Availability
    if selected_date and selected_date in filt_df.columns:
        val = pd.to_numeric(filt_df[selected_date], errors='coerce').mean()
        st.metric(f"Avg Cell Availability ({selected_date})", f"{val:.2f}%")
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


# --- TREND GRAPH WITH DURATION SELECTOR ---
if len(date_cols) > 1:
    # 1. Open the CSS container FIRST
    st.markdown('<div class="graph-container">', unsafe_allow_html=True)
    
    # 2. Layout for Header and Selector (now inside the div)
    head_col, select_col = st.columns([4, 1])
    
    with head_col:
        # Using markdown for the header to prevent extra top-margin inside the container
        st.markdown('<h3 style="color: #1e293b; margin-top: 0;">Cell Availibility</h3>', unsafe_allow_html=True)

    with select_col:
        # User chooses how many days to show
        num_days = st.selectbox(
            "Display Range",
            options=[7, 14, 21, 30],
            index=0,  # Default to 7 days
            key="graph_duration_selector",
            label_visibility="collapsed" # Hides the text label so it looks cleaner next to the title
        )
    
    # 3. Slice date columns based on user selection
    trend_days = date_cols[-num_days:]
    
    # Calculate means for the selected timeline
    day_values = filt_df[trend_days].apply(pd.to_numeric, errors='coerce').mean()
    
    # 4. Render the chart
    st.plotly_chart(
        create_advanced_chart(
            trend_days, 
            day_values, 
            f"Last {len(trend_days)} Days", 
            "#3b82f6", 
            "Availability"
        ), 
        use_container_width=True
    )
    
    # 5. Close the CSS container LAST
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


# 8. SITE LOCATION MAP
if search_sid != "All Sites" and len(filt_df) == 1:
    st.markdown(f"### 📍 Site Location: {filt_df.iloc[0]['SID']}")
    
    # Extract coordinates
    # Replace 'LATITUDE' and 'LONGITUDE' with the exact column names in your sheet
    lat = filt_df.iloc[0].get('LATITUDE')
    lon = filt_df.iloc[0].get('LONGITUDE')
    
    if pd.notnull(lat) and pd.notnull(lon):
        
        # 1. Create the Google Maps Embed URL
        # 'q' is the query (lat,lon), 't=k' is satellite, 'z' is zoom level
        google_maps_embed = f"https://www.google.com/maps?q={lat},{lon}&hl=en&z=14&output=embed"
        
        # 2. Embed using an IFRAME
        components.html(
            f"""
            <iframe 
                width="100%" 
                height="450" 
                frameborder="0" 
                scrolling="no" 
                marginheight="0" 
                marginwidth="0" 
                src="{google_maps_embed}">
            </iframe>
            """,
            height=460,
        )
    
    # Optional button to open full site
    st.link_button("Open in Google Maps App", f"https://www.google.com/maps/search/?api=1&query={lat},{lon}")