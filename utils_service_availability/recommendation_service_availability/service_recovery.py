# utils_service_availability/recommendation_service_availability/service_recovery.py
import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np

# ============================
# Company visual theme
# ============================
px.defaults.template = "plotly_white"
PRIMARY_BLUE = "#004C99"
SECONDARY_BLUE = "#007ACC"
MES_BLUE_SEQ = [PRIMARY_BLUE, SECONDARY_BLUE, "#3399FF", "#66B2FF", "#9BD1FF"]

# ============================================================
# Helper function for CIO Tables
# ============================================================
def render_cio_tables(title, cio_data):
    st.subheader(title)
    with st.expander(" Cost Reduction"):
        st.markdown(cio_data["cost"], unsafe_allow_html=True)
    with st.expander(" Performance Improvement"):
        st.markdown(cio_data["performance"], unsafe_allow_html=True)
    with st.expander(" Customer Satisfaction Improvement"):
        st.markdown(cio_data["satisfaction"], unsafe_allow_html=True)

def _to_num(s):
    return pd.to_numeric(s, errors="coerce")

# ============================================================
# 8️⃣ SERVICE RECOVERY TIME
# ============================================================
def service_recovery(df: pd.DataFrame):

    required_cols = {"report_date", "service_name", "recovery_time_minutes", "rto_target_minutes", "incident_count"}
    if not required_cols.issubset(df.columns):
        st.warning(f"⚠️ Missing required columns: {required_cols - set(df.columns)}")
        return

    df = df.copy()
    df["report_date"] = pd.to_datetime(df["report_date"], errors="coerce")
    df["month"] = df["report_date"].dt.to_period("M").astype(str)
    df["recovery_time_minutes"] = _to_num(df["recovery_time_minutes"])
    df["rto_target_minutes"] = _to_num(df["rto_target_minutes"])
    df["incident_count"] = _to_num(df["incident_count"])

    # Optional cost fields
    has_cost = "estimated_cost_downtime" in df.columns
    avg_rm_per_min = np.nan
    tot_cost = np.nan
    if has_cost:
        df["estimated_cost_downtime"] = _to_num(df["estimated_cost_downtime"])
        tot_cost = float(df["estimated_cost_downtime"].sum())
        tot_min = float(df["recovery_time_minutes"].sum())
        if tot_min > 0:
            avg_rm_per_min = tot_cost / tot_min

    # ============================================================
    # 8a. Average Time Taken to Restore Services (MTTR)
    # ============================================================
    with st.expander("📌 Average Time Taken to Restore Services (MTTR)"):
        mttr = (
            df.groupby("service_name", as_index=False)
            .agg(avg_recovery=("recovery_time_minutes", "mean"), incidents=("incident_count", "sum"))
            .sort_values("avg_recovery", ascending=False)
        )

        # --- Graph: MTTR by Service
        fig_mttr = px.bar(
            mttr,
            x="service_name",
            y="avg_recovery",
            text="avg_recovery",
            title="Average Recovery Time (MTTR) by Service",
            labels={"service_name": "Service", "avg_recovery": "MTTR (minutes)"},
            color_discrete_sequence=[PRIMARY_BLUE],
            template="plotly_white",
        )
        fig_mttr.update_traces(texttemplate="%{text:.1f}", textposition="outside", cliponaxis=False)
        fig_mttr.update_layout(xaxis_tickangle=-15)
        st.plotly_chart(fig_mttr, use_container_width=True)

        max_r = mttr.loc[mttr["avg_recovery"].idxmax()]
        min_r = mttr.loc[mttr["avg_recovery"].idxmin()]
        range_diff = float(max_r["avg_recovery"] - min_r["avg_recovery"])
        avg_mttr_overall = float(mttr["avg_recovery"].mean())

        # Own analysis (Graph 1)
        st.markdown("### Analysis — MTTR by Service (Graph 1)")
        st.write(
f"""**What this graph is:** A **bar chart** showing **Mean Time to Recover (MTTR)** per service.  
**X-axis:** Service name.  
**Y-axis:** Average minutes to recover (MTTR).

**What it shows in your data:**  
- **Slowest recovery:** **{max_r['service_name']}** at **{max_r['avg_recovery']:.1f} mins**.  
- **Fastest recovery:** **{min_r['service_name']}** at **{min_r['avg_recovery']:.1f} mins**.  
- **Range difference:** **{range_diff:.1f} mins** across services.  
- **Overall average MTTR:** **{avg_mttr_overall:.1f} mins**.

**Overall:** Services above the average **{avg_mttr_overall:.1f} mins** consume disproportionate recovery time and risk. A wide spread (**{range_diff:.1f} mins**) indicates non-standardized recovery practices.

**How to read it operationally:**  
- **Gap to target:** Use **{avg_mttr_overall:.1f} mins** as a provisional floor; anything above needs runbook optimization or automation.  
- **Lead–lag:** Cross-check high MTTR services with their incident volume to separate **complex restores** from **frequent but quick** ones.  
- **Recovery strength:** Prioritize the tallest bars first; each minute shaved compounds across **incident count**.  
- **Control:** Enforce **golden-path runbooks**, **pre-positioned diagnostics**, and **skill-based routing**.

**Why this matters:** Lower MTTR **directly increases uptime**, reduces overtime, and keeps customers productive."""
        )

        # CIO tables for Graph 1 (phased, detailed; use real values)
        rmmin_txt = f"(Avg RM/min≈RM {avg_rm_per_min:,.2f})" if has_cost and avg_rm_per_min == avg_rm_per_min else "RM/min from data (if available)"
        max_r_inc = int(max_r["incidents"])
        min_r_inc = int(min_r["incidents"])
        cio_8a = {
            "cost": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence |
|---|---|---|---|---|
| Attack the slowest MTTR first | **Phase 1 – Decompose:** Break the recovery process for **{max_r['service_name']}** into clear steps and identify where waiting time, manual checks or repeated handoffs are causing delays so that you know exactly which activities extend the overall MTTR.<br><br>**Phase 2 – Automate:** Turn the repetitive and mechanical restore steps such as restarts, cache refreshes or basic health checks into scripts or automation so that engineers spend their time on higher value diagnosis instead of manual repetition.<br><br>**Phase 3 – Verify:** After implementing these changes, compare the new MTTR against the baseline of **{max_r['avg_recovery']:.1f} mins** to confirm that the recovery time has fallen and that the new pattern is consistent across multiple incidents. | - The approach focuses cost and effort savings on the service where recovery currently takes the longest so every improvement delivers a visible impact on operational performance.<br><br>- The change reduces the number of engineer hours spent on each incident because the restore flow becomes faster, cleaner and less dependent on manual repetitive work.<br><br>- The new pattern gradually lowers overtime and after hours work as the average time to recover decreases and more incidents finish within standard business hours.<br><br>- The method creates a reusable approach that can be applied to other services once the slowest service has been improved, making the overall recovery landscape more efficient over time.<br><br> | **RM saved = ΔMTTR × incidents × RM/min** = (**Δ mins** × **{max_r_inc}** × **{rmmin_txt}**). | Highest bar: **{max_r['service_name']} {max_r['avg_recovery']:.1f} mins**; overall avg **{avg_mttr_overall:.1f} mins**. |
| Pre-position diagnostics | **Phase 1 – Capture:** At the moment an incident is opened, automatically collect key logs, metrics and traces related to the affected service so that engineers do not waste time hunting for basic information later in the restore process.<br><br>**Phase 2 – Snapshot:** Preserve a snapshot of the failing state such as configuration, load and error signatures so that root cause analysis can be done calmly after recovery without needing to reproduce the exact scenario immediately.<br><br>**Phase 3 – Drill:** Regularly practice retrieving and using these diagnostic artefacts in simulation or game day exercises so that teams are fluent and confident when a real incident occurs. | - The diagnostic pattern cuts the amount of time spent in the initial triage stage because the most important information is already prepared when the engineer starts working on the incident.<br><br>- Pre-positioned evidence helps teams identify root cause more quickly since engineers can review a structured set of logs and metrics instead of manually clicking through many tools under pressure.<br><br>- Early capture of failing-state data reduces the risk of lost or overwritten evidence which makes follow up analysis and long term fixes more accurate.<br><br>- Consistent access to structured diagnostics increases team confidence in the recovery process because engineers know that critical information will be available whenever an incident opens.<br><br> | **RM saved = ΔTriage_min × incidents × RM/min** using service-level incident counts. | Long MTTRs typically include search time; tallest bars indicate triage drag. |
| Golden-path runbooks | **Phase 1 – Standardize:** Create a clear one page standard operating procedure for each major service with step by step recovery actions, verification checks and rollback options so that engineers can follow a reliable pattern even when stressed.<br><br>**Phase 2 – Enforce:** Require that incidents are resolved using these runbooks and that engineers confirm each step has been followed so that essential controls are not accidentally skipped.<br><br>**Phase 3 – Refresh:** Review and update the runbooks at least quarterly or whenever the architecture changes so that the documented golden path always reflects the current reality of the system. | - Standardised runbooks reduce variation in how different engineers handle similar incidents because everyone follows the same agreed recovery pattern for the service.<br><br>- Written guidance lowers the number of avoidable mistakes and rework activities since runbooks remind engineers to execute critical verification and rollback steps before closing an incident.<br><br>- Clear instructions make onboarding of new staff easier, allowing new engineers to rely on well-documented guidance instead of depending only on informal tribal knowledge.<br><br>- Codified best practices gradually narrow the gap between the slowest and fastest services because proven techniques are reused consistently across the environment.<br><br> | **RM saved = rework_min_avoided × incidents × RM/min**. | MTTR spread (**{range_diff:.1f} mins**) shows inconsistency across services. |
| Warm standby for critical services | **Phase 1 – Identify:** Select those services that sit above **{avg_mttr_overall:.1f} mins** MTTR and also have high incident volumes or business impact so that warm standby investments are focused where they matter most.<br><br>**Phase 2 – Provision:** Build and maintain warm standby instances or configurations that can take over quickly when the primary path fails so that recovery does not rely solely on repairing the failing component.<br><br>**Phase 3 – Test:** Run regular failover drills that switch traffic to the standby and back again so that teams are confident the mechanism works when a real incident occurs. | - Warm standby capability significantly reduces recovery time for the most critical services because traffic can be moved to a ready standby instead of waiting for complex repairs on the primary environment.<br><br>- Additional resilience protects key SLAs and revenue streams since high value services are brought back within a much shorter timeframe when issues occur.<br><br>- A prepared failover path lowers stress on engineers during severe incidents because responders can rely on a known pattern instead of improvising under pressure.<br><br>- Increased safety margin gives more breathing room for careful root cause analysis after incidents without prolonging user impact, as service is already restored through the standby path.<br><br> | **Benefit = ΔMTTR × incidents × RM/min** against current **{max_r['avg_recovery']:.1f} mins**. | Tall bars justify redundancy investment. |
| Skill-based routing | **Phase 1 – Map:** Analyse historical incidents to understand which skills or teams resolve different types of issues most effectively and then map incident categories to the best suited subject matter experts.<br><br>**Phase 2 – Automate:** Configure the service desk or incident management tool so that new tickets are automatically routed to the most appropriate queue or engineer based on this mapping.<br><br>**Phase 3 – Audit:** Periodically review routing performance, reassignment patterns and resolution times so that the skill map stays accurate as the team and systems evolve. | - Skill-based routing reduces waiting time at the start of the incident because tickets reach the right expert team earlier instead of bouncing through multiple queues.<br><br>- Matching cases to expertise improves first touch resolution rates since the people handling the incident already have the relevant knowledge and context to act quickly.<br><br>- Fewer unnecessary handoffs lower frustration for both engineers and users because repeated explanations of the same problem become less common.<br><br>- Routing data provides insight into which skill sets are underused or overloaded, supporting better training plans and workforce planning.<br><br> | **Minutes saved/incident × incidents × RM/min**. | High MTTR services suggest skill mismatches. |
""",
            "performance": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence |
|---|---|---|---|---|
| Real-time MTTR watch | **Phase 1 – Surface:** Build a live dashboard that shows current and recent MTTR by service so that operations leads can see emerging problems as they develop instead of only in monthly reports.<br><br>**Phase 2 – Alert:** Configure alerts that trigger when MTTR trends rise above the overall benchmark of **{avg_mttr_overall:.1f} mins** so that intervention starts before the pattern becomes normalised.<br><br>**Phase 3 – Intervene:** Use these alerts to trigger focused reviews, unblock stuck incidents and adjust staffing so that spike patterns are corrected quickly. | - A real-time view turns MTTR into an operational signal rather than a backward-looking KPI, enabling teams to act while incidents are still in progress.<br><br>- Early visibility of rising MTTR enables interventions on services that are trending in the wrong direction, preventing long periods of degraded performance from becoming the norm.<br><br>- Shared dashboards improve coordination between support, operations and engineering because all teams reference the same live recovery metrics.<br><br>- Continuous monitoring supports data-driven evaluation of new processes or tools by making before-and-after MTTR changes easy to observe.<br><br> | **ΔMTTR × incidents** at service level. | Bars above mean indicate drift risk. |
| Dependency maps & RCA | **Phase 1 – Visualize:** Document and visualise the upstream and downstream dependencies for services with high MTTR so that incident responders can quickly understand what components are involved when a failure occurs.<br><br>**Phase 2 – Fix once:** For recurring patterns identified in root cause analysis, design and implement structural fixes that address the real dependency or design issue instead of repeatedly patching symptoms.<br><br>**Phase 3 – Validate:** After these fixes are implemented, monitor MTTR for the affected services to ensure that the expected reduction in recovery time is actually achieved. | - Clear dependency maps shorten investigation time because engineers know where to look first when a particular component fails.<br><br>- Structural fixes based on RCAs reduce repeat incidents for the same underlying problem, improving long-term stability.<br><br>- Better understanding of system interactions improves performance for complex services where hidden dependencies frequently cause surprises during recovery.<br><br>- Shared diagrams and explanations create a common mental model across teams, which improves collaboration and planning for future changes.<br><br> | **ΔMTTR from systemic fix × incidents**. | High MTTR often correlates with complex dependencies. |
| Post-incident 30–60–90 validation | **Phase 1 – Track:** After major incidents, track recovery performance for the following 30, 60 and 90 days to ensure that MTTR remains improved and does not quietly drift back up.<br><br>**Phase 2 – Escalate:** If MTTR begins to rise again during any of these windows, escalate the issue for further investigation and additional corrective actions so that gains are protected.<br><br>**Phase 3 – Standardize:** When a recovery improvement proves stable over time, incorporate the successful practices into standard runbooks and training so that they become the default way of working. | - Ongoing validation prevents hard won improvements from eroding over time because teams keep an eye on performance beyond the immediate aftermath of the incident.<br><br>- Follow-up checks ensure that temporary workarounds are either replaced with permanent fixes or actively managed so they do not create new issues later.<br><br>- Sustained tracking builds confidence that reported MTTR improvements are genuine and durable rather than short lived anomalies.<br><br>- Regular review encourages disciplined follow-through on action items from incident reviews since teams know results will be revisited multiple times.<br><br> | **Repeat incidents avoided × MTTR mins**. | Persistent tall bars need follow-through. |
""",
            "satisfaction": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence |
|---|---|---|---|---|
| Auto-ETA notifications | **Phase 1 – Predict:** Use historic MTTR for each service to generate an estimated time to recover whenever a new incident is opened so that users immediately know what to expect.<br><br>**Phase 2 – Notify:** Automatically send ETA updates to affected users or channels as the incident progresses so that people do not need to keep asking for manual status updates.<br><br>**Phase 3 – Close:** When the service is restored, send a final message confirming closure and summarising any key follow up information so that users know it is safe to resume normal work. | - Automated ETAs reduce the number of duplicate tickets and phone calls because users already have a clear expectation of when the service is likely to be restored.<br><br>- Timely estimates help users plan their work around the outage by giving a realistic timeframe instead of leaving them uncertain and frustrated.<br><br>- Consistent notification patterns improve the perception of professionalism and responsiveness because communication happens automatically for every incident.<br><br>- Shared ETA information supports better internal coordination since business stakeholders see the same recovery expectations as the operations team.<br><br> | **Ticket deflection × handling cost** for services > **{avg_mttr_overall:.1f} mins**. | Long MTTR drives anxiety; tallest bars correlate with call spikes. |
| Status page with workarounds | **Phase 1 – Publish:** Maintain a status page that clearly shows which services are impacted, what the current state is and which temporary workarounds users can apply during recovery so that information is centralised.<br><br>**Phase 2 – Surface:** Make this page easily accessible from portals, applications or internal communication tools so that users can find it quickly without needing instructions every time.<br><br>**Phase 3 – Measure:** Track usage of the status page and associated workarounds so that you can see whether they are actually helping users remain productive. | - A well-maintained status page keeps more users productive during service disruptions because guidance on workarounds is easy to locate and follow.<br><br>- Centralised messaging reduces frustration and confusion by providing a single authoritative source of truth about the current situation and progress.<br><br>- Self-service access to outage details decreases load on support teams as users no longer need to raise tickets just to ask for basic status information.<br><br>- Usage metrics highlight which services and user journeys cause the most pain during outages, guiding prioritisation of longer term design and automation improvements.<br><br> | **Visible minutes avoided × users × value/min**. | High bars = longer user-visible downtime. |
| VIP comms channel | **Phase 1 – Identify:** Determine which customers, business units or executives are considered high value or high impact and map which services they depend on that show slower recovery times.<br><br>**Phase 2 – Dedicated updates:** Provide these VIP stakeholders with a dedicated communication channel or customised updates during major incidents so that they receive timely, relevant information without needing to chase it.<br><br>**Phase 3 – Review:** After significant incidents, review satisfaction and feedback from these VIPs to see whether communication met their expectations and where improvements are needed. | - Dedicated communication for VIPs protects key revenue and strategic relationships by ensuring that the most important stakeholders feel informed and supported during outages.<br><br>- Proactive, tailored updates reduce escalations from senior leaders because leaders already have direct, accurate information about impact and recovery plans.<br><br>- Early and targeted communication helps customers coordinate their own contingency plans in parallel with recovery activities, minimising internal disruption.<br><br>- Continuous feedback from VIPs provides qualitative data about which information matters most, shaping broader communication strategies for all users.<br><br> | **Churn avoided × ACV**. | Tall bars hurt VIPs more; targeted comms mitigate. |
"""
        }
        render_cio_tables("CIO – Average Service Recovery (MTTR)", cio_8a)

    # ============================================================
    # 8b. Recovery Time Objective (RTO) Compliance
    # ============================================================
    with st.expander("📌 Recovery Time Objective (RTO) Compliance by Service"):
        df["rto_breach"] = df["recovery_time_minutes"] > df["rto_target_minutes"]
        df["minutes_over_target"] = (df["recovery_time_minutes"] - df["rto_target_minutes"]).clip(lower=0)

        rto = (
            df.groupby("service_name", as_index=False)
            .agg(
                total_incidents=("incident_count", "sum"),
                breaches=("rto_breach", "sum"),
                minutes_over=("minutes_over_target", "sum"),
                avg_recovery=("recovery_time_minutes", "mean"),
                avg_rto=("rto_target_minutes", "mean")
            )
        )
        rto["compliance_rate"] = (1 - (rto["breaches"] / rto["total_incidents"].replace(0, 1))) * 100

        # --- Graph: RTO Compliance (breaches)
        fig_rto = px.bar(
            rto.sort_values("breaches", ascending=False),
            x="service_name",
            y="breaches",
            text="breaches",
            title="RTO Breaches by Service",
            labels={"service_name": "Service", "breaches": "Number of RTO Breaches"},
            color_discrete_sequence=[SECONDARY_BLUE],
            template="plotly_white",
        )
        fig_rto.update_traces(textposition="outside", cliponaxis=False)
        fig_rto.update_layout(xaxis_tickangle=-15)
        st.plotly_chart(fig_rto, use_container_width=True)

        worst_rto = rto.loc[rto["breaches"].idxmax()]
        best_rto = rto.loc[rto["breaches"].idxmin()]
        avg_compliance = float(rto["compliance_rate"].mean())

        # Own analysis (Graph 2)
        st.markdown("### Analysis — RTO Compliance by Service (Graph 2)")
        st.write(
f"""**What this graph is:** A **bar chart** showing **how many times each service exceeded its RTO target**.  
**X-axis:** Service name.  
**Y-axis:** Count of RTO breaches.

**What it shows in your data:**  
- **Most breaches:** **{worst_rto['service_name']}** (**{int(worst_rto['breaches'])}**).  
- **Fewest breaches:** **{best_rto['service_name']}** (**{int(best_rto['breaches'])}**).  
- **Average compliance rate:** **{avg_compliance:.1f}%** across services.

**Overall:** High breach counts often co-exist with longer recoveries; services with **frequent breaches** and **high MTTR** are the fastest path to penalty and churn reduction.

**How to read it operationally:**  
- **Gap to target:** Add pre-breach alerts at **70–80%** of each service’s average RTO to enable early escalation.  
- **Lead–lag:** Compare breach patterns to **MTTR bars above** to identify where slow recovery is driving misses.  
- **Control:** Recalibrate unrealistic RTOs and parallelize restore steps to meet realistic, customer-aligned targets.

**Why this matters:** Hitting RTO is the **promise to the business**; staying inside it prevents penalties and protects credibility."""
        )

        # Additional analysis referencing the graph above (Graph 1 vs Graph 2)
        # Join with MTTR info to narrate relationship
        mttr_join = rto.merge(
            mttr[["service_name", "avg_recovery"]].rename(columns={"avg_recovery": "mttr_from_graph_1"}),
            on="service_name",
            how="left"
        )
        worst_row = mttr_join.loc[mttr_join["breaches"].idxmax()]
        best_row = mttr_join.loc[mttr_join["breaches"].idxmin()]

        st.markdown("### Analysis — RTO Breaches vs MTTR (Context from Graph 1)")
        st.write(
f"""**What this graph is (contextual comparison):** A reading of **RTO breaches** in relation to the **MTTR by service** from the graph above.  
**X-axis (reference):** Service (same ordering).  
**Y-axis (reference):** MTTR minutes (Graph 1) vs Breach counts (this graph).

**What it shows in your data:**  
- **Top breach service:** **{worst_row['service_name']}** with **{int(worst_row['breaches'])}** breaches and an MTTR of **{worst_row['mttr_from_graph_1']:.1f} mins**.  
- **Lowest breach service:** **{best_row['service_name']}** with **{int(best_row['breaches'])}** breaches and an MTTR of **{best_row['mttr_from_graph_1']:.1f} mins**.  
- Where breaches are high **and** MTTR is above the overall average **{avg_mttr_overall:.1f} mins**, the service is structurally off-pace.

**How to read it operationally:**  
- **Gap = breach risk:** Close the MTTR gap for the worst breach services first to cut penalty exposure.  
- **Lead–lag:** If MTTR recently improved but breaches remain high, **recalibrate RTO** to more realistic targets, then tighten.  
- **Control:** Combine **pre-breach timers**, **parallel restore**, and **skill-based routing** for the worst offenders.

**Why this matters:** Connecting breach counts to MTTR identifies exactly **where each minute saved converts into fewer penalties** and better SLA attainment."""
        )

        # CIO tables for Graph 2 (phased, detailed; use real values)
        rmmin_txt_b = f"(Avg RM/min≈RM {avg_rm_per_min:,.2f})" if has_cost and avg_rm_per_min == avg_rm_per_min else "RM/min from data (if available)"
        cio_8b = {
            "cost": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence |
|---|---|---|---|---|
| Recalibrate unrealistic RTOs | **Phase 1 – Assess:** Compare each service’s actual MTTR with its average RTO target so that you can see which services have expectations that do not match reality.<br><br>**Phase 2 – Reset:** Adjust RTO targets to a level that is achievable with current capabilities and then design a roadmap of process and tooling improvements that will allow you to tighten those targets over time.<br><br>**Phase 3 – Monitor:** Perform monthly reviews to check for drift between actual recovery times and the new targets so that unrealistic expectations do not silently return. | - Alignment of targets with real MTTR reduces the number of formal RTO breaches because service commitments match what the organisation can genuinely deliver while improvements are being built.<br><br>- Smaller gaps between contractual promises and operational performance lower the risk of penalties and strained customer relationships.<br><br>- Transparent mapping of RTOs to current capability provides a solid basis for investment discussions by showing how additional spend could support tighter objectives.<br><br>- Realistic targets prevent teams from feeling permanently behind, supporting healthier culture while reliability is still improving.<br><br> | **RM saved = breaches_avoided × minutes_over_target × RM/min** using service-level **minutes_over** (**{int(worst_rto['minutes_over']):,} mins** for worst offender). | Most breaches: **{worst_rto['service_name']} = {int(worst_rto['breaches'])}**; minutes over target in data support sizing. |
| Auto-escalation near RTO | **Phase 1 – Timer:** Implement timers that track how long each incident has been open relative to its RTO target so that the system can see when the risk of a breach is increasing.<br><br>**Phase 2 – Page:** Automatically escalate to senior engineers or incident commanders when incidents approach 70–80% of their RTO so that experts are involved early enough to prevent overruns.<br><br>**Phase 3 – Audit:** Review which escalations were useful and which were noise so that thresholds and rules can be tuned to balance responsiveness with alert fatigue. | - Pre-emptive escalation prevents many avoidable breaches because the right people are called in before the situation passes the RTO limit rather than after the fact.<br><br>- Early engagement of senior staff improves decision making under time pressure since experienced responders are already aware of context when critical decisions must be made.<br><br>- Clear rules for escalation create predictable response patterns, reducing confusion in tense situations.<br><br>- Incident-level data on near-breach events provides insight into structural delays that can be addressed through process or staffing changes.<br><br> | **Breaches avoided × avg minutes_over × RM/min**; base minutes_over on dataset. | Bars highlight concentration of misses by service. |
| Pre-stage restore assets | **Phase 1 – Prepare:** Identify the most common restore artefacts such as images, keys and scripts and ensure they are stored in accessible, up to date locations close to the systems that use them.<br><br>**Phase 2 – Cache:** Where possible, keep frequently used assets cached or partially loaded so that they can be applied without long download or initialization times when an incident occurs.<br><br>**Phase 3 – Test:** Run regular tests that rehearse using these pre-staged assets during simulated incidents so that teams know they can trust them in real events. | - Ready-to-use restore artefacts shorten the early stages of recovery because engineers are not wasting time searching for correct versions of images, scripts or configuration files.<br><br>- Curated and maintained asset sets reduce the risk of mistakes caused by outdated or incorrect artefacts, improving quality of recovery actions.<br><br>- Faster access to technical prerequisites allows more of the recovery window to be spent on solving the root problem instead of running infrastructure housekeeping tasks.<br><br>- Reduced cold-start overhead contributes directly to lower minutes over the RTO target during real incidents.<br><br> | **ΔStart minutes × incidents × RM/min**. | High **minutes_over** and breach bars show cold starts. |
| Timebox triage & rollback | **Phase 1 – Define:** Set clear maximum time limits for different triage steps and document when a rollback must be triggered if progress is not being made so that teams always know the latest safe decision point.<br><br>**Phase 2 – Enforce:** Use these timeboxes during real incidents and empower the incident commander to enforce them so that teams do not get stuck endlessly trying the same actions while time passes.<br><br>**Phase 3 – Review:** After incidents, review where timeboxes were helpful and where they might need adjustment so that the approach remains realistic but firm. | - Timeboxed triage reduces excessively long incidents where teams remain in investigation mode long after rollback would have been safer for users.<br><br>- Defined limits encourage faster decision making because responders know a change of approach is required when a threshold is hit.<br><br>- Predictable bounds on triage efforts help RTO performance remain more consistent across incidents and services.<br><br>- Post-incident review of timebox adherence provides a structured lens for learning and process refinement.<br><br> | **Overage minutes reduced × RM/min**. | Breaches imply protracted triage windows. |
| RTO drill calendar | **Phase 1 – Focus:** Select the three worst performing services in terms of breaches and minutes over target and schedule regular RTO drills that simulate real incidents for those services.<br><br>**Phase 2 – Measure:** During each drill, measure how recovery time and minutes over target change compared to previous exercises so that improvements are captured with evidence.<br><br>**Phase 3 – Scale:** Once performance for these services stabilises, expand the drill approach to additional services so that overall RTO discipline improves across the estate. | - Focused drills create repeated practice for teams working on the riskiest services, making real-world responses faster and more confident.<br><br>- Simulations reveal hidden dependencies or process weaknesses in a safe environment before they cause real penalties or severe customer impact.<br><br>- Measured improvement across drill cycles provides leadership with clear evidence to justify investments in tooling, training or staffing.<br><br>- Expansion of drill practices from a small set of services to a wider estate steadily lifts overall RTO reliability culture.<br><br> | **ΔBreaches × avg minutes_over × RM/min**. | Tall bars identify drill candidates. |
""",
            "performance": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence |
|---|---|---|---|---|
| Pre-breach dashboards & timers | **Phase 1 – Visual:** Build dashboards that show live incidents, their elapsed time and the remaining time before RTO is breached so that everyone can see which cases are at risk.<br><br>**Phase 2 – Paging:** Configure the system to automatically page additional support or leadership when specific time thresholds are crossed so that help arrives before the breach happens.<br><br>**Phase 3 – Tune:** Regularly adjust these thresholds and notification rules based on real incident data so that alerts stay meaningful and do not overwhelm teams. | - Live RTO countdown dashboards turn the objective into a visible and manageable signal instead of a hidden line noticed only after a breach.<br><br>- Clear time-to-breach displays ensure attention is directed towards incidents closest to crossing the limit, sharpening operational focus during busy periods.<br><br>- Automatic paging rules give incident commanders a reliable mechanism for prioritising limited resources when multiple situations occur at once.<br><br>- Alert histories and response logs create an audit trail that can be analysed to refine thresholds, staffing patterns and escalation paths.<br><br> | **Breach reduction rate × incidents**. | Breach-heavy services need proactive cues. |
| Parallelize restore tasks | **Phase 1 – Map:** Analyse restore procedures to identify tasks that do not depend on each other and could be done at the same time instead of in a long sequence.<br><br>**Phase 2 – Execute:** Adjust runbooks and staffing so that these independent tasks are carried out in parallel during real incidents as long as it is safe to do so.<br><br>**Phase 3 – Validate:** After changes, review incidents to ensure that the new parallel approach kept quality high while reducing overall restore time. | - Parallelisation shortens total recovery time because independent activities no longer queue up behind each other unnecessarily.<br><br>- Revised runbooks allow staff capacity to be used more efficiently, with different responders handling different steps at the same time.<br><br>- Greater emphasis on concurrent low-risk tasks frees more senior staff to focus on complex decision making or customer communication.<br><br>- Structured analysis of the restore chain exposes which steps are truly dependent and which were historically sequenced by habit, supporting better long-term process design.<br><br> | **ΔMTTR × incidents** for worst services. | High averages suggest sequential bottlenecks. |
| Incident commander role | **Phase 1 – Assign:** For major incidents, assign a single incident commander responsible for coordination, communication and key decisions so that responsibility is clear from the outset.<br><br>**Phase 2 – Script:** Provide this commander with decision trees and guidelines that describe when to escalate, when to roll back and how to manage stakeholders so that the role is effective in practice.<br><br>**Phase 3 – Review:** After incidents, review the commander’s actions and outcomes to identify strengths and improvement areas which can be fed back into training. | - A clearly defined incident commander reduces confusion during high pressure incidents because a single point of control coordinates actions and communication.<br><br>- Centralised decision-making speeds up coordination across teams as tasks, updates and escalations follow one orchestrated plan.<br><br>- Stakeholders benefit from consistent, structured updates that come from one accountable owner rather than fragmented messages from many sources.<br><br>- Rotations through the commander role build leadership capability and provide experience that strengthens the organisation’s operational bench.<br><br> | **Coordination mins saved × incidents**. | High breach counts hint at coordination gaps. |
""",
            "satisfaction": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence |
|---|---|---|---|---|
| Live RTO countdown on status page | **Phase 1 – Expose:** Show a clear countdown or timeframe for expected recovery on the status page for each major incident so that users can see how close the situation is to the RTO limit.<br><br>**Phase 2 – Update:** Refresh this timer and the supporting narrative as new information becomes available so that what users see remains accurate throughout the incident.<br><br>**Phase 3 – Close:** Once the service is restored, update the page with a short reason for the incident and the key preventive actions being taken so that the story is complete. | - A visible RTO countdown reduces anxiety and speculation among users because the remaining time before the target is reached is transparent rather than hidden.<br><br>- Proactive updates on the status page decrease repeated requests for information since users can self-serve the latest view of progress.<br><br>- Clear visual signals create a perception of transparency and control, which helps protect trust even when service performance degrades temporarily.<br><br>- A shared view of RTO timing aligns business stakeholders and technical teams on the urgency and remaining recovery window.<br><br> | **Ticket deflection × handling cost** on breach-heavy services. | Misses are user-visible; clarity mitigates fallout. |
| Customer playbooks for critical flows | **Phase 1 – Identify:** Use incident and usage data to identify the most critical user journeys on services with frequent RTO breaches so that you know where downtime hurts most.<br><br>**Phase 2 – Publish:** Create simple, practical playbooks that describe how users can continue or adapt their work during outages affecting those journeys so that they are not completely blocked.<br><br>**Phase 3 – Measure:** Monitor how often these playbooks are accessed and whether they actually help reduce complaints and productivity loss during incidents. | - Customer-focused playbooks keep important business processes moving even when core systems are partially unavailable because alternative steps are clearly documented.<br><br>- Guidance on temporary options reduces feelings of helplessness when incidents occur by giving users constructive next actions instead of a passive wait.<br><br>- Well-designed instructions lower support volumes because many questions about what to do next are answered proactively in the playbook content.<br><br>- Observed usage of playbooks highlights which flows are too fragile and need long-term design changes because no meaningful workarounds exist.<br><br> | **Visible minutes avoided × value/min**. | Bars indicate where playbooks pay off. |
| VIP notifications | **Phase 1 – Tag:** Identify VIP users or accounts and tag their key services in monitoring and incident management tools so that you can see exactly when they are affected by breaches.<br><br>**Phase 2 – Notify:** Provide these VIPs with tailored pre breach warnings, incident updates and recovery ETAs through channels they prefer so that they are never surprised by impact to their operations.<br><br>**Phase 3 – Review:** After major events, gather feedback from VIPs on the quality and frequency of communication so that the notification approach can be refined. | - Tagging and targeted outreach strengthens relationships with high value customers by demonstrating active monitoring of services that matter most to them.<br><br>- Tailored notifications reduce escalations driven by surprise because VIPs receive early, direct information about risk and impact.<br><br>- Early awareness helps VIPs coordinate their own contingency plans, reducing the operational shock when RTO breaches occur.<br><br>- Structured feedback from priority accounts reveals what high value users expect from communication, shaping more effective engagement models for the wider base.<br><br> | **Churn avoided × ACV** for VIPs tied to worst bars. | Worst services likely hit VIPs hardest. |
"""
        }
        render_cio_tables("CIO – RTO Compliance", cio_8b)

    # ============================================================
    # 8c. Monthly MTTR Trend
    # ============================================================
    with st.expander("📌 Monthly MTTR Trend Over Time"):
        monthly = (
            df.groupby("month", as_index=False)
            .agg(
                avg_mttr=("recovery_time_minutes", "mean"),
                total_breaches=("rto_breach", "sum")
            )
        )

        # --- Graph: Monthly MTTR
        fig_mttr_monthly = px.line(
            monthly,
            x="month",
            y="avg_mttr",
            markers=True,
            title="Monthly Average MTTR Trend",
            labels={"month": "Month", "avg_mttr": "MTTR (minutes)"},
            color_discrete_sequence=[PRIMARY_BLUE],
            template="plotly_white",
        )
        st.plotly_chart(fig_mttr_monthly, use_container_width=True)

        peak_m = monthly.loc[monthly["avg_mttr"].idxmax()]
        low_m = monthly.loc[monthly["avg_mttr"].idxmin()]
        avg_monthly = float(monthly["avg_mttr"].mean())

        # Own analysis (Graph 3)
        st.markdown("### Analysis — Monthly MTTR Trend (Graph 3)")
        st.write(
f"""**What this graph is:** A **line chart** showing **monthly average MTTR (minutes)** over time.  
**X-axis:** Calendar month.  
**Y-axis:** Average minutes to recover (MTTR).

**What it shows in your data:**  
- **Highest MTTR month:** **{peak_m['month']}** at **{peak_m['avg_mttr']:.1f} mins**.  
- **Lowest MTTR month:** **{low_m['month']}** at **{low_m['avg_mttr']:.1f} mins**.  
- **Overall monthly average:** **{avg_monthly:.1f} mins**.

**Overall:** Spikes mark periods where processes or capacity were stressed; sustained highs imply process debt or insufficient rehearsal.

**How to read it operationally:**  
- **Gap to target:** Keep the series near or below **{avg_monthly:.1f} mins** while you tighten.<br>
- **Lead–lag:** Compare with **RTO breaches above**; months with higher MTTR typically show more breaches.<br>
- **Control:** Staff to demand in spike months, bundle risky work into planned windows, and run game-days to rehearse restores.

**Why this matters:** Stable, low MTTR produces **predictable recovery**, protecting SLAs and customer experience."""
        )

        # Additional analysis referencing the graph above (breaches vs monthly MTTR)
        worst_month_breaches = monthly.loc[monthly["total_breaches"].idxmax()] if monthly["total_breaches"].sum() > 0 else None
        if worst_month_breaches is not None:
            st.markdown("### Analysis — Monthly Breaches vs MTTR (Context from Graph 2)")
            st.write(
f"""**What this graph is (contextual comparison):** A reading of **monthly MTTR** alongside **monthly RTO breaches** from the graph above.  
**X-axis (reference):** Month.  
**Y-axis (reference):** MTTR minutes (this graph) vs Breach counts (above).

**What it shows in your data:**  
- **Highest breach month:** **{worst_month_breaches['month']}** with **{int(worst_month_breaches['total_breaches'])} breaches** and an MTTR of **{float(monthly.loc[monthly['month']==worst_month_breaches['month'],'avg_mttr'].iloc[0]):.1f} mins**.  
- MTTR spikes and breach spikes often co-occur, indicating capacity or process constraint.

**How to read it operationally:**  
- **Gap = penalty risk:** Shorten restore time in that month via pre-staged assets and timeboxed triage.<br>
- **Lead–lag:** If breach counts remain high even when MTTR improves, recalibrate RTOs then tighten progressively.<br>
- **Control:** Add **pre-breach timers** and **parallel restore** in the worst months first.

**Why this matters:** Synchronizing MTTR reduction with breach control yields the fastest drop in **penalty exposure** and **customer pain**."""
            )

        # CIO tables for Graph 3 (phased, detailed; use real values)
        rmmin_txt_c = f"(Avg RM/min≈RM {avg_rm_per_min:,.2f})" if has_cost and avg_rm_per_min == avg_rm_per_min else "RM/min from data (if available)"
        cio_8c = {
            "cost": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence |
|---|---|---|---|---|
| Staff to demand during spike months | **Phase 1 – Forecast:** Use historical data and the MTTR spike in **{peak_m['month']}** at **{peak_m['avg_mttr']:.1f} mins** to forecast when recovery demand is likely to be highest so that staffing can be planned in advance.<br><br>**Phase 2 – Flex:** Adjust on call and shift patterns during expected spike months so that more engineers are available when incidents are most likely to be complex or numerous.<br><br>**Phase 3 – Review:** After these months, review whether the additional coverage materially reduced MTTR and overtime and then scale the approach up or down for future cycles. | - Forecast-aligned staffing ensures engineering capacity is available during periods of higher recovery effort, preventing teams from being overwhelmed in peak months.<br><br>- Planned coverage reduces unplanned overtime because extra support is scheduled proactively instead of added at the last minute.<br><br>- Better resourcing in difficult periods improves incident outcomes since more people are available to share workload and handle parallel tasks.<br><br>- Post-period review provides clear data on the cost and benefit of flexible staffing models, informing longer-term workforce planning and budgets.<br><br> | **RM saved = ΔMTTR (vs {avg_monthly:.1f}) × incidents × {rmmin_txt_c}** in spike months. | Peak month **{peak_m['month']}** shows clear increase to **{peak_m['avg_mttr']:.1f} mins**. |
| Preventive fixes before high months | **Phase 1 – Identify:** Examine patterns in the months leading up to MTTR spikes to identify recurring faults or capacity issues that tend to trigger higher recovery times.<br><br>**Phase 2 – Schedule:** Plan and execute preventive maintenance, patches or design changes aimed at these recurring issues before the next expected high risk month begins.<br><br>**Phase 3 – Measure:** Compare MTTR and incident patterns before and after these preventive actions to verify that the high months are becoming less severe over time. | - Analysis of pre-spike months reduces the number of difficult incidents in high periods because known problem areas are addressed proactively rather than reactively.<br><br>- Shifting effort into preventive work smooths operational workload by moving a portion of effort from crisis periods into quieter planning windows.<br><br>- Proactive changes increase confidence that MTTR improvements are sustainable rather than dependent on exceptional firefighting during incidents.<br><br>- A structured pipeline of preventive fixes converts historical pain into targeted engineering work that steadily improves reliability.<br><br> | **Incidents avoided × avg_minutes × {rmmin_txt_c}**. | Spikes often follow repeat causes; line peak evidences timing. |
| Bundle risky work into planned windows | **Phase 1 – Cluster:** Identify high risk changes or maintenance activities and group them into controlled planned windows rather than allowing them to occur in a scattered, ad hoc fashion across the month.<br><br>**Phase 2 – Guardrails:** Within these windows, use canaries, extra monitoring and clear rollback plans so that if something goes wrong the impact on MTTR and outages is limited.<br><br>**Phase 3 – Audit:** After each window, review what went well and what caused issues so that the process can be improved for the next cycle. | - Consolidating high risk work into structured windows reduces the number of unplanned incidents that inflate monthly MTTR because potentially destabilising activity happens in safer conditions.<br><br>- A predictable change calendar makes planning easier for both technical teams and business stakeholders, improving coordination around critical dates.<br><br>- Tighter guardrails limit the blast radius of risky activities since changes are executed with additional safeguards and focused attention.<br><br>- Concentrated review of change windows strengthens learning because incident analysis can look at a coherent set of modifications instead of scattered individual changes.<br><br> | **ΔUnplanned incidents × minutes × {rmmin_txt_c}**. | Volatility in the line implies reactive work. |
| Improve on-call rotations | **Phase 1 – Balance:** Design on call schedules that balance night, weekend and holiday duties fairly across the team so that no single group is consistently overburdened.<br><br>**Phase 2 – Limits:** Set clear limits on consecutive nights or weeks on call so that engineers have enough time to rest and recover between intense periods.<br><br>**Phase 3 – Monitor:** Watch MTTR and incident quality metrics across different shifts to ensure that the rotation design is supporting good performance. | - Fair and balanced on-call design reduces the impact of fatigue on recovery time because engineers are less likely to handle critical incidents while exhausted.<br><br>- Shared responsibility for high-stress shifts improves morale and retention by avoiding chronic overload of a small subset of staff.<br><br>- Better-rested responders make higher-quality technical decisions during off hours, supporting safer and more effective recovery actions.<br><br>- Shift-level tracking of MTTR and quality provides feedback to refine rotation patterns and reinforce sustainable 24x7 operations.<br><br> | **ΔNight MTTR × incidents × {rmmin_txt_c}**. | Month-to-month drift suggests fatigue impact. |
| MTTR SLOs per month | **Phase 1 – Set:** Define monthly MTTR targets by service tier that reflect both business expectations and current technical capability so that performance has a clear reference point.<br><br>**Phase 2 – Watch:** Track MTTR against these targets throughout the month and generate alerts when the trend suggests that the SLO might be missed if nothing changes.<br><br>**Phase 3 – Correct:** Use these early warnings to trigger process adjustments, extra staffing or focused problem solving so that MTTR is brought back within the agreed range. | - Clear MTTR SLOs turn recovery performance into a managed objective rather than an after-the-fact statistic, enabling active control throughout the month.<br><br>- Early alerts encourage incremental corrections rather than waiting for large failures that demand drastic action.<br><br>- Alignment of SLOs with business tiers ensures that services with higher business impact receive tighter recovery attention.<br><br>- Transparent reporting of SLO performance supports accountability and constructive conversations with stakeholders about trade-offs and required investments.<br><br> | **Overage minutes reduced × {rmmin_txt_c}**. | Line deviations above **{avg_monthly:.1f} mins** show controllable overage. |
""",
            "performance": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence |
|---|---|---|---|---|
| Weekly MTTR standup | **Phase 1 – Review:** Hold a short weekly review where teams look at recent MTTR outliers, discuss what caused delays and identify any patterns across services.<br><br>**Phase 2 – Assign:** Convert the most important findings into clear actions with owners and due dates so that they do not get lost after the meeting ends.<br><br>**Phase 3 – Track:** Begin each subsequent standup by quickly checking progress on previous actions so that improvements keep moving. | - Weekly MTTR reviews create a regular feedback loop focused specifically on recovery performance instead of waiting for infrequent, high-level reviews.<br><br>- Rapid action assignment ensures that small but important process issues are addressed before they grow into structural problems.<br><br>- Frequent visibility keeps MTTR at the front of mind for both managers and engineers, reinforcing its role as a core reliability metric.<br><br>- Cross-team discussions in standups encourage knowledge sharing as techniques that improved MTTR in one area are transferred to others.<br><br> | **Time saved/week × incidents**. | Variability needs tight feedback loops. |
| Chaos/game days | **Phase 1 – Simulate:** Design realistic failure scenarios based on past incidents or known weak spots and run controlled simulations to practice recovery without impacting real users.<br><br>**Phase 2 – Measure:** During these exercises, measure recovery time, communication quality and process adherence to identify where improvements are needed.<br><br>**Phase 3 – Fix:** Implement changes to tooling, documentation and training based on the findings and repeat the simulations to confirm improvement. | - Controlled simulations build operational muscle memory so that real incidents feel like familiar scenarios rather than unpredictable crises.<br><br>- Game-day exercises uncover weaknesses in tooling, runbooks or communication flows that are difficult to spot during normal operations.<br><br>- Practice environments provide a safe space for experimenting with new recovery techniques, roles and coordination patterns before applying them in production.<br><br>- Documented improvements from repeated exercises demonstrate to stakeholders that resilience and recovery capability are being actively developed.<br><br> | **ΔMTTR × incidents** comparing pre/post drills. | Spikes indicate rehearsal need. |
| Auto-diagnostics at incident open | **Phase 1 – Instrument:** Configure systems so that when an incident is opened, key diagnostics such as logs, metrics and traces are automatically linked to the incident record.<br><br>**Phase 2 – Store:** Ensure that these diagnostics are stored in a structured, searchable way tied to the incident identifier so that engineers can quickly review them.<br><br>**Phase 3 – Use:** Train engineers to rely on these auto collected diagnostics as the first step in triage so that investigation starts from a rich evidence base. | - Automatic diagnostic capture reduces time wasted gathering basic information at the start of an incident because relevant data appears directly in the ticket.<br><br>- A structured evidence set improves the quality of diagnosis since engineers can see system behaviour immediately before and during the failure.<br><br>- Reliable storage of incident-linked diagnostics lowers the risk that vital clues disappear due to log rotation or manual mistakes.<br><br>- A consistent evidence trail supports better post-incident analysis and makes identification of recurring patterns easier over time.<br><br> | **ΔTriage_min × incidents**. | High months likely waste in triage. |
| Versioned runbooks | **Phase 1 – Curate:** Create runbooks for each key service and give them clear version numbers so that teams know which instructions are current.<br><br>**Phase 2 – Update:** Whenever architecture, tooling or processes change, update the relevant runbook and increment the version so that instructions remain aligned with reality.<br><br>**Phase 3 – Govern:** Periodically review runbook usage and accuracy to ensure that teams are using them and that they remain effective. | - Version-controlled runbooks keep recovery instructions accurate and reduce confusion caused by outdated documentation during incidents.<br><br>- A clear change history provides an audit trail of how recovery procedures have evolved, supporting governance and compliance requirements.<br><br>- Consistent use of up-to-date runbooks improves the predictability of outcomes because responders follow a validated pattern.<br><br>- Centralised management of versions makes it easier to roll out improvements organization-wide, embedding new best practices quickly.<br><br> | **Defects avoided × minutes**. | Instability reflects process drift. |
| Capacity guardrails during restore | **Phase 1 – Throttle/scale:** Implement mechanisms to temporarily throttle non critical traffic or scale resources during recovery so that core user journeys continue to perform acceptably while fixes are applied.<br><br>**Phase 2 – Monitor:** While these guardrails are active, closely watch key SLOs to ensure that throttling or scaling is helping rather than harming the situation.<br><br>**Phase 3 – Audit:** After recovery, review the use of guardrails and refine thresholds and rules so that they are even more effective next time. | - Capacity guardrails reduce the chance that systems collapse under load during recovery efforts, a failure mode that often extends outage duration.<br><br>- Protection of core user journeys maintains a tolerable experience for the most important transactions even when less critical features are temporarily constrained.<br><br>- Additional levers for stabilisation provide engineers with more options to control system behaviour while underlying causes are addressed.<br><br>- Observed behaviour under throttling and scaling informs longer-term capacity planning and resilience design, improving future architecture decisions.<br><br> | **Minutes saved under load × {rmmin_txt_c}**. | Peaks may coincide with high load. |
""",
            "satisfaction": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence |
|---|---|---|---|---|
| Publish monthly reliability note | **Phase 1 – Summarize:** At the end of each month, summarise key reliability signals such as MTTR peaks and troughs for months like **{peak_m['month']}** and **{low_m['month']}** in plain language that business users can understand.<br><br>**Phase 2 – Actions:** Briefly describe what actions were taken during the month to improve recovery time or stability so that stakeholders see progress rather than just numbers.<br><br>**Phase 3 – Commit:** Highlight a small set of commitments for the next month so that users know what to expect going forward. | - Regular reliability notes build trust by showing that MTTR and outage patterns are being monitored and actively managed rather than ignored.<br><br>- Proactive updates reduce ad hoc questions because key insights are communicated in a predictable, easy-to-consume format.<br><br>- Business stakeholders gain context for specific incidents since they can relate individual experiences to the broader recovery trend and improvement plan.<br><br>- A consistent narrative of continuous improvement supports long-term confidence in the IT organisation and underpins future investment discussions.<br><br> | **Ticket deflection × handling cost**. | Trend is easy to narrate for stakeholders. |
| Predictive user comms for spike months | **Phase 1 – Warn:** Before historically problematic months, inform users that these periods have previously shown higher MTTR and explain what is being done to reduce that risk.<br><br>**Phase 2 – Workarounds:** Share recommended workarounds or alternative scheduling strategies that users can adopt during these months to minimise disruption if incidents occur.<br><br>**Phase 3 – Follow-up:** After the period, share a short update on what actually happened and how effective the preparations were. | - Early warnings reduce surprise when issues occur in known high-risk periods because users are informed in advance and understand the context.<br><br>- Guidance on planning and workarounds empowers users to adapt their own workloads, reducing the impact of potential incidents on business operations.<br><br>- Joint planning reinforces the perception that IT and business are partners managing risk together rather than operating in silos.<br><br>- Follow-up messages provide feedback on which mitigation strategies worked, improving preparation for future high-risk periods.<br><br> | **Visible minutes avoided × value/min**. | Spike months identify when to pre-communicate. |
| Priority restoration for user-facing services | **Phase 1 – Order:** Rank services based on business and user impact, especially in spike months, so that everyone knows which systems must be restored first when multiple incidents occur.<br><br>**Phase 2 – Execute:** During incidents, follow this priority list and focus recovery efforts on the highest impact services before less visible internal systems.<br><br>**Phase 3 – Review:** After incidents, check whether the priority order still matches business needs and adjust as required. | - Clear prioritisation improves the perceived responsiveness of IT because user-facing and revenue-critical services are restored before lower-impact internal systems.<br><br>- Focused recovery efforts prevent teams from spreading capacity too thinly, concentrating energy on services where downtime hurts the most.<br><br>- Agreed priority lists remove debate during stressful events, accelerating the start of recovery actions.<br><br>- Periodic validation keeps the priority order aligned with evolving business strategy and customer expectations.<br><br> | **CSAT uplift** vs baseline. | Aligns effort with user pain during high MTTR months. |
| “What to expect” guides | **Phase 1 – Document:** Create simple guides explaining what typically happens during incidents, what communications users will receive and what they should do while waiting for recovery.<br><br>**Phase 2 – Surface:** Make these guides easy to find on portals or intranets so that users can access them quickly during real events.<br><br>**Phase 3 – Update:** Refine the guides over time using feedback from users and lessons learned from incidents. | - Clear “what to expect” guides reduce confusion and repeated questions about process because users understand the standard response pattern before they are affected by an incident.<br><br>- Practical advice in the guides helps users make better decisions during outages, including which actions to take and which to avoid.<br><br>- Defined expectations for updates, ETAs and closure messages support smoother communication and fewer misunderstandings.<br><br>- Shared understanding of roles and responses contributes to a more mature incident culture where staff and users know how to behave when problems arise.<br><br> | **Repeat contact drop × cost**. | High months trigger repeated questions. |
| Survey after recoveries | **Phase 1 – Pulse:** Within 24–48 hours after significant incidents, send short, focused surveys to users asking about their experience of communication, impact and recovery quality.<br><br>**Phase 2 – Fix:** Analyse the responses to identify the most common pain points and convert them into concrete improvement actions for processes, tools or communication templates.<br><br>**Phase 3 – Share:** Periodically share what has been changed as a result of this feedback so that users see their input being taken seriously. | - Post-recovery surveys provide direct insight into how incidents are experienced by users instead of relying solely on internal technical metrics.<br><br>- Aggregated feedback highlights the pain points where improvements in communication or recovery practice will have the greatest effect on satisfaction and productivity.<br><br>- Visible linkage between feedback and change strengthens trust and engagement because users see their opinions driving real adjustments.<br><br>- Trend data from repeated surveys shows whether process changes genuinely improve user experience over time.<br><br> | **Complaint recurrence ↓** month-over-month. | Trend informs when to survey. |
"""
        }
        render_cio_tables("CIO – Monthly MTTR Trend", cio_8c)
