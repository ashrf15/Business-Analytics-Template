import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np
import re

# ============================================================
# Helper: CIO Table Renderer
# ============================================================
def render_cio_tables(title, cio_data):
    st.subheader(title)
    with st.expander("Cost Reduction"):
        st.markdown(cio_data["cost"], unsafe_allow_html=True)
    with st.expander("Performance Improvement"):
        st.markdown(cio_data["performance"], unsafe_allow_html=True)
    with st.expander("Customer Satisfaction Improvement"):
        st.markdown(cio_data["satisfaction"], unsafe_allow_html=True)

# ============================================================
# Small helpers
# ============================================================
def _fmt_rm(x):
    try:
        return f"RM {float(x):,.0f}"
    except Exception:
        return "RM 0"

def _safe_sum(s):
    try:
        return float(pd.to_numeric(s, errors="coerce").fillna(0).sum())
    except Exception:
        return 0.0

def _safe_mean(s):
    try:
        return float(pd.to_numeric(s, errors="coerce").dropna().mean())
    except Exception:
        return float("nan")

# ============================================================
# 2️⃣ Service Overview
# ============================================================
def service_overview(df: pd.DataFrame):

    # ============================================================
    # COLUMN NORMALIZATION — EXTREME SAFE MODE
    # ============================================================
    df = df.copy()

    # Step 1: Strip spaces, normalize Unicode, lowercasing
    df.columns = [
        re.sub(r"[^\w]+", "_", str(c).strip().lower())
        .replace("\u200b", "")
        .replace("\xa0", "")
        .replace(" ", "")  # narrow no-break space
        for c in df.columns
    ]

    # Step 2: Replace any double underscores from cleaning
    df.columns = [re.sub(r"__+", "_", c) for c in df.columns]

    cols = set(df.columns)

    # --- Mesiniaga palette ---
    MES_BLUE = ["#004C99", "#007ACC", "#3399FF", "#66B2FF", "#9BD1FF"]

    # ============================================================
    # 2a. List of Critical IT Services Covered in the Report
    # ============================================================
    with st.expander("📌 List of Critical IT Services Covered in the Report"):
        required_cols = {"service_name", "downtime_minutes", "incident_count", "estimated_cost_downtime"}
        missing = required_cols - cols

        if not missing:
            # Aggregate
            svc_summary = (
                df.groupby("service_name", as_index=False)
                .agg({
                    "incident_count": "sum",
                    "downtime_minutes": "sum",
                    "estimated_cost_downtime": "sum",
                })
            )

            # Totals for evidence & cost math
            total_cost_all = _safe_sum(svc_summary["estimated_cost_downtime"])
            total_dt_all   = _safe_sum(svc_summary["downtime_minutes"])
            total_inc_all  = _safe_sum(svc_summary["incident_count"])

            top10 = svc_summary.sort_values("estimated_cost_downtime", ascending=False).head(10)
            top10_cost = _safe_sum(top10["estimated_cost_downtime"])
            top10_share = (top10_cost / total_cost_all * 100.0) if total_cost_all > 0 else 0.0

            fig = px.bar(
                top10,
                x="service_name",
                y="estimated_cost_downtime",
                text="estimated_cost_downtime",
                title="Top 10 Critical IT Services by Downtime Cost",
                labels={"service_name": "Service", "estimated_cost_downtime": "Downtime Cost (RM)"},
                color_discrete_sequence=MES_BLUE,
            )
            fig.update_traces(texttemplate="RM %{text:,.0f}", textposition="outside", cliponaxis=False)
            fig.update_layout(xaxis_tickangle=-15)
            st.plotly_chart(fig, use_container_width=True)

            # Peaks/lows inside the TOP10 set
            top_service = top10.iloc[0]
            low_service = top10.iloc[-1]

            # ---------- Analysis ----------
            st.markdown("### Analysis")
            st.markdown(
                f"""**What this graph is:** A ranked bar chart showing **downtime-related cost** by service (Top 10).

**X-axis:** Service name.  
**Y-axis:** Total **estimated downtime cost (RM)** over the reporting period.

**What it shows in your data:** The **highest cost** service is **{top_service['service_name']}** at **{_fmt_rm(top_service['estimated_cost_downtime'])}**, while the **lowest among the Top 10** is **{low_service['service_name']}** at **{_fmt_rm(low_service['estimated_cost_downtime'])}**. The Top 10 account for **{top10_share:.1f}%** of all downtime cost (**{_fmt_rm(top10_cost)}** of **{_fmt_rm(total_cost_all)}**), confirming cost concentration.

**How to read it operationally:**  
1) **Focus first:** Direct resilience investment to the top bars where ROI is highest.  
2) **Cross-check:** Compare each top service’s incidents and downtime minutes to isolate structural drivers.  
3) **Track monthly:** Re-run this chart to verify the bars shrink after remediation.  
4) **Benchmark:** Borrow practices from consistently low-cost peers.

**Why this matters:** Downtime cost maps directly to lost productivity/revenue. Targeting the small set of high-cost services yields the fastest cost recovery and improves overall availability."""
            )

            # ---------- CIO tables ----------
            highest_name = str(top_service["service_name"])
            highest_cost = float(top_service["estimated_cost_downtime"])
            highest_dt   = float(top_service["downtime_minutes"])
            avg_cost_top10 = _safe_mean(top10["estimated_cost_downtime"])

            cio_2a = {
                "cost": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Prioritize remediation for **{highest_name}** | **Phase 1:** Conduct a structured root-cause analysis on the top failure modes for {highest_name}. Document the specific triggers, impacted components, and the time-to-detect and time-to-recover for each issue so the team knows exactly what to fix. <br><br> **Phase 2:** Implement preventive controls such as redundancy, smarter alerting, and automated failover so the same faults cannot recur silently. Confirm monitoring coverage and simulate failure to validate the control works as intended. <br><br> **Phase 3:** Re-test the service in controlled scenarios and monitor live metrics with before and after baselines so the cost and downtime reduction can be verified. | – Delivers an immediate reduction of outage cost where the exposure is largest. <br><br> – Reduces repeat incidents by addressing the specific root causes that drive the biggest losses. <br><br> – Cuts overtime and urgent vendor call outs by stabilizing the service during peak demand windows. <br><br> – Accelerates payback within the current quarter because improvements are applied to the single biggest cost driver. | **Formula:** Avoidable Cost (upper bound) = Cost({highest_name}) = **{_fmt_rm(highest_cost)}**. | Bar chart shows {highest_name} is #1 by cost (**{_fmt_rm(highest_cost)}**). |
| Top-10 action program | **Phase 1:** Create a visible Top 10 remediation worklist with named owners, due dates, and expected cost takeout so everyone understands priorities. <br><br> **Phase 2:** Drive a weekly burn down cadence that removes blockers, verifies fixes in production, and records measurable reductions in incidents and minutes. <br><br> **Phase 3:** Graduate a service from the list only after its cost remains below the median for multiple cycles so improvements are locked in. | – Concentrates engineering effort where it will remove the most cost in the shortest time. <br><br> – Reduces aggregate exposure by shrinking several high impact bars at once. <br><br> – Introduces governance by metrics which improves accountability and speeds decision making. <br><br> – Increases forecasting accuracy because cost curves become stable after remediation. | **Formula:** Addressable Pool (Top-10) = **{_fmt_rm(top10_cost)}** (={top10_share:.1f}% of total). | Top-10 bars concentrate downtime cost (**{_fmt_rm(top10_cost)}**). |
| Shift planned work off-peak | **Phase 1:** Map each top service to its demand profile and identify low traffic windows where user impact is minimal. <br><br> **Phase 2:** Reschedule maintenance and deployments into those windows and pre stage rollback plans so reversals are quick if needed. <br><br> **Phase 3:** Validate that KPIs do not regress after the window and publish the outcomes for transparency. | – Minimizes business hour disruption so revenue and critical workflows are protected. <br><br> – Lowers lost productivity for end users because high impact tasks happen when demand is quiet. <br><br> – Reduces complaint volume because customers experience fewer visible interruptions. <br><br> – Improves SLA attainment because risky work happens away from peak periods. | **Formula:** Cost Avoided = ΔBusiness-hour minutes × (Cost/min).<br>**Data point:** Total minutes (all services) = **{int(total_dt_all):,}**. | Cost concentration indicates sensitivity to timing. |
| Remove chronic “long tails” | **Phase 1:** Identify services that consistently sit above the Top 10 median cost and label them as chronic contributors to leakage. <br><br> **Phase 2:** Apply a standard hardening pack that addresses monitoring gaps, recovery automation, and known configuration risks. <br><br> **Phase 3:** Exit a service from the chronic list when its cost remains below the threshold for several cycles and capture the pattern as a reusable playbook. | – Eliminates background leakage that erodes the gains from fixing the top bar only. <br><br> – Creates broad based stability so total platform risk comes down rather than shifting between services. <br><br> – Improves forecastability of operations workload because the tail no longer spikes unpredictably. <br><br> – Frees capacity for new work by reducing the steady trickle of avoidable incidents. | **Formula:** Sum of costs for long-tail services above threshold.<br>**Data:** Median/mean in chart. | Distribution shows several non-peak bars still sizable. |
| Tighten change freeze for Top-10 | **Phase 1:** Restrict risky changes near peak periods for Top 10 services and document the rule set that determines when freezes apply. <br><br> **Phase 2:** Enforce robust rollback plans and peer reviews before any exception is granted so residual risk is understood. <br><br> **Phase 3:** Audit all exceptions monthly and retire rules that no longer add value so velocity remains healthy without compromising stability. | – Lowers the number of change induced incidents on services that would have the most expensive impact. <br><br> – Shortens recovery time because changes are safer and better prepared. <br><br> – Reduces penalty exposure on customer contracts by avoiding avoidable breaches. <br><br> – Improves focus for engineers during critical windows because noise is reduced. | **Formula:** Cost Avoided = Incidents during freeze × avg cost per incident (RM).<br>**Data:** Incidents(top services) = **{int(_safe_sum(top10['incident_count'])):,}**. | Top-10 services align with higher incidents and cost. |
""",
                "performance": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| SLOs per service tied to cost | **Phase 1:** Define monthly SLO targets for each service tiered by cost impact so targets are proportionate to business value. <br><br> **Phase 2:** Configure early warning thresholds that auto escalate when trends indicate an SLO miss is likely. <br><br> **Phase 3:** Publish an SLO report that shows compliance, actions taken, and the effect on incidents. | – Focuses engineering effort on the services where reliability has the highest customer and financial impact. <br><br> – Raises predictability of service levels because risk is surfaced before breaches happen. <br><br> – Stabilizes queues during load because teams know where to place attention first. <br><br> – Improves planning for stakeholders because commitments are visible and tracked. | **Formula:** ΔSLO × Incidents(top services) = throughput gain. | High-cost bars reveal where tighter SLOs drive results. |
| Golden signals dashboard | **Phase 1:** Implement golden signals such as latency errors and saturation for the Top 10 services with clear alert routes. <br><br> **Phase 2:** Trigger alerts on early drift rather than on failure so response starts before users feel pain. <br><br> **Phase 3:** Review incidents with the supporting metrics to confirm whether signals were timely and actionable. | – Accelerates detection so engineers react before a minor issue becomes a customer facing outage. <br><br> – Cuts mean time to restore because diagnosis starts with high quality telemetry. <br><br> – Prevents cascade failures by treating leading indicators on shared components. <br><br> – Improves confidence in on call rotations because signals are reliable. | **Formula:** MTTR↓ × incidents(top services).<br>**Data:** Incidents(top services) = **{int(_safe_sum(top10['incident_count'])):,}**. | Costly services typically correlate with higher MTTR. |
| Auto-remediation runbooks | **Phase 1:** Encode the fixes for the most common faults into safe automation with clear guardrails and rollbacks. <br><br> **Phase 2:** Protect the automation with circuit breakers and error thresholds so it never makes a bad situation worse. <br><br> **Phase 3:** Track the weekly success rate and the minutes saved to refine the playbooks. | – Removes human latency from repetitive recovery tasks so services recover faster. <br><br> – Shrinks outage duration which directly reduces user impact. <br><br> – Frees engineers to focus on higher value analysis rather than repetitive manual steps. <br><br> – Creates consistent outcomes because the same fix runs the same way every time. | **Formula:** Minutes avoided = success_rate × minutes(top services).<br>**Data:** Minutes(top services) = **{int(_safe_sum(top10['downtime_minutes'])):,}**. | High downtime minutes in Top-10 bars. |
| Blast-radius reduction | **Phase 1:** Map cross service dependencies for the top services to understand where failures can spread. <br><br> **Phase 2:** Implement rate limits fallbacks and bulkhead patterns so one failure cannot pull down unrelated components. <br><br> **Phase 3:** Run quarterly chaos tests to verify that the designed containment actually works under stress. | – Limits the number of users and systems affected when a fault occurs. <br><br> – Prevents platform wide degradation by isolating failures to their origin. <br><br> – Improves resilience because critical paths are protected by design. <br><br> – Increases confidence to release changes because safety nets are proven. | **Formula:** Impacted minutes ↓ measurable in next cycle. | Concentration implies systemic coupling risk. |
| Weekly ops review on Top-10 | **Phase 1:** Hold a short owner review that inspects incidents actions and outstanding risks for each top service. <br><br> **Phase 2:** Track a simple burn down KPI that shows how quickly problems are being retired. <br><br> **Phase 3:** Graduate services once stability is proven and reassign capacity to the next most critical items. | – Creates a continuous improvement loop that prevents issues from lingering. <br><br> – Speeds removal of chronic problems by keeping attention on measurable outcomes. <br><br> – Strengthens ownership accountability because results are visible every week. <br><br> – Improves overall delivery rhythm by aligning teams on what matters. | **Formula:** ΔIncidents × avg restore time. | Post-intervention bars should compress over time. |
""",
                "satisfaction": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Proactive outage comms for Top-10 | **Phase 1:** Prepare clear status page templates and stakeholder messages for high impact services before the next incident happens. <br><br> **Phase 2:** Auto notify affected users when an event starts and include scope and expected timelines so stakeholders can plan. <br><br> **Phase 3:** Publish post mortem summaries with actions taken so customers see learning and improvement. | – Reduces uncertainty for users who rely on the affected services. <br><br> – Lowers ticket noise because users do not need to ask what is happening. <br><br> – Maintains trust during high impact events because communication is timely and factual. <br><br> – Improves sentiment after resolution because users understand the fix and next steps. | **Formula:** Complaints avoided × handling cost (RM).<br>**Data:** Cost exposure in Top-10 = **{_fmt_rm(top10_cost)}**. | High-cost services affect most users/business. |
| Tiered incident routing | **Phase 1:** Route incidents that hit Top 10 services directly to a senior queue with the right subject matter experts on call. <br><br> **Phase 2:** Ensure diagnostics and triage start immediately with pre collected logs and runbooks. <br><br> **Phase 3:** Rotate the SME pool to maintain coverage without fatigue. | – Delivers faster resolutions for the users most affected by outages. <br><br> – Increases first time fix rates because expertise is applied from the start. <br><br> – Raises perceived quality of IT because responses are decisive and informed. <br><br> – Protects critical business processes that depend on these services. | **Formula:** MTTR↓ × incidents(top services). | High incident counts in Top-10 subset. |
| Reliability status dashboard | **Phase 1:** Publish real time status by service and make the history easily accessible to build a factual narrative. <br><br> **Phase 2:** Keep a permanent archive so customers can see trends and not just snapshots. <br><br> **Phase 3:** Link workarounds when applicable so users can stay productive during recovery. | – Improves transparency which reduces inbound status queries. <br><br> – Decreases ad hoc chasers because information is available on demand. <br><br> – Lifts CSAT by giving users clarity during stressful events. <br><br> – Helps managers plan around incidents because visibility is continuous. | **Formula:** Escalations avoided × cost/esc. | Cost and incident concentration justify visibility. |
| “Customer care pack” for key users | **Phase 1:** Prepare pre agreed workaround kits and contact channels for high value user groups that are sensitive to downtime. <br><br> **Phase 2:** Provide a VIP communication lane so updates are prioritized and context is understood. <br><br> **Phase 3:** Review quarterly with those users to tune the approach. | – Protects retention of high value customers who experience the most impact. <br><br> – Reduces revenue risk by keeping critical users productive even during incidents. <br><br> – Enhances relationship capital because users see tailored support. <br><br> – Improves renewal conversations because reliability actions are visible. | **Formula:** Retention value (RM) documented in CRM. | Top services likely map to critical business units. |
| Publish quarterly reliability wins | **Phase 1:** Share improvements and measurable metrics that show how costs and downtime have reduced. <br><br> **Phase 2:** Recognize owners and teams that delivered the outcomes to reinforce the behaviors that work. <br><br> **Phase 3:** Set the next set of targets so momentum continues. | – Builds positive reinforcement that motivates teams to keep improving. <br><br> – Increases stakeholder confidence because results are visible and sustained. <br><br> – Supports funding decisions by demonstrating return on reliability investments. <br><br> – Encourages shared ownership across teams through public recognition. | **Formula:** N/A (qualitative CSAT gain). | Visible bar compression over quarters. |
"""
            }
            render_cio_tables("Critical IT Services – Recommendations", cio_2a)
        else:
            st.error(f"❌ Missing required columns for this section: {missing}")

    # ============================================================
    # 2b. Service Owners and Stakeholders
    # ============================================================
    with st.expander("📌 Service Owners and Stakeholders"):
        required_cols = {"service_owner", "stakeholder", "service_name", "downtime_minutes"}
        missing = required_cols - cols

        if not missing:
            owner_perf = (
                df.groupby(["service_owner", "stakeholder"], as_index=False)
                .agg({"downtime_minutes": "sum", "incident_count": "sum"})
                .sort_values("downtime_minutes", ascending=False)
            )

            total_dt_owner = _safe_sum(owner_perf["downtime_minutes"])
            top_owner = owner_perf.iloc[0]
            low_owner = owner_perf.iloc[-1]

            fig = px.bar(
                owner_perf,
                x="service_owner",
                y="downtime_minutes",
                color="stakeholder",
                text="downtime_minutes",
                title="Downtime by Service Owner and Stakeholder",
                labels={"downtime_minutes": "Downtime (minutes)", "service_owner": "Service Owner"},
                color_discrete_sequence=MES_BLUE,
            )
            fig.update_traces(texttemplate="%{text:.0f}", textposition="outside", cliponaxis=False)
            fig.update_layout(xaxis_tickangle=-15)
            st.plotly_chart(fig, use_container_width=True)

            # ---------- Analysis ----------
            st.markdown("### Analysis")
            st.markdown(
                f"""**What this graph is:** A stacked bar chart showing **total downtime minutes** by **service owner**, coloured by **stakeholder**.

**X-axis:** Service owner.  
**Y-axis:** Total downtime minutes (stacked by stakeholder).

**What it shows in your data:** The **highest downtime** owner is **{top_owner['service_owner']}** with **{int(top_owner['downtime_minutes']):,} minutes** (primary stakeholder: **{top_owner['stakeholder']}**), while the **lowest** is **{low_owner['service_owner']}** at **{int(low_owner['downtime_minutes']):,} minutes**. Overall downtime across owners totals **{int(total_dt_owner):,} minutes**.

**How to read it operationally:**  
1) **Assign accountability:** Owners with taller bars need focused reliability plans.  
2) **Stakeholder alignment:** Colour segments expose where stakeholder groups experience the most impact.  
3) **Load balance:** Compare incidents to see if a few owners are overloaded or under-skilled.  
4) **Trend watch:** Re-plot monthly to ensure bars shrink after targeted actions.

**Why this matters:** Clear ownership accelerates fixes and prevents repeat downtime. Aligning stakeholders and owners reduces handoff delays and improves SLA outcomes."""
            )

            # ---------- CIO tables ----------
            dt_top_owner = int(top_owner["downtime_minutes"])
            inc_top_owner = int(top_owner.get("incident_count", 0))

            cio_2b = {
                "cost": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Link downtime cost to ownership | **Phase 1:** Attribute downtime cost to each owner using a simple minutes times RM per minute model so the impact is clear and comparable. <br><br> **Phase 2:** Publish a monthly ranked dashboard that shows cost by owner so leaders can see where to invest. <br><br> **Phase 3:** Tie budget and incentives to measured cost reduction so behavior changes persist. | – Creates financial accountability by connecting outcomes to the teams that own them. <br><br> – Directs spend to the right owner because the largest cost centers are visible. <br><br> – Reduces duplicated efforts by focusing initiatives where they will actually move the needle. <br><br> – Improves leadership decision making because trade offs are quantified. | **Owner Cost** = (Owner minutes ÷ Total minutes) × Total RM.<br>**Data:** Top owner minutes = **{dt_top_owner:,}**. | Tallest bar = **{top_owner['service_owner']}** drives highest downtime minutes. |
| Budget by outcome | **Phase 1:** Allocate funds to owners who demonstrate quarter on quarter reductions in downtime minutes so capital follows actual results. <br><br> **Phase 2:** Defund low return initiatives that do not move the metrics and reassign resources to proven interventions. <br><br> **Phase 3:** Rebalance the model quarterly based on realized savings so the portfolio stays efficient. | – Maximizes return on investment because funds chase measurable improvement. <br><br> – Accelerates cost takeout by rewarding what works and stopping what does not. <br><br> – Improves forecasting of operational spend because interventions have tracked impact. <br><br> – Builds a culture of evidence based decisions across owners. | **Δminutes × RM/min**; compare pre vs post at owner level. | Owner bars enable apples-to-apples comparison. |
| Shared platform services | **Phase 1:** Centralize common capabilities such as monitoring backup and patch automation so owners stop buying and managing duplicates. <br><br> **Phase 2:** Negotiate volume pricing once centrally and standardize the stack so onboarding is faster. <br><br> **Phase 3:** Charge back usage fairly so owners have an incentive to optimize consumption. | – Eliminates tool sprawl that inflates license and support costs. <br><br> – Reduces administrative overhead because one platform replaces many. <br><br> – Raises baseline quality because standards are consistent across owners. <br><br> – Speeds incident response because teams operate familiar tools. | **Tooling cost avoided** vs current aggregate per owner. | Multiple owners repeating the same tooling needs. |
""",
                "performance": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Owner runbooks & drills | **Phase 1:** Standardize the top ten fault fixes per owner in clear runbooks so responders know the exact steps. <br><br> **Phase 2:** Run monthly time boxed drills to practice those runbooks and capture timings. <br><br> **Phase 3:** Track MTTR by scenario and iterate the instructions that underperform. | – Produces faster and repeatable restores because responders act from a tested script. <br><br> – Lowers variance across shifts so customer experience is more predictable. <br><br> – Reduces cognitive load during incidents which lowers mistakes. <br><br> – Builds confidence across teams because recovery is rehearsed. | **MTTR↓ × incidents(owner)** = minutes saved.<br>**Data:** Incidents(top owner) = **{inc_top_owner:,}**. | Tall bars imply slower recovery or higher fault rate. |
| Stakeholder escalation paths | **Phase 1:** Define a RACI with explicit timers so the right stakeholder is contacted at the right time. <br><br> **Phase 2:** Auto page the correct SME chain according to incident type so routing errors disappear. <br><br> **Phase 3:** Audit skipped steps weekly and remove bottlenecks that slow handoffs. | – Cuts handoff latency by ensuring the next action is triggered automatically. <br><br> – Reduces misrouting that wastes precious minutes during outages. <br><br> – Shrinks queue thrash at peak times because ownership is unambiguous. <br><br> – Improves coordination across teams through a reliable escalation path. | **Handoff delay↓ × incidents(owner)**. | Stack colours expose which stakeholders are most impacted. |
| Cross-skilling across owners | **Phase 1:** Pair adjacent owner teams for shadow rotations so secondary coverage is developed. <br><br> **Phase 2:** Certify backup responders on core systems so absences do not create gaps. <br><br> **Phase 3:** Rotate on call schedules to keep knowledge fresh across the bench. | – Removes single points of failure that make downtime longer. <br><br> – Improves coverage depth so incidents get the right skills faster. <br><br> – Stabilizes service during leave and seasonal peaks because backup capacity is real. <br><br> – Encourages shared standards as people work across teams. | **Reassignable tickets × avg restore time**. | Imbalance indicates dependency risk on few individuals. |
""",
                "satisfaction": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Publish owner scorecards | **Phase 1:** Report monthly CSAT uptime and incident KPIs by owner in a format that business users can understand. <br><br> **Phase 2:** Show trends versus last quarter so progress is obvious. <br><br> **Phase 3:** Recognize improvements publicly to reinforce positive behavior. | – Improves transparency so users know who is accountable for outcomes. <br><br> – Builds trust because progress and setbacks are communicated honestly. <br><br> – Creates healthy competition between owners to lift the experience. <br><br> – Helps business leaders plan because reliability is visible by domain. | **Complaints avoided × handling cost** (RM). | Users see who is accountable and how performance moves. |
| Stakeholder briefings post-incident | **Phase 1:** Hold a short post mortem for each owner within seventy two hours that explains what happened and why. <br><br> **Phase 2:** Publish action items with owners and due dates so stakeholders see the path to prevention. <br><br> **Phase 3:** Track closure on a dashboard so promises are verifiable. | – Reduces uncertainty by replacing rumor with facts. <br><br> – Prevents repeat escalations because stakeholders know what is being done. <br><br> – Aligns expectations for remediation and timelines. <br><br> – Increases confidence that lessons are being applied. | **Escalations avoided × cost/esc**. | Tall bars correlate with dissatisfaction/visibility risks. |
| VIP routing with owner SMEs | **Phase 1:** Route incidents affecting critical stakeholders directly to the relevant owner SMEs so context is not lost. <br><br> **Phase 2:** Define response and communication SLAs so VIPs receive timely and actionable updates. <br><br> **Phase 3:** Review service quality for VIP groups quarterly and adjust staffing where needed. | – Delivers faster outcomes for priority users who cannot afford downtime. <br><br> – Raises perceived competence because experts handle the case from the outset. <br><br> – Improves retention of key accounts by protecting their productivity. <br><br> – Reduces complaint escalations because communication is proactive and clear. | **VIP minutes saved × RM/min**. | Stack composition identifies priority stakeholder groups. |
"""
            }
            render_cio_tables("Service Owners & Stakeholders – Recommendations", cio_2b)
        else:
            st.error(f"❌ Missing required columns for this section: {missing}")

    # ============================================================
    # 2c. Service Categories Overview
    # ============================================================
    with st.expander("📌 Service Categories (Infrastructure, Applications, Communication)"):
        required_cols = {"service_category", "downtime_minutes", "estimated_cost_downtime"}
        missing = required_cols - cols

        if not missing:
            cat_summary = (
                df.groupby("service_category", as_index=False)
                .agg({
                    "downtime_minutes": "sum",
                    "estimated_cost_downtime": "sum",
                })
                .sort_values("estimated_cost_downtime", ascending=False)
            )

            total_cat_cost = _safe_sum(cat_summary["estimated_cost_downtime"])
            total_cat_minutes = _safe_sum(cat_summary["downtime_minutes"])
            top_cat = cat_summary.iloc[0]
            low_cat = cat_summary.iloc[-1]

            fig = px.pie(
                cat_summary,
                names="service_category",
                values="estimated_cost_downtime",
                hole=0.4,
                title="Downtime Cost by Service Category",
                color_discrete_sequence=MES_BLUE,
            )
            st.plotly_chart(fig, use_container_width=True)

            # ---------- Analysis ----------
            st.markdown("### Analysis")
            st.markdown(
                f"""**What this graph is:** A donut chart showing **share of downtime cost (RM)** by **service category**.

**X-axis:** (Categorical) Service category.  
**Y-axis:** (Implicit) Share of total estimated downtime cost.

**What it shows in your data:** The **highest-cost** category is **{top_cat['service_category']}** at **{_fmt_rm(top_cat['estimated_cost_downtime'])}**, while the **lowest** is **{low_cat['service_category']}** at **{_fmt_rm(low_cat['estimated_cost_downtime'])}**. Across all categories, total cost is **{_fmt_rm(total_cat_cost)}** with **{int(total_cat_minutes):,} total downtime minutes**.

**How to read it operationally:**  
1) **Prioritize top slice:** Focus capacity and resilience improvements on the largest wedge.  
2) **Monitor mid slices:** Small improvements here can push them to the tail.  
3) **Tail slices:** Codify practices from these reliable categories.  
4) **Rebalance:** Ensure investment aligns with cost share.

**Why this matters:** Cost concentration by category points to where budget and engineering yield the greatest business impact."""
            )

            # ---------- CIO tables ----------
            cio_2c = {
                "cost": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Build redundancy for **{top_cat['service_category']}** | **Phase 1:** Map single points of failure across the full category stack including data stores messaging layers and external dependencies so risk hotspots are documented. <br><br> **Phase 2:** Introduce failover replication and health checks that can switch traffic automatically when a fault is detected and test them in staging. <br><br> **Phase 3:** Run quarterly failover drills with explicit success SLOs so teams can prove recovery works under realistic conditions. | – Cuts unplanned downtime in the highest cost category by ensuring a backup path exists. <br><br> – Reduces breach penalties because outages are shorter and less frequent. <br><br> – Stabilizes revenue critical flows that depend on this category. <br><br> – Increases operational confidence because failover is rehearsed not theoretical. | **Upper-bound Potential Avoidable Cost** = **{_fmt_rm(top_cat['estimated_cost_downtime'])}**. | Donut shows {top_cat['service_category']} dominates cost share. |
| Optimize capacity allocation | **Phase 1:** Profile CPU memory storage and network headroom per category so saturation patterns are known. <br><br> **Phase 2:** Apply throttling and autoscale policies that expand capacity gracefully when load rises instead of failing hard. <br><br> **Phase 3:** Remove hotspots and validate before and after performance so the improvements are measurable. | – Prevents saturation induced incidents that drive severe performance drops. <br><br> – Smooths user experience by keeping latency within expected bounds during peaks. <br><br> – Lowers firefighting workload for operations because the platform copes with variability. <br><br> – Makes spend more efficient because capacity is matched to real demand. | **Minutes avoided** = Δsaturation events × avg minutes impact. | High cost implies saturation episodes are consequential. |
| Off-peak maintenance policy | **Phase 1:** Shift maintenance for this category to low demand windows identified from usage analytics so the user impact is minimized. <br><br> **Phase 2:** Freeze risky work during peak business periods and document exception criteria so rules are clear. <br><br> **Phase 3:** Audit exceptions and publish adherence so discipline is maintained without blocking necessary work. | – Minimizes disruption during business hours for users who depend on the affected systems. <br><br> – Reduces user complaints because interventions are less visible. <br><br> – Improves SLA hit rate by avoiding preventable breaches during peak. <br><br> – Protects team capacity because urgent follow ups after daytime changes are reduced. | **ΔBusiness-hour minutes × RM/min**.<br>**Data:** Category minutes total = **{int(total_cat_minutes):,}**. | Cost concentration heightens sensitivity to timing. |
""",
                "performance": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Category-tiered SLOs | **Phase 1:** Define SLOs per category according to cost impact tier so higher exposure receives tighter targets. <br><br> **Phase 2:** Alert when indicators trend off target with thresholds that give time to intervene. <br><br> **Phase 3:** Review monthly with a backlog of actions tied to owners so slippage is corrected. | – Lifts stability where value is highest by aligning targets to impact. <br><br> – Keeps teams focused on the signals that matter most. <br><br> – Prevents drift into breach conditions because early alerts trigger action. <br><br> – Improves cross team coordination because expectations are explicit. | **ΔSLO × incidents(category)**. | Largest slice warrants tighter SLO governance. |
| Early-warning signals | **Phase 1:** Add category specific probes for latency error rates and saturation and ensure alerts include context for fast triage. <br><br> **Phase 2:** Auto page the correct SMEs with on call rotations that balance load. <br><br> **Phase 3:** Track MTTR trends and refine thresholds to maximize true positive rates. | – Detects issues earlier so user impact is smaller. <br><br> – Lowers MTTR because responders land on the problem with the right information. <br><br> – Reduces blast radius when failures happen because containment starts sooner. <br><br> – Builds confidence that monitoring is actionable not noisy. | **MTTR↓ × incidents(category)**. | High cost → earlier detection yields outsized benefit. |
| Fault-budget policy | **Phase 1:** Allocate a measured error budget per category so a controlled amount of risk is tolerated for velocity. <br><br> **Phase 2:** Halt risky changes when the budget is exhausted so stability is restored before new work lands. <br><br> **Phase 3:** Reset budgets monthly and capture learnings that adjust policies for the next cycle. | – Prevents compounding incidents by pausing change when the environment is fragile. <br><br> – Enforces disciplined releases that respect reliability constraints. <br><br> – Drives safer behavior during pressure periods. <br><br> – Provides a transparent mechanism to balance speed and safety. | **Minutes saved** when freezes trigger pre-breach. | Category share evidences risk concentration. |
""",
                "satisfaction": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Category reliability reports | **Phase 1:** Publish a monthly report that shows uptime cost and key incidents for each category in plain language. <br><br> **Phase 2:** Compare results against last quarter and targets so progress is obvious. <br><br> **Phase 3:** Share the next step mitigations so customers know what will improve next. | – Boosts stakeholder confidence by giving clear evidence of reliability performance. <br><br> – Reduces ad hoc status requests because the information is readily available. <br><br> – Aligns expectations around trade offs and timelines for improvements. <br><br> – Encourages constructive dialogue because the same facts are shared. | **Complaints avoided × cost/complaint**. | Donut clarifies which categories users feel most. |
| Tailored comms by category | **Phase 1:** Prepare outage templates that reflect the business impact of each category so messages resonate. <br><br> **Phase 2:** Notify affected business units promptly with ETAs and clear next steps. <br><br> **Phase 3:** Provide workaround links and keep updates flowing until stability is confirmed. | – Lowers the number of chaser tickets because users have timely answers. <br><br> – Sets clear expectations which reduces frustration during incidents. <br><br> – Raises perceived competence because communication is structured and helpful. <br><br> – Improves coordination with business teams who can plan around outages. | **Escalations avoided × cost/esc**. | Largest slices impact the widest audience. |
| Feedback loops per category | **Phase 1:** Run short post incident micro surveys targeted at users of the affected category to capture real pain points. <br><br> **Phase 2:** Convert the top feedback items into backlog work with owners and due dates. <br><br> **Phase 3:** Close the loop publicly so users see their input turning into changes. | – Improves fitness for purpose because changes are guided by user feedback. <br><br> – Raises CSAT and NPS because users feel heard and see outcomes. <br><br> – Builds long term trust through visible action after incidents. <br><br> – Helps prioritize work that actually reduces future frustration. | **CSAT uplift × user base size**. | Category lens localizes improvement to where it matters. |
"""
            }
            render_cio_tables("Service Categories – Recommendations", cio_2c)
        else:
            st.error(f"❌ Missing required columns for this section: {missing}")
