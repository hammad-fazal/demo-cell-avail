import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Admin Portal", layout="centered")

st.title("🔐 Admin Upload Portal")
st.info("This page is for data management. Use the sidebar to navigate to the Public Dashboard.")

DATA_PATH = "current_availability.csv"

# Create data folder if it doesn't exist
if not os.path.exists("data"):
    os.makedirs("data")

# Admin Login
password = st.text_input("Enter Admin Password to Upload", type="password")

if password == "admin123": # Change this!
    st.success("Access Granted")
    uploaded_file = st.file_uploader("Upload Today's Cell Availability (Excel or CSV)", type=['xlsx', 'csv'])
    
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.xlsx'):
                df = pd.read_excel(uploaded_file)
            else:
                df = pd.read_csv(uploaded_file)
            
            # Save to the shared data folder
            df.to_csv(DATA_PATH, index=False)
            st.success("✅ File uploaded successfully! Everyone can now see the updated data on the Dashboard page.")
            st.balloons()
        except Exception as e:
            st.error(f"Error processing file: {e}")
else:
    if password != "":
        st.error("Incorrect Password")

st.markdown("---")
st.write("👈 **Navigate to the 'Dashboard' in the sidebar to view the data.**")