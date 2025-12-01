import plotly.express as px
import streamlit as st
import pandas as pd
import numpy as np

from utils_change_management.recommendation_modules.change_overview import change_overview
from utils_change_management.recommendation_modules.change_classification import change_classification
from utils_change_management.recommendation_modules.change_success_rate import change_success_rate
from utils_change_management.recommendation_modules.change_status import change_status
from utils_change_management.recommendation_modules.approval_process import approval_process
from utils_change_management.recommendation_modules.impact_assessment import impact_assessment
from utils_change_management.recommendation_modules.window_utilization import window_utilization
from utils_change_management.recommendation_modules.emergency_changes import emergency_changes

def recommendation_change(df):
    st.markdown("## 📊 Change Management Summary — Data Analysis & Recommendations")
    st.markdown("---")

    # Normalize column names
    df.columns = [c.strip().replace(" ", "_").lower() for c in df.columns]

    # --- Date range filter ---
    st.subheader("Select Date Range")

    if "implemented_date" in df.columns:
        df["implemented_date"] = pd.to_datetime(df["implemented_date"], errors="coerce")
        valid_dates = df["implemented_date"].dropna()

        if valid_dates.empty:
            st.warning("⚠️ No valid Implemented_Date found in dataset. Showing all data.")
            df_filtered = df.copy()
        else:
            min_date = valid_dates.min().date()
            max_date = valid_dates.max().date()

            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start Date", value=min_date, min_value=min_date, max_value=max_date, key="change_start")
            with col2:
                end_date = st.date_input("End Date", value=max_date, min_value=min_date, max_value=max_date, key="change_end")

            st.markdown(f"🗓️ **Selected Range:** `{start_date.strftime('%d/%m/%Y')}` → `{end_date.strftime('%d/%m/%Y')}`")

            reset_filter = st.button("🔁 Reset to Default", key="reset_change")

            if reset_filter:
                df_filtered = df.copy()
                st.info("Showing all available data (no date filter applied).")
            elif start_date > end_date:
                st.warning("⚠️ Start date is after end date. Please select a valid range.")
                df_filtered = df.copy()
            else:
                df_filtered = df[
                    (df["implemented_date"].dt.date >= start_date)
                    & (df["implemented_date"].dt.date <= end_date)
                ]
    else:
        st.warning("⚠️ 'Implemented_Date' column not found. Using full dataset.")
        df_filtered = df.copy()

    st.markdown("---")

    # --- Overview Metrics ---
    st.subheader("📌 Overview Metrics")
    col1, col2, col3, col4 = st.columns(4)

    total_changes = len(df_filtered)
    implemented = df_filtered["status"].astype(str).str.lower().eq("implemented").sum() if "status" in df_filtered.columns else 0
    backlog = total_changes - implemented
    emergency = df_filtered["emergency_flag"].astype(str).str.lower().isin(["yes", "true"]).sum() if "emergency_flag" in df_filtered.columns else 0
    avg_approval = df_filtered["approval_duration"].mean() if "approval_duration" in df_filtered.columns else np.nan

    col1.metric("Total Changes", total_changes)
    col2.metric("Implemented Changes", implemented)
    col3.metric("Backlog Changes", backlog)
    col4.metric("Emergency Changes", emergency)

    st.markdown("---")

    # --- Analytical Modules (aligned with Service Desk layout) ---
    st.header("📊 Change Overview")
    change_overview(df_filtered)

    st.header("📊 Change Classification Analysis")
    change_classification(df_filtered)

    st.header("📊 Change Success Rate")
    change_success_rate(df_filtered)

    st.header("📊 Change Status Analysis")
    change_status(df_filtered)

    st.header("📊 Approval Process Efficiency")
    approval_process(df_filtered)

    st.header("📊 Impact Assessment (High/Medium/Low)")
    impact_assessment(df_filtered)

    st.header("📊 Change Window Utilization")
    window_utilization(df_filtered)

    st.header("📊 Emergency Change Insights")
    emergency_changes(df_filtered)

    # --- Summary block ---
    summary_text = f"""
    **Total Changes:** {total_changes}  
    **Implemented:** {implemented}  
    **Emergency Changes:** {emergency}  
    **Backlog:** {backlog}    
    """

    st.info("### 📄 Summary Insight Overview")
    st.markdown(summary_text)

    return df_filtered
