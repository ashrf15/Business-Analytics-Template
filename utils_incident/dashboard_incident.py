# dashboard_incident.py

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# ---- Visual defaults ----
px.defaults.template = "plotly_white"
PX_PALETTE = px.colors.qualitative.Safe
PX_SEQ = PX_PALETTE

# =========================
# Helpers
# =========================
def _apply_bar_labels(fig, show_labels: bool, fmt: str = None):
    """
    Apply data labels to bar-like traces only.
    Avoids setting invalid textposition on scatter/line traces.
    """
    if not show_labels:
        return fig

    for tr in fig.data:
        t = getattr(tr, "type", None)
        if t == "bar":
            tr.update(
                texttemplate=fmt if fmt else "%{y}",
                textposition="outside",
                cliponaxis=False,
            )
        elif t in ("pie", "funnel", "funnelarea", "waterfall"):
            tr.update(texttemplate=fmt if fmt else "%{value}")
        else:
            pass
    return fig


@st.cache_data(show_spinner=False)
def _prep_base(df: pd.DataFrame):
    d = df.copy()

    # --- Canonical datetime parsing
    for c in ("created_time", "resolved_time", "completed_time", "responded_date"):
        if c in d.columns:
            d[c] = pd.to_datetime(d[c], errors="coerce")
    if "created_time" in d.columns:
        d["created_date"] = d["created_time"].dt.date

    # --- RESPONSE: create response_hours (hours) no matter the input shape
    if "response_time_elapsed" in d.columns:
        rt = pd.to_timedelta(d["response_time_elapsed"], errors="coerce")
        d["response_hours"] = rt.dt.total_seconds() / 3600.0
    elif {"created_time", "responded_date"} <= set(d.columns):
        d["response_hours"] = (d["responded_date"] - d["created_time"]).dt.total_seconds() / 3600.0
    elif "response_time_minutes" in d.columns:
        d["response_hours"] = pd.to_numeric(d["response_time_minutes"], errors="coerce") / 60.0

    # --- RESOLUTION: create resolution_hours (hours) no matter the input shape
    if "resolution_time" in d.columns:
        rtd = pd.to_timedelta(d["resolution_time"], errors="coerce")
        d["resolution_hours"] = rtd.dt.total_seconds() / 3600.0
    elif {"created_time", "resolved_time"} <= set(d.columns):
        d["resolution_hours"] = (d["resolved_time"] - d["created_time"]).dt.total_seconds() / 3600.0
    elif {"created_time", "completed_time"} <= set(d.columns):
        d["resolution_hours"] = (d["completed_time"] - d["created_time"]).dt.total_seconds() / 3600.0

    # --- Keep legacy field used by KPIs
    if "resolution_time_hours" not in d.columns and "resolution_hours" in d.columns:
        d["resolution_time_hours"] = d["resolution_hours"]

    # --- Sanitize negatives/impossible durations
    for c in ("response_hours", "resolution_hours", "resolution_time_hours"):
        if c in d.columns:
            d[c] = pd.to_numeric(d[c], errors="coerce")
            d.loc[d[c] < 0, c] = np.nan

    return d


def _agg_by_granularity(s: pd.Series, how="count", granularity="D"):
    # s is a datetime-indexed Series
    if granularity == "W":
        return s.resample("W-MON").size() if how == "count" else s.resample("W-MON").mean()
    if granularity == "M":
        return s.resample("MS").size() if how == "count" else s.resample("MS").mean()
    return s.resample("D").size() if how == "count" else s.resample("D").mean()


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


def _compute_incident_kpis(df: pd.DataFrame) -> dict:
    d = df.copy()

    # Parse times if present
    for c in ("created_time", "responded_date", "resolved_time"):
        if c in d.columns:
            d[c] = pd.to_datetime(d[c], errors="coerce")

    # Derive durations
    if "response_hours" not in d.columns:
        if "response_time_elapsed" in d.columns:
            d["response_hours"] = pd.to_timedelta(d["response_time_elapsed"], errors="coerce").dt.total_seconds() / 3600.0
        elif {"created_time", "responded_date"} <= set(d.columns):
            d["response_hours"] = (d["responded_date"] - d["created_time"]).dt.total_seconds() / 3600.0

    if "resolution_hours" not in d.columns:
        if "time_elapsed" in d.columns:
            d["resolution_hours"] = pd.to_timedelta(d["time_elapsed"], errors="coerce").dt.total_seconds() / 3600.0
        elif {"created_time", "resolved_time"} <= set(d.columns):
            d["resolution_hours"] = (d["resolved_time"] - d["created_time"]).dt.total_seconds() / 3600.0

    # SLA targets in hours
    if "sla_response_hours" not in d.columns and "sla_response_time" in d.columns:
        d["sla_response_hours"] = pd.to_timedelta(d["sla_response_time"], errors="coerce").dt.total_seconds() / 3600.0
    if "sla_resolution_hours" not in d.columns and "sla_resolution_time" in d.columns:
        d["sla_resolution_hours"] = pd.to_timedelta(d["sla_resolution_time"], errors="coerce").dt.total_seconds() / 3600.0

    # KPI values
    total = int(len(d))
    avg_resp = float(d["response_hours"].mean()) if "response_hours" in d.columns and d["response_hours"].notna().any() else None
    avg_res  = float(d["resolution_hours"].mean()) if "resolution_hours" in d.columns and d["resolution_hours"].notna().any() else None

    resp_sla = None
    if {"response_hours","sla_response_hours"} <= set(d.columns):
        v = d.dropna(subset=["response_hours","sla_response_hours"])
        if not v.empty:
            resp_sla = float((v["response_hours"] <= v["sla_response_hours"]).mean() * 100)

    res_sla = None
    if {"resolution_hours","sla_resolution_hours"} <= set(d.columns):
        v = d.dropna(subset=["resolution_hours","sla_resolution_hours"])
        if not v.empty:
            res_sla = float((v["resolution_hours"] <= v["sla_resolution_hours"]).mean() * 100)

    open_tickets = None
    if "request_status" in d.columns:
        open_tickets = int((~d["request_status"].astype(str).str.lower().isin(["closed","resolved"])).sum())
    elif "resolved_time" in d.columns:
        open_tickets = int(d["resolved_time"].isna().sum())

    return {
        "Total Tickets": total,
        "Avg Response (hrs)": avg_resp,
        "Avg Resolution (hrs)": avg_res,
        "Response SLA %": resp_sla,
        "Resolution SLA %": res_sla,
        "Open Tickets": open_tickets,
    }


# =========================
# Main
# =========================
def dashboard_incident(df: pd.DataFrame):
    st.markdown("## 🚨 Incident Management Dashboard")
    df = _prep_base(df)

    # =========================================================
    # Sidebar: Column-aware, context-aware filters
    # 1) Date range first (if available)
    # 2) Attribute filters populated from the CURRENT date-filtered subset
    # 3) View options apply to charts only
    # =========================================================
    with st.sidebar:
        st.markdown("### 🔎 Filters")

        # ---------- DATE RANGE (drives option lists below) ----------
        if "created_date" in df.columns and not pd.isna(df["created_date"]).all():
            min_d = pd.to_datetime(df["created_date"]).min()
            max_d = pd.to_datetime(df["created_date"]).max()
            date_range = st.date_input(
                "Date range",
                value=(min_d.date(), max_d.date()),
                min_value=min_d.date(),
                max_value=max_d.date(),
                key="inc_flt_date_range",
            )
        else:
            date_range = None

        # Apply ONLY the date filter to compute relevant option lists
        df_for_options = df.copy()
        if date_range and "created_date" in df_for_options.columns:
            start_date, end_date = date_range if isinstance(date_range, tuple) else (date_range, date_range)
            df_for_options = df_for_options[
                (pd.to_datetime(df_for_options["created_date"]) >= pd.to_datetime(start_date)) &
                (pd.to_datetime(df_for_options["created_date"]) <= pd.to_datetime(end_date))
            ]

        def _choices(dfin: pd.DataFrame, col: str):
            if col not in dfin.columns:
                return []
            vals = dfin[col].dropna().astype(str).str.strip()
            vals = vals[vals != ""]
            out = sorted(vals.unique().tolist())
            return out

        # ---------- ATTRIBUTE FILTERS (only show when column exists & has variety) ----------
        # These filters are the ones actually used by our charts.
        # Department
        dept_opts = _choices(df_for_options, "department")
        if len(dept_opts) > 1:
            dept = st.multiselect("Department", dept_opts, key="inc_flt_dept")
        else:
            dept = []

        # Priority/Level (auto-detect correct column)
        pri_col_detect = None
        for c in ("level", "priority", "Priority"):
            if c in df_for_options.columns:
                pri_col_detect = c
                break
        if pri_col_detect:
            pri_opts = _choices(df_for_options, pri_col_detect)
            if len(pri_opts) > 1:
                pri = st.multiselect("Priority/Level", pri_opts, key="inc_flt_pri")
            else:
                pri = []
        else:
            pri = []

        # Technician
        tech_opts = _choices(df_for_options, "technician")
        if len(tech_opts) > 1:
            tech = st.multiselect("Technician", tech_opts, key="inc_flt_tech")
        else:
            tech = []

        # Category
        cat1_opts = _choices(df_for_options, "category")
        if len(cat1_opts) > 1:
            cat1 = st.multiselect("Category", cat1_opts, key="inc_flt_cat1")
        else:
            cat1 = []

        # Service Category
        cat2_opts = _choices(df_for_options, "service_category")
        if len(cat2_opts) > 1:
            cat2 = st.multiselect("Service Category", cat2_opts, key="inc_flt_cat2")
        else:
            cat2 = []

        # Request Status
        rstat_opts = _choices(df_for_options, "request_status")
        if len(rstat_opts) > 1:
            rstat = st.multiselect("Request Status", rstat_opts, key="inc_flt_rstat")
        else:
            rstat = []

        # Smart toggle: Only show Open incidents (appears only if we can infer "open")
        show_open_only = False
        if ("request_status" in df_for_options.columns) or ("resolved_time" in df_for_options.columns) or ("completed_time" in df_for_options.columns):
            show_open_only = st.toggle("Show only OPEN incidents", value=False, key="inc_flt_open_only")

        st.markdown("---")
        st.markdown("### ⚙️ View options")
        gran = st.radio("Time granularity", ["Daily","Weekly","Monthly"], horizontal=True, key="inc_gran")
        gran_key = {"Daily":"D","Weekly":"W","Monthly":"M"}[gran]
        show_labels = st.toggle("Show bar labels", value=True, key="inc_show_labels")
        show_rangeslider = st.toggle("Show range slider on time-series", value=True, key="inc_show_rangeslider")
        show_smoothing = st.toggle("Show 7-day moving average where relevant", value=False, key="inc_show_smoothing")

        st.markdown("---")
        clear = st.button("Clear all filters", use_container_width=True, key="inc_clear")

    # =========================================================
    # Apply all filters (date first → attribute filters)
    # =========================================================
    df_filtered = df.copy()

    if clear:
        # reset to date bounds in data
        if "created_date" in df_filtered.columns and date_range:
            date_range = (
                pd.to_datetime(df_filtered["created_date"]).min().date(),
                pd.to_datetime(df_filtered["created_date"]).max().date()
            )
        dept = pri = tech = cat1 = cat2 = rstat = []
        show_open_only = False

    # Date filter (if present)
    if date_range and "created_date" in df_filtered.columns:
        start_date, end_date = date_range if isinstance(date_range, tuple) else (date_range, date_range)
        df_filtered = df_filtered[
            (pd.to_datetime(df_filtered["created_date"]) >= pd.to_datetime(start_date)) &
            (pd.to_datetime(df_filtered["created_date"]) <= pd.to_datetime(end_date))
        ]

    # Attribute filters
    if dept and "department" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["department"].astype(str).isin(dept)]

    if pri:
        pri_col = None
        for c in ("level", "priority", "Priority"):
            if c in df_filtered.columns:
                pri_col = c
                break
        if pri_col:
            df_filtered = df_filtered[df_filtered[pri_col].astype(str).isin(pri)]

    if tech and "technician" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["technician"].astype(str).isin(tech)]

    if cat1 and "category" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["category"].astype(str).isin(cat1)]

    if cat2 and "service_category" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["service_category"].astype(str).isin(cat2)]

    if rstat and "request_status" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["request_status"].astype(str).isin(rstat)]

    # Open-only toggle (applied last)
    if show_open_only:
        if "request_status" in df_filtered.columns:
            df_filtered = df_filtered[~df_filtered["request_status"].astype(str).str.lower().isin({"closed","resolved"})]
        elif "resolved_time" in df_filtered.columns:
            df_filtered = df_filtered[df_filtered["resolved_time"].isna()]
        elif "completed_time" in df_filtered.columns:
            df_filtered = df_filtered[df_filtered["completed_time"].isna()]

    # =========================================================
    # KPIs
    # =========================================================
    st.markdown("---")
    st.markdown("### 🔹 Key Metrics")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Incidents", f"{len(df_filtered):,}")
    if "resolution_time_hours" in df_filtered.columns:
        k2.metric("Avg Resolution Time (hrs)", f"{pd.to_numeric(df_filtered['resolution_time_hours'], errors='coerce').mean():.2f}")
    else:
        k2.metric("Avg Resolution Time (hrs)", "N/A")
    k3.metric("Unique Categories", df_filtered['category'].nunique() if 'category' in df_filtered.columns else "N/A")
    if "sla_met" in df_filtered.columns:
        k4.metric("SLA Adherence", f"{(pd.to_numeric(df_filtered['sla_met'], errors='coerce').mean() * 100):.1f}%")
    else:
        k4.metric("SLA Adherence", "—")

    cdl1, cdl2 = st.columns([1,1])
    with cdl1:
        st.download_button(
            "⬇️ Download filtered data (CSV)",
            df_filtered.to_csv(index=False).encode("utf-8"),
            file_name="incident_dashboard_filtered.csv",
            mime="text/csv",
            use_container_width=True
        )
    with cdl2:
        kpi_snap = {
            "total_incidents": [len(df_filtered)],
            "avg_resolution_hrs": [pd.to_numeric(df_filtered.get('resolution_time_hours', pd.Series(dtype=float)), errors='coerce').mean()],
            "unique_categories": [df_filtered['category'].nunique() if 'category' in df_filtered.columns else np.nan],
            "sla_adherence_pct": [pd.to_numeric(df_filtered.get("sla_met", pd.Series(dtype=float)), errors='coerce').mean()*100 if "sla_met" in df_filtered.columns else np.nan],
        }
        st.download_button(
            "⬇️ Download KPI snapshot (CSV)",
            pd.DataFrame(kpi_snap).to_csv(index=False).encode("utf-8"),
            file_name="incident_dashboard_kpis.csv",
            mime="text/csv",
            use_container_width=True
        )

    # =========================================================
    # 🧭 Incident Overview
    # =========================================================
    st.markdown("---")
    st.markdown("### Incident Overview")

    # Row 1: Incidents Created Over Time | Incidents Resolved (by resolved_date)
    c1, c2 = st.columns(2)
    with c1:
        if "created_time" in df_filtered.columns:
            t = df_filtered.dropna(subset=["created_time"]).copy().set_index("created_time").sort_index()
            ts = _safe_timecounts_from_index(t.index, gran_key, "date").rename(columns={"count":"incidents"})
            if not ts.empty:
                fig = px.line(ts, x="date", y="incidents", title="Incidents Created Over Time", markers=True, color_discrete_sequence=PX_SEQ)
                if show_rangeslider:
                    fig.update_xaxes(rangeslider_visible=True)
                if show_smoothing and gran_key == "D":
                    ts["MA7"] = ts["incidents"].rolling(7).mean()
                    fig.add_scatter(x=ts["date"], y=ts["MA7"], mode="lines", name="7-day MA")
                fig.update_layout(hovermode="x unified")
                st.plotly_chart(fig, use_container_width=True, key="inc_1a_created_over_time")

    with c2:
        # Use completed_time (or resolved_time) as actual closure signal
        close_col = "completed_time" if "completed_time" in df_filtered.columns else ("resolved_time" if "resolved_time" in df_filtered.columns else None)
        if close_col:
            t = df_filtered.dropna(subset=[close_col]).copy().set_index(close_col).sort_index()
            ts = _safe_timecounts_from_index(t.index, gran_key, "date").rename(columns={"count":"closed"})
            fig = px.bar(ts, x="date", y="closed", title="Incidents Resolved (by actual resolved date)", color_discrete_sequence=PX_SEQ)
            fig = _apply_bar_labels(fig, show_labels)
            if show_rangeslider:
                fig.update_xaxes(rangeslider_visible=True)
            fig.update_layout(hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True, key="inc_1b_resolved_daily")

    # Row 2: Opened vs Closed | Incident Backlog
    c3, c4 = st.columns(2)
    with c3:
        if "created_time" in df_filtered.columns:
            dfr = df_filtered.copy()
            dfr["created_time"] = pd.to_datetime(dfr["created_time"], errors="coerce")
            close_col = "completed_time" if "completed_time" in dfr.columns else ("resolved_time" if "resolved_time" in dfr.columns else None)
            if close_col:
                dfr[close_col] = pd.to_datetime(dfr[close_col], errors="coerce")
                opened = _safe_timecounts_from_index(
                    dfr.dropna(subset=["created_time"]).set_index("created_time").sort_index().index,
                    gran_key, "date"
                ).rename(columns={"count":"opened"})
                closed = _safe_timecounts_from_index(
                    dfr.dropna(subset=[close_col]).set_index(close_col).sort_index().index,
                    gran_key, "date"
                ).rename(columns={"count":"closed"})
                rate = pd.merge(opened, closed, on="date", how="outer").fillna(0).sort_values("date")
                fig = px.line(rate, x="date", y=["opened","closed"], title="Opened vs Closed Over Time", color_discrete_sequence=PX_SEQ)
                if show_rangeslider:
                    fig.update_xaxes(rangeslider_visible=True)
                fig.update_layout(hovermode="x unified")
                st.plotly_chart(fig, use_container_width=True, key="inc_1c_opened_vs_closed")

    with c4:
        if "created_time" in df_filtered.columns:
            dfb = df_filtered.copy()
            close_col = "completed_time" if "completed_time" in dfb.columns else ("resolved_time" if "resolved_time" in dfb.columns else None)
            if close_col:
                op = _safe_timecounts_from_index(
                    dfb.dropna(subset=["created_time"]).set_index("created_time").sort_index().index,
                    gran_key, "date"
                ).rename(columns={"count":"opened"})
                cl = _safe_timecounts_from_index(
                    dfb.dropna(subset=[close_col]).set_index(close_col).sort_index().index,
                    gran_key, "date"
                ).rename(columns={"count":"closed"})
                rate = pd.merge(op, cl, on="date", how="outer").fillna(0).sort_values("date")
                rate["backlog"] = (rate["opened"] - rate["closed"]).cumsum()
                fig = px.line(rate, x="date", y="backlog", title="📈 Incident Backlog Over Time", color_discrete_sequence=PX_SEQ)
                if show_rangeslider:
                    fig.update_xaxes(rangeslider_visible=True)
                fig.update_layout(hovermode="x unified")
                st.plotly_chart(fig, use_container_width=True, key="inc_1d_backlog")

    # Row 3: Open Incidents by Level | Pareto – Incidents by Category
    c5, c6 = st.columns(2)
    with c5:
        if {"request_status","level"} <= set(df_filtered.columns):
            open_now = df_filtered[df_filtered["request_status"].astype(str).str.lower().eq("open")]
            if not open_now.empty:
                by_level = open_now.groupby("level").size().reset_index(name="open_count")
                fig = px.bar(by_level.sort_values("open_count", ascending=False), x="level", y="open_count",
                             title="Open Incidents by Level", text="open_count", color_discrete_sequence=PX_SEQ)
                fig = _apply_bar_labels(fig, show_labels)
                st.plotly_chart(fig, use_container_width=True, key="inc_1e_open_by_level")

    with c6:
        if "category" in df_filtered.columns:
            cat_summary = (
                df_filtered.groupby("category").size().reset_index(name="count")
                .sort_values("count", ascending=False)
            )
            if not cat_summary.empty:
                cat_summary["cum_pct"] = cat_summary["count"].cumsum() / cat_summary["count"].sum() * 100
                fig_pareto = px.bar(cat_summary, x="category", y="count",
                                    title="Pareto – Incidents by Category", color_discrete_sequence=PX_SEQ)
                fig_pareto.add_scatter(x=cat_summary["category"], y=cat_summary["cum_pct"],
                                       mode="lines+markers", name="Cumulative %")
                fig_pareto = _apply_bar_labels(fig_pareto, show_labels)
                st.plotly_chart(fig_pareto, use_container_width=True, key="inc_1f_pareto_category")

    # =========================================================
    # 🧩 Incident Classification
    # =========================================================
    st.markdown("---")
    st.markdown("### Incident Classification")

    # Row 4: Service Category Top 20 | Incidents by Level
    c7, c8 = st.columns(2)
    with c7:
        if "service_category" in df_filtered.columns:
            cat = df_filtered["service_category"].fillna("Unknown")
            counts = cat.value_counts().reset_index()
            counts.columns = ["service_category", "count"]
            if not counts.empty:
                fig = px.bar(counts.head(20), x="service_category", y="count",
                             title="Top Service Categories (count)", text="count", color_discrete_sequence=PX_SEQ)
                fig = _apply_bar_labels(fig, show_labels)
                st.plotly_chart(fig, use_container_width=True, key="inc_2a_service_category_top20")

    with c8:
        lvl_col = "level" if "level" in df_filtered.columns else None
        if lvl_col:
            lvl = df_filtered[lvl_col].fillna("Not Assigned")
            counts = lvl.value_counts().reset_index()
            counts.columns = [lvl_col, "count"]
            fig = px.bar(counts, x=lvl_col, y="count",
                         title="Incidents by Level", text="count", color_discrete_sequence=PX_SEQ)
            fig = _apply_bar_labels(fig, show_labels)
            st.plotly_chart(fig, use_container_width=True, key="inc_2b_incidents_by_level")

    # Row 5: SLA Adherence by Level (if SLA present) | Resolution Time Distribution
    c9, c10 = st.columns(2)
    with c9:
        if {"level", "created_time"}.issubset(df_filtered.columns) and (
           ("sla_resolution_time" in df_filtered.columns and "resolved_time" in df_filtered.columns) or
           ("sla_met" in df_filtered.columns)):
            tmp = df_filtered.copy()
            tmp["created_time"] = pd.to_datetime(tmp["created_time"], errors="coerce")

            if "sla_met" not in tmp.columns and {"resolved_time","sla_resolution_time"} <= set(tmp.columns):
                tmp["resolved_time"] = pd.to_datetime(tmp["resolved_time"], errors="coerce")
                tmp["resolution_hours"] = (tmp["resolved_time"] - tmp["created_time"]).dt.total_seconds() / 3600
                # Convert SLA to hours if timedelta
                if pd.api.types.is_timedelta64_dtype(tmp["sla_resolution_time"]):
                    tmp["sla_resolution_hours"] = tmp["sla_resolution_time"].dt.total_seconds() / 3600
                else:
                    tmp["sla_resolution_hours"] = pd.to_numeric(tmp["sla_resolution_time"], errors="coerce")
                tmp["sla_met"] = (tmp["resolution_hours"] <= tmp["sla_resolution_hours"]).astype(float)

            if {"level","sla_met"} <= set(tmp.columns):
                by_lvl = tmp.dropna(subset=["sla_met"]).groupby("level")["sla_met"].mean().reset_index()
                by_lvl["SLA %"] = (by_lvl["sla_met"] * 100).round(1)
                fig2 = px.bar(by_lvl.sort_values("SLA %", ascending=False), x="level", y="SLA %",
                              title="Resolution SLA Adherence by Level", text="SLA %",
                              color_discrete_sequence=PX_SEQ)
                fig2 = _apply_bar_labels(fig2, show_labels, fmt="%{text:.1f}")
                st.plotly_chart(fig2, use_container_width=True, key="inc_2c_sla_by_level")

    with c10:
        # Generic resolution distribution if we have resolution_time_hours (from _prep_base)
        if "resolution_time_hours" in df_filtered.columns:
            figh = px.histogram(df_filtered, x="resolution_time_hours", nbins=30,
                                title="Resolution Time Distribution (hours)",
                                labels={"resolution_time_hours":"Resolution Time (hours)"},
                                color_discrete_sequence=PX_SEQ)
            st.plotly_chart(figh, use_container_width=True, key="inc_2d_res_time_hist")

    # =========================================================
    # 3) Response & Resolution Times (Graphs only)
    # =========================================================
    st.markdown("---")
    st.markdown("### Response & Resolution")

    rr1, rr2 = st.columns(2)
    with rr1:
        if "response_hours" in df_filtered.columns and df_filtered["response_hours"].notna().any():
            fig = px.histogram(df_filtered, x="response_hours", nbins=30,
                               title="Response Time Distribution (hours)",
                               labels={"response_hours":"Response (hrs)"},
                               color_discrete_sequence=PX_SEQ)
            st.plotly_chart(fig, use_container_width=True, key="inc_resp_hist")

    with rr2:
        if "resolution_hours" in df_filtered.columns and df_filtered["resolution_hours"].notna().any():
            fig = px.box(df_filtered, y="resolution_hours", points="outliers",
                         title="Resolution Time (hours) – Variation",
                         labels={"resolution_hours":"Resolution (hrs)"},
                         color_discrete_sequence=PX_SEQ)
            st.plotly_chart(fig, use_container_width=True, key="inc_res_box")

    # SLA Adherence (%)
    if ({"response_hours","sla_response_hours"} <= set(df_filtered.columns)) or ({"resolution_hours","sla_resolution_hours"} <= set(df_filtered.columns)):
        frames = []
        if {"response_hours","sla_response_hours"} <= set(df_filtered.columns):
            valid = df_filtered.dropna(subset=["response_hours","sla_response_hours"])
            if not valid.empty:
                frames.append(("Response SLA %", (valid["response_hours"] <= valid["sla_response_hours"]).mean()*100))
        if {"resolution_hours","sla_resolution_hours"} <= set(df_filtered.columns):
            valid = df_filtered.dropna(subset=["resolution_hours","sla_resolution_hours"])
            if not valid.empty:
                frames.append(("Resolution SLA %", (valid["resolution_hours"] <= valid["sla_resolution_hours"]).mean()*100))
        if frames:
            sla_df = pd.DataFrame(frames, columns=["Metric","Percent"])
            fig = px.bar(sla_df, x="Metric", y="Percent", title="SLA Adherence (%)", text="Percent",
                         range_y=[0,100], color_discrete_sequence=PX_SEQ)
            fig = _apply_bar_labels(fig, show_labels, fmt="%{text:.1f}")
            st.plotly_chart(fig, use_container_width=True, key="inc_sla_bar")

    # =========================================================
    # 4) Incident Status (Graphs only)
    # =========================================================
    st.markdown("---")
    st.markdown("### Incident Status & Escalations")

    # Derive 'is_open'
    tmp = df_filtered.copy()
    if "is_open" not in tmp.columns:
        if "resolved_time" in tmp.columns:
            tmp["is_open"] = tmp["resolved_time"].isna()
        elif "completed_time" in tmp.columns:
            tmp["is_open"] = tmp["completed_time"].isna()
        elif "request_status" in tmp.columns:
            tmp["is_open"] = ~tmp["request_status"].astype(str).str.lower().isin({"closed","resolved"})
        else:
            tmp["is_open"] = False

    # Open incidents by derived status (bar)
    open_df = tmp[tmp["is_open"]].copy()
    if not open_df.empty:
        status_cols = [c for c in ["pending_status","on_hold_status","overdue_status"] if c in open_df.columns]
        if status_cols:
            open_df["derived_status"] = open_df[status_cols].apply(
                lambda r: next((str(v) for v in r if pd.notna(v) and str(v).strip() != ""), "Open"), axis=1
            )
        else:
            open_df["derived_status"] = "Open"
        counts = open_df["derived_status"].fillna("Open").value_counts().reset_index()
        counts.columns = ["Status","count"]
        fig = px.bar(counts, x="Status", y="count", title="Open Incidents — Derived Status",
                     text="count", color_discrete_sequence=PX_SEQ)
        fig = _apply_bar_labels(fig, show_labels)
        st.plotly_chart(fig, use_container_width=True, key="inc_open_status")

    # Escalation indicators (bar)
    frames = []
    have_proxy = False
    if "reopened" in df_filtered.columns:
        ro = df_filtered["reopened"].astype(str).str.lower().isin(["true","yes","1"]).sum()
        frames.append(("ReOpened Incidents", int(ro)))
        have_proxy = True
    if "overdue_status" in df_filtered.columns:
        od = df_filtered["overdue_status"].astype(str).str.lower().str.contains("overdue").sum()
        frames.append(("Overdue Incidents", int(od)))
        have_proxy = True
    if have_proxy:
        dd = pd.DataFrame(frames, columns=["Metric","Count"])
        fig = px.bar(dd, x="Metric", y="Count", title="Escalation Indicators", text="Count",
                     color_discrete_sequence=PX_SEQ)
        fig = _apply_bar_labels(fig, show_labels)
        st.plotly_chart(fig, use_container_width=True, key="inc_escalation_bar")

    # =========================================================
    # 5) Root Cause & Category Trends (Graphs only)
    # =========================================================
    st.markdown("---")
    st.markdown("### Root Cause & Category Trends")

    rc1, rc2 = st.columns(2)
    with rc1:
        # Root cause (proxy) top bars
        proxy_col = None
        for c in ["request_closure_code", "request_closure_comments"]:
            if c in df_filtered.columns:
                proxy_col = c
                break
        if proxy_col:
            ser = df_filtered[proxy_col].fillna("Unspecified").astype(str).str.strip()
            counts = ser.value_counts().reset_index()
            counts.columns = ["Root Cause (Proxy)","count"]
            fig = px.bar(counts.head(20), x="Root Cause (Proxy)", y="count",
                         title="Top Root Causes (Proxy)", text="count",
                         color_discrete_sequence=PX_SEQ)
            fig = _apply_bar_labels(fig, show_labels)
            st.plotly_chart(fig, use_container_width=True, key="inc_rca_top")

    with rc2:
        # Monthly trend by top 5 service categories
        if {"service_category","created_time"} <= set(df_filtered.columns):
            sc = df_filtered.dropna(subset=["service_category", "created_time"]).copy()
            sc["service_category"] = sc["service_category"].astype(str)
            top5 = sc["service_category"].value_counts().head(5).index.tolist()
            subset = sc[sc["service_category"].isin(top5)].copy()
            subset["created_month"] = subset["created_time"].dt.to_period("M").astype(str)
            trend = subset.groupby(["created_month","service_category"]).size().reset_index(name="count")
            if not trend.empty:
                fig = px.line(trend, x="created_month", y="count", color="service_category",
                              title="Monthly Trend by Top Service Categories",
                              labels={"created_month":"Month","count":"Incidents"},
                              color_discrete_sequence=PX_SEQ)
                st.plotly_chart(fig, use_container_width=True, key="inc_cat_trend")

    # Before vs After intervention — auto-pick midpoint of filtered range (graph only)
    if "created_time" in df_filtered.columns and df_filtered["created_time"].notna().any():
        ct = df_filtered.dropna(subset=["created_time"]).copy()
        if not ct.empty:
            lo = ct["created_time"].min().normalize()
            hi = ct["created_time"].max().normalize()
            mid = lo + (hi - lo) / 2  # automatic intervention point
            before_df = ct[ct["created_time"] < mid]
            after_df  = ct[ct["created_time"] >= mid]
            if len(before_df) > 0 and len(after_df) > 0:
                compare_df = pd.DataFrame({
                    "Period": ["Before","After"],
                    "Incident Volume": [len(before_df), len(after_df)]
                })
                fig = px.bar(compare_df, x="Period", y="Incident Volume", text="Incident Volume",
                             title=f"Incident Volume Before vs After (auto: {mid.date()})",
                             color_discrete_sequence=PX_SEQ)
                fig = _apply_bar_labels(fig, show_labels)
                st.plotly_chart(fig, use_container_width=True, key="inc_before_after")

    # =========================================================
    # 6) Incident Trends (Daily / Weekly / Monthly) + Seasonality
    # =========================================================
    st.markdown("---")
    st.markdown("### Temporal Trends & Seasonality")

    if "created_time" in df_filtered.columns and df_filtered["created_time"].notna().any():
        base = df_filtered.dropna(subset=["created_time"]).copy()

        # Daily / Weekly / Monthly series
        day = base.groupby(base["created_time"].dt.date).size().reset_index(name="count").rename(columns={"created_time":"date"})
        week = base.groupby(base["created_time"].dt.to_period("W").apply(lambda p: p.start_time.date())).size().reset_index(name="count").rename(columns={"created_time":"week_start"})
        month = base.groupby(base["created_time"].dt.to_period("M").apply(lambda p: p.start_time.date())).size().reset_index(name="count").rename(columns={"created_time":"month_start"})

        tr1, tr2, tr3 = st.columns(3)
        with tr1:
            if not day.empty:
                fig1 = px.line(day, x="date", y="count", title="Daily Incident Trends",
                                labels={"date":"Date","count":"Incidents"},
                                color_discrete_sequence=PX_SEQ)
                if show_rangeslider:
                    fig1.update_xaxes(rangeslider_visible=True)
                if show_smoothing:
                    d2 = day.sort_values("date").copy()
                    d2["MA7"] = d2["count"].rolling(7).mean()
                    fig1.add_scatter(x=d2["date"], y=d2["MA7"], mode="lines", name="7-day MA")
                fig1.update_layout(hovermode="x unified")
                st.plotly_chart(fig1, use_container_width=True, key="inc_trend_daily")

        with tr2:
            if not week.empty:
                fig2 = px.bar(week, x="week_start", y="count", title="Weekly Incident Volume",
                              labels={"week_start":"Week Start","count":"Incidents"},
                              color_discrete_sequence=PX_SEQ)
                fig2 = _apply_bar_labels(fig2, show_labels)
                st.plotly_chart(fig2, use_container_width=True, key="inc_trend_weekly")

        with tr3:
            if not month.empty:
                fig3 = px.area(month, x="month_start", y="count", title="Monthly Incident Volume Trend",
                               labels={"month_start":"Month","count":"Incidents"},
                               color_discrete_sequence=PX_SEQ)
                st.plotly_chart(fig3, use_container_width=True, key="inc_trend_monthly")

        # Seasonality heatmap (Weekday vs Week-of-Month)
        heat = base.copy()
        heat["Weekday"] = heat["created_time"].dt.day_name()
        heat["WeekOfMonth"] = ((heat["created_time"].dt.day - 1) // 7 + 1).astype(int)
        pivot = heat.pivot_table(index="Weekday", columns="WeekOfMonth", values="created_time", aggfunc="count").fillna(0)
        if not pivot.empty:
            fig_hm = go.Figure(data=go.Heatmap(
                z=pivot.values,
                x=[f"W{c}" for c in pivot.columns],
                y=pivot.index,
                coloraxis="coloraxis"
            ))
            fig_hm.update_layout(title="Seasonal Heatmap: Weekday vs Week-of-Month",
                                 coloraxis_colorscale="Viridis")
            st.plotly_chart(fig_hm, use_container_width=True, key="inc_heatmap_seasonal")

    # Done
    return df_filtered
