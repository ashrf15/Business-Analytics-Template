import plotly.express as px
import streamlit as st
import pandas as pd
from datetime import datetime
import numpy as np

from utils_scorecard.recommendation.service_overview import service_overview
from utils_scorecard.recommendation.service_availability import service_availability
from utils_scorecard.recommendation.service_response_resolution_time import service_response_resolution_time
from utils_scorecard.recommendation.incident_problem_management import incident_problem_management
from utils_scorecard.recommendation.change_management import change_management
from utils_scorecard.recommendation.service_desk_performance import service_desk_performance
from utils_scorecard.recommendation.security_metrics import security_metrics
from utils_scorecard.recommendation.capacity_scalability import capacity_scalability


def recommendation_scorecard(df):

    if 'created_time' in df.columns and not df['created_time'].isna().all():
        st.markdown("---")
        st.subheader("Select Date Range")
        df['created_time'] = pd.to_datetime(df['created_time'], errors='coerce')
        df['created_date'] = df['created_time'].dt.date
        min_date = df['created_date'].min()
        max_date = df['created_date'].max()

        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", value=min_date, min_value=min_date, max_value=max_date, key="start_date_picker")
        with col2:
            end_date = st.date_input("End Date", value=max_date, min_value=min_date, max_value=max_date, key="end_date_picker")

        st.markdown(f"🗓️ **Selected Range:** `{start_date.strftime('%d/%m/%Y')}` → `{end_date.strftime('%d/%m/%Y')}`")

        reset_filter = st.button("🔁 Reset to Default", key="reset_button_2")

        if reset_filter:
            df_filtered = df.copy()
            st.info("Showing all available data (no date filter applied).")
        elif start_date > end_date:
            st.warning("⚠️ Start date is after end date. Please select a valid range.")
            return
        else:
            df_filtered = df[(df['created_date'] >= start_date) & (df['created_date'] <= end_date)]
    else:
        df_filtered = df.copy()

    st.markdown("---")

#---------------------------------------------------------------------------------------------------------------------------------------------------

    st.subheader("📌 Overview Metrics")
    col1, col2, col3, col4, col5 = st.columns(5)

    # Total tickets
    total_tickets = len(df_filtered)
    col1.metric("Total Tickets", total_tickets)

    # Closed & Open tickets (if status column exists)
    closed_count = None
    open_count = None
    if "status" in df_filtered.columns:
        closed_count = df_filtered["status"].astype(str).str.lower().isin(
            ["closed", "resolved", "completed", "done"]
        ).sum()
        open_count = total_tickets - closed_count

    if closed_count is not None:
        col2.metric("Closed Tickets", closed_count)
        col3.metric("Open Tickets (Backlog)", open_count)
    else:
        col2.metric("Closed Tickets", "N/A")
        col3.metric("Open Tickets (Backlog)", "N/A")

    # Avg resolution time
    if "service_availability" in df_filtered.columns and not df_filtered["service_availability"].dropna().empty:
        avg_res_time = df_filtered["service_availability"].mean()
        col4.metric("Avg Resolution Time (hrs)", f"{avg_res_time:.2f}")
    else:
        col4.metric("Avg Resolution Time (hrs)", "N/A")

    # Departments involved (if department column exists)
    if "department" in df_filtered.columns:
        col5.metric("Departments Involved", df_filtered["department"].nunique())
    else:
        col5.metric("Departments Involved", "N/A")
#--------------------------------------------------------------------------------------------------------------------------

    # 📊 SERVICE OVERVIEW ANALYSIS
    st.header(" Service Overview Analysis")
    service_overview(df_filtered)

#----------------------------------------------------------------------------------------------------

    # 📊 SERVICE AVAILABILITY
    st.header(" Service Availability")
    service_availability(df_filtered)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------

    # 📊 RESPONSE & RESOLUTION TIME
    st.header(" Response & Resolution Time")
    service_response_resolution_time(df_filtered)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------

    # 📊 INCIDENT & PROBLEM MANAGEMENT
    st.header(" Incident & Problem Management")
    incident_problem_management(df_filtered)

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    # 📊 CHANGE MANAGEMENT
    st.header(" Change Management")
    change_management(df_filtered)

#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    # 📊 SERVICE DESK PERFORMANCE
    st.header(" Service Desk Performance")
    service_desk_performance(df_filtered)

#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    # 📊 SECURITY METRICS
    st.header(" Security Metrics")
    security_metrics(df_filtered)

#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    # 📊 CAPACITY & SCALABILITY
    st.header(" Capacity & Scalability")
    capacity_scalability(df_filtered)

#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
