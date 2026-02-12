import streamlit as st
import pandas as pd
import os

# Configuration
st.set_page_config(page_title="Cell Availability Portal", layout="wide")
DATA_FILE = "current_availability.csv"
ADMIN_PASSWORD = "admin123"  # Change this to your preferred password

st.title("📊 Daily Cell Availability Dashboard")

# --- SIDEBAR: ADMIN UPLOAD ---
st.sidebar.title("Admin Panel")
status_placeholder = st.sidebar.empty()

if st.sidebar.text_input("Admin Password", type="password") == ADMIN_PASSWORD:
    uploaded_file = st.sidebar.file_uploader("Upload Daily Excel/CSV", type=['xlsx', 'csv'])
    
    if uploaded_file:
        try:
            if uploaded_file.name.endswith('.xlsx'):
                df_new = pd.read_excel(uploaded_file)
            else:
                df_new = pd.read_csv(uploaded_file)
            
            # Save as CSV for the public to view
            df_new.to_csv(DATA_FILE, index=False)
            status_placeholder.success("✅ File updated successfully!")
        except Exception as e:
            status_placeholder.error(f"Error: {e}")

# --- MAIN VIEW: PUBLIC DATA ---
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)

    # Search and Filters
    search_query = st.text_input("🔍 Search by SID or Grid", "")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        regions = st.multiselect("Region", options=sorted(df['Region'].unique().tolist()))
    with col2:
        techs = st.multiselect("Technology", options=sorted(df['Technology'].unique().tolist()))
    with col3:
        cat = st.multiselect("Site Category", options=sorted(df['Site Category'].unique().tolist()))

    # Apply Filtering Logic
    filtered_df = df.copy()
    if search_query:
        filtered_df = filtered_df[
            filtered_df['SID'].astype(str).str.contains(search_query, case=False) | 
            filtered_df['Grid '].astype(str).str.contains(search_query, case=False)
        ]
    if regions:
        filtered_df = filtered_df[filtered_df['Region'].isin(regions)]
    if techs:
        filtered_df = filtered_df[filtered_df['Technology'].isin(techs)]
    if cat:
        filtered_df = filtered_df[filtered_df['Site Category'].isin(cat)]

    # Display Data
    st.subheader(f"Current Stats ({len(filtered_df)} Sites)")
    st.dataframe(filtered_df, use_container_width=True)

else:
    st.info("👋 Welcome! Please wait for the Admin to upload today's availability sheet.")