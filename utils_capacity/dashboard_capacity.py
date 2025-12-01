# dashboard_capacity.py

import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# ---- Visual defaults (Company Blue & White) ----
px.defaults.template = "plotly_white"

# Company blue palette (dark → light)
COMPANY_BLUES = [
    "#004C99",  # deep blue
    "#005BB5",
    "#007ACC",  # brand blue
    "#2F8DE0",
    "#66B2FF",
    "#99CCFF",
    "#CFE6FF"   # very light blue
]

# Apply globally so ALL charts use the blue theme
px.defaults.color_discrete_sequence = COMPANY_BLUES
px.defaults.color_continuous_scale = "Blues"

# Local alias used throughout the file
PX_SEQ = COMPANY_BLUES


# =========================
# Helpers
# =========================
def _apply_bar_labels(fig, show_labels: bool, fmt: str = None):
    if not show_labels:
        return fig
    fig.update_traces(texttemplate=fmt if fmt else "%{y}", textposition="outside", cliponaxis=False)
    return fig

@st.cache_data(show_spinner=False)
def _prep_base(df: pd.DataFrame):
    d = df.copy()

    # Normalize common time columns
    # Preferred: data_timestamp (datetime). Fallback: date (date-like).
    if "data_timestamp" in d.columns:
        d["data_timestamp"] = pd.to_datetime(d["data_timestamp"], errors="coerce")
        d["data_date"] = d["data_timestamp"].dt.normalize()
    elif "date" in d.columns:
        # accept both str-date and datetime/date
        d["data_date"] = pd.to_datetime(d["date"], errors="coerce").dt.normalize()

    # Safe numerics for utilizations
    for col in [
        "avg_cpu_utilization",
        "avg_memory_utilization",
        "avg_storage_utilization",
        "avg_network_utilization",
        "storage_tb",
        "network_bandwidth_gbps",
        "projected_growth_pct",
        "sla_met",  # if present
        "energy_consumption_kwh",
        "cost_per_month_usd",
        "potential_savings_usd",
    ]:
        if col in d.columns:
            d[col] = pd.to_numeric(d[col], errors="coerce")

    # Convenience columns
    if "resolution_time" in d.columns and pd.api.types.is_timedelta64_dtype(d["resolution_time"]):
        d["resolution_time_hours"] = d["resolution_time"].dt.total_seconds() / 3600.0

    # Projected CPU/Memory if growth provided (used in Capacity Planning section)
    if "avg_cpu_utilization" in d.columns and "projected_growth_pct" in d.columns:
        d["projected_cpu_utilization"] = (d["avg_cpu_utilization"] * (1 + d["projected_growth_pct"] / 100)).clip(upper=100)
    if "avg_memory_utilization" in d.columns and "projected_growth_pct" in d.columns:
        d["projected_memory_utilization"] = (d["avg_memory_utilization"] * (1 + d["projected_growth_pct"] / 100)).clip(upper=100)
    return d

def _agg_by_granularity(s: pd.Series, how="mean", granularity="D"):
    # s is a datetime-indexed Series OR a Series to aggregate with datetime index set by caller
    if granularity == "W":
        rule = "W-MON"
    elif granularity == "M":
        rule = "MS"
    else:
        rule = "D"

    if how == "count":
        return s.resample(rule).size()
    elif how == "sum":
        return s.resample(rule).sum()
    else:
        return s.resample(rule).mean()

def _safe_timecounts_from_index(idx, granularity, label_out):
    """
    Avoids 'cannot insert <col>, already exists' when resetting index on a named DatetimeIndex.
    Forces a neutral index name, aggregates, resets, then renames to the desired output label.
    Returns a DataFrame with columns [label_out, 'count'].
    """
    s = idx.to_series().copy()
    s.name = "__dt__"
    out = _agg_by_granularity(s, how="count", granularity=granularity)
    if isinstance(out, pd.Series):
        out = out.rename_axis("__dt__").reset_index(name="count")
    else:
        out = out.reset_index()
    return out.rename(columns={"__dt__": label_out})

# ---- Key namespace helper (avoid collisions with other dashboards) ----
KEY_NS = "capdash_"  # change once, all keys are unique to this page
def k(name: str) -> str:
    return f"{KEY_NS}{name}"

# =========================
# Main
# =========================
def dashboard_capacity(df: pd.DataFrame):
    st.markdown("## 🧮 IT Infrastructure Capacity — Executive Visual Dashboard")
    df = _prep_base(df)

    # ---------------- Sidebar controls ----------------
    with st.sidebar:
        st.markdown("### 🔎 Filters")
        # Date range from data_date if available
        if "data_date" in df.columns and not pd.isna(df["data_date"]).all():
            min_d = pd.to_datetime(df["data_date"]).min()
            max_d = pd.to_datetime(df["data_date"]).max()
            date_range = st.date_input(
                "Date range",
                value=(min_d.date(), max_d.date()),
                min_value=min_d.date(),
                max_value=max_d.date(),
                key=k("cap_flt_date_range"),
            )
        else:
            date_range = None


        def _opt(col):
            return sorted([v for v in df[col].dropna().astype(str).unique()]) if col in df.columns else []

        comp = st.multiselect("Component Type", _opt("component_type"), key=k("cap_flt_component"))
        loc = st.multiselect("Location", _opt("location"), key=k("cap_flt_location"))
        vendor = st.multiselect("Vendor", _opt("vendor"), key=k("cap_flt_vendor"))
        env = st.multiselect("Environment", _opt("environment"), key=k("cap_flt_env"))
        critical = st.multiselect("Criticality", _opt("criticality"), key=k("cap_flt_critical"))

        st.markdown("---")
        st.markdown("### ⚙️ View options")
        gran = st.radio("Time granularity", ["Daily", "Weekly", "Monthly"], horizontal=True, key=k("cap_gran"))
        gran_key = {"Daily": "D", "Weekly": "W", "Monthly": "M"}[gran]
        show_labels = st.toggle("Show bar labels", value=True, key=k("cap_show_lbls"))
        show_rangeslider = st.toggle("Show range slider on time-series", value=True, key=k("cap_show_slider"))
        show_smoothing = st.toggle("Show 7-day moving average where relevant", value=False, key=k("cap_show_ma"))
        st.markdown("---")
        clear = st.button("Clear all filters", use_container_width=True, key=k("cap_clear_btn"))

    # -------------- Apply filters --------------
    df_filtered = df.copy()
    if clear:
        comp = loc = vendor = env = critical = []
        if "data_date" in df_filtered.columns:
            # reset date range to full span
            date_range = (
                pd.to_datetime(df_filtered["data_date"]).min().date(),
                pd.to_datetime(df_filtered["data_date"]).max().date(),
            )

    if date_range and "data_date" in df_filtered.columns:
        start_date, end_date = date_range if isinstance(date_range, tuple) else (date_range, date_range)
        df_filtered = df_filtered[
            (pd.to_datetime(df_filtered["data_date"]) >= pd.to_datetime(start_date))
            & (pd.to_datetime(df_filtered["data_date"]) <= pd.to_datetime(end_date))
        ]
    if comp and "component_type" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["component_type"].astype(str).isin(comp)]
    if loc and "location" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["location"].astype(str).isin(loc)]
    if vendor and "vendor" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["vendor"].astype(str).isin(vendor)]
    if env and "environment" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["environment"].astype(str).isin(env)]
    if critical and "criticality" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["criticality"].astype[str].isin(critical)]

    # ===== KPIs =====
    st.markdown("---")
    st.markdown("### 🔹 Key Metrics")

    k1, k2, k3, k4 = st.columns(4)
    # Total Assets
    if "asset_id" in df_filtered.columns:
        k1.metric("Total Assets", f"{df_filtered['asset_id'].nunique():,}")
    else:
        k1.metric("Total Records", f"{len(df_filtered):,}")

    # Avg Utilizations
    def _avg(col):
        return float(pd.to_numeric(df_filtered[col], errors="coerce").dropna().mean()) if col in df_filtered.columns else np.nan

    avg_cpu = _avg("avg_cpu_utilization")
    avg_mem = _avg("avg_memory_utilization")
    avg_sto = _avg("avg_storage_utilization")
    avg_net = _avg("avg_network_utilization")

    # Show combined utilization KPI (CPU preferred, else memory/storage)
    if pd.notna(avg_cpu):
        k2.metric("Avg CPU Utilization", f"{avg_cpu:.2f}%")
    elif pd.notna(avg_mem):
        k2.metric("Avg Memory Utilization", f"{avg_mem:.2f}%")
    elif pd.notna(avg_sto):
        k2.metric("Avg Storage Utilization", f"{avg_sto:.2f}%")
    else:
        k2.metric("Avg Utilization", "N/A")

    # Monthly Cost / Potential Savings
    total_cost = pd.to_numeric(df_filtered.get("cost_per_month_usd", pd.Series(dtype=float)), errors="coerce").sum()
    total_sav = pd.to_numeric(df_filtered.get("potential_savings_usd", pd.Series(dtype=float)), errors="coerce").sum()
    k3.metric("Total Monthly Cost", f"${total_cost:,.2f}" if total_cost == total_cost else "—")
    k4.metric("Est. Potential Savings", f"${total_sav:,.2f}" if total_sav == total_sav else "—")

    cdl1, cdl2 = st.columns([1, 1])
    with cdl1:
        st.download_button(
            "⬇️ Download filtered data (CSV)",
            df_filtered.to_csv(index=False).encode("utf-8"),
            file_name="capacity_dashboard_filtered.csv",
            mime="text/csv",
            use_container_width=True,
            key=k("cap_dl_filtered"),
        )
    with cdl2:
        kpi_snap = {
            "total_assets": [int(df_filtered["asset_id"].nunique()) if "asset_id" in df_filtered.columns else len(df_filtered)],
            "avg_cpu_pct": [avg_cpu if pd.notna(avg_cpu) else np.nan],
            "avg_memory_pct": [avg_mem if pd.notna(avg_mem) else np.nan],
            "avg_storage_pct": [avg_sto if pd.notna(avg_sto) else np.nan],
            "avg_network_pct": [avg_net if pd.notna(avg_net) else np.nan],
            "total_monthly_cost_usd": [total_cost if total_cost == total_cost else np.nan],
            "potential_savings_usd": [total_sav if total_sav == total_sav else np.nan],
        }
        st.download_button(
            "⬇️ Download KPI snapshot (CSV)",
            pd.DataFrame(kpi_snap).to_csv(index=False).encode("utf-8"),
            file_name="capacity_dashboard_kpis.csv",
            mime="text/csv",
            use_container_width=True,
            key=k("cap_dl_kpis"),
        )

    # =========================================================
    # 1) Executive Summary Visuals
    # =========================================================
    st.markdown("---")
    st.markdown("### 🧭 Executive Summary")

    e1, e2 = st.columns(2)
    with e1:
        # Cost Distribution by Component Type (Donut)
        if {"component_type", "cost_per_month_usd"} <= set(df_filtered.columns):
            cost_by_type = (
                df_filtered.groupby("component_type", as_index=False)["cost_per_month_usd"].sum().sort_values("cost_per_month_usd", ascending=False)
            )
            fig = px.pie(
                cost_by_type,
                values="cost_per_month_usd",
                names="component_type",
                title="Cost Distribution by Component Type",
                hole=0.4,
                color_discrete_sequence=PX_SEQ,
            )
            st.plotly_chart(fig, use_container_width=True, key=k("cap_exe_cost_donut"))
    with e2:
        # Average Utilization Comparison (bar)
        util_rows = []
        if "avg_cpu_utilization" in df_filtered.columns:
            util_rows.append(("CPU Utilization", float(df_filtered["avg_cpu_utilization"].mean())))
        if "avg_memory_utilization" in df_filtered.columns:
            util_rows.append(("Memory Utilization", float(df_filtered["avg_memory_utilization"].mean())))
        if "avg_storage_utilization" in df_filtered.columns:
            util_rows.append(("Storage Utilization", float(df_filtered["avg_storage_utilization"].mean())))
        if "avg_network_utilization" in df_filtered.columns:
            util_rows.append(("Network Utilization", float(df_filtered["avg_network_utilization"].mean())))
        if util_rows:
            avg_util = pd.DataFrame(util_rows, columns=["Metric", "Average (%)"])
            fig2 = px.bar(
                avg_util,
                x="Metric",
                y="Average (%)",
                text="Average (%)",
                title="Average Utilization Across Key Resources",
                color="Metric",
                range_y=[0, 100],
                color_discrete_sequence=PX_SEQ,
            )
            fig2 = _apply_bar_labels(fig2, show_labels, fmt="%{text:.2f}")
            st.plotly_chart(fig2, use_container_width=True, key=k("cap_exe_avg_util"))

    # =========================================================
    # 2) Infrastructure Inventory
    # =========================================================
    st.markdown("---")
    st.markdown("### 🗂️ Infrastructure Inventory")

    ii1, ii2 = st.columns(2)
    with ii1:
        # Asset Distribution by Component Type (Bar)
        if "component_type" in df_filtered.columns:
            counts = df_filtered["component_type"].value_counts().reset_index()
            counts.columns = ["component_type", "count"]
            fig = px.bar(counts, x="component_type", y="count", text="count", title="Asset Distribution by Component Type", color_discrete_sequence=PX_SEQ)
            fig = _apply_bar_labels(fig, show_labels)
            st.plotly_chart(fig, use_container_width=True, key=k("cap_inv_component_bar"))
    with ii2:
        # Treemap — Share of Assets by Type
        if "component_type" in df_filtered.columns:
            if "asset_id" in df_filtered.columns:
                treemap_df = df_filtered.groupby("component_type", as_index=False)["asset_id"].nunique().rename(columns={"asset_id": "count"})
            else:
                treemap_df = df_filtered["component_type"].value_counts().reset_index()
                treemap_df.columns = ["component_type", "count"]
            fig = px.treemap(treemap_df, path=["component_type"], values="count", title="Treemap — Share of Assets by Type")
            st.plotly_chart(fig, use_container_width=True, key=k("cap_inv_component_treemap"))

    ii3, ii4 = st.columns(2)
    with ii3:
        # Cost Distribution by Component Type (Donut) — inventory section as well
        if {"component_type", "cost_per_month_usd"} <= set(df_filtered.columns):
            cost_by_type = df_filtered.groupby("component_type", as_index=False)["cost_per_month_usd"].sum()
            fig = px.pie(
                cost_by_type,
                values="cost_per_month_usd",
                names="component_type",
                title="Monthly Cost by Component Type",
                hole=0.4,
                color_discrete_sequence=PX_SEQ,
            )
            st.plotly_chart(fig, use_container_width=True, key=k("cap_inv_component_cost_donut"))
    with ii4:
        # Asset Count by Location (Bar)
        if {"location", "asset_id"} <= set(df_filtered.columns):
            loc_counts = df_filtered.groupby("location", as_index=False)["asset_id"].nunique().sort_values("asset_id", ascending=False)
            fig = px.bar(loc_counts, x="location", y="asset_id", text="asset_id", title="Asset Count by Location", color_discrete_sequence=PX_SEQ)
            fig = _apply_bar_labels(fig, show_labels)
            st.plotly_chart(fig, use_container_width=True, key=k("cap_inv_loc_bar"))

    # Cost Box Plot per Location
    if {"location", "cost_per_month_usd"} <= set(df_filtered.columns):
        fig = px.box(df_filtered.dropna(subset=["location", "cost_per_month_usd"]), x="location", y="cost_per_month_usd", title="Monthly Cost per Asset by Location", color_discrete_sequence=PX_SEQ)
        st.plotly_chart(fig, use_container_width=True, key=k("cap_inv_loc_cost_box"))

    # =========================================================
    # 3) Capacity Utilization (CPU, Memory, Storage, Network)
    # =========================================================
    st.markdown("---")
    st.markdown("### 🧠 Capacity Utilization")

    # CPU — Histogram | Box by Component Type | Trend
    cu1, cu2 = st.columns(2)
    with cu1:
        if "avg_cpu_utilization" in df_filtered.columns:
            fig = px.histogram(df_filtered, x="avg_cpu_utilization", nbins=20, title="CPU Utilization Distribution (%)", color_discrete_sequence=PX_SEQ)
            st.plotly_chart(fig, use_container_width=True, key=k("cap_cpu_hist"))
    with cu2:
        if "avg_cpu_utilization" in df_filtered.columns:
            fig = px.box(
                df_filtered,
                x="component_type" if "component_type" in df_filtered.columns else None,
                y="avg_cpu_utilization",
                title="CPU Utilization by Component Type (%)" if "component_type" in df_filtered.columns else "CPU Utilization (All Assets)",
                color_discrete_sequence=PX_SEQ,
            )
            st.plotly_chart(fig, use_container_width=True, key=k("cap_cpu_box"))

    if {"data_date", "avg_cpu_utilization"} <= set(df_filtered.columns):
        ts = (
            df_filtered.dropna(subset=["data_date", "avg_cpu_utilization"])
            .set_index("data_date")
            .sort_index()
            .pipe(lambda d: _agg_by_granularity(d["avg_cpu_utilization"], how="mean", granularity=gran_key).reset_index())
        )
        ts.columns = ["date", "avg_cpu_utilization"]
        if not ts.empty:
            fig = px.line(ts, x="date", y="avg_cpu_utilization", title="Mean CPU Utilization Over Time", markers=True, color_discrete_sequence=PX_SEQ)
            if show_rangeslider:
                fig.update_xaxes(rangeslider_visible=True)
            if show_smoothing and gran_key == "D":
                ts["MA7"] = ts["avg_cpu_utilization"].rolling(7).mean()
                fig.add_scatter(x=ts["date"], y=ts["MA7"], mode="lines", name="7-day MA")
            fig.update_layout(hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True, key=k("cap_cpu_trend"))

    # Memory — Box | Histogram | Trend
    mu1, mu2 = st.columns(2)
    with mu1:
        if "avg_memory_utilization" in df_filtered.columns:
            fig = px.box(
                df_filtered,
                x="component_type" if "component_type" in df_filtered.columns else None,
                y="avg_memory_utilization",
                title="Memory Utilization by Component Type (%)" if "component_type" in df_filtered.columns else "Memory Utilization (All Assets)",
                color_discrete_sequence=PX_SEQ,
            )
            st.plotly_chart(fig, use_container_width=True, key=k("cap_mem_box"))
    with mu2:
        if "avg_memory_utilization" in df_filtered.columns:
            fig = px.histogram(df_filtered, x="avg_memory_utilization", nbins=20, title="Memory Utilization Distribution (%)", color_discrete_sequence=PX_SEQ)
            st.plotly_chart(fig, use_container_width=True, key=k("cap_mem_hist"))

    if {"data_date", "avg_memory_utilization"} <= set(df_filtered.columns):
        ts = (
            df_filtered.dropna(subset=["data_date", "avg_memory_utilization"])
            .set_index("data_date")
            .sort_index()
            .pipe(lambda d: _agg_by_granularity(d["avg_memory_utilization"], how="mean", granularity=gran_key).reset_index())
        )
        ts.columns = ["date", "avg_memory_utilization"]
        if not ts.empty:
            fig = px.line(ts, x="date", y="avg_memory_utilization", title="Mean Memory Utilization Over Time", markers=True, color_discrete_sequence=PX_SEQ)
            if show_rangeslider:
                fig.update_xaxes(rangeslider_visible=True)
            if show_smoothing and gran_key == "D":
                ts["MA7"] = ts["avg_memory_utilization"].rolling(7).mean()
                fig.add_scatter(x=ts["date"], y=ts["MA7"], mode="lines", name="7-day MA")
            fig.update_layout(hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True, key=k("cap_mem_trend"))

    # Storage — Histogram | Scatter(Size vs Util) | Trend
    su1, su2 = st.columns(2)
    with su1:
        if "avg_storage_utilization" in df_filtered.columns:
            fig = px.histogram(df_filtered, x="avg_storage_utilization", nbins=20, title="Storage Utilization Distribution (%)", color_discrete_sequence=PX_SEQ)
            st.plotly_chart(fig, use_container_width=True, key=k("cap_sto_hist"))
    with su2:
        if {"avg_storage_utilization", "storage_tb"} <= set(df_filtered.columns):
            fig = px.scatter(
                df_filtered, x="storage_tb", y="avg_storage_utilization", title="Storage Size (TB) vs Utilization (%)", trendline="ols", color_discrete_sequence=PX_SEQ
            )
            st.plotly_chart(fig, use_container_width=True, key=k("cap_sto_scatter"))

    if {"data_date", "avg_storage_utilization"} <= set(df_filtered.columns):
        ts = (
            df_filtered.dropna(subset=["data_date", "avg_storage_utilization"])
            .set_index("data_date")
            .sort_index()
            .pipe(lambda d: _agg_by_granularity(d["avg_storage_utilization"], how="mean", granularity=gran_key).reset_index())
        )
        ts.columns = ["date", "avg_storage_utilization"]
        if not ts.empty:
            fig = px.line(ts, x="date", y="avg_storage_utilization", title="Mean Storage Utilization Over Time", markers=True, color_discrete_sequence=PX_SEQ)
            if show_rangeslider:
                fig.update_xaxes(rangeslider_visible=True)
            if show_smoothing and gran_key == "D":
                ts["MA7"] = ts["avg_storage_utilization"].rolling(7).mean()
                fig.add_scatter(x=ts["date"], y=ts["MA7"], mode="lines", name="7-day MA")
            fig.update_layout(hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True, key=k("cap_sto_trend"))

    # Network — Histogram | Scatter(BW vs Util) | Trend
    nu1, nu2 = st.columns(2)
    with nu1:
        if "avg_network_utilization" in df_filtered.columns:
            fig = px.histogram(df_filtered, x="avg_network_utilization", nbins=20, title="Network Utilization Distribution (%)", color_discrete_sequence=PX_SEQ)
            st.plotly_chart(fig, use_container_width=True, key=k("cap_net_hist") )
    with nu2:
        if {"avg_network_utilization", "network_bandwidth_gbps"} <= set(df_filtered.columns):
            fig = px.scatter(
                df_filtered,
                x="network_bandwidth_gbps",
                y="avg_network_utilization",
                title="Provisioned Bandwidth (Gbps) vs Utilization (%)",
                trendline="ols",
                color_discrete_sequence=PX_SEQ,
            )
            st.plotly_chart(fig, use_container_width=True, key=k("cap_net_scatter"))

    if {"data_date", "avg_network_utilization"} <= set(df_filtered.columns):
        ts = (
            df_filtered.dropna(subset=["data_date", "avg_network_utilization"])
            .set_index("data_date")
            .sort_index()
            .pipe(lambda d: _agg_by_granularity(d["avg_network_utilization"], how="mean", granularity=gran_key).reset_index())
        )
        ts.columns = ["date", "avg_network_utilization"]
        if not ts.empty:
            fig = px.line(ts, x="date", y="avg_network_utilization", title="Mean Network Utilization Over Time", markers=True, color_discrete_sequence=PX_SEQ)
            if show_rangeslider:
                fig.update_xaxes(rangeslider_visible=True)
            if show_smoothing and gran_key == "D":
                ts["MA7"] = ts["avg_network_utilization"].rolling(7).mean()
                fig.add_scatter(x=ts["date"], y=ts["MA7"], mode="lines", name="7-day MA")
            fig.update_layout(hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True, key=k("cap_net_trend"))

    # =========================================================
    # 4) Capacity Planning (CPU & Memory)
    # =========================================================
    st.markdown("---")
    st.markdown("### 🧩 Capacity Planning")

    cp1, cp2 = st.columns(2)
    with cp1:
        # CPU: current vs projected
        if {"avg_cpu_utilization", "projected_cpu_utilization"} <= set(df_filtered.columns):
            fig = px.scatter(
                df_filtered,
                x="avg_cpu_utilization",
                y="projected_cpu_utilization",
                title="Projected CPU Utilization (Next 12 Months)",
                labels={"avg_cpu_utilization": "Current CPU (%)", "projected_cpu_utilization": "Projected CPU (%)"},
                color_discrete_sequence=PX_SEQ,
            )
            st.plotly_chart(fig, use_container_width=True, key=k("capplan_cpu_scatter"))
    with cp2:
        # CPU Growth by Component Type (Projected - Current)
        if {"component_type", "avg_cpu_utilization", "projected_cpu_utilization"} <= set(df_filtered.columns):
            dfc = df_filtered.copy()
            dfc["cpu_growth_delta"] = dfc["projected_cpu_utilization"] - dfc["avg_cpu_utilization"]
            g = dfc.groupby("component_type", as_index=False)["cpu_growth_delta"].mean()
            fig = px.bar(g, x="component_type", y="cpu_growth_delta", title="Average CPU Growth by Component Type (%)", color_discrete_sequence=PX_SEQ, text="cpu_growth_delta")
            fig = _apply_bar_labels(fig, show_labels, fmt="%{text:.2f}")
            st.plotly_chart(fig, use_container_width=True, key=k("capplan_cpu_growth"))

    cp3, cp4 = st.columns(2)
    with cp3:
        # Memory: current vs projected
        if {"avg_memory_utilization", "projected_memory_utilization"} <= set(df_filtered.columns):
            fig = px.scatter(
                df_filtered,
                x="avg_memory_utilization",
                y="projected_memory_utilization",
                title="Projected Memory Utilization (Next 12 Months)",
                labels={"avg_memory_utilization": "Current Memory (%)", "projected_memory_utilization": "Projected Memory (%)"},
                color_discrete_sequence=PX_SEQ,
            )
            st.plotly_chart(fig, use_container_width=True, key=k("capplan_mem_scatter"))
    with cp4:
        # Memory Growth by Component Type
        if {"component_type", "avg_memory_utilization", "projected_memory_utilization"} <= set(df_filtered.columns):
            dfm = df_filtered.copy()
            dfm["mem_growth_delta"] = dfm["projected_memory_utilization"] - dfm["avg_memory_utilization"]
            g = dfm.groupby("component_type", as_index=False)["mem_growth_delta"].mean()
            fig = px.bar(g, x="component_type", y="mem_growth_delta", title="Average Memory Growth by Component Type (%)", color_discrete_sequence=PX_SEQ, text="mem_growth_delta")
            fig = _apply_bar_labels(fig, show_labels, fmt="%{text:.2f}")
            st.plotly_chart(fig, use_container_width=True, key=k("capplan_mem_growth"))

    # =========================================================
    # 5) Resource Efficiency (Under/Over Utilized)
    # =========================================================
    st.markdown("---")
    st.markdown("### ♻️ Resource Efficiency")

    re1, re2 = st.columns(2)
    with re1:
        # Underutilized Assets < 30% CPU
        if {"asset_id", "avg_cpu_utilization"} <= set(df_filtered.columns):
            low_util = df_filtered[df_filtered["avg_cpu_utilization"] < 30]
            if not low_util.empty:
                fig = px.bar(
                    low_util,
                    x="asset_id",
                    y="avg_cpu_utilization",
                    title="Underutilized Assets (<30% CPU)",
                    labels={"avg_cpu_utilization": "CPU Utilization (%)", "asset_id": "Asset ID"},
                    color_discrete_sequence=PX_SEQ,
                )
                st.plotly_chart(fig, use_container_width=True, key=k("cap_res_low_bar"))
    with re2:
        if "avg_cpu_utilization" in df_filtered.columns:
            fig = px.histogram(df_filtered, x="avg_cpu_utilization", nbins=20, title="CPU Utilization Distribution (All Assets)", color_discrete_sequence=PX_SEQ)
            st.plotly_chart(fig, use_container_width=True, key=k("cap_res_low_hist"))

    re3, re4 = st.columns(2)
    with re3:
        # Overutilized Assets > 85% CPU
        if {"asset_id", "avg_cpu_utilization"} <= set(df_filtered.columns):
            high_util = df_filtered[df_filtered["avg_cpu_utilization"] > 85]
            if not high_util.empty:
                fig = px.bar(
                    high_util,
                    x="asset_id",
                    y="avg_cpu_utilization",
                    title="Overutilized Assets (>85% CPU)",
                    labels={"avg_cpu_utilization": "CPU Utilization (%)", "asset_id": "Asset ID"},
                    color_discrete_sequence=PX_SEQ,
                )
                st.plotly_chart(fig, use_container_width=True, key=k("cap_res_high_bar"))
    with re4:
        if "avg_cpu_utilization" in df_filtered.columns:
            fig = px.histogram(df_filtered, x="avg_cpu_utilization", nbins=20, title="Overall CPU Utilization Spread", color_discrete_sequence=PX_SEQ)
            st.plotly_chart(fig, use_container_width=True, key=k("cap_res_high_hist"))



    # =========================================================
    # 6) Target 6 — Bottleneck Identification
    # =========================================================
    st.markdown("---")
    st.markdown("### 6) 🧩 Bottleneck Identification")

    if {"component_type","avg_cpu_utilization","avg_memory_utilization"} <= set(df_filtered.columns):
        _d = df_filtered.copy()
        _d["bottleneck_score"] = (_d["avg_cpu_utilization"] + _d["avg_memory_utilization"]) / 2

        t6a, t6b = st.columns(2)
        with t6a:
            _g1 = _d.groupby("component_type", as_index=False)["bottleneck_score"].mean()
            _fig1 = px.bar(
                _g1.sort_values("bottleneck_score", ascending=False),
                x="component_type", y="bottleneck_score",
                title="Average Bottleneck Score by Component Type",
                text="bottleneck_score",
                color_discrete_sequence=PX_SEQ,
            )
            _fig1.update_traces(texttemplate="%{text:.2f}", textposition="outside")
            st.plotly_chart(_fig1, use_container_width=True, key=k("cap6_bneck_comp_bar"))
        with t6b:
            _fig2 = px.histogram(
                _d, x="bottleneck_score", nbins=20,
                title="Distribution of Bottleneck Scores",
                color_discrete_sequence=PX_SEQ,
            )
            st.plotly_chart(_fig2, use_container_width=True, key=k("cap6_bneck_hist"))

        # Top 10 assets
        _top10 = _d.nlargest(10, "bottleneck_score")[["asset_id","bottleneck_score"]] if "asset_id" in _d.columns else None
        if _top10 is not None:
            _fig3 = px.bar(
                _top10, x="asset_id", y="bottleneck_score",
                title="Top 10 Bottlenecked Assets",
                text="bottleneck_score",
                color_discrete_sequence=PX_SEQ,
            )
            _fig3.update_traces(texttemplate="%{text:.2f}", textposition="outside")
            st.plotly_chart(_fig3, use_container_width=True, key=k("cap6_bneck_top10"))

    # =========================================================
    # 7) Target 7 — Resource Allocation Efficiency
    # =========================================================
    st.markdown("---")
    st.markdown("### 7) ♻️ Resource Allocation Efficiency")

    if {"avg_cpu_utilization","avg_memory_utilization"} <= set(df_filtered.columns):
        _d3 = df_filtered.copy()
        _d3["efficiency_score"] = 100 - (_d3["avg_cpu_utilization"] - _d3["avg_memory_utilization"]).abs()

        t7a, t7b = st.columns(2)
        with t7a:
            _fig4 = px.histogram(
                _d3, x="efficiency_score", nbins=20,
                title="Resource Efficiency Distribution (%)",
                color_discrete_sequence=PX_SEQ,
            )
            st.plotly_chart(_fig4, use_container_width=True, key=k("cap7_eff_hist"))
        with t7b:
            _fig5 = px.scatter(
                _d3, x="avg_cpu_utilization", y="avg_memory_utilization",
                title="CPU vs Memory Utilization Balance",
                labels={"avg_cpu_utilization":"CPU Utilization (%)","avg_memory_utilization":"Memory Utilization (%)"},
                color_discrete_sequence=PX_SEQ,
            )
            st.plotly_chart(_fig5, use_container_width=True, key=k("cap7_balance_scatter"))

    if {"component_type","avg_cpu_utilization"} <= set(df_filtered.columns):
        _comp = df_filtered.groupby("component_type", as_index=False)["avg_cpu_utilization"].mean()

        t7c, t7d = st.columns(2)
        with t7c:
            _fig6 = px.bar(
                _comp, x="component_type", y="avg_cpu_utilization",
                title="Average CPU Utilization by Component Type",
                text="avg_cpu_utilization",
                labels={"avg_cpu_utilization":"CPU Utilization (%)"},
                color_discrete_sequence=PX_SEQ,
            )
            _fig6.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
            st.plotly_chart(_fig6, use_container_width=True, key=k("cap7_comp_bar"))
        with t7d:
            _comp_sorted = _comp.sort_values("avg_cpu_utilization", ascending=False)
            _fig7 = px.line(
                _comp_sorted, x="component_type", y="avg_cpu_utilization",
                title="CPU Utilization Trend by Component Type",
                markers=True,
                color_discrete_sequence=PX_SEQ,
            )
            st.plotly_chart(_fig7, use_container_width=True, key=k("cap7_comp_line"))

    # =========================================================
    # 8) Target 8 — Workload Analysis
    # =========================================================
    st.markdown("---")
    st.markdown("### 8) 🧱 Workload Analysis")

    if "avg_cpu_utilization" in df_filtered.columns:
        t8a, t8b = st.columns(2)
        with t8a:
            if "component_type" in df_filtered.columns:
                _comp2 = df_filtered.groupby("component_type", as_index=False)["avg_cpu_utilization"].mean()
                _fig8 = px.bar(
                    _comp2, x="component_type", y="avg_cpu_utilization",
                    text="avg_cpu_utilization",
                    title="Average CPU Utilization by Component Type",
                    labels={"avg_cpu_utilization":"Average CPU Utilization (%)"},
                    color_discrete_sequence=PX_SEQ,
                )
                _fig8.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
                st.plotly_chart(_fig8, use_container_width=True, key=k("cap8_workload_component_bar"))
        with t8b:
            _fig9 = px.histogram(
                df_filtered, x="avg_cpu_utilization", nbins=20,
                title="CPU Utilization Frequency Distribution",
                labels={"avg_cpu_utilization":"CPU Utilization (%)"},
                color_discrete_sequence=PX_SEQ,
            )
            st.plotly_chart(_fig9, use_container_width=True, key=k("cap8_workload_component_hist"))

    if {"avg_cpu_utilization","avg_memory_utilization"} <= set(df_filtered.columns):
        t8c, t8d = st.columns(2)
        with t8c:
            _fig10 = px.scatter(
                df_filtered,
                x="avg_cpu_utilization", y="avg_memory_utilization",
                color=("component_type" if "component_type" in df_filtered.columns else None),
                title="CPU vs Memory Utilization by Component Type",
                labels={"avg_cpu_utilization":"CPU Utilization (%)","avg_memory_utilization":"Memory Utilization (%)"},
                color_discrete_sequence=PX_SEQ,
            )
            st.plotly_chart(_fig10, use_container_width=True, key=k("cap8_workload_corr_scatter"))
        with t8d:
            _fig11 = px.density_heatmap(
                df_filtered, x="avg_cpu_utilization", y="avg_memory_utilization",
                nbinsx=20, nbinsy=20,
                title="Workload Density Heatmap (CPU vs Memory)",
            )
            st.plotly_chart(_fig11, use_container_width=True, key=k("cap8_workload_corr_heatmap"))

    # =========================================================
    # 9) Target 9 — Virtualization & Cloud
    # =========================================================
    st.markdown("---")
    st.markdown("### 9) ☁️ Virtualization & Cloud")

    if {"vm_name","avg_cpu_utilization"} <= set(df_filtered.columns):
        t9a, t9b = st.columns(2)
        with t9a:
            _vm = df_filtered.groupby("vm_name", as_index=False)["avg_cpu_utilization"].mean()
            _fig12 = px.bar(
                _vm, x="vm_name", y="avg_cpu_utilization",
                text="avg_cpu_utilization",
                title="Average CPU Utilization by VM",
                labels={"vm_name":"VM","avg_cpu_utilization":"Avg CPU Util (%)"},
                color_discrete_sequence=PX_SEQ,
            )
            _fig12.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
            st.plotly_chart(_fig12, use_container_width=True, key=k("cap9_vm_eff_bar"))
        with t9b:
            _fig13 = px.histogram(
                _vm, x="avg_cpu_utilization", nbins=20,
                title="VM Utilization Distribution (%)",
                labels={"avg_cpu_utilization":"CPU Utilization (%)"},
                color_discrete_sequence=PX_SEQ,
            )
            st.plotly_chart(_fig13, use_container_width=True, key=k("cap9_vm_eff_hist"))

    if {"avg_cpu_utilization","cost_per_month_usd"} <= set(df_filtered.columns):
        _d4 = df_filtered.copy()
        t9c, t9d = st.columns(2)
        with t9c:
            _fig14 = px.scatter(
                _d4, x="avg_cpu_utilization", y="cost_per_month_usd",
                title="Cloud Cost vs CPU Utilization",
                labels={"avg_cpu_utilization":"Avg CPU Utilization (%)","cost_per_month_usd":"Monthly Cost (USD)"},
                trendline="ols",
                color_discrete_sequence=PX_SEQ,
            )
            st.plotly_chart(_fig14, use_container_width=True, key=k("cap9_cloud_cost_scatter"))
        with t9d:
            _d4 = _d4.sort_values("avg_cpu_utilization")
            _d4["cost_efficiency"] = _d4["cost_per_month_usd"] / _d4["avg_cpu_utilization"].replace(0, pd.NA)
            _fig15 = px.line(
                _d4, x="avg_cpu_utilization", y="cost_efficiency",
                title="Cost Efficiency Trend (USD per % Utilization)",
                labels={"avg_cpu_utilization":"CPU Utilization (%)","cost_efficiency":"USD / % Util"},
                color_discrete_sequence=PX_SEQ,
            )
            st.plotly_chart(_fig15, use_container_width=True, key=k("cap9_cost_eff_trend"))

    # =========================================================
    # 10) Target 10 — Storage Capacity
    # =========================================================
    st.markdown("---")
    st.markdown("### 10) 💾 Storage Capacity")

    _df_st = df_filtered.copy()
    if "storage_capacity_tb" not in _df_st.columns and "storage_tb" in _df_st.columns:
        _df_st["storage_capacity_tb"] = pd.to_numeric(_df_st["storage_tb"], errors="coerce")
    if "storage_used_tb" not in _df_st.columns and {"avg_storage_utilization","storage_capacity_tb"} <= set(_df_st.columns):
        _df_st["storage_used_tb"] = (pd.to_numeric(_df_st["avg_storage_utilization"], errors="coerce")/100.0) * pd.to_numeric(_df_st["storage_capacity_tb"], errors="coerce")
    if {"storage_used_tb","storage_capacity_tb"} <= set(_df_st.columns):
        _cap = pd.to_numeric(_df_st["storage_capacity_tb"], errors="coerce").replace(0, np.nan)
        _used = pd.to_numeric(_df_st["storage_used_tb"], errors="coerce")
        _df_st["storage_utilization_pct"] = (_used / _cap) * 100

    if {"asset_id","storage_utilization_pct"} <= set(_df_st.columns):
        t10a, t10b = st.columns(2)
        with t10a:
            _fig16 = px.bar(
                _df_st.sort_values("storage_utilization_pct", ascending=False),
                x="asset_id", y="storage_utilization_pct",
                title="Storage Utilization by Asset (%)",
                text="storage_utilization_pct",
                labels={"asset_id":"Asset","storage_utilization_pct":"Utilization (%)"},
                color_discrete_sequence=PX_SEQ,
            )
            _fig16.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
            st.plotly_chart(_fig16, use_container_width=True, key=k("cap10_stor_asset_bar"))
        with t10b:
            _fig17 = px.histogram(
                _df_st, x="storage_utilization_pct", nbins=20,
                title="Distribution of Storage Utilization (%)",
                labels={"storage_utilization_pct":"Utilization (%)"},
                color_discrete_sequence=PX_SEQ,
            )
            st.plotly_chart(_fig17, use_container_width=True, key=k("cap10_stor_asset_hist"))

        _fig18 = None
        if "storage_capacity_tb" in _df_st.columns:
            _fig18 = px.scatter(
                _df_st, x="storage_capacity_tb", y="storage_utilization_pct",
                title="Provisioned Capacity (TB) vs Utilization (%)",
                labels={"storage_capacity_tb":"Capacity (TB)","storage_utilization_pct":"Utilization (%)"},
                trendline="ols",
                color_discrete_sequence=PX_SEQ,
            )
            st.plotly_chart(_fig18, use_container_width=True, key=k("cap10_stor_asset_scatter"))

    _dt = _df_st.copy()
    _date_col = None
    if "date" in _dt.columns:
        _dt["date"] = pd.to_datetime(_dt["date"], errors="coerce"); _date_col = "date"
    elif "data_timestamp" in _dt.columns:
        _dt["date"] = pd.to_datetime(_dt["data_timestamp"], errors="coerce"); _date_col = "date"

    if _date_col and "storage_used_tb" in _dt.columns:
        _monthly = (
            _dt.dropna(subset=[_date_col,"storage_used_tb"])
            .assign(month=lambda x: x[_date_col].dt.to_period("M"))
            .groupby("month", as_index=False)["storage_used_tb"].sum()
        )
        _monthly["month"] = _monthly["month"].astype(str)

        t10c, t10d = st.columns(2)
        with t10c:
            _fig19 = px.line(
                _monthly, x="month", y="storage_used_tb",
                title="Monthly Storage Consumption (TB)",
                labels={"month":"Month","storage_used_tb":"Total Used (TB)"},
                color_discrete_sequence=PX_SEQ,
            )
            _fig19.update_traces(mode="lines+markers")
            st.plotly_chart(_fig19, use_container_width=True, key=k("cap10_stor_growth_monthly"))
        with t10d:
            if len(_monthly) >= 2:
                _monthly2 = _monthly.copy()
                _monthly2["growth_tb"] = _monthly2["storage_used_tb"].diff()
                _fig20 = px.bar(
                    _monthly2, x="month", y="growth_tb",
                    title="Month-over-Month Storage Growth (TB)",
                    labels={"month":"Month","growth_tb":"Δ Used (TB)"},
                    color_discrete_sequence=PX_SEQ,
                )
                st.plotly_chart(_fig20, use_container_width=True, key=k("cap10_stor_growth_mom"))

    # =========================================================
    # 11) Target 11 — Network Capacity
    # =========================================================
    st.markdown("---")
    st.markdown("### 11) 🌐 Network Capacity")

    if {"date","network_bandwidth_usage_gbps","network_capacity_gbps"} <= set(df_filtered.columns):
        _d5 = df_filtered.copy()
        _d5["date"] = pd.to_datetime(_d5["date"], errors="coerce")
        _d5["network_utilization_pct"] = (_d5["network_bandwidth_usage_gbps"] / _d5["network_capacity_gbps"].replace(0, np.nan)) * 100

        t11a, t11b = st.columns(2)
        with t11a:
            _fig21 = px.line(
                _d5, x="date", y="network_utilization_pct",
                title="Network Utilization Trend Over Time (%)",
                labels={"date":"Date","network_utilization_pct":"Utilization (%)"},
                color_discrete_sequence=PX_SEQ,
            )
            st.plotly_chart(_fig21, use_container_width=True, key=k("cap11_net_util_line"))
        with t11b:
            _fig22 = px.histogram(
                _d5, x="network_utilization_pct", nbins=20,
                title="Distribution of Network Utilization (%)",
                labels={"network_utilization_pct":"Utilization (%)"},
                color_discrete_sequence=PX_SEQ,
            )
            st.plotly_chart(_fig22, use_container_width=True, key=k("cap11_net_util_hist"))

    if {"asset_id","network_bandwidth_usage_gbps"} <= set(df_filtered.columns):
        _top10n = df_filtered.nlargest(10, "network_bandwidth_usage_gbps")[["asset_id","network_bandwidth_usage_gbps"]]

        t11c, t11d = st.columns(2)
        with t11c:
            _fig23 = px.bar(
                _top10n, x="asset_id", y="network_bandwidth_usage_gbps",
                text="network_bandwidth_usage_gbps",
                title="Top 10 Network Nodes by Bandwidth Usage (GBps)",
                labels={"asset_id":"Network Node","network_bandwidth_usage_gbps":"Bandwidth Usage (GBps)"},
                color_discrete_sequence=PX_SEQ,
            )
            _fig23.update_traces(texttemplate="%{text:.2f}", textposition="outside")
            st.plotly_chart(_fig23, use_container_width=True, key=k("cap11_net_top_nodes"))
        with t11d:
            _total_bw = float(pd.to_numeric(df_filtered.get("network_bandwidth_usage_gbps", pd.Series([])), errors="coerce").sum())
            if _total_bw > 0:
                _fig24 = px.pie(
                    _top10n, names="asset_id", values="network_bandwidth_usage_gbps",
                    title="Top 10 Nodes — Share of Total Network Traffic (%)",
                    hole=0.4,
                )
                st.plotly_chart(_fig24, use_container_width=True, key=k("cap11_net_top_pie"))

    # =========================================================
    # 12) Target 12 — Energy Efficiency
    # =========================================================
    st.markdown("---")
    st.markdown("### 12) ⚡ Energy Efficiency")

    # Power vs Utilization
    _ene = df_filtered.copy()
    if "power_kw" not in _ene.columns and "power_watts" in _ene.columns:
        _ene["power_kw"] = pd.to_numeric(_ene["power_watts"], errors="coerce") / 1000.0
    if "power_kw" in _ene.columns and "avg_cpu_utilization" in _ene.columns:
        _ene["power_kw"] = pd.to_numeric(_ene["power_kw"], errors="coerce")
        _ene["avg_cpu_utilization"] = pd.to_numeric(_ene["avg_cpu_utilization"], errors="coerce")

        t12a, t12b = st.columns(2)
        with t12a:
            _fig1201 = px.scatter(
                _ene, x="avg_cpu_utilization", y="power_kw",
                trendline="ols",
                title="Power Draw (kW) vs CPU Utilization (%)",
                labels={"avg_cpu_utilization":"CPU Utilization (%)","power_kw":"Power (kW)"},
                color_discrete_sequence=PX_SEQ,
            )
            st.plotly_chart(_fig1201, use_container_width=True, key=k("cap12_power_vs_util_scatter"))
        with t12b:
            _ene["util_per_kw"] = _ene["avg_cpu_utilization"] / _ene["power_kw"].replace(0, np.nan)
            _fig1202 = px.histogram(
                _ene, x="util_per_kw", nbins=20,
                title="Efficiency Index Distribution (Utilization % per kW)",
                labels={"util_per_kw":"Utilization % per kW"},
                color_discrete_sequence=PX_SEQ,
            )
            st.plotly_chart(_fig1202, use_container_width=True, key=k("cap12_eff_index_hist"))

    # PUE Trend
    _pue = df_filtered.copy()
    _date_col = None
    if "date" in _pue.columns:
        _pue["date"] = pd.to_datetime(_pue["date"], errors="coerce"); _date_col = "date"
    elif "data_timestamp" in _pue.columns:
        _pue["date"] = pd.to_datetime(_pue["data_timestamp"], errors="coerce"); _date_col = "date"
    if _date_col and "pue" in _pue.columns:
        _pue["pue"] = pd.to_numeric(_pue["pue"], errors="coerce")
        _fig1203 = px.line(
            _pue.sort_values(_date_col), x=_date_col, y="pue",
            title="PUE Trend Over Time",
            labels={_date_col:"Date","pue":"PUE"},
            color_discrete_sequence=PX_SEQ,
        )
        _fig1203.update_traces(mode="lines+markers")
        st.plotly_chart(_fig1203, use_container_width=True, key=k("cap12_pue_trend"))

    # Energy Consumption by Asset
    _ek = df_filtered.copy()
    if "energy_kwh_month" in _ek.columns:
        _ek["energy_kwh_month"] = pd.to_numeric(_ek["energy_kwh_month"], errors="coerce")
    elif {"power_kw","runtime_hours_month"} <= set(_ek.columns):
        _ek["energy_kwh_month"] = pd.to_numeric(_ek["power_kw"], errors="coerce") * pd.to_numeric(_ek["runtime_hours_month"], errors="coerce")

    if {"asset_id","energy_kwh_month"} <= set(_ek.columns):
        t12c, t12d = st.columns(2)
        with t12c:
            _topE = _ek.nlargest(10, "energy_kwh_month")[["asset_id","energy_kwh_month"]]
            _fig1204 = px.bar(
                _topE, x="asset_id", y="energy_kwh_month",
                text="energy_kwh_month",
                title="Top 10 Assets by Monthly Energy (kWh)",
                labels={"asset_id":"Asset","energy_kwh_month":"Energy (kWh)"},
                color_discrete_sequence=PX_SEQ,
            )
            _fig1204.update_traces(texttemplate="%{text:.0f}", textposition="outside")
            st.plotly_chart(_fig1204, use_container_width=True, key=k("cap12_energy_top10_bar"))
        with t12d:
            _fig1205 = px.histogram(
                _ek, x="energy_kwh_month", nbins=20,
                title="Distribution of Monthly Energy (kWh)",
                labels={"energy_kwh_month":"Energy (kWh)"},
                color_discrete_sequence=PX_SEQ,
            )
            st.plotly_chart(_fig1205, use_container_width=True, key=k("cap12_energy_hist"))

    # Energy Intensity by Component
    _ei = df_filtered.copy()
    if "energy_kwh_month" in _ei.columns:
        _ei["energy_kwh_month"] = pd.to_numeric(_ei["energy_kwh_month"], errors="coerce")
    elif {"power_kw","runtime_hours_month"} <= set(_ei.columns):
        _ei["energy_kwh_month"] = pd.to_numeric(_ei["power_kw"], errors="coerce") * pd.to_numeric(_ei["runtime_hours_month"], errors="coerce")

    if {"component_type","energy_kwh_month"} <= set(_ei.columns):
        t12e, t12f = st.columns(2)
        with t12e:
            _compE = _ei.groupby("component_type", as_index=False)["energy_kwh_month"].mean()
            _fig1206 = px.bar(
                _compE, x="component_type", y="energy_kwh_month",
                text="energy_kwh_month",
                title="Avg Monthly Energy by Component (kWh)",
                labels={"component_type":"Component","energy_kwh_month":"Avg Energy (kWh)"},
                color_discrete_sequence=PX_SEQ,
            )
            _fig1206.update_traces(texttemplate="%{text:.0f}", textposition="outside")
            st.plotly_chart(_fig1206, use_container_width=True, key=k("cap12_energy_component_bar"))
        with t12f:
            _compE_sorted = _compE.sort_values("energy_kwh_month", ascending=False)
            _fig1207 = px.line(
                _compE_sorted, x="component_type", y="energy_kwh_month",
                title="Energy Intensity Trend by Component (kWh)",
                markers=True,
                color_discrete_sequence=PX_SEQ,
            )
            st.plotly_chart(_fig1207, use_container_width=True, key=k("cap12_energy_component_line"))

    # Energy Cost vs Utilization
    _ec = df_filtered.copy()
    if "monthly_energy_cost_usd" not in _ec.columns and {"energy_kwh_month","energy_cost_per_kwh_usd"} <= set(_ec.columns):
        _ec["monthly_energy_cost_usd"] = pd.to_numeric(_ec["energy_kwh_month"], errors="coerce") * pd.to_numeric(_ec["energy_cost_per_kwh_usd"], errors="coerce")

    if {"avg_cpu_utilization","monthly_energy_cost_usd"} <= set(_ec.columns):
        t12g, t12h = st.columns(2)
        with t12g:
            _ec["avg_cpu_utilization"] = pd.to_numeric(_ec["avg_cpu_utilization"], errors="coerce")
            _ec["monthly_energy_cost_usd"] = pd.to_numeric(_ec["monthly_energy_cost_usd"], errors="coerce")
            _fig1208 = px.scatter(
                _ec, x="avg_cpu_utilization", y="monthly_energy_cost_usd",
                trendline="ols",
                title="CPU Utilization vs Monthly Energy Cost",
                labels={"avg_cpu_utilization":"CPU Utilization (%)","monthly_energy_cost_usd":"Energy Cost (USD)"},
                color_discrete_sequence=PX_SEQ,
            )
            st.plotly_chart(_fig1208, use_container_width=True, key=k("cap12_util_vs_energycost_scatter"))
        with t12h:
            _fig1209 = px.histogram(
                _ec, x="monthly_energy_cost_usd", nbins=20,
                title="Distribution of Monthly Energy Cost (USD)",
                labels={"monthly_energy_cost_usd":"Energy Cost (USD)"},
                color_discrete_sequence=PX_SEQ,
            )
            st.plotly_chart(_fig1209, use_container_width=True, key=k("cap12_energycost_hist"))

    # Carbon Emissions (Estimated)
    _co2 = df_filtered.copy()
    if "co2_kg_month" in _co2.columns:
        _co2["co2_kg_month"] = pd.to_numeric(_co2["co2_kg_month"], errors="coerce")
    elif {"energy_kwh_month","emission_factor_kg_per_kwh"} <= set(_co2.columns):
        _co2["co2_kg_month"] = pd.to_numeric(_co2["energy_kwh_month"], errors="coerce") * pd.to_numeric(_co2["emission_factor_kg_per_kwh"], errors="coerce")

    if {"asset_id","co2_kg_month"} <= set(_co2.columns):
        t12i, t12j = st.columns(2)
        with t12i:
            _topC = _co2.nlargest(10, "co2_kg_month")[["asset_id","co2_kg_month"]]
            _fig1210 = px.bar(
                _topC, x="asset_id", y="co2_kg_month",
                text="co2_kg_month",
                title="Top 10 Assets by Estimated CO₂ (kg/month)",
                labels={"asset_id":"Asset","co2_kg_month":"CO₂ (kg/month)"},
                color_discrete_sequence=PX_SEQ,
            )
            _fig1210.update_traces(texttemplate="%{text:.0f}", textposition="outside")
            st.plotly_chart(_fig1210, use_container_width=True, key=k("cap12_co2_top10_bar"))
        with t12j:
            if "energy_kwh_month" in _co2.columns:
                _fig1211 = px.scatter(
                    _co2, x="energy_kwh_month", y="co2_kg_month",
                    trendline="ols",
                    title="CO₂ Emissions vs Energy Consumption",
                    labels={"energy_kwh_month":"Energy (kWh/month)","co2_kg_month":"CO₂ (kg/month)"},
                    color_discrete_sequence=PX_SEQ,
                )
                st.plotly_chart(_fig1211, use_container_width=True, key=k("cap12_co2_vs_energy_scatter"))
