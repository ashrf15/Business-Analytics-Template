# utils_capacity/recommendation_capacity/resource_efficiency.py

import streamlit as st
import plotly.express as px
import pandas as pd

# --- Visual identity: professional blue & white ---
px.defaults.template = "plotly_white"
PX_SEQ = ["#004C99", "#007ACC", "#3399FF", "#66B2FF", "#99CCFF"]
px.defaults.color_discrete_sequence = PX_SEQ  # apply globally

# 🔹 Helper to render CIO tables with 3 nested expanders
def render_cio_tables(title, cio_data):
    st.subheader(title)
    with st.expander("Cost Reduction"):
        st.markdown(cio_data["cost"], unsafe_allow_html=True)
    with st.expander("Performance Improvement"):
        st.markdown(cio_data["performance"], unsafe_allow_html=True)
    with st.expander("Customer Satisfaction Improvement"):
        st.markdown(cio_data["satisfaction"], unsafe_allow_html=True)

def resource_efficiency(df):
    # ======================
    # 1️⃣ Underutilized Assets
    # ======================
    with st.expander("📌 Underutilized Assets"):
        if "avg_cpu_utilization" in df.columns:
            low_util = df[pd.to_numeric(df["avg_cpu_utilization"], errors="coerce") < 30]

            # Graph 1: Bar chart for underutilized assets
            fig_bar = px.bar(
                low_util,
                x="asset_id",
                y="avg_cpu_utilization",
                title="Underutilized Assets (<30% CPU Utilization)",
                labels={"avg_cpu_utilization": "CPU Utilization (%)", "asset_id": "Asset ID"},
            )
            fig_bar.update_traces(marker_color=PX_SEQ[0], texttemplate=None)
            st.plotly_chart(fig_bar, use_container_width=True, key="res_eff_low_bar")

            # --- Analysis (formatted like reference) ---
            total_assets = len(df)
            low_assets = len(low_util)
            avg_util_all = pd.to_numeric(df["avg_cpu_utilization"], errors="coerce").mean() if total_assets else 0
            min_util_all = pd.to_numeric(df["avg_cpu_utilization"], errors="coerce").min() if total_assets else 0
            max_util_all = pd.to_numeric(df["avg_cpu_utilization"], errors="coerce").max() if total_assets else 0
            pct_low = (low_assets / total_assets * 100) if total_assets else 0.0

            st.write(f"""
What this graph is: A bar chart showing individual assets that are underutilized with average CPU utilization below 30 percent.

X-axis: Asset IDs.
Y-axis: CPU utilization (%).

What it shows in your data: There are {low_assets} underutilized assets out of {total_assets} total assets, which represents {pct_low:.2f}% of the environment.
The environment wide average CPU utilization is {avg_util_all:.2f}% and the utilization values across all assets range from {min_util_all:.2f}% up to {max_util_all:.2f}%.
This cluster of short bars highlights specific nodes where capacity is powered on but not being used effectively.

Overall: The chart reveals a clear pocket of idle or oversized capacity that is concentrated on a subset of servers rather than evenly spread.
This pattern indicates that a meaningful share of the hardware estate could be consolidated, repurposed or retired without jeopardising service performance.

How to read it operationally:

Peaks: Treat the bars that sit near zero percent CPU utilization as immediate candidates for decommissioning or reassignment, because they provide almost no productive work for the cost they incur.
Plateaus: Assets in the 20–30 percent band are strong candidates for rightsizing or consolidation because they are lightly used but still active throughout the period.
Drift control: If the number of bars in this underutilized group increases month over month, it signals that default VM sizes and provisioning guardrails are too generous and should be tightened.
Prioritisation: Overlay monthly cost per asset so that the most expensive idle servers are addressed first, turning this chart into a targeted cost reduction list.

Why this matters: Idle capacity is financial debt because it continues to consume power, licenses and operational effort without generating corresponding value.
Eliminating the left tail of this chart reduces operating expenditure and simplifies performance management by shrinking the amount of unused infrastructure that teams must care for.
""")

            # Graph 2: Histogram distribution of underutilized CPU
            fig_hist = px.histogram(
                df, x="avg_cpu_utilization", nbins=20, title="CPU Utilization Distribution"
            )
            fig_hist.update_traces(marker_color=PX_SEQ[1])
            st.plotly_chart(fig_hist, use_container_width=True, key="res_eff_low_hist")

            st.write(f"""
What this graph is: A histogram showing the overall distribution of CPU utilization across all assets in the environment.

X-axis: CPU utilization bins (%).
Y-axis: Asset count in each utilization bin.

What it shows in your data: Assets under 30 percent CPU utilization account for {low_assets} servers, which is {pct_low:.2f}% of the total estate.
The environment wide average CPU utilization is {avg_util_all:.2f}% and utilization values span from {min_util_all:.2f}% at the low end to {max_util_all:.2f}% at the high end.
A visible left tail in the histogram confirms that underutilization is a structural feature and not just a handful of isolated outliers.

Overall: The shape of the distribution shows how much of the estate sits in low utilization bands versus mid range or near saturation.
A heavy left tail means the estate is generally over-provisioned, while a more balanced shape suggests closer alignment between provisioned capacity and real workloads.

How to read it operationally:

Win zone: Spikes in the 0–20 percent utilization bins represent quick win opportunities where consolidation and down tiering can release capacity and reduce costs with minimal risk.
Guardrails: Aim for a modal utilization band that sits comfortably away from saturation but does not leave most assets idling in the lowest bins, then track whether the modal band drifts left or right over time.
Policy: If the histogram gradually shifts leftwards month after month, it indicates a provisioning culture that oversizes by default and needs stricter templates and review processes.
Targeting: Combine this utilization distribution with energy and licensing information so that focus is placed on low utilization assets that also carry the highest monthly cost.

Why this matters: The utilization distribution exposes systemic provisioning habits in a single view and shows whether the organization is leaving money on the table by running too cold.
Shifting the curve modestly to the right without driving assets into saturation translates directly into lower run rate while still protecting service quality.
""")

            # CIO Recommendation Tables (Benefits expanded, Phases more detailed)
            low_cost = float(
                pd.to_numeric(
                    df.loc[pd.to_numeric(df["avg_cpu_utilization"], errors="coerce") < 30, "cost_per_month_usd"],
                    errors="coerce"
                ).fillna(0).sum()
            ) if "cost_per_month_usd" in df.columns else 0
            low_savings = float(
                pd.to_numeric(
                    df.loc[pd.to_numeric(df["avg_cpu_utilization"], errors="coerce") < 30, "potential_savings_usd"],
                    errors="coerce"
                ).fillna(0).sum()
            ) if "potential_savings_usd" in df.columns else 0

            cio_under = {
                "cost": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Decommission persistently idle assets | **Phase 1 – Identify:** Identify assets whose CPU utilization remains below 30 percent for at least three consecutive months by using historical monitoring reports and dashboards. <br><br>**Phase 2 – Validate:** Engage application owners and infrastructure teams to confirm that these servers are not hosting critical workloads and that any dependencies are documented and safe to remove. <br><br>**Phase 3 – Retire/Repurpose:** Remove validated idle assets from production, or repurpose them into a controlled burst or lab pool with clear rules for when they can be used. | - Eliminates recurring license, energy and support costs by turning off servers that no longer provide meaningful business value.<br><br>- Reduces the number of nodes that operations teams need to patch, monitor and back up which lowers day to day workload and risk surface.<br><br>- Produces a cleaner and more accurate asset inventory so budgeting, audits and lifecycle planning are easier to execute and explain. | Savings Ratio = Σ(potential_savings_usd) / Σ(cost_per_month_usd) = ${low_savings:,.2f} / ${low_cost:,.2f} = **{(low_savings/low_cost if low_cost else 0):.2f}x**. | Bar chart lists **{low_assets}** sub-30% assets; histogram’s left tail quantifies idle cohort share. |
| Reallocate workloads from idle nodes | **Phase 1 – Pool:** Build a pool of low utilization workloads by grouping applications and services running on the sub 30 percent servers, including their placement and dependency constraints. <br><br>**Phase 2 – Pack:** Move these workloads onto fewer hosts and raise host utilization toward the estate average of {avg_util_all:.2f}% while keeping headroom for growth and incident recovery. <br><br>**Phase 3 – Power down:** Shut down the hardware that has been emptied, reclaim attached licenses and update inventory and monitoring so the estate view matches the new footprint. | - Delivers direct operating expense reduction because powered down hosts no longer consume energy, cooling or support effort every month.<br><br>- Increases overall utilization efficiency by concentrating workloads onto a smaller number of well sized servers instead of scattering them thinly across many machines.<br><br>- Improves data center power usage effectiveness because fewer active hosts are required for the same business output which is positive for both cost and sustainability targets. | Energy Savings ≈ (kWh avoided × tariff) + License reclaim; scope bounded by {low_assets} assets. | Histogram confirms concentration below 30% and portfolio range {min_util_all:.2f}%→{max_util_all:.2f}%. |
| Tighten provisioning policies | **Phase 1 – Audit:** Review current default VM sizes, templates and request patterns, and compare them against actual utilization data to see where capacity is routinely over requested. <br><br>**Phase 2 – Enforce:** Introduce stricter minimum and step sizes, standardized builds and approval workflows so that new capacity requests have to align with right sized templates. <br><br>**Phase 3 – Review:** Run monthly drift checks that compare requested sizes against realized utilization and adjust policies where teams still overshoot. | - Prevents future waste by stopping new oversized servers from being provisioned and keeps the estate from drifting back into low utilization patterns.<br><br>- Stabilizes the baseline configuration landscape which makes it easier to manage patching, monitoring and incident response with fewer exceptions.<br><br>- Reduces variation across teams so that infrastructure usage becomes more predictable and more transparent in cost discussions. | Avoided Cost ≈ (oversized cores × cost/core-month). | Left-tail density evidences oversizing trend requiring policy correction. |
""",
                "performance": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Adaptive workload placement | **Phase 1 – Instrument:** Ensure that each server emits clear hot and cold utilization signals by standardizing CPU metrics, tags and health checks across the environment. <br><br>**Phase 2 – Automate:** Configure the orchestrator or scheduling logic so that low priority or batch jobs are automatically moved away from hot nodes and placed on underused servers. <br><br>**Phase 3 – Tune:** Review performance and threshold settings on a quarterly basis to refine when and how workloads are moved so that stability and performance stay in balance. | - Improves performance consistency because hot nodes are relieved by automatically offloading less important jobs when they start to struggle.<br><br>- Increases overall throughput as workloads are kept within healthy utilization bands rather than oscillating between idle and overloaded states.<br><br>- Reduces manual intervention by operators who would otherwise need to rebalance workloads by hand during peak periods. | Throughput Gain ≈ (utilization rebalance × perf factor). | Bar list marks candidates to move; histogram shows breadth of underuse. |
| Utilization-based auto-scaling | **Phase 1 – Policy:** Define clear auto scaling policies that use CPU utilization thresholds and time windows to decide when to scale out and scale in for each service or pool. <br><br>**Phase 2 – Cap:** Configure sensible minimum and maximum instance counts or capacity limits so that scaling behaviour does not oscillate or overshoot in either direction. <br><br>**Phase 3 – Validate:** Generate regular efficiency and performance reports that compare auto scaling behaviour against incident and response time metrics. | - Reduces manual toil for operations teams because the platform reacts automatically to load changes instead of requiring constant human tuning.<br><br>- Provides capacity elasticity without forcing large capital purchases, especially for fluctuating or seasonal workloads.<br><br>- Keeps utilization in a healthier band which reduces the likelihood of performance incidents or prolonged slowdowns. | Efficiency Gain = automated hours / total hours. | Persistent low bins show automation headroom. |
| Monthly capacity reviews | **Phase 1 – Report:** Produce a monthly capacity review pack that highlights utilization outliers, trend shifts and the health of the under and over utilized cohorts. <br><br>**Phase 2 – Act:** Convert review findings into concrete actions such as consolidation, resizing or policy changes and assign owners and due dates. <br><br>**Phase 3 – Verify:** Track whether the utilization distribution shifts in the expected direction and confirm that completed actions deliver the planned effect. | - Ensures that capacity optimization becomes a continuous practice instead of a one off clean up exercise that quickly goes stale.<br><br>- Creates a closed feedback loop between analysis and action so issues are caught and addressed before they become urgent incidents.<br><br>- Builds shared accountability across infrastructure, finance and application teams because everyone can see the same evidence and decisions. | Time Saved = (manual review hours avoided × cost/hr). | Distribution width indicates current governance gap. |
""",
                "satisfaction": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Communicate optimisation benefits | **Phase 1 – Publish:** Create simple summaries of cost savings, energy reductions and risk reductions that result from turning off or consolidating idle servers and share these with stakeholders. <br><br>**Phase 2 – Socialise:** Present these outcomes in team briefings and governance forums so that business and technical leaders see how optimization work supports their goals. <br><br>**Phase 3 – Feedback:** Capture feedback on perceived performance and any concerns, and adjust optimization plans where valid risks are raised. | - Reduces pushback when infrastructure is removed because stakeholders understand the concrete benefits and see that risk has been assessed.<br><br>- Builds trust between technical teams and the business by turning optimization into a visible and shared success story instead of hidden technical work.<br><br>- Encourages future collaboration, as teams are more willing to participate in optimization when they can see positive outcomes communicated clearly. | Complaint deflection × minutes per case. | Charts make waste and wins visible to non-technical stakeholders. |
| Transparency dashboards | **Phase 1 – Build:** Develop dashboards that show resource usage, cost and optimization status at a level of detail that business and technical stakeholders can understand without specialist tools. <br><br>**Phase 2 – Share:** Provide read only access to these dashboards for key stakeholders so they can self serve answers to basic capacity questions. <br><br>**Phase 3 – Automate:** Set the dashboards to refresh automatically on a weekly or monthly cadence so that the information stays current without manual effort. | - Empowers stakeholders to understand how infrastructure is being used which reduces ad hoc information requests and misunderstandings.<br><br>- Provides a single source of truth for capacity and cost information which simplifies governance and decision making.<br><br>- Reduces escalation volume because stakeholders can see planned work and current posture without waiting for manual reports. | Escalation cost avoided × frequency. | Left-tail shrinkage becomes a KPI everyone can track. |
| Sustainability KPIs | **Phase 1 – Add:** Extend capacity dashboards to include energy consumption and estimated CO₂ emissions for each asset or service so environmental impact is visible. <br><br>**Phase 2 – Track:** Monitor these sustainability indicators on a monthly basis and correlate them with optimization actions taken on idle or oversized servers. <br><br>**Phase 3 – Target:** Set clear yearly reduction goals and align optimization initiatives to meet or exceed those targets. | - Supports environmental and social governance commitments by making carbon impact part of everyday infrastructure decisions.<br><br>- Creates additional business justification for decommissioning idle assets because the environmental benefits are quantified alongside cost savings.<br><br>- Improves the organisation’s public and internal reputation by demonstrating that infrastructure is managed responsibly from both cost and environmental perspectives. | CO₂ reduction × cost per ton. | Underuse cohort is the easiest CO₂ win; visible in left bins. |
"""
            }
            render_cio_tables("Underutilized Assets — CIO Recommendations", cio_under)

    # ======================
    # 2️⃣ Overutilized Assets
    # ======================
    with st.expander("📌 Overutilized Assets"):
        if "avg_cpu_utilization" in df.columns:
            df = df.copy()
            cpu_num = pd.to_numeric(df["avg_cpu_utilization"], errors="coerce")
            high_util = df[cpu_num > 85]

            # Graph 1: Bar chart for overutilized assets
            fig_bar_high = px.bar(
                high_util,
                x="asset_id",
                y="avg_cpu_utilization",
                title="Overutilized Assets (>85% CPU Utilization)",
                labels={"avg_cpu_utilization": "CPU Utilization (%)", "asset_id": "Asset ID"},
            )
            fig_bar_high.update_traces(marker_color=PX_SEQ[0])
            st.plotly_chart(fig_bar_high, use_container_width=True, key="res_eff_high_bar")

            # --- Analysis (formatted like reference) ---
            total_assets = len(df)
            high_assets = len(high_util)
            avg_util_all = cpu_num.mean() if total_assets else 0
            peak_util_all = cpu_num.max() if total_assets else 0
            low_util_all = cpu_num.min() if total_assets else 0
            pct_high = (high_assets / total_assets * 100) if total_assets else 0.0

            st.write(f"""
What this graph is: A bar chart showing individual assets that are overutilized with average CPU utilization above 85 percent.

X-axis: Asset IDs.
Y-axis: CPU utilization (%).

What it shows in your data: There are {high_assets} overutilized assets out of {total_assets} total assets, which is {pct_high:.2f}% of the environment.
The environment wide average CPU utilization is {avg_util_all:.2f}% and utilization values range from {low_util_all:.2f}% at the low end up to {peak_util_all:.2f}% at the peak.
The cluster of tall bars close to 100 percent highlights nodes that are running with very little safety margin.

Overall: The chart reveals a concentration of saturation risk on a specific subset of servers rather than a uniform load across the estate.
These hot nodes are more likely to generate performance incidents, tickets and SLA breaches if growth continues or if additional workloads are placed on them.

How to read it operationally:

Peaks: Treat bars at or above 95 percent as immediate action items that require load shedding, scaling or hardware upgrades before they cause outages.
Sustained risk: Assets in the 85–90 percent band should be placed under predictive alerts and orchestration policies so they do not creep higher without visibility.
Regression test: After remediation work, monitor whether these bars shrink and stay lower over time to confirm that fixes are durable instead of temporary patches.
Service lens: Map each hot asset to the services and SLAs it supports so that remediation is prioritised for the most customer facing or revenue critical workloads.

Why this matters: Sustained CPU saturation represents service risk debt that accumulates in the form of latency, instability and penalties when SLAs are breached.
Addressing the rightmost bars early lowers the probability of high impact incidents and gives teams back breathing room for planned change and growth.
""")

            # Graph 2: Histogram
            fig_hist_high = px.histogram(
                df, x="avg_cpu_utilization", nbins=20, title="Overall CPU Utilization Spread"
            )
            fig_hist_high.update_traces(marker_color=PX_SEQ[1])
            st.plotly_chart(fig_hist_high, use_container_width=True, key="res_eff_high_hist")

            st.write(f"""
What this graph is: A histogram showing the overall spread of CPU utilization across the environment.

X-axis: CPU utilization bins (%).
Y-axis: Asset count in each bin.

What it shows in your data: The right tail of the distribution corresponds to {high_assets} assets whose average CPU utilization is above 85 percent.
The environment wide average CPU utilization is {avg_util_all:.2f}% and the values span from {low_util_all:.2f}% to {peak_util_all:.2f}%.
A strong and persistent right tail indicates that a non trivial portion of the estate is operating close to saturation.

Overall: The distribution makes it clear how many assets are running hot versus those that are comfortably below risk thresholds.
If the bulk of the estate is clustered far from the right edge but the tail is heavy, then risk is concentrated and can be addressed in a targeted way.

How to read it operationally:

Incident early warning: Spikes in the 90–100 percent bins are leading indicators of performance tickets and outages if capacity is not adjusted.
Baseline drift: If the entire distribution shifts to the right over time, it signals that baseline load is increasing and that capacity plans need to be brought forward.
Balanced fix: Aim to reduce the right tail without creating a new oversized left tail, so remediation should combine optimization with sensible capacity adds rather than blunt overprovisioning.
Forensics: Correlate incident timestamps and service complaints with periods when assets fall into the highest utilization bins to size the remediation that will have the biggest impact.

Why this matters: The utilization spread shows whether systemic pressure is building up in the environment, which informs where buffers, automation and new capacity will buy the most stability for each dollar spent.
Using this view regularly reduces surprise incidents and gives leadership a clear narrative for proactive investment instead of reactive firefighting.
""")

            # CIO Recommendations (Benefits expanded, Phases detailed)
            high_cost = float(
                pd.to_numeric(df.loc[cpu_num > 85, "cost_per_month_usd"], errors="coerce").fillna(0).sum()
            ) if "cost_per_month_usd" in df.columns else 0
            high_savings = float(
                pd.to_numeric(df.loc[cpu_num > 85, "potential_savings_usd"], errors="coerce").fillna(0).sum()
            ) if "potential_savings_usd" in df.columns else 0

            cio_over = {
                "cost": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Redistribute high-load workloads | **Phase 1 – Detect:** Identify all servers whose average CPU utilization is above 85 percent by using monitoring tools and capacity reports. <br><br>**Phase 2 – Move:** Shift appropriate workloads from these hot servers to nodes that typically run below 70 percent, taking into account affinity rules and performance requirements. <br><br>**Phase 3 – Validate:** Monitor utilization for at least two weeks after the moves to confirm that the previously hot nodes now stay under 85 percent and that no new hotspots are created. | - Reduces the risk of outages and emergency purchases because workloads are spread more evenly and individual servers are less likely to hit hard limits.<br><br>- Lowers unplanned overtime for operations teams who would otherwise have to react to saturation driven incidents and firefights.<br><br>- Stabilizes energy usage per transaction because servers operate in more efficient utilization bands rather than oscillating between idle and maxed out. | Avoided Outage ≈ (hours avoided × cost/hr); cohort size = **{high_assets}**; potential savings observed = ${high_savings:,.2f}. | Bar chart highlights the specific hot assets; histogram right tail quantifies systemic pressure. |
| Preempt emergency purchases | **Phase 1 – Forecast:** Use recent utilization trends to highlight nodes that are likely to reach 90–100 percent CPU utilization within the next planning period if no action is taken. <br><br>**Phase 2 – Budget:** Plan and secure capacity additions or cloud burst arrangements for these nodes before they become urgent, aligning timing with financial and change windows. <br><br>**Phase 3 – Audit:** After the period ends, compare actual purchases and incidents against the forecast to refine the prediction model. | - Replaces last minute capacity purchases at premium rates with planned procurement at more favourable prices.<br><br>- Reduces the number of change freezes and emergency maintenance windows that disrupt normal delivery work.<br><br>- Gives leadership a clearer line of sight on upcoming spend which improves budget accuracy and reduces financial surprises. | Savings ≈ (emergency premium − planned price) × units; high-risk share seen in 90–100% bins. | Peak utilization reaches **{peak_util_all:.2f}%**; right-tail density supports pre-buy. |
| Optimise license allocation | **Phase 1 – Map:** Map premium license tiers and support contracts to the actual servers and services that use them and compare this to CPU utilization and workload criticality. <br><br>**Phase 2 – Right-size:** Reduce or downgrade licenses on nodes that do not require premium capacity or support while ensuring that critical high utilization systems remain properly covered. <br><br>**Phase 3 – Automate:** Introduce checks in renewal and provisioning processes so license allocation is reviewed against utilization data on a regular basis. | - Reduces overpayment on licensing by matching premium tiers only to servers that truly require them based on utilization and business importance.<br><br>- Aligns infrastructure cost more closely with delivered performance so finance teams can see clear justification for higher tier spend where it remains.<br><br>- Simplifies future audits because license usage and utilization evidence are aligned and easier to demonstrate to vendors and auditors. | License savings ≈ (excess licenses × fee/license); focus on top-decile nodes. | High bars show where premium tiers are actually justified versus not. |
""",
                "performance": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Workload auto-balancing | **Phase 1 – Enable:** Configure your orchestration or scheduling platform to be aware of CPU utilization and to treat sustained high utilization as a signal for rebalancing. <br><br>**Phase 2 – Tune:** Set queue and wait time thresholds that trigger movement of workloads off saturated nodes and onto underused nodes without breaking locality or latency requirements. <br><br>**Phase 3 – Measure:** Track tail latency and throughput for services affected by auto balancing to confirm that performance improves and remains stable. | - Reduces bottlenecks by ensuring that no single node carries a disproportionate share of the workload for long periods.<br><br>- Increases end to end throughput because requests are processed by servers that are not already overloaded.<br><br>- Improves user experience by flattening response time spikes that would otherwise appear during peak load on a small set of servers. | Δ Latency × request volume; target **{high_assets}** hot assets first. | Histogram right tail + bar list identify pressure nodes. |
| Predictive capacity alerts | **Phase 1 – Slope:** Monitor growth in CPU utilization over time and calculate the rate at which assets are approaching the 85–90–95 percent thresholds. <br><br>**Phase 2 – Alert:** Configure alerts that fire before these thresholds are crossed so mitigation actions or capacity adds can be executed in advance. <br><br>**Phase 3 – Review:** Review incident history each month against alert activity to optimise thresholds and reduce noise while still catching real risk. | - Prevents unnoticed drift into saturation by surfacing risk before it turns into outages or severe performance problems.<br><br>- Lowers mean time to respond and mean time to resolve because teams can act on early warnings rather than react to live incidents.<br><br>- Reduces the number of high severity incidents that reach customers because capacity issues are handled when they are still internal signals. | SLA penalties avoided × incident reduction. | Share of assets >85% = **{high_assets}**; max **{peak_util_all:.2f}%**. |
| Buffer provisioning | **Phase 1 – Allocate:** Identify services that operate near 80 percent or higher for sustained periods and define a modest safety margin for them in capacity models. <br><br>**Phase 2 – Recheck:** Reassess utilization and buffer sizes monthly to ensure that the margin is still appropriate and adjust for growth or optimization wins. <br><br>**Phase 3 – Adjust:** Reduce buffers for services that have stabilised and redeploy capacity to areas where it is more urgently needed. | - Provides a controlled safety margin so demand spikes can be absorbed without immediately causing incidents for critical services.<br><br>- Reduces the frequency of performance tickets by ensuring that high traffic services do not always operate at the edge of their capacity envelope.<br><br>- Optimizes capacity allocation over time by refining which services truly need a buffer and which can operate safely closer to average utilization. | Value ≈ (queue length reduction × cost/time). | Right-tail size justifies buffer deployment. |
""",
                "satisfaction": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Transparent performance status | **Phase 1 – Publish:** Provide stakeholders with simple dashboards or status pages that show overall utilization and highlight hot spots in non technical language. <br><br>**Phase 2 – Plan:** Use these views to communicate planned mitigation activities and expected completion dates for high utilization systems. <br><br>**Phase 3 – Track:** Monitor customer satisfaction trends alongside utilization to confirm that visible performance risks are being addressed. | - Reduces anxiety among business stakeholders who might otherwise only hear about performance issues when they become severe.<br><br>- Decreases duplicate tickets and escalations because users can see that problems are known and that there is an active plan to fix them.<br><br>- Builds trust in the infrastructure team by making performance risks and remediation transparent rather than opaque. | Complaint deflection × minutes per case; focus on peak days near **{peak_util_all:.2f}%**. | Right-tail spikes correlate with perceived slowness windows. |
| Prioritise customer-facing services | **Phase 1 – Map:** Map customer facing SLAs and critical business processes to the hot nodes identified in the overutilization analysis. <br><br>**Phase 2 – Shield:** Provide additional capacity, guardrails or isolation for those nodes so that they are less exposed to noise from other workloads. <br><br>**Phase 3 – Verify:** Monitor SLOs for these key services after changes to confirm that performance has become more predictable. | - Protects brand critical customer journeys from degradation during busy periods by ensuring they run on more stable infrastructure.<br><br>- Reduces the number and severity of escalations tied directly to revenue impacting services.<br><br>- Provides a clear story to leadership that the riskiest infrastructure issues are being addressed in line with business priorities. | SLA penalty avoided × affected transactions. | Bar chart pinpoints which assets to shield first. |
| Communicate recovery timelines | **Phase 1 – Notify:** When overutilization related issues are discovered, communicate what is affected, what actions are planned and when users can expect improvement. <br><br>**Phase 2 – Update:** Provide short progress updates as remediation steps are completed so stakeholders are not left guessing about status. <br><br>**Phase 3 – Review:** After the incident or risk period has passed, review customer satisfaction scores and feedback to improve future communication. | - Sets realistic expectations for stakeholders instead of leaving them uncertain about when performance will improve.<br><br>- Helps reduce the overall volume of inbound queries and tickets because users can see that actions are underway and when they should see the results.<br><br>- Supports long term trust recovery by showing that issues are acknowledged, addressed and followed up with learning. | CSAT uplift × ticket reduction. | Shrinking right tail after actions demonstrates recovery. |
"""
            }
            render_cio_tables("Overutilized Assets — CIO Recommendations", cio_over)
