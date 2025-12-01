import streamlit as st
import plotly.express as px
import plotly.io as pio
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# ---- Visual defaults (match ticket dashboard) ----
BLUE_TONES = [
    "#004C99",  # navy blue (brand)
    "#0066CC",  # strong blue
    "#007ACC",  # azure (brand)
    "#3399FF",  # light blue
    "#66B2FF",  # lighter blue
    "#99CCFF",  # pale blue
]

# Create a custom template that applies the blue colorway globally
pio.templates["mesiniaga_blue"] = pio.templates["plotly_white"]
pio.templates["mesiniaga_blue"].layout.colorway = BLUE_TONES

# Make it the default for all px figures
px.defaults.template = "mesiniaga_blue"

# Also keep a handy sequence for explicit plots that pass color_discrete_sequence
PX_SEQ = BLUE_TONES

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

    # Time columns
    for col in ["report_date", "created_time", "resolved_time", "completed_time"]:
        if col in d.columns:
            d[col] = pd.to_datetime(d[col], errors="coerce")

    # Derived date (for filtering)
    if "report_date" in d.columns:
        d["report_day"] = d["report_date"].dt.date

    # Numeric coercions commonly used
    numeric_like = [
        "uptime_percentage", "downtime_minutes", "incident_count",
        "estimated_cost_downtime", "recovery_time_minutes", "rto_target_minutes",
        "sla_met", "sla_target",
        "cpu_utilization", "memory_utilization", "disk_utilization", "network_utilization"
    ]
    for c in numeric_like:
        if c in d.columns:
            d[c] = pd.to_numeric(d[c], errors="coerce")

    # Guard against negatives on key metrics
    for c in ["downtime_minutes", "recovery_time_minutes", "rto_target_minutes", "uptime_percentage"]:
        if c in d.columns:
            d[c] = d[c].clip(lower=0)

    # Normalize SLA boolean if present as text
    if "sla_met" in d.columns and d["sla_met"].dtype == object:
        d["sla_met"] = (
            d["sla_met"].astype(str).str.strip().str.lower()
            .replace({"true": 1, "yes": 1, "1": 1, "false": 0, "no": 0, "0": 0})
        )
        d["sla_met"] = pd.to_numeric(d["sla_met"], errors="coerce")

    return d

def _agg_by_granularity(s: pd.Series, how="mean", granularity="D"):
    # s is a datetime-indexed Series (values used if how == "mean", size if "count")
    if granularity == "W":
        return s.resample("W-MON").mean() if how == "mean" else s.resample("W-MON").size()
    if granularity == "M":
        return s.resample("MS").mean() if how == "mean" else s.resample("MS").size()
    return s.resample("D").mean() if how == "mean" else s.resample("D").size()

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

# Optional: seasonal decomposition (guarded)
try:
    from statsmodels.tsa.seasonal import seasonal_decompose
    _HAS_DECOMP = True
except Exception:
    _HAS_DECOMP = False

def _to_num(s):
    return pd.to_numeric(s, errors="coerce")

# =========================
# Main
# =========================
def dashboard_service(df: pd.DataFrame):
    st.markdown("## 📊 Executive Visual Dashboard — Service Availability")
    df = _prep_base(df)

    # ---------------- Sidebar controls ----------------
    with st.sidebar:
        st.markdown("### 🔎 Filters")

        # Date range on report_date
        if "report_day" in df.columns and not pd.isna(df["report_day"]).all():
            min_d = pd.to_datetime(df["report_day"]).min()
            max_d = pd.to_datetime(df["report_day"]).max()
            date_range = st.date_input(
                "Report Date range",
                value=(min_d, max_d),
                min_value=min_d, max_value=max_d,
                key="svc_flt_date_range",
            )
        else:
            date_range = None

        def _opt(col):
            return sorted([v for v in df[col].dropna().astype(str).unique()]) if col in df.columns else []

        svc = st.multiselect("Service Name", _opt("service_name"), key="svc_flt_service")
        cat = st.multiselect("Service Category", _opt("service_category"), key="svc_flt_cat")
        owner = st.multiselect("Service Owner", _opt("service_owner"), key="svc_flt_owner")
        stake = st.multiselect("Stakeholder", _opt("stakeholder"), key="svc_flt_stake")
        mtype = st.multiselect("Maintenance Type", _opt("maintenance_type"), key="svc_flt_mtype")

        st.markdown("---")
        st.markdown("### ⚙️ View options")
        gran = st.radio("Time granularity (for time-series)", ["Daily", "Weekly", "Monthly"], horizontal=True, key="svc_gran")
        gran_key = {"Daily": "D", "Weekly": "W", "Monthly": "M"}[gran]
        show_labels = st.toggle("Show bar labels", value=True, key="svc_lbls")
        show_rangeslider = st.toggle("Show range slider on time-series", value=True, key="svc_rs")
        show_smoothing = st.toggle("Show 7-day moving average where relevant", value=False, key="svc_smooth")

        st.markdown("---")
        clear = st.button("Clear all filters", use_container_width=True, key="svc_clear")

    # -------------- Apply filters --------------
    df_filtered = df.copy()

    if clear:
        svc = cat = owner = stake = mtype = []
        if "report_day" in df_filtered.columns and not df_filtered["report_day"].isna().all():
            min_d = pd.to_datetime(df_filtered["report_day"]).min().date()
            max_d = pd.to_datetime(df_filtered["report_day"]).max().date()
            date_range = (min_d, max_d)

    if date_range and "report_day" in df_filtered.columns:
        start_date, end_date = date_range if isinstance(date_range, tuple) else (date_range, date_range)
        df_filtered = df_filtered[
            (pd.to_datetime(df_filtered["report_day"]) >= pd.to_datetime(start_date)) &
            (pd.to_datetime(df_filtered["report_day"]) <= pd.to_datetime(end_date))
        ]

    if svc and "service_name" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["service_name"].astype(str).isin(svc)]
    if cat and "service_category" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["service_category"].astype(str).isin(cat)]
    if owner and "service_owner" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["service_owner"].astype(str).isin(owner)]
    if stake and "stakeholder" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["stakeholder"].astype(str).isin(stake)]
    if mtype and "maintenance_type" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["maintenance_type"].astype(str).isin(mtype)]

    # ===== KPIs =====
    st.markdown("---")
    st.markdown("### 🔹 Key Metrics")
    k1, k2, k3, k4 = st.columns(4)

    avg_uptime = (pd.to_numeric(df_filtered.get("uptime_percentage", pd.Series(dtype=float)), errors="coerce").mean()
                  if "uptime_percentage" in df_filtered.columns else np.nan)
    total_dt = (pd.to_numeric(df_filtered.get("downtime_minutes", pd.Series(dtype=float)), errors="coerce").sum()
                if "downtime_minutes" in df_filtered.columns else np.nan)
    total_inc = (pd.to_numeric(df_filtered.get("incident_count", pd.Series(dtype=float)), errors="coerce").sum()
                 if "incident_count" in df_filtered.columns else np.nan)
    total_cost = (pd.to_numeric(df_filtered.get("estimated_cost_downtime", pd.Series(dtype=float)), errors="coerce").sum()
                  if "estimated_cost_downtime" in df_filtered.columns else np.nan)

    k1.metric("Average Uptime (%)", f"{avg_uptime:.2f}%" if pd.notna(avg_uptime) else "N/A")
    k2.metric("Total Downtime (mins)", f"{total_dt:,.0f}" if pd.notna(total_dt) else "N/A")
    k3.metric("Total Incidents", f"{total_inc:,.0f}" if pd.notna(total_inc) else "N/A")
    k4.metric("Total Downtime Cost (RM)", f"{total_cost:,.0f}" if pd.notna(total_cost) else "N/A")

    cdl1, cdl2 = st.columns([1, 1])
    with cdl1:
        st.download_button(
            "⬇️ Download filtered data (CSV)",
            df_filtered.to_csv(index=False).encode("utf-8"),
            file_name="service_dashboard_filtered.csv",
            mime="text/csv",
            use_container_width=True
        )
    with cdl2:
        kpi_snap = {
            "avg_uptime_pct": [avg_uptime],
            "total_downtime_mins": [total_dt],
            "total_incidents": [total_inc],
            "total_downtime_cost_rm": [total_cost],
            "unique_services": [df_filtered["service_name"].nunique() if "service_name" in df_filtered.columns else np.nan],
        }
        st.download_button(
            "⬇️ Download KPI snapshot (CSV)",
            pd.DataFrame(kpi_snap).to_csv(index=False).encode("utf-8"),
            file_name="service_dashboard_kpis.csv",
            mime="text/csv",
            use_container_width=True
        )

    # =========================================================
    # 🧠 Executive Service Overview (graphs only)
    # =========================================================
    st.markdown("---")
    st.markdown("### 🧠 Executive Service Overview")

    # Uptime trend over time
    c1, c2 = st.columns(2)
    with c1:
        if {"report_date", "uptime_percentage"}.issubset(df_filtered.columns):
            tmp = df_filtered.dropna(subset=["report_date"]).copy()
            # Aggregate by granularity
            grp = tmp.set_index("report_date").sort_index()["uptime_percentage"]
            ts = _agg_by_granularity(grp, how="mean", granularity=gran_key).reset_index()
            ts.columns = ["report_date", "avg_uptime"]
            if not ts.empty:
                fig = px.line(ts, x="report_date", y="avg_uptime",
                              title="Average Uptime Trend", markers=True,
                              labels={"avg_uptime": "Uptime (%)"},
                              color_discrete_sequence=PX_SEQ)
                if show_rangeslider:
                    fig.update_xaxes(rangeslider_visible=True)
                if show_smoothing and gran_key == "D":
                    ts["MA7"] = ts["avg_uptime"].rolling(7).mean()
                    fig.add_scatter(x=ts["report_date"], y=ts["MA7"], mode="lines", name="7-day MA")
                fig.update_layout(hovermode="x unified")
                st.plotly_chart(fig, use_container_width=True, key="svc_exec_uptime_trend")

    # Total downtime by service (minutes)
    with c2:
        if {"service_name", "downtime_minutes"}.issubset(df_filtered.columns):
            svc_down = (df_filtered.groupby("service_name", as_index=False)["downtime_minutes"]
                        .sum().sort_values("downtime_minutes", ascending=False))
            fig = px.bar(svc_down, x="service_name", y="downtime_minutes",
                         title="Total Downtime by Service (Minutes)",
                         text="downtime_minutes", labels={"service_name": "Service"},
                         color_discrete_sequence=PX_SEQ)
            fig = _apply_bar_labels(fig, show_labels)
            fig.update_traces(texttemplate="%{text:.0f}" if show_labels else None)
            fig.update_layout(xaxis_tickangle=-15)
            st.plotly_chart(fig, use_container_width=True, key="svc_exec_downtime_service")

    # MTTR vs RTO scatter
    if {"service_name", "recovery_time_minutes", "rto_target_minutes"}.issubset(df_filtered.columns):
        mttr = (df_filtered.groupby("service_name", as_index=False)[["recovery_time_minutes", "rto_target_minutes"]]
                .mean().dropna())
        if not mttr.empty:
            fig = px.scatter(mttr, x="rto_target_minutes", y="recovery_time_minutes",
                             text="service_name",
                             title="MTTR vs RTO by Service",
                             labels={"rto_target_minutes": "RTO Target (min)", "recovery_time_minutes": "Average Restore Time (min)"},
                             trendline="ols", color_discrete_sequence=PX_SEQ)
            st.plotly_chart(fig, use_container_width=True, key="svc_exec_mttr_rto")

    # Cost of downtime by category
    c3, c4 = st.columns(2)
    with c3:
        if {"service_category", "estimated_cost_downtime"}.issubset(df_filtered.columns):
            cat_cost = (df_filtered.groupby("service_category", as_index=False)["estimated_cost_downtime"]
                        .sum().sort_values("estimated_cost_downtime", ascending=False))
            fig = px.bar(cat_cost, x="service_category", y="estimated_cost_downtime",
                         title="Estimated Downtime Cost by Category (RM)",
                         text="estimated_cost_downtime",
                         labels={"service_category": "Category"},
                         color_discrete_sequence=PX_SEQ)
            fig.update_traces(texttemplate="RM %{text:,.0f}" if show_labels else None)
            fig.update_layout(xaxis_tickangle=-15)
            st.plotly_chart(fig, use_container_width=True, key="svc_exec_cost_category")

    # SLA compliance by service
    with c4:
        if {"service_name", "sla_met"}.issubset(df_filtered.columns):
            sla = (df_filtered.groupby("service_name", as_index=False)["sla_met"]
                   .mean().assign(sla_pct=lambda x: 100 * x["sla_met"]))
            fig = px.bar(sla.sort_values("sla_pct", ascending=False),
                         x="service_name", y="sla_pct", title="SLA Compliance by Service (%)",
                         text="sla_pct", labels={"sla_pct": "SLA Met (%)"},
                         color_discrete_sequence=PX_SEQ)
            fig.update_traces(texttemplate="%{text:.1f}%" if show_labels else None)
            fig.update_layout(xaxis_tickangle=-15)
            st.plotly_chart(fig, use_container_width=True, key="svc_exec_sla_service")

    # =========================================================
    # 📋 Service Overview (graphs only)
    # =========================================================
    st.markdown("---")
    st.markdown("### 📋 Service Overview")

    o1, o2 = st.columns(2)
    # Top 10 services by downtime COST
    with o1:
        if {"service_name", "estimated_cost_downtime"}.issubset(df_filtered.columns):
            top10 = (df_filtered.groupby("service_name", as_index=False)["estimated_cost_downtime"]
                     .sum().sort_values("estimated_cost_downtime", ascending=False).head(10))
            fig = px.bar(top10, x="service_name", y="estimated_cost_downtime",
                         title="Top 10 Services by Downtime Cost (RM)",
                         text="estimated_cost_downtime",
                         labels={"service_name": "Service"},
                         color_discrete_sequence=PX_SEQ)
            fig.update_traces(texttemplate="RM %{text:,.0f}" if show_labels else None)
            fig.update_layout(xaxis_tickangle=-15)
            st.plotly_chart(fig, use_container_width=True, key="svc_overview_top10_cost")

    # Downtime by owner & stakeholder (stacked)
    with o2:
        if {"service_owner", "stakeholder", "downtime_minutes"}.issubset(df_filtered.columns):
            owner_perf = (df_filtered.groupby(["service_owner", "stakeholder"], as_index=False)
                          .agg({"downtime_minutes": "sum"}))
            fig = px.bar(owner_perf, x="service_owner", y="downtime_minutes",
                         color="stakeholder", title="Downtime by Service Owner & Stakeholder",
                         text="downtime_minutes", labels={"downtime_minutes": "Downtime (mins)"},
                         color_discrete_sequence=PX_SEQ)
            fig.update_traces(texttemplate="%{text:.0f}" if show_labels else None)
            fig.update_layout(barmode="stack", xaxis_tickangle=-15)
            st.plotly_chart(fig, use_container_width=True, key="svc_overview_owner_stake")

    # Category share (donut)
    if {"service_category", "estimated_cost_downtime"}.issubset(df_filtered.columns):
        cat_summary = (df_filtered.groupby("service_category", as_index=False)["estimated_cost_downtime"].sum())
        if not cat_summary.empty:
            fig = px.pie(
                cat_summary,
                names="service_category",
                values="estimated_cost_downtime",
                hole=0.4,
                title="Downtime Cost Share by Category",
                color_discrete_sequence=BLUE_TONES,   # <- changed from Set3
            )
            st.plotly_chart(fig, use_container_width=True, key="svc_overview_cat_donut")

    # =========================================================
    # ⏱ Availability & SLA Metrics (graphs only)
    # =========================================================
    st.markdown("---")
    st.markdown("### ⏱ Availability & SLA Metrics")

    r1, r2 = st.columns(2)
    with r1:
        # Average uptime by service (ranked)
        if {"service_name", "uptime_percentage"}.issubset(df_filtered.columns):
            uptime_summary = (df_filtered.groupby("service_name", as_index=False)["uptime_percentage"]
                              .mean().sort_values("uptime_percentage", ascending=False))
            fig = px.bar(uptime_summary, x="service_name", y="uptime_percentage",
                         title="Average Uptime by Service (%)",
                         text="uptime_percentage", labels={"uptime_percentage": "Uptime (%)"},
                         color_discrete_sequence=PX_SEQ)
            fig.update_traces(texttemplate="%{text:.2f}%" if show_labels else None)
            fig.update_layout(xaxis_tickangle=-15)
            st.plotly_chart(fig, use_container_width=True, key="svc_avail_uptime_by_service")

    with r2:
        # Breach trend (if sla_met exists)
        if {"report_date", "sla_met"}.issubset(df_filtered.columns):
            tmp = df_filtered.copy()
            tmp = tmp.dropna(subset=["report_date"])
            tmp["report_date"] = pd.to_datetime(tmp["report_date"], errors="coerce")
            daily = (tmp.set_index("report_date").sort_index()["sla_met"].resample("D").mean() * 100).reset_index()
            daily.columns = ["report_date", "sla_pct"]
            if not daily.empty:
                fig = px.line(daily, x="report_date", y="sla_pct",
                              title="SLA Adherence Trend (%)",
                              labels={"sla_pct": "SLA Met (%)"},
                              markers=True, color_discrete_sequence=PX_SEQ)
                if show_rangeslider:
                    fig.update_xaxes(rangeslider_visible=True)
                if show_smoothing:
                    daily["MA7"] = daily["sla_pct"].rolling(7).mean()
                    fig.add_scatter(x=daily["report_date"], y=daily["MA7"], mode="lines", name="7-day MA")
                fig.update_layout(hovermode="x unified")
                st.plotly_chart(fig, use_container_width=True, key="svc_sla_trend")

    # =========================================================
    # 📈 Historical Availability Trends (graphs only)
    # =========================================================
    st.markdown("---")
    st.markdown("### 📈 Historical Availability Trends")

    h1, h2 = st.columns(2)
    if "report_date" in df_filtered.columns:
        tmp = df_filtered.dropna(subset=["report_date"]).copy()
        tmp["month"] = pd.to_datetime(tmp["report_date"], errors="coerce").dt.to_period("M").astype(str)

        with h1:
            if {"uptime_percentage"}.issubset(tmp.columns):
                monthly_uptime = tmp.groupby("month", as_index=False)["uptime_percentage"].mean()
                fig = px.line(monthly_uptime, x="month", y="uptime_percentage",
                              title="Average Uptime (Monthly)", markers=True,
                              labels={"uptime_percentage": "Uptime (%)"},
                              color_discrete_sequence=PX_SEQ)
                st.plotly_chart(fig, use_container_width=True, key="svc_hist_monthly_uptime")

        with h2:
            if "estimated_cost_downtime" in tmp.columns:
                monthly_cost = tmp.groupby("month", as_index=False)["estimated_cost_downtime"].sum()
                fig = px.bar(monthly_cost, x="month", y="estimated_cost_downtime",
                             title="Monthly Downtime Cost (RM)",
                             text="estimated_cost_downtime",
                             labels={"estimated_cost_downtime": "Cost (RM)"},
                             color_discrete_sequence=PX_SEQ)
                fig.update_traces(texttemplate="RM %{text:,.0f}" if show_labels else None)
                st.plotly_chart(fig, use_container_width=True, key="svc_hist_monthly_cost")

        # Multi-line: service uptime comparison over time
        if {"service_name", "uptime_percentage"}.issubset(tmp.columns):
            monthly_service = (tmp.groupby(["month", "service_name"], as_index=False)
                               .agg(avg_uptime=("uptime_percentage", "mean")))
            if not monthly_service.empty:
                fig = px.line(monthly_service, x="month", y="avg_uptime", color="service_name",
                              markers=True, title="Service Uptime Comparison Over Time",
                              labels={"avg_uptime": "Average Uptime (%)"},
                              color_discrete_sequence=PX_SEQ)
                fig.update_layout(hovermode="x unified")
                st.plotly_chart(fig, use_container_width=True, key="svc_hist_service_compare")

        # =========================================================
    # 🛠 Planned Maintenance (graphs only)
    # =========================================================
    st.markdown("---")
    st.markdown("### 🛠 Planned Maintenance")

    pm1, pm2 = st.columns(2)
    with pm1:
        if {"report_date", "maintenance_type"}.issubset(df_filtered.columns):
            tmp = df_filtered.dropna(subset=["report_date"]).copy()
            tmp["month"] = pd.to_datetime(tmp["report_date"], errors="coerce").dt.to_period("M").astype(str)
            scheduled = tmp[tmp["maintenance_type"].astype(str).str.lower() == "scheduled"]
            monthly_sched = scheduled.groupby("month").size().reset_index(name="maintenance_count")
            if not monthly_sched.empty:
                fig = px.bar(
                    monthly_sched, x="month", y="maintenance_count",
                    title="Monthly Scheduled Maintenance Activities",
                    text="maintenance_count",
                    labels={"maintenance_count": "Count"},
                    color_discrete_sequence=PX_SEQ
                )
                fig = _apply_bar_labels(fig, show_labels)
                st.plotly_chart(fig, use_container_width=True, key="svc_pm_monthly_count")
            else:
                st.info("No scheduled maintenance found for the selected filters.")
        else:
            st.warning("⚠️ Missing required columns: report_date, maintenance_type")

    with pm2:
        if {"service_name", "maintenance_type", "downtime_minutes"}.issubset(df_filtered.columns):
            planned = df_filtered[df_filtered["maintenance_type"].astype(str).str.lower() == "scheduled"].copy()
            if not planned.empty:
                planned["downtime_minutes"] = _to_num(planned["downtime_minutes"])
                downtime_summary = (planned.groupby("service_name", as_index=False)["downtime_minutes"]
                                    .sum().sort_values("downtime_minutes", ascending=False))
                fig = px.bar(
                    downtime_summary, x="service_name", y="downtime_minutes",
                    title="Planned Downtime Duration by Service",
                    text="downtime_minutes",
                    labels={"downtime_minutes": "Downtime (mins)"},
                    color_discrete_sequence=PX_SEQ
                )
                fig = _apply_bar_labels(fig, show_labels)
                fig.update_layout(xaxis_tickangle=-15)
                st.plotly_chart(fig, use_container_width=True, key="svc_pm_planned_downtime")
            else:
                st.info("No planned downtime records in the selected filters.")
        else:
            st.warning("⚠️ Missing required columns: service_name, maintenance_type, downtime_minutes")

    # =========================================================
    # 🚨 Emergency Changes (graphs only)
    # =========================================================
    st.markdown("---")
    st.markdown("### 🚨 Emergency Changes")

    # Normalize change_type if dataset uses maintenance_type
    df_ec = df_filtered.copy()
    if "change_type" not in df_ec.columns and "maintenance_type" in df_ec.columns:
        df_ec["change_type"] = df_ec["maintenance_type"]

    ec1, ec2 = st.columns(2)
    with ec1:
        need = {"report_date", "change_type"}
        if need.issubset(df_ec.columns):
            t = df_ec.dropna(subset=["report_date"]).copy()
            t["month"] = pd.to_datetime(t["report_date"], errors="coerce").dt.to_period("M").astype(str)
            emer = t[t["change_type"].astype(str).str.lower() == "emergency"]
            monthly = emer.groupby("month", as_index=False).size().rename(columns={"size": "emergency_count"})
            if not monthly.empty:
                fig = px.bar(
                    monthly, x="month", y="emergency_count",
                    title="Emergency Changes per Month",
                    text="emergency_count",
                    labels={"emergency_count": "Count"},
                    color_discrete_sequence=PX_SEQ
                )
                fig = _apply_bar_labels(fig, show_labels)
                st.plotly_chart(fig, use_container_width=True, key="svc_ec_count")
            else:
                st.info("✅ No emergency changes in the selected period.")
        else:
            st.warning("⚠️ Missing required columns: report_date, change_type")

    with ec2:
        need = {"report_date", "change_type", "uptime_percentage", "downtime_minutes"}
        if need.issubset(df_ec.columns):
            t = df_ec.copy()
            emer = t[t["change_type"].astype(str).str.lower() == "emergency"].copy()
            if not emer.empty:
                emer["report_date"] = pd.to_datetime(emer["report_date"], errors="coerce")
                emer["month"] = emer["report_date"].dt.to_period("M").astype(str)
                emer["uptime_percentage"] = _to_num(emer["uptime_percentage"])
                emer["downtime_minutes"] = _to_num(emer["downtime_minutes"])
                impact = emer.groupby("month", as_index=False).agg(
                    avg_uptime=("uptime_percentage", "mean"),
                    total_downtime=("downtime_minutes", "sum")
                )

                # Show line (uptime) overlayed with bars (downtime) in one figure for compact view
                fig = px.bar(
                    impact, x="month", y="total_downtime",
                    title="Emergency Months: Downtime (bars) & Uptime (line)",
                    labels={"total_downtime": "Downtime (mins)"},
                    color_discrete_sequence=PX_SEQ
                )
                fig.update_traces(name="Downtime (mins)")
                fig.add_scatter(x=impact["month"], y=impact["avg_uptime"], mode="lines+markers",
                                name="Avg Uptime (%)")
                st.plotly_chart(fig, use_container_width=True, key="svc_ec_impact")
            else:
                st.info("No emergency-change impact data in the selected filters.")
        else:
            st.warning("⚠️ Missing required columns: report_date, change_type, uptime_percentage, downtime_minutes")

    # =========================================================
    # 🛟 Service Recovery (graphs only)
    # =========================================================
    st.markdown("---")
    st.markdown("### 🛟 Service Recovery")

    sr1, sr2 = st.columns(2)
    with sr1:
        need = {"service_name", "recovery_time_minutes"}
        if need.issubset(df_filtered.columns):
            t = df_filtered.copy()
            t["recovery_time_minutes"] = _to_num(t["recovery_time_minutes"])
            mttr = (t.groupby("service_name", as_index=False)["recovery_time_minutes"]
                    .mean().rename(columns={"recovery_time_minutes": "avg_recovery"})
                    .sort_values("avg_recovery", ascending=False))
            if not mttr.empty:
                fig = px.bar(
                    mttr, x="service_name", y="avg_recovery",
                    title="Average Recovery Time (MTTR) by Service",
                    text="avg_recovery",
                    labels={"avg_recovery": "MTTR (mins)"},
                    color_discrete_sequence=PX_SEQ
                )
                fig.update_traces(texttemplate="%{text:.1f}" if show_labels else None)
                fig.update_layout(xaxis_tickangle=-15)
                st.plotly_chart(fig, use_container_width=True, key="svc_sr_mttr")
            else:
                st.info("No MTTR data available for the selection.")
        else:
            st.warning("⚠️ Missing required columns: service_name, recovery_time_minutes")

    with sr2:
        need = {"service_name", "recovery_time_minutes", "rto_target_minutes"}
        if need.issubset(df_filtered.columns):
            t = df_filtered.copy()
            t["recovery_time_minutes"] = _to_num(t["recovery_time_minutes"])
            t["rto_target_minutes"] = _to_num(t["rto_target_minutes"])
            t["rto_breach"] = t["recovery_time_minutes"] > t["rto_target_minutes"]
            rto = (t.groupby("service_name", as_index=False)["rto_breach"]
                   .sum().rename(columns={"rto_breach": "breaches"})
                   .sort_values("breaches", ascending=False))
            if not rto.empty:
                fig = px.bar(
                    rto, x="service_name", y="breaches",
                    title="RTO Breaches by Service",
                    text="breaches",
                    labels={"breaches": "Count"},
                    color_discrete_sequence=PX_SEQ
                )
                fig = _apply_bar_labels(fig, show_labels)
                fig.update_layout(xaxis_tickangle=-15)
                st.plotly_chart(fig, use_container_width=True, key="svc_sr_rto_breaches")
            else:
                st.info("No RTO breaches in the selected filters.")
        else:
            st.warning("⚠️ Missing required columns: service_name, recovery_time_minutes, rto_target_minutes")

    # Monthly MTTR trend (full width)
    if {"report_date", "recovery_time_minutes"}.issubset(df_filtered.columns):
        t = df_filtered.dropna(subset=["report_date"]).copy()
        t["report_date"] = pd.to_datetime(t["report_date"], errors="coerce")
        t["month"] = t["report_date"].dt.to_period("M").astype(str)
        t["recovery_time_minutes"] = _to_num(t["recovery_time_minutes"])
        monthly = t.groupby("month", as_index=False)["recovery_time_minutes"].mean().rename(columns={"recovery_time_minutes": "avg_mttr"})
        if not monthly.empty:
            fig = px.line(
                monthly, x="month", y="avg_mttr", markers=True,
                title="Monthly Average MTTR Trend",
                labels={"avg_mttr": "MTTR (mins)"},
                color_discrete_sequence=PX_SEQ
            )
            st.plotly_chart(fig, use_container_width=True, key="svc_sr_mttr_trend")
    else:
        st.warning("⚠️ Missing required columns: report_date, recovery_time_minutes")

    # =========================================================
    # 💼 Business Impact (graphs only)
    # =========================================================
    st.markdown("---")
    st.markdown("### 💼 Business Impact")

    bi1, bi2 = st.columns(2)
    with bi1:
        need = {"service_name", "estimated_cost_downtime"}
        if need.issubset(df_filtered.columns):
            t = df_filtered.copy()
            t["estimated_cost_downtime"] = _to_num(t["estimated_cost_downtime"])
            df_cost = (t.groupby("service_name", as_index=False)["estimated_cost_downtime"]
                       .sum().sort_values("estimated_cost_downtime", ascending=False))
            if not df_cost.empty:
                fig = px.bar(
                    df_cost, x="service_name", y="estimated_cost_downtime",
                    title="Total Estimated Downtime Cost by Service (RM)",
                    text="estimated_cost_downtime",
                    labels={"estimated_cost_downtime": "Cost (RM)"},
                    color_discrete_sequence=PX_SEQ
                )
                fig.update_traces(texttemplate="RM %{text:,.0f}" if show_labels else None)
                fig.update_layout(xaxis_tickangle=-15)
                st.plotly_chart(fig, use_container_width=True, key="svc_bi_cost_service")
            else:
                st.info("No cost data for the selected filters.")
        else:
            st.warning("⚠️ Missing required columns: service_name, estimated_cost_downtime")

    with bi2:
        need = {"business_impact"}
        if need.issubset(df_filtered.columns):
            t = df_filtered.copy()
            impact_count = t.groupby("business_impact").size().reset_index(name="count").sort_values("count", ascending=False)
            if not impact_count.empty:
                fig = px.pie(
                    impact_count,
                    names="business_impact",
                    values="count",
                    hole=0.4,
                    title="Distribution of Business Impact Levels",
                    color_discrete_sequence=BLUE_TONES,   # <- changed from Set3
                )
                st.plotly_chart(fig, use_container_width=True, key="svc_bi_impact_donut")
            else:
                st.info("No business impact categorization available.")
        else:
            st.warning("⚠️ Missing required column: business_impact")

    # RTO gap by service (full width)
    if {"service_name", "recovery_time_minutes", "rto_target_minutes"}.issubset(df_filtered.columns):
        t = df_filtered.copy()
        t["recovery_time_minutes"] = _to_num(t["recovery_time_minutes"])
        t["rto_target_minutes"] = _to_num(t["rto_target_minutes"])
        t["recovery_gap"] = t["recovery_time_minutes"] - t["rto_target_minutes"]
        if not t.empty:
            # Business Impact: RTO gap by service
            fig = px.bar(
                t, x="service_name", y="recovery_gap",
                color=(t["recovery_gap"] > 0),
                title="Recovery Time vs Target (RTO Gap)",
                labels={"recovery_gap": "Minutes Over Target"},
                color_discrete_map={
                    True: "#0066CC",   # over target (blue)
                    False: "#99CCFF",  # within target (light blue)
                },
            )
            fig.update_traces(cliponaxis=False)
            fig.update_layout(xaxis_tickangle=-15, legend_title_text="Over Target?")
            st.plotly_chart(fig, use_container_width=True, key="svc_bi_rto_gap")
    else:
        st.warning("⚠️ Missing required columns: service_name, recovery_time_minutes, rto_target_minutes")

    # =========================================================
    # 🧩 Resource Utilization & Scalability (graphs only)
    # =========================================================
    st.markdown("---")
    st.markdown("### 🧩 Resource Utilization & Scalability")

    ru1, ru2 = st.columns(2)
    with ru1:
        need = {"service_name", "cpu_utilization", "memory_utilization", "disk_utilization", "network_utilization"}
        if need.issubset(df_filtered.columns):
            util = df_filtered.groupby("service_name", as_index=False).agg({
                "cpu_utilization": "mean",
                "memory_utilization": "mean",
                "disk_utilization": "mean",
                "network_utilization": "mean",
            }).round(1)
            df_long = util.melt(id_vars="service_name", var_name="Resource", value_name="Utilization (%)")
            if not df_long.empty:
                fig = px.bar(
                    df_long, x="service_name", y="Utilization (%)", color="Resource",
                    barmode="group", title="Average Resource Utilization by Service",
                    color_discrete_sequence=PX_SEQ
                )
                fig.update_layout(xaxis_tickangle=-15)
                st.plotly_chart(fig, use_container_width=True, key="svc_ru_grouped")
            else:
                st.info("No utilization records for the selected filters.")
        else:
            st.warning("⚠️ Missing required columns for utilization (CPU/MEM/DISK/NET).")

    with ru2:
        need = {"service_name", "cpu_utilization", "incident_count", "downtime_minutes"}
        if need.issubset(df_filtered.columns):
            corr = df_filtered.groupby("service_name", as_index=False).agg({
                "cpu_utilization": "mean",
                "incident_count": "sum",
                "downtime_minutes": "sum",
            })
            if not corr.empty:
                fig = px.scatter(
                    corr, x="cpu_utilization", y="incident_count",
                    size="downtime_minutes", hover_name="service_name",
                    title="CPU Utilization vs Incident Volume (Bubble = Downtime)",
                    labels={"cpu_utilization": "CPU Utilization (%)", "incident_count": "Incident Count"},
                    color_discrete_sequence=PX_SEQ
                )
                st.plotly_chart(fig, use_container_width=True, key="svc_ru_scatter")
            else:
                st.info("No utilization/incidents correlation in the selected filters.")
        else:
            st.warning("⚠️ Missing required columns: service_name, cpu_utilization, incident_count, downtime_minutes")

    # Capacity status (full width)
    if {"service_name", "capacity_status"}.issubset(df_filtered.columns):
        cap = df_filtered.groupby(["service_name", "capacity_status"], as_index=False).size()
        if not cap.empty:
            fig = px.bar(
                cap, x="service_name", y="size", color="capacity_status",
                title="Capacity Status by Service",
                labels={"size": "Record Count", "capacity_status": "Capacity Status"},
                color_discrete_sequence=PX_SEQ
            )
            fig.update_layout(xaxis_tickangle=-15)
            st.plotly_chart(fig, use_container_width=True, key="svc_ru_capacity_status")
        else:
            st.info("No capacity status data for the selected filters.")
    else:
        st.warning("⚠️ Missing required columns: service_name, capacity_status")

__all__ = ["dashboard_service"]
