# utils_scorecard/recommendation/service_availability.py

import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np

# ========== Mesiniaga Theme ==========
MES_BLUE = ["#004C99", "#007ACC", "#3399FF", "#66B2FF", "#9BD1FF"]

def _fmt_int(n):
    try:
        return f"{int(n):,}"
    except Exception:
        return "0"

def _fmt_float(x, d=2):
    try:
        return f"{float(x):.{d}f}"
    except Exception:
        return "0.00"

def render_cio_tables(title, cio_data):
    st.subheader(title)
    with st.expander("Cost Reduction"):
        st.markdown(cio_data.get("cost", "_No cost recommendations._"), unsafe_allow_html=True)
    with st.expander("Performance Improvement"):
        st.markdown(cio_data.get("performance", "_No performance recommendations._"), unsafe_allow_html=True)
    with st.expander("Customer Satisfaction Improvement"):
        st.markdown(cio_data.get("satisfaction", "_No satisfaction recommendations._"), unsafe_allow_html=True)

def service_availability(df_filtered: pd.DataFrame):

    # Ensure month column
    if "report_date" in df_filtered.columns:
        df_filtered["report_date"] = pd.to_datetime(df_filtered["report_date"], errors="coerce")
        df_filtered["report_month"] = df_filtered["report_date"].dt.to_period("M").astype(str)

    # ---------------------- Uptime & Availability of Critical Services ----------------------
    with st.expander("📌 Uptime & Availability of Critical Services"):

        # Step 1: Recreate report_month from report_date (if it exists)
        if "report_date" in df_filtered.columns:
            df_filtered["report_month"] = (
                pd.to_datetime(df_filtered["report_date"], errors="coerce")
                .dt.to_period("M")
                .astype(str)
            )
        else:
            st.warning("⚠️ 'report_date' not found — cannot compute monthly trends.")
            st.stop()

        # Step 2: Ensure 'uptime_percent' exists or derive from related column
        if "uptime_percent" not in df_filtered.columns:
            possible_uptime_cols = [c for c in df_filtered.columns if ("uptime" in c) or ("availability" in c)]
            if possible_uptime_cols:
                df_filtered["uptime_percent"] = pd.to_numeric(df_filtered[possible_uptime_cols[0]], errors="coerce")
                st.info(f"ℹ️ Using '{possible_uptime_cols[0]}' as uptime source column.")
            else:
                st.error("❌ No 'uptime_percent' or related column found in dataset.")
                st.stop()
        else:
            df_filtered["uptime_percent"] = pd.to_numeric(df_filtered["uptime_percent"], errors="coerce")

        # Step 3: Clean and group
        df_clean = df_filtered.dropna(subset=["uptime_percent", "report_month"])
        if df_clean.empty:
            st.warning("⚠️ No valid uptime data found after cleaning.")
            st.stop()

        ts = (
            df_clean.groupby("report_month")["uptime_percent"]
            .mean()
            .reset_index()
            .sort_values("report_month")
        )

        # Step 4: Chart
        fig = px.line(
            ts,
            x="report_month",
            y="uptime_percent",
            markers=True,
            title="Monthly Uptime % (mean)",
            labels={"report_month": "Month", "uptime_percent": "Average Uptime (%)"},
            color_discrete_sequence=MES_BLUE,
            template="plotly_white",
        )
        st.plotly_chart(fig, use_container_width=True)

        # Step 5: Analysis
        if not ts.empty:
            peak = ts.loc[ts["uptime_percent"].idxmax()]
            low = ts.loc[ts["uptime_percent"].idxmin()]
            mean = ts["uptime_percent"].mean()
            sd = ts["uptime_percent"].std(ddof=0) if len(ts) > 1 else 0.0

            st.markdown("### Analysis")
            st.write(f"""
**What this graph is:** A monthly line chart comparing **average service uptime (%)** by month.  
**X-axis:** Calendar month.  
**Y-axis:** Mean uptime percentage across services.

**What it shows in your data:**  
- **Largest uptime month:** **{peak['report_month']}** with **{_fmt_float(peak['uptime_percent'])}%**  
- **Lowest uptime month:** **{low['report_month']}** with **{_fmt_float(low['uptime_percent'])}%**  
- **Average over the period:** **{_fmt_float(mean)}%**, **Std Dev:** **{_fmt_float(sd)}**

**Overall:** When the line dips below the long-run mean (**{_fmt_float(mean)}%**), reliability risk increases; sustained sequences above mean indicate stable operations.

**How to read it operationally:**  
- **Gap to target:** The vertical distance from your SLO/SLA target to the line estimates shortfall.  
- **Lead–lag vs. changes:** If dips align with change windows, tighten release guardrails.  
- **Recovery strength:** Faster rebounds after troughs signal healthier incident handling.  
- **Control:** Hold the series near a high flatline via WIP limits, golden paths, and release freeze criteria.

**Why this matters:** Uptime is the heartbeat of service quality. Keeping it close to target prevents ticket surges, SLA breaches, and customer churn.
""")

            ev = (
                f"Peak **{peak['report_month']} = {_fmt_float(peak['uptime_percent'])}%**, "
                f"Lowest **{low['report_month']} = {_fmt_float(low['uptime_percent'])}%**, "
                f"Average **{_fmt_float(mean)}%**, Std Dev **{_fmt_float(sd)}**."
            )

            # ---------- CIO: Uptime & Availability (Benefits expanded; Explanations elaborated) ----------
            cio = {
                "cost": f"""
            | Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence |
            |---|---|---|---|---|
            | **Suppress duplicate alerts** | **Phase 1 – Identify:** Analyze the alert stream during low months such as **{low['report_month']}** and locate patterns of repeated notifications from the same underlying issue. Explain the approach to correlate alerts by source, signature and time window to isolate flapping rules. <br><br> **Phase 2 – Dedupe:** Implement cooldown periods and rate limits that collapse repeated signals into a single actionable event and document the deduplication logic so operations understands the behavior. <br><br> **Phase 3 – Review:** Produce a weekly false positive report that lists the top noisy rules and decisions taken so the rulebase continually improves. | - Cuts paging and overtime because engineers are not woken up for the same event repeatedly. <br><br> - Reduces analyst context switching because fewer irrelevant alerts arrive during triage. <br><br> - Shrinks the alert queue which lets real incidents surface and be handled faster. <br><br> - Lowers tooling cost over time because unnecessary alert routes and integrations are pruned. | **Savings = (Alerts suppressed × avg reaction mins × rate).** | {ev} |
            | **Bundle maintenance windows** | **Phase 1 – Cluster:** Group related changes into fixed windows and describe the calendar policy that concentrates risk into planned periods. <br><br> **Phase 2 – Prep:** Use a single communications plan and a single CAB session per window and include rollback readiness so each change arrives with the same quality bar. <br><br> **Phase 3 – Measure:** Track the reduction in preparation and administration time per change and report on incidents that spill over after windows to validate stability. | - Lowers preparation cycles per month because teams brief once for multiple changes. <br><br> - Reduces coordination overhead across owners because approvals and testing align to one timeline. <br><br> - Creates predictable stakeholder notifications that reduce follow up traffic. <br><br> - Decreases change collision risk because fewer ad hoc releases occur outside the window. | **Savings = (Maintenance windows reduced × prep mins).** | Troughs likely align with change clusters; {ev} |
            | **Right-size monitoring thresholds** | **Phase 1 – Baseline:** Calibrate thresholds around the observed mean of **{_fmt_float(mean)}%** with guardbands derived from the standard deviation of **{_fmt_float(sd)}** and explain the rationale to stakeholders. <br><br> **Phase 2 – Tune:** Convert alerts to SLO based triggers that fire on user impact rather than raw infrastructure signals and document exception paths. <br><br> **Phase 3 – Guard:** Run nightly anomaly detection jobs and review deltas so rules adapt to seasonality without drifting into noise. | - Cuts false positives because alerts fire only when real risk to users is detected. <br><br> - Shortens mean time to acknowledge because engineers see fewer irrelevant pages. <br><br> - Protects on call capacity during peak demand because noise is suppressed. <br><br> - Improves post incident signal quality which accelerates root cause analysis. | **Benefit = (False positives cut × triage mins).** | Variability around mean implies over-alerting; {ev} |
            | **Error-budget policy** | **Phase 1 – Define:** Establish a burn rate threshold that pauses risky changes when error budget consumption accelerates and publish examples so teams know how it applies. <br><br> **Phase 2 – Enforce:** Add a CAB gate that requires explicit approval to proceed during burn and capture justifications for audit. <br><br> **Phase 3 – Audit:** Perform burn postmortems that review causes and corrective actions so release behavior improves over time. | - Prevents stacked failures because fragile periods are protected from additional change risk. <br><br> - Reduces incident minutes in bad months by limiting exposure while the platform recovers. <br><br> - Stabilizes SLA attainment without adding headcount by focusing on risk control. <br><br> - Increases engineering focus on quality because burn events have visible governance. | **Incidents avoided × avg MTTR × rate** during months below mean. | Low month **{low['report_month']}** marks risk; {ev} |
            """,
                "performance": f"""
            | Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence |
            |---|---|---|---|---|
            | **48-hour post-change guardrails** | **Phase 1 – Extra sensors:** Instrument canary releases and golden signals immediately after deploys and describe the acceptance criteria for health. <br><br> **Phase 2 – Auto-rollback rules:** Configure automated rollback when predefined error spikes or latency breaches are detected and document the trigger logic so teams trust the safety net. <br><br> **Phase 3 – Review:** Maintain hotfix playbooks and run short retrospectives after each guardrail event to harden patterns. | - Enables earlier regression detection which reduces the blast radius of bad changes. <br><br> - Lowers the probability of prolonged incidents because unhealthy versions are rolled back quickly. <br><br> - Delivers faster return to baseline which supports higher deploy frequency safely. <br><br> - Boosts deploy confidence among teams because safety mechanisms are reliable. | **Minutes saved vs. late detection × incidents.** | Faster rebounds after troughs confirm effect; {ev} |
            | **Per-service uptime drilldown** | **Phase 1 – Rank:** Identify the bottom decile services by uptime and explain the scoring model used for ranking. <br><br> **Phase 2 – Fix:** Drive the top three defect themes per service with owners and time bound actions and capture before and after metrics. <br><br> **Phase 3 – Track:** Monitor uplift against the fleet mean and adjust investment to lift the floor quickly. | - Targets underperformers for rapid operational wins that are visible to stakeholders. <br><br> - Raises the fleet floor so systemic volatility is reduced across services. <br><br> - Shrinks repeat incident patterns which improves stability. <br><br> - Improves predictability for dependent teams because weak links are addressed first. | **SLA uplift (%) × service volume.** | Mean hides weak services; {ev} |
            | **Change freeze on high burn** | **Phase 1 – Thresholds:** Define deviation triggers from **{_fmt_float(mean)}%** that automatically propose a freeze and communicate this policy widely. <br><br> **Phase 2 – CAB:** Enforce a governance step that pauses releases until error rates and uptime recover to safe levels. <br><br> **Phase 3 – Exit:** Resume with controlled canaries and additional monitoring to prevent relapse. | - Avoids compounding outages by reducing risky changes when the platform is unstable. <br><br> - Keeps backlog controllable because teams are not firefighting avoidable incidents. <br><br> - Protects customer experience during fragile windows by privileging stability. <br><br> - Preserves delivery cadence long term because freezes are short and purposeful. | **Incidents avoided × MTTR × rate.** | Low month pinpoints risk; {ev} |
            """,
                "satisfaction": f"""
            | Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence |
            |---|---|---|---|---|
            | **Status transparency** | **Phase 1 – Public page:** Publish a live status page that reports current uptime and known issues with plain language summaries. <br><br> **Phase 2 – Webhooks:** Push incident updates to subscribed channels so customers receive timely information without polling. <br><br> **Phase 3 – Postmortems:** Publish short learning notes after incidents with owner and fix so trust accumulates. | - Reduces inbound queries because customers can self check service health at any time. <br><br> - Increases trust because communications are consistent and visible during stress. <br><br> - Improves net sentiment because transparency sets expectations realistically. <br><br> - Decreases duplicate tickets because updates answer common questions proactively. | **Value = (Complaints avoided × handling mins).** | Users correlate with dips; {ev} |
            | **Comms playbook** | **Phase 1 – T+15:** Send an initial holding note within fifteen minutes that confirms awareness and next update timing. <br><br> **Phase 2 – Hourly:** Provide progress and ETA updates in human readable terms with clear actions for affected users. <br><br> **Phase 3 – Closure:** Issue a brief root cause and remediation summary that closes the loop. | - Reduces anxiety among customers because they know what is happening and when to expect news. <br><br> - Cuts duplicate tickets because the playbook answers status questions clearly. <br><br> - Sets clear expectations which helps frontline teams manage conversations. <br><br> - Protects CSAT by showing ownership and momentum during incidents. | **Follow-ups avoided × mins.** | Dips raise query volume; {ev} |
            | **Customer SLO credits policy** | **Phase 1 – Define:** Document clear thresholds and calculation rules for credits when SLOs are not met. <br><br> **Phase 2 – Automate:** Trigger credit issuance from monitoring data and notify customers with a concise statement of impact. <br><br> **Phase 3 – Review:** Track issuance trends and drive corrective actions to reduce recurrence. | - Reduces disputes because remediation is predictable and fair. <br><br> - Protects loyalty for key accounts because customers see timely recognition of impact. <br><br> - Lowers manual handling effort because credits are system driven. <br><br> - Improves compliance posture because decisions are auditable. | **Escalation cost avoided.** | Evidence months show where policy applies; {ev} |
            """
            }
            render_cio_tables("CIO — Uptime & Availability", cio)

    # ---------------------- 2(b) SLA related to Availability ----------------------
    with st.expander("📌 SLA related to Availability"):
        if "sla_availability" in df_filtered.columns:
            # Distribution of SLA values
            sla_dist = df_filtered["sla_availability"].value_counts(dropna=False).reset_index()
            sla_dist.columns = ["sla_availability", "records"]
            fig = px.bar(
                sla_dist, x="sla_availability", y="records",
                title="SLA Availability Levels",
                labels={"sla_availability": "SLA (%)", "records": "Records"},
                color_discrete_sequence=MES_BLUE, template="plotly_white"
            )
            st.plotly_chart(fig, use_container_width=True)

            if not sla_dist.empty:
                total = int(sla_dist["records"].sum())
                miss_mask = sla_dist["sla_availability"].isna() | (
                    sla_dist["sla_availability"].astype(str).str.lower() == "nan"
                )
                miss = int(sla_dist.loc[miss_mask, "records"].sum())
                top = sla_dist.loc[sla_dist["records"].idxmax()]
                st.markdown("### Analysis")
                st.write(f"""
**What this graph is:** A bar chart showing **distribution of declared SLA availability levels** across records.  
**X-axis:** SLA percentage bucket.  
**Y-axis:** Number of rows at each SLA level.

**What it shows in your data:**  
- **Total rows:** **{_fmt_int(total)}**  
- **Most common SLA:** **{top['sla_availability']}%** (**{_fmt_int(top['records'])}** rows)  
- **Missing SLA entries:** **{_fmt_int(miss)}** rows

**Overall:** High concentration at one tier suggests standardization; a large “missing” bucket signals governance gaps.

**How to read it operationally:**  
- **Peaks:** Use as default templates for new services.  
- **Tails:** Revisit outlier SLAs for feasibility.  
- **Missing:** Block data ingestion without SLA.

**Why this matters:** Clear SLAs drive planning, capacity targets, and expectation setting; gaps slow audits and erode trust.
""")
                ev = f"Most common SLA **{top['sla_availability']}%** with **{_fmt_int(top['records'])}** rows; **{_fmt_int(miss)}** rows missing; total **{_fmt_int(total)}**."
            else:
                ev = "No rows available."

            # ---- LOCALIZED UPTIME SUMMARY FOR THIS BLOCK (prevents UnboundLocalError) ----
            avg, rng = np.nan, np.nan
            if {"report_month", "uptime_percent"} <= set(df_filtered.columns):
                ts_u = (
                    df_filtered.dropna(subset=["uptime_percent"])
                    .groupby("report_month")["uptime_percent"]
                    .mean()
                    .reset_index()
                    .sort_values("report_month")
                )
                if not ts_u.empty:
                    avg = float(ts_u["uptime_percent"].mean())
                    rng = float(ts_u["uptime_percent"].max() - ts_u["uptime_percent"].min())
                    pk = ts_u.loc[ts_u["uptime_percent"].idxmax()]
                    lw = ts_u.loc[ts_u["uptime_percent"].idxmin()]
                else:
                    pk = {"report_month": "N/A", "uptime_percent": np.nan}
                    lw = {"report_month": "N/A", "uptime_percent": np.nan}
            else:
                pk = {"report_month": "N/A", "uptime_percent": np.nan}
                lw = {"report_month": "N/A", "uptime_percent": np.nan}

            # ---------- CIO: Availability SLAs (Benefits expanded; Explanations elaborated) ----------
            cio = {
                "cost": f"""
            | Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence |
            |---|---|---|---|---|
            | **Align maintenance into stable windows** | **Phase 1 – Pick:** Choose months adjacent to the peak such as **{pk['report_month']}** and avoid trough months such as **{lw['report_month']}** so risk is scheduled when resilience is higher. <br><br> **Phase 2 – Batch:** Consolidate work into a single communication and a single CAB per window and specify the exact roles responsible for pre checks and rollback plans. <br><br> **Phase 3 – Review:** Measure the change in preparation hours and the reduction in incident spillover after windows and circulate a brief report. | - Lowers preparation and administration cost because multiple changes are handled together. <br><br> - Reduces fragmented handoffs across teams because the process runs on a single timeline. <br><br> - Decreases aftershock incidents because coordinated planning improves quality. <br><br> - Increases schedule predictability for stakeholders because maintenance windows are known in advance. | **Savings = (Windows reduced × prep mins) + (spillover incidents avoided × MTTR × rate).** | {ev} |
            | **Alert noise cleanup** | **Phase 1 – Inventory:** Catalogue noisy rules observed near trough months and describe the criteria used to classify a rule as noisy. <br><br> **Phase 2 – Retire:** Remove non actionable alerts and document the reason for retirement so similar rules do not reappear. <br><br> **Phase 3 – Tune:** Convert remaining rules to SLO based triggers with cooldowns and keep a changelog for transparency. | - Lowers operational toil because teams stop handling alerts that never lead to action. <br><br> - Shortens time to acknowledge because analysts spend less time filtering noise. <br><br> - Raises the signal to noise ratio so responders trust monitoring more. <br><br> - Makes on call load sustainable during fragile periods because only important events page. | **Benefit = (False positives removed × triage mins) + (MTTA reduction × incidents).** | Variability around trough indicates noise; {ev} |
            | **Right-size thresholds** | **Phase 1 – Calibrate:** Set thresholds around **{_fmt_float(avg)}%** using the observed range of **{_fmt_float(rng)} pp** and explain the math so owners buy in. <br><br> **Phase 2 – Guard:** Establish escalation bands that provide early warning before breaches and define actions for each band. <br><br> **Phase 3 – Audit:** Review drift monthly against policy and adjust limits when the platform improves. | - Reduces spurious breaches because thresholds match real behavior. <br><br> - Keeps on call experience steadier because alerts cluster around meaningful deviations. <br><br> - Improves SLA predictability which helps account teams manage commitments. <br><br> - Minimizes process churn because policies change only with evidence. | **Minutes saved × alerts avoided** + **SLA penalties avoided**. | Trend shows where bands should sit; {ev} |
            """,
                "performance": f"""
            | Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence |
            |---|---|---|---|---|
            | **Freeze during burn** | **Phase 1 – Detect:** Monitor error budget burn and declare a freeze when consumption exceeds the guardband and document the trigger in a public runbook. <br><br> **Phase 2 – Freeze:** Block risky changes until the mean uptime re enters the safe zone and record exceptions with approvals. <br><br> **Phase 3 – Exit:** Lift the freeze using a controlled canary rollout sequence and verify stability before resuming normal cadence. | - Protects uptime in the moment because risk is reduced when the platform is fragile. <br><br> - Reduces compounding failures that would extend outage duration. <br><br> - Stabilizes SLO recovery so teams regain confidence quickly. <br><br> - Preserves delivery momentum over the quarter because freezes are targeted and brief. | **Incidents avoided × MTTR × rate** during burn periods. | Trough month indicates burn risk; {ev} |
            | **Guardrails pre/post deploy** | **Phase 1 – Extra checks:** Add canaries and golden signals with explicit pass fail criteria and explain who monitors them. <br><br> **Phase 2 – Auto-rollback:** Configure automatic rollback for error or latency spikes and state the thresholds in change records. <br><br> **Phase 3 – Postmortem:** Produce short action oriented notes after rollbacks to prevent recurrence. | - Delivers faster recovery because bad versions are rolled back with minimal delay. <br><br> - Reduces prolonged dips in availability because issues are contained early. <br><br> - Increases deployment success because patterns are standardized across teams. <br><br> - Improves operational learning because each event yields concrete actions. | **Minutes saved vs late detect × incidents**; **rollback time avoided**. | Recovery speed around troughs; {ev} |
            | **Per-service drilldowns** | **Phase 1 – Identify:** Select the bottom decile services by uptime and share a ranked list with owners. <br><br> **Phase 2 – Fix:** Execute three high leverage fixes per service with owners accountable and capture uplift metrics. <br><br> **Phase 3 – Track:** Compare uplift to the fleet average monthly and re target investment if needed. | - Raises the floor on reliability by focusing on the weakest services first. <br><br> - Narrows volatility across the estate which protects aggregate uptime. <br><br> - Shrinks aggregate risk by eliminating repeated failure modes. <br><br> - Improves partner team planning because reliability becomes more uniform. | **SLA uplift × service volume** + **incidents avoided × MTTR**. | Mean masks tails; {ev} |
            """,
                "satisfaction": f"""
            | Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence |
            |---|---|---|---|---|
            | **Status comms cadence** | **Phase 1 – Pre-announce:** Publish maintenance windows and risk notes in advance using standard templates that customers recognize. <br><br> **Phase 2 – Live updates:** Provide clear progress messages during dips with ETA bands and practical workarounds where available. <br><br> **Phase 3 – Summary:** Share learning notes and next actions after resolution so customers see improvement momentum. | - Reduces complaints because customers know what is happening and what to expect. <br><br> - Increases predictability for stakeholders because updates arrive on a set cadence. <br><br> - Creates calmer interactions during incidents because messaging is clear and consistent. <br><br> - Supports CSAT by demonstrating ownership and accountability. | **Complaints avoided × handling mins** + **chaser calls avoided × mins**. | Dips & rebounds guide comms timing; {ev} |
            | **Clear ETA to recover** | **Phase 1 – Estimate:** Use historical time from trough to recovery to produce an initial ETA window and explain uncertainty. <br><br> **Phase 2 – Commit:** Share the window and checkpoints so customers can plan their work. <br><br> **Phase 3 – Update:** Provide variance handling guidance and revise the ETA if new information arrives. | - Lowers anxiety for users because they have a realistic timeline for restoration. <br><br> - Reduces inbound traffic because proactive updates answer common questions. <br><br> - Improves sentiment in surveys because expectations are met or managed. <br><br> - Enhances credibility for operations because estimates are grounded in data. | **Chaser contacts avoided × mins** + **CSAT uplift value**. | Historical recovery speed informs ETA; {ev} |
            | **Publish learnings** | **Phase 1 – Root causes:** Create short root cause write ups for each dip with the primary driver and the confirmed fix. <br><br> **Phase 2 – Actions:** Assign an owner and a due date for each corrective action and make status visible. <br><br> **Phase 3 – Verify:** Confirm the effect in the next cycle and close the action with evidence. | - Restores confidence because customers can see how the system improves after issues. <br><br> - Reduces repeat incidents because fixes are tracked to completion. <br><br> - Grows cultural maturity in reliability because teams learn from data not anecdotes. <br><br> - Improves stakeholder alignment because actions and accountability are explicit. | **Detractors avoided × value** + **repeat incidents avoided × MTTR**. | Trend improvement after actions; {ev} |
            """
            }
            render_cio_tables("CIO — Availability SLAs", cio)

        else:
            st.warning("Column 'sla_availability' not found.")

    # ---------------------- 2(c) Historical Availability Trends ----------------------
    with st.expander("📌 Historical Availability Trends"):
        if {"report_month", "uptime_percent"} <= set(df_filtered.columns):
            ts = df_filtered.groupby("report_month")["uptime_percent"].mean().reset_index()
            ts = ts.sort_values("report_month")
            fig = px.area(
                ts, x="report_month", y="uptime_percent",
                title="Historical Availability Trend (Mean Uptime%)",
                labels={"report_month": "Month", "uptime_percent": "Mean Uptime (%)"},
                color_discrete_sequence=MES_BLUE, template="plotly_white"
            )
            st.plotly_chart(fig, use_container_width=True)

            if not ts.empty:
                peak = ts.loc[ts["uptime_percent"].idxmax()]
                low = ts.loc[ts["uptime_percent"].idxmin()]
                avg = ts["uptime_percent"].mean()
                rng = float(peak["uptime_percent"] - low["uptime_percent"])
                st.markdown("### Analysis")
                st.write(f"""
**What this graph is:** An area chart showing **historical mean uptime%** by month.  
**X-axis:** Calendar month.  
**Y-axis:** Mean uptime percentage.

**What it shows in your data:**  
- **Peak:** **{peak['report_month']}** at **{_fmt_float(peak['uptime_percent'])}%**  
- **Trough:** **{low['report_month']}** at **{_fmt_float(low['uptime_percent'])}%**  
- **Average:** **{_fmt_float(avg)}%**; **Range:** **{_fmt_float(rng)} pp**

**Overall:** Recurring troughs point to maintenance cycles or seasonal factors; sustained lift above average suggests maturing reliability.

**How to read it operationally:**  
- **Gap = risk delta:** Distance from target to the area shows exposure.  
- **Lead–lag:** Post-change dips followed by rebounds imply reactive sprints.  
- **Recovery strength:** Faster crossover back to average = healthier system.  
- **Control:** Aim for a high, stable “plateau” by smoothing releases and standardizing runbooks.

**Why this matters:** Keeping the trend tight and high protects SLA, prevents aging backlog, and steadies customer experience.
""")
                ev = f"Peak **{peak['report_month']} = {_fmt_float(peak['uptime_percent'])}%**, Trough **{low['report_month']} = {_fmt_float(low['uptime_percent'])}%**, Avg **{_fmt_float(avg)}%**, Range **{_fmt_float(rng)} pp**."
            else:
                ev = "No rows available."

            # ---------- CIO: Historical Availability (Benefits expanded; Explanations elaborated) ----------
            cio = {
                "cost": f"""
            | Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence |
            |---|---|---|---|---|
            | **Backfill missing SLA values** | **Phase 1 – Map:** Build a catalog that maps each service to its SLA using contracts and policy and explain the data sources and owners. <br><br> **Phase 2 – Enforce:** Make the SLA field mandatory at service intake with guardrails and provide guidance text so submitters know the default tiers. <br><br> **Phase 3 – Audit:** Issue a weekly missing list to service owners and track closure time so governance improves. | - Avoids audit rework because records are complete at the point of entry. <br><br> - Reduces clarifications between teams because SLA expectations are explicit. <br><br> - Accelerates onboarding of new services because templates are ready to use. <br><br> - Lowers recurring admin time because fewer manual lookups are needed. | **Rework mins saved = {_fmt_int(miss)} × 3–5 mins** (lookups/clarifications). | {ev} |
            | **SLA templates by category** | **Phase 1 – Define:** Create standard Gold Silver and Bronze tiers with clear opex and capex guidance and document when each tier applies. <br><br> **Phase 2 – Default:** Auto apply templates by category and require CAB approval for exceptions so variance is controlled. <br><br> **Phase 3 – Tune:** Review quarterly against outcomes and adjust thresholds and wording where needed. | - Speeds service definition because teams can adopt a proven template quickly. <br><br> - Reduces bespoke cases that create complexity and cost. <br><br> - Simplifies training for new staff because the tiering system is consistent. <br><br> - Improves planning accuracy because capacity targets link to standard tiers. | **Setup mins saved × #services adopting top tier {top['sla_availability']}%**. | Concentration supports templating; {ev} |
            | **SLA inference rules** | **Phase 1 – Heuristics:** If SLA is empty infer a value from category and peer services and record the inference reason. <br><br> **Phase 2 – Flag:** Send the inferred SLA to the owner for confirmation with a one click approve or correct workflow. <br><br> **Phase 3 – Lock:** After sign off lock the SLA with versioning so downstream systems rely on a stable value. | - Cuts manual lookups for missing values which speeds service registration. <br><br> - Reduces back and forth between teams because the workflow is structured. <br><br> - Keeps the registry complete which prevents blocked requests and reporting gaps. <br><br> - Improves data lineage because changes are tracked with reasons. | **Lookups avoided × mins** for {_fmt_int(miss)} missing rows; **blocked-work avoidance value**. | {ev} |
            | **Owner scorecards** | **Phase 1 – Attribute:** Attach SLA ownership to services and expose accountability in a shared dashboard. <br><br> **Phase 2 – Report:** Publish a monthly compliance heatmap and annotate reasons for low scores. <br><br> **Phase 3 – Coach:** Meet outliers with action plans and deadlines so improvement is managed. | - Creates clear accountability which reduces drift in compliance. <br><br> - Reduces audit penalties and rework because owners act before deadlines. <br><br> - Aligns incentives with business targets so improvements are sustained. <br><br> - Enhances cross team collaboration because responsibilities are explicit. | **Benefit = (Drift reduction × audit mins) + penalties avoided**. | Variation across buckets visible; {ev} |
            """,
                "performance": f"""
            | Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence |
            |---|---|---|---|---|
            | **SLA miss alerts** | **Phase 1 – Daily roll-up:** Detect services with low or missing SLAs and compile a prioritized list each day. <br><br> **Phase 2 – Notify:** Ping the owner with a due date and the exact fix path so closure is straightforward. <br><br> **Phase 3 – Track:** Measure time to fix and recurrence so leaders can see progress. | - Accelerates correction because owners receive precise and timely prompts. <br><br> - Lowers exposure to penalties because gaps are resolved before audits. <br><br> - Improves operational readiness by keeping the registry current. <br><br> - Reduces last minute fire drills because issues are addressed continuously. | **SLA uplift × service volume** + **penalties avoided**. | Peaks and misses guide focus; {ev} |
            | **Trend tracking of SLA%** | **Phase 1 – Monthly:** Chart SLA trendlines by category and owner and store snapshots for comparison. <br><br> **Phase 2 – Seasonality:** Annotate changes in policy or infrastructure so the data tells a coherent story. <br><br> **Phase 3 – Review:** Log CAB actions and verify improvement against the following month. | - Prevents drift because deviations are visible and discussed. <br><br> - Keeps teams aligned on service targets which reduces conflicting priorities. <br><br> - Enables continuous improvement because actions are tied to measured outcomes. <br><br> - Detects systemic issues earlier because trends reveal patterns. | **Drift mins avoided** relative to baseline tier; **breach likelihood reduction**. | Trend expectations set by distribution; {ev} |
            | **Intake validations** | **Phase 1 – Block:** Reject service creation when SLA is missing and provide immediate guidance to fix. <br><br> **Phase 2 – UX:** Offer helper defaults and tooltips that recommend appropriate tiers based on category. <br><br> **Phase 3 – Logs:** Capture rejection reasons for governance reporting and process tuning. | - Produces cleaner data because errors are corrected at the source. <br><br> - Reduces hotfix work later because records are accurate from day one. <br><br> - Speeds provisioning because approvals are not delayed by missing fields. <br><br> - Improves governance because leaders can see why submissions fail. | **Time saved = (Manual corrections × mins)** + **failed changes avoided**. | Missing count {_fmt_int(miss)} demonstrates need. |
            """,
                "satisfaction": f"""
            | Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence |
            |---|---|---|---|---|
            | **Publish SLA stance** | **Phase 1 – Dashboard:** Display SLA per service with targets and current status in a simple portal. <br><br> **Phase 2 – Notes:** Add maintenance windows and expectation notes so customers plan accordingly. <br><br> **Phase 3 – Reviews:** Hold quarterly sessions with stakeholders to validate targets and adjust where needed. | - Reduces queries because SLA information is easy to find and understand. <br><br> - Improves expectation management because customers see both targets and context. <br><br> - Increases trust because governance is transparent. <br><br> - Strengthens cross functional accountability because commitments are visible. | **Queries avoided × mins** + **CSAT uplift value**. | Visibility reduces anxiety; {ev} |
            | **Customer comms on risk** | **Phase 1 – Detect:** Identify services at low or missing SLA tiers from the dashboard and flag them for outreach. <br><br> **Phase 2 – Notify:** Send a proactive message that explains risk and mitigation steps with timelines. <br><br> **Phase 3 – Mitigate:** Track completion of actions and report status until risk is retired. | - Reduces surprises because customers hear about risk before it causes impact. <br><br> - Prevents escalations because there is a documented plan with dates. <br><br> - Protects renewals for key accounts because transparency builds confidence. <br><br> - Improves coordination between product and support because actions are shared. | **Complaints avoided × mins** + **churn risk reduction value**. | Low tiers highlighted by bars; {ev} |
            | **Credits policy clarity** | **Phase 1 – Rules:** Define when credits apply and how they are calculated and present examples. <br><br> **Phase 2 – Automate:** Trigger credits on breach and notify customers with a concise impact statement. <br><br> **Phase 3 – Report:** Publish issuance metrics and root cause categories so leadership can steer investment. | - Reduces disputes because rules are clear and consistent. <br><br> - Improves CSAT during failure events because remediation is timely. <br><br> - Lowers dispute handling time because cases are straightforward. <br><br> - Guides engineering focus because credit trends highlight costly problem areas. | **Escalation cost avoided + dispute handling mins saved**. | Distribution informs exposure; {ev} |
            """
            }
            render_cio_tables("CIO — Historical Availability", cio)

        else:
            st.warning("Need monthly uptime data.")
