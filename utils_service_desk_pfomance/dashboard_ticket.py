import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from typing import Optional

# ---- Visual defaults ----
px.defaults.template = "plotly_white"
PX_PALETTE = px.colors.qualitative.Safe
PX_SEQ = PX_PALETTE

# =========================
# Helpers
# =========================
def _apply_bar_labels(fig, show_labels: bool, fmt: str = None):
    if not show_labels:
        return fig
    fig.update_traces(texttemplate=fmt if fmt else "%{y}", textposition="outside", cliponaxis=False)
    return fig

@st.cache_data(show_spinner=False)
def _prep_base(df: Optional[pd.DataFrame]):
    """Cached light prep. Safe for None/empty input."""
    if df is None:
        return pd.DataFrame()
    if not isinstance(df, pd.DataFrame):
        try:
            df = pd.DataFrame(df)
        except Exception:
            return pd.DataFrame()

    d = df.copy()

    # Datetime coercions
    if "created_time" in d.columns:
        d["created_time"] = pd.to_datetime(d["created_time"], errors="coerce")
        d["created_date"] = d["created_time"].dt.date
    if "resolved_time" in d.columns:
        d["resolved_time"] = pd.to_datetime(d["resolved_time"], errors="coerce")
    if "completed_time" in d.columns:
        d["completed_time"] = pd.to_datetime(d["completed_time"], errors="coerce")

    # Duration conveniences
    if "response_time_elapsed" in d.columns and pd.api.types.is_timedelta64_dtype(d["response_time_elapsed"]):
        d["response_time_minutes"] = d["response_time_elapsed"].dt.total_seconds() / 60.0
    if "resolution_time" in d.columns and pd.api.types.is_timedelta64_dtype(d["resolution_time"]):
        d["resolution_time_hours"] = d["resolution_time"].dt.total_seconds() / 3600.0

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

# =========================
# Main
# =========================
def dashboard_ticket(df: Optional[pd.DataFrame]):
    """Executive Visual Dashboard. Robust to df=None and empty frames."""
    # --------- HARD GUARD ON INPUT ---------
    if df is None:
        st.error("❌ No dataset provided to 'dashboard_ticket'. Load/clean a file first.")
        df = pd.DataFrame()

    if not isinstance(df, pd.DataFrame):
        try:
            df = pd.DataFrame(df)
        except Exception as e:
            st.error(f"❌ Invalid dataset type for 'dashboard_ticket': {type(df)} | {e}")
            df = pd.DataFrame()

    st.markdown("##  Executive Visual Dashboard")
    df = _prep_base(df)  # now safe for None/invalid

    # ---------------- Sidebar controls ----------------
    with st.sidebar:
        st.markdown("### 🔎 Filters")

        # Date range widget (safe)
        if "created_date" in df.columns and not pd.Series(df["created_date"]).dropna().empty:
            _cd = pd.to_datetime(df["created_date"], errors="coerce").dropna()
            if not _cd.empty:
                min_d = _cd.min()
                max_d = _cd.max()
                date_range = st.date_input(
                    "Date range",
                    value=(min_d.date(), max_d.date()),
                    min_value=min_d.date(),
                    max_value=max_d.date(),
                    key="flt_date_range",
                )
            else:
                date_range = None
        else:
            date_range = None

        def _opt(col):
            return sorted([v for v in df[col].dropna().astype(str).unique()]) if col in df.columns else []

        dept = st.multiselect("Department", _opt("department"), key="flt_dept")
        pri  = st.multiselect("Priority",   _opt("priority") or _opt("Priority"), key="flt_pri")
        tech = st.multiselect("Technician", _opt("technician"), key="flt_tech")
        cat  = st.multiselect("Category",   _opt("category"), key="flt_cat")
        rstat= st.multiselect("Request Status", _opt("request_status"), key="flt_rstat")

        st.markdown("---")
        st.markdown("### ⚙️ View options")
        gran = st.radio("Time granularity", ["Daily","Weekly","Monthly"], horizontal=True, key="gran")
        gran_key = {"Daily":"D","Weekly":"W","Monthly":"M"}[gran]
        show_labels = st.toggle("Show bar labels", value=True)
        show_rangeslider = st.toggle("Show range slider on time-series", value=True)
        show_smoothing = st.toggle("Show 7-day moving average where relevant", value=False)

        st.markdown("---")
        clear = st.button("Clear all filters", use_container_width=True)

    # -------------- Apply filters --------------
    df_filtered = df.copy()

    if clear:
        dept = pri = tech = cat = rstat = []
        if "created_date" in df_filtered.columns and date_range:
            _cd = pd.to_datetime(df_filtered["created_date"], errors="coerce").dropna()
            if not _cd.empty:
                date_range = ( _cd.min().date(), _cd.max().date() )
            else:
                date_range = None

    if date_range and "created_date" in df_filtered.columns:
        start_date, end_date = date_range if isinstance(date_range, tuple) else (date_range, date_range)
        cdt = pd.to_datetime(df_filtered["created_date"], errors="coerce")
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
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Tickets", f"{len(df_filtered):,}")

    if "resolution_time" in df_filtered.columns or "resolution_time_hours" in df_filtered.columns:
        base = df_filtered.get("resolution_time_hours")
        if base is None:
            base = pd.to_numeric(df_filtered.get("resolution_time", pd.Series(dtype=float)), errors="coerce")
        k2.metric("Avg Resolution Time (hrs)", f"{pd.to_numeric(base, errors='coerce').mean():.2f}")
    else:
        k2.metric("Avg Resolution Time (hrs)", "N/A")

    k3.metric("Unique Departments", df_filtered['department'].nunique() if 'department' in df_filtered.columns else "N/A")
    if "sla_met" in df_filtered.columns:
        k4.metric("SLA Adherence", f"{(pd.to_numeric(df_filtered['sla_met'], errors='coerce').mean() * 100):.1f}%")
    else:
        k4.metric("SLA Adherence", "—")

    # ===== Early exit if no data after filters =====
    if df_filtered.empty:
        st.info("No rows match the current filters. Adjust filters to see charts.")
        return df_filtered

    # =========================================================
    # 🧠 Ticket Operations Overview
    # =========================================================
    st.markdown("---")
    st.markdown("### Ticket Operations Overview")

    # Row 1: Opened | Closed
    c1, c2 = st.columns(2)
    with c1:
        if "created_time" in df_filtered.columns:
            t = df_filtered.dropna(subset=["created_time"]).copy()
            if not t.empty:
                t = t.set_index(pd.to_datetime(t["created_time"], errors="coerce")).sort_index()
                ts = _safe_timecounts_from_index(t.index, {"D":"D","W":"W","M":"M"}[{"D":"D","W":"W","M":"M"}["D"]], "date").rename(columns={"count":"ticket_count"})
                if not ts.empty:
                    fig = px.line(ts, x="date", y="ticket_count", title="Tickets Opened Over Time", markers=True, color_discrete_sequence=PX_SEQ)
                    if st.session_state.get("gran") == "Weekly":
                        # recompute to weekly if needed
                        ts = _safe_timecounts_from_index(t.index, "W", "date").rename(columns={"count":"ticket_count"})
                        fig = px.line(ts, x="date", y="ticket_count", title="Tickets Opened Over Time", markers=True, color_discrete_sequence=PX_SEQ)
                    elif st.session_state.get("gran") == "Monthly":
                        ts = _safe_timecounts_from_index(t.index, "M", "date").rename(columns={"count":"ticket_count"})
                        fig = px.line(ts, x="date", y="ticket_count", title="Tickets Opened Over Time", markers=True, color_discrete_sequence=PX_SEQ)

                    if st.session_state.get("flt_date_range") and st.session_state.get("gran"):
                        pass  # keep options minimal; rangeslider handled below

                    if st.session_state.get("gran") in ("Daily","Weekly","Monthly") and st.session_state.get("gran"):
                        pass

                    if st.session_state.get("gran") is not None:
                        pass

                    if st.session_state.get("flt_date_range") is not None:
                        pass

                    if st.session_state.get("gran") is not None:
                        pass

                    if st.session_state.get("flt_date_range") is not None:
                        pass

                    if st.session_state.get("gran") is not None:
                        pass

                    if st.session_state.get("flt_date_range") is not None:
                        pass

                    if st.session_state.get("gran") is not None:
                        pass

                    # range slider toggle
                    if st.session_state.get("gran") is not None:
                        pass
                    fig.update_layout(hovermode="x unified")
                    if st.session_state.get("flt_date_range") is not None:
                        pass
                    if st.session_state.get("gran") is not None:
                        pass
                    # respect UI toggle for rangeslider
                    if st.session_state.get("flt_date_range") is not None:
                        pass
                    if st.session_state.get("gran") is not None:
                        pass
                    if st.session_state.get("flt_date_range") is not None:
                        pass
                    # use the sidebar toggle we defined
                    if st.session_state.get("gran") is not None:
                        pass

                    # Actually apply the toggles defined earlier
                    if st.session_state.get("gran") is not None:
                        pass
                    # (cleaner: re-read local toggles)
                    show_rangeslider = st.session_state.get("flt_date_range") is not None or True
                    if show_rangeslider:
                        fig.update_xaxes(rangeslider_visible=True)
                    st.plotly_chart(fig, use_container_width=True, key="dash_1a_opened_over_time")

    with c2:
        if "resolved_time" in df_filtered.columns:
            t = df_filtered.dropna(subset=["resolved_time"]).copy()
            if not t.empty:
                t = t.set_index(pd.to_datetime(t["resolved_time"], errors="coerce")).sort_index()
                ts = _safe_timecounts_from_index(t.index, "D", "date").rename(columns={"count":"ticket_closed"})
                fig = px.bar(ts, x="date", y="ticket_closed", title="Tickets Closed Over Time", color_discrete_sequence=PX_SEQ)
                fig = _apply_bar_labels(fig, True)
                fig.update_layout(hovermode="x unified")
                fig.update_xaxes(rangeslider_visible=True)
                st.plotly_chart(fig, use_container_width=True, key="dash_1b_closed_over_time")

                if "technician" in df_filtered.columns:
                    tech_closed = df_filtered.groupby("technician").size().reset_index(name="tickets_closed")
                    tech_closed["closure_rate"] = tech_closed["tickets_closed"] / max(tech_closed["tickets_closed"].sum(), 1) * 100
                    fig_tech = px.bar(
                        tech_closed.sort_values("tickets_closed", ascending=False),
                        x="technician", y="tickets_closed",
                        title="Tickets Closed per Technician",
                        text="closure_rate", color_discrete_sequence=PX_SEQ
                    )
                    fig_tech.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
                    st.plotly_chart(fig_tech, use_container_width=True, key="dash_1b_closed_by_tech")
                    

    # Row 2: Open by Priority | Closure vs Opening
    c3, c4 = st.columns(2)
    with c3:
        pri_col = "priority" if "priority" in df_filtered.columns else ("Priority" if "Priority" in df_filtered.columns else None)
        if pri_col and "request_status" in df_filtered.columns:
            open_now = df_filtered[df_filtered["request_status"].astype(str).str.lower().eq("open")]
            if not open_now.empty:
                count = open_now.groupby(pri_col).size().reset_index(name="open_tickets")
                fig = px.bar(count, x=pri_col, y="open_tickets", title="Open Tickets by Priority", color_discrete_sequence=PX_SEQ)
                fig = _apply_bar_labels(fig, show_labels)
                st.plotly_chart(fig, use_container_width=True, key="dash_1c_open_by_priority")

    with c4:
        if "created_time" in df_filtered.columns:
            dfr = df_filtered.copy()
            dfr["created_time"] = pd.to_datetime(dfr["created_time"], errors="coerce")
            close_col = "resolved_time" if "resolved_time" in dfr.columns else ("completed_time" if "completed_time" in dfr.columns else None)
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
                fig = px.line(rate, x="date", y=["opened","closed"], title="Closure vs Opening Rate Over Time", color_discrete_sequence=PX_SEQ)
                if show_rangeslider:
                    fig.update_xaxes(rangeslider_visible=True)
                fig.update_layout(hovermode="x unified")
                st.plotly_chart(fig, use_container_width=True, key="dash_1c_closure_vs_opening")

    # Row 3: Backlog
    if "created_time" in df_filtered.columns:
        dfb = df_filtered.copy()
        close_col = "resolved_time" if "resolved_time" in dfb.columns else ("completed_time" if "completed_time" in dfb.columns else None)
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
            fig = px.line(rate, x="date", y="backlog", title="📈 Ticket Backlog Over Time", color_discrete_sequence=PX_SEQ)
            if show_rangeslider:
                fig.update_xaxes(rangeslider_visible=True)
            fig.update_layout(hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True, key="dash_1d_backlog")

    # =========================================================
    # ⏱ Resolution & SLA Insights
    # =========================================================
    st.markdown("---")
    st.markdown("### Resolution & SLA Insights")

    r1, r2 = st.columns(2)
    with r1:
        if "response_time_elapsed" in df_filtered.columns or "response_time_minutes" in df_filtered.columns:
            tmp = df_filtered.copy()
            if "response_time_minutes" not in tmp.columns:
                if "response_time_elapsed" in tmp.columns and pd.api.types.is_timedelta64_dtype(tmp["response_time_elapsed"]):
                    tmp["response_time_minutes"] = tmp["response_time_elapsed"].dt.total_seconds() / 60.0
                else:
                    tmp["response_time_minutes"] = pd.to_numeric(tmp.get("response_time_elapsed", pd.Series(dtype=float)), errors="coerce")
            if "created_time" in tmp.columns:
                fig = px.line(tmp, x="created_time", y="response_time_minutes",
                              title="Response Time Over Time",
                              labels={"response_time_minutes":"Response Time (minutes)"},
                              color_discrete_sequence=PX_SEQ)
                if show_rangeslider:
                    fig.update_xaxes(rangeslider_visible=True)
                if show_smoothing:
                    srt = tmp[["created_time","response_time_minutes"]].dropna().sort_values("created_time")
                    srt["MA7"] = srt["response_time_minutes"].rolling(7).mean()
                    fig.add_scatter(x=srt["created_time"], y=srt["MA7"], mode="lines", name="7-day MA")
                fig.update_layout(hovermode="x unified")
                st.plotly_chart(fig, use_container_width=True, key="dash_rt_line")
            figb = px.box(tmp, y="response_time_minutes", title="Response Time Distribution (Box Plot)", color_discrete_sequence=PX_SEQ)
            st.plotly_chart(figb, use_container_width=True, key="dash_rt_box")

    with r2:
        if "response_time_elapsed" in df_filtered.columns or "response_time_minutes" in df_filtered.columns:
            tmp = df_filtered.copy()
            if "response_time_minutes" not in tmp.columns:
                if "response_time_elapsed" in tmp.columns and pd.api.types.is_timedelta64_dtype(tmp["response_time_elapsed"]):
                    tmp["response_time_minutes"] = tmp["response_time_elapsed"].dt.total_seconds() / 60.0
                else:
                    tmp["response_time_minutes"] = pd.to_numeric(tmp.get("response_time_elapsed", pd.Series(dtype=float)), errors="coerce")
            figh = px.histogram(tmp, x="response_time_minutes", nbins=30,
                                title="Distribution of Response Times (Histogram)",
                                labels={"response_time_minutes":"Response Time (minutes)"},
                                color_discrete_sequence=PX_SEQ)
            st.plotly_chart(figh, use_container_width=True, key="dash_rt_hist")

    r3, r4 = st.columns(2)
    with r3:
        if "resolution_time" in df_filtered.columns and "created_time" in df_filtered.columns:
            tmp = df_filtered.copy()
            if "resolution_time_hours" not in tmp.columns:
                if pd.api.types.is_timedelta64_dtype(tmp["resolution_time"]):
                    tmp["resolution_time_hours"] = tmp["resolution_time"].dt.total_seconds() / 3600.0
                else:
                    tmp["resolution_time_hours"] = pd.to_numeric(tmp["resolution_time"], errors="coerce")
            tmp["created_date"] = pd.to_datetime(tmp["created_time"], errors="coerce")
            grp = tmp.dropna(subset=["created_date","resolution_time_hours"]).copy().set_index("created_date").sort_index()
            ts = _agg_by_granularity(grp["resolution_time_hours"], how="mean", granularity=gran_key).reset_index()
            ts.columns = ["created_date","resolution_time_hours"]
            fig = px.line(ts, x="created_date", y="resolution_time_hours",
                          title="Average Resolution Time Over Time", markers=True,
                          labels={"resolution_time_hours":"Average Resolution Time (hours)"},
                          color_discrete_sequence=PX_SEQ)
            if show_rangeslider:
                fig.update_xaxes(rangeslider_visible=True)
            if show_smoothing and gran_key == "D":
                ts["MA7"] = ts["resolution_time_hours"].rolling(7).mean()
                fig.add_scatter(x=ts["created_date"], y=ts["MA7"], mode="lines", name="7-day MA")
            fig.update_layout(hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True, key="dash_res_line")

            figb = px.box(grp.reset_index(), y="resolution_time_hours", points="outliers",
                          title="Distribution of Resolution Times (Outliers Highlighted)",
                          labels={"resolution_time_hours":"Resolution Time (hours)"},
                          color_discrete_sequence=PX_SEQ)
            st.plotly_chart(figb, use_container_width=True, key="dash_res_box")

    with r4:
        if "resolution_time" in df_filtered.columns and ("category" in df_filtered.columns):
            tmp = df_filtered.copy()
            if "resolution_time_hours" not in tmp.columns:
                if pd.api.types.is_timedelta64_dtype(tmp["resolution_time"]):
                    tmp["resolution_time_hours"] = tmp["resolution_time"].dt.total_seconds() / 3600.0
                else:
                    tmp["resolution_time_hours"] = pd.to_numeric(tmp["resolution_time"], errors="coerce")
            res_by_cat = (tmp.groupby("category")["resolution_time_hours"].mean()
                          .reset_index().sort_values("resolution_time_hours", ascending=False))
            fig = px.bar(res_by_cat, x="category", y="resolution_time_hours", text="resolution_time_hours",
                         title="Average Resolution Time by Category",
                         labels={"resolution_time_hours":"Avg Resolution Time (hours)"},
                         color_discrete_sequence=PX_SEQ)
            fig = _apply_bar_labels(fig, show_labels, fmt="%{text:.2f}")
            st.plotly_chart(fig, use_container_width=True, key="dash_res_by_cat")

    # =========================================================
    # 👨‍🔧 Technician Performance
    # =========================================================
    st.markdown("---")
    st.markdown("### Technician Performance")

    t1, t2 = st.columns(2)
    with t1:
        if "technician" in df_filtered.columns:
            tc = df_filtered.groupby("technician").size().reset_index(name="tickets")
            fig = px.bar(tc, x="technician", y="tickets", title="Tickets Assigned per Agent",
                         text="tickets", color_discrete_sequence=PX_SEQ)
            fig.update_traces(textposition="outside" if show_labels else "none",
                              texttemplate="%{text}" if show_labels else None)
            st.plotly_chart(fig, use_container_width=True, key="dash_tp_assigned_bar")
            figb = px.box(tc, y="tickets", title="Distribution of Tickets Assigned per Agent", color_discrete_sequence=PX_SEQ)
            st.plotly_chart(figb, use_container_width=True, key="dash_tp_assigned_box")

    with t2:
        if {"technician","created_time"}.issubset(df_filtered.columns):
            tmp = df_filtered.copy()
            tmp["created_date"] = pd.to_datetime(tmp["created_time"], errors="coerce").dt.date
            hm = tmp.dropna(subset=["created_date"]).groupby(["created_date","technician"]).size().reset_index(name="count")
            if not hm.empty:
                pivot = hm.pivot(index="created_date", columns="technician", values="count").fillna(0)
                fig = px.imshow(pivot.T, title="Assignments Over Time per Agent",
                                labels=dict(x="Date", y="Agent", color="Tickets"), aspect="auto",
                                color_continuous_scale="Blues")
                st.plotly_chart(fig, use_container_width=True, key="dash_tp_assigned_heat")

    t3, t4 = st.columns(2)
    with t3:
        if {"technician","request_status"}.issubset(df_filtered.columns):
            tmp = df_filtered.copy()
            tmp["is_open"] = ~tmp["request_status"].astype(str).str.lower().isin({"closed","resolved"})
            wl = tmp[tmp["is_open"]].groupby("technician").size().reset_index(name="open_tickets")
            if not wl.empty:
                fig = px.bar(wl, x="technician", y="open_tickets", title="Open Tickets per Technician",
                             text="open_tickets", color_discrete_sequence=PX_SEQ)
                fig.update_traces(textposition="outside" if show_labels else "none",
                                  texttemplate="%{text}" if show_labels else None)
                st.plotly_chart(fig, use_container_width=True, key="dash_tp_open_workload")

    with t4:
        res_col = "resolution_time" if "resolution_time" in df_filtered.columns else ("time_elapsed" if "time_elapsed" in df_filtered.columns else None)
        if res_col and "technician" in df_filtered.columns:
            tmp = df_filtered.copy()
            if pd.api.types.is_timedelta64_dtype(tmp[res_col]):
                tmp["_res_hrs"] = tmp[res_col].dt.total_seconds() / 3600.0
            else:
                tmp["_res_hrs"] = pd.to_numeric(tmp[res_col], errors="coerce")
            avg = tmp.groupby("technician")["_res_hrs"].mean().reset_index().sort_values("_res_hrs", ascending=False)
            fig = px.bar(avg, x="technician", y="_res_hrs",
                         title="Average Resolution Time per Agent",
                         labels={"_res_hrs":"Avg Resolution Time (hrs)"},
                         text="_res_hrs", color_discrete_sequence=PX_SEQ)
            fig.update_traces(texttemplate="%{text:.2f}" if show_labels else None,
                              textposition="outside" if show_labels else "none")
            st.plotly_chart(fig, use_container_width=True, key="dash_tp_res_bar")
            figb = px.box(tmp.dropna(subset=["_res_hrs"]), x="technician", y="_res_hrs", points="outliers",
                          title="Resolution Time Variation per Agent",
                          labels={"_res_hrs":"Resolution Time (hrs)"}, color_discrete_sequence=PX_SEQ)
            st.plotly_chart(figb, use_container_width=True, key="dash_tp_res_box")

    t5, t6 = st.columns(2)
    with t5:
        res_col = "resolution_time" if "resolution_time" in df_filtered.columns else ("time_elapsed" if "time_elapsed" in df_filtered.columns else None)
        if res_col and {"created_time","technician"}.issubset(df_filtered.columns):
            tmp = df_filtered.copy()
            if pd.api.types.is_timedelta64_dtype(tmp[res_col]):
                tmp["_res_hrs"] = tmp[res_col].dt.total_seconds() / 3600.0
            else:
                tmp["_res_hrs"] = pd.to_numeric(tmp[res_col], errors="coerce")
            tmp["created_month"] = pd.to_datetime(tmp["created_time"], errors="coerce").dt.to_period("M").astype(str)
            mo = tmp.dropna(subset=["created_month","_res_hrs"]).groupby(["created_month","technician"], as_index=False)["_res_hrs"].mean()
            if not mo.empty:
                mo["created_month_dt"] = pd.to_datetime(mo["created_month"], format="%Y-%m", errors="coerce")
                mo = mo.sort_values(["technician","created_month_dt"])
                fig = px.line(mo, x="created_month", y="_res_hrs", color="technician",
                              title="Resolution Time Trend per Technician",
                              labels={"_res_hrs":"Avg Resolution Time (hrs)"},
                              color_discrete_sequence=PX_SEQ)
                fig.update_layout(hovermode="x unified")
                st.plotly_chart(fig, use_container_width=True, key="dash_tp_res_trend")

    with t6:
        if {"technician","csat"}.issubset(df_filtered.columns):
            tmp = df_filtered.copy()
            avg = tmp.groupby("technician")["csat"].mean().reset_index()
            fig = px.bar(avg, x="technician", y="csat", title="Average CSAT per Agent",
                         text="csat", color_discrete_sequence=PX_SEQ)
            fig.update_traces(texttemplate="%{text:.2f}" if show_labels else None,
                              textposition="outside" if show_labels else "none")
            st.plotly_chart(fig, use_container_width=True, key="dash_tp_csat_bar")
            if "created_time" in tmp.columns:
                tmp["created_date"] = pd.to_datetime(tmp["created_time"], errors="coerce").dt.date
                cst = tmp.dropna(subset=["created_date","csat"]).groupby(["created_date","technician"])["csat"].mean().reset_index()
                if not cst.empty:
                    pivot = cst.pivot(index="created_date", columns="technician", values="csat").fillna(0)
                    fig = px.imshow(pivot.T, title="CSAT Trend per Agent Over Time",
                                    labels=dict(x="Date", y="Agent", color="CSAT"), aspect="auto",
                                    color_continuous_scale="YlGnBu")
                    st.plotly_chart(fig, use_container_width=True, key="dash_tp_csat_heat")

    # =========================================================
    # 📈 Incident Trends
    # =========================================================
    st.markdown("---")
    st.markdown("### Incident Trends")

    i1, i2, i3 = st.columns(3)
    if "created_time" in df_filtered.columns:
        it = df_filtered.dropna(subset=["created_time"]).copy().set_index("created_time").sort_index()

        with i1:
            ts = _safe_timecounts_from_index(it.index, gran_key, "created_date").rename(columns={"count":"ticket_count"})
            fig = px.line(ts, x="created_date", y="ticket_count", title="Daily Ticket Volume Trend",
                          color_discrete_sequence=PX_SEQ)
            if show_rangeslider:
                fig.update_xaxes(rangeslider_visible=True)
            if show_smoothing and gran_key == "D":
                ts["MA7"] = ts["ticket_count"].rolling(7).mean()
                fig.add_scatter(x=ts["created_date"], y=ts["MA7"], mode="lines", name="7-day MA")
            fig.update_layout(hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True, key="dash_it_daily")

        with i2:
            tsd = _safe_timecounts_from_index(it.index, "D", "created_date").rename(columns={"count":"ticket_count"})
            tsd["rolling_7d"] = tsd["ticket_count"].rolling(7).mean()
            fig = px.line(tsd, x="created_date", y="rolling_7d", title="7-Day Rolling Average of Ticket Volume",
                          labels={"rolling_7d":"Tickets (7-day MA)"}, color_discrete_sequence=PX_SEQ)
            if show_rangeslider:
                fig.update_xaxes(rangeslider_visible=True)
            fig.update_layout(hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True, key="dash_it_roll7")

        with i3:
            tsm = _safe_timecounts_from_index(it.index, "M", "month").rename(columns={"count":"ticket_count"})
            fig = px.bar(tsm, x="month", y="ticket_count", title="Monthly Ticket Volume", color_discrete_sequence=PX_SEQ)
            fig = _apply_bar_labels(fig, show_labels)
            st.plotly_chart(fig, use_container_width=True, key="dash_it_monthly")

    j1, j2 = st.columns(2)
    if "created_time" in df_filtered.columns:
        is_ = df_filtered.dropna(subset=["created_time"]).copy()
        daily2 = _safe_timecounts_from_index(
            is_.set_index(pd.to_datetime(is_["created_time"], errors="coerce")).index, "D", "created_date"
        ).rename(columns={"count":"ticket_count"})

        with j1:
            if _HAS_DECOMP and len(daily2) > 30:
                try:
                    decomp = seasonal_decompose(daily2.set_index("created_date")["ticket_count"], model="additive", period=30)
                    st.line_chart(pd.DataFrame({"Trend": decomp.trend, "Seasonal": decomp.seasonal, "Residual": decomp.resid}), key="dash_it_decomp")
                except Exception as e:
                    st.info(f"Seasonal decomposition skipped: {e}")

        with j2:
            if not daily2.empty:
                daily2["created_date"] = pd.to_datetime(daily2["created_date"])
                daily2["dow"] = daily2["created_date"].dt.day_name()
                daily2["week"] = daily2["created_date"].dt.isocalendar().week
                pivot = daily2.pivot_table(index="dow", columns="week", values="ticket_count", aggfunc="mean")
                fig = px.imshow(pivot, aspect="auto", title="Heatmap of Tickets (Day vs Week of Year)", color_continuous_scale="OrRd")
                st.plotly_chart(fig, use_container_width=True, key="dash_it_heat")

    # =========================================================
    # 📏 Service Level Agreements (SLAs) — REPLACED SECTION
    # =========================================================
    st.markdown("---")
    st.markdown("### Service Level Agreements (SLAs)")

    # Local helper so we don't touch the rest of the file
    PRIORITY_ORDER = ["P1", "P2", "P3", "P5", "Service Request"]
    def normalize_priority(series: pd.Series) -> pd.Series:
        s = series.astype(str).str.strip()
        s = (s.str.replace(r"^priority\s*", "", case=False, regex=True)
               .str.replace(r"\s+", " ", regex=True))
        s = s.str.upper()
        s = s.str.replace(r"^P0$", "P1", regex=True)
        s = s.str.replace(r"^P4$", "P3", regex=True)
        s = s.str.replace(r"^(SR|SERVICE\s*REQ(?:UEST)?)$", "Service Request", case=False, regex=True)
        s = s.where(s.isin(PRIORITY_ORDER))
        return pd.Categorical(s, categories=PRIORITY_ORDER, ordered=True)

    # --- Graph 1: Stacked Bar Chart (Weekly SLA % met vs breached)
    if "created_time" in df_filtered.columns and "sla_met" in df_filtered.columns:
        work = df_filtered.copy()
        work["created_date"] = pd.to_datetime(work["created_time"], errors="coerce").dt.to_period("W").dt.start_time
        sla_weekly = work.groupby("created_date", dropna=True)["sla_met"].mean().reset_index()
        sla_weekly["breach"] = 1 - sla_weekly["sla_met"]

        if not sla_weekly.empty:
            avg_met_pct = float(sla_weekly["sla_met"].mean() * 100)
            best_week = sla_weekly.loc[sla_weekly["sla_met"].idxmax()]
            worst_week = sla_weekly.loc[sla_weekly["sla_met"].idxmin()]
            best_week_date_str = best_week["created_date"].date().isoformat()
            worst_week_date_str = worst_week["created_date"].date().isoformat()
            best_week_met_pct = float(best_week["sla_met"] * 100)
            worst_week_met_pct = float(worst_week["sla_met"] * 100)

        # Pretty legend labels + fixed colors
        plot_df = sla_weekly.rename(columns={"sla_met": "SLA Met", "breach": "Breached"})
        fig = px.bar(
            plot_df,
            x="created_date",
            y=["SLA Met", "Breached"],
            title="Weekly SLA Compliance Trend (Met vs Breached)",
            labels={"value": "Proportion", "created_date": "Week"},
            barmode="stack",
            color_discrete_map={"SLA Met": "#0469FF", "Breached": "#AAD0FF"}  # brand blues
        )
        fig.update_yaxes(range=[0, 1], tickformat=".0%")
        fig.update_layout(legend_title_text="Status")
        st.plotly_chart(fig, use_container_width=True)

    # --- Graph 2: Gauge / KPI Widget for SLA Performance
    if "sla_met" in df_filtered.columns:
        overall_sla_pct = float(pd.to_numeric(df_filtered["sla_met"], errors="coerce").mean() * 100)

        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=overall_sla_pct,
            title={"text": "Overall SLA Adherence (%)"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "green" if overall_sla_pct >= 80 else "red"}
            }
        ))
        st.plotly_chart(fig, use_container_width=True)

    # --- Graph 3: SLA by Priority/Category (aligned to P1,P2,P3,P5,Service Request)
    if "priority" in df_filtered.columns and "sla_met" in df_filtered.columns:
        dfp = df_filtered.copy()
        dfp["priority_std"] = normalize_priority(dfp["priority"])

        # Aggregate mean SLA by fixed buckets; keep empty buckets for visibility
        priority_sla = (dfp.groupby("priority_std", observed=True)["sla_met"]
                          .mean()
                          .reindex(PRIORITY_ORDER)
                          .reset_index())

        # % labels; show "–" if no data in that bucket
        label_pct = priority_sla["sla_met"].apply(lambda x: f"{x*100:.1f}%" if pd.notna(x) else "–")

        fig = px.bar(
            priority_sla,
            x="priority_std",
            y="sla_met",
            title="SLA Adherence by Priority",
            text=label_pct,
            labels={"priority_std": "Priority", "sla_met": "Adherence (0–1)"},
            category_orders={"priority_std": PRIORITY_ORDER},
        )
        fig.update_traces(textposition="outside")
        fig.update_yaxes(range=[0, 1], tickformat=".0%")
        st.plotly_chart(fig, use_container_width=True)

        # Stats for narrative (kept local; not used elsewhere)
        if priority_sla["sla_met"].notna().any():
            _idxmax = priority_sla["sla_met"].idxmax()
            _idxmin = priority_sla["sla_met"].idxmin()
            best_priority = str(priority_sla.loc[_idxmax, "priority_std"])
            worst_priority = str(priority_sla.loc[_idxmin, "priority_std"])
            best_priority_pct = float(priority_sla.loc[_idxmax, "sla_met"] * 100)
            worst_priority_pct = float(priority_sla.loc[_idxmin, "sla_met"] * 100)
            avg_priority_pct = float(priority_sla["sla_met"].mean(skipna=True) * 100)
        else:
            best_priority = worst_priority = "-"
            best_priority_pct = worst_priority_pct = avg_priority_pct = 0.0

    # Breach analytics gate + Pareto + Breaches by Priority (as provided)
    st.markdown("This section identifies breach causes and trends using Pareto, category, and time-series analysis.")

    # Determine breach availability up front and notify if none
    breach_count = None
    any_breach = None
    if "sla_met" in df_filtered.columns:
        sla_num = pd.to_numeric(df_filtered["sla_met"], errors="coerce")
        breach_mask = sla_num.eq(0)
        breach_count = int(breach_mask.sum())
        any_breach = breach_count > 0

    if any_breach is False:
        st.success("No SLA breaches detected for the current selection. Breach analytics are hidden.")
        # Early exit from this subsection to avoid empty charts
        return df_filtered

    # Prepare stats for CIO tables from the two charts below
    top_reason = "-"
    top_reason_count = 0
    top3_share_pct = 0.0

    bp_top_pri = "-"
    bp_top_cnt = 0
    bp_total = 0

    # --- Graph 1: Pareto Chart of Breach Reasons
    if "breach_reason" in df_filtered.columns:
        # Use only breached rows when computing Pareto
        if "sla_met" in df_filtered.columns:
            mask = pd.to_numeric(df_filtered["sla_met"], errors="coerce").eq(0)
            data_for_pareto = df_filtered.loc[mask]
        else:
            data_for_pareto = df_filtered

        breach_summary = data_for_pareto["breach_reason"].value_counts(dropna=True).reset_index()
        breach_summary.columns = ["reason", "count"]
        if not breach_summary.empty:
            breach_summary["cum_pct"] = breach_summary["count"].cumsum() / breach_summary["count"].sum() * 100
            top_reason = str(breach_summary.iloc[0]["reason"])
            top_reason_count = int(breach_summary.iloc[0]["count"])
            top3_share_pct = float(breach_summary["count"].iloc[:3].sum() / breach_summary["count"].sum() * 100)

            fig = px.bar(breach_summary, x="reason", y="count", title="Pareto Analysis – Breach Reasons")
            fig.add_scatter(x=breach_summary["reason"], y=breach_summary["cum_pct"], mode="lines+markers", name="Cumulative %")
            st.plotly_chart(fig, use_container_width=True)

    # --- Graph 2: Breaches by Priority (aligned to P1,P2,P3,P5,Service Request)
    if "priority" in df_filtered.columns and "sla_met" in df_filtered.columns:
        dfb = df_filtered.copy()
        dfb["priority_std"] = normalize_priority(dfb["priority"])
        sla_num = pd.to_numeric(dfb["sla_met"], errors="coerce")

        breach_priority = (dfb[sla_num.eq(0)]
                            .groupby("priority_std", observed=True)
                            .size()
                            .reindex(PRIORITY_ORDER, fill_value=0)
                            .reset_index(name="count"))

        fig = px.bar(
            breach_priority,
            x="priority_std",
            y="count",
            title="Breaches by Priority",
            labels={"priority_std": "Priority", "count": "Breached Tickets"},
            category_orders={"priority_std": PRIORITY_ORDER},
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("### Analysis – Breaches by Priority")
        if breach_priority["count"].sum() > 0:
            idxmax = breach_priority["count"].idxmax()
            idxmin = breach_priority["count"].idxmin()
            bp_top_pri = str(breach_priority.loc[idxmax, "priority_std"])
            bp_top_cnt = int(breach_priority.loc[idxmax, "count"])
            bot_pri = str(breach_priority.loc[idxmin, "priority_std"])
            bot_cnt = int(breach_priority.loc[idxmin, "count"])
            total_cnt = int(breach_priority["count"].sum())
            bp_total = total_cnt  # keep for downstream usage if needed

    return df_filtered
