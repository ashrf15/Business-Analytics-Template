import plotly.express as px
import streamlit as st
import pandas as pd
from datetime import datetime
import numpy as np

from utils_service_availability.recommendation_service_availability.executive_summary import executive_summary
from utils_service_availability.recommendation_service_availability.service_overview import service_overview
from utils_service_availability.recommendation_service_availability.service_availability import service_availability
from utils_service_availability.recommendation_service_availability.historical_availability import historical_availability
from utils_service_availability.recommendation_service_availability.incident_analysis import incident_analysis
from utils_service_availability.recommendation_service_availability.planned_maintenance import planned_maintenance
from utils_service_availability.recommendation_service_availability.emergency_changes import emergency_changes
from utils_service_availability.recommendation_service_availability.service_recovery import service_recovery
from utils_service_availability.recommendation_service_availability.business_impact import business_impact
from utils_service_availability.recommendation_service_availability.resource_utilization import resource_utilization


def recommendation_service(df):

    if 'created_time' in df.columns and not df['created_time'].isna().all():
        df['created_time'] = pd.to_datetime(df['created_time'], errors='coerce')
        df['created_date'] = df['created_time'].dt.date
        min_date = df['created_date'].min()
        max_date = df['created_date'].max()

        st.markdown("---")
        st.subheader("Select Date Range")

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

#------------------------------------------------------------------------------------------------------------------------------------------------------------------

    col1, col2, col3, col4 = st.columns(4)

    avg_uptime = df["uptime_percentage"].mean() if "uptime_percentage" in df.columns else np.nan
    total_dt   = df["downtime_minutes"].sum() if "downtime_minutes" in df.columns else np.nan
    total_inc  = df["incident_count"].sum() if "incident_count" in df.columns else np.nan
    total_cost = df["estimated_cost_downtime"].sum() if "estimated_cost_downtime" in df.columns else np.nan

    col1.metric("Average Uptime (%)", f"{avg_uptime:.2f}%" if pd.notna(avg_uptime) else "N/A")
    col2.metric("Total Downtime (mins)", f"{total_dt:,.0f}" if pd.notna(total_dt) else "N/A")
    col3.metric("Total Incidents", f"{total_inc:,.0f}" if pd.notna(total_inc) else "N/A")
    col4.metric("Total Downtime Cost (RM)", f"{total_cost:,.0f}" if pd.notna(total_cost) else "N/A")

#--------------------------------------------------------------------------------------------------------------------------

    st.markdown("---")

    # 📊 Executive Summary
    st.header(" Executive Summary")
    executive_summary(df_filtered)
#----------------------------------------------------------------------------------------------------

    # 📊 Service Overview
    st.header(" Service Overview")
    service_overview(df_filtered)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------

    # 📊 Service Availibility Metrics
    st.header(" Service Availibility Metrics")
    service_availability(df_filtered)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------

    # 📊 Historical Availibility Trends
    st.header(" Historical Availability Trends")
    historical_availability(df_filtered)

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    
    # 📊 Incident Analysis
    st.header(" Incident Analysis")
    incident_analysis(df_filtered)

#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    
    # 📊 Planned Maintenance and Downtime
    st.header(" Planned Maintenance and Downtime")
    planned_maintenance(df_filtered)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------

    # 📊 Emergency Changes and Their Impacts
    st.header(" Emergency Changes and Their Impacts")
    emergency_changes(df_filtered)

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    
    # 📊 Service Recovery Time
    st.header(" Service Recovery Time")
    service_recovery(df_filtered)

#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    
    # 📊 Business Impact Analysis
    st.header(" Business Impact Analysis")
    business_impact(df_filtered)

#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
 
    # 📊 Resource Utilization and Scalability
    st.header(" Resource Utilization and Scalability")
    resource_utilization(df_filtered)

#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    summary_text = f"""
    Total Tickets: {len(df_filtered)}
    Unique Departments: {df_filtered['department'].nunique() if 'department' in df_filtered.columns else 'N/A'}
    Top Technician: {df_filtered['technician'].value_counts().idxmax() if 'technician' in df_filtered.columns else 'N/A'}
    Peak Hour: {df_filtered['created_time'].dt.hour.mode()[0] if 'created_time' in df_filtered.columns else 'N/A'}
    """

    return df_filtered

