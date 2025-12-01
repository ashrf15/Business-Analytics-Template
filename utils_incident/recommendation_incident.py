import plotly.express as px
import streamlit as st
import pandas as pd
from datetime import datetime
import numpy as np

from utils_incident.recommendation.incident_overview import incident_overview
from utils_incident.recommendation.incident_classification import incident_classification
from utils_incident.recommendation.response_and_resolution_times import response_and_resolution_times
from utils_incident.recommendation.incident_status import incident_status
from utils_incident.recommendation.root_cause_analysis import root_cause_analysis
from utils_incident.recommendation.incident_trends import incident_trends
from utils_incident.recommendation.service_impact import service_impact
from utils_incident.recommendation.resolution_action import resolution_action
from utils_incident.report_incident import _compute_overview_kpis


# ---------- Safe local fallback if upstream KPIs are missing ----------
def _fallback_overview_kpis(df: pd.DataFrame) -> dict:
    d = df.copy()

    # Parse time columns if present
    for c in ("created_time", "resolved_time"):
        if c in d.columns:
            d[c] = pd.to_datetime(d[c], errors="coerce")

    # Try to build resolution hours
    res_hrs = None
    if "resolution_time_hours" in d.columns:
        res_hrs = pd.to_numeric(d["resolution_time_hours"], errors="coerce")
    elif {"created_time", "resolved_time"} <= set(d.columns):
        res_hrs = (d["resolved_time"] - d["created_time"]).dt.total_seconds() / 3600.0

    avg_res_hrs = float(res_hrs.mean()) if res_hrs is not None and res_hrs.notna().any() else None

    # Departments involved
    if "department" in d.columns:
        depts = int(pd.Series(d["department"], dtype="object").dropna().astype(str).nunique())
    else:
        depts = 0

    return {
        "Total Tickets": int(len(d)),
        "Avg Resolution Time (hrs)": avg_res_hrs,  # may be None -> we render "—"
        "Departments Involved": depts,
    }


def _normalize_kpis(raw: dict, df_for_fallback: pd.DataFrame) -> dict:
    """
    Normalize any KPI dict to a stable schema:
      - Total Tickets
      - Avg Resolution Time (hrs)
      - Departments Involved
    Accepts alternative key names and fills gaps via fallback.
    """
    fb = _fallback_overview_kpis(df_for_fallback)

    def pick(keys, default):
        for k in keys:
            if k in raw and raw[k] is not None:
                return raw[k]
        return default

    total = pick(
        ["Total Tickets", "Total Incidents", "Tickets", "Count"],
        fb["Total Tickets"],
    )

    avg_res = pick(
        ["Avg Resolution Time (hrs)", "Average Resolution Time (hrs)", "Avg Resolution (hrs)", "Avg Resolution"],
        fb["Avg Resolution Time (hrs)"],
    )

    depts = pick(
        ["Departments Involved", "Unique Departments", "Departments"],
        fb["Departments Involved"],
    )

    # Final coercions/formatting safety
    try:
        total = int(total)
    except Exception:
        total = fb["Total Tickets"]

    try:
        avg_res = float(avg_res) if avg_res is not None else None
    except Exception:
        avg_res = fb["Avg Resolution Time (hrs)"]

    try:
        depts = int(depts)
    except Exception:
        depts = fb["Departments Involved"]

    return {
        "Total Tickets": total,
        "Avg Resolution Time (hrs)": avg_res,
        "Departments Involved": depts,
    }


def recommendation_incident(df: pd.DataFrame):
    st.markdown("---")
    st.subheader("Select Date Range")

    # ---------------- Date filter ----------------
    if "created_time" in df.columns and not df["created_time"].isna().all():
        df = df.copy()
        df["created_time"] = pd.to_datetime(df["created_time"], errors="coerce")
        df["created_date"] = df["created_time"].dt.date

        min_date = df["created_date"].min()
        max_date = df["created_date"].max()

        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Start Date",
                value=min_date,
                min_value=min_date,
                max_value=max_date,
                key="start_date_picker",
            )
        with col2:
            end_date = st.date_input(
                "End Date",
                value=max_date,
                min_value=min_date,
                max_value=max_date,
                key="end_date_picker",
            )

        st.markdown(
            f"🗓️ **Selected Range:** `{start_date.strftime('%d/%m/%Y')}` → `{end_date.strftime('%d/%m/%Y')}`"
        )

        reset_filter = st.button("🔁 Reset to Default", key="reset_button_2")

        if reset_filter:
            df_filtered = df.copy()
            st.info("Showing all available data (no date filter applied).")
        elif start_date > end_date:
            st.warning("⚠️ Start date is after end date. Please select a valid range.")
            return
        else:
            df_filtered = df[
                (df["created_date"] >= start_date) & (df["created_date"] <= end_date)
            ]
    else:
        df_filtered = df.copy()

    st.markdown("---")

    # ---------------- KPIs (safe) ----------------
    st.subheader("📌 Overview Metrics")

    # Try upstream KPIs; normalize; fallback fills any gap
    try:
        upstream = _compute_overview_kpis(df_filtered)
        if not isinstance(upstream, dict):
            upstream = {}
    except Exception:
        upstream = {}

    kpis = _normalize_kpis(upstream, df_filtered)

    c1, c2, c3 = st.columns(3)
    # Total Tickets – guaranteed
    c1.metric("Total Tickets", f"{kpis['Total Tickets']:,}")

    # Avg Resolution Time (hrs) – show "—" if None
    avg_res_val = kpis.get("Avg Resolution Time (hrs)")
    c2.metric(
        "Avg Resolution Time (hrs)",
        f"{avg_res_val:.2f}" if isinstance(avg_res_val, (int, float)) else "—",
    )

    # Departments Involved – guaranteed int
    c3.metric("Departments Involved", kpis.get("Departments Involved", 0))

    st.markdown("---")

    # =========================
    # Sections (use filtered df)
    # =========================

    # 📦 INCIDENT OVERVIEW
    st.header("📦 Incident Overview")
    incident_overview(df_filtered)

    # 📦 INCIDENT CLASSIFICATION
    st.header("📦 Incident Classification")
    incident_classification(df_filtered)

    # 📦 RESPONSE AND RESOLUTION TIMES
    st.header("📦 Response and Resolution Time")
    response_and_resolution_times(df_filtered)

    # 📦 INCIDENT STATUS
    st.header("📦 Incident Status")
    incident_status(df_filtered)

    # 📦 ROOT CAUSE
    st.header("📦 Root Cause Analysis")
    root_cause_analysis(df_filtered)

    # 📦 INCIDENT TRENDS
    st.header("📦 Incident Trends")
    incident_trends(df_filtered)

    # (If you want to include these later)
    # st.header("📦 Service Impact")
    # service_impact(df_filtered)
    # st.header("📦 Resolution Action")
    # resolution_action(df_filtered)

    return df_filtered
