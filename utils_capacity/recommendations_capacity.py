import plotly.express as px
import streamlit as st
import pandas as pd
from datetime import datetime
import numpy as np

from utils_capacity.recommendation_capacity.executive_summary import executive_summary
from utils_capacity.recommendation_capacity.infrastructure_inventory import infrastructure_inventory
from utils_capacity.recommendation_capacity.capacity_utilization import capacity_utilization
from utils_capacity.recommendation_capacity.capacity_planning import capacity_planning
from utils_capacity.recommendation_capacity.resource_efficiency import resource_efficiency
from utils_capacity.recommendation_capacity.bottleneck_identification import bottleneck_identification
from utils_capacity.recommendation_capacity.resource_allocation import resource_allocation
from utils_capacity.recommendation_capacity.workload_analysis import workload_analysis
from utils_capacity.recommendation_capacity.virtualization_cloud import virtualization_cloud
from utils_capacity.recommendation_capacity.storage_capacity import storage_capacity
from utils_capacity.recommendation_capacity.network_capacity import network_capacity
from utils_capacity.recommendation_capacity.energy_efficiency import energy_efficiency
from utils_capacity.recommendation_capacity.cost_benefit import cost_benefit
from utils_capacity.recommendation_capacity.risk_assessment import risk_assessment
from utils_capacity.recommendation_capacity.actionable_insight import actionable_insight
from utils_capacity.recommendation_capacity.implementation_plan import implementation_plan


def recommendations_capacity(df):
    
    # ── Date filter prep ────────────────────────────────────────────────────────
    if 'created_time' in df.columns and not df['created_time'].isna().all():
        st.markdown("---")
        st.subheader("Select Date Range")
        df = df.copy()
        df['created_time'] = pd.to_datetime(df['created_time'], errors='coerce')
        df['created_date'] = df['created_time'].dt.date

        # Guard against all-NaT after coercion
        if df['created_date'].notna().any():
            min_date = df['created_date'].min()
            max_date = df['created_date'].max()

            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input(
                    "Start Date",
                    value=min_date,
                    min_value=min_date,
                    max_value=max_date,
                    key="start_date_picker"
                )
            with col2:
                end_date = st.date_input(
                    "End Date",
                    value=max_date,
                    min_value=min_date,
                    max_value=max_date,
                    key="end_date_picker"
                )

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
            # created_time exists but all invalid → fall back to no date filter
            df_filtered = df.copy()
    else:
        df_filtered = df.copy()

    st.markdown("---")

#---------------------------------------------------------------------------------------------------------------------------------------------------

    st.subheader("📌 Infrastructure Overview Metrics")
    col1, col2, col3, col4, col5 = st.columns(5)

    # 1) Total Active Assets
    total_assets = df_filtered["asset_id"].nunique() if "asset_id" in df_filtered.columns else len(df_filtered)
    col1.metric("Total Active Assets", total_assets)

    # 2) Avg CPU
    avg_cpu = float(df_filtered["avg_cpu_utilization"].mean()) if "avg_cpu_utilization" in df_filtered.columns else 0.0
    col2.metric("Avg CPU Utilization (%)", f"{avg_cpu:.2f}")

    # 3) Avg Memory
    avg_mem = float(df_filtered["avg_memory_utilization"].mean()) if "avg_memory_utilization" in df_filtered.columns else 0.0
    col3.metric("Avg Memory Utilization (%)", f"{avg_mem:.2f}")

    # 4) Avg Storage
    avg_storage = float(df_filtered["avg_storage_utilization"].mean()) if "avg_storage_utilization" in df_filtered.columns else 0.0
    col4.metric("Avg Storage Utilization (%)", f"{avg_storage:.2f}")

    # 5) Total Monthly Cost — define DEFAULT FIRST to avoid UnboundLocalError
    total_cost = 0.0
    if "cost_per_month_usd" in df_filtered.columns:
        # Use numeric coercion to be safe if the column is object-typed strings
        total_cost = pd.to_numeric(df_filtered["cost_per_month_usd"], errors="coerce").fillna(0).sum()
        col5.metric("Total Monthly Cost (USD)", f"${total_cost:,.2f}")
    else:
        col5.metric("Total Monthly Cost (USD)", "N/A")

#--------------------------------------------------------------------------------------------------------------------------

    st.markdown("---")

    # 📊 EXECUTIVE SUMMARY
    st.header(" Executive Summary")
    executive_summary(df_filtered)

#----------------------------------------------------------------------------------------------------

    # 📊 INFRASTRUCTURE INVENTORY
    st.header(" Infrastructure Inventory")
    infrastructure_inventory(df_filtered)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------

    # 📊 CAPACITY UTILIZATION METRICS
    st.header(" Capacity Utilization Metrics")
    capacity_utilization(df_filtered)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------

    # 📊 Capacity Planning
    st.header(" Capacity Planning")
    capacity_planning(df_filtered)

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    
    # 📊 Resource Efficiency Analysis
    st.header(" Resource Efficiency Analysis")
    resource_efficiency(df_filtered)

#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    
    # 📊 Bottleneck Identification
    st.header(" Bottleneck Identification")
    bottleneck_identification(df_filtered)

#--------------------------------------------------------------------------------------------------------------------------

    # 📊 Resource Allocation and Rightsizing
    st.header(" Resource Allocation and Rightsizing")
    resource_allocation(df_filtered)
    
#----------------------------------------------------------------------------------------------------

    # 📊 Workload Analysis
    st.header(" Workload Analysis")
    workload_analysis(df_filtered)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------

    # 📊 Virtualization and Cloud Optimization
    st.header(" Virtualization and Cloud Optimization")
    virtualization_cloud(df_filtered)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------

    # 📊 Storage Capacity Analysis
    st.header(" Storage Capacity Analysis")
    storage_capacity(df_filtered)

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    
    # 📊 Network Capacity Analysis
    st.header(" Network Capacity Analysis")
    network_capacity(df_filtered)

#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    
    # 📊 Energy Efficiency and Sustainability
    st.header(" Energy Efficiency and Sustainability")
    energy_efficiency(df_filtered)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------

    # 📊 Cost-Benefit Analysis
    st.header(" Cost-Benefit Analysis")
    cost_benefit(df_filtered)

#-----------------------------------------------------------------------------------------------------------------------------------------------------------

    # 📊 Risk Assessment
    st.header(" Risk Assessment")
    risk_assessment(df_filtered)

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    
    # 📊 Actionable Insights
    st.header(" Actionable Insights")
    actionable_insight(df_filtered)

#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    
    # 📊 Implementation Plan
    st.header(" Implementation Plan")
    implementation_plan(df_filtered)

#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

     # ── Summary string (safe even if some columns missing) ─────────────────────
    summary_text = (
        f"Total Active Assets: {total_assets}\n"
        f"Avg CPU Utilization: {avg_cpu:.2f} %\n"
        f"Avg Memory Utilization: {avg_mem:.2f} %\n"
        f"Avg Storage Utilization: {avg_storage:.2f} %\n"
        f"Monthly Cost: ${total_cost:,.2f} USD"
    )
    # You can st.text(summary_text) or keep it for export
    # st.text(summary_text)

    return df_filtered
