import streamlit as st
import plotly.express as px
import pandas as pd

# --- Visual identity: professional blue & white (global) ---
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


def virtualization_cloud(df):

    # ======================================================
    # 1️⃣ VM Utilization Efficiency
    # ======================================================
    with st.expander("📌 VM Utilization Efficiency"):
        if {"vm_name", "avg_cpu_utilization"} <= set(df.columns):
            vm_eff = df.groupby("vm_name")["avg_cpu_utilization"].mean().reset_index()

            # Graph 1: Bar chart of average CPU utilization by VM
            fig_vm_bar = px.bar(
                vm_eff,
                x="vm_name",
                y="avg_cpu_utilization",
                title="Average CPU Utilization by Virtual Machine",
                text="avg_cpu_utilization",
                labels={"avg_cpu_utilization": "Average CPU Utilization (%)", "vm_name": "Virtual Machine Name"}
            )
            fig_vm_bar.update_traces(texttemplate="%{text:.2f}%", textposition="outside", marker_color=PX_SEQ[0])
            st.plotly_chart(fig_vm_bar, use_container_width=True, key="vm_eff_bar")

            # --- Analysis for Graph 1 (Bar) ---
            avg_util = vm_eff["avg_cpu_utilization"].mean() if len(vm_eff) else 0
            peak_vm = vm_eff.loc[vm_eff["avg_cpu_utilization"].idxmax()] if len(vm_eff) else {"vm_name": "N/A", "avg_cpu_utilization": 0}
            low_vm = vm_eff.loc[vm_eff["avg_cpu_utilization"].idxmin()] if len(vm_eff) else {"vm_name": "N/A", "avg_cpu_utilization": 0}

            st.write(f"""
What this graph is: A bar chart showing average CPU utilization by virtual machine.

X-axis: Virtual machine names.
Y-axis: Average CPU utilization (%).
What it shows in your data: {peak_vm['vm_name']} is the highest utilization VM at {peak_vm['avg_cpu_utilization']:.2f}%, while {low_vm['vm_name']} is the lowest at {low_vm['avg_cpu_utilization']:.2f}%. The overall VM average across the environment is {avg_util:.2f}%.
This spread indicates that some VMs are running hot and close to their limits while others are significantly underused and likely oversized for their current workloads.

Overall: The virtualized estate is unevenly sized across machines, with a visible mix of high, medium, and low utilization instances.
That pattern simplifies prioritization because actions focused on the extreme highs and lows can unlock savings and stability without disturbing the healthy middle band.

How to read it operationally:

Peaks: Standardize an action plan for VMs with sustained utilization above about 85%, deciding whether to scale them up, redistribute their workloads, or adjust resource limits so that they operate with safe headroom.<br>
Plateaus: Treat the mid range VMs with stable utilization as reference templates and use their shapes as starting points for future capacity planning and VM sizing.<br>
Downswings: Investigate very low bars to confirm whether those machines can be consolidated, rehosted, or switched off without affecting service levels for users.<br>
Mix: Combine this bar view with cost and criticality data so that high utilization high value VMs receive resilience investments and low utilization high cost VMs become early rightsizing targets.<br>
Why it matters: Steering VM utilization toward a controlled mid band reduces the risk of SLA breaches on overloaded machines and cuts wasted spend on machines that do very little work.
""")

            # Graph 2: Histogram of VM utilization spread
            fig_vm_hist = px.histogram(
                vm_eff, x="avg_cpu_utilization", nbins=20, title="VM Utilization Distribution (%)"
            )
            fig_vm_hist.update_traces(marker_color=PX_SEQ[1])
            st.plotly_chart(fig_vm_hist, use_container_width=True, key="vm_eff_hist")

            # --- Analysis for Graph 2 (Histogram) ---
            n_vms = len(vm_eff)
            low_tail = int((vm_eff["avg_cpu_utilization"] < 30).sum()) if n_vms else 0
            high_tail = int((vm_eff["avg_cpu_utilization"] > 85).sum()) if n_vms else 0
            pct_low_tail = (low_tail / n_vms * 100) if n_vms else 0
            pct_high_tail = (high_tail / n_vms * 100) if n_vms else 0
            min_util = vm_eff["avg_cpu_utilization"].min() if n_vms else 0
            max_util = vm_eff["avg_cpu_utilization"].max() if n_vms else 0

            st.write(f"""
What this graph is: A histogram showing the distribution of CPU utilization across all virtual machines.

X-axis: CPU utilization buckets (%).
Y-axis: Number of virtual machines in each utilization bucket.
What it shows in your data: {low_tail} of {n_vms} VMs ({pct_low_tail:.2f}%) sit below 30% utilization on the left tail and {high_tail} of {n_vms} VMs ({pct_high_tail:.2f}%) exceed 85% utilization on the right tail. Overall utilization spans from {min_util:.2f}% at the lowest to {max_util:.2f}% at the highest.
The combination of a wide left tail and a noticeable right tail suggests that there is both consolidation potential and saturation risk within the same environment.

Overall: The utilization profile shows a broad spread rather than a tight cluster around a single healthy band.
That shape indicates that provisioning habits vary across teams and workloads and that consistent policies could bring more machines into an efficient middle range.

How to read it operationally:

Peaks: Focus left hand peaks in the 0–30% range as candidates for consolidation, retirement, or rightsizing and treat peaks in the 90–100% range as immediate hotspots that need capacity relief or workload redistribution.<br>
Plateaus: Treat the central buckets in the 50–70% range as the desired operating zone and use that band as a benchmark when sizing new workloads and instances.<br>
Downswings: After optimization programs, expect the extreme tails to shrink and the mass of the histogram to move closer to the efficient middle range in subsequent reporting periods.<br>
Mix: Overlay cost, criticality, and incident data so that you address both expensive idle capacity and high risk hotspots in a prioritized and coordinated way.<br>
Why it matters: Shaping the utilization distribution toward the middle reduces operating expense and lowers the probability of incidents that are caused by either chronic underuse or chronic overload.
""")

            # Data-driven analysis for CIO tables
            total_cost = df["cost_per_month_usd"].sum() if "cost_per_month_usd" in df.columns else 0
            pot_savings = df["potential_savings_usd"].sum() if "potential_savings_usd" in df.columns else 0
            high_util_count = (df["avg_cpu_utilization"] > 85).sum()
            low_util_count = (df["avg_cpu_utilization"] < 30).sum()

            # CIO Tables — VM Utilization Efficiency
            cio_vm_eff = {
                "cost": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Consolidate underutilized virtual machines | Phase 1: Identify virtual machines with average CPU utilization below 30% using the histogram and bar chart and confirm with application owners that no critical or hidden batch workloads depend on them.<br><br>Phase 2: Plan and execute migration of any remaining workloads from these low use VMs onto shared hosts and mark truly idle instances for decommission so that capacity is pooled more efficiently.<br><br>Phase 3: After consolidation, review utilization, cost, and incident trends for the affected VMs over at least one full billing cycle to verify that savings are real and that no service regression has occurred.<br><br> | - Reduces ongoing operating expenditure because fewer virtual machines and underlying hosts need to be powered, licensed, and supported for the same amount of business work.<br><br>- Cuts the amount of idle or low value capacity in the fleet which means more of the cloud or on premises spend is directly aligned with real usage and demand.<br><br>- Shrinks the logical and physical footprint of the environment which simplifies monitoring, backup, and patching activities for operations teams.<br><br>- Improves overall resource utilization which supports sustainability and efficiency targets without compromising availability or response times for users.<br><br> | Formula: Savings Ratio = potential_savings_usd ÷ cost_per_month_usd<br>Dataset: ${pot_savings:,.2f}/${total_cost:,.2f} = {(pot_savings/total_cost if total_cost else 0):.2f}<br>Result: Indicates how much of current monthly cost could be reclaimed through consolidation.<br> | Histogram left tail confirms {low_util_count} low use VMs below 30% utilization and the bar chart pinpoints the specific VM names that sit in that low efficiency cohort. |
| Implement automated rightsizing policies | Phase 1: Enable or configure cloud and virtualization recommendations that analyze historical CPU and memory utilization for each VM and propose smaller or more appropriate instance sizes where usage is persistently low.<br><br>Phase 2: Review the recommendations with platform and application teams and apply rightsizing changes in controlled waves so that resource allocations are adjusted without destabilizing workloads.<br><br>Phase 3: Reassess utilization, performance, and cost each quarter to refine thresholds and ensure that rightsizing policies continue to reflect actual workload behavior as systems evolve.<br><br> | - Reduces overspending on compute capacity by aligning VM sizes more closely to the resources that workloads actually use rather than worst case assumptions.<br><br>- Lowers manual effort for engineers by turning recurring rightsizing decisions into standard policy driven workflows instead of one off tuning exercises.<br><br>- Improves visibility into capacity posture for leadership because the estate gradually converges on a consistent sizing approach with fewer extreme outliers.<br><br>- Creates a sustainable and repeatable optimization loop so that new workloads are regularly corrected if they drift away from their ideal size over time.<br><br> | Formula: Overprovisioned capacity cost = (Overprovisioned vCPU hours × Cost per vCPU hour)<br>Dataset: Average utilization of {avg_util:.2f}% across VMs indicates where high vCPU counts are not fully used.<br>Result: Highlights the financial impact of persistent underuse relative to allocated capacity.<br> | Bar chart shows many VMs operating well below peak capacity while paying for higher tiers, indicating rightsizing opportunities flagged by the utilization spread. |
| Rebalance VM-to-host density | Phase 1: Analyze host level metrics to understand which physical or logical hosts are lightly loaded and which are carrying dense sets of virtual machines that are still under overall capacity limits.<br><br>Phase 2: Carefully migrate or evacuate low use VMs from multiple underutilized hosts onto a smaller number of consolidated hosts while respecting redundancy and fault domain requirements.<br><br>Phase 3: Once workloads are concentrated appropriately, power down, repurpose, or reclassify the freed hosts and update inventory and monitoring systems so that cost reductions are captured and maintained.<br><br> | - Lowers compute, energy, and facility costs by reducing the number of active hosts required to support the current workload mix while keeping enough headroom for growth and failover.<br><br>- Reduces operational complexity because there are fewer servers to patch, monitor, and troubleshoot which streamlines day to day run activities.<br><br>- Increases the overall efficiency of the virtualization layer by ensuring that remaining hosts run closer to their optimal utilization range.<br><br>- Frees up hardware capacity that can be reused for new projects, lab environments, or disaster recovery without immediate capital expenditure.<br><br> | Formula: Savings = (Number of hosts avoided × Monthly cost per host)<br>Dataset: Consolidation potential is indicated by the population of VMs below 30% utilization shown in the histogram.<br>Result: Quantifies cost impact of retiring or repurposing lightly utilized hosts after consolidation.<br> | Histogram distribution supports high consolidation potential and the VM bar chart identifies where underloaded VMs can be grouped onto fewer hosts. |
""",
                "performance": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Scale up high-load virtual machines | Phase 1: Identify virtual machines that show sustained CPU utilization above about 85% and validate with performance and incident data that they are genuinely overloaded rather than misconfigured.<br><br>Phase 2: Increase vCPU or memory allocations, or move these critical workloads to higher performance instance types or hosts with more headroom while scheduling changes during agreed windows.<br><br>Phase 3: Re measure response times, error rates, and queue lengths after scaling to ensure that the additional capacity has resolved the bottlenecks without simply masking deeper issues.<br><br> | - Reduces the risk of timeouts, slow transactions, and service disruptions caused by VMs that frequently operate near saturation.<br><br>- Improves user experience for applications running on those virtual machines because there is more capacity available during peak demand periods.<br><br>- Lowers incident volumes linked to resource exhaustion which in turn decreases firefighting workload for support teams.<br><br>- Creates a clear pattern for when and how to increase capacity so that scaling decisions are consistent and data driven instead of reactive.<br><br> | Formula: Performance benefit = (Improvement in response time × Request volume) translated into time or revenue gained<br>Dataset: {high_util_count} VMs exceed the 85% utilization threshold identified in the histogram.<br>Result: Indicates how many VMs are at risk of throttle and where scaling interventions should be targeted first.<br> | Bar chart highlights heavily loaded VMs near saturation and the histogram right tail confirms a cohort of high utilization instances that affect performance. |
| Enable predictive auto-scaling | Phase 1: Configure auto scaling policies based on observed demand patterns, including thresholds for adding or removing VM instances and timing profiles for known peaks and troughs.<br><br>Phase 2: Integrate the auto scaling configuration with monitoring and alerting so that operators can see when and why capacity is added or removed in response to utilization signals.<br><br>Phase 3: Review auto scaling events and performance outcomes on a monthly basis to tune thresholds, cooldown periods, and scaling steps so that capacity changes are smooth and effective.<br><br> | - Maintains stable performance under fluctuating demand by adding capacity ahead of saturation and releasing it when it is no longer needed.<br><br>- Reduces manual intervention during peak events which allows engineers to focus on exception handling instead of routine scaling tasks.<br><br>- Keeps utilization closer to the desired middle band by continuously balancing load across a flexible pool of virtual machines.<br><br>- Improves predictability of service levels since traffic spikes are handled by defined policy rather than improvised responses.<br><br> | Formula: SLA breach cost avoided = (Number of prevented performance incidents × Average cost per incident)<br>Dataset: Peaks around {peak_vm['avg_cpu_utilization']:.2f}% in the bar and histogram views justify the need for automatic allocation during high load.<br>Result: Connects scaling automation to tangible reductions in SLA risk and incident cost.<br> | Histogram right tail and tall bars in the bar chart confirm periodic high utilization spikes where auto scaling provides value. |
| Use resource affinity rules | Phase 1: Review placement and scheduling of heavy compute, disk, and network workloads to identify clusters of resource intensive VMs that currently contend on the same hosts or storage paths.<br><br>Phase 2: Define and apply affinity and anti affinity rules so that particularly heavy workloads are either separated or intentionally grouped depending on resilience and performance requirements.<br><br>Phase 3: Monitor latency, throughput, and error patterns after applying the rules and refine placements if new hotspots or imbalances appear.<br><br> | - Reduces noisy neighbor effects where one or two heavy workloads degrade performance for other virtual machines sharing the same host or underlying resources.<br><br>- Improves stability for critical applications by ensuring that their resource needs are not constantly in conflict with other intensive jobs.<br><br>- Makes performance tuning more predictable because workload placements follow a designed pattern instead of evolving randomly over time.<br><br>- Supports better use of hardware by matching workloads to host capabilities in a deliberate and transparent manner.<br><br> | Formula: Benefit approximation = (Reduction in average latency or error rate × Transaction volume) converted into user time or revenue protected<br>Dataset: Cluster analysis of the highest utilization VMs in the bar chart and histogram reveals where contention is likely.<br>Result: Links resource placement design to measurable performance gains for busy workloads.<br> | Visual evidence of high utilization clusters in the charts supports the need for explicit affinity and anti affinity strategies on the top percentage of VMs. |
""",
                "satisfaction": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Maintain transparency on virtualization performance | Phase 1: Build simple reports and dashboards that show VM utilization profiles, including hot, normal, and cold machines, in language that business stakeholders can understand.<br><br>Phase 2: Include cost to performance insights in these dashboards so that people can see how utilization and spend relate for major application groups or business services.<br><br>Phase 3: Share these views on a regular cadence and invite questions from stakeholders so that performance and cost conversations are grounded in shared data.<br><br> | - Builds trust with business and customers because they can see how virtualized resources are being used to support their services.<br><br>- Reduces subjective complaints about performance by providing factual context around utilization trends and any actions taken to improve them.<br><br>- Encourages collaborative decision making on where to invest or reduce capacity since all parties can see the same underlying evidence.<br><br>- Demonstrates proactive stewardship of the platform which reassures stakeholders that capacity, cost, and performance are being actively managed.<br><br> | Formula: Escalations avoided = (Reduction in performance related escalations × Average handling effort per escalation)<br>Dataset: Average to peak utilization difference from {avg_util:.2f}% to {peak_vm['avg_cpu_utilization']:.2f}% is clearly visible in the charts.<br>Result: Shows how transparency can prevent misinterpretation of normal high utilization as uncontrolled risk.<br> | Bar chart conveys a clear hierarchy of VM utilization and the histogram gives an estate wide view that supports communication with non technical audiences. |
| Prioritize mission critical workloads in high demand clusters | Phase 1: Work with business stakeholders to identify which workloads running on the virtualized platform are mission critical and document their mapping to specific virtual machines and services.<br><br>Phase 2: Assign additional safeguards and capacity buffers to those critical workloads, such as higher priority resource pools or stricter utilization thresholds, so that they remain stable under load.<br><br>Phase 3: Monitor these prioritized workloads during peak periods and verify that their performance stays within agreed targets even when the rest of the environment is under stress.<br><br> | - Protects the user journeys and business processes that cause the most impact if they slow down or fail, which directly supports satisfaction and revenue protection.<br><br>- Reduces the likelihood that critical services are affected by noisy neighbor issues or generic platform wide contention.<br><br>- Provides a clear rationale for why some workloads receive more resources or attention which helps manage expectations for less critical systems.<br><br>- Creates a structured playbook for handling performance trade offs when capacity is limited so that decisions remain aligned with business priorities.<br><br> | Formula: SLA penalties avoided = (Expected penalty per breach × Number of prevented SLA breaches for critical services)<br>Dataset: {high_util_count} VMs above 85% utilization represent the segment where mission critical workloads are most exposed.<br>Result: Quantifies the value of directing protection to the riskiest high load areas first.<br> | Histogram right tail and the tallest bars in the utilization chart identify the clusters where prioritization of critical workloads will have the greatest impact on satisfaction. |
| Communicate performance improvements post optimization | Phase 1: After making changes such as consolidation, scaling, or rightsizing, capture before and after snapshots of utilization distributions and highlight shifts away from extremes.<br><br>Phase 2: Share short summaries with business stakeholders that explain what was changed, why it was done, and how it affects stability, capacity, and cost for their services.<br><br>Phase 3: Collect user feedback and ticket trends after optimizations to see whether perceptions of performance have improved and feed those findings back into future plans.<br><br> | - Reinforces confidence that optimization work is producing tangible benefits rather than being purely technical activity in the background.<br><br>- Helps users and managers connect reduced incidents or smoother performance with specific engineering actions which supports ongoing investment.<br><br>- Encourages constructive feedback loops where users are more likely to share issues early because they have seen their input lead to improvements before.<br><br>- Provides a clear narrative for leadership that links virtualization tuning to better service quality and more efficient use of budget.<br><br> | Formula: Satisfaction impact = (Increase in CSAT or Net Promoter Score × Number of respondents) converted into a value proxy<br>Dataset: A visible shift of the histogram from heavy tails to a tighter middle band after optimization is a strong visual indicator of improvement.<br>Result: Helps quantify how technical optimization contributes to user experience outcomes.<br> | Trend analysis of utilization charts before and after actions validates that the environment has moved toward a more stable and efficient state that users can feel. |
"""
            }
            render_cio_tables("VM Utilization Efficiency — CIO Recommendations", cio_vm_eff)

    # ======================================================
    # 2️⃣ Cloud Cost vs Utilization
    # ======================================================
    with st.expander("📌 Cloud Cost vs Utilization"):
        if {"avg_cpu_utilization", "cost_per_month_usd"} <= set(df.columns):

            # Graph 1: Scatter chart of cost vs utilization
            fig_cost_scatter = px.scatter(
                df,
                x="avg_cpu_utilization",
                y="cost_per_month_usd",
                title="Cloud Cost vs CPU Utilization",
                labels={"avg_cpu_utilization": "Average CPU Utilization (%)", "cost_per_month_usd": "Monthly Cost (USD)"},
                trendline="ols"
            )
            fig_cost_scatter.update_traces(marker=dict(color=PX_SEQ[0]))
            st.plotly_chart(fig_cost_scatter, use_container_width=True, key="cloud_cost_scatter")

            # --- Analysis for Graph 1 (Scatter) ---
            peak_cost = float(df["cost_per_month_usd"].max())
            low_cost = float(df["cost_per_month_usd"].min())
            avg_cost = float(df["cost_per_month_usd"].mean())
            peak_util = float(df["avg_cpu_utilization"].max())
            low_util = float(df["avg_cpu_utilization"].min())
            n_rows = len(df)
            hi_cost_lo_util = int(((df["avg_cpu_utilization"] < 40) & (df["cost_per_month_usd"] >= df["cost_per_month_usd"].quantile(0.75))).sum()) if n_rows else 0

            st.write(f"""
What this graph is: A scatter plot showing monthly cloud cost against CPU utilization, with a fitted trendline.

X-axis: Average CPU utilization (%).
Y-axis: Monthly cloud cost (USD).
What it shows in your data: Individual resources range in cost from ${low_cost:,.2f} to ${peak_cost:,.2f} with an average of ${avg_cost:,.2f}, while utilization spans from {low_util:.2f}% to {peak_util:.2f}%. There are {hi_cost_lo_util} high cost but low utilization points in the upper left area which indicate overspend on underused capacity.
The slope and spread of the points reveal how well cost is aligned with real usage across the estate.

Overall: Spend is unevenly tied to utilization, with some resources delivering good value for money and others consuming budget without delivering proportional work.
That pattern highlights where targeted clean up of outliers can free budget while leaving well aligned resources untouched.

How to read it operationally:

Peaks: Focus on expensive resources with utilization below about 40% and evaluate whether they can be downsized, consolidated, or shut down to eliminate waste.<br>
Plateaus: Identify mid band resources that are consistently used and consider moving them to reserved or committed pricing to secure lower unit rates for predictable demand.<br>
Downswings: After optimization, expect the upper left cluster of high cost low utilization points to shrink and the main cloud of points to move closer to the diagonal suggested by the trendline.<br>
Mix: Join this view with business unit or cost center tags so that ownership for high cost anomalies is clear and chargeback discussions are based on visible evidence.<br>
Why it matters: Paying premium prices for resources that deliver little work erodes budgets and credibility and reduces the ability to invest in capacity where it genuinely improves performance and resilience.
""")

            # Graph 2: Trendline of cost efficiency (cost per utilization unit)
            safe_util = df["avg_cpu_utilization"].replace(0, pd.NA)
            df["cost_efficiency"] = df["cost_per_month_usd"] / safe_util
            fig_eff_trend = px.line(
                df.sort_values("avg_cpu_utilization"),
                x="avg_cpu_utilization",
                y="cost_efficiency",
                title="Cost Efficiency Trend (USD per % Utilization)"
            )
            fig_eff_trend.update_traces(line=dict(color=PX_SEQ[1]))
            st.plotly_chart(fig_eff_trend, use_container_width=True, key="cost_eff_trend")

            # --- Analysis for Graph 2 (Line) ---
            eff_series = df["cost_efficiency"].dropna()
            avg_eff = float(eff_series.mean()) if not eff_series.empty else 0
            min_eff = float(eff_series.min()) if not eff_series.empty else 0
            max_eff = float(eff_series.max()) if not eff_series.empty else 0

            st.write(f"""
What this graph is: A line chart showing cost per unit of utilization, expressed as USD spent per percentage point of CPU utilization, ordered by utilization level.

X-axis: Average CPU utilization (%).
Y-axis: Cost per utilization point (USD per % CPU).
What it shows in your data: Cost efficiency ranges from ${min_eff:,.2f} per percentage point of CPU at the best end to ${max_eff:,.2f} at the worst end, with an average of ${avg_eff:,.2f}. Higher values at low utilization levels represent poor efficiency while flatter and lower values at higher utilization show better value for each dollar spent.
The overall curve shape indicates where marginal spend is buying meaningful work versus where it mostly funds idle capacity.

Overall: The efficiency curve is not flat which means some resources deliver significantly better cost per unit of work than others.
That variation suggests that policy and sizing improvements can pull inefficient outliers toward the more efficient baseline and smooth the curve over time.

How to read it operationally:

Peaks: Target sharp spikes at low utilization as first priority for rightsizing or decommission because these points indicate high spend for very little usage.<br>
Plateaus: Use flat segments where efficiency is stable as benchmarks for healthy cost behavior and encode those patterns into templates and guidelines for future allocations.<br>
Downswings: Monitor the curve after each optimization wave and confirm that new data shows lower and more stable cost per utilization across the range.<br>
Mix: Extend the metric beyond CPU to include storage and network components so that teams see total cost per unit of useful work rather than a single dimension.<br>
Why it matters: A flatter and more predictable efficiency curve makes budgeting more reliable and reduces the chance of sudden cost spikes without corresponding business value.
""")

            # CIO Tables — Cloud Cost vs Utilization
            cio_cloud_cost = {
                "cost": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Terminate or downsize high-cost, low-use VMs | Phase 1: Use the scatter plot to identify resources that fall into the quadrant with utilization below about 40% and cost in the top quartile and confirm with owners that these are not reserved for imminent projects or critical standby roles.<br><br>Phase 2: For confirmed candidates, either move workloads to smaller instance types, consolidate them with other workloads, or terminate idle instances once any required data has been preserved.<br><br>Phase 3: After one or two billing cycles, verify that cloud spend has dropped in line with the removed or downsized resources and that there has been no unexpected impact on service levels.<br><br> | - Cuts direct cloud expenditure by eliminating resources that consume a relatively large monthly fee while doing very little useful work.<br><br>- Frees up budget that can be redirected to performance, resilience, or innovation initiatives that produce visible business value.<br><br>- Reduces configuration and monitoring overhead for operations teams because there are fewer redundant or idle resources to track and manage.<br><br>- Sends a clear signal to internal teams about the importance of active stewardship of cloud resources which supports better cultural discipline around consumption.<br><br> | Formula: Savings = Sum of monthly cost of high cost low utilization VMs retired or downsized<br>Dataset: High cost VMs extend up to ${peak_cost:,.2f} in the scatter with utilization below 40% for identified waste candidates.<br>Result: Shows the absolute value of reclaimed spend when those points are removed or shrunk.<br> | Scatter plot upper left quadrant clearly shows a group of high cost low utilization instances that do not align spend with usage. |
| Adopt reserved instances for steady workloads | Phase 1: Analyze historical utilization and uptime for workloads to find those with stable and predictable usage patterns that rarely fall idle or exceed their normal range.<br><br>Phase 2: For suitable workloads, move from pure on demand pricing to reserved or committed use contracts that match their typical instance shapes and runtime profiles.<br><br>Phase 3: Track actual savings versus expectations and refine the mix of reserved and on demand capacity at renewal points to stay aligned with business needs.<br><br> | - Lowers unit pricing for compute that is needed anyway by taking advantage of long term or committed use discounts from cloud providers.<br><br>- Provides more predictable and stable cloud bills which makes budgeting and forecasting easier for finance and technology leadership.<br><br>- Encourages teams to plan for steady state workloads rather than overusing short term or burst oriented capacity models.<br><br>- Reinforces good architecture practices by making clear which workloads are long lived and should be engineered for efficiency and reliability.<br><br> | Formula: Cost reduction = (On demand hourly price minus reserved hourly price) × Hours of reserved usage<br>Dataset: Mid range utilization band between about 50% and 70% on the scatter is a good candidate set for reserved pricing.<br>Result: Quantifies the recurring monthly savings from moving stable workloads into reserved models.<br> | Scatter and trendline highlight a core of consistently used resources where reserved or committed pricing would bring down average cost per unit of work. |
| Implement chargeback policies for low-use cost centers | Phase 1: Tag resources by business unit, project, or cost center and generate reports that show cost against utilization so owners can see where spend is not matched by usage.<br><br>Phase 2: Share these reports and establish a clear chargeback or showback model that allocates costs to the teams responsible for the underlying consumption patterns.<br><br>Phase 3: Review trends each quarter and work with teams that show persistent low use high cost patterns to adjust architectures, retire unused environments, or redesign processes.<br><br> | - Encourages more responsible use of cloud by making the cost of idle or inefficient resources visible to the teams that control them.<br><br>- Leads to ongoing optimization as project owners identify and shut down forgotten or overprovisioned systems to avoid internal charges.<br><br>- Aligns financial accountability with technical decision making which improves the quality of choices around architecture and capacity.<br><br>- Supports transparent budgeting discussions where leaders can see which areas are carrying the highest ratio of cost to utilization and take action accordingly.<br><br> | Formula: Cost reallocation or reduction = Sum of cost associated with low utilization resources that are either eliminated or funded by their owning cost center<br>Dataset: Scatter points below 40% utilization with significant cost are mapped to specific tags for accountability.<br>Result: Shows where governance and policy can drive structural reductions in wasteful spend.<br> | Combination of the cost versus utilization scatter and per owner tagging reveals which cost centers have the largest clusters of inefficient resources. |
""",
                "performance": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Rebalance workloads across instances | Phase 1: Use the scatter plot and utilization metrics to identify instances that are overloaded and others that are lightly used but have similar capabilities and compatible workloads.<br><br>Phase 2: Move or redistribute workloads so that demand is spread more evenly across instances which prevents some machines from being overworked while others sit idle.<br><br>Phase 3: Measure performance indicators such as response times, error rates, and throughput after rebalancing to ensure that the new distribution has improved overall system behavior.<br><br> | - Improves aggregate throughput because more of the available compute capacity is actively contributing to useful work instead of sitting idle.<br><br>- Reduces chances of performance incidents caused by local hotspots on specific instances while other capacity remains underused.<br><br>- Can postpone or reduce the need for new capacity purchases because existing resources are used more effectively.<br><br>- Creates a more predictable performance envelope for users since load is smoothed across the compute estate rather than spiking on a few nodes.<br><br> | Formula: Throughput gain value = (Increase in processed transactions or jobs × Value per transaction) adjusted by any extra cost<br>Dataset: Moving points from low utilization high cost areas toward the main utilization band improves the cost and performance balance seen in the scatter.<br>Result: Connects improved workload distribution to both better performance and better cost efficiency.<br> | Scatter shape indicates overconcentration of work on some instances while others sit in lower utilization zones that can absorb additional load. |
| Enable auto-tiering between on-prem and cloud | Phase 1: Classify workloads based on volatility, latency sensitivity, and compliance so that steady predictable workloads and spiky or bursty workloads are clearly separated.<br><br>Phase 2: Place steady loads on the most cost efficient platform such as on premises or long term reserved cloud capacity and direct bursty episodic loads to flexible cloud resources that can scale quickly when needed.<br><br>Phase 3: Monitor cost and performance outcomes over time and adjust tiering rules and platform choices when patterns of usage or cost models change.<br><br> | - Balances flexibility and cost by using elastic cloud only where it adds value and relying on lower cost platforms for consistent workloads.<br><br>- Improves performance for burst workloads which benefit from the ability to scale rapidly during peaks instead of queuing on fixed capacity.<br><br>- Reduces risk of runaway cloud bills by making sure stable workloads are not unnecessarily left on premium on demand pricing.<br><br>- Provides clearer architectural guidance for teams designing new services so platform choices align with expected behavior from the start.<br><br> | Formula: Net benefit = (Reduced cloud cost for steady workloads plus reduced performance incidents for burst workloads) minus migration and integration costs<br>Dataset: Distinct clusters of high cost low utilization and medium utilization points in the scatter support a tiered approach.<br>Result: Highlights how correct placement of different workload types changes the shape of cost versus utilization over time.<br> | Scatter distribution and trendline show where some workloads are poorly matched to their current platform and could be re tiered for better cost and performance. |
| Integrate forecasting to prevent cost overruns | Phase 1: Use historical cost and utilization data to build simple forecasts of future usage and spend for major applications and environments under different growth assumptions.<br><br>Phase 2: Set proactive alerts and guardrails that trigger reviews or scaling actions when actual utilization or cost deviates significantly from forecasted ranges.<br><br>Phase 3: Regularly compare forecasted versus actual outcomes and refine the models and guardrails so they become more accurate and useful over time.<br><br> | - Reduces the likelihood of sudden and unexpected cost spikes because emerging trends are seen early and corrected before invoices grow too large.<br><br>- Helps teams plan capacity changes ahead of time which maintains performance without relying on last minute reactive scaling.<br><br>- Improves confidence for finance and leadership in cloud budgets since spend follows a more predictable trajectory.<br><br>- Encourages a culture of continuous planning and review rather than waiting for problems to appear after the fact.<br><br> | Formula: Cost avoided = Sum of difference between forecasted and uncontrolled spend where corrective actions were taken in time<br>Dataset: Deviations from the expected trendline in the scatter and instability in the cost efficiency line indicate where forecasting and guardrails can reduce volatility.<br>Result: Shows how predictive insight transforms cost management from reactive to proactive with measurable impact.<br> | Cost efficiency line and scatter trendline highlight ranges where behavior is predictable enough to forecast and others where extra controls are needed. |
""",
                "satisfaction": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Improve transparency on cloud cost efficiency | Phase 1: Build simple visuals that show both utilization and cost for key services and share them with product owners, finance partners, and other stakeholders.<br><br>Phase 2: Explain the meaning of cost per utilization metrics and highlight which services are currently efficient and which are not so that the concept becomes part of regular dialogue.<br><br>Phase 3: Track how efficiency indicators change after optimization work and report progress in terms of fewer outliers and smoother cost behavior.<br><br> | - Builds trust that cloud spending is being actively managed and not left to grow without oversight.<br><br>- Gives non technical stakeholders a clear way to understand whether they are getting good value for the money spent on their services.<br><br>- Encourages collaborative decision making on where to optimize or invest because everyone can see the same metrics and trends.<br><br>- Reduces friction between technology and finance teams by replacing vague discussions with concrete efficiency indicators.<br><br> | Formula: Escalations avoided = (Reduction in spend related disputes or complaints × Handling cost per escalation)<br>Dataset: Smoothing of the cost efficiency line over time indicates more predictable and fair cost per unit of work.<br>Result: Demonstrates that transparency and optimization directly reduce tension around cloud bills.<br> | Graph trend communicates how optimization efforts gradually reduce extreme values and bring overall efficiency into a more controlled band. |
| Align service-level expectations to cost tiers | Phase 1: Define clear service tiers that link expected performance and availability levels with the cost of the underlying cloud resources and architectures used to deliver them.<br><br>Phase 2: Map applications and customers to the appropriate tiers so that high paying or mission critical services sit on more resilient and higher cost platforms and lower tier services use more economical options.<br><br>Phase 3: Review feedback and performance data regularly and adjust tier mappings or underlying designs where expectations and delivered experience are not aligned.<br><br> | - Ensures that customer expectations about reliability and speed match the investment made in the infrastructure that supports their workloads.<br><br>- Protects high value customers and services by explicitly funding the level of resilience and performance they require.<br><br>- Prevents frustration from lower tier customers who might otherwise expect premium performance without the corresponding spend.<br><br>- Provides a clear framework for commercial and technical conversations when users request higher service levels or lower costs.<br><br> | Formula: Value from alignment = (Reduction in SLA disputes and credits × Monetary impact per dispute) plus retained revenue from satisfied customers<br>Dataset: Top quartile cost points in the scatter correspond to premium service zones that should have matching expectations.<br>Result: Shows how tiering and expectation setting turn cloud cost differences into deliberate and accepted choices rather than surprises.<br> | Scatter shows where higher cost resources are concentrated which should correlate with higher service tiers to keep satisfaction and spend in balance. |
| Communicate budget adherence metrics | Phase 1: Define simple budget adherence indicators such as monthly spend versus plan and cost efficiency targets and publish them alongside utilization charts.<br><br>Phase 2: During governance or steering sessions, review these indicators with stakeholders and explain how optimization work is contributing to staying within or under budget.<br><br>Phase 3: Capture feedback on where additional visibility or changes are needed and refine reporting and optimization focus accordingly.<br><br> | - Increases confidence that cloud budgets are under control and that surprises are being actively prevented rather than discovered late.<br><br>- Helps stakeholders see the connection between optimization initiatives and financial outcomes which makes it easier to support further improvements.<br><br>- Reduces anxiety around cloud costs for both business and technology leaders because they can see trends and corrective actions in one place.<br><br>- Encourages continuous improvement by making budget and efficiency metrics part of normal management rhythms instead of one off reviews.<br><br> | Formula: Budget variance impact = (Difference between planned and actual spend × Impact factor for over or underspend)<br>Dataset: Stabilizing cost efficiency lines and reduced scatter outliers indicate healthier adherence to budget expectations.<br>Result: Provides a quantitative link between technical cost control actions and financial governance outcomes.<br> | Line trend and scatter shape together show whether cost management is becoming more disciplined which directly affects stakeholders perception of control and competence. |
"""
            }
            render_cio_tables("Cloud Cost vs Utilization — CIO Recommendations", cio_cloud_cost)
