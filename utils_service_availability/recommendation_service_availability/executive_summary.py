# utils_availability/executive_summary.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# --- Mesiniaga theme ---
px.defaults.template = "plotly_white"
MES_BLUE = ["#004C99", "#007ACC", "#3399FF", "#66B2FF", "#9BD1FF"]


def _to_dt(s):
    return pd.to_datetime(s, errors="coerce")


def _num(df: pd.DataFrame, cols: list[str]):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def _fmt_date(d):
    try:
        return pd.to_datetime(d).strftime("%d %b %Y")
    except Exception:
        return str(d)


# ============================================================
# Helper for CIO tables – standard pattern
# ============================================================
def render_cio_tables(title, cio):
    st.subheader(title)
    with st.expander(" Cost Reduction"):
        st.markdown(cio["cost"], unsafe_allow_html=True)
    with st.expander(" Performance Improvement"):
        st.markdown(cio["performance"], unsafe_allow_html=True)
    with st.expander(" Customer Satisfaction Improvement"):
        st.markdown(cio["satisfaction"], unsafe_allow_html=True)


def _to_num(x):
    return pd.to_numeric(x, errors="coerce")


def executive_summary(df: pd.DataFrame):
    """
    IT Service Availability – Executive Summary (compatible with the attached dataset)
    Columns detected and used when present:
      - report_date, service_name, service_category, service_owner, stakeholder
      - uptime_percentage, downtime_minutes, incident_count, major_incident, root_cause
      - recovery_time_minutes, rto_target_minutes, sla_target, sla_met
      - maintenance_type, maintenance_window, maintenance_impact
      - business_impact, estimated_cost_downtime
      - cpu_utilization, memory_utilization, disk_utilization, network_utilization
      - capacity_status, improvement_action, month
    """

    # ------------------ Prep ------------------
    df = df.copy()
    if "Unnamed: 0" in df.columns:
        df = df.drop(columns=["Unnamed: 0"])

    if "report_date" in df.columns:
        df["report_date"] = _to_dt(df["report_date"])

    numeric_cols = [
        "uptime_percentage",
        "downtime_minutes",
        "incident_count",
        "estimated_cost_downtime",
        "recovery_time_minutes",
        "rto_target_minutes",
        "sla_target",
        "sla_met",
        "cpu_utilization",
        "memory_utilization",
        "disk_utilization",
        "network_utilization",
    ]
    _num(df, numeric_cols)

    # Guard against negative artifacts
    for c in [
        "downtime_minutes",
        "recovery_time_minutes",
        "rto_target_minutes",
        "uptime_percentage",
    ]:
        if c in df.columns:
            df[c] = df[c].clip(lower=0)

    # ============================================================
    # 1️⃣ Key KPI Overview (cards + clear line breaks in Analysis)
    # ============================================================
    with st.expander("📌 Key Availability Metrics Overview", expanded=True):
        st.markdown("### Overall Service Performance Indicators")

        col1, col2, col3, col4 = st.columns(4)

        avg_uptime = (
            df["uptime_percentage"].mean()
            if "uptime_percentage" in df.columns
            else np.nan
        )
        total_dt = (
            df["downtime_minutes"].sum()
            if "downtime_minutes" in df.columns
            else np.nan
        )
        total_inc = (
            df["incident_count"].sum()
            if "incident_count" in df.columns
            else np.nan
        )
        total_cost = (
            df["estimated_cost_downtime"].sum()
            if "estimated_cost_downtime" in df.columns
            else np.nan
        )

        st.markdown("#### Analysis")
        bullets = []
        if pd.notna(avg_uptime):
            bullets.append(
                f"• Average uptime across the reporting period is {avg_uptime:.2f}%, indicating the overall reliability baseline."
            )
        if pd.notna(total_dt):
            bullets.append(
                f"• Cumulative downtime amounts to {total_dt:,.0f} minutes, which reflects the aggregate disruption window experienced by users."
            )
        if pd.notna(total_inc):
            bullets.append(
                f"• Total incident volume is {total_inc:,.0f}, a proxy for operational load and potential repeat issues."
            )
        if pd.notna(total_cost):
            bullets.append(
                f"• Estimated financial impact recorded in data is RM {total_cost:,.0f}; this should be used to rank remediation ROI."
            )
        if bullets:
            st.markdown("<br>".join(bullets), unsafe_allow_html=True)
        else:
            st.info("KPIs cannot be derived because required columns are missing.")

    # ============================================================
    # 2️⃣ Uptime Trend Over Time
    # ============================================================
    if {"report_date", "uptime_percentage"}.issubset(df.columns):
        with st.expander("📌 Uptime Trend Over Time", expanded=False):
            uptime_trend = (
                df.dropna(subset=["report_date"])
                .groupby("report_date", as_index=False)["uptime_percentage"]
                .mean()
                .sort_values("report_date")
            )
            if not uptime_trend.empty:
                fig = px.line(
                    uptime_trend,
                    x="report_date",
                    y="uptime_percentage",
                    title="Average Uptime Trend by Date",
                    labels={
                        "report_date": "Report Date",
                        "uptime_percentage": "Uptime (%)",
                    },
                    markers=True,
                    color_discrete_sequence=MES_BLUE,
                )
                st.plotly_chart(fig, use_container_width=True)

                max_idx = uptime_trend["uptime_percentage"].idxmax()
                min_idx = uptime_trend["uptime_percentage"].idxmin()
                max_u = uptime_trend.loc[max_idx]
                min_u = uptime_trend.loc[min_idx]
                rng = max_u["uptime_percentage"] - min_u["uptime_percentage"]
                mean_u = uptime_trend["uptime_percentage"].mean()

                target = (
                    df["sla_target"].dropna().iloc[0]
                    if "sla_target" in df.columns
                    and df["sla_target"].notna().any()
                    else None
                )
                breaches = None
                if target is not None:
                    breaches = int(
                        (uptime_trend["uptime_percentage"] < target).sum()
                    )

                st.markdown("### Analysis")
                st.write(
                    f"""**What this graph is:** A time-series line chart showing **average uptime (%)** per reporting date.  
**X-axis:** Calendar date.  
**Y-axis:** Average uptime (%) for the date.

**What it shows in your data:** Peak uptime on **{_fmt_date(max_u['report_date'])}** at **{max_u['uptime_percentage']:.2f}%** and the lowest on **{_fmt_date(min_u['report_date'])}** at **{min_u['uptime_percentage']:.2f}%**. The span between peak and low is **{rng:.2f} percentage points**. Average across the period is **{mean_u:.2f}%**{f"; days below target ({target:.2f}%): **"+str(breaches)+"**" if breaches is not None else ""}.

**How to read it operationally:**  
- **Gap = reliability delta:** The vertical distance between peak and trough shows volatility to reduce.  
- **Lead–lag with change windows:** Cross-check dips with release/maintenance to pinpoint regressions.  
- **Recovery strength:** Faster rebound after dips = healthier engineering controls.  
- **Control:** Aim to keep the line above SLO/SLA with minimal variance.

**Why this matters:** Uptime is the headline reliability signal. Keeping the line high and flat reduces SLA penalties, support tickets, and downstream business disruption."""
                )

                ev = f"Peak {_fmt_date(max_u['report_date'])} {max_u['uptime_percentage']:.2f}% vs low {_fmt_date(min_u['report_date'])} {min_u['uptime_percentage']:.2f}%; mean {mean_u:.2f}%."

                cio_uptime = {
                    "cost": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence |
|---|---|---|---|---|
| Stabilize peak-to-trough variance | **Phase 1 – Pinpoint dips:** Identify the top three dip dates and correlate them with deployments, infrastructure changes, or vendor incidents so that each dip has a clearly documented cause. <br><br>**Phase 2 – Harden weak points:** Apply concrete fixes such as rollbacks, configuration safeguards, rate limiting, or capacity buffers on the exact components linked to the dips. <br><br>**Phase 3 – Re-verify stability:** Monitor in the next release cycle to confirm the dip pattern is eliminated and lock the changes as permanent safeguards. | - Reduces the volatility in reliability which directly lowers the probability of SLA breaches during busy periods.<br><br>- Decreases firefighting effort because the repetitive root causes are removed and teams can focus on value work.<br><br>- Improves predictability for stakeholders which makes planning and communications more credible.<br><br>- Creates durable engineering controls that maintain a consistently high uptime floor. | Variance band = peak−low = **{rng:.2f} pp**; a 50% shrink reduces exposure to half the current swing. | {ev} |
| Pre-emptive maintenance during safe windows | **Phase 1 – Map safe windows:** Use historic trends to find time ranges with the lowest user impact and schedule changes only inside those windows. <br><br>**Phase 2 – Enforce change freezes:** Establish blackout periods around peak transaction times and month-end activities to prevent self-inflicted dips. <br><br>**Phase 3 – Audit impact rigorously:** After each window, compare uptime before and after the change and capture any small regressions for immediate rollback. | - Lowers rework and overtime because fewer changes collide with peak demand and fewer fixes are required after hours.<br><br>- Protects critical business cycles which reduces escalations and loss of trust from stakeholders.<br><br>- Improves maintenance efficiency as teams operate in controlled windows with clear rollback plans.<br><br>- Produces cleaner trend lines that are easier to monitor and explain to leadership. | Days below the mean **{mean_u:.2f}%** converted to safe windows reduce overtime and penalty exposure{f'; includes **{breaches}** below-target days if SLA target is {target:.2f}%' if breaches is not None else ''}. | {ev} |
| Noise reduction in monitoring | **Phase 1 – Remove redundant alerts:** Identify signatures that never lead to action and suppress or aggregate them to cut noise. <br><br>**Phase 2 – Tune thresholds:** Calibrate alert thresholds and deduplication rules so that signals fire only when service health degrades. <br><br>**Phase 3 – Monthly review loop:** Re-evaluate alert performance and retire stale rules as architecture evolves. | - Cuts analyst triage minutes so teams respond faster to the signals that actually matter.<br><br>- Reduces alert fatigue which lowers the risk of missing real incidents during heavy periods.<br><br>- Improves the MTTA and MTTR chain because teams spend less time sorting noise and more time fixing issues.<br><br>- Increases confidence in dashboards which supports faster decision making. | Analyst minutes saved = (alerts eliminated × average review minutes) measured from current alert volumes. | {ev} |
""",
                    "performance": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence |
|---|---|---|---|---|
| Automated rollback for change-related dips | **Phase 1 – Detect regressions quickly:** Create post-deploy guards that watch golden metrics and trigger alerts when error rate or latency deviates beyond allowed bands. <br><br>**Phase 2 – Execute safe rollback:** Provide a one-click or scripted rollback path with automatic traffic shifting and state checks. <br><br>**Phase 3 – Compare outcomes:** Perform A/B comparisons of pre- and post-rollback metrics to ensure stability and document learnings. | - Shrinks the duration of low-uptime windows which directly lowers customer impact.<br><br>- Reduces manual intervention time which improves overall recovery speed and consistency.<br><br>- Encourages safer experimentation because teams have a proven escape hatch.<br><br>- Builds institutional knowledge that prevents repeats of the same regression. | Dip duration saved = average minutes of post-deploy regression eliminated by automatic rollback. | {ev} |
| Golden-path runbooks for top services | **Phase 1 – Document critical paths:** Produce step-by-step recovery guides for the highest value services covering diagnostics, decision trees, and verification. <br><br>**Phase 2 – Drill the team:** Run regular tabletop and live exercises so owners can execute under pressure without delay. <br><br>**Phase 3 – Track MTTR shrinkage:** Measure the reduction in restore time and update runbooks when gaps are discovered. | - Improves recovery speed because responders follow proven steps instead of improvising during incidents.<br><br>- Reduces variance in outcomes which helps leadership rely on consistent timelines.<br><br>- Accelerates onboarding of new engineers who can perform at a higher level sooner.<br><br>- Increases cross-team coordination because responsibilities are unambiguous. | MTTR improvement (minutes) × number of incidents on covered services across the period. | {ev} |
| Real-time SLO dashboard and breach forecast | **Phase 1 – Expose live SLOs:** Show current uptime against target with clear thresholds per service. <br><br>**Phase 2 – Predict breaches:** Use rolling windows to forecast when the service will fall below target if no action is taken. <br><br>**Phase 3 – Weekly review:** Review forecast accuracy and interventions to continuously tighten controls. | - Enables earlier interventions which keep uptime above target before customers feel pain.<br><br>- Aligns operations and engineering around one truth which improves coordination.<br><br>- Reduces unplanned penalties through proactive guardrail actions.<br><br>- Builds confidence with stakeholders who can see issues before they become incidents. | Breaches avoided × penalty minutes; compare against the observed below-target days{f' (**{breaches}** days)' if breaches is not None else ''}. | {ev} |
""",
                    "satisfaction": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence |
|---|---|---|---|---|
| Transparent status updates on dip days | **Phase 1 – Auto-publish banners:** When uptime drops, immediately inform users on the portal with clear scope and symptoms. <br><br>**Phase 2 – Provide reliable ETAs:** Share realistic restoration timelines and next steps to set expectations. <br><br>**Phase 3 – Summarize resolution:** Close with a concise post-mortem note to restore confidence. | - Reduces inbound queries because customers know that the team is aware and working on the issue.<br><br>- Preserves trust during disruption by communicating clearly and consistently.<br><br>- Improves satisfaction post-incident because users understand what changed and why it will be better.<br><br>- Decreases escalation volume as expectations are managed in real time. | Queries avoided compared to historical average on dip days after transparent communication is enabled. | {ev} |
| Stakeholder reliability brief | **Phase 1 – Publish monthly narrative:** Present peaks, lows, actions taken, and risk areas in a concise executive format. <br><br>**Phase 2 – Align decisions:** Tie remediation proposals to business impact and seek targeted approvals. <br><br>**Phase 3 – Track commitments:** Report on action completion and the resulting trend movement. | - Increases leadership confidence which speeds funding and removes blockers.<br><br>- Reduces ad-hoc escalations because stakeholders already see the plan and the trajectory.<br><br>- Improves cross-department coordination when priorities are explained with data.<br><br>- Builds durable accountability through published commitments. | Escalations avoided per month following adoption of the reliability brief cadence. | {ev} |
| Celebrate stable months | **Phase 1 – Recognize excellence:** Publicly acknowledge teams that achieved flat high uptime with data-backed results. <br><br>**Phase 2 – Extract practices:** Document the behaviors and controls that produced stability. <br><br>**Phase 3 – Replicate widely:** Coach other teams to adopt the same patterns and measure diffusion. | - Reinforces the behaviors that create reliability which makes them more common across the portfolio.<br><br>- Increases motivation and retention because teams see the impact of their work.<br><br>- Accelerates convergence on best practice which reduces variance across services.<br><br>- Produces faster systemic improvement through positive examples. | Reduction in time to adopt best-practice across additional services after recognition and playbook sharing. | {ev} |
"""
                }

                render_cio_tables("CIO — Uptime Trend Recommendations", cio_uptime)
            else:
                st.info("No uptime data available to display.")

    # ============================================================
    # 3️⃣ Downtime by Service
    # ============================================================
    if {"service_name", "downtime_minutes"}.issubset(df.columns):
        with st.expander("📌 Total Downtime by Service", expanded=False):
            svc_down = (
                df.groupby("service_name", as_index=False)["downtime_minutes"]
                .sum()
                .sort_values("downtime_minutes", ascending=False)
            )
            if not svc_down.empty:
                fig = px.bar(
                    svc_down,
                    x="service_name",
                    y="downtime_minutes",
                    text="downtime_minutes",
                    title="Total Downtime by Service",
                    labels={
                        "service_name": "Service",
                        "downtime_minutes": "Downtime (minutes)",
                    },
                    color_discrete_sequence=MES_BLUE,
                )
                fig.update_traces(textposition="outside", cliponaxis=False)
                fig.update_layout(xaxis_tickangle=-15)
                st.plotly_chart(fig, use_container_width=True)

                worst = svc_down.iloc[0]
                best = svc_down.iloc[-1]
                top3_minutes = svc_down["downtime_minutes"].head(3).sum()

                st.markdown("### Analysis")
                st.write(
                    f"""**What this graph is:** A ranked **bar chart** of **total downtime (minutes)** by service.  
**X-axis:** Service name.  
**Y-axis:** Total downtime minutes across the reporting period.

**What it shows in your data:** Highest downtime at **{worst['service_name']}** (**{worst['downtime_minutes']:.0f} minutes**) and lowest at **{best['service_name']}** (**{best['downtime_minutes']:.0f} minutes**). Top-3 services contribute **{top3_minutes:.0f} minutes** combined, indicating outsized ROI from targeted fixes.

**How to read it operationally:**  
- **Top bars:** Immediate candidates for resilience fixes (redundancy, failover, alerting).  
- **Tail services:** Benchmark reliable practices for reuse.  
- **Shifts over time:** Re-run monthly to confirm bar height reduction after mitigations.  
- **Correlate:** Pair with root causes to find structural issues.

**Why this matters:** Minutes lost map directly to user pain and cost. Reducing the tallest bars yields the fastest recovery of availability and the biggest cost savings."""
                )

                ev = (
                    f"Top service **{worst['service_name']}** "
                    f"{worst['downtime_minutes']:.0f} mins; Top-3 sum **{top3_minutes:.0f}** mins; "
                    f"Best **{best['service_name']}** {best['downtime_minutes']:.0f} mins."
                )

                cio_downtime = {
                    "cost": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence |
|---|---|---|---|---|
| Hardening plan for top-3 downtime services | **Phase 1 – Deep-dive RCA:** For each of the top three services by downtime, compile a component-level fault tree and quantify repeat failure modes. <br><br>**Phase 2 – Implement resilience controls:** Add redundancy, auto-restart, circuit breaking, and failover policies that directly address the dominant modes. <br><br>**Phase 3 – Validate results:** Run soak and chaos tests to prove the new design reduces downtime and then lock the configuration. | - Concentrates investment where the majority of downtime minutes occur which drives the fastest ROI.<br><br>- Reduces repeat incidents that drain operations time and increase user dissatisfaction.<br><br>- Improves stability for the most visible services which lowers escalation pressure.<br><br>- Creates proven architecture patterns that can be applied to the remaining services. | Minutes to reclaim ≈ Top-3 total **{top3_minutes:.0f} mins** × achievable reduction percentage based on chosen controls. | {ev} |
| Proactive component replacement | **Phase 1 – Identify flapping components:** Use incident logs to isolate hardware or service components with recurring intermittent failures. <br><br>**Phase 2 – Replace or upgrade:** Swap the unstable parts with vendor-supported and tested alternatives. <br><br>**Phase 3 – Monitor for regression:** Track downtime trend line for at least one full operating cycle to confirm stability. | - Prevents cyclical failures that repeatedly trigger outages and emergency work.<br><br>- Reduces total repair time and associated coordination costs across teams.<br><br>- Improves user confidence as chronic issues disappear from status reports.<br><br>- Frees engineering capacity to address higher value reliability improvements. | Avoided repair hours = prior repeat incidents × average repair minutes converted to hours. | {ev} |
| Maintenance window consolidation | **Phase 1 – Batch non-urgent work:** Group compatible maintenance activities into fewer, longer windows rather than many small ones. <br><br>**Phase 2 – Reduce window count:** Coordinate across teams to minimize the number of service interruptions. <br><br>**Phase 3 – Track preparation overhead:** Measure planning and coordination time saved per quarter. | - Lowers administrative overhead and reduces the number of disruptions perceived by users.<br><br>- Cuts after-hours effort which reduces overtime costs and fatigue risk.<br><br>- Simplifies communications because fewer notices are required for customers.<br><br>- Delivers clearer performance reporting with fewer maintenance artifacts. | Administrative minutes saved = maintenance windows eliminated × average preparation minutes. | {ev} |
""",
                    "performance": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence |
|---|---|---|---|---|
| Failover drills for top services | **Phase 1 – Simulate quarterly:** Conduct realistic failover exercises including traffic shift and data checks. <br><br>**Phase 2 – Record recovery metrics:** Capture RTO, data integrity, and user impact for each drill. <br><br>**Phase 3 – Close gaps:** Prioritize and fix bottlenecks before the next production incident. | - Reduces recovery time during real incidents because responders have rehearsed the exact steps.<br><br>- Increases reliability of failover paths which minimizes user impact.<br><br>- Builds confidence across leadership that the team can handle outages effectively.<br><br>- Surfaces hidden dependencies that would otherwise cause long delays. | Δ(recovery minutes) pre- vs post-drill × number of incidents on the drilled services. | {ev} |
| Real-time anomaly detection | **Phase 1 – Enable signal-based alerting:** Use latency, error, and saturation signals rather than single device alarms. <br><br>**Phase 2 – Tune noise:** Calibrate to lower false positives and group related alerts. <br><br>**Phase 3 – Weekly review:** Iterate thresholds and rules based on analyst feedback. | - Detects degradation earlier which shortens the resulting downtime minutes.<br><br>- Improves responder focus by suppressing noisy alerts and highlighting actionable clusters.<br><br>- Reduces incident sprawl by catching issues before they cascade.<br><br>- Enhances situational awareness for duty engineers. | Minutes saved per incident equals the earlier detection window measured from current alerting performance. | {ev} |
| Hot-path observability | **Phase 1 – Instrument critical user paths:** Add tracing and health checks to the endpoints that matter most. <br><br>**Phase 2 – Set SLO-aligned alerts:** Trigger on user-experience thresholds rather than raw infrastructure metrics. <br><br>**Phase 3 – Rotate ownership:** Assign clear owners to each hot path and rotate readiness duties. | - Accelerates detection and isolation of issues along the most valuable journeys.<br><br>- Increases accountability which shortens coordination time during incidents.<br><br>- Improves decision quality because data reflects user experience directly.<br><br>- Supports meaningful SLA reporting that aligns with business outcomes. | SLA breaches avoided × breach penalty minutes as measured after observability improvements. | {ev} |
""",
                    "satisfaction": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence |
|---|---|---|---|---|
| User-facing comms for top services | **Phase 1 – Publish clear banners:** Provide plain-language incident and maintenance notices with scope and likely impact. <br><br>**Phase 2 – Share dependable ETAs:** Update customers with time-boxed expectations and workarounds. <br><br>**Phase 3 – Post-incident recap:** Explain the fix and prevention steps to close the loop. | - Decreases uncertainty for users which reduces help-desk contact volume during outages.<br><br>- Builds credibility because communication is timely and specific.<br><br>- Improves satisfaction even when incidents occur as customers feel informed.<br><br>- Reduces repeat complaints after service is restored. | Queries avoided during outage windows compared to historical baselines without proactive communication. | {ev} |
| Service health dashboards for stakeholders | **Phase 1 – Expose uptime and downtime trends:** Provide drill-downs by service with context. <br><br>**Phase 2 – Enable self-service:** Allow stakeholders to pull reports without ad-hoc requests. <br><br>**Phase 3 – Monthly walkthrough:** Review trends and planned actions with business owners. | - Lowers ad-hoc update burden on the ops team which frees time for delivery work.<br><br>- Increases trust because stakeholders see the same data as the operations team.<br><br>- Improves decision speed for prioritizing reliability investments.<br><br>- Reduces escalation volume due to improved transparency. | Hours of ad-hoc briefing avoided per month after dashboards are adopted. | {ev} |
| Share best-practice from low-downtime services | **Phase 1 – Capture patterns:** Document design and operational practices used by consistently stable services. <br><br>**Phase 2 – Pilot in high-risk areas:** Apply these patterns to one or two problematic services. <br><br>**Phase 3 – Scale across portfolio:** Roll out with training and measure adoption. | - Accelerates improvement by reusing proven methods rather than reinventing fixes.<br><br>- Reduces variance across teams which creates more predictable outcomes.<br><br>- Increases team confidence by providing concrete playbooks.<br><br>- Produces faster systemic uplift with limited additional cost. | Time-to-parity decreases across services as practices are replicated and measured. | {ev} |
"""
                }

                render_cio_tables("CIO — Downtime by Service", cio_downtime)
            else:
                st.info("No downtime data found for visualization.")

    # ============================================================
    # 4️⃣ MTTR vs RTO (optional but supported by your dataset)
    # ============================================================
    if {
        "service_name",
        "recovery_time_minutes",
        "rto_target_minutes",
    }.issubset(df.columns):
        with st.expander("📌 Recovery Time vs RTO", expanded=False):
            mttr = (
                df.groupby("service_name", as_index=False)[
                    ["recovery_time_minutes", "rto_target_minutes"]
                ]
                .mean()
                .dropna(subset=["recovery_time_minutes", "rto_target_minutes"])
            )
            if not mttr.empty:
                fig = px.scatter(
                    mttr,
                    x="rto_target_minutes",
                    y="recovery_time_minutes",
                    text="service_name",
                    title="MTTR vs RTO by Service",
                    labels={
                        "rto_target_minutes": "RTO Target (min)",
                        "recovery_time_minutes": "Average Restore Time (min)",
                    },
                    trendline="ols",
                    color_discrete_sequence=MES_BLUE,
                )
                st.plotly_chart(fig, use_container_width=True)

                breaches_mask = (
                    mttr["recovery_time_minutes"] > mttr["rto_target_minutes"]
                )
                breaches = int(breaches_mask.sum())
                overage_minutes = (
                    mttr.loc[breaches_mask, "recovery_time_minutes"]
                    - mttr.loc[breaches_mask, "rto_target_minutes"]
                ).sum()
                slowest = mttr.iloc[mttr["recovery_time_minutes"].idxmax()]
                fastest = mttr.iloc[mttr["recovery_time_minutes"].idxmin()]

                st.markdown("### Analysis")
                st.write(
                    f"""**What this graph is:** A **scatter plot** comparing **average restore time (MTTR)** to **RTO target** per service.  
**X-axis:** RTO target (minutes).  
**Y-axis:** Average restore time (minutes).

**What it shows in your data:** **{breaches}** services sit **above** the diagonal (breaching RTO on average). Slowest restore: **{slowest['service_name']}** at **{slowest['recovery_time_minutes']:.0f} min**; fastest: **{fastest['service_name']}** at **{fastest['recovery_time_minutes']:.0f} min**. Total overage above RTO across breaches is **{overage_minutes:.0f} minutes**.

**How to read it operationally:**  
- **Above line:** Requires acceleration (automation, paging, runbooks) or RTO re-baseline.  
- **Near line:** Add guardrails to avoid slipping into breach.  
- **Below line:** Capture practices and replicate.  
- **Trend:** Track quarterly to verify MTTR reductions.

**Why this matters:** Breaching RTOs undermines contractual trust and increases business risk. Driving points below the line safeguards commitments and reduces downtime exposure."""
                )

                ev = (
                    f"Breaches: **{breaches}** services; total overage **{overage_minutes:.0f} mins**; "
                    f"slowest {slowest['service_name']} {slowest['recovery_time_minutes']:.0f} min "
                    f"vs fastest {fastest['service_name']} {fastest['recovery_time_minutes']:.0f} min."
                )

                cio_mttr_rto = {
                    "cost": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence |
|---|---|---|---|---|
| Automate restore workflows for breaching services | **Phase 1 – Map current restore steps:** Document each manual action, decision point, and validation for the services that breach RTO. <br><br>**Phase 2 – Script repetitive work:** Convert the highest-frequency steps into idempotent scripts or runbook automation with built-in safety checks. <br><br>**Phase 3 – Enable one-click execution:** Provide an orchestrated button that performs the sequence reliably under pressure. | - Cuts human latency during restoration which brings average restore times under the RTO line.<br><br>- Reduces error rates that occur when responders work from memory during stressful incidents.<br><br>- Improves capacity planning because restore time becomes predictable and measurable.<br><br>- Increases the number of incidents resolved within contract, lowering penalty risk. | Overage minutes to eliminate = **{overage_minutes:.0f} mins** across breaching services based on current period data. | {ev} |
| Paging and escalation policy refresh | **Phase 1 – Tighten on-call rotations:** Ensure primary and secondary responders cover all critical hours with clear SLAs for response times. <br><br>**Phase 2 – Add secondary triggers on breach forecast:** When telemetry predicts an RTO breach, automatically page senior support without waiting for a manual decision. <br><br>**Phase 3 – Drill quarterly:** Test escalation paths and measure mean response time improvements. | - Improves response speed which directly compresses the overall restore time.<br><br>- Reduces the long tail of incidents by getting the right expertise engaged earlier.<br><br>- Increases confidence that critical services are always covered even during off-hours.<br><br>- Lowers the variance of outcomes which helps reporting and planning. | MTTR delta (minutes) × frequency of incidents that previously breached RTO after escalation improvements. | {ev} |
| Hot-spare or blue-green for chronic breachers | **Phase 1 – Identify chronic outliers:** Select services that repeatedly sit above the RTO line despite process fixes. <br><br>**Phase 2 – Add hot-spare or blue-green:** Provide a pre-warmed environment or parallel stack to fail to when the primary path is degraded. <br><br>**Phase 3 – Validate failover MTTR:** Execute controlled failovers to prove the new approach meets targets. | - Removes lengthy restore procedures from the critical path which brings chronic breachers into compliance.<br><br>- Improves service continuity for users because failovers are rapid and reversible.<br><br>- Reduces stress on responders who can focus on root cause after the service is stable.<br><br>- Creates a repeatable pattern for other high-risk services. | Minutes saved = historical average restore time minus measured failover time for each targeted service. | {ev} |
""",
                    "performance": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence |
|---|---|---|---|---|
| Runbook standardization | **Phase 1 – Normalize tasks by scenario:** Build canonical runbooks for the top restore scenarios with tested commands and validation steps. <br><br>**Phase 2 – Template in the toolchain:** Publish runbooks inside the incident platform with parameter prompts and guardrails. <br><br>**Phase 3 – Train teams:** Walk through runbooks during rotations and verify competency. | - Reduces variance in restore outcomes which tightens performance around the RTO target.<br><br>- Speeds up execution because steps are sequenced and pre-approved.<br><br>- Improves auditability as actions are consistent and logged.<br><br>- Shortens onboarding for new responders who can contribute sooner. | Standard-deviation of restore time shrinks relative to the pre-standardization period, measured in minutes. | {ev} |
| SLO-driven alerts near RTO threshold | **Phase 1 – Define pre-breach signals:** Alert when predicted restore time risks crossing the RTO threshold. <br><br>**Phase 2 – Route to owners:** Send actionable alerts to the responsible team with context and next steps. <br><br>**Phase 3 – Weekly review:** Inspect near-misses and refine thresholds for better precision. | - Enables earlier corrective actions which keeps more incidents below the RTO line.<br><br>- Reduces noisy paging because alerts are tied to business thresholds rather than raw metrics.<br><br>- Improves coordination between teams with a shared definition of risk.<br><br>- Stabilizes service recovery performance over time. | Breaches avoided × penalty minutes using observed breach counts as the baseline. | {ev} |
| Post-incident learning loop | **Phase 1 – 48-hour review:** Conduct structured reviews with timeline, impact, and action items. <br><br>**Phase 2 – Assign and close actions:** Track fixes in a shared system and prevent re-occurrence. <br><br>**Phase 3 – Trend outcomes:** Verify that similar incidents resolve faster over the next quarters. | - Converts isolated fixes into sustained performance gains that compound over time.<br><br>- Reduces repeat failure modes which lowers incident frequency and duration.<br><br>- Improves cultural maturity by reinforcing learning rather than blame.<br><br>- Enhances credibility with stakeholders through visible follow-through. | Reduction in repeat breaches over subsequent quarters relative to the baseline rate. | {ev} |
""",
                    "satisfaction": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence |
|---|---|---|---|---|
| Proactive customer comms on RTO breach risk | **Phase 1 – Notify early:** When a breach looks likely, inform affected users with the scope, likely duration, and workarounds. <br><br>**Phase 2 – Maintain cadence:** Provide reliable updates until service is restored and confirm when normal operations resume. <br><br>**Phase 3 – Close with clarity:** Send a brief resolution summary and next steps to avoid recurrence. | - Reduces complaints because users understand the situation and timing.<br><br>- Preserves trust by showing ownership and transparency throughout the event.<br><br>- Improves satisfaction scores in post-incident surveys as expectations are managed.<br><br>- Decreases inbound calls which frees the team to focus on restoration. | Queries and complaints avoided on breach-risk days compared to historical averages without proactive communication. | {ev} |
| Publish restore reliability metrics | **Phase 1 – Share MTTR vs RTO monthly:** Provide a consistent report to stakeholders with clear visuals. <br><br>**Phase 2 – Highlight improvements:** Show what changed and how it affected restore times. <br><br>**Phase 3 – Gather feedback:** Incorporate stakeholder input into the next iteration of improvements. | - Builds confidence that the team is improving core reliability quarter over quarter.<br><br>- Reduces ad-hoc data requests because stakeholders have a scheduled, reliable report.<br><br>- Aligns investment decisions with measured outcomes.<br><br>- Encourages teams to sustain improvements due to visibility. | Escalations avoided after regular reporting begins and stakeholders gain clarity on progress. | {ev} |
| Acknowledge fastest services | **Phase 1 – Recognize best performers:** Publicize services consistently below RTO with clean incident handling. <br><br>**Phase 2 – Share methods:** Document their tactics and tools. <br><br>**Phase 3 – Replicate across peers:** Coach similar teams to adopt the same approach. | - Reinforces behaviors that keep restore times low which strengthens culture.<br><br>- Accelerates diffusion of effective methods to other services.<br><br>- Maintains high morale because teams see their excellence mattering to the organization.<br><br>- Improves overall portfolio performance as more services meet targets. | Improvement toward parity across services measured as a reduction in the gap to the leaders. | {ev} |
"""
                }

                render_cio_tables("CIO — MTTR vs RTO", cio_mttr_rto)
            else:
                st.info("Insufficient data points to compare MTTR and RTO.")

    # ============================================================
    # 5️⃣ Cost of Downtime by Service Category
    # ============================================================
    if {"service_category", "estimated_cost_downtime"}.issubset(df.columns):
        with st.expander(
            "📌 Cost of Downtime by Service Category", expanded=False
        ):
            cat_cost = (
                df.groupby("service_category", as_index=False)[
                    "estimated_cost_downtime"
                ]
                .sum()
                .sort_values("estimated_cost_downtime", ascending=False)
            )
            if not cat_cost.empty:
                fig = px.bar(
                    cat_cost,
                    x="service_category",
                    y="estimated_cost_downtime",
                    title="Estimated Cost of Downtime by Service Category (RM)",
                    labels={
                        "service_category": "Service Category",
                        "estimated_cost_downtime": "Cost (RM)",
                    },
                    text="estimated_cost_downtime",
                    color_discrete_sequence=MES_BLUE,
                )
                fig.update_traces(
                    texttemplate="RM %{text:,.0f}",
                    textposition="outside",
                    cliponaxis=False,
                )
                fig.update_layout(xaxis_tickangle=-15)
                st.plotly_chart(fig, use_container_width=True)

                top = cat_cost.iloc[0]
                low = cat_cost.iloc[-1]
                top3_rm = cat_cost["estimated_cost_downtime"].head(3).sum()

                st.markdown("### Analysis")
                st.write(
                    f"""**What this graph is:** A **bar chart** aggregating **estimated cost of downtime (RM)** by service category.  
**X-axis:** Service category.  
**Y-axis:** Total estimated downtime cost (RM).

**What it shows in your data:** Highest cost category is **{top['service_category']}** at **RM {top['estimated_cost_downtime']:,.0f}**; lowest is **{low['service_category']}** at **RM {low['estimated_cost_downtime']:,.0f}**. Top-3 categories account for **RM {top3_rm:,.0f}** combined.

**How to read it operationally:**  
- **Top categories:** Prioritize resilience/capacity spend for maximum ROI.  
- **Middle band:** Monitor closely—small improvements may avert step-ups.  
- **Tail:** Preserve stability; mine best practices.  
- **Budgeting:** Align reduction initiatives to upcoming quarters.

**Why this matters:** Cost concentration indicates the fastest route to savings. Targeted fixes in the top categories reduce risk, penalties, and lost productivity."""
                )

                ev = (
                    f"Top category **{top['service_category']}** RM {top['estimated_cost_downtime']:,.0f}; "
                    f"Top-3 sum **RM {top3_rm:,.0f}**; Lowest **{low['service_category']}** "
                    f"RM {low['estimated_cost_downtime']:,.0f}."
                )

                cio_cost_category = {
                    "cost": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence |
|---|---|---|---|---|
| Top-3 category remediation programme | **Phase 1 – Prioritize failure modes:** Identify the dominant failure patterns and operational weaknesses within the three most expensive categories. <br><br>**Phase 2 – Implement targeted controls:** Apply redundancy, auto-healing, and capacity tuning specifically mapped to those patterns. <br><br>**Phase 3 – Re-baseline financial impact:** Measure cost reduction after remediation and recycle savings into the next highest category. | - Concentrates spend where it produces the largest reduction in downtime cost which improves payback time.<br><br>- Reduces exposure to penalties and lost productivity by addressing the categories that drive the majority of impact.<br><br>- Creates a repeatable investment playbook guided by real numbers which improves governance.<br><br>- Builds stakeholder confidence through transparent ROI tracking. | Addressable exposure ≈ Top-3 = **RM {top3_rm:,.0f}** × achievable reduction percentage validated post-remediation. | {ev} |
| Premium tier only on hot paths | **Phase 1 – Identify user-critical components:** Trace the transactions and systems that create the most business value inside each category. <br><br>**Phase 2 – Apply premium tiers surgically:** Place higher reliability or faster recovery only on those hot paths instead of upgrading everything. <br><br>**Phase 3 – Measure outcome precisely:** Track incident frequency and cost changes to confirm that targeted spend outperforms broad upgrades. | - Lowers total cost by avoiding blanket upgrades while still protecting the most important user journeys.<br><br>- Improves perceived performance for critical functions which reduces complaint volume.<br><br>- Increases agility in budgeting because enhancements are scoped with precision.<br><br>- Creates clarity on which components genuinely need premium resilience. | Premium spend is justified when avoided downtime RM in the targeted components exceeds the incremental tier cost for the same period. | {ev} |
| Vendor SLA renegotiation using loss data | **Phase 1 – Prepare evidence pack:** Compile category-level cost of downtime and breach history for vendor-owned components. <br><br>**Phase 2 – Align incentives:** Negotiate credits and penalties that reflect the true business impact when targets are missed. <br><br>**Phase 3 – Monitor delivery:** Track vendor performance monthly and enforce agreed remedies. | - Reduces external risk exposure because vendor contracts now reflect actual impact to the business.<br><br>- Improves reliability where vendors respond to stronger incentives and clearer targets.<br><br>- Recovers value through credits that offset periods of poor delivery.<br><br>- Supports strategic sourcing decisions with hard numbers. | Recovered credits = negotiated terms × historical breach profile converted into RM according to contract clauses. | {ev} |
""",
                    "performance": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence |
|---|---|---|---|---|
| Chaos and soak tests for costly categories | **Phase 1 – Run controlled failure tests:** Inject realistic faults to observe resilience under stress. <br><br>**Phase 2 – Fix weak points:** Address the precise failure propagation paths that the tests reveal. <br><br>**Phase 3 – Re-test and verify:** Ensure that fixes reduce incident frequency and duration. | - Decreases the chance of large outages because weaknesses are found in rehearsals instead of production.<br><br>- Improves recovery playbooks by exposing real behavior under failure.<br><br>- Raises team readiness which shortens time to diagnose and repair.<br><br>- Produces measurable declines in downtime minutes over time. | Incidents avoided × average incident RM impact for the targeted categories. | {ev} |
| Capacity tuning on high-cost categories | **Phase 1 – Profile CPU, IO, and memory pressure:** Identify saturation and throttling that correlate with incidents. <br><br>**Phase 2 – Tune or right-size:** Adjust limits, concurrency, and scaling to remove pressure hotspots. <br><br>**Phase 3 – Validate trend:** Monitor incident rate and response time to confirm improvement. | - Stabilizes performance and reduces failure cascades that lead to costly outages.<br><br>- Improves user experience during peak load which decreases complaint spikes.<br><br>- Optimizes infrastructure spending by placing capacity where it actually removes risk.<br><br>- Creates clearer operating margins that prevent sudden degradations. | RM impact reduced through fewer and shorter incidents after capacity changes, measured against the current baseline. | {ev} |
| Event correlation and early warning | **Phase 1 – Link infrastructure signals to business services:** Map component alerts to user-facing service health. <br><br>**Phase 2 – Act pre-emptively:** Trigger mitigations when patterns precede incidents. <br><br>**Phase 3 – Review alert efficacy:** Retire weak predictors and strengthen strong ones. | - Enables earlier containment of failures which reduces the length and spread of outages.<br><br>- Improves triage accuracy because alerts carry business context.<br><br>- Lowers noise so responders can focus on the events that move the needle.<br><br>- Raises the percentage of incidents caught before users feel impact. | Minutes avoided × RM per minute for each affected category after correlation is implemented. | {ev} |
""",
                    "satisfaction": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence |
|---|---|---|---|---|
| Customer-grade incident communications for top categories | **Phase 1 – Tailor the channel and message:** Use language that is easy for customers to understand and select the right communication channel. <br><br>**Phase 2 – Provide hourly updates:** Maintain a dependable cadence with honest ETAs and workarounds. <br><br>**Phase 3 – Close with clarity:** Share what changed and how recurrence risk is being reduced. | - Reduces frustration because customers are not left guessing about progress.<br><br>- Lowers complaint volume as expectations are set and met throughout the incident.<br><br>- Increases trust in the operations team since communication is reliable and consistent.<br><br>- Improves survey responses following transparent handling of difficult events. | Complaint volume drop measured during high-cost category incidents after adopting the new communication cadence. | {ev} |
| Quarterly value report | **Phase 1 – Show RM saved versus baseline:** Present a clear before-and-after comparison for each major initiative. <br><br>**Phase 2 – Highlight trend direction:** Explain how the metrics are moving and what remains to be addressed. <br><br>**Phase 3 – Define next actions:** List funded and proposed items with expected ROI. | - Builds trust with leadership and secures continued funding for effective reliability initiatives.<br><br>- Reduces ad-hoc status requests because progress is visible and scheduled.<br><br>- Aligns teams on priorities informed by financial impact rather than anecdotes.<br><br>- Encourages disciplined execution because outcomes are tracked publicly. | Stakeholder escalation rate decreases after routine value reporting is established and maintained. | {ev} |
| Replicate practices from low-cost categories | **Phase 1 – Extract patterns:** Document design and process practices from the categories with the lowest downtime cost. <br><br>**Phase 2 – Pilot in high-cost areas:** Apply the same controls to similar services and measure differences. <br><br>**Phase 3 – Scale wins:** Roll out broadly once benefits are proven. | - Shortens time to improvement by reusing proven operational patterns.<br><br>- Reduces the learning curve because teams implement steps that already work in the same environment.<br><br>- Increases consistency of delivery which stabilizes overall experience.<br><br>- Produces measurable cost reductions without heavy experimentation. | Time-to-improvement shortens relative to greenfield approaches when best-practice is replicated. | {ev} |
"""
                }

                render_cio_tables("CIO — Cost of Downtime (Category)", cio_cost_category)
            else:
                st.info("No cost data available to analyze.")

    # ============================================================
    # 6️⃣ SLA Compliance Overview (optional if data present)
    # ============================================================
    if {"service_name", "sla_met"}.issubset(df.columns):
        with st.expander("📌 SLA Compliance by Service", expanded=False):
            sla = (
                df.groupby("service_name", as_index=False)["sla_met"]
                .mean()
                .assign(sla_pct=lambda x: 100 * x["sla_met"])
            )
            if not sla.empty:
                fig = px.bar(
                    sla.sort_values("sla_pct", ascending=False),
                    x="service_name",
                    y="sla_pct",
                    title="SLA Compliance by Service (%)",
                    labels={"service_name": "Service", "sla_pct": "SLA Met (%)"},
                    text="sla_pct",
                    color_discrete_sequence=MES_BLUE,
                )
                fig.update_traces(
                    texttemplate="%{text:.1f}%",
                    textposition="outside",
                    cliponaxis=False,
                )
                fig.update_layout(xaxis_tickangle=-15)
                st.plotly_chart(fig, use_container_width=True)

                max_row = sla.iloc[0]
                min_row = sla.iloc[-1]
                mean_sla = sla["sla_pct"].mean()
                gap_pp = float(max_row["sla_pct"] - min_row["sla_pct"])

                st.markdown("### Analysis")
                st.write(
                    f"""**What this graph is:** A **bar chart** showing **percentage of records meeting SLA** for each service.  
**X-axis:** Service name.  
**Y-axis:** SLA met (%).

**What it shows in your data:** Highest compliance is **{max_row['service_name']}** at **{max_row['sla_pct']:.1f}%**, lowest is **{min_row['service_name']}** at **{min_row['sla_pct']:.1f}%**. The spread between top and bottom is **{gap_pp:.1f} pp**; overall mean is **{mean_sla:.1f}%**.

**How to read it operationally:**  
- **Low bars:** Deep-dive handoffs, queues, routing; remove wait states.  
- **Leaders:** Document & replicate practices.  
- **Volatility:** Month-over-month stability matters; watch drift.  
- **Correlation:** Compare with incident and capacity signals.

**Why this matters:** SLA adherence drives trust and reduces penalties. Raising the floor toward top performers improves reliability and satisfaction."""
                )

                ev = (
                    f"Top **{max_row['service_name']}** {max_row['sla_pct']:.1f}% vs bottom "
                    f"**{min_row['service_name']}** {min_row['sla_pct']:.1f}%; mean **{mean_sla:.1f}%**; "
                    f"spread **{gap_pp:.1f} pp**."
                )
                low_gap = float(100.0 - min_row["sla_pct"])

                cio_sla = {
                    "cost": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence |
|---|---|---|---|---|
| Remove missing or ambiguous SLA data at intake | **Phase 1 – Enforce mandatory SLA fields:** Require service, priority, and response targets to be present and validated. <br><br>**Phase 2 – Auto-derive defaults:** Populate targets from the service catalogue when requesters omit details. <br><br>**Phase 3 – Add validation checks:** Block submission when fields are inconsistent or unknown and provide user guidance. | - Reduces rework and audit effort because tickets contain complete and accurate SLA information from the start.<br><br>- Improves reporting integrity which strengthens trust with stakeholders and customers.<br><br>- Lowers cycle time by avoiding back-and-forth to collect missing data.<br><br>- Creates a cleaner foundation for automation and routing rules. | Administrative minutes saved = number of missing or corrected entries × average lookup minutes measured before enforcement. | {ev} |
| Playbooks for low-SLA services | **Phase 1 – Build cause-to-action matrices:** Map common breach reasons to concrete corrective steps with ownership. <br><br>**Phase 2 – Train service owners:** Walk through scenarios and expected responses so execution is consistent. <br><br>**Phase 3 – Audit adherence:** Check that playbooks are used and update them with new learnings. | - Improves predictability for the weakest services by standardizing how they respond to risk situations.<br><br>- Raises the floor in SLA results which reduces overall volatility across the estate.<br><br>- Shortens time to fix recurrent issues because teams know what to do next.<br><br>- Boosts transparency when reviews show whether actions were followed. | Addressable gap for the worst service ≈ **{low_gap:.1f} pp** movement toward 100% when playbooks are applied effectively. | {ev} |
| Queue segmentation and skill-based routing | **Phase 1 – Split by complexity:** Separate simple, repeatable requests from complex, diagnostic work. <br><br>**Phase 2 – Route to skilled teams first time:** Use rules that send the ticket to the right resolver group on first assignment. <br><br>**Phase 3 – Monitor uplift:** Track reassignments and SLA outcomes to refine rules monthly. | - Reduces cycle time by eliminating unnecessary handoffs and wait states.<br><br>- Improves SLA attainment because work lands with the right people earlier in the process.<br><br>- Increases throughput and capacity utilization across the team.<br><br>- Enhances user experience with faster and more accurate resolutions. | Breaches avoided × penalty minutes using pre-segmentation breach rates as the baseline. | {ev} |
""",
                    "performance": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence |
|---|---|---|---|---|
| Real-time SLA wallboard | **Phase 1 – Surface near-breach items:** Show tickets approaching SLA thresholds with aging and owner. <br><br>**Phase 2 – Enable supervisor intervention:** Allow quick rebalancing and swarming with one click. <br><br>**Phase 3 – Weekly metrics review:** Track misses avoided and refine triggers. | - Enables earlier action which prevents avoidable breaches and keeps queues healthy.<br><br>- Improves flow stability across the day as leaders can nudge work proactively.<br><br>- Increases accountability and visibility for the whole team.<br><br>- Produces a repeatable rhythm that sustains performance. | Misses avoided compared to pre-wallboard baseline measured weekly. | {ev} |
| Aging SLO tiers | **Phase 1 – Escalate at clear thresholds:** Create time-based triggers for each priority that escalate before SLA breach. <br><br>**Phase 2 – Auto-page SMEs:** Bring the right expertise into the ticket at the exact moment it is needed. <br><br>**Phase 3 – Review top ten aged tickets weekly:** Remove systemic blockers and update thresholds. | - Collapses aging tails which directly reduces the number of breaches.<br><br>- Improves visibility of stuck work which accelerates progress and resolution quality.<br><br>- Protects high-priority items by guaranteeing timely attention.<br><br>- Builds discipline in queue management across teams. | Minutes saved on the aged cohort relative to the prior trend after introducing SLO tiers. | {ev} |
| After-action reviews for repeated misses | **Phase 1 – Weekly RCA on patterns:** Examine clusters of similar breaches to understand structural causes. <br><br>**Phase 2 – Close actions quickly:** Assign owners with due dates and track completion. <br><br>**Phase 3 – Monitor recurrence:** Ensure that the same breach reason declines over the next cycles. | - Converts insights into concrete improvements that persist beyond a single week.<br><br>- Reduces repetitive failure modes which increases compliance rate over time.<br><br>- Builds credibility with stakeholders through clear follow-through.<br><br>- Encourages a culture of continuous improvement rather than blame. | Reduction in repeat miss rate over subsequent cycles compared to the baseline period. | {ev} |
""",
                    "satisfaction": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence |
|---|---|---|---|---|
| Proactive breach communications | **Phase 1 – Notify on risk:** When a ticket approaches breach, inform the customer with current status and next actions. <br><br>**Phase 2 – Offer ETA and alternatives:** Provide realistic timing and any temporary workarounds. <br><br>**Phase 3 – Close the loop:** Confirm resolution and capture feedback to improve future handling. | - Lowers complaint volume because customers see ownership and progress before the timer expires.<br><br>- Preserves trust during stressful cases by setting and meeting expectations.<br><br>- Improves sentiment in post-resolution surveys which supports executive reporting.<br><br>- Reduces inbound chaser calls which frees analysts to complete the work. | Complaint volume drop during breach-risk weeks compared to prior weeks without proactive outreach. | {ev} |
| Publish SLA success stories | **Phase 1 – Share wins and improvements:** Highlight services that lifted SLA performance and how they achieved it. <br><br>**Phase 2 – Recognize teams:** Celebrate results to encourage adoption of effective practices. <br><br>**Phase 3 – Replicate playbooks:** Provide concise guides that others can follow. | - Increases morale and engagement which supports sustained performance gains.<br><br>- Accelerates spread of effective methods across the portfolio.<br><br>- Builds a positive reputation for the service desk with internal stakeholders.<br><br>- Makes improvement visible which helps justify further investment. | CSAT or NPS uplift correlated with the periods after success communication is embedded. | {ev} |
| Stakeholder SLA brief | **Phase 1 – Monthly graph plus actions:** Present clear visuals with the current month’s performance and planned remediations. <br><br>**Phase 2 – Capture decision points:** Ask for support on cross-team blockers and resource needs. <br><br>**Phase 3 – Follow-ups:** Report progress and adjust plans the next month. | - Reduces ad-hoc queries and escalations as stakeholders are kept in the loop on a predictable cadence.<br><br>- Aligns priorities across departments which removes friction and accelerates fixes.<br><br>- Improves accountability because commitments are reviewed regularly.<br><br>- Builds sustained confidence in the delivery organization. | Queries avoided after implementing the monthly brief cadence measured against the prior baseline. | {ev} |
"""
                }

                render_cio_tables("CIO — SLA Compliance by Service", cio_sla)
            else:
                st.info("No SLA compliance data to display.")

    # ============================================================
    # 7️⃣ Executive Summary Narrative
    # ============================================================
    with st.expander("📌 Executive Summary Overview", expanded=False):
        bullets = []
        if "uptime_percentage" in df.columns:
            bullets.append(
                "• **Availability** – Average uptime trend and peaks/lows highlight stability versus risk periods."
            )
        if "downtime_minutes" in df.columns:
            bullets.append(
                "• **Downtime** – Service and category breakdowns indicate where targeted fixes will materially reduce disruption."
            )
        if "incident_count" in df.columns:
            bullets.append(
                "• **Incidents** – Volume proxies operational load; cross-reference with root causes for structural improvements."
            )
        if "estimated_cost_downtime" in df.columns:
            bullets.append(
                "• **Financial Impact** – In-data cost estimates rank remediation by ROI."
            )
        if "recovery_time_minutes" in df.columns and "rto_target_minutes" in df.columns:
            bullets.append(
                "• **Recovery Performance** – MTTR vs RTO reveals which services breach response objectives."
            )
        if bullets:
            st.markdown("<br>".join(bullets), unsafe_allow_html=True)
        else:
            st.write(
                "Upload includes limited fields; add uptime, downtime, incident and cost columns to enrich this narrative."
            )
