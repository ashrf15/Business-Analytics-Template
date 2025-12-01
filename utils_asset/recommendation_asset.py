import plotly.express as px
import streamlit as st
import pandas as pd
from datetime import datetime
import numpy as np


from utils_asset.recommendation.asset_overview import asset_overview
from utils_asset.recommendation.asset_hardware import asset_hardware
from utils_asset.recommendation.asset_software import asset_software
from utils_asset.recommendation.asset_assignments import asset_assignments
from utils_asset.recommendation.asset_lifecycle import asset_lifecycle

#------------------------------------------------------------------------------------------------------------------------------

def recommendation_asset(df):
    st.markdown("---")

    if 'created_time' in df.columns and not df['created_time'].isna().all():
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

#----------------------------------------------------------------------------------------------------------------------------------------------

    st.subheader("📌 Overview Metrics")
    k1, k2, k3, k4 = st.columns(4)

    # ===== Replaced with Key Metrics logic from dashboard_asset.py =====
    # Total assets (nunique of __asset_id__ if present, else row count)
    total_assets = df_filtered["__asset_id__"].nunique() if "__asset_id__" in df_filtered.columns else len(df_filtered)
    k1.metric("Total Assets", f"{total_assets:,}")

    # In-use % (by __asset_status__)
    inuse_pct = None
    if "__asset_status__" in df_filtered.columns:
        stat = df_filtered["__asset_status__"].astype(str).str.lower().str.strip()
        denom = stat.notna().sum()
        if denom > 0:
            inuse_pct = (stat.eq("in use").sum() / denom) * 100.0
    k2.metric("In-Use (%)", f"{inuse_pct:.1f}%" if inuse_pct is not None else "N/A")

    # Unique brands
    uniq_brands = df_filtered["__brand__"].nunique() if "__brand__" in df_filtered.columns else np.nan
    k3.metric("Unique Brands", f"{int(uniq_brands):,}" if pd.notna(uniq_brands) else "N/A")

    # Warranties expiring next 60 days
    expiring_60 = None
    if "warranty_end" in df_filtered.columns:
        w_end = pd.to_datetime(df_filtered["warranty_end"], errors="coerce")
        now = pd.Timestamp.today().normalize()
        soon = now + pd.Timedelta(days=60)
        expiring_60 = int(w_end.between(now, soon, inclusive="both").sum())
    k4.metric("Expiring ≤60 Days", f"{expiring_60:,}" if expiring_60 is not None else "N/A")
    # ===== End replacement =====

    st.markdown("---")

#----------------------------------------------------------------------------------------------------------------------------------------------

    # 📦 ASSET OVERVIEW
    st.header("📦 Asset Overview")
    asset_overview(df)

#----------------------------------------------------------------------------------------------------------------------------------------------

    # 📦 HARDWARE ASSETS
    st.header("📦 Hardware Assets")
    asset_hardware(df)

#---------------------------------------------------------------------------------------------------------------------------------------------
    
    # 📦 SOFTWARE ASSETS
    st.header("📦 Software Assets")
    asset_software(df)

#----------------------------------------------------------------------------------------------------------------------------------------------

     # 📦 ASSETS ASSIGNMENTS
    st.header("📦 Assets Assignments")
    asset_assignments(df)

#----------------------------------------------------------------------------------------------------------------------------------------------

     # 📦 ASSETS LIFECYCLE
    st.header("📦 Assets Lifecycle")
    asset_lifecycle(df)
