import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# ───────────────────────────── Visual theme (Mesiniaga blue/white) ─────────────────────────────
px.defaults.template = "plotly_white"
BLUE_TONES = [
    "#004C99",  # deep brand navy
    "#0066CC",  # strong blue
    "#007ACC",  # azure
    "#3399FF",  # light blue
    "#66B2FF",  # lighter blue
    "#99CCFF",  # pale blue
]

# ───────────────────────────── CIO renderer (defensive) ─────────────────────────────
def render_cio_tables(title, cio_data):
    st.subheader(title)
    cost = cio_data.get("cost", "_No cost recommendations provided._")
    perf = cio_data.get("performance", "_No performance recommendations provided._")
    sat  = cio_data.get("satisfaction", "_No customer satisfaction recommendations provided._")

    with st.expander("Cost Reduction"):
        st.markdown(cost, unsafe_allow_html=True)
    with st.expander("Performance Improvement"):
        st.markdown(perf, unsafe_allow_html=True)
    with st.expander("Customer Satisfaction Improvement"):
        st.markdown(sat, unsafe_allow_html=True)

# ───────────────────── Plotly safety: coerce Period -> str ─────────────────────
def _plotly_safe_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure all columns / index are JSON-serializable for Plotly/Streamlit:
      - pandas PeriodDtype -> string (e.g., '2025-01')
      - PeriodIndex       -> string
    """
    out = df.copy()
    if isinstance(out.index, pd.PeriodIndex):
        out.index = out.index.astype(str)
    for c in out.columns:
        try:
            if pd.api.types.is_period_dtype(out[c]):
                out[c] = out[c].astype(str)
        except Exception:
            pass
    return out

# ───────────────────── Robust datetime parser (excel, mixed, etc.) ─────────────────────
def _best_parse_datetime(series, ref_series=None):
    s = series.copy()
    if np.issubdtype(s.dtype, np.datetime64):
        return pd.to_datetime(s, errors="coerce")

    s_num = pd.to_numeric(s, errors="coerce")
    serial_mask = s_num.notna()
    parsed_from_serial = pd.Series(pd.NaT, index=s.index, dtype="datetime64[ns]")
    if serial_mask.any():
        parsed_from_serial.loc[serial_mask] = pd.to_datetime(
            s_num.loc[serial_mask], unit="D", origin="1899-12-30", errors="coerce"
        )

    string_mask = ~serial_mask
    s_str = s.where(string_mask)

    p_dayfirst = pd.to_datetime(s_str, errors="coerce", dayfirst=True,  infer_datetime_format=True)
    p_monthfirst = pd.to_datetime(s_str, errors="coerce", dayfirst=False, infer_datetime_format=True)

    def _score(parsed):
        valid = parsed.notna().sum()
        future = (parsed > (pd.Timestamp.today().normalize() + pd.Timedelta(days=30))).sum()
        near_ref = 0
        if ref_series is not None:
            ref = pd.to_datetime(ref_series, errors="coerce")
            if ref.notna().any():
                ref_min, ref_max = ref.min(), ref.max()
                if pd.notna(ref_min) and pd.notna(ref_max):
                    lo = ref_min - pd.Timedelta(days=180)
                    hi = ref_max + pd.Timedelta(days=180)
                    near_ref = ((parsed >= lo) & (parsed <= hi)).sum()
        return (valid, -future, near_ref)

    p_best_strings = p_dayfirst if _score(p_dayfirst) >= _score(p_monthfirst) else p_monthfirst
    out = parsed_from_serial.copy()
    out.loc[string_mask] = p_best_strings.loc[string_mask]
    return pd.to_datetime(out, errors="coerce")

# ─────────────────────────────────── Main view ───────────────────────────────────
def incident_overview(df_filtered: pd.DataFrame):

    # ─────────────── 1a. Total incidents ───────────────
    with st.expander("📌 Total Number of Incidents Reported"):
        if "created_time" not in df_filtered.columns:
            st.warning("Column 'created_time' is required for this section.")
            return

        df_local = df_filtered.copy()
        df_local["created_time"] = pd.to_datetime(df_local["created_time"], errors="coerce")

        daily = (
            df_local.dropna(subset=["created_time"])
            .groupby(df_local["created_time"].dt.date)
            .size().reset_index(name="count")
            .rename(columns={"created_time": "date"})
        )

        if not daily.empty:
            daily["date_dt"] = pd.to_datetime(daily["date"])
            daily = daily.sort_values("date_dt")
            daily["date_str"] = daily["date_dt"].dt.strftime("%d/%m/%Y")
            fig = px.line(
                _plotly_safe_df(daily),
                x="date_str",
                y="count",
                title="Incidents Created Over Time",
                color_discrete_sequence=BLUE_TONES
            )
            st.plotly_chart(fig, use_container_width=True)

            total_inc   = int(len(df_local))
            avg_per_day = float(daily["count"].mean())
            max_row     = daily.loc[daily["count"].idxmax()]
            min_row     = daily.loc[daily["count"].idxmin()]
            latest_row  = daily.iloc[-1]

            # --- Uniform analysis format
            st.markdown("#### Analysis – Daily Incident Trend")
            st.write(
                f"""What this graph is: A throughput chart showing opened tickets per day.  
X-axis: Calendar date.  
Y-axis: Tickets created per day.  

What it shows in your data:  
Largest intake day: {max_row['date_str']} with {int(max_row['count'])} opened.  
Quietest day: {min_row['date_str']} with {int(min_row['count'])} opened.  
Averages over the period are {avg_per_day:.1f} opened/day; latest day {latest_row['date_str']} logged {int(latest_row['count'])}.  

Overall, when daily points trend upward persistently, demand is outpacing prevention; when they flatten or fall, intake is stabilizing.  
How to read it operationally:  
Gap vs baseline: The vertical distance between a spike and the average ({avg_per_day:.1f}) estimates extra same-day load.  
Lead–lag: Spikes shortly after change windows imply change-driven incidents rather than organic demand.  
Recovery strength: Faster return to the average after a spike signals healthier prevention and triage.  
Control: Use control limits (μ±2σ) to trigger surge staffing and deflection.  
Why this matters: Intake stability is the heartbeat of the desk; keeping openings near controllable ranges prevents aging, protects SLA, and steadies user experience."""
            )
        else:
            total_inc = 0
            avg_per_day = 0.0
            max_row = {"date_str": "-", "count": 0}
            min_row = {"date_str": "-", "count": 0}
            latest_row = {"date_str": "-", "count": 0}
            st.info("No daily incident rows to display for the selected period.")

        # Pareto by category
        if "category" in df_local.columns and not df_local.empty:
            cat_summary = (
                df_local.groupby("category")
                .size()
                .reset_index(name="count")
                .sort_values("count", ascending=False)
            )

            if not cat_summary.empty:
                cat_summary["cum_pct"] = cat_summary["count"].cumsum() / cat_summary["count"].sum() * 100
                fig_pareto = px.bar(
                    _plotly_safe_df(cat_summary),
                    x="category",
                    y="count",
                    title="Pareto Analysis – Incidents by Category",
                    labels={"count": "Incident count", "category": "Category"},
                    color_discrete_sequence=BLUE_TONES
                )
                st.plotly_chart(fig_pareto, use_container_width=True)

                top_cat_row   = cat_summary.iloc[0]
                top_cat       = str(top_cat_row["category"])
                top_cat_count = int(top_cat_row["count"])
                top_share_pct = (top_cat_count / max(total_inc, 1)) * 100
                top3_count    = int(cat_summary["count"].iloc[:3].sum()) if len(cat_summary) >= 3 else int(cat_summary["count"].sum())
                top3_share_pct= (top3_count / max(total_inc, 1)) * 100

                # --- Uniform analysis format for Pareto
                st.markdown("#### Analysis – Category Pareto")
                st.write(
                    f"""What this graph is: A Pareto chart showing incident volume by category (bars) with cumulative contribution.  
X-axis: Category.  
Y-axis: Incident count (bars).  

What it shows in your data:  
Largest category: {top_cat} with {top_cat_count} incidents ({top_share_pct:.1f}% of {total_inc} total).  
Top-3 categories together contribute {top3_share_pct:.1f}% of all incidents.  

Overall, the steep front confirms a small set of categories generates most workload.  
How to read it operationally:  
Focus: Attack the top 1–3 categories first (runbooks, guided intake, automation).  
Standardize: Lock in fixes and monitor for drift once volumes fall.  
Decompose: Split the top category into subtypes to find automatable slices.  
Align: Map categories to teams/SLA tiers so the right skills handle the right work.  
Why this matters: Optimizing where volume concentrates yields the largest cost, performance, and CSAT gains fastest."""
                )

                # --- CIO tables (≥3 recommendations; phased explanations; real values in calc/evidence)
                cio = {
    "cost": f"""
| Recommendations | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Automate intake for repetitive top categories | **Phase 1 – Identify:** In this phase, we analyze the category Pareto and confirm that the top three categories account for **{top3_share_pct:.1f}%** of the total **{total_inc}** incidents. We document the exact request patterns and error codes that repeat most frequently. <br><br> **Phase 2 – Design:** We design structured intake forms with clear field validation and auto-classification rules so that repetitive details are captured the first time. We also define routing rules and exception paths. <br><br> **Phase 3 – Deploy:** We deploy auto-creation and auto-routing for the targeted categories with audit trails, and we monitor deflection and error rates to iterate safely. | - Reduces manual triage time on the majority of tickets by eliminating repeated data collection and classification steps. <br><br> - Lowers peak-day overtime by smoothing the intake workload so analysts can focus on higher-value cases. <br><br> - Stabilizes unit cost per incident because standardized intake reduces rework and misroutes. | **Hours saved** = reduction% × (avg_handling_min/60) × total_tickets. Example: 0.15 × 10/60 × **{total_inc}** = **{0.15*10/60*total_inc:.2f} h**. | Daily intake shows peaks (e.g., **{max_row['date_str']}** with **{int(max_row['count'])}**). Pareto concentration (top-3 **{top3_share_pct:.1f}%**) validates automation ROI. |
| Standardize recurring fixes in **{top_cat}** | **Phase 1 – Capture:** We mine historical resolutions inside **{top_cat}** and convert the most common fixes into step-by-step runbooks and short knowledge articles. <br><br> **Phase 2 – Embed:** We embed those runbooks directly into the agent console with checklists and pre-filled fields to make the happy path the default. <br><br> **Phase 3 – Improve:** We A/B test article clarity, searchability, and resolution rates, and we retire obsolete steps as the environment changes. | - Improves first-time-fix for the largest volume slice by ensuring analysts follow proven steps consistently. <br><br> - Reduces escalations because clear runbooks cut ambiguity and handoffs. <br><br> - Lowers average handling time as duplicated effort and rework are removed. | **Hours saved** = (Δmins_per_ticket/60) × **{top_cat_count}**. | Top category **{top_cat}** has **{top_cat_count}** tickets (**{top_share_pct:.1f}%** of total **{total_inc}**). |
| Batch-process low-priority repeats | **Phase 1 – Cluster:** We group similar low-effort incidents by signature (e.g., same error code) so they can be solved together. <br><br> **Phase 2 – Execute:** We schedule daily or bi-daily batch windows where an analyst clears the entire cluster with minimal context switching. <br><br> **Phase 3 – Measure:** We compare time per ticket in batched mode versus ad-hoc mode and keep the batch size that gives the best throughput. | - Raises throughput without adding headcount by cutting context switching and setup time. <br><br> - Reduces day-to-day variance so teams are less whiplashed by spikes. <br><br> - Lowers burnout because repetitive tasks are handled in predictable windows. | **Hours saved** = (mins_saved_per_batched_ticket/60) × batch_volume. Batch_volume proxy: spike **{int(max_row['count'])}** vs avg **{avg_per_day:.1f}**. | Intake spikes (e.g., **{max_row['date_str']}**) indicate windows where batching stabilizes load. |
| Streamline overlapping categories | **Phase 1 – Audit:** We review the long tail and identify synonyms, duplicates, and rarely used categories that confuse routing and analytics. <br><br> **Phase 2 – Merge:** We consolidate the taxonomy into a canonical list and update forms, routing rules, and dashboards accordingly. <br><br> **Phase 3 – Retrain:** We retrain classification models and agents so the new list is consistently applied. | - Cuts misroutes and duplicate tickets because agents and users see a clearer category list. <br><br> - Reduces triage rework by eliminating ambiguous labels that cause back-and-forth. <br><br> - Improves reporting accuracy which enables better planning and staffing. | **Hours saved** = duplicates_avoided × (triage_min/60). | Long-tail shape in Pareto implies fragmentation and misclassification risk. |
| Demand-aligned staffing | **Phase 1 – Forecast:** We model staffing against the baseline of **{avg_per_day:.1f}** opened per day and the observed peak of **{int(max_row['count'])}** so we know the true capacity requirements. <br><br> **Phase 2 – Flex:** We implement surge shifts or on-call coverage on predicted peak days and reduce coverage on troughs. <br><br> **Phase 3 – Review:** We hold a weekly variance review to tune rosters as patterns evolve. | - Lowers overtime on peak days by aligning capacity to forecasted demand. <br><br> - Reduces idle time on quiet days which smooths cost per incident. <br><br> - Stabilizes performance because the team is neither understaffed nor overstaffed. | **OT avoided (h)** ≈ max(0, **{int(max_row['count'])}** − planned_intake) × hrs/ticket. | The gap between peak and baseline is visible in the daily series, driving OT exposure. |
""",
    "performance": f"""
| Recommendations | Explanation | Benefits | Cost Calculation | Evidence |
|---|---|---|---|---|
| Surge alerts on μ±2σ | **Phase 1 – Compute:** We calculate the rolling mean and standard deviation of daily openings (μ ≈ **{avg_per_day:.1f}**) to define control limits. <br><br> **Phase 2 – Alert:** We trigger alerts when counts exceed those limits so leaders can intervene early. <br><br> **Phase 3 – Respond:** We pre-define actions such as auto-triage, deflection messages, or swarm assignments. | - Shortens time to respond when demand spikes so queues do not snowball. <br><br> - Reduces SLA breaches by containing surges before they create aging. <br><br> - Produces smoother cycle time because throughput actions kick in predictably. | **Hours saved** = (spike_openings − **{avg_per_day:.1f}**) × hrs/ticket on alert days. | Daily spikes (e.g., **{max_row['date_str']}**) above average **{avg_per_day:.1f}**. |
| Skill-based routing by category | **Phase 1 – Map:** We link the top-3 categories to resolver pools with proven expertise to minimize handoffs. <br><br> **Phase 2 – Route:** We auto-assign new tickets in those categories to the right pool on first touch. <br><br> **Phase 3 – Audit:** We monitor reassignment and rework rates and refine routing rules. | - Lowers handoffs which reduces delays and errors. <br><br> - Decreases mean time to resolve because experts handle issues from the start. <br><br> - Improves throughput in the categories that drive most volume. | **Hours saved** = (reassignments_avoided × mins_reassign/60) + (Δresolution_hours × **{top3_count}**). | Pareto: top-3 share **{top3_share_pct:.1f}%** of workload. |
| Predictive staffing using seasonality | **Phase 1 – Model:** We quantify day-of-week and month effects to forecast peaks and troughs. <br><br> **Phase 2 – Schedule:** We align shift start times and team sizes to the predicted pattern so coverage matches expected inflow. <br><br> **Phase 3 – Calibrate:** We back-test monthly and update schedules when drift appears. | - Makes capacity proactive instead of reactive which reduces firefighting. <br><br> - Cuts last-minute escalations because staffing is right-sized for the day’s profile. <br><br> - Keeps output stable even when demand is uneven. | **OT avoided (h)** = Σ(max(0, forecast_open − planned_close)) × hrs/ticket. | Repeating high days relative to average **{avg_per_day:.1f}** indicate seasonal swings. |
| Cross-train to reduce bottlenecks | **Phase 1 – Select:** We choose agents to upskill on **{top_cat}** and the remaining top categories based on current bottlenecks. <br><br> **Phase 2 – Train:** We deliver focused training with KB practice and short shadowing rotations. <br><br> **Phase 3 – Rotate:** We rotate work to maintain proficiency and avoid single-thread risk. | - Removes dependency on a few specialists so queues do not stall when they are busy. <br><br> - Increases peak-handling capacity because more people can handle hot categories. <br><br> - Improves resilience when absence or turnover occurs. | **Hours saved** = (handoff_drop × mins_handoff/60) × volume_in_top3. | Concentration shows risk of expertise bottlenecks. |
| Category-focused backlog burn-down | **Phase 1 – Queue:** We prioritize the oldest items within the top-3 categories so work hits the biggest impact areas first. <br><br> **Phase 2 – Sprint:** We run short, time-boxed burn-downs with a clear owner and daily target. <br><br> **Phase 3 – Verify:** We measure backlog slope and keep what works. | - Reduces aging where it matters most which lifts on-time performance quickly. <br><br> - Converts effort into visible progress that stakeholders can track. <br><br> - Creates repeatable playbooks for future spikes. | **Hours released** = sprint_closures × hrs/ticket (volume focus: **{top3_count}**). | Top-3 account for **{top3_share_pct:.1f}%** of inflow; focusing accelerates impact. |
""",
    "satisfaction": f"""
| Recommendations | Explanation | Benefits | Cost Calculation | Evidence |
|---|---|---|---|---|
| Auto-ack + next steps on creation | **Phase 1 – Template:** We send an instant acknowledgement with next steps and required information as soon as an incident is logged. <br><br> **Phase 2 – Personalize:** We tailor the message by category, emphasizing **{top_cat}** where many users are affected. <br><br> **Phase 3 – Track:** We track follow-up contacts and iterate templates to reduce confusion. | - Reduces duplicate contacts because users know what happens next and what they can do immediately. <br><br> - Improves perceived responsiveness, especially during peak days when agents are busy. <br><br> - Increases data completeness which speeds up resolution. | **Hours saved** = contacts_deflected × (followup_min/60). | Peak exposure on **{max_row['date_str']}**; top-3 affect most users (**{top3_share_pct:.1f}%**). |
| Self-service status dashboards | **Phase 1 – Publish:** We provide live status by category with simple ETAs and current known issues. <br><br> **Phase 2 – Notify:** We push delay notifications when SLAs slip so users are not left guessing. <br><br> **Phase 3 – Survey:** We measure CSAT shifts and refine content and timing. | - Cuts inbound “any update?” inquiries because answers are visible without opening a ticket. <br><br> - Builds trust through transparency so dissatisfaction does not compound during delays. <br><br> - Helps agents focus on solving rather than answering status questions. | **Hours saved** = inquiries_deflected × (handling_min/60). | Pareto shows where most users are affected; daily chart shows when. |
| Fast-lane for high-impact categories | **Phase 1 – Define:** We mark the critical categories inside the top-3 and agree on stricter SLAs and escalation paths. <br><br> **Phase 2 – Route:** We route those incidents to a senior owner with clear triage windows. <br><br> **Phase 3 – Validate:** We track breach deltas and adjust thresholds. | - Protects key business processes and high-value users by shortening their wait time. <br><br> - Reduces escalations because problems are seen and handled faster. <br><br> - Improves sentiment among stakeholders who experience fewer high-impact delays. | **Penalty avoided** = breaches_prevented × penalty_per_breach. | Risk concentrates in top-3 (**{top3_share_pct:.1f}%**). |
| Proactive “peak-day” comms | **Phase 1 – Trigger:** We automatically message when the count exceeds μ (**{avg_per_day:.1f}**) so expectations are set early. <br><br> **Phase 2 – Channel:** We inform users via email, portal banners, or SMS with clear ETAs and alternatives. <br><br> **Phase 3 – Learn:** We track complaint rates and refine timing and tone. | - Prevents frustration by acknowledging delays before users have to ask. <br><br> - Reduces complaint volume because people understand what to expect and when. <br><br> - Maintains trust during overload by showing active management. | **Hours saved** = complaints_avoided × (complaint_handling_min/60). | Peak **{int(max_row['count'])}** vs baseline **{avg_per_day:.1f}** quantifies audience. |
| Targeted feedback on **{top_cat}** | **Phase 1 – Survey:** We run short, focused surveys in **{top_cat}** to find friction points in the user journey. <br><br> **Phase 2 – Fix:** We update runbooks, forms, or communications to address the top issues. <br><br> **Phase 3 – Re-check:** We re-survey after changes to confirm that satisfaction has improved. | - Produces quick, visible CX wins where the most users are affected. <br><br> - Reduces follow-up contacts because issues are addressed at the source. <br><br> - Creates a measurable feedback loop that sustains quality. | **Hours saved** = followups_reduced × (handling_min/60) on **{top_cat_count}** cases. | **{top_cat}** dominates volume (**{top_share_pct:.1f}%**). |
"""
}

                render_cio_tables("Total Incidents", cio)
            else:
                st.info("No category distribution available after filtering.")
        else:
            st.info("Column 'category' not found or dataset is empty—Pareto analysis skipped.")

    # ─────────────── 1b. Incidents Resolved ───────────────
    with st.expander("📌 Incidents Resolved"):
        if "completed_time" in df_filtered.columns:

            ref_col = df_filtered["created_time"] if "created_time" in df_filtered.columns else None
            df_filtered["_completed_time_parsed"] = _best_parse_datetime(df_filtered["completed_time"], ref_series=ref_col)

            df_resolved = df_filtered.dropna(subset=["_completed_time_parsed"]).copy()
            if df_resolved.empty:
                st.info("No resolved incidents found in the uploaded data.")
            else:
                df_resolved["resolved_date"] = df_resolved["_completed_time_parsed"].dt.floor("D")
                closed = (
                    df_resolved.groupby("resolved_date")
                    .size()
                    .reset_index(name="closed")
                    .sort_values("resolved_date")
                )

                fig = px.bar(
                    _plotly_safe_df(closed),
                    x="resolved_date",
                    y="closed",
                    title="Daily Resolved Incidents",
                    labels={"resolved_date": "Resolved Date", "closed": "Incidents Closed"},
                    color_discrete_sequence=BLUE_TONES
                )
                st.plotly_chart(fig, use_container_width=True)

                total_res = int(closed["closed"].sum()) if not closed.empty else 0
                avg_res   = float(closed["closed"].mean()) if not closed.empty else 0

                st.markdown("### Analysis – Resolution Trends")
                if not closed.empty:
                    mx = closed.loc[closed["closed"].idxmax()]
                    mn = closed.loc[closed["closed"].idxmin()]
                    best_day  = pd.to_datetime(mx["resolved_date"]).strftime("%d/%m/%Y")
                    worst_day = pd.to_datetime(mn["resolved_date"]).strftime("%d/%m/%Y")

                    # --- Uniform analysis format
                    st.write(f"""What this graph is: A bar chart showing daily incident closures based on actual resolved dates.  
X-axis: Resolved date.  
Y-axis: Number of incidents closed per day.  

What it shows in your data:  
Total closures: {total_res} with a daily average of {avg_res:.1f}.  
Largest closure day: {best_day} with {int(mx['closed'])} closed.  
Smallest closure day: {worst_day} with {int(mn['closed'])} closed.  

Overall, bursts indicate backlog burn; troughs suggest capacity gaps or blockers.  
How to read it operationally:  
Peaks: Capture what enabled high throughput (staff mix, batching, runbooks).  
Plateaus: Standardize best-performing playbooks to hold steady output.  
Downswings: Remove bottlenecks (handoffs, approvals, parts).  
Mix: Compare with openings to assess backlog pressure.  
Why this matters: Stable closure flow reduces aging and SLA risk, improving predictability and user confidence.""")

                    # CIO with ≥3 recs; phased explanations; real values used
                    cio = {
    "cost": f"""
| Recommendations | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Standardize and automate closure workflows | **Phase 1 – Map:** We document every step from “work in progress” to “resolved,” including status transitions, mandatory fields, and documentation attachments, so the closure path is explicit and repeatable. <br><br> **Phase 2 – Automate:** We implement templates, pre-filled fields, and auto-transitions for common paths so agents complete administrative tasks with minimal clicks and fewer mistakes. <br><br> **Phase 3 – Assure:** We run monthly quality checks and review exceptions so the workflow stays lean and correct as volumes and categories evolve. | - Lowers cost per incident by removing repetitive closure admin and reducing rework loops. <br><br> - Increases consistency across agents which improves data quality and downstream reporting. <br><br> - Stabilizes daily output on historically low days because closure friction is removed. | **Savings (h)** = (mins_saved_per_ticket ÷ 60) × total_closed = (e.g., 5/60) × **{total_res}** = **{(5/60)*total_res:.2f} h**. | Peak closure day **{best_day}** hit **{int(mx['closed'])}**, trough **{worst_day}** had **{int(mn['closed'])}**—automation narrows this gap. |
| Structured batching for low-complexity incidents | **Phase 1 – Identify:** We label repetitive, low-effort incident types that do not need deep investigation so they can be cleared together with the same steps. <br><br> **Phase 2 – Schedule:** We create daily or bi-daily batch windows where a dedicated agent clears an entire cluster in one focused session to reduce context switching. <br><br> **Phase 3 – Compare:** We measure time per ticket for batched work versus ad-hoc and lock in the batch size and cadence that deliver the best throughput. | - Raises throughput with the current team by cutting setup and switching overhead between similar tasks. <br><br> - Reduces performance variance so output is more predictable across the week. <br><br> - Lowers fatigue because repetitive work is contained within short, efficient windows. | **Time saved (h)** = (mins_saved_per_batched_ticket ÷ 60) × batched_volume (use high-volume days like **{best_day}**). | Surges (e.g., **{best_day}**) imply ad-hoc batching; formalizing stabilizes output near avg **{avg_res:.1f}**. |
| Align staffing to high-output days | **Phase 1 – Forecast:** We analyze weekday and month patterns to predict when closures are easiest to achieve and when more hands are required. <br><br> **Phase 2 – Roster:** We align shift start times and headcount with the predicted high-closure windows so easy tickets are not left in the queue. <br><br> **Phase 3 – Recalibrate:** We review variance weekly and adjust rosters as data drifts so capacity stays matched to real demand. | - Cuts overtime by scheduling the right number of people when closure opportunities are highest. <br><br> - Reduces idle time when volumes are naturally low which improves cost discipline. <br><br> - Improves on-time delivery because staffing follows the beat of actual work. | **OT avoided (h)** ≈ max(0, **{int(mx['closed'])}** − {avg_res:.1f}) × hrs/ticket. | **{best_day}** materially exceeds average (**{int(mx['closed'])} vs {avg_res:.1f}**). |
| De-duplicate and auto-link related incidents | **Phase 1 – Detect:** We implement duplicate and “related incident” detection early in the lifecycle using text similarity and rule signatures. <br><br> **Phase 2 – Auto-link:** We auto-link duplicates to a parent so agents close a set once rather than many times individually. <br><br> **Phase 3 – Track:** We track duplicate rates weekly and refine signatures to keep noise low over time. | - Removes redundant closure effort so analysts spend time fixing rather than duplicating admin steps. <br><br> - Lowers reopen risk because related work is coordinated under one record. <br><br> - Speeds overall cycle time as linked incidents close in a single motion. | **Savings (h)** = (#dupes × hrs/dupe). | Bulk-closure peaks typically include duplicates; linking prevents double work. |
| SLA-aware early escalations | **Phase 1 – Trigger:** We set alerts at 70–80% of SLA elapsed so at-risk incidents are visible before the last minute. <br><br> **Phase 2 – Route:** We route at-risk items to available resolvers or escalation owners with clear SLAs for response. <br><br> **Phase 3 – Review:** We analyze breach patterns monthly and refine thresholds and owners to keep risk low. | - Avoids penalty costs by preventing last-minute scrambles that often miss the SLA window. <br><br> - Reduces firefighting because escalations are proactive rather than reactive. <br><br> - Creates steadier daily closure flow as risk is managed earlier. | **Penalty avoided** = breaches_prevented × penalty_per_breach. | Troughs followed by sharp peaks suggest late pushes near SLA limits. |
""",
    "performance": f"""
| Recommendations | Explanation | Benefits | Cost Calculation | Evidence |
|---|---|---|---|---|
| Enforce WIP limits per resolver | **Phase 1 – Set:** We set clear work-in-progress caps by complexity so no one carries more than they can actively progress. <br><br> **Phase 2 – Pull:** We switch to a pull system where new work is taken only when capacity exists to avoid hidden queues. <br><br> **Phase 3 – Inspect:** We monitor limit breaches and coach teams on disciplined flow. | - Shortens cycle time because items are not waiting behind overloaded queues. <br><br> - Stabilizes daily closures as throughput is paced to real capacity. <br><br> - Reduces multi-day stalls that produce aging and breaches. | **Hours saved** = (aging_drop × hrs/ticket) + (variance_drop × hrs/recovery). | Very low days post-peak indicate WIP overload elsewhere. |
| Daily 15-min aging & SLA huddle | **Phase 1 – Surface:** We list the top aging items and those close to SLA breach so the team knows the handful that matter today. <br><br> **Phase 2 – Act:** We assign owners and an ETA on the spot with blockers captured and unblocked quickly. <br><br> **Phase 3 – Track:** We track same-day movement so the huddle stays outcome-focused and lean. | - Lifts on-time performance by turning attention to the few items that drive most risk. <br><br> - Reduces carryover because decisions happen early each day. <br><br> - Keeps everyone aligned on what must move now. | **Hours saved** = 0.25 h × participants × huddle_days − rework_hours_avoided. | Worst day **{worst_day}** marks stalling risk. |
| Real-time throughput dashboard | **Phase 1 – Monitor:** We display rolling averages versus actual closures so dips are visible immediately. <br><br> **Phase 2 – Alert:** We alert when closures drop below a threshold so leaders can intervene. <br><br> **Phase 3 – Intervene:** We apply staffing tweaks or deflection moves to recover within the same day. | - Accelerates correction on slow days so backlog does not accumulate. <br><br> - Reduces variance across the week by catching dips early. <br><br> - Improves predictability which stakeholders value. | **Hours saved** = (below_threshold_days × recovery_hours/day). | Troughs would trigger alarms for proactive action. |
""",
    "satisfaction": f"""
| Recommendations | Explanation | Benefits | Cost Calculation | Evidence |
|---|---|---|---|---|
| Standardized closure notes | **Phase 1 – Template:** We define short, structured notes for cause, action, and prevention so users receive clear explanations. <br><br> **Phase 2 – Enforce:** We add pre-close validation so missing fields are flagged before closure. <br><br> **Phase 3 – Audit:** We review reopen cases and refine templates to address recurring confusion. | - Reduces reopen rates because users understand what was done and what to do next. <br><br> - Cuts follow-up inquiries as clarity replaces ambiguity at closure. <br><br> - Builds trust through consistent, professional communication. | **Hours saved** = reopens_avoided × (reopen_handling_min/60). | Irregular daily volumes correlate with inconsistent comms. |
| Proactive updates on low-throughput days | **Phase 1 – Detect:** We detect days when closures fall below the average **{avg_res:.1f}** so communication can get ahead of frustration. <br><br> **Phase 2 – Notify:** We send ETA and an apology with next steps so expectations are reset early. <br><br> **Phase 3 – Measure:** We track complaint rate changes to tune timing and content. | - Mitigates dissatisfaction by acknowledging delays before users escalate. <br><br> - Lowers complaint volume which frees analysts to keep closing. <br><br> - Preserves stakeholder confidence even when output dips. | **Hours saved** = complaints_avoided × (handling_min/60). | Low-closure day {worst_day} is a CX hazard. |
| VIP fast-lane on low-output days | **Phase 1 – Tag:** We identify VIP and critical tickets so they are visible during slowdowns. <br><br> **Phase 2 – Route:** We route to a senior owner with stricter SLA and faster updates. <br><br> **Phase 3 – Track:** We track the VIP breach delta and adjust policy as needed. | - Protects key accounts by keeping their incidents moving even when throughput is constrained. <br><br> - Reduces escalations from executives which are costly and disruptive. <br><br> - Signals reliability to high-value stakeholders. | **Penalty avoided** = vip_breaches_prevented × penalty_per_breach. | Troughs heighten VIP impact risk. |
"""
}
                    render_cio_tables("Incidents Resolved", cio)
        else:
            st.warning("No closure-related columns detected for this section.")

    # ─────────────── 1c. Incidents Currently Open ───────────────
    with st.expander("📌 Incidents Currently Open"):
        if "request_status" in df_filtered.columns:
            open_df = df_filtered[df_filtered["request_status"].astype(str).str.lower() == "open"]

            # For CIO text safety
            safe_mx_level, safe_mx_open = "Lx", 0
            total_open_now = int(len(open_df))

            # Open by level
            if "level" in open_df.columns and not open_df.empty:
                by_level = open_df.groupby("level").size().reset_index(name="open_count")
                fig = px.bar(
                    _plotly_safe_df(by_level),
                    x="level",
                    y="open_count",
                    title="Open Incidents by Level",
                    color_discrete_sequence=BLUE_TONES
                )
                st.plotly_chart(fig, use_container_width=True)

                st.markdown("### Analysis of Open Incidents by Level")
                if not by_level.empty:
                    mx = by_level.loc[by_level["open_count"].idxmax()]
                    mn = by_level.loc[by_level["open_count"].idxmin()]
                    safe_mx_level = str(mx.get("level", "Lx"))
                    safe_mx_open  = int(mx.get("open_count", 0))
                    min_level = str(mn.get("level","-"))
                    min_open  = int(mn.get("open_count",0))

                    # --- Uniform analysis format for bar
                    st.write(f"""What this graph is: A bar chart showing current distribution of open incidents by support level.  
X-axis: Support level.  
Y-axis: Count of currently open incidents.  

What it shows in your data:  
Total open right now: {total_open_now}.  
Highest load at {safe_mx_level} with {safe_mx_open}; lowest at {min_level} with {min_open}.  

Overall, taller bars flag where backlog risk concentrates and aging is likely to start.  
How to read it operationally:  
Gap = relief target: Difference between the max ({safe_mx_open}) and the median is the immediate relief target.  
Lead–lag: If higher levels dominate, expect complexity/escalations; if L1 dominates, triage/automation gaps exist.  
Control: Set per-level WIP limits to prevent queue growth in the worst buckets.  
Why this matters: Concentrated open load increases aging, breaches, and escalations—prioritize these queues first.""")

            else:
                st.info("No 'level' column available or no open incidents to categorize.")

            # Opened vs Closed Over Time
            if "created_time" in df_filtered.columns:
                df_filtered["created_time"] = pd.to_datetime(df_filtered["created_time"], errors="coerce")
            if "completed_time" in df_filtered.columns:
                df_filtered["completed_time"] = pd.to_datetime(df_filtered["completed_time"], errors="coerce")

            if "created_time" in df_filtered.columns and "completed_time" in df_filtered.columns:
                opened = (
                    df_filtered.dropna(subset=["created_time"])
                    .groupby(df_filtered["created_time"].dt.date)
                    .size().reset_index(name="opened")
                )
                closed = (
                    df_filtered.dropna(subset=["completed_time"])
                    .groupby(df_filtered["completed_time"].dt.date)
                    .size().reset_index(name="closed")
                )

                rate = pd.merge(
                    opened.rename(columns={"created_time": "date"}),
                    closed.rename(columns={"completed_time": "date"}),
                    on="date", how="outer"
                ).fillna(0).sort_values("date")

                fig2 = px.line(
                    _plotly_safe_df(rate),
                    x="date",
                    y=["opened", "closed"],
                    title="Opened vs Closed Over Time",
                    labels={"value": "Number of Incidents", "variable": "Metric"},
                    color_discrete_sequence=BLUE_TONES
                )
                st.plotly_chart(fig2, use_container_width=True)

                if not rate.empty:
                    total_opened  = int(rate["opened"].sum())
                    total_closed  = int(rate["closed"].sum())
                    avg_opened    = float(rate["opened"].mean())
                    avg_closed    = float(rate["closed"].mean())
                    peak_open     = rate.loc[rate["opened"].idxmax()]
                    peak_close    = rate.loc[rate["closed"].idxmax()]
                    daily_gap_avg = avg_opened - avg_closed

                    st.markdown("### Analysis – Opened vs Closed Trends")
                    # --- Uniform analysis format
                    st.write(f"""What this graph is: A dual throughput chart comparing opened (inflow) and closed (outflow) tickets per day.  
X-axis: Calendar date.  
Y-axis: Counts for each daily metric (opened, closed).  

What it shows in your data:  
Largest intake day: {peak_open['date']} with {int(peak_open['opened'])} opened.  
Largest closure day: {peak_close['date']} with {int(peak_close['closed'])} closed.  
Averages over the period are {avg_opened:.1f} opened/day vs {avg_closed:.1f} closed/day.  

Overall, when the closed line persistently tracks below the opened line, the process is under-capacity and backlog grows; when it meets or exceeds openings, backlog burns down and stability improves.  
How to read it operationally:  
Gap = backlog delta: The vertical distance between lines is the daily backlog change (≈ {daily_gap_avg:.1f} on average).  
Lead–lag: Closures peaking after openings implies reactive sprints, not smooth flow.  
Recovery strength: Faster crossover after spikes = healthier system.  
Control: Target near-parallel lines with minimal gap via routing, WIP limits, and surge capacity.  
Why this matters: Balance between inflow and outflow is the heartbeat of the desk; keeping outflow at or above inflow prevents aging, protects SLA, and steadies customer experience.""")

                else:
                    total_opened = total_closed = 0
                    avg_opened = avg_closed = 0.0
                    daily_gap_avg = 0.0
                    peak_open = {"date": "-", "opened": 0}
                    peak_close = {"date": "-", "closed": 0}

                # CIO tables for Open Incidents section
                cio = {
    "cost": f"""
| Recommendations | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Automate repetitive low-priority incidents | **Phase 1 – Detect:** We mine low-complexity L1 patterns where resolution steps are short and consistent so they are suitable for automation or self-service. <br><br> **Phase 2 – Build:** We create bots or guided flows that complete the fix or collect the exact data needed for a fast human touch. <br><br> **Phase 3 – Govern:** We watch deflection rates and error fallbacks to keep automation safe and continuously improved. | - Reduces analyst minutes per ticket because common issues are solved without manual effort. <br><br> - Lowers overtime on spike days as inflow is partially deflected before it hits the queue. <br><br> - Stabilizes unit cost per incident by shifting routine work to cheaper, automated paths. | **Savings (h)** = automated × (mins/ticket/60). Spike sizing: **{peak_open['date'] if isinstance(peak_open, pd.Series) else '-'}** with **{int(peak_open['opened']) if isinstance(peak_open, pd.Series) else 0}** opened vs avg **{avg_opened:.1f}**. | Level chart shows concentration at **{safe_mx_level}** (**{safe_mx_open}**). Dual chart shows intake spikes and persistent gap ≈ **{daily_gap_avg:.1f}/day**. |
| Optimize staffing to match inflow | **Phase 1 – Model:** We set schedules against the observed averages of **{avg_opened:.1f}** opened and **{avg_closed:.1f}** closed per day so we know the base capacity delta. <br><br> **Phase 2 – Flex:** We implement surge seats and short shifts around predicted peaks so queues do not swell. <br><br> **Phase 3 – Review:** We hold a weekly variance review to fine-tune coverage as patterns drift. | - Lowers overtime by matching capacity to the demand curve. <br><br> - Reduces idle time on quiet days which keeps cost per incident consistent. <br><br> - Improves predictability by shrinking the daily opened-minus-closed gap. | **OT avoided (h)** ≈ max(0, spike_open − planned) × hrs/ticket. Spike proxy: **{peak_open['date'] if isinstance(peak_open, pd.Series) else '-'}** = **{int(peak_open['opened']) if isinstance(peak_open, pd.Series) else 0}**. | Persistent opened > closed gap ≈ **{daily_gap_avg:.1f}/day** proves mismatch. |
| Fast-close factory for aging queues | **Phase 1 – Identify:** We target “nearly done” items and queues with simple pending actions so they can be closed quickly. <br><br> **Phase 2 – Swarm:** We run short sprints with clear owners to close these items in bulk and free capacity. <br><br> **Phase 3 – Sustain:** We add concise checklists so similar items do not linger in the future. | - Lowers work-in-progress carrying cost by converting stuck items into closures. <br><br> - Frees capacity to handle new inflow, reducing backlog growth. <br><br> - Shortens lead times for users waiting on small final steps. | **Hours released** = sprint_closures × hrs/ticket; sprint sizing guided by current open total **{total_open_now}**. | Heaviest queue at **{safe_mx_level}** (**{safe_mx_open}**); outflow trails inflow by **{daily_gap_avg:.1f}/day**. |
""",
    "performance": f"""
| Recommendations | Explanation | Benefits | Cost Calculation | Evidence |
|---|---|---|---|---|
| SLA-driven prioritization & WIP limits | **Phase 1 – Rank:** We rank open items by time-to-breach and age so the riskiest are always worked first. <br><br> **Phase 2 – Cap:** We set per-agent WIP limits so work flows without hidden queues and context switching. <br><br> **Phase 3 – Audit:** We monitor breach and aging trends weekly to enforce discipline. | - Raises on-time performance because attention stays on items that matter most. <br><br> - Shrinks tail aging which improves overall cycle time. <br><br> - Creates steadier throughput relative to intake. | **Penalty avoided** = breaches_prevented × penalty_per_breach; **Hours saved** = (aging_drop × hrs/ticket). | Opened > closed by ~**{daily_gap_avg:.1f}/day** → breach risk. |
| Real-time flow triggers | **Phase 1 – Instrument:** We stream opened and closed counts in real time to create a daily gap indicator. <br><br> **Phase 2 – Trigger:** We alert when the gap stays above zero for consecutive days so leaders can intervene. <br><br> **Phase 3 – Act:** We apply surge staffing, re-routing, or deflection until the lines converge. | - Enables earlier interventions so small gaps do not become backlogs. <br><br> - Reduces firefighting because corrections happen during the day, not after the fact. <br><br> - Keeps the system in steady state more often. | **Hours saved** = (gap_days × gap_per_day × hrs/ticket). | Multi-day stretches where closures trail openings are visible in the dual chart. |
| Skill-based re-routing on overload levels | **Phase 1 – Map:** We map overflow from **{safe_mx_level}** to additional trained pools so items move where capacity exists. <br><br> **Phase 2 – Route:** We auto-route new and selected existing items to the expanded pool to drain the heaviest queue. <br><br> **Phase 3 – Tune:** We minimize reassignments by refining rules based on real outcomes. | - Cuts handoffs and waiting time by getting work to the right people faster. <br><br> - Improves first-touch resolution rates because specialists engage earlier. <br><br> - Reduces queue imbalance that creates local bottlenecks. | **Hours saved** = (reassignment_drop × mins_reassign/60) × **{safe_mx_open}**. | Level bars show the heaviest queue (**{safe_mx_level}: {safe_mx_open}**). |
""",
    "satisfaction": f"""
| Recommendations | Explanation | Benefits | Cost Calculation | Evidence |
|---|---|---|---|---|
| Proactive ETA when daily gap > 0 | **Phase 1 – Detect:** We detect when opened − closed is above zero and forecast the impact window for users. <br><br> **Phase 2 – Notify:** We send ETAs and next steps so expectations are set and anxiety is reduced. <br><br> **Phase 3 – Measure:** We track complaints and contact rates and tune triggers accordingly. | - Reduces “any update?” contacts because users understand the delay and the plan. <br><br> - Improves sentiment by acknowledging pressure days transparently. <br><br> - Frees agent time by deflecting unnecessary follow-ups. | **Hours saved** = (impacted_tickets × followup_min/60); impact proxy ≈ day gap **{daily_gap_avg:.1f}**. | Dual chart shows days with outflow lag; target those windows. |
| VIP fast-lane for open queues | **Phase 1 – Tag:** We mark VIP and critical tickets within the open pool so they are prioritized despite high load. <br><br> **Phase 2 – Route:** We assign to senior owners with specific SLAs and checkpoint updates. <br><br> **Phase 3 – Track:** We track VIP breach deltas and adjust fast-lane criteria. | - Protects key relationships by accelerating high-impact work through congestion. <br><br> - Reduces executive escalations which are time-consuming and costly. <br><br> - Signals reliability for strategic stakeholders. | **Penalty avoided** = vip_breaches_prevented × penalty_per_breach. | High open load (**{total_open_now}**) raises risk for VIPs. |
| Status transparency by level | **Phase 1 – Publish:** We show per-level queue size and ETA on the portal so users and managers can see progress. <br><br> **Phase 2 – Update:** We auto-refresh status periodically so information stays current without manual effort. <br><br> **Phase 3 – Survey:** We measure CSAT effect and refine visibility and messaging. | - Cuts inbound inquiries because users can self-serve status. <br><br> - Increases perceived fairness as workload distribution is visible. <br><br> - Helps managers plan around realistic ETAs. | **Hours saved** = inquiries_deflected × (handling_min/60). | Largest queue: **{safe_mx_level}** with **{safe_mx_open}** drives perception issues. |
"""
}
                render_cio_tables("Open Incidents", cio)
            else:
                st.warning("⚠️ 'created_time' and 'completed_time' columns required for Opened vs Closed analysis.")
        else:
            st.warning("⚠️ 'request_status' column not found. Cannot derive open incidents.")

    # ─────────────── 1d. Average Time to Resolve ───────────────
    with st.expander("📌 Average Time to Resolve Incidents"):
        if {"created_time", "resolved_time"} <= set(df_filtered.columns):
            df_filtered["created_time"] = pd.to_datetime(df_filtered["created_time"], errors="coerce")
            df_filtered["resolved_time"] = pd.to_datetime(df_filtered["resolved_time"], errors="coerce")

            df_filtered["resolution_hours"] = (
                (df_filtered["resolved_time"] - df_filtered["created_time"]).dt.total_seconds() / 3600
            )
            res = df_filtered["resolution_hours"].dropna()

            if not res.empty:
                # month may be Period; coerce to str if present
                if "month" in df_filtered.columns and pd.api.types.is_period_dtype(df_filtered["month"]):
                    df_filtered["month"] = df_filtered["month"].astype(str)

                if "month" in df_filtered.columns:
                    by_m = (
                        df_filtered.dropna(subset=["resolution_hours"])
                        .groupby("month")["resolution_hours"]
                        .median()
                        .reset_index()
                    )
                    fig = px.line(
                        _plotly_safe_df(by_m), x="month", y="resolution_hours",
                        title="Median Resolution Time by Month (hours)",
                        color_discrete_sequence=BLUE_TONES
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    if not by_m.empty:
                        min_med   = float(by_m["resolution_hours"].min())
                        max_med   = float(by_m["resolution_hours"].max())
                        med_of_med= float(by_m["resolution_hours"].median())
                        st.markdown("### Analysis – Median Resolution Time by Month")
                        st.write(f"""What this graph is: A line chart showing median resolution time by month.  
X-axis: Month.  
Y-axis: Median hours to resolve.  

What it shows in your data:  
Monthly medians range from {min_med:.2f} h to {max_med:.2f} h (median of medians ≈ {med_of_med:.2f} h).  

Overall, downtrends indicate process efficiency gains; spikes suggest bottlenecks (staffing, parts, vendors, approvals).  
How to read it operationally:  
Peaks: Investigate runbooks, vendor SLAs, and handoff delays.  
Plateaus: Standardize best-performing playbooks.  
Downswings: Institutionalize improvements (automation, knowledge).  
Mix: Segment by category/priority to localize issues.  
Why this matters: Lower, stable medians reduce SLA breaches, cost, and variance in user experience.""")

                else:
                    by_m = pd.DataFrame()

                fig2 = px.histogram(
                    _plotly_safe_df(df_filtered.dropna(subset=["resolution_hours"])),
                    x="resolution_hours", nbins=30, title="Resolution Time Distribution (hours)",
                    color_discrete_sequence=BLUE_TONES
                )
                st.plotly_chart(fig2, use_container_width=True)

                mean_val   = float(res.mean())
                median_val = float(res.median())
                p90_val    = float(res.quantile(0.9))
                max_val    = float(res.max())
                p90_cases  = int((res >= p90_val).sum())
                n_res      = int(res.shape[0])

                # --- Uniform analysis format for histogram
                st.markdown("### Analysis – Resolution Time Distribution")
                st.write(f"""What this graph is: A histogram showing the distribution of resolution times.  
X-axis: Resolution duration (hours).  
Y-axis: Incident frequency.  

What it shows in your data:  
Mean {mean_val:.2f} h, median {median_val:.2f} h, 90th percentile {p90_val:.2f} h, max {max_val:.2f} h.  
There are {p90_cases} tickets at or above the 90th-percentile threshold.  

Overall, compact clusters around the median show predictable work, while the right tail represents SLA and CSAT risk.  
How to read it operationally:  
Peaks (tail bins): Swarm and escalate earlier to compress the tail.  
Plateaus (mid bins): Standardize steps to shave minutes consistently.  
Downswings: Confirm which fixes lowered tail weight.  
Mix: Tag outliers by category/owner to target coaching and playbooks.  
Why this matters: Tail compression yields the largest SLA and satisfaction gains for the least process change.""")

                med_of_med = float(by_m["resolution_hours"].median()) if (not by_m.empty) else median_val

                cio = {
    "cost": f"""
| Recommendations | Explanation | Benefits | Cost Calculation | Evidence |
|---|---|---|---|---|
| Standardize workflows for high-volume categories | **Phase 1 – Codify:** We translate proven steps for frequent issues into concise, unambiguous checklists so analysts do the right things in the right order. <br><br> **Phase 2 – Embed:** We embed those checklists in the agent UI with pre-filled fields and validations to reduce errors and omissions. <br><br> **Phase 3 – Audit:** We track adherence and time per step and refine the workflow where friction persists. | - Lowers average handling time because unnecessary steps and avoidable rework are removed. <br><br> - Reduces escalations by creating a reliable, quality baseline for common work. <br><br> - Produces predictable throughput that aligns staffing to real effort. | **Hours saved** = ({mean_val:.2f} − target_mean) × **{n_res}**. | Histogram shows mean **{mean_val:.2f} h** with long right tail—evidence of inconsistent handling. |
| Automate repetitive resolutions | **Phase 1 – Identify:** We isolate low-complexity patterns where the entire fix or a large portion can be automated safely. <br><br> **Phase 2 – Build:** We implement self-service flows or bots that execute the resolution with appropriate guardrails. <br><br> **Phase 3 – Measure:** We track deflection and error rates and iterate to expand safe coverage. | - Offloads routine work so engineers concentrate on complex cases with higher value. <br><br> - Compresses the right tail by removing slow repeats from the human queue. <br><br> - Improves cost to serve by shifting volume to a cheaper path. | **Hours saved** = automated_tickets × **{mean_val:.2f}**. | Tail cohort **{p90_cases}** ≥ p90 (**{p90_val:.2f} h**) highlights automation targets. |
| Root-cause fixes for repeats | **Phase 1 – Analyze:** We investigate the categories dominating the tail to find technical or process causes that keep recurring. <br><br> **Phase 2 – Remediate:** We implement technical fixes, configuration changes, or vendor adjustments that remove the source. <br><br> **Phase 3 – Verify:** We watch recurrence rate and resolution-time distribution for sustained improvement. | - Reduces total incident volume by removing repeat drivers at the source. <br><br> - Lowers total cost of ownership because fewer incidents enter the system. <br><br> - Stabilizes monthly medians by eliminating chronic outliers. | **Hours saved** = repeat_tickets × **{mean_val:.2f}**. | Max reaches **{max_val:.2f} h**; repeated long cases inflate cost. |
| Staff to monthly medians | **Phase 1 – Read:** We treat the median-of-month medians (≈ **{med_of_med:.2f} h**) as a realistic planning baseline rather than best or worst extremes. <br><br> **Phase 2 – Roster:** We align staffing to heavier months and avoid overstaffing in lighter months. <br><br> **Phase 3 – Tune:** We back-test each month and adjust staffing and playbooks as the distribution shifts. | - Reduces overtime in heavy months by preparing capacity in advance. <br><br> - Smooths the cost profile across months by avoiding reactionary swings. <br><br> - Improves predictability for stakeholders who depend on steady delivery. | **OT avoided (h)** ≈ (peak_month_median − **{med_of_med:.2f}**) × tickets_in_peak_month. | Median-by-month line shows variation between months. |
| Closure checklists | **Phase 1 – Define:** We define must-have closure fields and acceptance criteria so “done” means the same thing every time. <br><br> **Phase 2 – Enforce:** We enforce pre-close validation so incomplete work cannot slip through. <br><br> **Phase 3 – Track:** We track reopen percentage and fix the patterns that drive returns. | - Prevents rework loops that increase average time and frustrate users. <br><br> - Lifts data quality which enables better analytics and planning. <br><br> - Protects the mean and median from creeping upward due to poor-quality closures. | **Hours saved** = reopens_avoided × **{mean_val:.2f}**. | Outliers beyond **{p90_val:.2f} h** often correlate with reopens. |
""",
    "performance": f"""
| Recommendations | Explanation | Benefits | Cost Calculation | Evidence |
|---|---|---|---|---|
| Swarm complex cases early | **Phase 1 – Flag:** We flag cases trending above median **{median_val:.2f} h** so they receive early attention. <br><br> **Phase 2 – Assist:** We assemble a short multi-skill swarm to unblock the case quickly. <br><br> **Phase 3 – Exit:** We run a brief post-mortem to capture the fix and prevent repeat delays. | - Shrinks p90 and p95 so the long tail does less damage to SLA and perception. <br><br> - Reduces breaches by accelerating hard work before clocks run out. <br><br> - Spreads expertise through rapid knowledge capture. | **Hours saved** = ({p90_val:.2f} − target_p90) × **{p90_cases}**. | Gap median→p90 (**{median_val:.2f} → {p90_val:.2f} h**). |
| Early-warning timers (median+2σ) | **Phase 1 – Compute:** We compute dynamic thresholds using median plus two standard deviations to detect emerging tail items. <br><br> **Phase 2 – Alert:** We alert owners before breach risk spikes so they can escalate or re-route. <br><br> **Phase 3 – Act:** We apply playbooks that pull help in fast. | - Lifts on-time rate by giving teams enough runway to respond. <br><br> - Reduces last-minute firefights that consume disproportionate effort. <br><br> - Stabilizes tail behavior across months. | **Penalty avoided** = breaches_prevented × penalty_per_breach. | Presence of long tail including max **{max_val:.2f} h**. |
| Expertise routing by category | **Phase 1 – Map:** We map slow categories to resolvers with demonstrated speed and accuracy. <br><br> **Phase 2 – Auto-route:** We route on first touch to the expert pool to reduce handoffs. <br><br> **Phase 3 – Review:** We monitor reassignment and time deltas to refine rules. | - Lowers the mean by getting complex work to the right experts faster. <br><br> - Tightens variance which improves predictability for planning. <br><br> - Increases first-time-fix where specialization matters most. | **Hours saved** = (Δmean_per_category × volume_per_category) aggregated over categories. | Histogram clusters by category imply specialization need. |
""",
    "satisfaction": f"""
| Recommendations | Explanation | Benefits | Cost Calculation | Evidence |
|---|---|---|---|---|
| Milestone-based ETAs | **Phase 1 – Define:** We define clear milestones such as acknowledge, triage, fix, and verify so users see progress. <br><br> **Phase 2 – Notify:** We send ETAs at each milestone and update delays transparently. <br><br> **Phase 3 – Review:** We track inquiry rates and adjust content for clarity. | - Cuts duplicate contacts because users know where they are in the journey. <br><br> - Improves trust by showing movement even when final resolution takes time. <br><br> - Helps managers plan around realistic timelines. | **Hours saved** = inquiries_deflected × (handling_min/60). | Tail up to **{max_val:.2f} h** hurts perception most. |
| Tiered VIP SLAs | **Phase 1 – Tag:** We tag VIPs and critical services and define stricter timers and escalation paths for them. <br><br> **Phase 2 – Monitor:** We monitor timers and trigger faster updates for high-impact users. <br><br> **Phase 3 – Report:** We report VIP breach deltas to validate value and tune policies. | - Protects key relationships by ensuring faster decision cycles. <br><br> - Reduces high-cost escalations that distract teams from broad delivery. <br><br> - Demonstrates control to senior stakeholders. | **Penalty avoided** = vip_breaches_prevented × penalty_per_breach. | Outliers disproportionately damage VIP sentiment. |
| Post-resolution feedback loops | **Phase 1 – Target:** We gather short feedback on cases above the median **{median_val:.2f} h** to locate friction in the process. <br><br> **Phase 2 – Fix:** We update runbooks, automation, or vendor steps to remove the friction. <br><br> **Phase 3 – Iterate:** We re-survey and confirm that the distribution shifts left. | - Delivers quick CX wins by fixing pain points that users actually report. <br><br> - Reduces follow-ups because recurring issues are resolved at the source. <br><br> - Creates a measurable closed-loop improvement cycle. | **Hours saved** = followups_reduced × (handling_min/60) among slow cases. | Tail points directly at dissatisfaction cohort. |
"""
}
                render_cio_tables("Resolution Time", cio)

            else:
                st.info("No resolved incidents found to calculate resolution time.")
        else:
            st.warning("⚠️ Required columns 'created_time' and 'resolved_time' not found.")

    # ─────────────── 1e. Backlog (Unresolved) ───────────────
    with st.expander("📌 Incident Backlog (Unresolved)"):
        if "created_time" in df_filtered.columns:
            df_filtered = df_filtered.copy()  # avoid SettingWithCopy
            df_filtered["created_time"]  = pd.to_datetime(df_filtered["created_time"], errors="coerce")

            # prefer completed_time if present; otherwise create it as NaT
            if "completed_time" in df_filtered.columns:
                df_filtered["completed_time"] = pd.to_datetime(df_filtered["completed_time"], errors="coerce")
            else:
                df_filtered["completed_time"] = pd.NaT

            opened = (
                df_filtered.dropna(subset=["created_time"])
                .groupby(df_filtered["created_time"].dt.date)
                .size().reset_index(name="opened")
            )
            closed = (
                df_filtered.dropna(subset=["completed_time"])
                .groupby(df_filtered["completed_time"].dt.date)
                .size().reset_index(name="closed")
            )

            rate = pd.merge(
                opened.rename(columns={"created_time": "date"}),
                closed.rename(columns={"completed_time": "date"}),
                on="date", how="outer"
            ).fillna(0).sort_values("date")

            # If no rows, show info and stop
            if rate.empty:
                st.info("No open/closed activity found—cannot derive backlog or CIO actions.")
                st.stop()

            rate["backlog"]   = (rate["opened"] - rate["closed"]).cumsum()
            rate["daily_gap"] = rate["opened"] - rate["closed"]

            fig = px.line(
                _plotly_safe_df(rate), x="date", y="backlog", title="Incident Backlog Over Time",
                color_discrete_sequence=BLUE_TONES
            )
            st.plotly_chart(fig, use_container_width=True)

            avg_opened = float(rate["opened"].mean())
            avg_closed = float(rate["closed"].mean())
            net_gap_avg= float(rate["daily_gap"].mean())

            peak   = rate.loc[rate["backlog"].idxmax()]
            latest = rate.iloc[-1]
            avg_bk = float(rate["backlog"].mean())

            # stringify dates for CIO tables (DD/MM/YYYY)
            fmt_date = lambda d: pd.to_datetime(d).strftime("%d/%m/%Y") if pd.notna(d) else "-"

            st.markdown("### Analysis – Incident Backlog Over Time")
            st.write(f"""What this graph is: A cumulative flow line showing unresolved ticket backlog over time (opened − closed cumulatively).  
    X-axis: Calendar date.  
    Y-axis: Backlog size (tickets).  

    What it shows in your data:  
    Backlog peaked on {fmt_date(peak['date'])} with {int(peak['backlog'])} unresolved tickets.  
    As of the latest date ({fmt_date(latest['date'])}), backlog stands at {int(latest['backlog'])} (average level ≈ {avg_bk:.1f}).  
    Average inflow ≈ {avg_opened:.1f}/day vs average outflow ≈ {avg_closed:.1f}/day (net gap ≈ {net_gap_avg:.1f}/day).  

    Overall, a rising line indicates demand exceeding capacity; a flat or falling line indicates catch-up and stabilization.  
    How to read it operationally:  
    Peaks: Trigger burn-down sprints and re-routing when backlog approaches the peak ({int(peak['backlog'])}).  
    Plateaus: Hold gains—keep outflow ≥ inflow (target ≥ {avg_opened:.1f}/day closures).  
    Downswings: Verify which interventions (staffing, automation, triage) created the decline and keep them.  
    Mix: Segment the backlog by priority/age so critical items aren’t buried.  
    Why this matters: Backlog is operational debt; the higher it climbs, the more expensive every day becomes (breaches, escalations, unhappy users).""")

            # Peaks and gaps
            peak_bk = int(peak["backlog"])
            latest_bk = int(latest["backlog"])

            peak_open_row  = rate.loc[rate["opened"].idxmax()] if (rate["opened"].max() >= 0) else None
            peak_close_row = rate.loc[rate["closed"].idxmax()] if (rate["closed"].max() >= 0) else None
            worst_gap_row  = rate.loc[rate["daily_gap"].idxmax()] if (rate["daily_gap"].max() >= 0) else None

            worst_gap       = int(worst_gap_row["daily_gap"]) if worst_gap_row is not None else 0
            worst_gap_date  = fmt_date(worst_gap_row["date"]) if worst_gap_row is not None else "-"
            peak_open       = int(peak_open_row["opened"]) if peak_open_row is not None else 0
            peak_open_date  = fmt_date(peak_open_row["date"]) if peak_open_row is not None else "-"
            peak_close      = int(peak_close_row["closed"]) if peak_close_row is not None else 0
            peak_close_date = fmt_date(peak_close_row["date"]) if peak_close_row is not None else "-"

            # Clearance math
            surge_closure = avg_closed if avg_closed > 0 else avg_opened
            surge_closure = max(surge_closure, avg_opened * 1.2)
            burn_rate_with_surge = max(surge_closure - avg_opened, 0.0001)
            est_days_to_clear_latest = latest_bk / burn_rate_with_surge if burn_rate_with_surge > 0 else float("inf")

            # ── CIO tables
            cio = {
                "cost": f"""
    | Recommendations | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
    |---|---|---|---|---|
    | Automate repetitive backlog items | **Phase 1 – Identify:** We scan the backlog for high-volume, low-complexity items that are safe to automate so humans can focus on harder work. <br><br> **Phase 2 – Build:** We implement self-service or bots that close these items or gather the exact data needed to close them quickly. <br><br> **Phase 3 – Govern:** We monitor deflection and fallback rates and tune flows to keep quality high. | - Frees skilled staff from routine tasks so they can accelerate the burn-down of complex items. <br><br> - Reduces overtime exposure during spikes because inflow is partially deflected. <br><br> - Lowers cost per incident by shifting repetitive work to low-cost automated paths. | **Savings (h)** = automated × hrs/ticket; capacity target: peak backlog **{peak_bk}** and worst gap **{worst_gap}** on **{worst_gap_date}**. | Backlog peak **{peak_bk}** and worst daily gap **{worst_gap}** prove repetitive load suitable for automation. |
    | Optimize staffing on spike windows | **Phase 1 – Forecast:** Plan coverage using average inflow **{avg_opened:.1f}** and outflow **{avg_closed:.1f}**. <br><br> **Phase 2 – Surge:** Schedule temporary surge seats around intake spike days (e.g., **{peak_open_date}**). <br><br> **Phase 3 – Review:** Refine staffing to keep burn-down on track. | - Cuts overtime premiums. <br><br> - Reduces idle time on troughs. <br><br> - Accelerates backlog reduction. | **OT avoided (h)** = max(0, **{peak_open}** − **{avg_closed:.1f}**) × hrs/ticket. | Opened peaked **{peak_open}** (on **{peak_open_date}**), exceeding avg closures **{avg_closed:.1f}**. |
    | Fast-close “nearly done” items | **Phase 1 – Detect:** Find tickets at the last step. <br><br> **Phase 2 – Swarm:** Short sprints to close them. <br><br> **Phase 3 – Sustain:** Add concise closure checklists. | - Reduces WIP carrying cost. <br><br> - Returns capacity to handle new inflow. <br><br> - Improves UX by clearing stale items. | **Hours released** = sprint_closures × hrs/ticket (target ≈ **{int(0.3*latest_bk)}** from **{latest_bk}**). | Latest backlog **{latest_bk}** favors quick-win focus. |
    | Streamline closure workflow | **Phase 1 – Map:** Remove redundant approvals/fields. <br><br> **Phase 2 – Automate:** Pre-fill/validate forms. <br><br> **Phase 3 – Measure:** Track closure lead-time. | - Increases outflow by removing friction. <br><br> - Reduces rework. <br><br> - Lowers backlog plateau. | **Hours saved/day** = (mins_saved_per_ticket/60) × **{avg_closed:.1f}**. | Plateau segments indicate slow closures. |
    | Self-service for common backlog types | **Phase 1 – Curate:** Top five frequent issues. <br><br> **Phase 2 – Publish:** Guided flows. <br><br> **Phase 3 – Track:** Measure deflection. | - Deflects inflow. <br><br> - Lowers cost to serve. <br><br> - Speeds user outcomes. | **Hours saved** = deflected × hrs/ticket; target deflection to worst gap **{worst_gap}**. | Worst daily gap **{worst_gap}** (on **{worst_gap_date}**). |
    """,
                "performance": f"""
    | Recommendations | Explanation | Benefits | Cost Calculation | Evidence |
    |---|---|---|---|---|
    | Apply WIP limits | **Cap → Pull → Inspect.** | - Shorter cycle times. <br><br> - Stable throughput. <br><br> - Less firefighting. | **Hours saved** = (aging_drop × hrs/ticket) + (variance_drop × hrs/recovery). | Rising stretches where outflow < inflow (gap ≈ **{net_gap_avg:.1f}**). |
    | Oldest-first with SLA bands | Band by age/priority; work oldest-first. | - Fewer SLA breaches. <br><br> - Predictability. <br><br> - Stakeholder confidence. | **Penalty avoided** = breaches_prevented × penalty_per_breach. | Peak backlog **{peak_bk}** implies aging risk. |
    | Backlog burn-down sprints | Target based on latest backlog **{latest_bk}**; add surge. | - Rapid backlog reduction. <br><br> - Faster return to normal. <br><br> - Repeatable playbook. | **Hours released** = (surge/day − **{avg_closed:.1f}**) × days × hrs/ticket; **Days to clear** ≈ **{est_days_to_clear_latest:.1f}**. | Averages justify surge; formula uses actuals. |
    """,
                "satisfaction": f"""
    | Recommendations | Explanation | Benefits | Cost Calculation | Evidence |
    |---|---|---|---|---|
    | Publish backlog recovery plan | Set weekly burn targets; share ETA. | - Fewer escalations. <br><br> - More trust. <br><br> - Alignment on goals. | **Hours saved** = escalations_avoided × (handling_min/60). | Peak **{peak_bk}** and latest **{latest_bk}**. |
    | Proactive updates for aging tickets | Detect >SLA; send ETA. | - Mitigates dissatisfaction. <br><br> - Lowers complaint volume. <br><br> - Fairness in queues. | **Hours saved** = complaints_avoided × (handling_min/60). | Positive gap ≈ **{net_gap_avg:.1f}/day**. |
    | VIP fast-lane within backlog | Tag/route VIPs to seniors. | - Protects high-value relationships. <br><br> - Reduces high-impact escalations. <br><br> - Shows control. | **Penalty avoided** = vip_breaches_prevented × penalty_per_breach. | High backlog concentrates risk for VIPs. |
    """
            }

            # ✅ Render the CIO tables (this was missing)
            render_cio_tables("Backlog Recovery – CIO Actions", cio)

        else:
            st.warning("Column 'created_time' is required to derive backlog.")
