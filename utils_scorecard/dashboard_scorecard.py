# utils_scorecard/data_cleaning_and_dashboard_scorecard.py

import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import io
import re
import uuid
from typing import Optional

# ─────────────────────────────────────────────────────────────
# Mesiniaga palettes / theme
# ─────────────────────────────────────────────────────────────
BLUE_TONES = [
    "#004C99",  # deep brand navy
    "#0066CC",  # strong blue
    "#007ACC",  # azure
    "#3399FF",  # light blue
    "#66B2FF",  # lighter blue
    "#99CCFF",  # pale blue
]
MES_BLUE = ["#004C99", "#007ACC", "#3399FF", "#66B2FF", "#9BD1FF"]
PRIMARY_BLUE = "#007ACC"
px.defaults.template = "plotly_white"


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────
def to_snake(name: str) -> str:
    """
    Robust snake_case normalizer:
      - trim, collapse whitespace to underscores
      - swap hyphens & slashes to spaces first
      - remove non-word chars except underscores
      - lowercase
    """
    s = str(name).strip()
    s = s.replace("-", " ").replace("/", " ")
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[^\w\s]", "", s)
    s = s.replace(" ", "_").lower()
    return s


def arrow_sanitize_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Make df safe for Streamlit's Arrow bridge:
      - Mixed-type object cols -> string
      - Lists/dicts/tuples in cells -> string
      - Pandas nullable Int64 -> float64 (preserve NaN)
      - datetimes -> naive datetime64[ns]
      - categoricals -> string
    """
    out = df.copy()
    for col in out.columns:
        s = out[col]
        if pd.api.types.is_object_dtype(s):
            mask_bad = s.map(lambda x: isinstance(x, (list, dict, tuple, set)))
            if mask_bad.any():
                out.loc[mask_bad, col] = s[mask_bad].map(str)
            try:
                ntypes = s.map(lambda x: type(x).__name__).nunique()
            except Exception:
                ntypes = 2
            if ntypes > 1:
                out[col] = s.astype("string")
        elif str(s.dtype) == "Int64":
            out[col] = s.astype("float64")
        elif pd.api.types.is_datetime64_any_dtype(s):
            out[col] = pd.to_datetime(s, errors="coerce").dt.tz_localize(None)
        elif pd.api.types.is_categorical_dtype(s):
            out[col] = s.astype("string")
    return out


def _dtype_table(df: pd.DataFrame, title: str) -> pd.DataFrame:
    return pd.DataFrame({"Column": df.columns, title: [str(t) for t in df.dtypes.values]})


def _p75_excess(series: pd.Series):
    """Return (p75, share_above_p75) with numeric coercion."""
    s = pd.to_numeric(series, errors="coerce").dropna()
    if s.empty:
        return np.nan, np.nan
    p75 = float(np.percentile(s, 75))
    share = float((s > p75).mean()) if len(s) else np.nan
    return p75, share


def _first_present(df: pd.DataFrame, *candidates):
    for c in candidates:
        if c in df.columns:
            return c
    return None


def _group_time(df: pd.DataFrame, date_col, freq="D", sum_cols=None, mean_cols=None, out_date_name="date"):
    """Resample by freq (D/W/M). sum_cols and mean_cols are lists."""
    if df.empty or date_col not in df.columns:
        return pd.DataFrame()

    gdf = df.copy()

    # 🔒 Guard against duplicate date_col names (e.g. after rename() onto an existing column)
    cols = list(gdf.columns)
    if cols.count(date_col) > 1:
        keep_mask = []
        seen = False
        for c in cols:
            if c == date_col:
                if not seen:
                    keep_mask.append(True)
                    seen = True
                else:
                    # drop duplicate occurrences of the date_col
                    keep_mask.append(False)
            else:
                keep_mask.append(True)
        gdf = gdf.loc[:, keep_mask]

    # Now gdf[date_col] is a Series, not a multi-column DataFrame
    gdf[date_col] = pd.to_datetime(gdf[date_col], errors="coerce")
    gdf = gdf.dropna(subset=[date_col]).sort_values(date_col)
    if gdf.empty:
        return pd.DataFrame()
    gdf = gdf.set_index(date_col)

    agg = {}
    if sum_cols:
        for c in sum_cols:
            if c in gdf.columns:
                agg[c] = "sum"
    if mean_cols:
        for c in mean_cols:
            if c in gdf.columns:
                agg[c] = "mean"

    if not agg:
        # default to count of rows
        res = gdf.resample(freq).size().rename("count").reset_index()
    else:
        res = gdf.resample(freq).agg(agg).reset_index()

    res = res.rename(columns={date_col: out_date_name})
    return res


def _maybe_rangeslider(fig, on: bool):
    if on:
        fig.update_xaxes(rangeslider_visible=True)


def _maybe_labels_bar(fig, on: bool, default_text=None):
    if not on:
        return
    # If a text field is already bound, Streamlit/Plotly will use it.
    # Otherwise show y as label.
    if default_text is None:
        fig.update_traces(texttemplate="%{y}", textposition="outside")
    else:
        fig.update_traces(text=default_text, textposition="outside")


def _smooth_7(gdf, xcol, ycols):
    """Return a copy with 7-period rolling mean on listed ycols (aligned to x)."""
    out = gdf.copy()
    if out.empty or not ycols:
        return out
    out = out.sort_values(xcol)
    for c in ycols:
        if c in out.columns:
            out[c] = pd.to_numeric(out[c], errors="coerce")
            out[c] = out[c].rolling(7, min_periods=1).mean()
    return out


@st.cache_data(show_spinner=False)
def _prep_scorecard_base(df: Optional[pd.DataFrame]) -> pd.DataFrame:
    """
    Light prep for scorecard dashboard. Safe for None / non-DF / empty.
    """
    if df is None:
        return pd.DataFrame()

    if not isinstance(df, pd.DataFrame):
        try:
            df = pd.DataFrame(df)
        except Exception:
            return pd.DataFrame()

    d = df.copy()

    # Standardise / derive report date fields
    if "report_date" in d.columns:
        d["report_date_parsed"] = pd.to_datetime(d["report_date"], errors="coerce")
    if "report_date_parsed" in d.columns:
        d["report_date_only"] = pd.to_datetime(d["report_date_parsed"], errors="coerce").dt.date
        d["report_month"] = pd.to_datetime(d["report_date_parsed"], errors="coerce").dt.to_period("M").astype(str)

    # Some datasets may already have created_date, etc. Leave them as-is.
    return arrow_sanitize_df(d)


# ─────────────────────────────────────────────────────────────
# MAIN DASHBOARD
# ─────────────────────────────────────────────────────────────
def dashboard_scorecard(df: Optional[pd.DataFrame]):
    """Executive Scorecard Dashboard. Follows same format style as dashboard_ticket."""
    # --------- HARD GUARD ON INPUT ---------
    if df is None:
        st.error("❌ No dataset provided to 'dashboard_scorecard'. Load/clean a file first.")
        df = pd.DataFrame()

    if not isinstance(df, pd.DataFrame):
        try:
            df = pd.DataFrame(df)
        except Exception as e:
            st.error(f"❌ Invalid dataset type for 'dashboard_scorecard': {type(df)} | {e}")
            df = pd.DataFrame()

    st.markdown("##  IT Service Scorecard – Executive Dashboard")

    # Base prep (cached)
    df = _prep_scorecard_base(df)

    # ---------------- Sidebar controls ----------------
    date_col = _first_present(df, "report_date_parsed", "created_date", "report_date")

    with st.sidebar:
        st.markdown("### 🔎 Filters")

        # Date range widget (safe)
        if date_col and date_col in df.columns and not pd.Series(df[date_col]).dropna().empty:
            _cd = pd.to_datetime(df[date_col], errors="coerce").dropna()
            if not _cd.empty:
                min_d = _cd.min().date()
                max_d = _cd.max().date()
                date_range = st.date_input(
                    "Date range",
                    value=(min_d, max_d),
                    min_value=min_d,
                    max_value=max_d,
                    key="score_flt_date_range",
                )
            else:
                date_range = None
        else:
            date_range = None

        def _opt(col):
            return sorted([v for v in df[col].dropna().astype(str).unique()]) if col in df.columns else []

        dept = st.multiselect("Department", _opt("department"), key="score_flt_dept")
        pri = st.multiselect("Priority", _opt("priority") or _opt("Priority"), key="score_flt_pri")
        tech = st.multiselect("Technician", _opt("technician"), key="score_flt_tech")
        cat = st.multiselect("Category", _opt("category"), key="score_flt_cat")
        rstat = st.multiselect("Request Status", _opt("request_status"), key="score_flt_rstat")

        st.markdown("---")
        st.markdown("### ⚙️ View options")
        gran_label = st.radio(
            "Time granularity",
            ["Daily", "Weekly", "Monthly"],
            horizontal=True,
            key="score_gran",
        )
        gran_key = {"Daily": "D", "Weekly": "W", "Monthly": "M"}[gran_label]
        show_labels = st.toggle("Show bar labels", value=True, key="score_show_labels")
        show_rangeslider = st.toggle("Show range slider on time-series", value=True, key="score_show_rs")
        show_smoothing = st.toggle("Show 7-period moving average where relevant", value=False, key="score_show_smooth")

        st.markdown("---")
        clear = st.button("Clear all filters", use_container_width=True, key="score_clear")

    # -------------- Apply filters --------------
    df_filtered = df.copy()

    if clear:
        dept = pri = tech = cat = rstat = []
        if date_col and date_col in df_filtered.columns:
            _cd = pd.to_datetime(df_filtered[date_col], errors="coerce").dropna()
            if not _cd.empty:
                date_range = (_cd.min().date(), _cd.max().date())
            else:
                date_range = None

    if date_range and date_col and date_col in df_filtered.columns:
        start_date, end_date = date_range if isinstance(date_range, tuple) else (date_range, date_range)
        cdt = pd.to_datetime(df_filtered[date_col], errors="coerce")
        mask = cdt.ge(pd.to_datetime(start_date)) & cdt.le(pd.to_datetime(end_date))
        df_filtered = df_filtered[mask]

    if dept and "department" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["department"].astype(str).isin(dept)]

    pri_col = "priority" if "priority" in df_filtered.columns else ("Priority" if "Priority" in df_filtered.columns else None)
    if pri and pri_col:
        df_filtered = df_filtered[df_filtered[pri_col].astype(str).isin(pri)]

    if tech and "technician" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["technician"].astype(str).isin(tech)]

    if cat and "category" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["category"].astype(str).isin(cat)]

    if rstat and "request_status" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["request_status"].astype(str).isin(rstat)]

    # ===== KPIs =====
    st.markdown("---")
    st.markdown("### 🔹 Key Metrics")

    # 2) Date helpers (normalized)
    if "report_date" in df_filtered.columns and "report_date_parsed" not in df_filtered.columns:
        df_filtered["report_date_parsed"] = pd.to_datetime(df_filtered["report_date"], errors="coerce")
    if "report_date_parsed" in df_filtered.columns:
        df_filtered["report_date_only"] = df_filtered["report_date_parsed"].dt.date
        df_filtered["report_month"] = df_filtered["report_date_parsed"].dt.to_period("M").astype(str)

    # 3) KPI derivations
    total_opened = None
    total_closed = None
    avg_uptime = None
    sla_rr_met = None
    sla_rr_not = None

    if "report_date_only" in df_filtered.columns:
        daily_open = df_filtered.groupby("report_date_only").size().reset_index(name="ticket_count")
        total_opened = int(daily_open["ticket_count"].sum()) if not daily_open.empty else 0

    if "incident_count" in df_filtered.columns:
        total_opened = int(pd.to_numeric(df_filtered["incident_count"], errors="coerce").fillna(0).sum())

    if "changes_successful" in df_filtered.columns:
        total_closed = int(pd.to_numeric(df_filtered["changes_successful"], errors="coerce").fillna(0).sum())

    # Uptime
    uptime_source = "uptime_percent" if "uptime_percent" in df_filtered.columns else None
    if not uptime_source:
        cand = [c for c in df_filtered.columns if ("uptime" in c or "availability" in c)]
        if cand:
            uptime_source = cand[0]
    if uptime_source and uptime_source in df_filtered.columns:
        avg_uptime = float(pd.to_numeric(df_filtered[uptime_source], errors="coerce").dropna().mean()) if len(df_filtered) else None

    # SLA normalize
    if "sla_rr_norm" not in df_filtered.columns and "sla_response_resolution" in df_filtered.columns:
        def _norm_sla(x):
            if pd.isna(x):
                return np.nan
            s = str(x).strip().lower()
            if s in {"met", "met."}:
                return "Met"
            if s in {"not met", "not_met", "not-met", "notmet"}:
                return "Not Met"
            return np.nan

        df_filtered["sla_rr_norm"] = df_filtered["sla_response_resolution"].apply(_norm_sla)

    if "sla_rr_norm" in df_filtered.columns:
        vc = df_filtered["sla_rr_norm"].value_counts(dropna=False)
        sla_rr_met = int(vc.get("Met", 0))
        sla_rr_not = int(vc.get("Not Met", 0))

    # Extended KPIs
    avg_csat = float(pd.to_numeric(df_filtered["customer_satisfaction"], errors="coerce").dropna().mean()) \
        if "customer_satisfaction" in df_filtered.columns else None
    avg_nps = float(pd.to_numeric(df_filtered["nps_score"], errors="coerce").dropna().mean()) \
        if "nps_score" in df_filtered.columns else None
    avg_resp_mins = float(pd.to_numeric(df_filtered["avg_response_time_mins"], errors="coerce").dropna().mean()) \
        if "avg_response_time_mins" in df_filtered.columns else None
    avg_resolution_mins = float(pd.to_numeric(df_filtered["avg_resolution_time_mins"], errors="coerce").dropna().mean()) \
        if "avg_resolution_time_mins" in df_filtered.columns else None
    sd_resp_mins = float(pd.to_numeric(df_filtered["service_desk_response_time"], errors="coerce").dropna().mean()) \
        if "service_desk_response_time" in df_filtered.columns else None
    total_sec_incidents = int(pd.to_numeric(df_filtered["security_incidents"], errors="coerce").fillna(0).sum()) \
        if "security_incidents" in df_filtered.columns else None
    total_vuln_found = int(pd.to_numeric(df_filtered["vulnerabilities_found"], errors="coerce").fillna(0).sum()) \
        if "vulnerabilities_found" in df_filtered.columns else None

    # Compliance rate mean
    avg_compliance_pct = None
    if "compliance_rate" in df_filtered.columns:
        avg_compliance_pct = float(pd.to_numeric(df_filtered["compliance_rate"], errors="coerce").dropna().mean())
    elif "compliance_status" in df_filtered.columns:
        _map = {
            "compliant": True, "yes": True, "pass": True, "true": True, "1": True,
            "non-compliant": False, "non compliant": False, "no": False, "fail": False, "false": False, "0": False
        }
        _m = df_filtered["compliance_status"].astype(str).str.strip().str.lower().map(_map)
        if _m.notna().any():
            avg_compliance_pct = float(_m.mean() * 100.0)

    # Fleet avg util
    util_cols = [c for c in ["cpu_utilization", "memory_utilization", "disk_utilization", "network_utilization"]
                 if c in df_filtered.columns]
    fleet_avg_util = float(pd.to_numeric(df_filtered[util_cols].stack(), errors="coerce").dropna().mean()) \
        if util_cols else None

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Tickets Opened", f"{total_opened:,}" if total_opened is not None else "—")
    k2.metric("Total Tickets Closed", f"{total_closed:,}" if total_closed is not None else "—")
    k3.metric("Avg Uptime (%)", f"{avg_uptime:.2f}" if (avg_uptime is not None and not np.isnan(avg_uptime)) else "—")
    k4.metric(
        "SLA Met / Not Met",
        f"{sla_rr_met or 0} / {sla_rr_not or 0}" if (sla_rr_met is not None or sla_rr_not is not None) else "—",
    )

    k5, k6, k7, k8 = st.columns(4)
    k5.metric("Avg CSAT (%)", f"{avg_csat:.1f}" if avg_csat is not None else "—")
    k6.metric("Avg NPS", f"{avg_nps:.1f}" if avg_nps is not None else "—")
    resp_to_show = sd_resp_mins if sd_resp_mins is not None else avg_resp_mins
    k7.metric("Avg Response (mins)", f"{resp_to_show:.1f}" if resp_to_show is not None else "—")
    k8.metric("Avg Resolution (mins)", f"{avg_resolution_mins:.1f}" if avg_resolution_mins is not None else "—")

    k9, k10, k11, k12 = st.columns(4)
    k9.metric("Security Incidents (total)", f"{total_sec_incidents:,}" if total_sec_incidents is not None else "—")
    k10.metric("Vulnerabilities Found (total)", f"{total_vuln_found:,}" if total_vuln_found is not None else "—")
    k11.metric("Avg Compliance (%)", f"{avg_compliance_pct:.1f}" if avg_compliance_pct is not None else "—")
    k12.metric("Fleet Avg Utilization (%)", f"{fleet_avg_util:.1f}" if fleet_avg_util is not None else "—")

    # ===== Early exit if no data after filters =====
    if df_filtered.empty:
        st.info("No rows match the current filters. Adjust filters to see charts.")
        return df_filtered

    # =========================================================
    # 1) Service Overview
    # =========================================================
    st.markdown("---")
    st.markdown("### Service Overview")

    c1, c2 = st.columns(2)

    # Opened over time (respects granularity & smoothing)
    created_col = _first_present(df_filtered, "created_date", "report_date_parsed", "report_date")
    if created_col:
        trend = _group_time(df_filtered, created_col, freq=gran_key)
        if "count" in trend.columns and not trend.empty:
            with c1:
                fig = px.line(
                    trend,
                    x="date",
                    y="count",
                    title=f"Tickets Opened Over Time ({gran_label})",
                    color_discrete_sequence=BLUE_TONES,
                    markers=True,
                )
                if show_smoothing:
                    sm = _smooth_7(trend, "date", ["count"])
                    fig.add_scatter(x=sm["date"], y=sm["count"], mode="lines", name="7-period MA")
                _maybe_rangeslider(fig, show_rangeslider)
                st.plotly_chart(fig, use_container_width=True, key="score_svc_opened_over_time")

    # Tickets by Service Owner
    if "service_owner" in df_filtered.columns:
        owner_summary = df_filtered.groupby("service_owner").size().reset_index(name="ticket_count")
        with c2:
            option = st.radio(
                "Service Owner View:",
                ("Top 10 Highest", "Top 10 Lowest"),
                horizontal=True,
                key="score_svc_owner_radio",
            )
            if option == "Top 10 Highest":
                owner_top10 = owner_summary.sort_values("ticket_count", ascending=False).head(10).reset_index(drop=True)
                title = "Top 10 Service Owners with Highest Tickets Opened"
            else:
                owner_top10 = owner_summary.sort_values("ticket_count", ascending=True).head(10).reset_index(drop=True)
                title = "Top 10 Service Owners with Lowest Tickets Opened"

            fig_owner = px.bar(
                owner_top10,
                x="service_owner",
                y="ticket_count",
                title=title,
                text=("ticket_count" if show_labels else None),
                color_discrete_sequence=BLUE_TONES,
            )
            _maybe_labels_bar(fig_owner, show_labels)
            st.plotly_chart(fig_owner, use_container_width=True, key="score_svc_owner_bar")

    r1, r2 = st.columns(2)

    # Closed over time (granularity)
    if created_col:
        closed = _group_time(df_filtered, created_col, freq=gran_key)
        if "count" in closed.columns and not closed.empty:
            with r1:
                fig_c = px.bar(
                    closed,
                    x="date",
                    y="count",
                    title=f"Tickets Closed Over Time ({gran_label})",
                    labels={"count": "Tickets Closed"},
                    color_discrete_sequence=BLUE_TONES,
                    text=("count" if show_labels else None),
                )
                _maybe_labels_bar(fig_c, show_labels)
                _maybe_rangeslider(fig_c, show_rangeslider)
                st.plotly_chart(fig_c, use_container_width=True, key="score_svc_closed_over_time")

    # Open Tickets by Category
    if {"incident_count", "service_category"} <= set(df_filtered.columns):
        count_cat = df_filtered.groupby("service_category")["incident_count"].sum().reset_index(name="open_tickets")
        with r2:
            fig = px.bar(
                count_cat,
                x="service_category",
                y="open_tickets",
                title="Open Tickets by Category",
                labels={"service_category": "Category", "open_tickets": "Open Tickets"},
                color_discrete_sequence=BLUE_TONES,
                text=("open_tickets" if show_labels else None),
            )
            _maybe_labels_bar(fig, show_labels)
            st.plotly_chart(fig, use_container_width=True, key="score_svc_open_by_cat")

    r3, r4 = st.columns(2)

    # Open vs Closed (granularity)
    if created_col:
        opened = _group_time(df_filtered.assign(opened=1), created_col, freq=gran_key, sum_cols=["opened"])
        closed = _group_time(df_filtered.assign(closed=1), created_col, freq=gran_key, sum_cols=["closed"])
        if not opened.empty or not closed.empty:
            rate = pd.merge(opened, closed, on="date", how="outer").fillna(0)
            with r3:
                fig2 = px.line(
                    rate,
                    x="date",
                    y=["opened", "closed"],
                    title=f"Closure vs Opening Rate ({gran_label})",
                    labels={"value": "Tickets", "variable": "Metric"},
                    color_discrete_sequence=BLUE_TONES,
                    markers=True,
                )
                _maybe_rangeslider(fig2, show_rangeslider)
                st.plotly_chart(fig2, use_container_width=True, key="score_svc_open_close_line")

    # Backlog over time (granularity)
    if created_col and {"incident_count", "changes_successful"} <= set(df_filtered.columns):
        op = _group_time(df_filtered, created_col, freq=gran_key, sum_cols=["incident_count"])
        cl = _group_time(df_filtered, created_col, freq=gran_key, sum_cols=["changes_successful"])
        if not op.empty or not cl.empty:
            rate = pd.merge(op, cl, on="date", how="outer").fillna(0)
            rate["backlog"] = (
                pd.to_numeric(rate.get("incident_count", 0), errors="coerce").fillna(0)
                - pd.to_numeric(rate.get("changes_successful", 0), errors="coerce").fillna(0)
            ).cumsum()
            with r4:
                fig_backlog = px.line(
                    rate,
                    x="date",
                    y="backlog",
                    title=f"📈 Ticket Backlog Over Time ({gran_label})",
                    labels={"backlog": "Cumulative Backlog"},
                    color_discrete_sequence=BLUE_TONES,
                    markers=True,
                )
                _maybe_rangeslider(fig_backlog, show_rangeslider)
                st.plotly_chart(fig_backlog, use_container_width=True, key="score_ticket_backlog")

    # =========================================================
    # 2) Service Availability
    # =========================================================
    st.markdown("---")
    st.markdown("### Service Availability")

    a1, a2 = st.columns(2)

    # Uptime % over time
    if "uptime_percent" not in df_filtered.columns:
        cand = [c for c in df_filtered.columns if ("uptime" in c or "availability" in c)]
        if cand:
            df_filtered["uptime_percent"] = pd.to_numeric(df_filtered[cand[0]], errors="coerce")

    if "uptime_percent" in df_filtered.columns and "report_date_parsed" in df_filtered.columns:
        src = df_filtered[["report_date_parsed", "uptime_percent"]].rename(columns={"report_date_parsed": "report_date"})
        ts = _group_time(src, "report_date", freq=gran_key, mean_cols=["uptime_percent"])
        if not ts.empty:
            with a1:
                fig = px.line(
                    ts,
                    x="date",
                    y="uptime_percent",
                    markers=True,
                    title=f"Uptime % (mean) — {gran_label}",
                    labels={"uptime_percent": "Avg Uptime (%)"},
                    color_discrete_sequence=MES_BLUE,
                )
                _maybe_rangeslider(fig, show_rangeslider)
                st.plotly_chart(fig, use_container_width=True, key="score_avail_uptime")

            with a2:
                fig_area = px.area(
                    ts,
                    x="date",
                    y="uptime_percent",
                    title=f"Historical Availability Trend — {gran_label}",
                    labels={"uptime_percent": "Mean Uptime (%)"},
                    color_discrete_sequence=MES_BLUE,
                )
                _maybe_rangeslider(fig_area, show_rangeslider)
                st.plotly_chart(fig_area, use_container_width=True, key="score_avail_history_area")

    # SLA Availability distribution
    if "sla_availability" in df_filtered.columns:
        b1, _ = st.columns([2, 1])
        sla_dist = df_filtered["sla_availability"].value_counts(dropna=False).reset_index()
        sla_dist.columns = ["sla_availability", "records"]
        with b1:
            fig = px.bar(
                sla_dist,
                x="sla_availability",
                y="records",
                title="SLA Availability Levels",
                labels={"sla_availability": "SLA (%)", "records": "Records"},
                color_discrete_sequence=MES_BLUE,
                text=("records" if show_labels else None),
            )
            _maybe_labels_bar(fig, show_labels)
            st.plotly_chart(fig, use_container_width=True, key="score_avail_sla_levels")

    # =========================================================
    # 3) Response & Resolution
    # =========================================================
    st.markdown("---")
    st.markdown("### Response & Resolution")

    r1, r2 = st.columns(2)

    if "avg_response_time_mins" in df_filtered.columns:
        with r1:
            fig = px.histogram(
                df_filtered,
                x="avg_response_time_mins",
                nbins=40,
                title="Distribution: Response Time (mins)",
                color_discrete_sequence=MES_BLUE,
            )
            st.plotly_chart(fig, use_container_width=True, key="score_resp_hist")

    if "avg_resolution_time_mins" in df_filtered.columns:
        with r2:
            fig = px.histogram(
                df_filtered,
                x="avg_resolution_time_mins",
                nbins=40,
                title="Distribution: Resolution Time (mins)",
                color_discrete_sequence=MES_BLUE,
            )
            st.plotly_chart(fig, use_container_width=True, key="score_res_hist")

    # SLA RR normalisation
    if "sla_response_resolution" in df_filtered.columns and "sla_rr_norm" not in df_filtered.columns:
        def norm_sla(x):
            if pd.isna(x):
                return np.nan
            s = str(x).strip().lower()
            if s in {"met", "met."}:
                return "Met"
            if s in {"not met", "not_met", "not-met", "notmet"}:
                return "Not Met"
            return np.nan

        df_filtered["sla_rr_norm"] = df_filtered["sla_response_resolution"].apply(norm_sla)

    if "sla_rr_norm" in df_filtered.columns:
        c1, _ = st.columns([2, 1])
        sla = df_filtered["sla_rr_norm"].value_counts(dropna=False).reset_index()
        sla.columns = ["SLA_Adherence", "records"]
        with c1:
            fig = px.bar(
                sla,
                x="SLA_Adherence",
                y="records",
                title="SLA Adherence (Response/Resolution)",
                color_discrete_sequence=MES_BLUE,
                text=("records" if show_labels else None),
            )
            _maybe_labels_bar(fig, show_labels)
            st.plotly_chart(fig, use_container_width=True, key="score_rr_sla_bar")

    # =========================================================
    # 4) Change Management
    # =========================================================
    st.markdown("---")
    st.markdown("### Change Management")

    c1, c2 = st.columns(2)

    if {"changes_successful", "report_date_parsed"} <= set(df_filtered.columns):
        cm = _group_time(
            df_filtered.rename(columns={"report_date_parsed": "report_date"}),
            "report_date",
            freq=gran_key,
            sum_cols=["changes_successful"],
        )
        if not cm.empty:
            with c1:
                fig = px.bar(
                    cm,
                    x="date",
                    y="changes_successful",
                    title=f"Successful Changes — {gran_label}",
                    color_discrete_sequence=MES_BLUE,
                    text=("changes_successful" if show_labels else None),
                )
                _maybe_labels_bar(fig, show_labels)
                _maybe_rangeslider(fig, show_rangeslider)
                st.plotly_chart(fig, use_container_width=True, key="score_chg_success_bar")

    if {"changes_emergency", "report_date_parsed"} <= set(df_filtered.columns):
        em = _group_time(
            df_filtered.rename(columns={"report_date_parsed": "report_date"}),
            "report_date",
            freq=gran_key,
            sum_cols=["changes_emergency"],
        )
        if not em.empty:
            with c2:
                fig = px.line(
                    em,
                    x="date",
                    y="changes_emergency",
                    markers=True,
                    title=f"Emergency Changes — {gran_label}",
                    color_discrete_sequence=MES_BLUE,
                )
                _maybe_rangeslider(fig, show_rangeslider)
                st.plotly_chart(fig, use_container_width=True, key="score_chg_emerg_line")

    # Change SLA adherence
    if "sla_change_adherence" not in df_filtered.columns:
        possible_cols = [c for c in df_filtered.columns if "sla" in c and "change" in c]
        if possible_cols:
            df_filtered["sla_change_adherence"] = df_filtered[possible_cols[0]]

    if "sla_change_adherence" in df_filtered.columns:
        c3, _ = st.columns([2, 1])
        ch = df_filtered["sla_change_adherence"].value_counts(dropna=False).reset_index()
        ch.columns = ["sla_change_adherence", "records"]
        with c3:
            fig = px.bar(
                ch,
                x="sla_change_adherence",
                y="records",
                title="Change SLA Adherence",
                color_discrete_sequence=MES_BLUE,
                text=("records" if show_labels else None),
            )
            _maybe_labels_bar(fig, show_labels)
            st.plotly_chart(fig, use_container_width=True, key="score_chg_sla_bar")

    # =========================================================
    # 6) Service Desk Performance
    # =========================================================
    st.markdown("---")
    st.markdown("### 6) Service Desk Performance")

    s1, s2 = st.columns(2)

    if {"customer_satisfaction", "report_date_parsed"} <= set(df_filtered.columns):
        ser = pd.to_datetime(df_filtered["report_date_parsed"], errors="coerce")
        df_filtered["month"] = ser.dt.to_period("M").astype(str)

        with s1:
            fig = px.box(
                df_filtered,
                x="month",
                y="customer_satisfaction",
                points="outliers",
                title="Customer Satisfaction by Month",
                labels={"month": "Month", "customer_satisfaction": "Satisfaction (%)"},
                color_discrete_sequence=MES_BLUE,
                template="plotly_white",
            )
            fig.update_traces(marker_color=PRIMARY_BLUE, line_color=PRIMARY_BLUE)
            st.plotly_chart(fig, use_container_width=True, key="score_sdp_csat_box")


    if {"nps_score", "report_date_parsed"} <= set(df_filtered.columns):
        plot_df = _group_time(
            df_filtered.rename(columns={"report_date_parsed": "report_date"}),
            "report_date",
            freq=gran_key,
            mean_cols=["nps_score"],
        )
        if not plot_df.empty:
            with s2:
                fig = px.line(
                    plot_df,
                    x="date",
                    y="nps_score",
                    markers=True,
                    title=f"Average NPS — {gran_label}",
                    labels={"nps_score": "Avg NPS"},
                    color_discrete_sequence=MES_BLUE,
                    template="plotly_white",
                )
                _maybe_rangeslider(fig, show_rangeslider)
                st.plotly_chart(fig, use_container_width=True, key="score_sdp_nps_line")

    s3, _ = st.columns([2, 1])

    if {"service_desk_response_time", "report_date_parsed"} <= set(df_filtered.columns):
        plot_df = _group_time(
            df_filtered.rename(columns={"report_date_parsed": "report_date"}),
            "report_date",
            freq=gran_key,
            mean_cols=["service_desk_response_time"],
        )
        if not plot_df.empty:
            with s3:
                fig = px.line(
                    plot_df,
                    x="date",
                    y="service_desk_response_time",
                    markers=True,
                    title=f"Service Desk Response Time — {gran_label}",
                    labels={"service_desk_response_time": "Response (mins)"},
                    color_discrete_sequence=MES_BLUE,
                    template="plotly_white",
                )
                if show_smoothing:
                    sm = _smooth_7(plot_df, "date", ["service_desk_response_time"])
                    fig.add_scatter(
                        x=sm["date"],
                        y=sm["service_desk_response_time"],
                        mode="lines",
                        name="7-period MA",
                    )
                _maybe_rangeslider(fig, show_rangeslider)
                st.plotly_chart(fig, use_container_width=True, key="score_sdp_response_line")

    # =========================================================
    # 7) Security Metrics
    # =========================================================
    st.markdown("---")
    st.markdown("### 7) Security Metrics")

    g1, g2 = st.columns(2)

    need = {"report_date_parsed", "security_incidents"}
    if need.issubset(df_filtered.columns):
        tmp = _group_time(
            df_filtered.rename(columns={"report_date_parsed": "report_date"}),
            "report_date",
            freq=gran_key,
            sum_cols=["security_incidents"],
        )
        if not tmp.empty:
            with g1:
                fig = px.line(
                    tmp,
                    x="date",
                    y="security_incidents",
                    markers=True,
                    title=f"Security Incidents — {gran_label}",
                    labels={"security_incidents": "Incidents"},
                    color_discrete_sequence=MES_BLUE,
                    template="plotly_white",
                )
                _maybe_rangeslider(fig, show_rangeslider)
                st.plotly_chart(fig, use_container_width=True, key="score_sec_inc_line")

    need = {"report_date_parsed", "vulnerabilities_found"}
    if need.issubset(df_filtered.columns):
        tmp = _group_time(
            df_filtered.rename(columns={"report_date_parsed": "report_date"}),
            "report_date",
            freq=gran_key,
            sum_cols=["vulnerabilities_found"],
        )
        if not tmp.empty:
            with g2:
                fig = px.line(
                    tmp,
                    x="date",
                    y="vulnerabilities_found",
                    markers=True,
                    title=f"Vulnerabilities Found — {gran_label}",
                    labels={"vulnerabilities_found": "Count"},
                    color_discrete_sequence=MES_BLUE,
                    template="plotly_white",
                )
                _maybe_rangeslider(fig, show_rangeslider)
                st.plotly_chart(fig, use_container_width=True, key="score_sec_vuln_line")

    # Compliance rate line (full width)
    norm_map = {c: re.sub(r"[^\w]+", "_", c.strip().lower()) for c in df_filtered.columns}
    df_sec2 = df_filtered.rename(columns=norm_map).copy()
    if {"report_date_parsed", "compliance_status"}.issubset(df_sec2.columns):
        df_sec2["report_date"] = pd.to_datetime(df_sec2["report_date_parsed"], errors="coerce")
        status_map = {
            "compliant": True, "yes": True, "pass": True, "true": True, "1": True,
            "non-compliant": False, "non compliant": False, "no": False, "fail": False, "false": False, "0": False
        }
        df_sec2["is_compliant"] = df_sec2["compliance_status"].astype(str).str.strip().str.lower().map(status_map)
        df_sec2 = df_sec2.dropna(subset=["report_date", "is_compliant"])
        daily = _group_time(
            df_sec2[["report_date", "is_compliant"]],
            "report_date",
            freq=gran_key,
            mean_cols=["is_compliant"],
        )
        if not daily.empty:
            daily["compliance_rate"] = daily["is_compliant"] * 100.0
            fig = px.line(
                daily,
                x="date",
                y="compliance_rate",
                markers=True,
                title=f"Compliance Rate — {gran_label}",
                labels={"compliance_rate": "Compliance (%)"},
                color_discrete_sequence=MES_BLUE,
                template="plotly_white",
            )
            _maybe_rangeslider(fig, show_rangeslider)
            st.plotly_chart(fig, use_container_width=True, key="score_sec_compliance_line")

    # =========================================================
    # 8) Capacity & Scalability
    # =========================================================
    st.markdown("---")
    st.markdown("### 8) Capacity & Scalability")

    h1, h2 = st.columns(2)

    need_cap = {
        "service_name", "service_category",
        "cpu_utilization", "memory_utilization",
        "disk_utilization", "network_utilization",
    }
    if need_cap.issubset(df_filtered.columns):
        util = df_filtered.dropna(subset=["service_name"]).copy()
        grp = (
            util.groupby(["service_name", "service_category"])[
                ["cpu_utilization", "memory_utilization", "disk_utilization", "network_utilization"]
            ]
            .quantile(0.75)
            .reset_index()
        )
        if not grp.empty:
            grp["q3_avg_util"] = grp[
                ["cpu_utilization", "memory_utilization", "disk_utilization", "network_utilization"]
            ].mean(axis=1)
            top = grp.sort_values("q3_avg_util", ascending=False).head(12)
            with h1:
                fig = px.bar(
                    top,
                    x="service_name",
                    y="q3_avg_util",
                    color="service_category",
                    title="Critical Capacity Candidates (Q3 Avg Util)",
                    labels={"service_name": "Service", "q3_avg_util": "Q3 Avg Util (%)"},
                    color_discrete_sequence=MES_BLUE,
                    template="plotly_white",
                    text=("q3_avg_util" if show_labels else None),
                )
                _maybe_labels_bar(fig, show_labels)
                st.plotly_chart(fig, use_container_width=True, key="score_cap_top_q3_bar")

    need2 = {
        "report_date_parsed",
        "cpu_utilization", "memory_utilization",
        "disk_utilization", "network_utilization",
    }
    if need2.issubset(df_filtered.columns):
        util = df_filtered.rename(columns={"report_date_parsed": "report_date"})
        daily = _group_time(
            util,
            "report_date",
            freq=gran_key,
            mean_cols=["cpu_utilization", "memory_utilization", "disk_utilization", "network_utilization"],
        )
        if not daily.empty:
            long = daily.melt(id_vars=["date"], var_name="metric", value_name="util_pct")
            with h2:
                fig = px.line(
                    long,
                    x="date",
                    y="util_pct",
                    color="metric",
                    markers=True,
                    title=f"Fleet Average Utilization — {gran_label}",
                    labels={"util_pct": "Utilization (%)", "metric": "Metric"},
                    color_discrete_sequence=MES_BLUE,
                    template="plotly_white",
                )
                _maybe_rangeslider(fig, show_rangeslider)
                st.plotly_chart(fig, use_container_width=True, key="score_cap_fleet_line")

    # Full-width capacity plan focus
    if need_cap.issubset(df_filtered.columns):
        util = df_filtered.dropna(subset=["service_name"]).copy()
        grp = (
            util.groupby(["service_name", "service_category"])[
                ["cpu_utilization", "memory_utilization", "disk_utilization", "network_utilization"]
            ]
            .quantile(0.75)
            .reset_index()
        )
        if not grp.empty:
            grp["q3_avg_util"] = grp[
                ["cpu_utilization", "memory_utilization", "disk_utilization", "network_utilization"]
            ].mean(axis=1)
            top = grp.sort_values("q3_avg_util", ascending=False).head(15)
            fig = px.bar(
                top,
                x="service_name",
                y="q3_avg_util",
                color="service_category",
                title="Capacity Plan Focus — Top 15 (Q3 Avg Util)",
                labels={"q3_avg_util": "Q3 Avg Util (%)", "service_name": "Service"},
                hover_data=["cpu_utilization", "memory_utilization", "disk_utilization", "network_utilization"],
                color_discrete_sequence=MES_BLUE,
                template="plotly_white",
                text=("q3_avg_util" if show_labels else None),
            )
            _maybe_labels_bar(fig, show_labels)
            st.plotly_chart(fig, use_container_width=True, key="score_cap_plan_bar")

    return df_filtered
