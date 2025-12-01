import streamlit as st
import pandas as pd
import plotly.express as px

# ───────────────── Mesiniaga theme ─────────────────
BLUE_TONES = [
    "#004C99",  # deep brand navy
    "#0066CC",  # strong blue
    "#007ACC",  # azure
    "#3399FF",  # light blue
    "#66B2FF",  # lighter blue
    "#99CCFF",  # pale blue
]
px.defaults.template = "plotly_white"

# 🔹 Helper to render CIO tables
def render_cio_tables(title, cio_data):
    st.subheader(title)
    with st.expander("Cost Reduction"):
        st.markdown(cio_data["cost"], unsafe_allow_html=True)
    with st.expander("Performance Improvement"):
        st.markdown(cio_data["performance"], unsafe_allow_html=True)
    with st.expander("Customer Satisfaction Improvement"):
        st.markdown(cio_data["satisfaction"], unsafe_allow_html=True)


def incident_status(df_filtered):
    # ---------------------- 4a ----------------------
    with st.expander("📌 Current Status of Each Open Incident"):
        # ✅ Create 'is_open' dynamically
        if "is_open" not in df_filtered.columns:
            if "resolved_time" in df_filtered.columns:
                df_filtered["is_open"] = df_filtered["resolved_time"].isna()
            elif "completed_time" in df_filtered.columns:
                df_filtered["is_open"] = df_filtered["completed_time"].isna()
            elif "request_status" in df_filtered.columns:
                df_filtered["is_open"] = ~df_filtered["request_status"].astype(str).str.lower().isin(
                    ["closed", "resolved"]
                )
            else:
                df_filtered["is_open"] = False

        open_df = df_filtered[df_filtered["is_open"]]

        # No open incidents ⇒ no graph/analysis
        if open_df.empty:
            st.info("No open incidents currently. Data is not available, so there will be no analysis.")
        else:
            # Build derived status
            status_cols = []
            if "pending_status" in open_df.columns:
                status_cols.append("pending_status")
            if "on_hold_status" in open_df.columns:
                status_cols.append("on_hold_status")
            if "overdue_status" in open_df.columns:
                status_cols.append("overdue_status")

            if status_cols:
                open_df["derived_status"] = open_df[status_cols].apply(
                    lambda r: next((str(v) for v in r if pd.notna(v) and str(v).strip() != ""), "Open"),
                    axis=1,
                )
            else:
                open_df["derived_status"] = "Open"

            counts = open_df["derived_status"].fillna("Open").value_counts().reset_index()
            counts.columns = ["Status", "count"]

            # If all bars would be zero (defensive), skip analysis
            if counts["count"].sum() == 0:
                st.info("Open status mix has zero counts. Data is not available, so there will be no analysis.")
            else:
                fig = px.bar(
                    counts,
                    x="Status",
                    y="count",
                    title="Open Incidents — Derived Status",
                    text="count",
                    color_discrete_sequence=BLUE_TONES,
                )
                fig.update_traces(textposition="outside")
                st.plotly_chart(fig, use_container_width=True)

                # ------------------- Dynamic Analysis -------------------
                st.markdown("### Analysis")
                total_open = int(counts["count"].sum())
                top = counts.iloc[0]
                top_status = top["Status"]
                top_count = int(top["count"])
                lowest_status = counts.iloc[-1]["Status"]
                lowest_count = int(counts.iloc[-1]["count"])
                share_top = (top_count / max(total_open, 1)) * 100

                st.write(f"""
What this graph is: A bar chart showing the current mix of open incidents by derived status.
                         
X-axis: Status categories (e.g., Pending, On Hold, Overdue, Open).
Y-axis: Count of open tickets.
                         
What it shows in your data:
Total open tickets: {total_open:,}.
Largest status: {top_status} with {top_count:,}.
Smallest status: {lowest_status} with {lowest_count:,}.
{top_status} share of open workload: {share_top:.1f}%.

Overall: Taller bars indicate demand > flow (aging + SLA risk); shorter bars indicate stabilization.

How to read it operationally:
Peaks: Reassign owners, run unblock sprints, and adjust routing where the dominant status accumulates.
Plateaus: Maintain outflow ≥ inflow with explicit next actions and timers to prevent re-accumulation.
Downswings: Validate which interventions (staffing, automation, triage SLAs) actually reduced the pile.
Mix: Always pair with priority and ticket age to keep critical items from being buried.
Why this matters: Status accumulation is operational debt; the higher the tallest bar, the more expensive each day becomes via breaches, escalations, and unhappy users.
                """)

                # ------------------- CIO TABLES -------------------
                cio_1b = None
                if total_open <= 1 or top_count <= 1:
                    st.warning(
                        "📊 The number of open incidents is too low to derive statistically valid insights or recommendations."
                    )
                else:
                    cio_1b = {
    "cost": f"""
| Recommendations | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Automate stale ticket closures | **Phase 1 – Define inactivity rules:** We document explicit inactivity thresholds per status and category, then configure the service desk platform to detect tickets exceeding those thresholds. The rule set includes clear customer messaging and safeguards so legitimate cases are not lost. <br>**Phase 2 – Safe reopen window:** We enable a defined grace period in which users can reopen a ticket with a single click, ensuring that automation does not block valid follow-ups and that context is fully preserved. <br>**Phase 3 – Audit & tune:** We run a monthly audit on a representative sample of auto-closures, compare outcomes against manual closures, and recalibrate thresholds and messages to balance efficiency with service quality. | - This reduces repetitive follow-ups because inactive tickets are closed automatically instead of requiring analysts to chase updates.<br><br>- This lowers the carrying cost of WIP since dormant tickets no longer consume queue space or attention cycles.<br><br>- This frees analyst capacity to address current and complex work which accelerates progress on the active backlog.<br><br>- This maintains customer control through a simple, time-boxed reopen flow that avoids accidental loss of valid requests.<br><br>- This improves governance because periodic audits ensure the automation stays accurate and fair over time.<br><br> | **Savings (h)** ≈ stale_tickets_in_{top_status} × avg_followup_min/60. Use {top_count:,} as the maximum pool for sizing this status. | {top_status} dominates with **{top_count:,}** tickets out of **{total_open:,}**; this is the ripest segment for automation. |
| Streamline inter-department dependencies | **Phase 1 – Structured handoffs:** We standardize inter-team handoffs with a required owner, due date, and data checklist so receiving teams can act immediately without rework. <br>**Phase 2 – Smart reminders:** We set automated nudges to dependent teams at planned intervals and escalate if progress is not recorded, reducing silent stalls. <br>**Phase 3 – SLA alignment:** We map upstream and downstream timers to prevent one team’s delay from silently pushing another team into breach, and we publish visibility of these timers to all stakeholders. | - This cuts idle time during handoffs because tickets arrive complete and actionable for the next team.<br><br>- This reduces coordination overhead as automated reminders replace manual chasing and ad hoc emails.<br><br>- This shortens unblock cycles so fewer tickets sit in pending states and age into breach risk.<br><br>- This improves predictability because cross-team SLAs are synchronized and transparent to everyone involved.<br><br>- This increases accountability since owners and due dates are explicit at every handoff stage.<br><br> | **Time saved (h)** ≈ dependency_cases_in_{top_status} × avg_delay_hours. Use the gap between {top_status}={lowest_count if lowest_count>top_count else top_count:,} vs {lowest_status}={lowest_count:,} as a proxy for imbalance. | The spread between largest (**{top_status}**) and smallest (**{lowest_status}**) bars indicates flow imbalance consistent with dependency drag. |
| Apply SLA timers for each status transition | **Phase 1 – Per-status timers:** We configure timeboxes for each status so the system measures elapsed time in Pending, On Hold, and Overdue states and surfaces aging risk early. <br>**Phase 2 – Pre-breach alerts:** We trigger structured alerts at 50/70/90% of the timer so owners can act, reassign, or escalate before the breach point. <br>**Phase 3 – Automatic escalation:** When thresholds expire, the platform routes items to leads or duty managers with context and next-step guidance for rapid recovery. | - This prevents last-minute firefighting by prompting action before deadlines are missed.<br><br>- This reduces contractual and financial exposure by lowering the number of items reaching Overdue without warning.<br><br>- This stabilizes throughput because risk is managed proactively rather than reactively.<br><br>- This reduces overtime pressure as teams adjust workload earlier in the cycle.<br><br>- This strengthens leadership control with consistent, data-driven escalation signals.<br><br> | **Cost avoided** ≈ overdue_in_{top_status} × hourly_penalty. When 'Overdue' exists, use its count directly; otherwise estimate overdue share within {top_status}. | Elevated 'Overdue' bars (when present) directly represent financial risk segments; {top_status} bar shows where timers should focus first. |
""",
    "performance": f"""
| Recommendations | Explanation | Benefits | Cost Calculation | Evidence |
|---|---|---|---|---|
| Prioritize oldest tickets in top status | **Phase 1 – Age-based routing:** We sort {top_status} by ticket age and enforce a “finish oldest first” pull policy so aged items consistently move to the front of the queue. <br>**Phase 2 – WIP limits:** We set explicit per-owner WIP caps to reduce multitasking and context switching, which improves end-to-end completion. <br>**Phase 3 – Review cadence:** We run a short daily huddle to review the oldest items, assign concrete actions, and track burn-down targets. | - This raises throughput by directing attention to completion rather than constant starting of new work.<br><br>- This reduces average age in {top_status} because old items are systematically advanced to closure.<br><br>- This lowers breach probability by prioritizing items closest to SLA thresholds.<br><br>- This improves predictability for stakeholders through visible, daily progress on aged work.<br><br>- This decreases rework because focused owners carry tasks to done without excessive handoffs.<br><br> | **SLA gain (pp)** ≈ (aged_reduced_in_{top_status}/ {total_open}) × 100. Use the {top_status} count **{top_count:,}** as the immediate burn-down target. | The tallest bar **{top_status}** signals stagnation; age-based routing directly attacks this backlog. |
| Implement weekly bottleneck reviews | **Phase 1 – 30-min weekly:** We institutionalize a short, high-leverage review on the tallest status bar, with clear ownership and decision logs. <br>**Phase 2 – Track actions:** We assign specific actions with owners and due dates, and we update tickets and dashboards to reflect commitments. <br>**Phase 3 – Iterate:** We compare week-over-week results and refine policies, staffing, or automation when the bottleneck does not shrink. | - This creates consistent focus on the biggest blocker instead of reactive attention shifts.<br><br>- This accelerates unblock cycles by ensuring decisions and actions have explicit owners and timelines.<br><br>- This prevents silent pile-ups because status growth is reviewed and acted upon regularly.<br><br>- This makes improvement measurable through week-over-week bar reduction.<br><br>- This strengthens cross-team alignment by making the bottleneck everyone’s shared priority.<br><br> | **Efficiency gain (h)** ≈ Δclosure_rate × backlog_in_{top_status} (baseline from **{top_count:,}**). | The chart reveals a persistent bottleneck requiring governance rituals to keep flow healthy. |
| Real-time dashboards for status tracking | **Phase 1 – Live boards:** We deliver live dashboards showing per-status counts, trends, and SLA risk so leaders and analysts share a single source of truth. <br>**Phase 2 – Auto-reassign:** We apply rules and playbooks to reassign stuck items from overloaded owners to available capacity in real time. <br>**Phase 3 – Alerts:** We set alert thresholds for {top_status} and other key statuses so spikes trigger immediate intervention. | - This improves accountability because teams see status growth and ownership in real time.<br><br>- This shortens time to unblock issues by making stuck work visible and actionable.<br><br>- This stabilizes daily performance with continuous micro-adjustments rather than infrequent corrections.<br><br>- This avoids manual reporting overhead by using system-generated visibility for decisions.<br><br>- This increases throughput as capacity is dynamically balanced across the team.<br><br> | **ROI (h)** ≈ closure_rate_gain × avg_hours_per_ticket × {top_count:,}. | Growth in **{top_status}** evidences control gaps that real-time dashboards can mitigate quickly. |
""",
    "satisfaction": f"""
| Recommendations | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Communicate next actions for pending tickets | **Phase 1 – Templates:** We draft clear, status-specific messages that state ownership, the next concrete step, and the expected update time. <br>**Phase 2 – Triggered sends:** We configure automatic sends on status changes and at set intervals while a ticket remains in the same state. <br>**Phase 3 – Feedback loop:** We monitor inquiry reductions and adjust wording or cadence to match customer expectations. | - This reduces uncertainty because users know exactly what will happen next and when.<br><br>- This lowers inbound chasers which frees analyst time for resolution work.<br><br>- This builds trust during wait periods through proactive, consistent communication.<br><br>- This standardizes tone and clarity across agents which improves perceived professionalism.<br><br>- This improves CSAT by setting and meeting transparent expectations throughout the lifecycle.<br><br> | **Benefit (h)** ≈ inquiries_avoided_in_{top_status} × handling_min/60. Size using the {top_status} cohort **{top_count:,}**. | Large **{top_status}** share amplifies uncertainty; templated comms directly serve the largest waiting pool. |
| Publish resolution forecasts | **Phase 1 – Backlog-aware ETAs:** We generate ETAs using status, age, and historical throughput so forecasts reflect current load. <br>**Phase 2 – Portal visibility:** We display ETAs in the portal and notifications so requestors can plan around realistic timelines. <br>**Phase 3 – Update cadence:** We refresh ETAs when status or age changes so forecasts remain credible and actionable. | - This increases transparency by giving users a concrete timeframe instead of silence.<br><br>- This improves planning for business teams that depend on ticket outcomes to schedule their work.<br><br>- This reduces complaints and status checks by replacing uncertainty with data-based forecasts.<br><br>- This surfaces capacity gaps when forecast accuracy is reviewed over time.<br><br>- This elevates stakeholder confidence because progress and timing are visible and trackable.<br><br> | **CSAT uplift** ≈ (%customers_informed_in_{top_status} × satisfaction_gain). | **{top_status}** at **{top_count:,}** indicates the group where forecasts will move the needle most. |
| Monitor VIP tickets separately | **Phase 1 – VIP tags:** We identify strategic customers and tag their tickets to enable special handling rules and prioritized visibility. <br>**Phase 2 – Senior ownership:** We route VIP tickets to experienced handlers with shorter communication cadences and decision authority. <br>**Phase 3 – Escalation rules:** We define fast-lane escalation triggers to leadership to protect outcomes under risk. | - This prevents high-impact escalations by making VIP issues visible and actively managed.<br><br>- This protects key accounts with faster updates and decisive action from senior handlers.<br><br>- This maintains fairness by codifying special handling rather than relying on informal exceptions.<br><br>- This provides leadership with early warning on relationship risk through dedicated visibility.<br><br>- This strengthens retention by resolving critical issues with urgency and transparency.<br><br> | **Penalty avoided** ≈ vip_breaches_prevented × penalty_per_breach. | High backlog concentrates breach risk for VIPs. |
"""
                }

                if cio_1b is not None:
                    render_cio_tables("Open Status Mix", cio_1b)

    # ---------------------- 4b ----------------------
    with st.expander("📌 Escalated Incidents (ReOpened / Overdue Proxy)"):
        have_proxy = False
        frames = []

        if "reopened" in df_filtered.columns:
            ro = df_filtered["reopened"].astype(str).str.lower().isin(["true", "yes", "1"]).sum()
            frames.append(("ReOpened Incidents", int(ro)))
            have_proxy = True

        if "overdue_status" in df_filtered.columns:
            od = df_filtered["overdue_status"].astype(str).str.lower().str.contains("overdue").sum()
            frames.append(("Overdue Incidents", int(od)))
            have_proxy = True

        if have_proxy:
            dd = pd.DataFrame(frames, columns=["Metric", "Count"])

            # If all zero, skip chart/analysis
            if dd["Count"].sum() == 0:
                st.info("Escalation indicators are all zero. Data is not available, so there will be no analysis.")
            else:
                fig = px.bar(
                    dd,
                    x="Metric",
                    y="Count",
                    title="Escalation Indicators",
                    text="Count",
                    color_discrete_sequence=BLUE_TONES,
                )
                fig.update_traces(textposition="outside")
                st.plotly_chart(fig, use_container_width=True)

                total_escalations = int(dd["Count"].sum())
                top_idx = dd["Count"].idxmax()
                top_metric = dd.loc[top_idx, "Metric"]
                top_val = int(dd.loc[top_idx, "Count"])

                st.markdown("### Analysis")
                st.write(f"""
What this graph is: A bar chart showing escalation proxies: reopened incidents and overdue incidents.

X-axis: Escalation metric type (ReOpened Incidents, Overdue Incidents).
Y-axis: Count of incidents.
                     
What it shows in your data:
Total escalation-related cases: {total_escalations:,}.
Largest escalation type: {top_metric} with {top_val:,}.
Overall: Taller bars indicate latent quality or flow issues (reopens = fix-quality gaps; overdue = timing/capacity gaps); shorter bars indicate better control.

How to read it operationally:
Peaks: Run root cause reviews, add owner accountability, and tighten controls on the dominant metric.
Plateaus: Maintain prevention checks (closure validation, SLA timers) to keep rates down and steady.
Downswings: Confirm which interventions (KB updates, early warnings, staffing) reduced escalations and standardize them.
Mix: Always pair with category/priority/age to ensure critical items don’t drive hidden churn.
Why this matters: Escalations consume rework time, drive breach penalties, and create customer dissatisfaction; lowering these bars protects cost, performance, and trust.
                """)

                # CIO guard
                cio_1a = None
                if total_escalations <= 1 or top_val <= 1:
                    st.warning("📉 Escalation volume is too low to generate meaningful recommendations.")
                else:
                    # build CIO only when we will render it
                    reopen_count = int(dd.loc[dd['Metric'] == 'ReOpened Incidents', 'Count'].iloc[0]) if 'ReOpened Incidents' in dd['Metric'].values else 0
                    overdue_count = int(dd.loc[dd['Metric'] == 'Overdue Incidents', 'Count'].iloc[0]) if 'Overdue Incidents' in dd['Metric'].values else 0

                    cio_1a = {
    "cost": f"""
| Recommendations | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Strengthen closure quality control | **Phase 1 – Mandatory closure data:** We enforce completion of cause, action, prevention, and verification fields before a ticket can close so fixes are explicit and reviewable. <br>**Phase 2 – Peer checks:** We introduce lightweight peer review for high-risk categories to validate that the resolution is correct and complete prior to closure. <br>**Phase 3 – Feedback loop:** We mine reopened tickets for patterns, update KB/runbooks, and coach teams to eliminate common failure modes. | - This reduces double handling because more tickets are truly fixed the first time.<br><br>- This lowers reopen rates by standardizing the definition of “done” with required evidence of resolution.<br><br>- This stabilizes effort per ticket by limiting post-closure rework and unplanned callbacks.<br><br>- This improves knowledge quality which compounds future speed and accuracy of fixes.<br><br>- This increases stakeholder confidence as closure quality becomes consistent and auditable.<br><br> | **Savings (h)** ≈ reopens_prevented × avg_fix_time. Use **ReOpened Incidents = {reopen_count}** as the baseline. | The **{top_metric}** bar at **{top_val}** indicates where QC will deliver the fastest return. |
| Automate SLA alerts | **Phase 1 – Threshold alerts:** We configure milestone alerts at 50/70/90% of SLA to give owners time to act on at-risk tickets. <br>**Phase 2 – Auto-escalation:** We auto-notify leads or reassign when owners are overloaded so items do not slip into breach unmanaged. <br>**Phase 3 – Audit:** We review near-misses and breaches weekly to confirm that alerts fired, were acted upon, and to refine rules where gaps appear. | - This reduces penalties by catching risk before the SLA expires.<br><br>- This decreases firefighting because teams intervene earlier rather than after a breach occurs.<br><br>- This improves overall on-time performance with fewer last-minute rushes and overtime spikes.<br><br>- This strengthens managerial control with clear visibility of at-risk work and actions taken.<br><br>- This enhances customer trust as fewer cases cross into overdue status without communication.<br><br> | **Avoided cost** ≈ overdue_prevented × penalty_rate. Baseline **Overdue Incidents = {overdue_count}**. | A higher **Overdue Incidents** bar confirms missed early warnings that alerts can directly reduce. |
| Introduce root cause analysis post-escalation | **Phase 1 – Lightweight RCA:** We capture a concise RCA for every escalation covering what happened, why it happened, and which control failed. <br>**Phase 2 – Theme aggregation:** We aggregate RCAs monthly, rank the top recurring themes by impact, and assign corrective owners and deadlines. <br>**Phase 3 – Verify fixes:** We track whether escalation rates for those themes fall over subsequent periods and we harden the control if improvement stalls. | - This reduces recurrence by addressing systemic causes rather than isolated symptoms.<br><br>- This cuts waste from repeat escalations that trigger rework and customer dissatisfaction.<br><br>- This focuses improvement effort on the few themes that create most of the negative volume.<br><br>- This creates an evidence-based narrative for leadership about risk drivers and remediation progress.<br><br>- This institutionalizes learning so the operation becomes more resilient over time.<br><br> | **Time saved (h)** ≈ reduction_in_escalation_rate × avg_duration × {total_escalations}. | Concentration in **{top_metric}** highlights preventable inefficiencies to target first. |
""",
    "performance": f"""
| Recommendations | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Weekly reopen audit | **Phase 1 – Pattern detect:** We review reopened items weekly, segment by category/owner/technology, and surface repeat failure modes. <br>**Phase 2 – Coaching:** We share targeted guidance and examples with owners involved in recurring issues to raise first-time-right outcomes. <br>**Phase 3 – KB/runbook fixes:** We convert insights into updated KB and runbook steps so better practice becomes the default path. | - This improves first-time resolution by converting recent lessons into specific behaviors.<br><br>- This shortens cycle time because fewer tickets loop back through the queue.<br><br>- This reduces escalation volume by eliminating the root causes of poor fixes.<br><br>- This reinforces a learning culture focused on systems rather than blame.<br><br>- This raises consistency so users receive predictable quality regardless of handler.<br><br> | **Efficiency gain** ≈ ΔFFR% × total_cases (use reopen baseline above). | Elevated **{top_metric}** bar shows recurring resolution issues that audits can directly address. |
| SLA breach dashboard | **Phase 1 – Visibility:** We build a dashboard showing breach trends by team, owner, category, and time so performance gaps are transparent. <br>**Phase 2 – Triggers:** We use the dashboard to drive actions—auto-assignment, targeted follow-ups, or staffing changes—where breaches cluster. <br>**Phase 3 – Accountability:** We publish weekly changes so teams see how interventions affect breach rates. | - This improves on-time delivery by directing attention to the exact segments that miss SLAs.<br><br>- This stabilizes compliance through fast feedback on the impact of interventions.<br><br>- This elevates leadership visibility which accelerates support and resource allocation.<br><br>- This reduces manual reporting effort by centralizing the metrics that matter.<br><br>- This creates a continuous improvement loop anchored in observable results.<br><br> | **SLA uplift (pp)** ≈ breaches_prevented / total_cases × 100. Baseline from **Overdue Incidents** count. | Overdue trends mark underperforming areas requiring action; dashboard centralizes attention. |
| Knowledge base for high-reopen categories | **Phase 1 – Diagnostics first:** We codify step-by-step diagnostics for the top reopen categories so analysts ask the right questions and perform the right tests. <br>**Phase 2 – Fix scripts:** We publish repeatable remediation scripts that reflect proven fixes and edge cases. <br>**Phase 3 – Prevention tips:** We add simple prevention guidance for users and operations teams to reduce recurrence at the source. | - This reduces TTR because analysts follow a validated troubleshooting path rather than trial and error.<br><br>- This lowers reopen probability by improving the completeness and accuracy of fixes.<br><br>- This harmonizes outputs across analysts so quality is less variable.<br><br>- This reduces training time for new joiners with clear, actionable references.<br><br>- This drives measurable decline in the reopen bar for targeted categories.<br><br> | **Time saved (h)** ≈ avg_resolution_drop × case_volume in top reopen categories. | Escalation-heavy categories clearly need procedural support to raise FTR. |
""",
    "satisfaction": f"""
| Recommendations | Explanation | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Dedicated escalation handlers | **Phase 1 – Ownership:** We assign a small cadre of escalation specialists with clear SLAs for response and update cadence. <br>**Phase 2 – Comms cadence:** We set time-to-first-contact and regular update intervals, and we template escalation comms for clarity under pressure. <br>**Phase 3 – Review:** We track time to first response, time to closure, and user feedback to validate the model and refine where needed. | - This improves response quality because experienced handlers manage complex, sensitive cases with confidence.<br><br>- This builds customer trust as escalations receive proactive, scheduled updates from named owners.<br><br>- This reduces churn risk for strategic accounts by resolving high-impact issues faster and more transparently.<br><br>- This creates consistency in stressful moments because the cadence and standards are predefined.<br><br>- This frees frontline agents to maintain flow on routine volume without constant interruption.<br><br> | **Retention value** ≈ VIP_escalations × avg_contract_value (subset of {total_escalations}). | Frequent **{top_metric}** implies ownership gaps that degrade customer experience. |
| Proactive delay notifications | **Phase 1 – Pre-breach messages:** We notify users before likely delays become breaches, with reason codes and updated ETAs. <br>**Phase 2 – Templates by cause:** We maintain a library of messages for vendor waits, parts shortages, approvals, and other common delays to keep comms fast and specific. <br>**Phase 3 – Measure:** We monitor complaint and follow-up rates post-implementation and iterate on wording and timing to maximize impact. | - This reduces dissatisfaction by acknowledging delays early and providing clear next steps.<br><br>- This lowers complaint volume by replacing uncertainty with proactive information.<br><br>- This reduces inbound noise so analysts can focus on moving work instead of answering status requests.<br><br>- This strengthens perception of control and professionalism during service hiccups.<br><br>- This improves SLA outcomes indirectly by triggering earlier internal action when delays surface.<br><br> | **Complaints avoided (h)** ≈ avoided_contacts × handling_cost, sized from overdue share. | **Overdue Incidents** visibly trigger negative sentiment and follow-ups; tackling them moves CSAT. |
| Collect feedback post-escalation | **Phase 1 – Short survey:** We send a concise survey at closure focusing on clarity, speed, and overall satisfaction to capture actionable insights. <br>**Phase 2 – Theme mining:** We analyze quantitative scores and comments to isolate high-frequency pain points and expectations gaps. <br>**Phase 3 – Close loop:** We communicate the improvements being implemented and show users where their feedback drove change. | - This enhances long-term trust by demonstrating that feedback results in visible improvements.<br><br>- This surfaces quick wins that reduce friction with minimal effort or cost.<br><br>- This guides strategic fixes by quantifying which aspects of the escalation journey matter most to users.<br><br>- This provides leadership with a clear readout of sentiment and trend direction over time.<br><br>- This creates a virtuous cycle where better experiences lift survey response and insight quality.<br><br> | **CSAT gain** ≈ feedback_rate × satisfaction_boost across {total_escalations} escalations. | Feedback on escalated items directly informs the highest-impact fixes. |
"""
            }
                if have_proxy and dd["Count"].sum() != 0 and cio_1a is not None:
                    render_cio_tables("Escalation Proxies", cio_1a)
        else:
            st.info("No fields available to estimate escalations (need ReOpened or Overdue Status).")
