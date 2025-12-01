# utils_capacity/recommendation_capacity/capacity_planning.py

import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# === Mesiniaga visual identity (blue & white) ===
px.defaults.template = "plotly_white"
PX_SEQ = ["#004C99", "#007ACC", "#3399FF", "#66B2FF", "#99CCFF"]

# 🔹 Helper to render CIO tables with 3 nested expanders
def render_cio_tables(title, cio_data):
    st.subheader(title)
    with st.expander("Cost Reduction"):
        st.markdown(cio_data["cost"], unsafe_allow_html=True)
    with st.expander("Performance Improvement"):
        st.markdown(cio_data["performance"], unsafe_allow_html=True)
    with st.expander("Customer Satisfaction Improvement"):
        st.markdown(cio_data["satisfaction"], unsafe_allow_html=True)

def _safe_mean(series):
    try:
        return float(pd.to_numeric(series, errors="coerce").dropna().mean())
    except Exception:
        return float("nan")

def _safe_min(series):
    try:
        return float(pd.to_numeric(series, errors="coerce").dropna().min())
    except Exception:
        return float("nan")

def _safe_max(series):
    try:
        return float(pd.to_numeric(series, errors="coerce").dropna().max())
    except Exception:
        return float("nan")

def _safe_sum(series):
    try:
        return float(pd.to_numeric(series, errors="coerce").fillna(0).sum())
    except Exception:
        return 0.0

def _fmt_cur(v):
    try:
        return f"${float(v):,.2f}"
    except Exception:
        return "N/A"

def _ratio(a, b):
    try:
        if float(b) == 0:
            return "0.00"
        return f"{float(a)/float(b):.2f}"
    except Exception:
        return "0.00"

def capacity_planning(df):

    # =========================
    # CPU Capacity Planning
    # =========================
    with st.expander("📌 CPU Capacity Planning"):
        if {"avg_cpu_utilization", "projected_growth_pct"} <= set(df.columns):
            df = df.copy()
            df["projected_cpu_utilization"] = (
                pd.to_numeric(df["avg_cpu_utilization"], errors="coerce")
                * (1 + pd.to_numeric(df["projected_growth_pct"], errors="coerce") / 100.0)
            ).clip(upper=100)

            # Graph 1: Scatter current vs projected CPU
            fig_cpu_proj = px.scatter(
                df,
                x="avg_cpu_utilization",
                y="projected_cpu_utilization",
                title="Projected CPU Utilization (Next 12 Months)",
                labels={
                    "avg_cpu_utilization": "Current CPU (%)",
                    "projected_cpu_utilization": "Projected CPU (%)"
                },
                color_discrete_sequence=PX_SEQ
            )
            st.plotly_chart(fig_cpu_proj, use_container_width=True, key="capplan_cpu_proj")

            risk_assets = df[df["projected_cpu_utilization"] >= 85]
            avg_now = _safe_mean(df["avg_cpu_utilization"])
            avg_proj = _safe_mean(df["projected_cpu_utilization"])
            max_now = _safe_max(df["avg_cpu_utilization"])
            max_proj = _safe_max(df["projected_cpu_utilization"])

            st.write(f"""
What this graph is: A scatter plot comparing current CPU utilization against projected CPU utilization 12 months ahead.

X-axis: Current CPU utilization (%).
Y-axis: Projected CPU utilization (%).

What it shows in your data: Average current CPU utilization is {avg_now:.2f}% while the average projected CPU utilization is {avg_proj:.2f}% based on your growth inputs.
Highest current utilization point reaches {max_now:.2f}% and the highest projected utilization point reaches {max_proj:.2f}% when growth is applied.
The high-risk cohort contains {len(risk_assets)} assets with projected CPU utilization at or above 85%, which are the nodes most likely to hit saturation first if no action is taken.

Overall: Points that sit well above the 45° reference line (y = x) indicate that demand is growing faster than available CPU capacity for those assets.
Points on or below the line indicate either a stable capacity posture or recovering headroom as workloads are optimized, shifted or reduced.

How to read it operationally:

Peaks: Focus first on assets in the upper-right area because they combine high current load and high projected load and therefore require rebalancing, upgrades or workload movement before peak periods.
Headroom targeting: Aim to keep most projected points below roughly 80–85% so there is enough buffer for bursts, deployments and unplanned events without immediately triggering saturation.
Rightsizing: Look for points where projected utilization is relatively low but current utilization is higher because these often represent over-provisioned or cooling workloads that can be consolidated or down-tiered safely.
Roadmap alignment: Overlay component type or business criticality on this view so that growth on core services is prioritised and sequenced clearly in the capacity roadmap.

Why this matters: CPU saturation directly drives latency, timeouts and SLA breaches, so deliberately steering projected utilization away from the risk band protects cost, performance and overall customer experience at the same time.
""")

            # Graph 2: CPU Growth by Component Type
            if "component_type" in df.columns:
                df["cpu_growth_delta"] = df["projected_cpu_utilization"] - pd.to_numeric(df["avg_cpu_utilization"], errors="coerce")
                growth_by_type = df.groupby("component_type", as_index=False)["cpu_growth_delta"].mean()
                fig_cpu_bar = px.bar(
                    growth_by_type,
                    x="component_type",
                    y="cpu_growth_delta",
                    title="Average CPU Growth by Component Type (pp)",
                    color_discrete_sequence=PX_SEQ
                )
                st.plotly_chart(fig_cpu_bar, use_container_width=True, key="capplan_cpu_bar")

                top = growth_by_type.loc[growth_by_type["cpu_growth_delta"].idxmax()]
                low = growth_by_type.loc[growth_by_type["cpu_growth_delta"].idxmin()]
                mean_delta = _safe_mean(growth_by_type["cpu_growth_delta"])

                st.write(f"""
What this graph is: A bar chart showing average projected CPU growth, in percentage points, by component type.

X-axis: Component type.
Y-axis: Growth delta, calculated as projected CPU utilization minus current CPU utilization in percentage points.

What it shows in your data: {top['component_type']} is the fastest-growing type with an average projected CPU growth of {top['cpu_growth_delta']:.2f} percentage points.
{low['component_type']} is the slowest or even declining type with a growth delta of {low['cpu_growth_delta']:.2f} percentage points.
Across the entire portfolio the average CPU growth delta is {mean_delta:.2f} percentage points, so types that sit far above this average are tightening capacity faster than the rest of the estate.

Overall: Taller bars highlight the component families where CPU pressure will emerge first if no action is taken to add capacity or optimise workloads.
Shorter or negative bars show areas where there is latent CPU capacity that can be reclaimed or reused without increasing operational risk.

How to read it operationally:

Peaks: Stage upgrades, auto-scaling policies and performance tuning for {top['component_type']} and any other fast-growing types before quarter-end so that growth does not turn into incidents.
Plateaus: For mid-range types around the portfolio average, keep sizing templates and guardrails in place and monitor whether their growth trends drift upward over time.
Downswings: Treat {low['component_type']} and other low or negative growth types as consolidation pools where hosts can be retired, workloads can be packed more tightly and licenses can be reduced.
Mix: Use the bar heights as a visual input into the capacity roadmap so that both capital and operating expenditure follow the technical risk instead of being spread evenly.

Why this matters: Targeting capacity investments on the fastest-growing families keeps spend efficient and reduces the chance of last-minute emergency work during peak cycles when business demand is highest.
""")

            # CIO Recommendations for CPU Capacity (≥3, phased, with real figures)
            cpu_savings = _safe_sum(df.get("potential_savings_usd", 0))
            cpu_cost = _safe_sum(df.get("cost_per_month_usd", 0))
            cio_cpu = {
                "cost": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Rebalance workloads from forecasted high-utilization nodes | **Phase 1 – Detect:** List assets with projected CPU ≥85% by using the projected_cpu_utilization field and group them into a clear high-risk cohort in the dashboard so that capacity owners can see where saturation is likely to occur first. Make sure the business and technical stakeholders review this list together and validate that the projected growth assumptions are realistic for the next 12 months. <br><br>**Phase 2 – Shift:** Move noisy neighbours and heavy workloads away from these high-risk nodes into hosts that are running at or below {avg_now:.2f}% current CPU utilisation so that load is spread more evenly across the estate. Document which workloads have been shifted and confirm that critical services retain enough headroom on their primary nodes. <br><br>**Phase 3 – Verify:** Monitor post-move CPU utilisation for at least two consecutive weeks and confirm that the previously high-risk nodes now operate consistently below 85% under normal and peak conditions. Capture before and after snapshots so that the impact of the rebalancing can be demonstrated during operational and financial reviews. | - Avoids premium emergency purchases by reducing surprise capacity shortages that would otherwise force last minute hardware or cloud orders at higher prices.<br><br>- Reduces incident triggered overtime because engineers spend less time firefighting CPU saturation issues and more time executing planned and predictable work.<br><br>- Lowers energy used per transaction by concentrating workloads on appropriately sized and better utilised servers instead of running many underused machines that still consume power and cooling.<br><br> | Savings Ratio = Σ(potential_savings_usd) / Σ(cost_per_month_usd) = {_fmt_cur(cpu_savings)} / {_fmt_cur(cpu_cost)} = **{_ratio(cpu_savings, cpu_cost)}x**. | Scatter shows **{len(risk_assets)}** assets in the ≥85% projected risk band; maxima reach **{max_proj:.2f}%**. |
| Consolidate low-growth workloads | **Phase 1 – Identify:** Use the CPU growth delta metric to highlight assets with a growth delta of less than 10 percentage points so that you can see which servers are essentially stable or cooling in demand. Share this list with platform and application owners so that they can confirm which workloads are suitable for consolidation. <br><br>**Phase 2 – Pack:** Gradually co-host compatible workloads on a smaller number of servers until projected CPU utilisation sits in the 60–75% comfort band where there is healthy headroom but minimal waste. Ensure that resilience and failover requirements are still respected while you increase utilisation on the remaining hosts. <br><br>**Phase 3 – Retire:** Decommission the freed hosts, reclaim their licences and remove them from patching, monitoring and support processes so that they no longer consume operational effort or data centre resources. Track the reduction in server count and use it as evidence of consolidation progress. | - Cuts ongoing run rate costs because fewer physical or virtual hosts need power, cooling, rack space and support contracts after consolidation is completed.<br><br>- Reduces the number of idle or lightly used cores that operations teams must patch, monitor and troubleshoot which simplifies day to day management of the environment.<br><br>- Creates a cleaner and more standardised fleet where capacity is concentrated in fewer, better utilised platforms that are easier to forecast and optimise over time.<br><br> | Monthly Cost Avoided ≈ (hosts removed × avg host cost). Scope guided by bars ≤10 pp in growth chart; portfolio mean = {mean_delta if 'mean_delta' in locals() else 0:.2f} pp. | Bar chart shows slowest growth: **{low['component_type'] if 'low' in locals() else '—'}** at **{low['cpu_growth_delta']:.2f} pp**. |
| Predictive scaling instead of static provisioning | **Phase 1 – Model:** Use historical utilisation and projected_growth_pct to build 12 month projection curves for each component type and major service so that you can see when nodes are likely to cross critical thresholds. Validate the model with business growth plans and known projects so the projections are tied to real initiatives. <br><br>**Phase 2 – Automate:** Configure scaling rules or procurement triggers that start when projected utilisation approaches 80% rather than waiting for actual saturation events so that capacity is added calmly and on schedule. Integrate these triggers with change and budgeting processes so that approvals and funding are lined up in advance. <br><br>**Phase 3 – Tune:** Review the accuracy of the projections and scaling thresholds every quarter and adjust parameters where utilisation patterns have changed or new applications have been introduced so that the model stays relevant. Share updated views with finance and operations so everyone understands upcoming capacity moves. | - Reduces stranded capacity by preventing large amounts of unused CPU from being purchased and left idle because scaling decisions follow measured growth rather than guesswork.<br><br>- Lowers the risk of sudden performance degradation by making sure additional capacity is provisioned before users experience slowdowns or errors in production.<br><br>- Supports smoother financial planning because capacity investments are spread over time and linked to data driven triggers instead of irregular emergency purchases.<br><br> | Avoided Over-Provision ≈ (Σ overshoot pp × cost per core). Overshoot visible where projected >> current (points well above y=x). | Scatter max gap current→projected reaches **{(max_proj - max_now):.2f} pp** among top assets. |
""",
                "performance": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Stress-test assets near saturation | **Phase 1 – Select:** Use the scatter plot and thresholds to select assets whose projected CPU utilisation sits between 80% and 90% so that you have a clear list of servers approaching risk. Confirm with application teams which of these hosts support critical workloads or peak-period services. <br><br>**Phase 2 – Simulate:** Run structured stress tests or load simulations against those assets that mimic peak demand so that you can observe tail latency, error rates and behaviour under pressure before real users are affected. Capture performance metrics during these tests and store them as part of the capacity record. <br><br>**Phase 3 – Reinforce:** Apply actions such as workload rebalancing, capacity increases or configuration tuning for assets that show poor resilience and then repeat targeted tests to confirm that saturation risk has reduced ahead of the next peak month. Document improvements in a simple before and after summary. | - Reduces the chance of CPU driven performance incidents by detecting fragility early while there is still time to fix configuration and capacity issues in a controlled way.<br><br>- Improves the reliability of critical workloads during peak periods because weak hosts are strengthened or offloaded before heavy user traffic arrives.<br><br>- Provides hard evidence on how systems behave under stress which can be used to refine both capacity models and operational runbooks over time.<br><br> | Downtime Avoided × Revenue/hr; cohort size = **{len(risk_assets)}** high-risk assets. | Scatter pinpoints the ≥85% band and overall projected average **{avg_proj:.2f}%**. |
| Dynamic workload orchestration | **Phase 1 – Enable:** Deploy or configure an orchestration platform that can see CPU utilisation across nodes and enforce target utilisation bands per component type so that workloads can be moved intelligently. Ensure that policies are aligned with resilience and compliance requirements before enabling automated placement. <br><br>**Phase 2 – Balance:** Use the orchestrator to redistribute workloads so that most nodes run around 70–80% utilisation during normal peaks rather than having some servers idle while others are saturated. Monitor the effect on overall performance and adjust allowable ranges where needed. <br><br>**Phase 3 – Measure:** Track key metrics such as p95 latency, error rates and saturation events over several cycles to verify that dynamic orchestration is delivering more stable performance than static allocations. Feed lessons from this measurement back into placement policies. | - Flattens CPU hotspots by moving work from overloaded nodes to cooler ones which leads to more predictable performance under changing business demand.<br><br>- Improves overall throughput because available CPU across the cluster is used more evenly instead of leaving pockets of unused capacity stranded on lightly loaded servers.<br><br>- Reduces operational effort during peak events because the orchestrator reacts continuously within defined policies instead of relying solely on manual interventions from engineers.<br><br> | Time Saved = (latency reduction × request volume) on fast-growth types (**{top['component_type'] if 'top' in locals() else '—'}**). | Growth bars highlight where orchestration pays off most (**{top['cpu_growth_delta']:.2f} pp**). |
| Trend-based CPU budgeting | **Phase 1 – Track:** Maintain quarterly time series of current and projected CPU utilisation by component type so that you can see how the portfolio is evolving rather than relying on isolated snapshots. Store these trends in a shared capacity dashboard that finance and operations can access. <br><br>**Phase 2 – Align:** Build budget proposals that link requested spend to the observed growth deltas by type so that each funding item is backed by measurable demand data. Use the portfolio mean delta as a reference when challenging or defending budget lines. <br><br>**Phase 3 – Adjust:** Review actual utilisation mid-year and compare it with earlier projections so that you can either release unused budget or request additional funding in a structured way where growth has exceeded expectations. Document these adjustments for future planning cycles. | - Increases the quality of budget discussions because funding requests are grounded in visible utilisation trends rather than rough estimates or historical habits.<br><br>- Reduces the risk of underfunding critical growth areas and overfunding stable or shrinking components by redirecting money to where CPU pressure genuinely exists.<br><br>- Helps avoid last minute re-forecasts and emergency funding exercises because deviations from plan are caught earlier through regular trend reviews.<br><br> | Budget Variance ÷ total CPU-hours; guided by portfolio mean delta **{mean_delta if 'mean_delta' in locals() else 0:.2f} pp**. | Type chart distributes growth risk explicitly by family. |
""",
                "satisfaction": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Communicate capacity readiness | **Phase 1 – Summarise:** Turn CPU projection views into simple business facing summaries that show where capacity is already safe and where risk is rising so stakeholders can understand the story without technical detail. Highlight the services and component types that are being watched closely. <br><br>**Phase 2 – Commit:** Translate the technical remediation and upgrade plans into clear delivery dates and milestones so that business owners know when high-risk areas will be addressed. Ensure those commitments are realistic based on procurement and change windows. <br><br>**Phase 3 – Report:** After actions are delivered, show updated CPU and SLO metrics that demonstrate improved resilience and use them in regular service review meetings to reinforce confidence in the platform. Archive old and new charts as evidence of progress. | - Reduces escalation volume because stakeholders already know which capacity risks are being worked on and when improvements will land so they do not need to chase for updates.<br><br>- Increases confidence in IT and operations teams by showing that growth and capacity are being managed proactively with a clear plan rather than reactively after incidents occur.<br><br>- Helps business units plan campaigns and projects with more certainty because they can see that the underlying infrastructure is being scaled deliberately to match demand.<br><br> | Complaints avoided × handling minutes; target the **{len(risk_assets)}**-asset risk cohort. | Scatter & bars show who’s at risk, by how much ({max_proj:.2f}% peak). |
| Prioritise upgrades for critical services | **Phase 1 – Map:** Link critical applications and business processes to the infrastructure assets that host them and check which of those nodes are projected to run at or above 85% CPU so that you can see where business risk concentrates. Confirm mappings with application owners to avoid gaps. <br><br>**Phase 2 – Upgrade:** Plan and execute CPU related upgrades, workload moves or architecture changes for these critical paths ahead of major business events so that there is guaranteed headroom during important periods. Coordinate dates with stakeholders and change governance. <br><br>**Phase 3 – Validate:** After upgrades, monitor SLOs, incident rates and customer feedback to ensure that performance of critical services has improved and that the new headroom is sufficient under real traffic. Capture lessons for use in future upgrade waves. | - Protects high value customer journeys and revenue generating processes from avoidable slowdowns caused by CPU saturation on key infrastructure components.<br><br>- Reduces the likelihood of SLA penalties and reputational damage associated with poor performance on flagship services that executives and customers notice most.<br><br>- Improves the perceived reliability of the platform because critical services continue to behave well even when overall demand grows or spikes unexpectedly.<br><br> | SLA penalties avoided × incident probability reduction. | Upper-right scatter cluster links to critical services when mapped. |
| Maintenance in low-load windows | **Phase 1 – Detect:** Use projected utilisation patterns to identify time windows where CPU load is expected to be well below normal peaks so that maintenance can be performed with minimal user impact. Confirm these windows with business teams for key services. <br><br>**Phase 2 – Schedule:** Place patching, reboots and capacity changes into those low load windows and document the schedule clearly so that operations, vendors and business stakeholders know what to expect. Build simple checklists for pre and post change validation. <br><br>**Phase 3 – Review:** After each maintenance cycle, review incident and performance data to confirm that the schedule is working and adjust windows if the business or traffic patterns change over time. Record improvements in a change calendar or service review pack. | - Minimises disruption felt by end users because most heavy maintenance takes place during periods when CPU utilisation and business activity are naturally low.<br><br>- Reduces the number of change day complaints and escalations since users are informed early about timing and experience fewer surprises during working hours.<br><br>- Improves the quality and predictability of maintenance work by giving engineers more headroom and time to validate changes when systems are under less stress.<br><br> | Δ Incidents during maintenance windows vs baseline. | Projection distribution indicates safest windows (points furthest below 70%). |
"""
            }
            render_cio_tables("CPU Capacity Planning — CIO Recommendations", cio_cpu)

            render_cio_tables("CPU Capacity Planning — CIO Recommendations", cio_cpu)

    # =========================
    # Memory Capacity Planning
    # =========================
    with st.expander("📌 Memory Capacity Planning"):
        if {"avg_memory_utilization", "projected_growth_pct"} <= set(df.columns):
            df = df.copy()
            df["projected_memory_utilization"] = (
                pd.to_numeric(df["avg_memory_utilization"], errors="coerce")
                * (1 + pd.to_numeric(df["projected_growth_pct"], errors="coerce") / 100.0)
            ).clip(upper=100)

            # Graph 1: Scatter current vs projected Memory
            fig_mem_proj = px.scatter(
                df,
                x="avg_memory_utilization",
                y="projected_memory_utilization",
                title="Projected Memory Utilization (Next 12 Months)",
                labels={
                    "avg_memory_utilization": "Current Memory (%)",
                    "projected_memory_utilization": "Projected Memory (%)"
                },
                color_discrete_sequence=PX_SEQ
            )
            st.plotly_chart(fig_mem_proj, use_container_width=True, key="capplan_mem_proj")

            high_assets = df[df["projected_memory_utilization"] >= 85]
            avg_now_m = _safe_mean(df["avg_memory_utilization"])
            avg_proj_m = _safe_mean(df["projected_memory_utilization"])
            max_now_m = _safe_max(df["avg_memory_utilization"])
            max_proj_m = _safe_max(df["projected_memory_utilization"])

            st.write(f"""
What this graph is: A scatter plot comparing current Memory utilization against projected Memory utilization 12 months ahead.

X-axis: Current Memory utilization (%).
Y-axis: Projected Memory utilization (%).

What it shows in your data: Average current Memory utilization is {avg_now_m:.2f}% and the average projected Memory utilization is {avg_proj_m:.2f}% once the growth assumptions are applied.
The highest current Memory utilization reaches {max_now_m:.2f}% and the highest projected Memory utilization reaches {max_proj_m:.2f}%.
The high-risk cohort contains {len(high_assets)} assets with projected Memory utilization at or above 85%, which are the systems most likely to experience pressure or saturation first.

Overall: Points that rise above the y = x reference line show where Memory demand is tightening faster than capacity, reducing available headroom over time.
Points that sit near or under the line indicate components where Memory posture is more stable or where optimisation work is already keeping growth in check.

How to read it operationally:

Peaks: Treat upper-right points as RAM pressure hotspots that need upgrades, workload shifts or configuration tuning before peak business periods.
Cache and garbage-collection hygiene: For mid-band risers, prioritise tuning cache sizes, GC settings and Memory leaks so that growth is reduced before committing to physical RAM purchases.
Rightsizing: Low-right points, where future utilization is low relative to today, indicate over-provisioned instances that can be down-tiered or consolidated without hurting performance.
Criticality lens: Map critical business services to the assets projected at or above 85% to make sure those are addressed first in capacity plans.

Why this matters: Memory saturation translates directly into pauses, crashes and timeouts from the user’s point of view, so holding a healthy headroom band protects cost, system stability and customer satisfaction together.
""")

            # Graph 2: Memory Growth by Component Type
            if "component_type" in df.columns:
                df["mem_growth_delta"] = df["projected_memory_utilization"] - pd.to_numeric(df["avg_memory_utilization"], errors="coerce")
                growth_by_type_m = df.groupby("component_type", as_index=False)["mem_growth_delta"].mean()
                fig_mem_bar = px.bar(
                    growth_by_type_m,
                    x="component_type",
                    y="mem_growth_delta",
                    title="Average Memory Growth by Component Type (pp)",
                    color_discrete_sequence=PX_SEQ
                )
                st.plotly_chart(fig_mem_bar, use_container_width=True, key="capplan_mem_bar")

                top_m = growth_by_type_m.loc[growth_by_type_m["mem_growth_delta"].idxmax()]
                low_m = growth_by_type_m.loc[growth_by_type_m["mem_growth_delta"].idxmin()]
                mean_delta_m = _safe_mean(growth_by_type_m["mem_growth_delta"])

                st.write(f"""
What this graph is: A bar chart showing average projected Memory growth, in percentage points, by component type.

X-axis: Component type.
Y-axis: Growth delta, calculated as projected Memory utilization minus current Memory utilization in percentage points.

What it shows in your data: {top_m['component_type']} is the fastest-growing type with an average projected Memory growth of {top_m['mem_growth_delta']:.2f} percentage points.
{low_m['component_type']} is the slowest or declining type with a growth delta of {low_m['mem_growth_delta']:.2f} percentage points.
The portfolio average Memory growth delta is {mean_delta_m:.2f} percentage points, so bars that sit well above this average indicate families where Memory contention will appear first.

Overall: Larger bars flag the component types where Memory demand is accelerating and will create pressure if capacity is not added or workloads are optimised.
Shorter or negative bars point to types where Memory demand is flat or shrinking and where consolidation or downsizing can safely create room for other services.

How to read it operationally:

RAM first-aid: Pre-stage Memory upgrades and tuning work for {top_m['component_type']} and similar high-growth types so they do not become sources of recurring incidents.
Policy alignment: Use the portfolio average of {mean_delta_m:.2f} percentage points as a reference and keep types near that level under 80–85% projected utilization through guardrails and regular forecasting.
Consolidate: Treat {low_m['component_type']} and other low or negative growth families as candidates for consolidation, where excess Memory can be reclaimed or reallocated.
Budget linkage: Tie RAM capex and supporting opex directly to these bar heights so that spend follows technical growth signals instead of being spread evenly across all types.

Why this matters: Focusing on the fastest Memory risers prevents SLA pain on noisy, user-facing systems and avoids last-minute spending when capacity constraints finally become visible in production.
""")

            # CIO Recommendations for Memory Capacity (≥3, phased, with real figures)
            mem_savings = _safe_sum(df.get("potential_savings_usd", 0))
            mem_cost = _safe_sum(df.get("cost_per_month_usd", 0))
            cio_mem = {
                "cost": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Consolidate underused memory nodes | **Phase 1 – Detect:** Use projected_memory_utilization to find assets that are expected to remain below 60% Memory utilisation so that you can clearly see which nodes are underused. Confirm with application teams that these nodes are not reserved for special cases that require extra headroom. <br><br>**Phase 2 – Co-host:** Gradually move compatible workloads onto a smaller set of servers and raise projected utilisation on those remaining nodes into the 70–80% band where Memory is well used but still safe. Validate that redundancy and failover paths remain in place as you consolidate. <br><br>**Phase 3 – Retire:** Decommission surplus nodes and free their operating system licences, database licences and support contracts so that they stop consuming budget and operational effort. Update CMDB and monitoring tools to reflect the smaller, more efficient footprint. | - Cuts ongoing costs for power, cooling and rack space because fewer physical or virtual machines are required to deliver the same amount of compute and Memory capacity.<br><br>- Reduces the number of servers that engineers must patch, monitor and troubleshoot which simplifies operations and reduces the chance of configuration drift on rarely used hosts.<br><br>- Increases the effective utilisation of Memory across the environment by ensuring that capacity is concentrated on a leaner set of nodes that are easier to size and manage.<br><br> | Savings Ratio = Σ(potential_savings_usd) / Σ(cost_per_month_usd) = {_fmt_cur(mem_savings)} / {_fmt_cur(mem_cost)} = **{_ratio(mem_savings, mem_cost)}x**. | Scatter shows low-right points suitable for consolidation; highest projected point is **{max_proj_m:.2f}%** with **{len(high_assets)}** at-risk assets. |
| Purchase memory upgrades strategically | **Phase 1 – Stage:** Identify nodes with projected Memory utilisation at or above 85% and plan upgrade orders for those assets based on vendor lead times so that RAM is available before real saturation. Confirm sizing with workload owners to avoid under or over buying. <br><br>**Phase 2 – Sequence:** Prioritise upgrades for nodes that host critical or user-facing services so that risk is removed first from the most visible systems. Align sequencing with maintenance windows and change advisory board approvals. <br><br>**Phase 3 – Validate:** After upgrades, monitor swap usage, page faults and p95 latency to confirm that Memory pressure and incident rates have decreased and record improvements as part of the business case for future upgrades. Share results with stakeholders. | - Avoids emergency last minute Memory purchases that often come with premium pricing or suboptimal configurations because capacity is bought according to a deliberate plan.<br><br>- Stabilises performance on user-facing and critical services by removing known Memory bottlenecks before they cause visible slowdowns or crashes for customers and staff.<br><br>- Provides clear evidence that planned upgrades deliver measurable improvements which builds trust with finance teams when new capacity investments are requested in the future.<br><br> | Upgrade Avoidance ≈ (emergency premium − planned price) × units; target cohort size = **{len(high_assets)}**. | Scatter upper-right density quantifies need; projected average **{avg_proj_m:.2f}%**. |
| Automate memory scaling | **Phase 1 – Policies:** Define autoscaling or elasticity policies that react when sustained Memory utilisation stays above 80% so that additional capacity can be added before applications become unstable. Make sure guardrails and quotas are in place to avoid runaway growth. <br><br>**Phase 2 – Tune:** Review how often these policies trigger and whether they are adding the right amount of Memory at the right time and refine thresholds every quarter based on observed patterns. Coordinate changes with cost management to keep spending under control. <br><br>**Phase 3 – Guardrails:** Implement upper limits and safety checks that prevent oscillation or over scaling and ensure that any manual overrides are logged and reviewed so that scaling behaviour stays predictable. Document these controls for audit and governance. | - Reduces the risk of Memory related outages by expanding capacity automatically when sustained load indicates that systems are under pressure rather than waiting for crashes or swap storms.<br><br>- Provides a better balance between cost and performance because Memory is added when there is a genuine need and can be scaled back when demand falls according to policy.<br><br>- Gives operations teams more confidence in handling unpredictable workloads since scaling rules provide a controlled safety net instead of ad hoc manual responses in production.<br><br> | Cost Avoided ≈ hours at high swap × cost/hr incidents. | Growth bars identify families where scaling triggers will fire (top type **{top_m['component_type'] if 'top_m' in locals() else '—'}**, {top_m['mem_growth_delta']:.2f} pp). |
""",
                "performance": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Stress-test high-risk workloads | **Phase 1 – Select:** Use the scatter plot and thresholds to pick workloads running on nodes projected between 80% and 90% Memory so that you have a clear list of systems close to saturation. Confirm with product and application owners which of these workloads are business critical. <br><br>**Phase 2 – Simulate:** Run load and failover tests that exercise Memory allocation patterns, garbage collection and cache behaviour at peak levels so that hidden issues such as leaks and fragmentation are exposed before production incidents occur. Capture metrics such as throughput, latency and error counts during these tests. <br><br>**Phase 3 – Fix:** Use findings from the tests to tune configurations, optimise code or upgrade hardware and then repeat targeted tests to verify that Memory headroom and performance have improved ahead of major events. Summarise the changes and their impact for stakeholders. | - Reduces the chance of Memory related outages and performance incidents by uncovering weaknesses in a controlled environment instead of discovering them during real customer traffic.<br><br>- Improves the resilience of critical workloads because the most exposed systems receive focused tuning and capacity work before the next seasonal or project driven peak.<br><br>- Builds a library of performance baselines and test results that can be reused in future releases which speeds up regression testing and capacity certification.<br><br> | Downtime Avoided × Revenue/hr; high-risk cohort size = **{len(high_assets)}**. | Scatter isolates the ≥85% cluster and max **{max_proj_m:.2f}%**. |
| Dynamic workload allocation | **Phase 1 – Enable:** Configure orchestration or scheduling tools to take Memory utilisation and workload characteristics into account when placing or moving tasks so that heavy consumers are not concentrated on the same node. Ensure resilience and compliance rules are respected by the placement logic. <br><br>**Phase 2 – Balance:** Use these tools to keep most nodes below 85% projected Memory utilisation by moving jobs away from hot spots during busy periods and consolidating during quiet times. Monitor memory related alerts to see whether hotspot frequency is dropping. <br><br>**Phase 3 – Measure:** Track improvements in p95 and p99 latency, swap utilisation and error rates over multiple cycles to confirm that dynamic allocation is delivering a more stable service. Feed the metrics back into policy tuning. | - Increases overall stability because Memory intensive workloads are spread more evenly across infrastructure instead of overloading a few nodes while others sit largely idle.<br><br>- Enhances user experience by reducing pauses, stalls and timeouts that typically occur when Memory hot spots drive heavy swapping or garbage collection overhead on specific servers.<br><br>- Gives operations teams more flexibility to respond to unexpected demand spikes since workloads can be shifted automatically in response to resource pressure rather than only via manual changes.<br><br> | Δ Latency × request volume on fast-growth types. | Bar chart: fastest riser **{top_m['component_type'] if 'top_m' in locals() else '—'}** at **{top_m['mem_growth_delta']:.2f} pp**. |
| Predictive saturation alerting | **Phase 1 – Forecast:** Use historical and projected Memory data to estimate how many days or weeks of headroom each node has before it reaches defined thresholds so that you understand time to risk for each asset. Store these lead time estimates in a simple view. <br><br>**Phase 2 – Alert:** Configure alerts that trigger when remaining headroom days fall below agreed limits at 80%, 85% and 90% utilisation so that teams can act before formal SLA breaches or major incidents occur. Ensure on call staff understand how to respond to these alerts. <br><br>**Phase 3 – Act:** Link alerts to clear runbooks and predefined actions such as scaling, rebalancing or optimisation and review how many potential breaches were prevented through early intervention so that the process can be refined. | - Reduces surprise Memory saturation events because teams are warned when systems are on track to reach dangerous levels well before they actually hit the limit.<br><br>- Improves mean time to resolve capacity related issues since responders already know which actions to take from linked runbooks when predictive alerts fire.<br><br>- Provides a clear connection between capacity analytics and real operational activity which helps justify continued investment in monitoring and forecasting capabilities.<br><br> | SLA penalty avoided × incident count reduction. | Distribution of projections shows how many nodes cross each threshold (≥85% = **{len(high_assets)}**). |
""",
                "satisfaction": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Communicate upcoming upgrades | **Phase 1 – Announce:** Share a forward view of Memory upgrade windows, affected services and expected benefits with business stakeholders so that they know what work is planned and when. Use simple language to describe why the upgrades are necessary. <br><br>**Phase 2 – Dashboards:** Provide easy to read dashboards that show before and after Memory utilisation and key service metrics so users can see progress at a glance once work is completed. Make sure these views are accessible to both IT and business teams. <br><br>**Phase 3 – Feedback:** Collect feedback from users after upgrades to understand whether they have noticed improvements in speed or stability and use this feedback to fine tune future upgrade plans and communications. | - Reduces user anxiety and speculation because people know that performance risks are being addressed proactively and they understand when maintenance will take place.<br><br>- Decreases the volume of duplicate tickets and status queries since stakeholders can see upgrade progress in dashboards rather than having to ask support teams for updates.<br><br>- Strengthens trust between IT and business units by showing that user experience is being monitored and directly linked to capacity improvement work.<br><br> | Complaint deflection × minutes per ticket; target peak days near **{max_proj_m:.2f}%**. | Scatter & bars document why, where, and when upgrades occur. |
| Prioritise critical apps | **Phase 1 – Map:** Work with business owners to identify which applications and services are critical and map them to the underlying nodes and component types that host them so that you can see where Memory risk intersects with business priority. Validate mappings periodically. <br><br>**Phase 2 – Safeguard:** Reserve additional headroom or apply stricter scaling and monitoring rules for nodes that support these critical paths so that they are less likely to experience Memory saturation during peak demand. Coordinate this with broader capacity plans. <br><br>**Phase 3 – Observe:** Track SLOs, incident trends and satisfaction scores for these critical applications over time to confirm that the safeguards are having the desired effect and adjust strategies where gaps remain. | - Protects the user journeys and business processes that matter most so customers and key internal teams see fewer slowdowns or errors during their important tasks.<br><br>- Helps account managers and product owners demonstrate to stakeholders that their critical services are being given special attention in capacity plans and operational monitoring.<br><br>- Improves overall perception of service quality because users experience consistent performance on the systems that they rely on most heavily in day to day work.<br><br> | Retention value proxy × SLO uplift on critical flows. | Upper-right points align with criticality when mapped. |
| Align maintenance with low-growth families | **Phase 1 – Pick:** Use the Memory growth by component type chart to select families with negative or low deltas as preferred candidates for maintenance windows so that higher risk types are kept free for business load. Confirm that these families do not host peak time critical applications. <br><br>**Phase 2 – Execute:** Schedule reboots, patching and configuration changes for these low-growth types during suitable off-peak periods and communicate the plan clearly to affected stakeholders so they can prepare. Maintain a simple calendar of these windows. <br><br>**Phase 3 – Review:** After maintenance, analyse incident rates and user feedback to make sure that the chosen families and timings are delivering low impact outcomes and refine the selection if new patterns appear. | - Minimises user visible disruption because the bulk of disruptive maintenance happens on components with stable or low growth where business usage is easier to work around.<br><br>- Simplifies communication with stakeholders since maintenance narratives can focus on lower risk systems while assuring them that high growth, high impact components remain available during key periods.<br><br>- Provides a repeatable pattern for planners who can use growth charts to select maintenance candidates logically rather than relying purely on intuition or habit.<br><br> | Δ incidents during maintenance vs baseline. | Bar chart shows safest families (e.g., **{low_m['component_type'] if 'low_m' in locals() else '—'}**, {low_m['mem_growth_delta']:.2f} pp). |
"""
            }
            render_cio_tables("Memory Capacity Planning — CIO Recommendations", cio_mem)

            render_cio_tables("Memory Capacity Planning — CIO Recommendations", cio_mem)

    # (Storage and Network capacity planning can follow the same pattern if added)
