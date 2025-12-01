import plotly.express as px
import streamlit as st
import pandas as pd
from datetime import datetime
import numpy as np

from utils_service_desk_pfomance.recommendation_performance.ticket_volume import ticket_volume
from utils_service_desk_pfomance.recommendation_performance.resolution_time import resolution_time
from utils_service_desk_pfomance.recommendation_performance.customer_satisfaction import customer_satisfaction
from utils_service_desk_pfomance.recommendation_performance.technician_performance import technician_performance
from utils_service_desk_pfomance.recommendation_performance.incident_trends import incident_trends
from utils_service_desk_pfomance.recommendation_performance.sla import sla


def recommendation_ticketing(df):
    st.markdown("---")
    st.subheader("Select Date Range")

    # ---- Namespaced widget keys to avoid cross-tab collisions
    KEY_START = "rec_start_date_picker"
    KEY_END = "rec_end_date_picker"
    KEY_RESET = "rec_reset_button"

    # ---- Build a working copy
    df = df.copy()

    # ---- Try to coerce created_time early so later code can rely on datetime
    if "created_time" in df.columns:
        df["created_time"] = pd.to_datetime(df["created_time"], errors="coerce")
        df["created_date"] = df["created_time"].dt.date

    # ---- Date filter UI
    if "created_date" in df.columns and not df["created_date"].dropna().empty:
        min_date = pd.Series(df["created_date"]).min()
        max_date = pd.Series(df["created_date"]).max()

        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", value=min_date, min_value=min_date, max_value=max_date, key=KEY_START)
        with col2:
            end_date = st.date_input("End Date", value=max_date, min_value=min_date, max_value=max_date, key=KEY_END)

        st.markdown(f"🗓️ **Selected Range:** `{start_date.strftime('%d/%m/%Y')}` → `{end_date.strftime('%d/%m/%Y')}`")

        reset_filter = st.button("🔁 Reset to Default", key=KEY_RESET)

        if reset_filter:
            df_filtered = df.copy()
            st.info("Showing all available data (no date filter applied).")
        elif start_date > end_date:
            st.warning("⚠️ Start date is after end date. Please select a valid range.")
            return
        else:
            df_filtered = df[(df["created_date"] >= start_date) & (df["created_date"] <= end_date)].copy()
    else:
        df_filtered = df.copy()

    st.markdown("---")

    # ---------------------------------------------------------------------
    # 📌 Overview Metrics
    st.subheader("📌 Overview Metrics")
    col1, col2, col3, col4, col5 = st.columns(5)

    # Total tickets
    total_tickets = len(df_filtered)
    col1.metric("Total Tickets", total_tickets)

    # Closed & Open tickets — try request_status first, then fallback to status
    closed_count = None
    open_count = None
    status_col = None
    for candidate in ["request_status", "status"]:
        if candidate in df_filtered.columns:
            status_col = candidate
            break

    if status_col:
        status_series = df_filtered[status_col].astype(str).str.lower()
        closed_count = status_series.isin(["closed", "resolved", "completed", "done"]).sum()
        open_count = total_tickets - closed_count
        col2.metric("Closed Tickets", int(closed_count))
        col3.metric("Open Tickets (Backlog)", int(open_count))
    else:
        col2.metric("Closed Tickets", "N/A")
        col3.metric("Open Tickets (Backlog)", "N/A")

    # Avg resolution time (safe numeric)
    avg_res_str = "N/A"
    if "resolution_time" in df_filtered.columns:
        avg_res = pd.to_numeric(df_filtered["resolution_time"], errors="coerce").mean()
        if pd.notna(avg_res):
            avg_res_str = f"{avg_res:.2f}"
    col4.metric("Avg Resolution Time (hrs)", avg_res_str)

    # Departments involved
    if "department" in df_filtered.columns:
        col5.metric("Departments Involved", int(df_filtered["department"].nunique()))
    else:
        col5.metric("Departments Involved", "N/A")
#--------------------------------------------------------------------------------------------------------------------------

    st.markdown("---")

    # 📊 TICKET VOLUME ANALYSIS
    st.header(" Ticket Volume Analysis")
    ticket_volume(df_filtered)
#----------------------------------------------------------------------------------------------------

    # 📊 Response & Resolution Time
    st.header(" Response & Resolution Time")
    resolution_time(df_filtered)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------

    # 📊 Customer Satisfaction
    st.header(" Customer Satisfaction")
    customer_satisfaction(df_filtered)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------

    # 📊 Technician Workload Analysis
    st.header(" Agent/Technician Performance")
    technician_performance(df_filtered)

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    
    # 📊 Incident Trends
    st.header(" Incident Trends")
    incident_trends(df_filtered)

#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    
    # 📊 Incident Trends
    st.header(" Service Level Agreements (SLAs)")
    sla(df_filtered)

#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    # Peak hour: only if created_time is datetime and has non-null values
    peak_hour_str = "N/A"
    if "created_time" in df_filtered.columns:
        ct = pd.to_datetime(df_filtered["created_time"], errors="coerce")
        if ct.notna().any():
            mh = ct.dt.hour.mode()
            if not mh.empty:
                peak_hour_str = str(int(mh.iloc[0]))

    # SLA compliance if both columns exist & numeric
    sla_str = "N/A"
    if ("resolution_time" in df_filtered.columns) and ("sla_hours" in df_filtered.columns):
        rt = pd.to_numeric(df_filtered["resolution_time"], errors="coerce")
        sh = pd.to_numeric(df_filtered["sla_hours"], errors="coerce")
        mask = pd.notna(rt) & pd.notna(sh)
        if mask.any():
            sla_comp = (rt[mask] <= sh[mask]).mean() * 100
            sla_str = f"{sla_comp:.2f}%"

    dept_str = df_filtered["department"].nunique() if "department" in df_filtered.columns else "N/A"
    avg_res_for_summary = avg_res_str  # already computed safely above

    summary_text = f"""
    Total Tickets: {len(df_filtered)}
    Avg Resolution Time: {avg_res_for_summary if avg_res_for_summary != 'N/A' else 'N/A'} hrs
    Unique Departments: {dept_str}
    SLA Compliance: {sla_str}
    Top Technician: {df_filtered['technician'].value_counts().idxmax() if 'technician' in df_filtered.columns and not df_filtered['technician'].dropna().empty else 'N/A'}
    Peak Hour: {peak_hour_str}
    """

    return df_filtered