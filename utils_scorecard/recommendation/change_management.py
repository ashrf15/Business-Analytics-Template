import streamlit as st
import plotly.express as px
import pandas as pd

# ---------- Mesiniaga palette ----------
MES_BLUE = ["#004C99", "#007ACC", "#3399FF", "#66B2FF", "#9BD1FF"]

def render_cio_tables(title, cio_data):
    st.subheader(title)
    with st.expander("Cost Reduction"):
        st.markdown(cio_data.get("cost","_No cost recommendations._"), unsafe_allow_html=True)
    with st.expander("Performance Improvement"):
        st.markdown(cio_data.get("performance","_No performance recommendations._"), unsafe_allow_html=True)
    with st.expander("Customer Satisfaction Improvement"):
        st.markdown(cio_data.get("satisfaction","_No satisfaction recommendations._"), unsafe_allow_html=True)

def _fmt_int(x):
    try:
        return f"{int(x):,}"
    except Exception:
        return "0"

def _fmt_float(x, d=1):
    try:
        return f"{float(x):.{d}f}"
    except Exception:
        return "0.0"

def change_management(df_filtered):

    if "report_date" in df_filtered.columns:
        df_filtered["report_date"] = pd.to_datetime(df_filtered["report_date"], errors="coerce")
        df_filtered["report_month"] = df_filtered["report_date"].dt.to_period("M").astype(str)

    # ---------------------- 5(a) Successful Changes Implemented ----------------------
    with st.expander("📌 Number of Successful Changes Implemented"):
        if {"changes_successful","report_month"} <= set(df_filtered.columns):
            cm = (
                df_filtered.groupby("report_month")["changes_successful"]
                .sum().reset_index().sort_values("report_month")
            )

            fig = px.bar(
                cm, x="report_month", y="changes_successful",
                title="Successful Changes per Month",
                color_discrete_sequence=MES_BLUE, template="plotly_white"
            )
            st.plotly_chart(fig, use_container_width=True)

            if not cm.empty:
                peak = cm.loc[cm["changes_successful"].idxmax()]
                low  = cm.loc[cm["changes_successful"].idxmin()]
                total = int(cm["changes_successful"].sum())
                avg   = float(cm["changes_successful"].mean())

                st.markdown("### Analysis – Successful Changes Throughput")
                st.write(f"""
**What this graph is:** A monthly throughput chart of **successfully implemented changes**.  
**X-axis:** Calendar month.  
**Y-axis:** Count of successful changes executed.

**What it shows in your data:**  
- **Largest month:** **{peak['report_month']}** with **{_fmt_int(peak['changes_successful'])}** successful changes.  
- **Smallest month:** **{low['report_month']}** with **{_fmt_int(low['changes_successful'])}**.  
- **Average across the period:** **{_fmt_float(avg)} changes/month** with **{_fmt_int(total)}** changes total.

**Overall:** Taller bars reflect **delivery intensity**; large variance between months hints at **batching** or **calendar conflicts**.

**How to read it operationally:**  
- **Capacity signalling:** Sudden peaks require extra **pre-deploy checks** and rollback readiness.  
- **Calendar hygiene:** Adjacent busy months risk **overlap with incidents**; deconflict windows early.  
- **Quality loop:** Compare this chart against incident spikes to validate whether **change quality controls** are effective.

**Why this matters:** High change velocity is good **only if** governance keeps failure rates down—protecting uptime and costs.
""")

                ev = (
                    f"Peak **{peak['report_month']} = {_fmt_int(peak['changes_successful'])}**, "
                    f"low **{low['report_month']} = {_fmt_int(low['changes_successful'])}**, "
                    f"avg **{_fmt_float(avg)}**; total **{_fmt_int(total)}**."
                )

                # ---- CIO tables (expanded explanations and benefits) ----
                cio = {
                    "cost": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation (from graph) | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Batch non-urgent changes into consolidated windows** | **Phase 1 – Identify:** Group routine and low-risk changes into predictable monthly windows and document the selection criteria so teams understand what qualifies. <br><br> **Phase 2 – Coordinate:** Align testing, approvers and release engineers to a single window and publish a shared checklist so duplicate work is removed. <br><br> **Phase 3 – Execute:** Run a single CAB slot with a standard rollback plan and capture metrics for prep time and incident spillover to validate the consolidation effect. | - Reduces repeated preparation work because many changes share the same window and checklist. <br><br> - Lowers overtime because fewer scattered after-hours releases are required across the month. <br><br> - Decreases vendor coordination cost because engagements are bundled into fewer sessions. <br><br> - Improves financial predictability because change effort is concentrated and measured. | **Admin mins saved** = (Old windows − New windows) × **prep mins/window**. Use peak month overage **{_fmt_int(peak['changes_successful'] - int(avg))}** to justify consolidation. | {ev} |
| **Template change records (pre-approved CR types)** | **Phase 1 – Codify:** Create standardised CR forms for repetitive tasks and prefill risk, testing and backout sections so submissions are consistent. <br><br> **Phase 2 – Gate:** Auto approve documented low-risk types within guardrails and log exceptions for manual CAB review so quality stays high. <br><br> **Phase 3 – Audit:** Review template effectiveness quarterly and retire templates that generate noise or rework. | - Cuts administrative time per CR because authors complete fewer unique fields. <br><br> - Lowers documentation errors because required information is prestructured and visible. <br><br> - Increases throughput during busy months because low-risk work flows without waiting. <br><br> - Improves audit readiness because standard records are easier to verify. | **Minutes saved** = (template mins saved × total CRs **{_fmt_int(total)}**). | Repetition implied by sustained volume; templates remove waste. |
| **Off-peak scheduling policy** | **Phase 1 – Segment:** Mark non-disruptive changes that can be executed in low-demand periods and record business owner approval for timing. <br><br> **Phase 2 – Schedule:** Place these changes into off-hours or quiet windows where user impact is minimal and confirm support coverage. <br><br> **Phase 3 – Measure:** Compare incident and performance spillover before and after the policy to ensure the shift reduces impact. | - Reduces premium staffing cost because support resources are planned for fewer concentrated windows. <br><br> - Lowers user-visible disruption because execution happens when traffic is naturally low. <br><br> - Smooths business as usual activities because daytime remediation and follow ups are minimized. <br><br> - Strengthens confidence in the release plan because outcomes are more consistent. | **Premium cost avoided** = (off-hours delta × CRs moved **{_fmt_int(total)}**). | Busy months (e.g., {peak['report_month']}) amplify savings from off-peak moves. |
""",
                    "performance": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation (from graph) | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Pre-deploy quality gates** | **Phase 1 – Checklist:** Apply a peer review, configuration validation and static analysis checklist to each CR and track completion status. <br><br> **Phase 2 – Smoke tests:** Execute automated smoke tests in staging environments that mirror production and record pass or fail with logs attached. <br><br> **Phase 3 – Approve:** Approve only when checks pass and reject or rework changes that miss the threshold with clear feedback. | - Lowers rollback probability because defects are caught before reaching users. <br><br> - Improves mean time to restore after issues because problems are smaller and easier to diagnose. <br><br> - Keeps throughput steady during peak months because fewer changes return for rework. <br><br> - Raises engineering discipline because gates are visible and measurable. | **MTTR mins saved** = (ΔMTTR × changes in peak month **{_fmt_int(peak['changes_successful'])}**). | High throughput months expand risk surface—gates keep quality stable. |
| **48-hour post-change guardrails** | **Phase 1 – Instrument:** Add targeted monitors and golden signals for each change with thresholds tailored to expected behaviour. <br><br> **Phase 2 – Watch:** Actively observe the first 48 hours and route anomalies to an on-call engineer with clear runbooks. <br><br> **Phase 3 – Rollback fast:** Provide one-click rollback and verify service recovery with a short checklist. | - Enables earlier regression detection because signals are tuned to the exact change. <br><br> - Reduces prolonged incidents because unhealthy versions are reversed quickly. <br><br> - Improves SLA adherence because time spent in degraded states is shorter. <br><br> - Increases deploy confidence across teams because protections are reliable. | **Minutes saved** = (early-detect mins × CRs in months > avg **{_fmt_int((cm['changes_successful'] > avg).sum())}**). | Variability around peaks calls for short-term guardrails. |
| **Change calendar hygiene** | **Phase 1 – Visualize:** Display overlaps, blackouts and dependency chains in a single calendar so conflicts are obvious. <br><br> **Phase 2 – Deconflict:** Move non critical changes out of risky clusters and confirm approvals with stakeholders. <br><br> **Phase 3 – Enforce:** Introduce CAB rules that block conflicts and require justification for exceptions. | - Reduces compounded incidents because risky overlaps are removed before execution. <br><br> - Improves capacity utilisation because resources are spread across time instead of colliding. <br><br> - Raises delivery predictability because fewer last minute moves are necessary. <br><br> - Enhances stakeholder planning because the calendar communicates constraints. | **Incidents avoided mins** = (overlap reductions × avg incident mins). | Peaks adjacent to other busy windows suggest collision risk. |
""",
                    "satisfaction": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation (from graph) | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Early maintenance communications** | **Phase 1 – Plan:** Publish a monthly change calendar with affected services and expected impact so users can plan work. <br><br> **Phase 2 – Notify:** Send reminders at T-7 and T-1 with clear ETAs and contact points for escalation. <br><br> **Phase 3 – Update:** Issue a T+15 status update if there are delays or deviations and include next steps. | - Decreases complaints because stakeholders know what will change and when. <br><br> - Lowers the volume of status queries because timelines and ETAs are visible. <br><br> - Improves business planning because teams align their deployments with the calendar. <br><br> - Increases perceived professionalism because communications are proactive and consistent. | **Tickets avoided mins** = (status queries avoided × mins/query) during months > avg (**{_fmt_int((cm['changes_successful'] > avg).sum())} months**). | Spikes drive user queries—proactive notices defuse them. |
| **Success reporting** | **Phase 1 – Summarize:** Provide a monthly summary of delivered outcomes, performance improvements and defect reductions tied to changes. <br><br> **Phase 2 – Share:** Distribute the summary to business stakeholders and support teams so the value is visible. <br><br> **Phase 3 – Archive:** Store the reports in a knowledge base linked to change IDs for future reference. | - Increases trust because stakeholders can see tangible benefits from releases. <br><br> - Reduces resistance to future windows because recent wins are documented. <br><br> - Lowers follow up questions because the summary answers common queries. <br><br> - Improves organisational memory because evidence is searchable. | **Minutes saved** via fewer escalations after positive updates. | High success counts are evidence worth sharing. |
| **Transparent rollback comms** | **Phase 1 – Own it:** Publish a plain language incident note that explains what went wrong and who is working on the fix. <br><br> **Phase 2 – Remedy:** Provide an ETA to stabilise and state the mitigation steps users should take. <br><br> **Phase 3 – Learn:** Link the final RCA and the preventive action so customers see improvement. | - Limits dissatisfaction because customers feel informed during disruption. <br><br> - Preserves credibility because ownership and timing are communicated clearly. <br><br> - Reduces repeated chasers because updates arrive on a known cadence. <br><br> - Protects long term trust because learning is demonstrated after closure. | **Complaint mins avoided** linked to peak month communications. | Clear comms soften impact when issues follow busy release cycles. |
"""
                }
                render_cio_tables("CIO — Successful Changes", cio)
        else:
            st.warning("Need 'changes_successful' & 'report_date'.")

    # ---------------------- 5(b) Emergency Changes ----------------------
    with st.expander("📌 Number of Emergency Changes"):
        if {"changes_emergency","report_month"} <= set(df_filtered.columns):
            em = (
                df_filtered.groupby("report_month")["changes_emergency"]
                .sum().reset_index().sort_values("report_month")
            )
            fig = px.line(
                em, x="report_month", y="changes_emergency", markers=True,
                title="Emergency Changes per Month",
                color_discrete_sequence=MES_BLUE, template="plotly_white"
            )
            st.plotly_chart(fig, use_container_width=True)

            if not em.empty:
                peak = em.loc[em["changes_emergency"].idxmax()]
                low  = em.loc[em["changes_emergency"].idxmin()]
                total = int(em["changes_emergency"].sum())
                avg   = float(em["changes_emergency"].mean())

                st.markdown("### Analysis – Emergency Change Trend")
                st.write(f"""
**What this graph is:** A monthly trend of **emergency (unplanned) changes**.  
**X-axis:** Calendar month.  
**Y-axis:** Count of emergency changes.

**What it shows in your data:**  
- **Largest emergency month:** **{peak['report_month']}** with **{_fmt_int(peak['changes_emergency'])}** emergencies.  
- **Lowest month:** **{low['report_month']}** with **{_fmt_int(low['changes_emergency'])}**.  
- **Average across the period:** **{_fmt_float(avg)} emergencies/month** with **{_fmt_int(total)}** total.

**Overall:** Elevated emergencies indicate **planning gaps** or **environmental instability**.

**How to read it operationally:**  
- **Lead–lag:** Check adjacency to incident spikes; coupling implies reactive fixes.  
- **Seasonality:** Recurring months suggest structural drivers (e.g., vendor cycles).  
- **Control:** Aim to keep emergencies **near zero** via pre-approved kits and hard gates.

**Why this matters:** Emergencies are expensive, risky, and often user-visible—minimizing them protects cost and trust.
""")

                ev_em = (
                    f"Emergency peak **{peak['report_month']} = {_fmt_int(peak['changes_emergency'])}**, "
                    f"low **{low['report_month']} = {_fmt_int(low['changes_emergency'])}**, "
                    f"avg **{_fmt_float(avg)}**, total **{_fmt_int(total)}**."
                )

                cio = {
                    "cost": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation (from graph) | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Plan-first to shift work out of emergency path** | **Phase 1 – Detect:** Identify the categories and services that drive emergencies during **{peak['report_month']}** and quantify common triggers. <br><br> **Phase 2 – Re-route:** Convert recurring emergency work into standard CRs using templates and clear lead times so it enters the normal pipeline. <br><br> **Phase 3 – Monitor:** Audit monthly to ensure re routed work stays in standard flow and publish a reduction target. | - Reduces after hours premiums because fewer issues require urgent late execution. <br><br> - Lowers firefighting overhead because work is planned and resourced ahead of time. <br><br> - Stabilises change related costs because demand becomes predictable. <br><br> - Improves budget forecasting because emergency variance is reduced. | **Premium mins avoided** = (emergencies above avg **{_fmt_int(peak['changes_emergency'] - int(avg))}**) × **mins/emergency** × **rate**. | {ev_em} |
| **Pre-approved remediation kits** | **Phase 1 – Catalogue:** List the top emergency fixes and standardise the scripts and steps with clear preconditions. <br><br> **Phase 2 – Automate:** Package the fixes into runbooks and automation playbooks with logging and safeguards. <br><br> **Phase 3 – Drill:** Practise on call execution quarterly so responders are fluent and confident. | - Speeds execution because responders follow a tested kit rather than improvising. <br><br> - Shortens service impact because recovery steps start immediately. <br><br> - Reduces escalations because the first team can resolve more incidents. <br><br> - Raises consistency of fixes because each run follows the same steps. | **MTTR mins saved** × emergencies in >avg months (**{_fmt_int((em['changes_emergency'] > avg).sum())} months**). | Repetition implies kit potential. |
| **Eliminate root triggers via RCA link-back** | **Phase 1 – Tie:** Link every emergency to a root cause record and describe the preventive change needed to remove the trigger. <br><br> **Phase 2 – Fix:** Prioritise the preventive changes in the next window and track delivery to closure. <br><br> **Phase 3 – Verify:** Confirm that the category drops in the following month and keep the counter visible. | - Delivers a sustainable reduction in emergencies because causes are removed. <br><br> - Improves predictability of the environment because fewer surprises occur. <br><br> - Increases CAB capacity for strategic work because fire fighting decreases. <br><br> - Strengthens quality culture because teams close the loop from failure to fix. | **Emergencies avoided** = (avg − new avg) × months. | Declines post-fix validate impact. 
""",
                    "performance": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation (from graph) | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **On-call readiness drills** | **Phase 1 – Simulate:** Run monthly scenario based drills that mirror recent emergencies and measure response time. <br><br> **Phase 2 – Measure:** Track detection time, handoff quality and fix duration with a simple scorecard. <br><br> **Phase 3 – Improve:** Close gaps with targeted training and playbook updates. | - Lowers mean time to restore because responders practice realistic workflows. <br><br> - Tightens cross team coordination because handoffs are rehearsed. <br><br> - Reduces the tail of long incidents because teams recognise patterns earlier. <br><br> - Builds confidence for rare but high impact events because muscle memory exists. | **ΔMTTR mins × emergencies** in peak month **{_fmt_int(peak['changes_emergency'])}**. | Preparedness directly reduces the longest bars. |
| **Guardrails & blackouts** | **Phase 1 – Define:** Establish no change windows around fiscal closes, major launches and vendor maintenance and publish them early. <br><br> **Phase 2 – Enforce:** Apply CAB rules that block deployments inside blackout periods unless a risk waiver is approved. <br><br> **Phase 3 – Review:** Revisit exceptions monthly and remove patterns that create repeated risk. | - Reduces cascades into incidents because risky periods are protected. <br><br> - Increases service stability because fewer changes occur when the environment is sensitive. <br><br> - Improves adherence to operational rhythms because teams plan around known constraints. <br><br> - Lowers rework because fewer reversals are required. | **Incidents avoided mins** attributed to reduced emergencies above avg **{_fmt_int(max(0, int(avg) - int(low['changes_emergency'])))}**. | Correlation between emergencies and incidents merits guardrails. |
| **Post-mortems within 48h** | **Phase 1 – Template:** Use a blameless RCA template that captures timeline, impact, causes and corrective actions with owners. <br><br> **Phase 2 – Actions:** Assign due dates and make progress visible to leadership to maintain momentum. <br><br> **Phase 3 – Track:** Verify action completion and measure category level incident reduction. | - Accelerates learning because insights are captured while context is fresh. <br><br> - Reduces repeat incidents because actions are owned and completed. <br><br> - Improves stakeholder confidence because remediation is transparent. <br><br> - Builds an evidence base for investment because high cost patterns are quantified. | **Repeat reduction** estimated from drop after **{peak['report_month']}**. | Trend down after disciplined RCAs evidences impact. |
""",
                    "satisfaction": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation (from graph) | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Honest, timely updates during emergencies** | **Phase 1 – Notify:** Send a T+15 update that states the scope, suspected cause and next update time in plain language. <br><br> **Phase 2 – Cadence:** Provide hourly progress and ETA updates until stability returns and keep the same channel. <br><br> **Phase 3 – Close:** Publish a short summary and where to find the full postmortem. | - Reduces complaints because customers receive clear and timely information. <br><br> - Lowers chaser volume because stakeholders know when the next update will arrive. <br><br> - Preserves trust because accountability is visible during high stress moments. <br><br> - Improves agent efficiency because fewer duplicate tickets are created. | **Complaint mins avoided** tied to peak overage **{_fmt_int(peak['changes_emergency'] - int(avg))}**. | Users react strongly to peak months; comms dampen impact. |
| **Publish ETAs and status page** | **Phase 1 – Surface:** Provide a real time status page that shows current impact, affected components and ETA to recover. <br><br> **Phase 2 – Integrate:** Feed updates into the customer portal and email lists so users do not need to search. <br><br> **Phase 3 – Review:** Send a short survey after resolution to validate whether information quality met expectations. | - Reduces anxiety for users because service status is visible without contacting support. <br><br> - Improves perceived responsiveness because updates are pushed automatically. <br><br> - Decreases the number of “any update” contacts because information is centralised. <br><br> - Increases data for improvement because survey feedback highlights gaps. | **Queries avoided mins** in months over avg (**{_fmt_int((em['changes_emergency'] > avg).sum())} months**). | Visibility lowers inbound noise when line spikes. |
| **“What changed” follow-ups** | **Phase 1 – Clarify:** Send a note that explains the fix applied and the services affected using simple terms. <br><br> **Phase 2 – Prevent:** Describe the preventive steps taken to avoid a repeat and include owner names. <br><br> **Phase 3 – Log:** Create a knowledge base entry that customers and agents can reference next time. | - Increases confidence that the problem is truly solved because the remedy is transparent. <br><br> - Enables better self service next time because knowledge is published and searchable. <br><br> - Reduces future ticket volume because users can verify outcomes themselves. <br><br> - Strengthens partnership with key accounts because communication is proactive. | **Detractors avoided** after peak months. | Post-event clarity stabilizes satisfaction.
"""
                }
                render_cio_tables("CIO — Emergency Changes", cio)
        else:
            st.warning("Need 'changes_emergency' & 'report_date'.")

    # ---------------------- 5(c) SLA Adherence for Change Implementations ----------------------
    with st.expander("📌 SLA Adherence for Change Implementations"):

        # Step 1: Detect dropped SLA columns and restore if necessary
        if "sla_change_adherence" not in df_filtered.columns:
            possible_cols = [c for c in df_filtered.columns if "sla" in c and "change" in c]
            if possible_cols:
                st.info(f"ℹ️ Using '{possible_cols[0]}' as SLA Change Adherence source column.")
                df_filtered["sla_change_adherence"] = df_filtered[possible_cols[0]]
            else:
                st.error("❌ No SLA Change Adherence column found — it might have been dropped due to missing data.")
                st.stop()

        # Step 2: Build chart
        ch = df_filtered["sla_change_adherence"].value_counts(dropna=False).reset_index()
        ch.columns = ["sla_change_adherence","records"]
        fig = px.bar(
            ch, x="sla_change_adherence", y="records", title="Change SLA Adherence",
            color_discrete_sequence=MES_BLUE, template="plotly_white"
        )
        st.plotly_chart(fig, use_container_width=True)

        if not ch.empty:
            total = int(ch["records"].sum())
            miss = int(ch.loc[ch["sla_change_adherence"].isna(),"records"].sum()) if ch["sla_change_adherence"].isna().any() else 0

            met = int(ch.loc[ch["sla_change_adherence"] == "Met", "records"].sum()) if "Met" in ch["sla_change_adherence"].values else 0
            not_met = int(ch.loc[ch["sla_change_adherence"] == "Not Met", "records"].sum()) if "Not Met" in ch["sla_change_adherence"].values else 0

            pct_met = (met / total * 100) if total else 0.0
            pct_not = (not_met / total * 100) if total else 0.0
            pct_mis = (miss / total * 100) if total else 0.0

            st.markdown("### Analysis – Change SLA Distribution")
            st.write(f"""
**What this graph is:** A distribution of **SLA adherence** statuses for changes.  
**X-axis:** SLA category (*Met*, *Not Met*, *Missing*).  
**Y-axis:** Number of change records.

**What it shows in your data:**  
- **Met:** **{_fmt_int(met)}** (**{_fmt_float(pct_met)}%**)  
- **Not Met:** **{_fmt_int(not_met)}** (**{_fmt_float(pct_not)}%**)  
- **Missing:** **{_fmt_int(miss)}** (**{_fmt_float(pct_mis)}%**)  
- **Total:** **{_fmt_int(total)}** records.

**Overall:** Any **Not Met** or **Missing** segment reflects **process friction** and audit risk.

**How to read it operationally:**  
- **Triage:** Attack **Not Met** with root-cause reviews per change type.  
- **Governance:** Eliminate **Missing** via mandatory fields and service→SLA auto-mapping.  
- **Control:** Watch month-over-month movement to verify improvement.

**Why this matters:** Strong SLA adherence signals **predictable delivery** and **lower incident spillover** from changes.
""")

            ev_sla = (
                f"Met **{_fmt_int(met)} ({_fmt_float(pct_met)}%)**, "
                f"Not Met **{_fmt_int(not_met)} ({_fmt_float(pct_not)}%)**, "
                f"Missing **{_fmt_int(miss)} ({_fmt_float(pct_mis)}%)**, total **{_fmt_int(total)}**."
            )

            cio = {
                "cost": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation (from graph) | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Template scheduling to fit SLA constraints** | **Phase 1 – Define:** Set window lengths and lead times by CR type and include examples so requestors choose the right slot. <br><br> **Phase 2 – Enforce:** Have CAB validate schedule fit and require adjustments when lead times are insufficient. <br><br> **Phase 3 – Adjust:** Iterate monthly using adherence and incident data to refine windows and templates. | - Reduces rework from late steps because submissions follow realistic timelines. <br><br> - Lowers after hours premiums because fewer urgent reschedules are needed. <br><br> - Stabilises team capacity because work arrives evenly across planned windows. <br><br> - Improves planning accuracy because duration expectations are explicit. | **Rework mins saved** = (**Not Met = {_fmt_int(not_met)}** × avg overage mins). | {ev_sla} |
| **Pre-approvals for low-risk CRs** | **Phase 1 – Catalogue:** Identify low risk change types and document clear guardrails so the scope is unambiguous. <br><br> **Phase 2 – Auto-approve:** Allow these types to proceed without full CAB while logging all details for oversight. <br><br> **Phase 3 – Audit:** Sample a subset monthly to confirm outcomes remain safe and adjust guardrails when needed. | - Speeds cycle time because straightforward changes do not wait in queues. <br><br> - Reduces CAB load because attention is focused on truly risky items. <br><br> - Improves adherence rate because delays from approvals are removed. <br><br> - Increases engineer satisfaction because bureaucracy for simple tasks is reduced. | **CAB mins saved** = (mins/CR × low-risk CR count). | Raising Met share above **{_fmt_float(pct_met)}%** cuts queueing. |
| **Backfill & block Missing** | **Phase 1 – Backfill:** Clear the current **Missing = {_fmt_int(miss)}** by contacting owners and updating records with the correct SLA. <br><br> **Phase 2 – Validate:** Add mandatory field rules at intake that block submission when SLA is empty and show guidance. <br><br> **Phase 3 – Map:** Implement service to SLA defaults so the system suggests a value when owners are unsure. | - Avoids audit toil because records are complete and verified. <br><br> - Improves reporting quality because gaps are removed at the source. <br><br> - Enables better forecasting because SLA assumptions are explicit. <br><br> - Decreases correction work later because submissions enter clean. | **Lookup mins avoided** = {_fmt_int(miss)} × mins/record. | Missing bucket materially visible in chart. |
""",
                "performance": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation (from graph) | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Calendar deconfliction** | **Phase 1 – Visual:** Build a calendar view that shows no go windows, dependencies and resource conflicts. <br><br> **Phase 2 – Move:** Shift conflicting changes to alternate slots and confirm alignment with owners and support teams. <br><br> **Phase 3 – Monitor:** Track the SLA hit rate each month and publish a trend to show improvement. | - Increases percentage of Met because schedules fit capacity and constraints. <br><br> - Reduces spillover incidents because risky overlaps are avoided. <br><br> - Creates smoother operational flow because handoffs are not overloaded. <br><br> - Enhances transparency because teams can see constraints early. | **%Met uplift** measured month over month from baseline **{_fmt_float(pct_met)}%**. | Not Met share **{_fmt_float(pct_not)}%** indicates calendar/process friction. |
| **Go/No-Go risk gates** | **Phase 1 – Checks:** Require explicit impact assessment, rollback viability and monitoring readiness before approval. <br><br> **Phase 2 – Block:** Prevent deployment when checks fail and record actions needed to pass. <br><br> **Phase 3 – Learn:** Perform RCA on failed gates to improve design and documentation quality. | - Reduces blowups because weak changes are intercepted before release. <br><br> - Speeds stabilisation because rollback readiness is confirmed. <br><br> - Improves predictability because only prepared changes progress. <br><br> - Strengthens engineering standards because evidence is required at approval. | **Incidents avoided mins** linked to Not Met count **{_fmt_int(not_met)}**. | Not Met bucket correlates with weak gates. |
| **24–48h post-change reviews** | **Phase 1 – Watch:** Monitor key metrics and logs in the first two days and document thresholds that trigger action. <br><br> **Phase 2 – Fix:** Address quick regressions with preapproved playbooks and confirm recovery in monitoring. <br><br> **Phase 3 – Close:** Capture lessons and update templates and runbooks so the improvement persists. | - Detects issues earlier which reduces the time customers experience degradation. <br><br> - Prevents long tails because small regressions are resolved before they escalate. <br><br> - Increases confidence in releases because early life health is verified. <br><br> - Improves knowledge assets because runbooks evolve after every review. | **MTTR mins saved** × total changes **{_fmt_int(total)}**. | Early checks shrink fallout from risky windows. |
""",
                "satisfaction": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation (from graph) | Evidence & Graph Interpretation |
|---|---|---|---|---|
| **Published change schedule** | **Phase 1 – Calendar:** Provide a public view of upcoming changes with impact notes and contact details. <br><br> **Phase 2 – Notifications:** Send reminders at T-7 and T-1 so customers can plan and raise conflicts. <br><br> **Phase 3 – Update:** Communicate delays and reschedules promptly with revised ETAs. | - Reduces complaints because stakeholders are informed ahead of time. <br><br> - Improves business planning because teams align their work with scheduled changes. <br><br> - Increases trust because the process is transparent and predictable. <br><br> - Lowers surprise related escalations because expectations are clear. | **Queries avoided mins** proportional to **Not Met + Missing = {_fmt_int(not_met + miss)}** exposure. | Visibility counters anxiety from non-adherent cases. |
| **Outcome notes for major changes** | **Phase 1 – Summarize:** Provide a concise note on the benefits realised, defects fixed and performance impact after major releases. <br><br> **Phase 2 – Share:** Send the note to stakeholders and frontline teams so messaging is consistent. <br><br> **Phase 3 – Archive:** Store notes in a knowledge base and link them to CR IDs for traceability. | - Improves perception of value because results are explained in business terms. <br><br> - Reduces “what changed” tickets because information is available on demand. <br><br> - Supports account conversations because proof points are documented. <br><br> - Enhances alignment between IT and business because outcomes are shared widely. | **Minutes avoided** via fewer follow-ups after months with high **Met = {_fmt_int(met)}**. | High Met months are proof points to communicate. |
| **Breach apology with fix path** | **Phase 1 – Own:** Explain why the SLA was missed in plain language and state the impact clearly. <br><br> **Phase 2 – Remedy:** Describe the specific preventive actions that will be taken and who is responsible. <br><br> **Phase 3 – Commit:** Provide a realistic timeline and confirm when the fix is complete. | - Restores confidence because the problem and remedy are clearly owned. <br><br> - Lowers escalations because customers understand what will change next. <br><br> - Protects NPS because timely remediation shows accountability. <br><br> - Encourages constructive dialogue because expectations are set and met. | **Escalation mins avoided** tied to **Not Met = {_fmt_int(not_met)}**. | Honest comms mitigate impact of missed SLAs. |
"""
            }
            render_cio_tables("CIO — Change SLA", cio)
        else:
            st.warning("Column 'sla_change_adherence' not found.")
