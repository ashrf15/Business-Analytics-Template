# utils_service_availability/recommendation_service_availability/planned_maintenance.py
import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np

# ============================================================
# Mesiniaga visual theme
# ============================================================
MES_BLUE = ["#004C99", "#007ACC", "#3399FF", "#66B2FF", "#9BD1FF"]
px.defaults.template = "plotly_white"

# ============================================================
# Helper for CIO tables (safe .get())
# ============================================================
def render_cio_tables(title, cio_data):
    st.subheader(title)

    with st.expander(" Cost Reduction"):
        st.markdown(
            (cio_data.get("cost", "_No cost recommendations._") or "_No cost recommendations._").lstrip(),
            unsafe_allow_html=True,
        )

    with st.expander(" Performance Improvement"):
        st.markdown(
            (cio_data.get("performance", "_No performance recommendations._") or "_No performance recommendations._").lstrip(),
            unsafe_allow_html=True,
        )

    with st.expander(" Customer Satisfaction Improvement"):
        st.markdown(
            (cio_data.get("satisfaction", "_No satisfaction recommendations._") or "_No satisfaction recommendations._").lstrip(),
            unsafe_allow_html=True,
        )


# ============================================================
# Target 6 – Planned Maintenance and Downtime
# ============================================================
def planned_maintenance(df: pd.DataFrame):

    # ========================================================
    # Subtarget 6a – Scheduled Maintenance Activities
    # ========================================================
    with st.expander("📌 Scheduled Maintenance Activities"):
        need = ["report_date", "service_name", "maintenance_type"]
        missing_cols = set(need) - set(df.columns)

        # 🔴 If required columns are missing → show warning only, NO CIO table
        if missing_cols:
            st.warning(f"⚠️ Missing required columns: {missing_cols}")
        else:
            df = df.copy()
            df["report_date"] = pd.to_datetime(df["report_date"], errors="coerce")

            # 🔴 If all dates invalid → info only, NO CIO table
            if df["report_date"].isna().all():
                st.info("ℹ️ All values in 'report_date' are invalid or empty. No monthly cadence can be derived.")
            else:
                df["month"] = df["report_date"].dt.to_period("M").astype(str)

                # Filter scheduled maintenance
                scheduled = df[df["maintenance_type"].astype(str).str.lower() == "scheduled"].copy()

                # 🔴 If no scheduled rows → info only, NO CIO table
                if scheduled.empty:
                    st.info("ℹ️ No rows with maintenance_type == 'scheduled'. Nothing to display for this subsection.")
                else:
                    # Optional cost/min computation for data-backed formulas
                    has_cost_cols = {"estimated_cost_downtime", "downtime_minutes"}.issubset(scheduled.columns)
                    avg_cost_per_min = None
                    total_sched_cost = None
                    total_sched_mins = None
                    if has_cost_cols:
                        total_sched_cost = pd.to_numeric(scheduled["estimated_cost_downtime"], errors="coerce").sum()
                        total_sched_mins = pd.to_numeric(scheduled["downtime_minutes"], errors="coerce").sum()
                        if total_sched_mins and total_sched_mins > 0:
                            avg_cost_per_min = total_sched_cost / total_sched_mins

                    # --- Graph 1: Number of Scheduled Maintenance per Month
                    monthly_sched = scheduled.groupby("month").size().reset_index(name="maintenance_count")

                    # 🔴 If nothing after grouping → info only, NO CIO table
                    if monthly_sched.empty:
                        st.info("ℹ️ After grouping by month, there are no scheduled activities to plot.")
                    else:
                        fig1 = px.bar(
                            monthly_sched,
                            x="month",
                            y="maintenance_count",
                            text_auto=True,
                            title="Monthly Scheduled Maintenance Activities",
                            labels={"month": "Month", "maintenance_count": "Count of Activities"},
                            color_discrete_sequence=MES_BLUE,
                            template="plotly_white",
                        )
                        st.plotly_chart(fig1, use_container_width=True)

                        # --- Dynamic Analysis
                        max_m = monthly_sched.loc[monthly_sched["maintenance_count"].idxmax()]
                        min_m = monthly_sched.loc[monthly_sched["maintenance_count"].idxmin()]
                        avg_m = monthly_sched["maintenance_count"].mean()

                        st.markdown("### Analysis – Scheduled Maintenance Activities")
                        st.write(
f"""**What this graph is:** A **monthly bar chart** showing **how many scheduled maintenance activities** were executed.  
- **X-axis:** Calendar month.  
- **Y-axis:** Count of scheduled maintenance events.

**What it shows in your data:**  
- **Peak month:** **{max_m['month']}** with **{int(max_m['maintenance_count'])}** activities.  
- **Lowest month:** **{min_m['month']}** with **{int(min_m['maintenance_count'])}** activities.  
- **Average cadence:** **{avg_m:.1f}** activities/month.

**How to read it operationally:**  
1) **Peaks:** Combine small patches and move non-urgent work to off-peak to avoid repeat user disruption.  
2) **Plateaus:** If consistently high, time-box activities and add pre-checks to prevent overrun.  
3) **Downswings:** Confirm whether work was truly not needed or merely deferred (which can create risk later).  
4) **Mix:** Align cadence with incident spikes so maintenance pre-empts fault-prone periods.

**Why this matters:** A right-sized, predictable cadence reduces **unplanned incidents** and **business-hour disruption**, improving cost control and user experience."""
                        )

                        # --- CIO Table (only when data exists)
                        cost_min_snip = f" (Avg RM/min ≈ RM {avg_cost_per_min:,.2f})" if avg_cost_per_min else ""
                        sched_total_snip = ""
                        if avg_cost_per_min is not None and total_sched_cost is not None and total_sched_mins is not None:
                            sched_total_snip = (
                                f" Scheduled maintenance totals: **minutes={int(total_sched_mins):,}**, "
                                f"**cost=RM {total_sched_cost:,.0f}**; Avg **RM/min≈RM {avg_cost_per_min:,.2f}**."
                            )

                        cio_a = {
                            "cost": f"""
| Recommendation | Explanation (Phased for Non-Analytic Users) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Shift activity to off-peak windows | **Phase 1:** Identify low-demand hours/months.<br>**Phase 2:** Reschedule to off-peak.<br>**Phase 3:** Track user impact. | Cuts disruption during revenue hours; lowers lost productivity and escalations; aligns work with low-demand periods. | **RM saved = moved_minutes × RM/min**{cost_min_snip} | Peak in **{max_m['month']}** signals heavy activity where timing matters.{sched_total_snip} |
| Consolidate minor patches | **Phase 1:** Bundle small changes.<br>**Phase 2:** Single validation cycle.<br>**Phase 3:** Standardize runbook. | Fewer windows and less fixed overhead; reduces coordination time; lowers overlap risk with other changes. | **Minutes saved = setup_mins × (events_merged−1)**; **RM = minutes × RM/min**{cost_min_snip} | High monthly counts imply fragmentation overhead. |
| Pre-flight validation checklists | **Phase 1:** Enforce dependency/backup checks.<br>**Phase 2:** Gate go-live on pass.<br>**Phase 3:** Audit overruns. | Prevents rework and rollbacks; shortens windows; improves first-pass success rate. | **RM saved = overrun_minutes_reduced × RM/min**{cost_min_snip} | Peaks correlate with higher overrun probability. |
| Right-size crew to cadence | **Phase 1:** Map workload vs month.<br>**Phase 2:** Flex staffing for peaks.<br>**Phase 3:** Review utilization. | Avoids overtime at peaks and idle time at troughs; smoother utilization; steadier delivery. | **Net RM = overtime_avoided − idle_cost** | Spread between **{int(max_m['maintenance_count'])}** and **{int(min_m['maintenance_count'])}** shows mismatch risk. |
| Quarterly cadence review | **Phase 1:** Compare cadence vs incident/cost trends.<br>**Phase 2:** Adjust schedule density.<br>**Phase 3:** Publish calendar. | Keeps spend proportional to risk; reduces reactive work; better stakeholder planning. | **Benefit = incidents_prevented × cost/incident** | Trend framing improves risk-based planning. |
""",
                            "performance": """
| Recommendation | Explanation (Phased for Non-Analytic Users) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Predictive maintenance triggers | **Phase 1:** Mine alerts for patterns.<br>**Phase 2:** Pre-emptive tasks.<br>**Phase 3:** Tune thresholds. | Fewer unplanned outages; earlier intervention; stabilized performance under load. | **Incidents_prevented × avg_downtime_min** | Regular cadence enables earlier intervention. |
| Time-boxed maintenance SLOs | **Phase 1:** Set max duration per activity.<br>**Phase 2:** Alert breaches.<br>**Phase 3:** Post-mortem. | Reduces variance and overrun; improves schedule reliability; faster recovery to steady state. | **Minutes saved = (baseline−target) × events** | Month-to-month variability indicates scope creep. |
| Parallelize non-conflicting steps | **Phase 1:** Map dependencies.<br>**Phase 2:** Safe parallel runs.<br>**Phase 3:** Validate outcomes. | Shorter windows, higher throughput; faster time-to-complete without added risk. | **Window_reduction_min × RM/min** | High counts suggest parallelization opportunity. |
| Automate recurring tasks | **Phase 1:** Script backups/health checks.<br>**Phase 2:** Auto-validate.<br>**Phase 3:** Log execution. | Faster, consistent execution; fewer human errors; lower MTTR contributions. | **Time saved per task × task volume** | Repeated activities benefit most from automation. |
| Owner scorecards | **Phase 1:** Publish overrun by owner.<br>**Phase 2:** Coach outliers.<br>**Phase 3:** Recognize gains. | Predictable delivery speeds; accountability-led improvements; institutional knowledge growth. | **ΔOverrun_min × RM/min** | Variability highlights process gaps to coach. |
""",
                            "satisfaction": f"""
| Recommendation | Explanation (Phased for Non-Analytic Users) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Publish monthly maintenance calendar | **Phase 1:** Announce dates early.<br>**Phase 2:** Reminders 48h/2h.<br>**Phase 3:** Closure notes. | Fewer surprises and escalations; better stakeholder coordination; higher perceived reliability. | **Complaints_avoided × handling_cost** | Activity spikes (e.g., **{max_m['month']}**) need stronger comms. |
| User-preferred windows | **Phase 1:** Survey preferred times.<br>**Phase 2:** Pilot windows.<br>**Phase 3:** Rollout. | Higher perceived reliability; reduced disruption during critical hours; improved CSAT. | **CSAT uplift vs baseline** | Aligning windows improves perception. |
| Impact labelling (high/low) | **Phase 1:** Tag expected impact.<br>**Phase 2:** Offer workarounds for high-impact.<br>**Phase 3:** Track results. | Protects productivity during work; better user planning; fewer urgent escalations. | **Deflected_minutes × user_value** | Clear labelling reduces disruption cost. |
| Live status page during windows | **Phase 1:** Expose ETA/milestones.<br>**Phase 2:** Update progress.<br>**Phase 3:** Archive history. | Reduces inbound queries; transparent progress; faster reassurance. | **Ticket_deflection × handling_cost** | Users self-serve updates during busy months. |
| Post-window feedback loop | **Phase 1:** Quick survey.<br>**Phase 2:** Fix pain points.<br>**Phase 3:** Publish changes. | Builds trust & engagement; continuous UX improvements; better adoption of schedules. | **Retention/CSAT gain** | Repeated months show where UX focus helps. |
"""
                        }

                        # ✅ Only here, where data exists, we show CIO tables
                        render_cio_tables("CIO – Scheduled Maintenance Activities", cio_a)

    # ========================================================
    # Subtarget 6b – Downtime Windows for Maintenance
    # ========================================================
    with st.expander("📌 Downtime Windows for Maintenance"):
        need2 = ["service_name", "maintenance_type", "downtime_minutes", "estimated_cost_downtime"]
        missing2 = set(need2) - set(df.columns)

        # 🔴 If required columns missing → warning only, NO CIO
        if missing2:
            st.warning(f"⚠️ Missing required columns: {missing2}")
        else:
            planned = df[df["maintenance_type"].astype(str).str.lower() == "scheduled"].copy()

            # 🔴 No scheduled rows → info only, NO CIO
            if planned.empty:
                st.info("ℹ️ No rows with maintenance_type == 'scheduled'. Cannot compute planned downtime by service.")
            else:
                # Clean numeric for safe math
                planned["downtime_minutes"] = pd.to_numeric(planned["downtime_minutes"], errors="coerce")
                planned["estimated_cost_downtime"] = pd.to_numeric(planned["estimated_cost_downtime"], errors="coerce")

                downtime_summary = (
                    planned.groupby("service_name", as_index=False)
                    .agg(
                        downtime_minutes=("downtime_minutes", "sum"),
                        estimated_cost_downtime=("estimated_cost_downtime", "sum"),
                    )
                    .sort_values("downtime_minutes", ascending=False)
                )

                # 🔴 If grouping yields nothing → info only, NO CIO
                if downtime_summary.empty:
                    st.info("ℹ️ After grouping, no valid numeric downtime rows remained to plot.")
                else:
                    # --- Graph 1: Total Planned Downtime per Service
                    fig2 = px.bar(
                        downtime_summary,
                        x="service_name",
                        y="downtime_minutes",
                        text_auto=True,
                        title="Planned Downtime Duration by Service",
                        labels={"service_name": "Service", "downtime_minutes": "Total Downtime (minutes)"},
                        color_discrete_sequence=MES_BLUE,
                        template="plotly_white",
                    )
                    st.plotly_chart(fig2, use_container_width=True)

                    # --- Dynamic Analysis
                    peak = downtime_summary.iloc[0]
                    low = downtime_summary.iloc[-1]
                    total_downtime = int(downtime_summary["downtime_minutes"].sum())
                    total_cost = float(downtime_summary["estimated_cost_downtime"].sum())
                    avg_rm_per_min = (total_cost / total_downtime) if total_downtime > 0 else np.nan

                    st.markdown("### Analysis – Downtime Windows for Maintenance")
                    st.write(
f"""**What this graph is:** A **bar chart** of **total planned downtime (minutes)** per **service** caused by scheduled maintenance.  
- **X-axis:** Service name.  
- **Y-axis:** Total minutes of planned downtime across the period.

**What it shows in your data:**  
- **Highest downtime service:** **{peak['service_name']}** with **{int(peak['downtime_minutes'])}** minutes.  
- **Lowest downtime service:** **{low['service_name']}** with **{int(low['downtime_minutes'])}** minutes.  
- **Portfolio totals:** **{total_downtime:,}** minutes planned; **RM {total_cost:,.0f}** cost recorded; **Avg RM/min ≈ {avg_rm_per_min:,.2f}**.

**How to read it operationally:**  
1) **Head services:** Compress the longest windows first (task sequencing, parallel steps, hot/rolling updates).  
2) **Tail services:** Ensure short windows still include pre-/post-checks to avoid quality defects.  
3) **Cost lens:** Re-base high-cost services to off-peak; use **Avg RM/min** to size the impact of each minute reduced.

**Why this matters:** Concentrated downtime on a few services indicates **over-maintenance or inefficient steps**. Tightening these windows cuts cost and keeps users productive."""
                    )

                    # --- CIO Table (only when data exists)
                    cio_b = {
                        "cost": f"""
| Recommendation | Explanation (Phased for Non-Analytic Users) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Shorten the longest window first | **Phase 1:** Decompose **{peak['service_name']}** tasks.<br>**Phase 2:** Remove waits & re-order steps.<br>**Phase 3:** Re-timebox. | Immediate reduction of the largest cost block; less overlap with business time; lower penalty exposure. | **RM saved = minutes_reduced × Avg RM/min ≈ RM {avg_rm_per_min:,.2f}/min** | **{peak['service_name']}** is the tallest bar (**{int(peak['downtime_minutes'])}** min). |
| Hot/rolling updates for head services | **Phase 1:** Add redundancy.<br>**Phase 2:** Rolling restarts.<br>**Phase 3:** Verify zero visible outage. | Converts planned downtime to near-zero user impact; keeps key journeys live; reduces lost productivity. | **Benefit = visible_minutes_avoided × Avg RM/min ≈ RM {avg_rm_per_min:,.2f}/min** | Head concentration shows full-stop patterns. |
| Batch cross-service work | **Phase 1:** Group dependencies in one window.<br>**Phase 2:** Single validation.<br>**Phase 3:** QA after. | Fewer windows and lower fixed setup costs; less fragmented comms; faster overall completion. | **Savings = (#windows_merged−1) × setup_mins × Avg RM/min** | Several services show medium bars suitable for batching. |
| Off-peak rebasing for costly services | **Phase 1:** Map RM/min to calendar.<br>**Phase 2:** Move to off-peak.<br>**Phase 3:** Track delta. | Less overlap with revenue time; lower productivity loss; fewer escalations. | **ΔCost = (Peak−Off-peak) RM/min × window_mins** | Combine downtime bars with cost column totals (**RM {total_cost:,.0f}**). |
| Pre-assembled validation artifacts | **Phase 1:** Prepare scripts/images.<br>**Phase 2:** Pre-run checks.<br>**Phase 3:** Cache artifacts. | Faster windows; fewer human errors; repeatable execution. | **Time saved = validation_mins_saved × events; RM = time × Avg RM/min** | Long windows imply validation drag. |
""",
                        "performance": f"""
| Recommendation | Explanation (Phased for Non-Analytic Users) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Automate maintenance sequencing | **Phase 1:** Script standard sequences.<br>**Phase 2:** Auto-verify checkpoints.<br>**Phase 3:** Log metrics. | Predictable, shorter windows; reduced variance; faster time-to-restore. | **Minutes saved/window × #windows** | Repeated long windows hint at manual steps. |
| Parallelize non-conflicting tasks | **Phase 1:** Identify safe concurrency.<br>**Phase 2:** Execute in parallel.<br>**Phase 3:** Compare outcomes. | Shrinks total downtime per service; improves throughput; minimizes customer-visible impact. | **Window_reduction_min × Avg RM/min ≈ RM {avg_rm_per_min:,.2f}/min** | Gap between head and tail bars shows compression room. |
| Maintenance SLOs with alerts | **Phase 1:** Set max window per tier.<br>**Phase 2:** Alert on breach.<br>**Phase 3:** Post-mortem. | Drives continuous improvement; catches overruns early; enforces discipline. | **ΔWindow_min × events × Avg RM/min** | Outliers reveal SLO breach risk. |
| Canary + instant rollback | **Phase 1:** Deploy to subset.<br>**Phase 2:** Monitor SLOs.<br>**Phase 3:** Rollback on regressions. | Avoids extended bad windows; limits blast radius; protects KPIs. | **Avoided bad_window_min × Avg RM/min** | Long tails suggest risky big-bang changes. |
| Owner-level scorecards | **Phase 1:** Publish duration by owner.<br>**Phase 2:** Coach high outliers.<br>**Phase 3:** Recognize gains. | Culture of precision and speed; institutionalized best practice; sustained improvements. | **ΔDuration × events × Avg RM/min** | Head bars identify owners to coach. |
""",
                        "satisfaction": f"""
| Recommendation | Explanation (Phased for Non-Analytic Users) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Advance notice with ETAs | **Phase 1:** Announce window & ETA per service.<br>**Phase 2:** Live progress updates.<br>**Phase 3:** Closure note & RCA link. | Fewer escalations; clearer expectations; improved trust during change windows. | **Complaints_avoided × handling_cost** | Long windows (e.g., **{peak['service_name']}**) heighten anxiety without updates. |
| Workarounds for head services | **Phase 1:** Publish alternatives for top downtime services.<br>**Phase 2:** Train support.<br>**Phase 3:** Measure deflection. | Keeps users productive; fewer blocked tasks; lower perceived impact. | **Deflected_minutes × user_value** | Users hit hardest by head bars benefit most. |
| Silent maintenance for key journeys | **Phase 1:** Route traffic to standby.<br>**Phase 2:** Update behind scenes.<br>**Phase 3:** Audit visibility. | Improves perceived reliability; reduces visible outages; better CSAT. | **Visible_minutes_avoided × Avg RM/min ≈ RM {avg_rm_per_min:,.2f}/min** | Concentrated downtime harms UX most. |
| Customer co-planning for critical services | **Phase 1:** Agree windows with key accounts.<br>**Phase 2:** Lock calendars.<br>**Phase 3:** Review quarterly. | Shared ownership reduces friction; higher acceptance of windows; stronger relationships. | **Retention/CSAT uplift** vs baseline | High-impact services justify joint planning. |
| After-action summaries | **Phase 1:** Share what changed and why.<br>**Phase 2:** Show before/after metrics.<br>**Phase 3:** Invite feedback. | Builds trust and transparency; educates users; fewer repeat queries. | **CSAT gain** measured post-change | Clear narrative reduces perceived pain. |
"""
                    }

                    # ✅ Only here, where downtime_summary has data, show CIO
                    render_cio_tables("CIO – Downtime Windows for Maintenance", cio_b)
