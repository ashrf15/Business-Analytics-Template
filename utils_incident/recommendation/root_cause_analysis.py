import streamlit as st
import pandas as pd
import plotly.express as px

# 🔹 Helper to render CIO tables
def render_cio_tables(title, cio_data):
    st.subheader(title)
    with st.expander("Cost Reduction"):
        st.markdown(cio_data["cost"], unsafe_allow_html=True)
    with st.expander("Performance Improvement"):
        st.markdown(cio_data["performance"], unsafe_allow_html=True)
    with st.expander("Customer Satisfaction Improvement"):
        st.markdown(cio_data["satisfaction"], unsafe_allow_html=True)

def root_cause_analysis(df_filtered):
    # ---------------------- 5a ----------------------
    with st.expander("📌 Common Root Causes (Closure Codes/Comments)"):
        proxy_col = None
        for c in ["request_closure_code", "request_closure_comments"]:
            if c in df_filtered.columns:
                proxy_col = c
                break

        if proxy_col:
            ser = df_filtered[proxy_col].fillna("Unspecified").astype(str).str.strip()
            counts = ser.value_counts().reset_index()
            counts.columns = ["Root Cause (Proxy)", "count"]
            fig = px.bar(counts.head(20), x="Root Cause (Proxy)", y="count", title="Top Root Causes (Proxy)", text="count")
            fig.update_traces(textposition="outside")
            st.plotly_chart(fig, use_container_width=True)

            # =================== ANALYSIS ===================
            st.markdown("### Analysis")
            if not counts.empty:
                total_cases = counts["count"].sum()
                top = counts.iloc[0]
                top_cause = top["Root Cause (Proxy)"]
                top_count = top["count"]
                share = (top_count / total_cases * 100) if total_cases > 0 else 0

                lowest = counts.iloc[-1]
                low_cause = lowest["Root Cause (Proxy)"]
                low_count = lowest["count"]

                st.write(f"""
**What this graph is:** A bar chart showing **root cause distribution (proxy from closure codes/comments)**.  
- **X-axis:** Root cause categories.  
- **Y-axis:** Incident count per category.

**What it shows in your data:** The top cause is **{top_cause}** with **{top_count:,} incidents** (**{share:.1f}%** of all recorded causes),  
while the lowest is **{low_cause}** with **{low_count:,} incidents** (total analyzed = **{total_cases:,}**).

Overall, a steep drop from the first bar to the rest indicates a **Pareto pattern**—a few causes create most incidents.

**How to read it operationally:**  
1) **Peaks:** Prioritize permanent fixes and problem records for the top 1–3 causes.  
2) **Plateaus:** Standardize documentation/categorization to keep classification clean.  
3) **Downswings:** Validate which corrective actions (KB, automation, process) reduced recurrence.  
4) **Mix:** Pair with priority/impact to ensure high-business-impact causes are addressed first.

**Why this matters:** Root causes are **cost and risk multipliers**. Eliminating the dominant few cuts repeat workload, improves stability, and protects SLA/CSAT.
                """)

                # =================== CIO TABLE ===================
                cio = {
    "cost": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Permanent fix for dominant root cause (**{top_cause}**) | **Phase 1 – Deep RCA:** We conduct a structured root-cause analysis that maps the end-to-end failure chain, the systems and teams involved, and the specific triggers that make **{top_cause}** recur. We document where detection failed, where controls were weak, and what technical or procedural gaps exist. <br><br> **Phase 2 – Design & Deploy Fix:** We implement a targeted change such as a configuration update, a code patch, or a policy control with a clear rollback plan and observable telemetry. The deployment follows change management and includes smoke tests to validate stability. <br><br> **Phase 3 – Verify & Lock:** We track post-fix incident volume for multiple cycles, compare against the pre-fix baseline, and convert the fix into a standard if the reduction sustains. We then close the problem record with learnings and updated controls. | - It eliminates a large portion of repeat work which reduces total analyst hours required for day-to-day operations. <br><br> - It lowers overtime exposure during demand spikes because the biggest source of noise has been removed from the system. <br><br> - It stabilizes operations around a smaller baseline which improves forecasting accuracy and resource planning. | **Avoidable Cost** = **{top_count}** incidents × Avg Handling Time × Hourly Rate. | Bar chart shows **{top_cause}** contributes **{share:.1f}%** of **{total_cases}** recorded causes—largest single reduction lever. |
| Automation for repetitive human errors | **Phase 1 – Identify Triggers:** We analyze the top categories for manual steps such as data entry, toggles, or form selections that frequently lead to mistakes and repeated tickets. We capture the exact error patterns and their business impact. <br><br> **Phase 2 – Script/Guard:** We add pre-checks, default values, and guided flows that prevent errors at the source or automatically correct common misconfigurations before they escalate. <br><br> **Phase 3 – Telemetry:** We log every auto-fix hit and miss so we can expand safe coverage and quickly disable rules that create noise. | - It cuts repeated manual touches which releases capacity for complex incidents that truly require expertise. <br><br> - It prevents inbound volume generated by avoidable mistakes so the queue grows slower and stays more predictable. <br><br> - It reduces handling time variance because automation produces consistent outcomes across shifts and teams. | **Savings** = (# Automated Cases × Avg Handling Time). Use repeated labels under the top bars as the target cohort. | Recurrent human-error descriptors cluster near top categories in the bar chart. |
| Closure code hygiene (reduce “Unspecified”) | **Phase 1 – Taxonomy & Hints:** We define a concise non-overlapping set of closure codes and provide in-UI examples so agents consistently pick the right option without second-guessing. <br><br> **Phase 2 – Enforcement:** We make the closure code mandatory with validation rules and nudge text so low-quality entries are prevented at the point of capture. <br><br> **Phase 3 – Audit:** We review samples weekly, correct drift, and refresh hints so the taxonomy stays accurate as services evolve. | - It accelerates future RCA cycles because incidents are categorized correctly and can be analyzed without rework. <br><br> - It improves prioritization so investment targets the causes that actually drive the most cost and risk. <br><br> - It strengthens governance and reporting which increases leadership confidence in the data. | **Savings** = (Analysis Hours Saved × Hourly Rate). | Presence of **“Unspecified”** inflates data gaps, slowing targeted improvements. |
| Focus problem management on top 3 causes | **Phase 1 – Prioritize:** We open problem records for the top three bars and define clear success metrics for volume and impact reduction. <br><br> **Phase 2 – Cross-Team Actions:** We coordinate infra, application, and service desk owners to implement the combined technical and process fixes required to remove the causes. <br><br> **Phase 3 – Close & Institutionalize:** We confirm sustained reduction, publish updated runbooks and KB articles, and embed controls so the improvement persists. | - It concentrates effort on the few causes that generate most of the work which maximizes return on engineering time. <br><br> - It compresses recurring volume which protects SLA during busy periods and frees capacity for strategic tasks. <br><br> - It improves predictability which helps with staffing and budget planning across quarters. | **Avoided Volume** = (Top3 Share × **{total_cases}**) × Avg Handling Cost. | Pareto pattern: steep drop after first bars proves vital-few concentration. |
    """,
    "performance": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Problem Records for **{top_cause}** and peers | **Phase 1 – Standard Capture:** We document the cause hypothesis, diagnostics, fix plan, and verification steps in a formal problem record so ownership and scope are unambiguous. <br><br> **Phase 2 – Owner & SLA:** We assign an accountable resolver with a realistic SLA for fix delivery and checkpoints to manage risk. <br><br> **Phase 3 – Verify:** We track the reduction in incident count and resolution time against baseline and keep the record open until the improvement is durable. | - It reduces recurrence and mean time to resolve because systemic fixes replace ad-hoc firefighting. <br><br> - It lowers escalations because the same problem does not repeatedly surprise the teams. <br><br> - It smooths operational flow because repeat bottlenecks are removed rather than worked around. | **Time Reduction** = ΔVolume × Avg Resolution Time. | Concentration under **{top_cause}** indicates structured RCA will yield outsized returns. |
| Cross-functional process reviews | **Phase 1 – Map Handoffs:** We visualize approvals, vendor waits, and multi-team steps to locate queues where time is lost repeatedly. <br><br> **Phase 2 – Remove Friction:** We parallelize safe steps, shorten approval paths, and add fast-lanes for standard changes that do not require heavyweight review. <br><br> **Phase 3 – Re-measure:** We compare cycle time and breach rate before and after to confirm compression. | - It shortens end-to-end timelines so fewer tickets age into risk zones. <br><br> - It prevents avoidable breaches by removing recurring waits that offer no value. <br><br> - It improves upstream data quality because process clarity reduces rework and misroutes. | **Savings** = (Time-to-Resolve Reduction × Incident Volume). | High-count categories imply process friction is systemic, not random. |
| KB and first-contact playbooks | **Phase 1 – Author:** We write step-by-step checklists for the top causes with clear diagnostics and decision points so agents can resolve in one pass. <br><br> **Phase 2 – Embed:** We surface these playbooks contextually in forms and macros so they are used by default without searching multiple tools. <br><br> **Phase 3 – Refresh:** We prune and expand content quarterly based on hit rate and resolution time data. | - It increases first contact resolution which removes handoffs and speeds closure. <br><br> - It reduces performance variance between analysts and shifts so outcomes are more predictable. <br><br> - It lowers training time for new hires because proven steps are available inside the workflow. | **Benefit** = (Reduced Resolution Time × Ticket Volume in top causes). | Tall bars = repetitive patterns ideal for standard playbooks. |
    """,
    "satisfaction": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| “We fixed it for good” communications | **Phase 1 – Draft:** We prepare a simple non-technical summary of what failed why it recurred and what has been changed permanently. <br><br> **Phase 2 – Target:** We send the note to the impacted users and stakeholders so they see the connection between pain and the fix. <br><br> **Phase 3 – Track:** We measure complaint and CSAT movement after the announcement to confirm confidence is restored. | - It increases trust because users see accountability and a concrete corrective action. <br><br> - It reduces follow ups because people understand the change and do not chase updates. <br><br> - It improves sentiment after recurring pain points because the outcome is visible and permanent. | **Value** = Complaints Avoided × Avg Handling Cost. | Users affected by **{top_cause}** ( **{top_count}** incidents ) will notice measurable change. |
| Root-cause transparency dashboards | **Phase 1 – Publish:** We provide a trend view of the top causes with the fixes in flight and the expected completion dates. <br><br> **Phase 2 – Update:** We annotate the chart when actions land so progress is visible without a meeting. <br><br> **Phase 3 – Review:** We walk key stakeholders through the dashboard quarterly to align priorities. | - It reduces “what’s going on” inquiries because status is self-serve and current. <br><br> - It sets realistic expectations which lowers frustration during remediation work. <br><br> - It builds credibility because improvements are evidenced in the same chart the users see. | **Savings** = Follow-ups Avoided × Cost per Inquiry. | The chart’s dominant bars are ideal to visualize and report progress. |
| Early-warning comms for predictable spikes | **Phase 1 – Define Triggers:** We list calendar events or system states that reliably precede spikes for the top causes. <br><br> **Phase 2 – Notify:** We inform impacted groups with guidance and ETAs before the window opens to reduce surprise. <br><br> **Phase 3 – Evaluate:** We track ticket deflection and error rates to confirm the messages are preventing incidents. | - It lowers unplanned demand by steering users away from risky actions when risk is highest. <br><br> - It reduces inbound during known-risk windows so the team stays focused on critical work. <br><br> - It improves overall experience because problems feel anticipated rather than reactive. | **Cost Avoided** = Prevented Tickets × Avg Handling Cost. | Dominant/predictable causes are visible in the top of the bar chart. |
    """
}
                render_cio_tables("Root Cause (Proxy)", cio)
            else:
                st.info("No data available for analysis.")
        else:
            st.info("No closure code/comment fields to infer root causes.")

    # ---------------------- 5b ----------------------
    with st.expander("📌 Trends in Incident Types (Service Category)"):
        if {"service_category", "created_time"} <= set(df_filtered.columns):
            df_filtered["created_time"] = pd.to_datetime(df_filtered["created_time"], errors="coerce")
            top5 = df_filtered["service_category"].value_counts().head(5).index.tolist()
            subset = df_filtered[df_filtered["service_category"].isin(top5)].copy()
            subset["Created Day"] = subset["created_time"].dt.to_period("M").astype(str)
            trend = subset.groupby(["Created Day", "service_category"]).size().reset_index(name="count")
            fig = px.line(trend, x="Created Day", y="count", color="service_category", title="Monthly Trend by Top Categories")
            st.plotly_chart(fig, use_container_width=True)

            # =================== ANALYSIS ===================
            st.markdown("### Analysis")
            if not trend.empty:
                total = trend["count"].sum()
                overall_peak = trend.loc[trend["count"].idxmax()]
                overall_low = trend.loc[trend["count"].idxmin()]

                st.write(f"""
**What this graph is:** A multi-series line chart showing **monthly incident volume by top service categories**.  
- **X-axis:** Calendar month.  
- **Y-axis:** Incident count per category.

**What it shows in your data:** The highest single-category peak is **{overall_peak['service_category']}** in **{overall_peak['Created Day']}** with **{overall_peak['count']} incidents**;  
the lowest observed point is **{overall_low['service_category']}** in **{overall_low['Created Day']}** with **{overall_low['count']} incidents** (total points analyzed = **{total}**).

Overall, recurring peaks indicate **seasonal or operational surges**, while troughs indicate **stability or reduced demand**.

**How to read it operationally:**  
1) **Peaks:** Pre-position staff, freeze risky changes, and schedule preventive maintenance one month prior.  
2) **Plateaus:** Standardize steady-state practices and guardrails.  
3) **Downswings:** Validate which interventions (automation, training, routing) lowered volume.  
4) **Mix:** Pair with SLA/breach data to ensure surges don’t trigger contract risk.

**Why this matters:** Anticipating category surges **cuts cost, prevents backlog, and protects SLA/CSAT** by aligning capacity to demand.
                """)

                # =================== CIO TABLE ===================
                cio = {
    "cost": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Preventive actions before peak months | **Phase 1 – Forecast:** We analyze the multi-series trend to flag upcoming peak months by category and set early warning thresholds one period in advance. <br><br> **Phase 2 – Schedule:** We plan preventive maintenance, patching, and capacity housekeeping in the month before the forecasted peak so risk is removed early. <br><br> **Phase 3 – Verify:** We compare month-over-month deltas to confirm that peak height falls and that work shifted from reactive to preventive. | - It reduces unplanned labor because fewer failures occur when underlying issues are addressed before demand spikes. <br><br> - It lowers overtime and weekend interventions because load is flattened into planned windows. <br><br> - It smooths capacity usage which improves agent focus and reduces context switching cost. | **Cost Avoided** = (**{overall_peak['count']}** − baseline_volume) × Avg Handling Cost. | **{overall_peak['service_category']}** peaked at **{overall_peak['count']}** in **{overall_peak['Created Day']}**. |
| Automation for high-volume categories | **Phase 1 – Select:** We prioritize categories that show repeated crests across months because they offer reliable automation payback. <br><br> **Phase 2 – Build:** We implement auto-diagnose and auto-resolve flows or guided forms that gather complete data in one pass. <br><br> **Phase 3 – Scale:** We extend automation to adjacent subtypes once accuracy and safety are validated. | - It cuts recurring manual minutes so the same headcount handles more work during seasonal surges. <br><br> - It stabilizes unit cost because high-volume peaks are absorbed by machines rather than overtime. <br><br> - It improves quality because enriched or auto-fixed tickets enter downstream steps with fewer errors. | **Savings** = automated_cases × Avg Resolution Time × Rate (anchor on peak **{overall_peak['count']}**). | Repeating crests in trend lines indicate ripe automation candidates. |
| Flexible resourcing (shifts/part-time) | **Phase 1 – Identify Windows:** We map the months and weeks where each category peaks so we know exactly when extra coverage is required. <br><br> **Phase 2 – Roster:** We add short overlaps, temporary shifts, or part-time pools to cover the high-risk windows without over-staffing quiet periods. <br><br> **Phase 3 – Tune:** We remove or resize the extra coverage after the peak passes and keep monitoring for drift. | - It minimizes escalations and backlog because capacity matches demand at the time it matters. <br><br> - It reduces emergency overtime because the plan anticipates surges rather than reacting late. <br><br> - It keeps SLAs steadier in busy months which protects credibility and penalties. | **Cost Avoided** = overtime_hours_reduced × Rate (driven by peak **{overall_peak['count']}** vs trough **{overall_low['count']}**). | Clear gap between peak and low months supports flexible capacity. |
| Category-specific intake guardrails | **Phase 1 – Form Enhancements:** We add mandatory fields, validation, and guided prompts for peak categories so requests arrive complete and actionable. <br><br> **Phase 2 – Auto-deflect:** We insert self-help links and quick checks for known issues so simple requests bypass the queue. <br><br> **Phase 3 – Audit:** We monitor duplicate and misroute rates and refine guardrails to keep intake quality high. | - It reduces misroutes and duplicates which lowers triage minutes and rework. <br><br> - It raises first-time-right rates so tickets move faster through the pipeline. <br><br> - It improves reporting accuracy because categories reflect real demand rather than noisy classification. | **Benefit** = duplicates_prevented × triage_minutes × Rate. | Steep month-over-month rises show where intake quality matters most. |
    """,
    "performance": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Change freezes before forecasted spikes | **Phase 1 – Mark Risk Windows:** We tag the weeks preceding forecasted peaks as high-risk windows based on historical surges. <br><br> **Phase 2 – Freeze:** We defer non-urgent changes in those windows so change-induced incidents do not collide with natural peaks. <br><br> **Phase 3 – Backlog Check:** We resume after the peak with a quick backlog and stability check to avoid piling risk. | - It prevents change-driven incidents when capacity is tight which reduces double-hits on service levels. <br><br> - It protects SLA by avoiding unnecessary volatility during known busy periods. <br><br> - It increases operational stability which helps teams stay focused on customer demand. | **Penalty Avoided** = breaches_prevented × penalty_per_breach (use peak month as risk anchor). | Peaks in **{overall_peak['service_category']}**/month suggest heightened change risk. |
| Real-time category monitoring | **Phase 1 – Dashboards:** We build live views that show inflow, outflow, and backlog per category so leaders see pressure building in real time. <br><br> **Phase 2 – Thresholds:** We alert at μ+2σ for each category so interventions start before service levels slip. <br><br> **Phase 3 – Review:** We adjust thresholds weekly based on observed volatility to keep signals meaningful. | - It enables earlier interventions which reduces breach clusters and backlog spikes. <br><br> - It speeds backlog burn because actions happen while queues are still small. <br><br> - It improves week-over-week stability because responses are calibrated to actual variance. | **Efficiency** = improved_closure_rate × category_volume. | Variability across months shows reactive handling—monitoring tightens control. |
| Seasonal spike alerts (ML/heuristics) | **Phase 1 – Train/Calibrate:** We use twelve to eighteen months of history to forecast category surges with simple models or heuristics. <br><br> **Phase 2 – Integrate:** We route alerts into rostering, change governance, and comms so each function adapts proactively. <br><br> **Phase 3 – Evaluate:** We measure forecast error and SLA impact to refine models and rules. | - It reduces response lag when spikes hit because capacity and controls are already in motion. <br><br> - It improves staffing fit which reduces idle time in quiet periods and stress in busy periods. <br><br> - It increases adherence because the system reacts to predicted risk rather than yesterday’s data. | **Cost Saved** = delayed_response_hours_cut × hourly_rate. | Repeated crests imply predictable seasonality that can be forecast. |
    """,
    "satisfaction": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Proactive notices before busy months | **Phase 1 – Draft:** We prepare concise category-specific advisories that explain likely delays and self-service options. <br><br> **Phase 2 – Target:** We send the notices to impacted user groups ahead of the surge so expectations are set before demand arrives. <br><br> **Phase 3 – Measure:** We track complaint volume and contact deflection during the window to confirm value. | - It reduces frustration because users know what to expect and how to get faster outcomes. <br><br> - It lowers inbound during spikes which protects agent focus for high-impact tickets. <br><br> - It improves satisfaction because communication is proactive rather than reactive. | **Value** = complaints_avoided × handling_cost; tie to peak **{overall_peak['Created Day']}**. | Peaks show when user pain concentrates—early comms soften impact. |
| Self-service flows for top categories | **Phase 1 – Map:** We identify the repeatable requests in the top lines and define the steps users can safely complete themselves. <br><br> **Phase 2 – Build:** We provide guided forms and auto-fixes that resolve common issues without an agent. <br><br> **Phase 3 – Iterate:** We expand coverage based on deflection data and user feedback. | - It delivers faster perceived service because simple issues are solved immediately. <br><br> - It reduces queues which improves experience for users with complex problems. <br><br> - It raises CSAT for repeatable issues because resolution is quick and consistent. | **Time Saved** = Avg Response Reduction × category_volume (use peak counts like **{overall_peak['count']}**). | High-frequency categories are ideal for deflection/self-service. |
| Publicize volume reductions | **Phase 1 – Compare:** We produce clear before/after visuals by month that show the drop achieved by interventions. <br><br> **Phase 2 – Share:** We present the results to business stakeholders to reinforce confidence and partnership. <br><br> **Phase 3 – Sustain:** We codify what worked and keep a cadence of updates so improvements persist. | - It builds confidence because stakeholders can see evidence that actions deliver results. <br><br> - It encourages adoption of improved processes which multiplies impact across teams. <br><br> - It lowers chasing contacts because progress is visible without asking for status. | **CSAT Gain** = ΔSatisfaction × impacted_volume. | Visible troughs after interventions show progress worth communicating. |
    """
}

                render_cio_tables("Type Trends", cio)
            else:
                st.info("Not enough category trend data available.")
        else:
            st.info("Need 'Service Category' and 'Created Time' to plot type trends.")

        # ---------------------- 5c ----------------------
    with st.expander("📌 Actions to Prevent Recurring Incidents (Before/After)"):

        # Check necessary fields
        if "created_time" in df_filtered.columns:
            df_filtered["created_time"] = pd.to_datetime(df_filtered["created_time"], errors="coerce")

            # Let user select intervention date
            intervention_date = st.date_input(
                "Select an intervention date to compare incident volume before and after:",
                value=df_filtered["created_time"].min().date() if not df_filtered["created_time"].isna().all() else None,
                min_value=df_filtered["created_time"].min().date() if not df_filtered["created_time"].isna().all() else None,
                max_value=df_filtered["created_time"].max().date() if not df_filtered["created_time"].isna().all() else None
            )

            if pd.notna(intervention_date):
                before_df = df_filtered[df_filtered["created_time"].dt.date < intervention_date]
                after_df = df_filtered[df_filtered["created_time"].dt.date >= intervention_date]

                before_count = len(before_df)
                after_count = len(after_df)

                # Create simple before/after summary
                if before_count > 0 and after_count > 0:
                    compare_df = pd.DataFrame({
                        "Period": ["Before", "After"],
                        "Incident Volume": [before_count, after_count]
                    })

                    fig = px.bar(compare_df, x="Period", y="Incident Volume", text="Incident Volume",
                                 title=f"Incident Volume Before vs. After {intervention_date}")
                    fig.update_traces(textposition="outside")
                    st.plotly_chart(fig, use_container_width=True)

                    # ---------- ANALYSIS ----------
                    st.markdown("### Analysis")
                    change = ((after_count - before_count) / before_count * 100) if before_count > 0 else 0
                    trend = "decrease" if change < 0 else "increase" if change > 0 else "no significant change"

                    st.write(f"""
**What this graph is:** A two-bar comparison showing **incident volume before vs after** the selected intervention date (**{intervention_date}**).  
- **X-axis:** Period (Before, After).  
- **Y-axis:** Total incident volume.

**What it shows in your data:** **Before = {before_count}** and **After = {after_count}**, a **{abs(change):.1f}% {trend}** relative to the chosen date.

Overall, a lower **After** bar suggests successful prevention or demand reduction; a higher **After** bar suggests new demand, reporting shifts, or incomplete adoption.

**How to read it operationally:**  
1) **Peaks (After > Before):** Investigate change side-effects; tighten controls, training, or automation scope.  
2) **Plateaus (After ≈ Before):** Reinforce adoption, expand scope, and monitor leading indicators.  
3) **Downswings (After < Before):** Institutionalize what worked (SOPs, KB, alerts) and track durability.  
4) **Mix:** Segment by category/priority to confirm improvements where business impact is highest.

**Why this matters:** Before/After evidence turns interventions into **measured ROI**—sustained reduction lowers cost, backlog, and breach risk while improving CSAT.
                    """)

                    # ---------- CIO TABLES ----------
                    if min(before_count, after_count) > 1:
                        cio = {
    "cost": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Standardize + automate repetitive steps | **Phase 1 – Identify:** We analyze the “Before” cohort to map the steps that repeat across incidents and quantify their time cost and failure modes. <br><br> **Phase 2 – Automate:** We introduce scripts, structured forms, or auto-approvals where risk is low so repetitive steps are executed quickly and correctly. <br><br> **Phase 3 – Rollout:** We stage the rollout by risk category, monitor success rates, and expand coverage as confidence grows. | - It reduces recurring incident handling cost because low-value steps are executed by systems rather than people. <br><br> - It lowers manual minutes per ticket which improves throughput without increasing headcount. <br><br> - It decreases overtime during surges because automation absorbs load when queues would otherwise expand. | **Cost Reduction** = (**{before_count}** − **{after_count}**) × Avg Cost per Ticket. | Bar chart: **Before = {before_count}**, **After = {after_count}** → **{abs(change):.1f}% {trend}** post **{intervention_date}**. |
| Dynamic resource reallocation | **Phase 1 – Re-roster:** We shift agents away from categories that show proven decline after the intervention so capacity is not stranded. <br><br> **Phase 2 – Re-purpose:** We move freed capacity to unresolved hotspots where demand still exceeds supply. <br><br> **Phase 3 – Track:** We review weekly volume and cost per ticket to ensure the mix remains efficient. | - It prevents idle time by aligning staffing with the new demand pattern after the change. <br><br> - It reduces the need for emergency overtime in hot areas because capacity is moved proactively. <br><br> - It keeps cost per resolved ticket trending down as resources follow value. | **Efficiency Gain** = resource_hours_saved × hourly_rate (sized by delta volume **{before_count - after_count}**). | Lower **After** bar indicates less volume to service after intervention. |
| Preventive maintenance cadence | **Phase 1 – Tune Frequency:** We increase maintenance cadence where the “Before” bar shows chronic load so the underlying causes are addressed regularly. <br><br> **Phase 2 – Align Windows:** We schedule work just before typical peaks to suppress spikes that would otherwise appear. <br><br> **Phase 3 – Validate:** We compare deltas in the next period to confirm the cadence is effective and adjust as needed. | - It avoids reactive fixes that are more expensive and disruptive than planned work. <br><br> - It reduces spikes that trigger breaches and escalations which protects SLOs and SLAs. <br><br> - It creates smoother demand which makes staffing and prioritization simpler. | **Cost Avoided** = reactive_tickets_prevented × handling_cost (anchor on **{before_count}-{after_count}** prevented). | The drop after **{intervention_date}** supports the value of preventive action. |
| Intake quality gates | **Phase 1 – Must-Have Fields:** We enforce the data needed to resolve in one pass so agents do not chase missing details. <br><br> **Phase 2 – Auto-Checks:** We validate environment and asset information at submission to prevent dead-on-arrival tickets. <br><br> **Phase 3 – Audit:** We monitor the decline in poor-quality intake and feed learnings back into forms. | - It reduces duplicates and misroutes which removes waste from the triage process. <br><br> - It shortens time to first meaningful action because tickets arrive complete. <br><br> - It increases first-time-right rates which lowers total cost per incident. | **Savings** = duplicates_prevented × triage_minutes × rate (size using **{before_count}→{after_count}**). | Reduction suggests fewer low-quality tickets entering the flow. |
    """,
    "performance": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| RCA on residual post-intervention incidents | **Phase 1 – Sample:** We analyze the “After” cohort to identify remaining drivers and quantify their contribution to residual demand. <br><br> **Phase 2 – Fix:** We open problem records and deliver targeted technical or process changes for the top residual drivers. <br><br> **Phase 3 – Verify:** We run 30/60/90-day checks to confirm the residual volume continues to fall. | - It improves throughput by removing the small number of blockers that still generate noise. <br><br> - It reduces mean time to resolve because complex cases receive focused engineering. <br><br> - It prevents new backlog formation by addressing the sources that remain after the main intervention. | **Performance Gain** = ΔMTTR × **{after_count}** tickets. | Even after improvement, **{after_count}** cases remain—targeted RCA can compress further. |
| Institutionalize successful changes | **Phase 1 – SOP:** We convert ad-hoc fixes into simple standard operating procedures that are easy to follow. <br><br> **Phase 2 – Train:** We deliver micro-learning to agents so adoption is quick and measurable. <br><br> **Phase 3 – Govern:** We audit adherence and outcomes so the gains are maintained over time. | - It maintains the reduction achieved so performance does not drift back to the old baseline. <br><br> - It lowers variance across shifts and teams because everyone follows the same playbook. <br><br> - It increases predictability which improves planning and stakeholder confidence. | **Value** = avoided_escalations × cost_per_escalation. | The sustained **{abs(change):.1f}% {trend}** indicates practices worth codifying. |
| Post-change performance reviews | **Phase 1 – KPIs:** We track volume, SLA, and MTTR at 30/60/90 days to evaluate the sustainability of the improvement. <br><br> **Phase 2 – Tune:** We adjust staffing, routing, or policies based on the observed performance and any emerging risks. <br><br> **Phase 3 – Iterate:** We close the loop with owners and set the next improvement cycle. | - It drives continuous improvement because each cycle locks in lessons learned. <br><br> - It detects regressions early so corrective action is small and fast. <br><br> - It improves capacity fit because resources shift in line with real demand. | **Benefit** = ΔVolume × ΔSLA × penalty_avoidance. | Before/after delta provides a measurable baseline for the reviews. |
    """,
    "satisfaction": f"""
| Recommendations | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Communicate the improvement | **Phase 1 – Announce:** We share the before and after numbers in a simple visual so users can see the change. <br><br> **Phase 2 – Explain:** We describe what changed operationally and how the new process benefits them in day-to-day usage. <br><br> **Phase 3 – Invite Feedback:** We collect CSAT and suggestions to refine the solution and capture new opportunities. | - It increases trust because progress is transparent and quantified. <br><br> - It reduces complaints because users understand what improved and why. <br><br> - It boosts perception of responsiveness which supports higher CSAT. | **Value** = complaints_avoided × avg_handling_cost; anchor on visible drop (**{before_count}→{after_count}**). | Users see a tangible **{abs(change):.1f}% {trend}** post **{intervention_date}**, reinforcing credibility. |
| Awareness enablement for prevention | **Phase 1 – Educate:** We publish brief tips and FAQs that match the categories showing a reduction so users can avoid common triggers. <br><br> **Phase 2 – Nudge:** We add in-app guidance during risky steps so prevention is timely and contextual. <br><br> **Phase 3 – Measure:** We track deflection and error rates to confirm knowledge is changing behavior. | - It sustains lower demand by helping users avoid the actions that used to create tickets. <br><br> - It equips users with self-service solutions which shortens time to value. <br><br> - It creates a positive feedback loop where fewer incidents free time to improve content further. | **Savings** = avoided_tickets × cost_per_ticket (use **{before_count - after_count}** as initial proxy). | Lower **After** bar suggests user behavior/process improved—keep reinforcing it. |
| Transparent live dashboards | **Phase 1 – Publish:** We provide a rolling thirty-day before/after view so anyone can verify performance without requesting reports. <br><br> **Phase 2 – Annotate:** We mark interventions on the chart to link actions to outcomes and make decisions traceable. <br><br> **Phase 3 – Review:** We hold a monthly stakeholder session to align on next steps and ensure momentum continues. | - It reduces status-check contacts because information is self-serve and current. <br><br> - It builds confidence across teams because impact is visible and attributed. <br><br> - It aligns expectations which lowers friction and escalations. | **Savings** = follow-ups_avoided × handling_cost. | The two-bar gap provides a simple, defensible narrative for progress. |
    """
}

                        render_cio_tables("Before vs After Intervention", cio)
                    else:
                        st.warning("Incident counts are too low to generate meaningful recommendations.")
                else:
                    st.info("Insufficient before/after data to generate a comparison chart.")
            else:
                st.info("Select a valid intervention date to view before/after comparison.")
        else:
            st.info("Column 'created_time' is required to perform before/after comparison.")
