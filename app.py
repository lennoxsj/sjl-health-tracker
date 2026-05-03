import streamlit as st
from src.ingest.data_loader import load_all
from src.dashboard.tabs import main_tab, activity_log_tab, goals_tab

st.set_page_config(
    page_title="Sarah's Health Tracker",
    page_icon="💪",
    layout="wide",
)

data = load_all()

tab1, tab2, tab3 = st.tabs(["Sarah's Health Tracker", "Activity Log", "Goals"])

with tab1:
    main_tab.render(data)

with tab2:
    activity_log_tab.render(data)

with tab3:
    goals_tab.render(data)
