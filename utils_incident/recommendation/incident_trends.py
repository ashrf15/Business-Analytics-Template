import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from textwrap import dedent

# ─────────────────────────────────────────────────────────
# Helper to render CIO tables (expects clean, left-aligned markdown)
# ─────────────────────────────────────────────────────────
def render_cio_tables(title, cio_data):
    st.subheader(title)
    with st.expander("Cost Reduction"):
        st.markdown(cio_data["cost"], unsafe_allow_html=True)
    with st.expander("Performance Improvement"):
        st.markdown(cio_data["performance"], unsafe_allow_html=True)
    with st.expander("Customer Satisfaction Improvement"):
        st.markdown(cio_data["satisfaction"], unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────
# Main function for Target 6
# ─────────────────────────────────────────────────────────
def incident_trends(df_filtered: pd.DataFrame):
    # ---------------------- 6a ----------------------
    with st.expander("📌 Daily / Weekly / Monthly Trends"):
        if "created_time" not in df_filtered.columns:
            st.warning("Need 'created_time' for trend analysis.")
        else:
            df_filtered = df_filtered.copy()
            df_filtered["created_time"] = pd.to_datetime(df_filtered["created_time"], errors="coerce")
            base = df_filtered.dropna(subset=["created_time"])
            if base.empty:
                st.info("No valid dates in 'created_time'.")
            else:
                # Prepare data
                day = (
                    base.groupby(base["created_time"].dt.date)
                    .size().reset_index(name="count")
                    .rename(columns={"created_time": "created_time"})
                )
                # Week start (use Period->start_time for stable buckets)
                week = (
                    base.groupby(base["created_time"].dt.to_period("W").apply(lambda p: p.start_time.date()))
                    .size().reset_index(name="count")
                    .rename(columns={"created_time": "created_time"})
                )
                # Month start
                month = (
                    base.groupby(base["created_time"].dt.to_period("M").apply(lambda p: p.start_time.date()))
                    .size().reset_index(name="count")
                    .rename(columns={"created_time": "created_time"})
                )

                # === Graph 1: Daily Trend ===
                if day.empty:
                    st.info("No daily trend data to display.")
                else:
                    fig1 = px.line(
                        day, x="created_time", y="count",
                        title="Daily Incident Trends",
                        labels={"created_time": "Date", "count": "Incident Count"}
                    )
                    st.plotly_chart(fig1, use_container_width=True)

                    # --- Analysis for Daily ---
                    st.markdown("#### Daily Trend Analysis")
                    peak_day = day.loc[day["count"].idxmax()]
                    low_day = day.loc[day["count"].idxmin()]
                    avg_daily = day["count"].mean()
                    st.write(f"""
**What this graph is:** A line chart showing **daily incident volume** over time.  
- **X-axis:** Calendar date.  
- **Y-axis:** Number of incidents created per day.

**What it shows in your data:** Daily volume peaked on **{pd.to_datetime(peak_day['created_time']).strftime('%d/%m/%Y')}** with **{int(peak_day['count'])} tickets**,  
and the lowest day recorded **{int(low_day['count'])} tickets**. The average daily level is **{avg_daily:.1f} tickets/day**.

Overall, sharp upswings indicate **demand spikes** (risk of aging/SLA breach), while flat or declining stretches indicate **catch-up and stabilization**.

**How to read it operationally:**  
1) **Peaks:** Trigger surge playbooks and adjust routing/staffing.  
2) **Plateaus:** Hold the gains—maintain outflow ≥ inflow.  
3) **Downswings:** Validate which interventions (staffing, automation, triage) worked.  
4) **Mix:** Segment by priority/category to ensure critical items aren’t buried.

**Why this matters:** Daily incident volume is **leading workload signal**. Managing spikes early prevents breaches, escalations, and downstream cost.
                    """)

                # === Graph 2: Weekly Trend ===
                if week.empty:
                    st.info("No weekly trend data to display.")
                else:
                    fig2 = px.bar(
                        week, x="created_time", y="count",
                        title="Weekly Incident Volume",
                        labels={"created_time": "Week Start", "count": "Incident Count"}
                    )
                    st.plotly_chart(fig2, use_container_width=True)

                    # --- Analysis for Weekly ---
                    st.markdown("#### Weekly Trend Analysis")
                    peak_week = week.loc[week["count"].idxmax()]
                    low_week = week.loc[week["count"].idxmin()]
                    avg_weekly = week["count"].mean()
                    st.write(f"""
**What this graph is:** A bar chart showing **weekly incident volume** (noise-reduced view of demand).  
- **X-axis:** Week start date.  
- **Y-axis:** Number of incidents created in the week.

**What it shows in your data:** The busiest week starts **{pd.to_datetime(peak_week['created_time']).strftime('%d/%m/%Y')}** with **{int(peak_week['count'])} tickets**,  
the quietest has **{int(low_week['count'])} tickets**. Average weekly level is **{avg_weekly:.1f} tickets/week**.

Overall, rising bars indicate **demand exceeding capacity** (backlog risk); flat or falling bars indicate **catch-up and stabilization**.

**How to read it operationally:**  
1) **Peaks:** Pre-position staff, refine change windows, and tune intake controls.  
2) **Plateaus:** Institutionalize controls to hold throughput.  
3) **Downswings:** Confirm which actions reduced load and preserve them.  
4) **Mix:** Pair with SLA outcomes to ensure high-impact weeks don’t drive breaches.

**Why this matters:** Weekly patterns enable **capacity planning** and budget alignment—anticipating surges preserves SLA and CSAT.
                    """)

                # === Graph 3: Monthly Trend ===
                if month.empty:
                    st.info("No monthly trend data to display.")
                else:
                    fig3 = px.area(
                        month, x="created_time", y="count",
                        title="Monthly Incident Volume Trend",
                        labels={"created_time": "Month", "count": "Incident Count"}
                    )
                    st.plotly_chart(fig3, use_container_width=True)

                    # --- Analysis for Monthly ---
                    st.markdown("#### Monthly Trend Analysis")
                    peak_month = month.loc[month["count"].idxmax()]
                    low_month = month.loc[month["count"].idxmin()]
                    avg_month = month["count"].mean()
                    st.write(f"""
**What this graph is:** An area chart showing **monthly incident volume** (long-horizon demand trend).  
- **X-axis:** Calendar month.  
- **Y-axis:** Number of incidents per month.

**What it shows in your data:** Peak month begins **{pd.to_datetime(peak_month['created_time']).strftime('%B %Y')}** with **{int(peak_month['count'])} tickets**;  
the lowest month records **{int(low_month['count'])} tickets**. Average monthly level is **{avg_month:.1f} tickets/month**.

Overall, a rising curve indicates **structural demand growth** (capacity/cost pressure); a flat or falling curve indicates **stabilization**.

**How to read it operationally:**  
1) **Peaks:** Plan budgets, hiring, and automation to offset sustained growth.  
2) **Plateaus:** Lock in process controls and monitor drift.  
3) **Downswings:** Validate which initiatives produced durable reduction.  
4) **Mix:** Map against deployments/seasonality to attribute changes.

**Why this matters:** Monthly trends inform **strategic planning**—resource mix, tooling investments, and risk controls that keep cost and SLA in check.
                    """)

                # === CIO Table (Temporal Trend Insights) ===
                # Only build if the necessary stats exist
                if not week.empty and not day.empty and not month.empty:
                    cio_1 = {
                        "cost": dedent(f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Align staffing to **weekly peaks** | **Phase 1 – Quantify Gap:** We calculate the difference between the busiest week (**{int(peak_week['count'])}**) and the average week (**{avg_weekly:.1f}**) so leadership sees the exact shortfall that creates overtime and backlog. We also convert this gap into hours using average handling time to size capacity needs. <br><br> **Phase 2 – Re-roster:** We reallocate overlaps and break coverage into the peak weeks so more analysts are online precisely when demand materializes rather than spreading coverage thin across quiet weeks. <br><br> **Phase 3 – Review:** We reassess monthly and tune rosters as the peak-to-mean spread moves, ensuring the plan follows the latest demand rather than last quarter’s pattern. | - This reduces overtime spend because additional hours are scheduled as standard time instead of emergency after-hours. <br><br> - This stabilizes service quality because staffing is aligned to the real weekly load rather than historical guesses. <br><br> - This lowers burnout and attrition risk because teams no longer sprint every peak week without planned cover. <br><br> - This improves predictability for finance because cost per incident stays consistent even when volume spikes. | **Savings** = (**{int(peak_week['count'])}** − **{avg_weekly:.1f}**) × Avg handling time × Hourly rate. | Weekly bars show the max week starting **{pd.to_datetime(peak_week['created_time']).strftime('%d/%m/%Y')}** at **{int(peak_week['count'])}** vs average **{avg_weekly:.1f}**. |
| Automate **daily repeaters** | **Phase 1 – Identify Top Patterns:** We mine the peak day to find categories and subcategories that repeat frequently and are safe to automate with validations and guardrails. <br><br> **Phase 2 – Script/Auto-resolve:** We implement guided forms or bots that capture required data, perform checks, and resolve or pre-triage with minimal human touch. <br><br> **Phase 3 – Scale:** We expand automation to adjacent variants that repeat on other days, turning the highest-frequency workload into self-service over time. | - This frees analysts to work complex tickets because routine items close without manual effort. <br><br> - This lowers unit cost on high-frequency categories because resolution effort per ticket drops. <br><br> - This absorbs peak-day surges without adding headcount because automation scales instantly. <br><br> - This improves consistency because automated flows apply the same checks every time. | **Savings** = (# automated tickets on peak day × Avg handling mins ÷ 60 × Hourly rate). Use peak day **{int(peak_day['count'])}** as the target cohort. | Daily line peaks on **{pd.to_datetime(peak_day['created_time']).strftime('%d/%m/%Y')}** with **{int(peak_day['count'])}** tickets—ideal automation payload. |
| Schedule maintenance in **quiet months** | **Phase 1 – Pick Windows:** We choose the lowest month (**{int(low_month['count'])}**) as preferred windows for patching, upgrades, and housekeeping to minimize user impact. <br><br> **Phase 2 – Batch Changes:** We bundle related changes together so testing, communications, and backout plans are handled once rather than repeatedly. <br><br> **Phase 3 – Guardrails:** We freeze major or risky changes near the peak month to avoid stacking change risk on top of high demand. | - This reduces incident side effects because risky changes happen when queues are shallow and recovery bandwidth is high. <br><br> - This lowers user disruption because maintenance avoids known busy periods. <br><br> - This improves engineer utilization because skilled time is spent on planned work instead of firefighting. <br><br> - This prevents surge-on-surge costs by separating demand peaks from change windows. | **Cost avoided** = (Incidents typically triggered by changes × Avg cost per ticket) anchored to low month **{pd.to_datetime(low_month['created_time']).strftime('%B %Y')}**. | Monthly area shows trough at **{int(low_month['count'])}** vs peak **{int(peak_month['count'])}** in **{pd.to_datetime(peak_month['created_time']).strftime('%B %Y')}**. |
| Forecast volume for budget lock-in | **Phase 1 – Model:** We fit weekly and monthly trends with simple seasonality so leaders get a forward view of expected tickets and required capacity. <br><br> **Phase 2 – Commit:** We pre-book contingent hours or vendor capacity for peak months to lock in lower rates and guaranteed cover. <br><br> **Phase 3 – Calibrate:** We update quarterly as data shifts so the budget and capacity plan stays synchronized with reality. | - This prevents surprise spend because peaks are anticipated and funded in advance. <br><br> - This secures capacity at better commercial terms because volume is committed before crunch time. <br><br> - This accelerates approvals because finance sees a defensible forecast with clear assumptions. <br><br> - This improves backlog control because coverage is ready before peaks arrive. | **Efficiency gain** = (Backlog avoided × Avg resolution hours × Hourly rate) using average **{avg_month:.1f}** vs peak **{int(peak_month['count'])}** to size avoided backlog. | Weekly and monthly graphs display repeatable cycles suitable for forecasting. |
| Retire/scale down underused services | **Phase 1 – Detect:** We flag services associated with persistently low monthly incidents and validate whether they warrant full support tiers. <br><br> **Phase 2 – Verify:** We compare usage and business value against support burden to confirm candidates for rationalization. <br><br> **Phase 3 – Act:** We decommission or reduce tiers and redeploy budget where it drives greater impact. | - This cuts maintenance and licensing costs where the value does not justify full support. <br><br> - This reduces on-call exposure because fewer low-value services require coverage. <br><br> - This simplifies the support portfolio which lowers cognitive load for agents. <br><br> - This redirects spend to higher-impact capabilities that improve outcomes. | **Cost reduction** = (Service overhead × Utilization delta) anchored to months near **{int(low_month['count'])}**. | Flat/low monthly segments flag candidates for rationalization. |
"""),
                        "performance": dedent(f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Dynamic surge playbook for **daily spikes** | **Phase 1 – Triggers:** We set a statistical trigger at μ + 2σ for daily volume so surge actions only fire on true spikes rather than noise. <br><br> **Phase 2 – Actions:** We enable auto-triage rules, short-term staff overlaps, and fast-lanes for SLA risks so throughput stays above intake on the day. <br><br> **Phase 3 – Audit:** We compare spike-day MTTR and closures to baseline to refine actions and keep only what moved the needle. | - This keeps throughput at or above intake during spikes which prevents backlog jumps. <br><br> - This compresses recovery time because the queue does not balloon on peak days. <br><br> - This reduces breach clusters since at-risk items are routed through fast-lanes proactively. <br><br> - This avoids blanket overtime by using targeted, data-driven surges. | **Performance gain** = (Δ resolved on spike days × SLA value). Use spike **{int(peak_day['count'])}** vs average **{avg_daily:.1f}** to quantify. | Daily line shows sharp crest on **{pd.to_datetime(peak_day['created_time']).strftime('%d/%m/%Y')}**. |
| Weekly change-window tuning | **Phase 1 – Map:** We overlay the change calendar onto weekly bars to see which change windows correlate with volume spikes. <br><br> **Phase 2 – Freeze/Ramp:** We restrict risky changes before and within the peak week and shift them into quieter weeks where recovery is safer. <br><br> **Phase 3 – Verify:** We track post-change incident patterns to confirm fewer change-induced spikes. | - This reduces change-induced incidents because timing avoids known hot weeks. <br><br> - This stabilizes weekly throughput by preventing preventable shocks. <br><br> - This increases on-time performance in busy weeks because capacity is focused on user demand. <br><br> - This improves CAB credibility with evidence-based scheduling. | **Penalty avoided** = (Breaches prevented × Penalty per breach) using weeks near **{int(peak_week['count'])}**. | Busiest week (**{int(peak_week['count'])}**) is a high-risk change window. |
| Monthly capacity & SLA banding | **Phase 1 – Band Targets:** We publish slightly looser SLA bands for the peak month with transparent comms and tighter bands for trough months. <br><br> **Phase 2 – Staff Fit:** We align rosters and specialist cover with the month’s expected level to match promise to capacity. <br><br> **Phase 3 – Monitor:** We bring the peak month back toward baseline by iterating staffing and automation until the variance shrinks. | - This reduces breach clusters by matching targets to reality instead of wishful thinking. <br><br> - This improves fairness because expectations are explicit and consistent. <br><br> - This reduces escalations since users know what to expect during peak periods. <br><br> - This supports continuous improvement by tracking how the gap closes over time. | **SLA uplift value** = (Δ SLA % × Tickets in **{pd.to_datetime(peak_month['created_time']).strftime('%B %Y')}**). | Peak month **{int(peak_month['count'])}** vs average **{avg_month:.1f}** shows structural strain. |
| Post-peak recovery sprints | **Phase 1 – Identify:** We select the first two weeks after the peak month to run short, focused burn-down sprints aimed at aged items. <br><br> **Phase 2 – Swarm:** We assign senior owners to unblock and close the highest-risk tickets first to reset queues quickly. <br><br> **Phase 3 – Normalize:** We exit the sprint once backlog stabilizes and move back to steady-state operations. | - This burns down aging quickly so SLA risk drops before the next cycle. <br><br> - This protects upcoming windows because the queue is reset to a manageable level. <br><br> - This improves team morale because visible progress follows a heavy month. <br><br> - This shortens average cycle time by clearing long-stalled items. | **Hours saved** = (Backlog avoided × Avg resolution hours). Use post-peak trajectory against peak **{int(peak_month['count'])}**. | Monthly curve’s descent phase is the best window for recovery sprints. |
| Daily root-cause flash reviews | **Phase 1 – Snap RCA:** We review the top categories from the peak day and capture one-page RCAs that identify failure points and quick fixes. <br><br> **Phase 2 – Micro-fixes:** We push KB patches and form validations within 24–48 hours so the next spike sees fewer repeats. <br><br> **Phase 3 – Track:** We watch next-day volume in those categories to confirm the fix worked and iterate until variance flattens. | - This creates a fast learning loop that prevents the same spike drivers from repeating. <br><br> - This flattens daily variance which makes staffing and SLA performance easier to manage. <br><br> - This improves first-time-right by addressing data quality and common misroutes. <br><br> - This reduces analyst frustration because recurring issues are systematically removed. | **Benefit** = (Δ daily count from **{int(peak_day['count'])}** toward **{avg_daily:.1f}** × Avg handling time). | Peak vs mean frames clear improvement target. |
"""),
                        "satisfaction": dedent(f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Peak-period proactive comms | **Phase 1 – Calendarized Notices:** We publish expected delays for the specific weeks and months above baseline so users plan around busy periods. <br><br> **Phase 2 – ETAs & Self-help:** We include realistic ETAs and link to self-service options so users can resolve common issues quickly. <br><br> **Phase 3 – Measure:** We compare complaint and deflection metrics before and after the notices to verify impact. | - This reduces “any update” inquiries because users know timelines in advance. <br><br> - This lowers escalation pressure because expectations are set to reality. <br><br> - This sustains CSAT during peaks because transparency reduces frustration. <br><br> - This increases self-resolution because alternatives are clear and timely. | **Value** = (Complaints avoided × Handling cost) anchored to peak week **{int(peak_week['count'])}** and peak month **{int(peak_month['count'])}**. | Weekly/monthly peaks are the precise periods to inform customers. |
| VIP fast-lane during peaks | **Phase 1 – Identify:** We define the VIP cohort and the thresholds that trigger priority handling during peak months. <br><br> **Phase 2 – Auto-escalate:** We auto-assign senior ownership when VIP tickets approach risk so action happens before a breach. <br><br> **Phase 3 – Report:** We publish VIP breach and save metrics by month to prove protection. | - This protects key relationships by shortening wait time when the system is most stressed. <br><br> - This concentrates expert talent where business impact is highest. <br><br> - This reduces churn risk because strategic users get predictable, high-touch handling. <br><br> - This creates clear accountability because ownership is explicit and timely. | **Retention value** = (# VIP tickets in **{pd.to_datetime(peak_month['created_time']).strftime('%B %Y')}** × Lifetime value). | Peak month creates VIP risk unless prioritized. |
| Self-service boosters on spike days | **Phase 1 – Spotlight:** We promote top FAQs and guided flows in the portal on predicted spike days so users find answers quickly. <br><br> **Phase 2 – Nudge:** We add inline hints at ticket creation to reduce duplicates and misroutes when queues are longest. <br><br> **Phase 3 – Iterate:** We keep the flows that show the highest deflection and retire low performers. | - This deflects simple requests at the moment demand is highest which shortens queues. <br><br> - This improves perceived responsiveness because users can self-solve quickly. <br><br> - This reduces handle time for agents by eliminating avoidable triage. <br><br> - This increases portal engagement which compounds future deflection. | **Deflection value** = (# self-resolved on **{pd.to_datetime(peak_day['created_time']).strftime('%d/%m/%Y')}** × Avg ticket cost). | Daily spike pinpoints when self-service matters most. |
| “Trend wins” reporting | **Phase 1 – Publish:** We show the monthly decline from peak to current levels and call out the exact actions taken. <br><br> **Phase 2 – Attribute:** We connect improvements to roster moves and automation so stakeholders see cause and effect. <br><br> **Phase 3 – Sustain:** We keep a monthly cadence so momentum is visible and durable. | - This builds trust because stakeholders see transparent progress against peaks. <br><br> - This reduces inquiry noise because updates answer common status questions. <br><br> - This reinforces adoption of effective changes by showing measurable results. <br><br> - This aligns teams around what is working so effort is not diluted. | **Savings** = (# inquiries avoided × Cost per inquiry) as monthly counts trend from **{int(peak_month['count'])}** toward **{avg_month:.1f}**. | Area chart makes improvements visible to non-technical stakeholders. |
| Priority-aware messaging | **Phase 1 – Templates:** We create different ETAs by priority during peak weeks so critical work communicates tighter windows. <br><br> **Phase 2 – Trigger:** We auto-notify when risk rises so users get updates before they need to ask. <br><br> **Phase 3 – Review:** We monitor CSAT and breach outcomes by priority band and refine the wording and cadence. | - This protects high-impact users because their communications reflect urgency and risk. <br><br> - This lowers frustration for critical teams by providing timely, relevant updates. <br><br> - This reduces escalations by addressing uncertainty proactively. <br><br> - This improves perception of fairness because rules are clear and consistent. | **Value** = (Escalations avoided × Avg escalation cost) in weeks around **{pd.to_datetime(peak_week['created_time']).strftime('%d/%m/%Y')}**. | Weekly/peak evidence shows when priority-aware comms are needed. |
""")
                    }
                    render_cio_tables("Temporal Trend Insights", cio_1)

    # ---------------------- 6b ----------------------
    with st.expander("📌 Seasonal / Recurring Patterns"):
        if "created_time" not in df_filtered.columns:
            st.info("Seasonality requires 'created_time'.")
            return

        df_filtered = df_filtered.copy()
        df_filtered["created_time"] = pd.to_datetime(df_filtered["created_time"], errors="coerce")
        base = df_filtered.dropna(subset=["created_time"])
        if base.empty:
            st.info("No valid dates in 'created_time' to compute seasonality.")
            return

        heat = base.copy()
        heat["Weekday"] = heat["created_time"].dt.day_name()
        heat["WeekOfMonth"] = ((heat["created_time"].dt.day - 1) // 7 + 1).astype(int)
        pivot = heat.pivot_table(index="Weekday", columns="WeekOfMonth", values="created_time", aggfunc="count").fillna(0)

        if pivot.empty or pivot.values.sum() == 0:
            st.info("No seasonality signal available to build the heatmap.")
            return

        # ---- seasonal metrics for evidence/cost calcs ----
        hot_val = int(pivot.values.max())
        cold_val = int(pivot.values.min())
        hot_idx = divmod(pivot.values.argmax(), pivot.values.shape[1])  # (row, col)
        cold_idx = divmod(pivot.values.argmin(), pivot.values.shape[1])
        hot_weekday = str(pivot.index[hot_idx[0]])
        hot_wom = int(pivot.columns[hot_idx[1]])
        cold_weekday = str(pivot.index[cold_idx[0]])
        cold_wom = int(pivot.columns[cold_idx[1]])

        weekday_avg = pivot.mean(axis=1).sort_values(ascending=False)
        hottest_row = weekday_avg.index[0]
        hottest_row_avg = float(weekday_avg.iloc[0])
        coolest_row = weekday_avg.index[-1]
        coolest_row_avg = float(weekday_avg.iloc[-1])

        fig = go.Figure(data=go.Heatmap(
            z=pivot.values,
            x=[f"W{c}" for c in pivot.columns],
            y=pivot.index,
            coloraxis="coloraxis"
        ))
        fig.update_layout(title="Seasonal Heatmap: Weekday vs. Week-of-Month", coloraxis_colorscale="Viridis")
        st.plotly_chart(fig, use_container_width=True)

        # --- Analysis for Heatmap ---
        st.markdown("### Analysis")
        st.write(f"""
**What this graph is:** A heatmap showing **incident concentration by weekday vs week-of-month**.  
- **X-axis:** Week of month (W1–W5).  
- **Y-axis:** Day of week.

**What it shows in your data:** Darker cells indicate **recurring hot periods** (higher incident counts), lighter cells show calmer windows.

Overall, persistent hot cells signal **predictable cyclical demand**—prime targets for staffing alignment, change timing, and automation.

**How to read it operationally:**  
1) **Peaks:** Avoid risky changes; add surge capacity in the hot cells.  
2) **Plateaus:** Standardize steady-state playbooks for those windows.  
3) **Downswings:** Schedule maintenance and training in cooler cells.  
4) **Mix:** Cross-reference with category/priority to protect critical services during hot periods.

**Why this matters:** Seasonality insights enable **precision scheduling**—reducing overtime, preventing breaches, and improving user experience when it matters most.
        """)

        # === CIO Table (Seasonality Insights) ===
        cio_2 = {
            "cost": dedent(f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Preventive maintenance in **cool cells** | **Phase 1 – Select Windows:** We choose **{cold_weekday} W{cold_wom}** (≈ **{cold_val}** incidents) as preferred maintenance slots so user impact is minimized. <br><br> **Phase 2 – Batch:** We bundle related work so testing, comms, and backout plans are executed once rather than multiple times. <br><br> **Phase 3 – Guard:** We restrict risky work from hot cells to prevent stacking change risk onto demand peaks. | - This reduces change-related incidents because work happens when queues are light and recovery capacity is high. <br><br> - This lowers reactive labor since fewer changes collide with busy periods. <br><br> - This improves user experience because downtime aligns with quieter operational windows. <br><br> - This increases engineer efficiency because preparation and validation are consolidated. | **Cost avoided** = (Incidents typically triggered by changes × Avg cost per ticket) anchored to cool cell **{cold_weekday} W{cold_wom}**. | Heatmap shows coolest cell **{cold_weekday} W{cold_wom}** at **{cold_val}**, ideal maintenance window. |
| Automate **month-end**/hot-cell workloads | **Phase 1 – Identify:** We pinpoint repeating requests concentrated in **{hot_weekday} W{hot_wom}** that have stable inputs and predictable outcomes. <br><br> **Phase 2 – Script/Forms:** We build guided forms and auto-resolution scripts with validations and rollbacks to handle these cases safely. <br><br> **Phase 3 – Scale:** We extend coverage to adjacent hot cells and categories as data proves reliability. | - This cuts analyst minutes at predictable spikes because simple tasks are offloaded to automation. <br><br> - This prevents queues from forming at the same time every month by absorbing volume automatically. <br><br> - This avoids headcount increases by scaling software rather than people. <br><br> - This improves quality because rules enforce complete and correct inputs. | **Savings** = (Automated cases in hot cells × Avg handling mins ÷ 60 × Hourly rate). Use hot cell volume **{hot_val}** to size. | Hottest heatmap cell **{hot_weekday} W{hot_wom}** = **{hot_val}** incidents. |
| Weekday-intensity staffing | **Phase 1 – Profile:** We rank weekday averages such as **{hottest_row} ≈ {hottest_row_avg:.1f}** and **{coolest_row} ≈ {coolest_row_avg:.1f}** so the team sees the true rhythm of demand. <br><br> **Phase 2 – Roster:** We add overlaps on the top two weekdays to keep first-response and closure rates steady. <br><br> **Phase 3 – Iterate:** We reevaluate monthly to keep the roster aligned with current patterns. | - This reduces overtime on hot days because capacity is planned rather than improvised. <br><br> - This reduces idle time on cool days because coverage is right-sized. <br><br> - This improves first-response times when users are most active. <br><br> - This smooths throughput which stabilizes SLA outcomes week to week. | **Cost reduction** = (Overtime hours avoided × Hourly rate) sized by (**{hottest_row_avg:.1f}** − **{coolest_row_avg:.1f}**) incidents/day spread. | Horizontal hot rows corroborate weekday intensity differences. |
| Intake quality gates in hot cells | **Phase 1 – Form Rules:** We enforce mandatory fields and smart validations in hot windows so submissions are complete and correctly routed. <br><br> **Phase 2 – Self-help:** We add inline hints and KB links to deflect common errors and duplicates before submission. <br><br> **Phase 3 – Audit:** We track drops in duplicates and misroutes and refine rules for the busiest cells. | - This reduces low-quality tickets when the queue is under the most pressure. <br><br> - This lowers triage minutes because agents deal with better-formed requests. <br><br> - This increases first-time-right which shortens overall resolution time. <br><br> - This reduces user frustration because fewer tickets bounce between teams. | **Savings** = (Duplicates prevented × Triage mins × Rate) targeted to **{hot_weekday} W{hot_wom}**. | Hot cell concentration pinpoints when intake quality matters most. |
"""),
            "performance": dedent(f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| SLA fast-lane in hot cells | **Phase 1 – Thresholds:** We lower T-1 and T-0 timers during **{hot_weekday} W{hot_wom}** so risk surfaces earlier. <br><br> **Phase 2 – Auto-escalate:** We route at-risk items to senior owners with authority to unblock quickly. <br><br> **Phase 3 – Review:** We measure breach deltas per hot cell and keep only the escalations that deliver results. | - This reduces breach clusters by moving the riskiest work faster during predictable peaks. <br><br> - This increases resilience because senior owners absorb complex cases before deadlines. <br><br> - This shortens recovery time after peaks by preventing avoidable overruns. <br><br> - This raises confidence among stakeholders who see fewer surprises. | **SLA value** = (Breaches avoided in hot cells × Penalty per breach). | Hottest cell **{hot_weekday} W{hot_wom}** = **{hot_val}** incidents where SLA risk concentrates. |
| Staggered shifts for recurrent peaks | **Phase 1 – Design:** We engineer small overlaps on **{hottest_row}** and the second-hottest weekday so coverage matches real demand curves. <br><br> **Phase 2 – Pilot:** We run two pilot cycles to confirm queue length and SLA improvements. <br><br> **Phase 3 – Scale:** We adopt the pattern if metrics improve and sunset it if they do not. | - This smooths throughput by adding capacity precisely where it bites. <br><br> - This shortens queues in predictable hotspots without permanent headcount. <br><br> - This reduces firefighting and context switching for analysts. <br><br> - This improves adherence because schedules feel fair and data-driven. | **Gain** = (Δ throughput × Hours) indexed to (**{hottest_row_avg:.1f}** vs **{coolest_row_avg:.1f}**) incident spread. | Heatmap rows show systematic weekday load differences. |
| Predictive scheduling | **Phase 1 – Model:** We forecast incidents by weekday × week-of-month so supervisors can see load one month ahead. <br><br> **Phase 2 – Plan:** We publish rosters and on-call rotations aligned to the forecast with clear ownership for hot cells. <br><br> **Phase 3 – Calibrate:** We track forecast error and bias and correct parameters so schedules stay accurate across seasons. | - This stabilizes performance because people and skills are in place before demand arrives. <br><br> - This reduces surprises that cause last-minute overtime and service degradation. <br><br> - This improves team morale because schedules are predictable and justified by data. <br><br> - This increases adherence and accountability because expectations are explicit. | **Benefit** = (Productivity gain × Avg ticket value) during **{hot_weekday} W{hot_wom}** windows. | Recurring hot cells validate predictable demand suitable for scheduling. |
"""),
            "satisfaction": dedent(f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Calendarized user comms for hot cells | **Phase 1 – Announce:** We publish busy windows like **{hot_weekday} W{hot_wom}** and explain what users should expect and how to get help faster. <br><br> **Phase 2 – Remind:** We send day-before reminders with links to self-help and tips to reduce avoidable tickets. <br><br> **Phase 3 – Measure:** We compare complaint and deflection changes to confirm value and tune content. | - This lowers complaint volume during known peaks because users understand the context and options. <br><br> - This reduces status checks because answers are provided proactively. <br><br> - This improves perceived transparency which strengthens trust in support. <br><br> - This improves channel fit as more users take the fastest path for simple issues. | **Value** = (Complaints avoided × Handling cost) tied to **{hot_val}** incidents in the hot cell. | Darkest heatmap cell indicates highest risk without expectation setting. |
| Pre-peak enablement | **Phase 1 – Train Users:** We publish short guides and videos in the week before hot cells so common tasks are self-served. <br><br> **Phase 2 – Promote Self-Service:** We surface the most effective flows prominently in the portal and ticket forms. <br><br> **Phase 3 – Iterate:** We keep content that deflects well and retire the rest so the library stays sharp. | - This enables users to self-solve frequent issues which reduces inbound volume at the worst times. <br><br> - This improves user confidence because guidance is easy to find and follow. <br><br> - This frees analysts to focus on complex incidents where expertise matters most. <br><br> - This increases portal adoption which compounds future deflection benefits. | **Cost avoided** = (# prevented tickets in hot cells × Avg ticket cost). | Concentrated hot zones show repeatable, coachable demand. |
| Transparent seasonality reports | **Phase 1 – Share Rhythm:** We send a monthly memo with hot and cool windows and the actions we are taking so stakeholders can plan dependencies. <br><br> **Phase 2 – Attribute:** We tie improvements to staffing and automation so people see which levers worked. <br><br> **Phase 3 – Feedback:** We gather input to refine next month’s plan and address blind spots. | - This builds trust and patience during peaks because the plan is visible and credible. <br><br> - This reduces escalation reflex because stakeholders know what is being done and why. <br><br> - This aligns business planning with support reality which reduces last-minute friction. <br><br> - This fosters collaborative problem solving across teams. | **Retention value** = (# satisfied stakeholders × Avg revenue impact). | Weekday×WOM pattern demonstrates mature operational awareness. |
""")
        }

        # ✅ Render the Seasonality CIO tables (previously missing)
        render_cio_tables("Seasonality Insights", cio_2)
