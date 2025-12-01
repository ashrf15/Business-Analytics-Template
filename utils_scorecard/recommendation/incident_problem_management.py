import streamlit as st
import plotly.express as px
import pandas as pd

# ---------- Mesiniaga palette helpers ----------
MES_BLUE = ["#004C99", "#007ACC", "#3399FF", "#66B2FF", "#9BD1FF"]

def render_cio_tables(title, cio_data):
    st.subheader(title)
    with st.expander("Cost Reduction"):
        st.markdown(cio_data.get("cost","_No cost recommendations._"), unsafe_allow_html=True)
    with st.expander("Performance Improvement"):
        st.markdown(cio_data.get("performance","_No performance recommendations._"), unsafe_allow_html=True)
    with st.expander("Customer Satisfaction Improvement"):
        st.markdown(cio_data.get("satisfaction","_No satisfaction recommendations._"), unsafe_allow_html=True)

def _fmt_int(n):
    try:
        return f"{int(n):,}"
    except Exception:
        return "0"

def _fmt_float(x, d=1):
    try:
        return f"{float(x):.{d}f}"
    except Exception:
        return "0.0"

def incident_problem_management(df_filtered):

    if "report_date" in df_filtered.columns:
        df_filtered["report_date"] = pd.to_datetime(df_filtered["report_date"], errors="coerce")
        df_filtered["report_month"] = df_filtered["report_date"].dt.to_period("M").astype(str)

    # ---------------------- 4(a) Incident and Problem Trends ----------------------
    with st.expander("📌 Incident & Problem Trends Over Time"):
        if {"incident_count","problem_count","report_month"} <= set(df_filtered.columns):
            tr = (
                df_filtered
                .groupby("report_month")[["incident_count","problem_count"]]
                .sum()
                .reset_index()
                .sort_values("report_month")
            )

            fig = px.line(
                tr, x="report_month", y=["incident_count","problem_count"],
                markers=True, title="Monthly Incidents vs Problems",
                color_discrete_sequence=MES_BLUE, template="plotly_white"
            )
            st.plotly_chart(fig, use_container_width=True)

            if not tr.empty:
                # Incidents
                inc_peak_row = tr.loc[tr["incident_count"].idxmax()]
                inc_low_row  = tr.loc[tr["incident_count"].idxmin()]
                inc_avg      = tr["incident_count"].mean()

                # Problems
                prob_peak_row = tr.loc[tr["problem_count"].idxmax()]
                prob_low_row  = tr.loc[tr["problem_count"].idxmin()]
                prob_avg      = tr["problem_count"].mean()

                st.markdown("### Analysis of Dual Trend of Incidents & Problems")
                st.write(f"""
**What this graph is:** A dual throughput chart comparing **incidents** (inflow of disruptions) and **problems** (underlying root-cause records) **per month**.  
**X-axis:** Calendar month.  
**Y-axis:** Counts for each monthly metric (**incidents**, **problems**).

**What it shows in your data:**  
- **Largest incident month:** **{inc_peak_row['report_month']}** with **{_fmt_int(inc_peak_row['incident_count'])}** incidents.  
- **Smallest incident month:** **{inc_low_row['report_month']}** with **{_fmt_int(inc_low_row['incident_count'])}** incidents.  
- **Largest problem month:** **{prob_peak_row['report_month']}** with **{_fmt_int(prob_peak_row['problem_count'])}** problems.  
- **Smallest problem month:** **{prob_low_row['report_month']}** with **{_fmt_int(prob_low_row['problem_count'])}** problems.  
- **Averages across period:** **{_fmt_float(inc_avg)} incidents/month** vs **{_fmt_float(prob_avg)} problems/month**.

**Overall:** When the **problems line persistently tracks below incidents**, the engine is logging symptoms faster than causes—**repeat risk rises**. When the problems line **meets or exceeds** incidents for a few months, **root-cause work is catching up** and recurrences should fall.

**How to read it operationally:**  
- **Gap = recurrence risk:** The vertical distance (incidents − problems) approximates unresolved causality.  
- **Lead–lag:** Problems peaking shortly **after** incident spikes implies reactive RCA; pulling problem creation **forward** reduces repeats.  
- **Recovery strength:** Faster convergence after spikes = healthier stabilization loop.  
- **Control:** Target **near-parallel** lines with minimal gap via pre-approved RCA windows and change guardrails.

**Why this matters:** Balancing incident inflow with sustained problem management **prevents repeat outages**, protects SLA, and **steadies customer experience**.
""")

                ev_dual = (
                    f"Incident peak **{inc_peak_row['report_month']} = {_fmt_int(inc_peak_row['incident_count'])}**, "
                    f"incident trough **{inc_low_row['report_month']} = {_fmt_int(inc_low_row['incident_count'])}**; "
                    f"problem peak **{prob_peak_row['report_month']} = {_fmt_int(prob_peak_row['problem_count'])}**, "
                    f"problem trough **{prob_low_row['report_month']} = {_fmt_int(prob_low_row['problem_count'])}**; "
                    f"averages **{_fmt_float(inc_avg)} incidents/mo** vs **{_fmt_float(prob_avg)} problems/mo**."
                )

                # ---------- CIO tables with phased explanations + live calculations ----------
                cio = {
                    "cost": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation (Live) | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Freeze risky changes during spike months** | **Phase 1 – Detect:** Use the dual trend to mark the months where incidents exceed the long run average by a clear margin such as **{_fmt_int(inc_peak_row['incident_count'] - int(inc_avg))}** above average in **{inc_peak_row['report_month']}**. Document the affected services and the change types with the highest blast radius.<br><br>**Phase 2 – Enforce:** Apply a temporary freeze or add an extra approval step for high-risk changes that could worsen instability. Communicate the rule of engagement to all change owners and vendors so scheduling is aligned.<br><br>**Phase 3 – Review:** Lift the freeze once the incident volume falls back near the average of **{_fmt_float(inc_avg)}** per month and record the outcome in a post-window review. | - Reduces the likelihood of cascading incidents during unstable months which directly lowers recovery labour and on-call cost.<br><br>- Shortens the time to stabilize services after spikes which improves overall service predictability.<br><br>- Protects operational budgets by avoiding emergency work that typically requires overtime. | **Incidents avoided** = (Spike − Avg) = **{_fmt_int(inc_peak_row['incident_count'] - int(inc_avg))}** × **avg MTTR (mins)** × **rate**. | {ev_dual} |
| **Batch maintenance into fewer, larger windows** | **Phase 1 – Consolidate:** Inventory all planned maintenance in the spike month and merge compatible tasks into one or two larger windows to avoid repeated prep and rollback work.<br><br>**Phase 2 – Coordinate:** Build a cross-team execution plan with shared communications, joint validation steps, and a unified backout plan to minimize interruptions.<br><br>**Phase 3 – Measure:** Track prep minutes and rollback minutes before and after consolidation and keep the evidence in a monthly playbook. | - Lowers repeated administrative effort because teams prepare once for a larger window instead of many smaller ones.<br><br>- Reduces the chance of change collisions that often create avoidable incidents and rework.<br><br>- Improves stakeholder experience by concentrating impact into predictable, clearly communicated windows. | **Admin mins saved** = (Old windows − New windows) × **prep mins/window**. Use spike months such as **{inc_peak_row['report_month']}** to anchor estimates. | Peak months suggest fragmented work contributing to spikes. |
| **Pull-forward RCA creation** | **Phase 1 – Trigger:** Automatically create a problem record in the same week when monthly incident volume crosses 120% of average so causes are investigated while context is fresh.<br><br>**Phase 2 – Timebox:** Set a strict 48–72 hour timeframe to assign an RCA owner, define hypotheses, and schedule data collection so the effort does not stall.<br><br>**Phase 3 – Verify:** Link fixes to the RCA record and track recurrence for the following two months to confirm effectiveness. | - Cuts recurrence because causes are addressed promptly while the signals are still visible in logs and traces.<br><br>- Reduces follow-on work created by repeated symptoms which protects analyst capacity.<br><br>- Improves planning accuracy because predictable RCA throughput leads to predictable incident reduction. | **Repeat incidents avoided** ≈ (Incident − Problem gap) = **{_fmt_int(max(0, int(inc_avg - prob_avg)))}**/mo × **avg handle mins** × **rate**. | Persistent gap where incidents > problems indicates unresolved root causes. |
""",
                    "performance": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation (Live) | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Lead indicator reviews (weekly)** | **Phase 1 – Inspect:** Compare the current month’s incident run-rate against the baseline of **{_fmt_float(inc_avg)}** each week and flag any acceleration early.<br><br>**Phase 2 – Act:** Pre-empt risky changes or expedite known fixes when the trajectory suggests a spike to prevent compounding failures.<br><br>**Phase 3 – Retrospect:** After the month ends, document the drivers and actions in a short write-up so learning feeds the next cycle. | - Enables earlier detection of negative drift which reduces the length and depth of incident spikes.<br><br>- Decreases emergency changes because risks are mitigated before failure windows open.<br><br>- Improves MTTR by ensuring teams are in a prepared posture before escalations happen. | **MTTR hours saved** = (ΔMTTR × incident count in spike month **{_fmt_int(inc_peak_row['incident_count'])}**). | Spikes followed by problem surges show reactive rather than proactive control. |
| **Standard rollback kits** | **Phase 1 – Catalogue:** Build a list of known-good images and configurations for top services with clear versioning and storage locations.<br><br>**Phase 2 – Script:** Provide one-click rollback or short step scripts so analysts do not improvise under pressure.<br><br>**Phase 3 – Drill:** Run quarterly rollback drills to ensure speed and reliability of execution. | - Accelerates containment when a change goes wrong which directly reduces user impact minutes.<br><br>- Shrinks the blast radius because consistent rollback steps avoid secondary faults during recovery.<br><br>- Raises team confidence which improves decision-making in high-stress conditions. | **Containment mins saved** per incident × incidents in peak months (**{_fmt_int(inc_peak_row['incident_count'])}**). | Steep rises require rapid rollback readiness. |
| **RCA SLA (creation + closure)** | **Phase 1 – SLA:** Require creation within 24 hours of a spike and closure with actions within ten business days so causes do not linger.<br><br>**Phase 2 – Escalate:** Auto-escalate any overdue RCA to leadership with a clear ask for unblockers.<br><br>**Phase 3 – Publish:** Add RCA scorecards to monthly service reviews to maintain visibility and accountability. | - Increases the conversion of incidents into durable fixes which steadily lowers recurrence rates.<br><br>- Reduces lead time from symptom to fix which improves stability faster after spikes.<br><br>- Improves cross-team coordination because expectations and timing are clear. | **Recurrence reduction** = (gap shrink per month **{_fmt_float(inc_avg - prob_avg)}**) × **avg handle mins**. | Gap between incident and problem lines quantifies missed RCA. |
""",
                    "satisfaction": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation (Live) | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Spike-aware customer communications** | **Phase 1 – Trigger:** When the month-to-date incident count exceeds the baseline by 20% publish a brief status outlining risk, mitigations, and support options.<br><br>**Phase 2 – Cadence:** Send a T+15 initial note and weekly rollups with progress and next steps so stakeholders are not left guessing.<br><br>**Phase 3 – Close-the-loop:** After RCA completion, share the outcome and prevention steps in plain language. | - Reduces inbound complaints during spikes because users receive timely and relevant updates.<br><br>- Increases perceived transparency which improves trust even when issues persist for a short period.<br><br>- Decreases ad-hoc queries to support which preserves analyst time for fixes. | **Complaints avoided × mins/case**, anchored to spike overage **{_fmt_int(inc_peak_row['incident_count'] - int(inc_avg))}**. | Users react strongly to spikes; clarity stabilizes sentiment. |
| **Expectation setting for problem work** | **Phase 1 – Roadmap:** Publish a simple problem backlog with target dates for top contributors to incidents.<br><br>**Phase 2 – Updates:** Provide weekly progress updates that state what moved and what is blocked.<br><br>**Phase 3 – Celebrate:** Call out completed items to signal progress and reinforce confidence. | - Builds confidence that problematic patterns will not repeat which supports retention of key customers.<br><br>- Reduces escalations because stakeholders can see progress toward prevention rather than only reactive fixes.<br><br>- Improves NPS by showing a credible plan and steady delivery. | **Escalation cost avoided** linked to months where problems ≥ incidents which indicates catch-up. | Convergence of the lines indicates effective prevention. |
| **Service review brief** | **Phase 1 – Monthly deck:** Produce a short deck that lists top incidents, the fixes applied, and the next actions with owners and dates.<br><br>**Phase 2 – Q&A:** Host a short session to address stakeholder concerns and clarify timelines.<br><br>**Phase 3 – Actions:** Track the commitments and close them in the next review so confidence grows. | - Creates shared understanding which lowers repeated queries to the support team.<br><br>- Aligns business and technical timelines which reduces friction in planning cycles.<br><br>- Improves satisfaction because stakeholders see accountability and delivery. | **Queries avoided × mins** during peak months. | Clear trends reduce anxiety and inbound noise. |
"""
                }
                render_cio_tables("CIO — Trend Actions", cio)
            else:
                st.info("No monthly rows available to analyse.")
        else:
            st.warning("Need 'report_date' + 'incident_count' + 'problem_count'.")

    # ---------------------- 4(b) Root Cause Analysis ----------------------
    with st.expander("📌 Root Cause Analysis (Major Incidents)"):
        if "root_cause" in df_filtered.columns:
            rc = df_filtered["root_cause"].value_counts(dropna=False).reset_index()
            rc.columns = ["root_cause","records"]
            fig = px.bar(
                rc, x="root_cause", y="records",
                title="Root Cause Distribution",
                color_discrete_sequence=MES_BLUE, template="plotly_white"
            )
            st.plotly_chart(fig, use_container_width=True)

            if not rc.empty:
                top = rc.loc[rc["records"].idxmax()]
                bot = rc.loc[rc["records"].idxmin()]

                st.markdown("### Analysis of Root Cause Pareto")
                st.write(f"""
**What this graph is:** A Pareto-style bar chart of **root causes** observed in incidents.  
**X-axis:** Root cause category.  
**Y-axis:** Number of incidents attributed.

**What it shows in your data:**  
- **Top cause:** **{top['root_cause']}** with **{_fmt_int(top['records'])}** occurrences.  
- **Lowest cause:** **{bot['root_cause']}** with **{_fmt_int(bot['records'])}** occurrences.

**Overall:** Tackling the tallest bars first yields the **largest immediate reduction** in repeat incidents.

**How to read it operationally:**  
- **Prioritize by volume:** Address the top 2–3 causes first.  
- **Template the fix:** Standard steps for recurring causes.  
- **Verify effect:** Re-measure after rollout.

**Why this matters:** Concentrated root causes are **low-hanging fruit** for performance, cost, and CSAT improvements.
""")

                ev_rc = f"Top cause **{top['root_cause']} = {_fmt_int(top['records'])}**; lowest **{bot['root_cause']} = {_fmt_int(bot['records'])}**."

                cio = {
                    "cost": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation (Live) | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Dry-run high-risk changes** | **Phase 1 – Rehearse:** Execute lab or sandbox rehearsals for changes linked to the top cause so steps and backouts are validated without production risk.<br><br>**Phase 2 – Peer-check:** Apply a short peer review checklist to confirm prerequisites, monitoring, and rollback plans are complete.<br><br>**Phase 3 – Gate:** Allow deployment only when the checklist passes and record results for audit. | - Reduces failed change rates which directly lowers the number of incidents tied to deployment errors.<br><br>- Shrinks recovery labour because rollbacks are tested and faster to execute in real conditions.<br><br>- Improves planning confidence which reduces last minute delays and vendor churn. | **Savings** = (Rollbacks avoided × recovery mins × rate). Focus on **{top['root_cause']}**. | {ev_rc} |
| **Standard fix templates for recurring causes** | **Phase 1 – Codify:** Convert the most common fixes for the top causes into step-by-step runbooks with clear validation points.<br><br>**Phase 2 – Train:** Walk the team through these runbooks using recent incidents as examples so knowledge becomes shared.<br><br>**Phase 3 – Enforce:** Require linking a completed template to ticket closure to ensure consistent execution. | - Lowers cycle time variability which makes outcomes more predictable for stakeholders.<br><br>- Reduces missteps by giving analysts a clear and proven path to resolution.<br><br>- Speeds onboarding of new team members which stabilizes performance across shifts. | **Resolution mins saved** = (Δcycle time × cases for top causes **{_fmt_int(top['records'])}**). | Concentration in tallest bars indicates repeatability. |
| **Preventative config checks** | **Phase 1 – Lint:** Create automated configuration checks for misconfiguration classes that commonly cause incidents.<br><br>**Phase 2 – Automate:** Integrate these checks into CI/CD or scheduled audits so drift is caught early.<br><br>**Phase 3 – Audit:** Review exceptions monthly and remove waivers that no longer make sense. | - Avoids incidents caused by configuration drift which reduces surprise outages for users.<br><br>- Lowers hotfix labour because fewer emergency corrections are needed in production.<br><br>- Improves reliability which supports higher SLA attainment. | **Incidents avoided** = (Misconfig share × total) × **avg MTTR**. | Misconfig-related categories are visible among bars. |
""",
                    "performance": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation (Live) | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **48h RCA SLA for majors** | **Phase 1 – Assign:** For major incidents, assign an RCA owner within 48 hours with a clear goal and deadline for initial findings.<br><br>**Phase 2 – Verify:** Ensure actions from the RCA are specific, time-bound, and linked to tickets so delivery can be tracked.<br><br>**Phase 3 – Track:** Monitor closure and recurrences so improvements are measured and sustained. | - Accelerates learning after major failures which reduces the chance of repeat disruptions.<br><br>- Shortens MTTR over time because the team fixes root causes rather than only symptoms.<br><br>- Builds stakeholder confidence by demonstrating disciplined follow-through. | **Repeat reduction** = (post-RCA incident drop for **{top['root_cause']}** × avg handle mins). | High volume category promises quick wins. |
| **Cause→Action linkage dashboard** | **Phase 1 – Map:** Link each root cause to a small set of discrete corrective actions and make them visible on a dashboard.<br><br>**Phase 2 – Measure:** Track before and after incident counts and MTTR per cause to prove which actions work.<br><br>**Phase 3 – Iterate:** Retire actions that do not move the metrics and double down on those that do. | - Closes the loop between diagnosis and prevention which speeds downtrend in incident volume.<br><br>- Focuses effort on interventions with demonstrated impact which improves resource efficiency.<br><br>- Enables transparent decision making that aligns teams. | **ΔTrend × cases** attributed to each cause. | Tracks whether bars shrink after actions. |
| **Runbook refresh cadence** | **Phase 1 – Curate:** Refresh key SOPs quarterly to reflect new tools and lessons from recent incidents.<br><br>**Phase 2 – Diffuse:** Brief teams and run short tests to verify understanding and adoption.<br><br>**Phase 3 – Score:** Track adoption rates and spot areas needing coaching. | - Sustains performance improvements by keeping procedures current and usable.<br><br>- Reduces reliance on tribal knowledge which lowers risk when staffing changes occur.<br><br>- Improves resolution consistency across teams and shifts. | **Minutes saved** = (rework mins reduced × cases). | Runbook alignment reduces variance across causes. |
""",
                    "satisfaction": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation (Live) | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Clear postmortems for stakeholders** | **Phase 1 – Narrative:** Create short plain-language postmortems that explain what happened, what was fixed, and how repeat risk is being reduced.<br><br>**Phase 2 – Timing:** Share within five business days so memory is fresh and questions are minimized.<br><br>**Phase 3 – Archive:** Keep a searchable index so future incidents can reference prior learnings. | - Reduces chase-ups because stakeholders can self-serve answers to common questions.<br><br>- Restores trust after disruptions by showing ownership and concrete prevention steps.<br><br>- Improves sentiment in governance reviews because communication is consistent. | **Queries avoided × mins** for categories with high counts (**{_fmt_int(top['records'])}**). | Transparency offsets impact of top-cause incidents. |
| **AMA/Q&A sessions** | **Phase 1 – Session:** Host a 30-minute monthly Q&A to discuss recent incidents and actions in a non-technical tone.<br><br>**Phase 2 – Capture:** Record recurring concerns and convert them into FAQs or training content.<br><br>**Phase 3 – Act:** Feed insights into the prevention backlog so concerns lead to fixes. | - Closes expectation gaps which lowers escalation pressure on support teams.<br><br>- Strengthens alignment with business teams which improves cooperation during future incidents.<br><br>- Builds a continuous improvement culture that users can see. | **Escalation cost avoided** in the months following sessions. | Engagement reduces friction following spikes. |
| **Prevention roadmap brief** | **Phase 1 – Publish:** Provide a simple timeline for fixes to the top causes with owners and delivery dates.<br><br>**Phase 2 – Update:** Post monthly status updates so progress is visible.<br><br>**Phase 3 – Celebrate:** Announce close-outs to reinforce confidence and accountability. | - Aligns expectations so stakeholders plan around known remediation activities.<br><br>- Reduces uncertainty which improves satisfaction and lowers ad-hoc complaints.<br><br>- Demonstrates momentum which helps rebuild goodwill after major incidents. | **Detractors avoided** as roadmap items convert to delivered fixes. | Visible plan tied to tallest bars builds confidence. |
"""
                }
                render_cio_tables("CIO — RCA", cio)
            else:
                st.info("No rows available for root cause analysis.")
        else:
            st.warning("Column 'root_cause' not found.")

    # ---------------------- 4(c) Actions to Prevent Recurrence ----------------------
    with st.expander("📌 Actions Taken to Prevent Recurring Incidents"):
        if "preventive_action" in df_filtered.columns:
            pa = df_filtered["preventive_action"].value_counts(dropna=False).reset_index()
            pa.columns = ["preventive_action","records"]
            fig = px.bar(
                pa, x="preventive_action", y="records",
                title="Preventive Actions Distribution",
                color_discrete_sequence=MES_BLUE, template="plotly_white"
            )
            st.plotly_chart(fig, use_container_width=True)

            if not pa.empty:
                top = pa.loc[pa["records"].idxmax()]
                low = pa.loc[pa["records"].idxmin()]

                st.markdown("### Analysis of Preventive Actions Mix")
                st.write(f"""
**What this graph is:** A bar chart showing how often each **preventive action** is used after incidents.  
**X-axis:** Preventive action type.  
**Y-axis:** Number of times applied.

**What it shows in your data:**  
- **Most-used action:** **{top['preventive_action']}** with **{_fmt_int(top['records'])}** uses.  
- **Least-used action:** **{low['preventive_action']}** with **{_fmt_int(low['records'])}** uses.

**Overall:** Standardizing the most effective, high-use actions boosts consistency; reviewing low-use actions uncovers gaps or misplaced effort.

**How to read it operationally:**  
- **Exploit winners:** Turn top actions into templates with checklists.  
- **Fix underuse:** If low-use actions are effective, coach and automate triggers.  
- **Retire waste:** Remove actions that add steps without measurable reduction.

**Why this matters:** A sharp, standardized prevention toolkit **reduces recurrence**, shortens recovery, and **improves user confidence**.
""")

                ev_pa = f"Top action **{top['preventive_action']} = {_fmt_int(top['records'])}**; least **{low['preventive_action']} = {_fmt_int(low['records'])}**."

                cio = {
                    "cost": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation (Live) | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Standard action set** | **Phase 1 – Define:** Select a minimal set of high-effect actions for the most frequent repeat scenarios and describe the exact conditions under which each action applies.<br><br>**Phase 2 – Template:** Provide clear step lists, approvals, and validation checks so execution is quick and consistent.<br><br>**Phase 3 – Enforce:** Require linking an approved action template to ticket closure to prevent drift from the standard. | - Lowers rework minutes because teams follow proven steps that avoid common mistakes.<br><br>- Reduces variance across analysts which improves predictability and speeds recovery for users.<br><br>- Improves throughput because fewer cycles are spent debating approach during busy periods. | **Minutes saved** = (Δrework mins × cases applying top actions **{_fmt_int(top['records'])}**). | {ev_pa} |
| **Automate common patches** | **Phase 1 – Schedule:** Create recurring patch windows for common fixes with clear pre-checks and backout rules.<br><br>**Phase 2 – Deploy:** Use automation to execute and verify patches so manual steps are minimized.<br><br>**Phase 3 – Verify:** Track success rates and runtime to prove value and tune coverage over time. | - Reduces manual toil which directly lowers operational cost during maintenance periods.<br><br>- Increases predictability because work runs in defined windows with consistent outcomes.<br><br>- Decreases emergency changes by resolving known defects before they trigger incidents. | **Toil mins avoided** per run × runs/month. | Frequent patch-type actions imply automation opportunity. |
| **Replace over-repair with early swap** | **Phase 1 – Identify:** Use incident history to spot hardware that repeatedly fails despite repair.<br><br>**Phase 2 – Policy:** Establish an early swap policy when failure frequency crosses a threshold so customers are not impacted repeatedly.<br><br>**Phase 3 – Track:** Measure drops in recurrence and total downtime after swaps to prove the ROI. | - Avoids repeated labour on the same assets which prevents waste and frees staff for higher-value work.<br><br>- Shortens recovery timelines for affected users which improves satisfaction and productivity.<br><br>- Lowers total cost of ownership when repeat-repair assets are replaced earlier. | **Savings** = (repeat repair mins avoided × cases). | Recurrent HW-fix actions indicate repair loops. |
""",
                    "performance": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation (Live) | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Action efficacy tracking** | **Phase 1 – Attribute:** Link each preventive action to the incident set it addresses so cause and action can be measured together.<br><br>**Phase 2 – Measure:** Monitor recurrence and MTTR before and after the action is applied to quantify effect.<br><br>**Phase 3 – Iterate:** Retire actions that do not improve outcomes and expand those that do to more services. | - Concentrates effort on interventions that genuinely reduce incidents which raises overall performance.<br><br>- Speeds stabilization because ineffective actions are removed quickly from playbooks.<br><br>- Builds a data-driven improvement loop that teams can trust. | **ΔRecurrence × cases** for each action type. | Winners should grow; ineffective actions should shrink over time. |
| **Triggered playbooks from RCA** | **Phase 1 – Map:** For each common RCA, map a specific playbook that can be triggered automatically when indicators are detected.<br><br>**Phase 2 – Auto-trigger:** Integrate with monitoring or deployment pipelines so the right playbook launches at the right time.<br><br>**Phase 3 – Audit:** Track adoption and success rates to ensure the playbooks remain effective. | - Delivers faster containment because the correct steps start without delay.<br><br>- Reduces escalations by making response consistent and predictable.<br><br>- Improves learning because outcomes are measured for each trigger. | **Time-to-fix mins saved** per triggered occurrence. | Cause→action linkage reduces lag from diagnosis to fix. |
| **Monthly action-mix reviews** | **Phase 1 – Review:** Examine the top and bottom bars to assess which actions are used and which are ignored.<br><br>**Phase 2 – Decide:** Expand high-value actions and retire low-value or duplicative actions to streamline execution.<br><br>**Phase 3 – Communicate:** Share the revised action set and provide short refreshers to keep adoption high. | - Prevents process drift by keeping the toolkit focused on what works which reduces waste.<br><br>- Increases throughput because teams spend less time choosing approaches and more time executing them.<br><br>- Improves cross-team consistency which stabilizes outcomes for users. | **Waste mins reduced** from retired actions. | The visual mix highlights over- and under-used actions clearly. |
""",
                    "satisfaction": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation (Live) | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **User-facing change notes** | **Phase 1 – Summarize:** Write short notes that explain what changed, why it changed, and how users benefit.<br><br>**Phase 2 – Distribute:** Send to affected users and publish in a searchable location.<br><br>**Phase 3 – Archive:** Keep a history so users can quickly understand past improvements. | - Increases perceived quality because users understand that incidents led to tangible improvements.<br><br>- Reduces support calls after changes because expectations are clear in advance.<br><br>- Builds trust through consistent and human-readable communication. | **Complaints avoided × mins** in months after high-use actions. | Clear prevention communications reduce anxiety after incidents. |
| **Prevention roadmap** | **Phase 1 – Publish:** Share a forward roadmap of upcoming preventive actions with dates and owners.<br><br>**Phase 2 – Update:** Provide status monthly so progress is visible and delays are explained.<br><br>**Phase 3 – Feedback:** Gather user input on impact and adjust priorities when necessary. | - Aligns expectations so customers can plan around maintenance and improvements.<br><br>- Lowers escalation risk because stakeholders see progress rather than silence.<br><br>- Improves planning on both sides which reduces last-minute surprises. | **Queries avoided × mins** post-publication. | Visibility around top actions such as **{top['preventive_action']}** builds confidence. |
| **Feedback loop on effectiveness** | **Phase 1 – Survey:** Send a short pulse survey after preventive actions to capture impact in the user’s words.<br><br>**Phase 2 – Analyse:** Identify the main detractor themes and map them to changes in the playbooks.<br><br>**Phase 3 – Adjust:** Implement improvements and close the loop with users so they see their input mattered. | - Confirms which actions are genuinely helpful which improves the overall quality of prevention work.<br><br>- Converts detractors into neutrals or promoters by addressing specific pain points quickly.<br><br>- Strengthens relationships by showing responsiveness to feedback. | **Detractors flipped × impact mins**. | Sentiment improves when actions measurably reduce repeats. |
"""
                }
                render_cio_tables("CIO — Preventive Actions", cio)
            else:
                st.info("No rows available to analyse preventive actions.")
        else:
            st.warning("Column 'preventive_action' not found.")
