import streamlit as st
import plotly.express as px
import pandas as pd
import re

# ======================================================
# Helper – CIO Table Renderer
# ======================================================
def render_cio_tables(title, cio_data):
    st.subheader(title)
    with st.expander("Cost Reduction"):
        st.markdown(cio_data["cost"], unsafe_allow_html=True)
    with st.expander("Performance Improvement"):
        st.markdown(cio_data["performance"], unsafe_allow_html=True)
    with st.expander("Customer Satisfaction Improvement"):
        st.markdown(cio_data["satisfaction"], unsafe_allow_html=True)


# ======================================================
# Target 8️⃣ – Workload Analysis
# ======================================================
def workload_analysis(df):
    df = df.copy()
    df.columns = [re.sub(r"[^\w]+", "_", c.strip().lower()) for c in df.columns]

    # ======================================================
    # Subtarget 1: Workload by Component Type
    # ======================================================
    with st.expander("📌 Workload by Component Type"):
        if {"component_type", "avg_cpu_utilization"} <= set(df.columns):
            comp_avg = df.groupby("component_type")["avg_cpu_utilization"].mean().reset_index()

            # --- Graph 1: Average CPU Utilization per Component ---
            fig_comp = px.bar(
                comp_avg,
                x="component_type",
                y="avg_cpu_utilization",
                text="avg_cpu_utilization",
                title="Average CPU Utilization by Component Type",
                labels={"component_type": "Component Type", "avg_cpu_utilization": "Average CPU Utilization (%)"},
            )
            fig_comp.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
            st.plotly_chart(fig_comp, use_container_width=True, key="workload_component_bar")

            # --- Dynamic Analysis (Graph 1) ---
            high_comp = comp_avg.loc[comp_avg["avg_cpu_utilization"].idxmax()]
            low_comp = comp_avg.loc[comp_avg["avg_cpu_utilization"].idxmin()]
            avg_util = comp_avg["avg_cpu_utilization"].mean()

            st.write(f"""
**What this graph is:** A comparative bar chart showing **average CPU workload** by component type.  
- **X-axis:** Component type.  
- **Y-axis:** Average CPU utilization (%).

**What it shows in your data:** Peak at **{high_comp['component_type']}** with **{high_comp['avg_cpu_utilization']:.2f}%**. Lowest at **{low_comp['component_type']}** with **{low_comp['avg_cpu_utilization']:.2f}%**. Overall average **{avg_util:.2f}%** across types.

**Overall:** A rising bar profile indicates **demand concentration** (risk of saturation), while shorter bars reveal **headroom** for redistribution.

**How to read it operationally:**  
1) **Peaks:** Shift workloads or scale capacity on top bars.  
2) **Plateaus:** If many bars are high, maintain outflow ≥ inflow via auto-scaling and throttles.  
3) **Downswings:** After actions, bars should flatten—validate which levers (orchestration, tuning) worked.  
4) **Mix:** Combine with cost/criticality so high-utilization, high-value components get priority.

**Why this matters:** Imbalanced load is **debt**. The more it concentrates, the more likely breaches, firefighting, and unhappy users. Balancing preserves **cost**, **performance**, and **satisfaction**.
""")

            # --- Graph 2: CPU Utilization Frequency Distribution ---
            fig_hist = px.histogram(
                df,
                x="avg_cpu_utilization",
                nbins=20,
                title="CPU Utilization Frequency Distribution",
                labels={"avg_cpu_utilization": "CPU Utilization (%)"},
            )
            st.plotly_chart(fig_hist, use_container_width=True, key="workload_component_hist")

            # --- Dynamic Analysis (Graph 2) ---
            peak = df["avg_cpu_utilization"].max()
            low = df["avg_cpu_utilization"].min()
            avg = df["avg_cpu_utilization"].mean()

            st.write(f"""
**What this graph is:** A histogram showing **CPU utilization distribution** across assets.  
- **X-axis:** CPU utilization (%).  
- **Y-axis:** Asset count per utilization bucket.

**What it shows in your data:** Range **{low:.2f}% → {peak:.2f}%** with an average of **{avg:.2f}%**. A dense mid-band suggests typical operating load; sparse tails capture low/high extremes.

**Overall:** A right-heavy tail indicates **demand exceeding capacity** (hot nodes); a left-heavy tail reveals **oversizing** and waste.

**How to read it operationally:**  
1) **Peaks:** Buckets above ~85% ⇒ trigger **load shedding** and tuning.  
2) **Plateaus:** Stable mid-bands ⇒ keep policies steady; watch drift.  
3) **Downswings:** After optimization, the right tail should shrink—confirm impact.  
4) **Mix:** Cross-tab by component/region so critical services don’t sit in the hot tail.

**Why this matters:** Tails are **debt**—they drive outages or waste. Keeping the distribution compact around a healthy band protects **budget**, **throughput**, and **user confidence**.
""")

            # --- CIO Recommendation Tables ---
            cio_component = {
                "cost": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Consolidate underutilized components | Phase 1: Identify components under 30% utilization and confirm that these low levels are consistent over time rather than caused by short term events so that the focus is on genuinely underused capacity.<br><br>Phase 2: Design a consolidation plan that migrates workloads from these lightly loaded components onto shared resources that can operate at healthier utilization while still meeting resilience and redundancy requirements.<br><br>Phase 3: Decommission or repurpose the idle assets that remain after migration and track the reduction in infrastructure, licensing, and maintenance costs over subsequent billing cycles. | - Reduces energy and maintenance cost by shutting down hardware that no longer carries meaningful workloads which directly lowers monthly operational expenses.<br><br>- Shrinks the physical and virtual footprint so teams spend less time patching, backing up, and monitoring unused or low value servers.<br><br>- Frees budget that can be redirected into modernizing critical systems, strengthening resilience, or funding innovation initiatives instead of supporting waste.<br><br>- Simplifies the estate which decreases complexity in capacity planning and makes it easier to standardize configurations across the environment.<br><br> | Formula: Cost Saving = Idle Components × Avg Monthly Cost. Dataset: {low_comp['component_type']} utilization = {low_comp['avg_cpu_utilization']:.2f}%. | Bar chart shows clear underutilization in {low_comp['component_type']}. |
| Reassign workloads from overburdened components | Phase 1: Detect components with utilization consistently above 80% and validate that this level is not a temporary spike but a regular operating pattern so that true hotspots are isolated.<br><br>Phase 2: Redistribute workloads from these highly loaded components to nodes with spare capacity or to newly provisioned resources in order to spread demand more evenly without breaching performance targets.<br><br>Phase 3: Validate system performance and stability after the migration by monitoring response times, error rates, and incident trends to ensure that the redistribution actually reduced risk rather than moving the bottleneck. | - Prevents capacity saturation and reactive scaling by reducing pressure on components that are constantly running near their limits which lowers the probability of sudden performance drops.<br><br>- Reduces unplanned outages and emergency interventions because workloads are proactively shifted before the infrastructure becomes overloaded.<br><br>- Extends the useful life of hardware and virtual capacity since components no longer operate at sustained maximum utilization that accelerates wear and risk.<br><br>- Improves user experience for services hosted on these components because they benefit from more consistent and predictable performance under varying load conditions.<br><br> | Formula: Cost Avoided = Δ Peak Utilization × Cost of Outage. Dataset: {high_comp['component_type']} peaks at {high_comp['avg_cpu_utilization']:.2f}%. | Bar chart identifies performance hotspots. |
| Automate scaling policies by component type | Phase 1: Configure scaling thresholds per component type based on observed utilization bands so that each class of component has rules tailored to its real workload profile rather than generic thresholds.<br><br>Phase 2: Implement automated policies that add or remove capacity when utilization crosses these thresholds, allowing the environment to adapt dynamically to load without waiting for manual actions.<br><br>Phase 3: Review utilization and scaling behaviour monthly to fine tune thresholds, cooldown periods, and scaling sizes so that automation remains aligned with actual demand patterns. | - Optimizes resource consumption dynamically by increasing capacity when demand rises and reducing it when demand falls which keeps utilization within a healthy range over time.<br><br>- Lowers the amount of human effort spent on routine capacity adjustments and reduces the risk of slow responses to sudden load changes.<br><br>- Avoids chronic over-provisioning because automated rules can trim excess capacity once peak periods pass rather than leaving extra resources idle indefinitely.<br><br>- Provides a clearer link between utilization targets and business outcomes so leaders can see how scaling policies protect both cost and performance objectives.<br><br> | Formula: Utilization Adjustment × Cost per VM. Dataset: Mean = {avg_util:.2f}%. | Histogram shows imbalance across utilization ranges. |
""",
                "performance": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Rebalance workloads across infrastructure | Phase 1: Map utilization levels across all components to identify which nodes are under heavy load and which have room to take on additional work so that imbalance becomes visible.<br><br>Phase 2: Redistribute high load workloads or split large jobs so that they run across multiple components with available capacity, taking into account dependency and latency requirements.<br><br>Phase 3: Monitor latency, throughput, and SLA adherence after rebalancing to confirm that the new distribution improves overall system performance without creating new hotspots. | - Improves throughput by ensuring that no single component becomes a chronic bottleneck while others sit partially idle which allows workloads to flow more smoothly.<br><br>- Reduces the risk of performance degradation during peak periods because processing is spread across a broader and better matched set of resources.<br><br>- Enhances stability for critical services since they are less likely to be impacted by localized overload on a single component or small group of nodes.<br><br>- Provides a stronger foundation for future growth because the platform can take on new workloads more gracefully when load is balanced from the start.<br><br> | Formula: Efficiency Gain = Δ Response Time × Transactions. Dataset: {high_comp['component_type']} operates 2.5× above {low_comp['component_type']}. | Graph shows uneven performance pressure. |
| Implement predictive workload analytics | Phase 1: Collect historical utilization data across components and time periods to understand demand cycles, peak windows, and recurring patterns that drive resource consumption.<br><br>Phase 2: Train simple forecasting models or adopt analytics that predict future workloads so that scaling decisions and maintenance windows can be scheduled ahead of demand rather than after the fact.<br><br>Phase 3: Automate or guide scaling decisions using these predictions and periodically validate the forecast accuracy to refine the models and inputs used. | - Enhances capacity accuracy by aligning infrastructure decisions with forward looking demand expectations instead of relying only on static thresholds or manual estimates.<br><br>- Improves SLA compliance because capacity is already in place when expected peaks arrive, reducing the likelihood of slowdowns and timeouts during busy windows.<br><br>- Reduces the amount of emergency scaling or last minute reconfiguration needed during unexpected bursts which lowers operational stress and error risk.<br><br>- Supports more credible communication with stakeholders as capacity plans can be backed by data and demonstrated predictive performance rather than guesswork.<br><br> | Formula: Forecast Error Reduction × Cost per Cycle. Dataset: Utilization spread = {peak-low:.2f}%. | Histogram demonstrates cyclic utilization behavior. |
| Standardize configuration templates | Phase 1: Define standard hardware and virtual configurations with clear CPU and memory ratios that are appropriate for the main workload categories in the environment.<br><br>Phase 2: Enforce these templates for new deployments and gradually migrate non standard systems into the closest fitting templates to reduce variation and special cases.<br><br>Phase 3: Audit performance and utilization after standardization to ensure that the templates deliver predictable results and adjust them when patterns or technologies change. | - Increases uniformity and predictability in how components behave under load which makes performance tuning and troubleshooting faster and more reliable.<br><br>- Reduces incidents caused by unusual or bespoke configurations that behave differently from the rest of the fleet and are poorly understood by operations teams.<br><br>- Simplifies automation, monitoring, and patching because tools can assume a smaller set of well known configuration patterns instead of many one off designs.<br><br>- Helps new engineers and support staff understand the environment more quickly since they interact with a consistent set of component types and templates.<br><br> | Formula: Downtime Prevented × SLA Value. Dataset: Range = {peak-low:.2f}%. | Graph reveals non-standard workload patterns. |
""",
                "satisfaction": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Prioritize optimization for critical components | Phase 1: Identify which component types host business critical workloads by mapping services and applications to their underlying infrastructure so that optimization focuses on the right areas.<br><br>Phase 2: Allocate additional capacity, stronger monitoring, and stricter change controls to these critical components to reduce the likelihood of user impacting slowdowns or outages.<br><br>Phase 3: Track SLA improvement, incident frequency, and user feedback for these workloads to ensure that the extra focus is delivering a noticeable uplift in reliability. | - Improves reliability for the systems that users and customers care about most which translates directly into higher satisfaction and fewer escalations.<br><br>- Reduces visible service interruptions for key journeys such as transactions, orders, or core business processes that depend on these components.<br><br>- Builds confidence among business stakeholders that infrastructure optimization is being driven by business impact rather than purely technical metrics.<br><br>- Creates a clear hierarchy of attention so teams know where to invest effort first when time and resources are limited.<br><br> | Formula: SLA Gain × Customer Value. Dataset: {high_comp['component_type']} peak = {high_comp['avg_cpu_utilization']:.2f}%. | Bar chart highlights mission-critical peaks. |
| Share workload optimization reports with stakeholders | Phase 1: Summarize key performance insights and actions taken to optimize workloads into simple, non technical reports that stakeholders can easily understand.<br><br>Phase 2: Review these findings in monthly or quarterly sessions with business owners to connect technical improvements with service outcomes such as fewer complaints or faster response times.<br><br>Phase 3: Use stakeholder feedback to refine priorities and build a continuous improvement loop where future optimization focuses on the areas that matter most to users. | - Builds trust through transparency because stakeholders can see what has been changed, why decisions were made, and how those changes affect their services.<br><br>- Reduces misalignment between IT and business expectations since performance discussions are anchored in shared data and documented actions rather than assumptions.<br><br>- Encourages collaborative decision making about where to direct future optimization efforts which leads to higher satisfaction with the roadmap.<br><br>- Lowers the volume of ad hoc queries and status requests because regular reporting provides a predictable channel for updates and explanations.<br><br> | Formula: Engagement Uplift = Communication Rate × Trust Index. | Histogram visually supports transparency of usage patterns. |
| Provide proactive alerts for high-utilization components | Phase 1: Enable alerting for components that exceed a defined utilization threshold such as 85% and ensure that alert routing is configured to reach the correct support teams in real time.<br><br>Phase 2: Integrate these alerts into operational dashboards and incident workflows so that engineers can investigate and remediate issues before users experience major impact.<br><br>Phase 3: Review alert history and resolution times regularly to fine tune thresholds and ensure alerts are actionable rather than noisy. | - Enhances end user confidence by reducing the number of times they experience slow or unavailable services because issues are caught and addressed earlier.<br><br>- Shortens the time between the start of a performance problem and the beginning of remediation which lowers the duration of user facing impact when issues do occur.<br><br>- Demonstrates a proactive posture to stakeholders who see that monitoring is designed to prevent incidents rather than only react to them.<br><br>- Provides evidence that the organization is continuously improving its ability to detect and manage high utilization events which supports long term satisfaction and trust.<br><br> | Formula: Downtime Avoided × Alert Efficiency. Dataset: {high_comp['component_type']} exceeds alert threshold. | Peaks clearly visible in histogram. |
"""
            }
            render_cio_tables("Component Workload — CIO Recommendations", cio_component)

        else:
            st.warning("⚠️ Required columns not found. Please ensure the dataset includes 'component_type' and 'avg_cpu_utilization'.")


    # ======================================================
    # Subtarget 2: Workload Correlation Analysis
    # ======================================================
    with st.expander("📌 Workload Correlation Analysis"):
        if {"avg_cpu_utilization", "avg_memory_utilization"} <= set(df.columns):
            # --- Graph 1: CPU vs Memory Utilization Scatter ---
            fig_scatter = px.scatter(
                df,
                x="avg_cpu_utilization",
                y="avg_memory_utilization",
                color="component_type",
                title="CPU vs Memory Utilization by Component Type",
                labels={"avg_cpu_utilization": "Average CPU Utilization (%)", "avg_memory_utilization": "Average Memory Utilization (%)"}
            )
            st.plotly_chart(fig_scatter, use_container_width=True, key="workload_corr_scatter")

            # --- Dynamic analysis for scatter ---
            corr = df["avg_cpu_utilization"].corr(df["avg_memory_utilization"])
            peak_cpu = df["avg_cpu_utilization"].max()
            peak_mem = df["avg_memory_utilization"].max()
            low_cpu = df["avg_cpu_utilization"].min()
            low_mem = df["avg_memory_utilization"].min()
            avg_cpu = df["avg_cpu_utilization"].mean()
            avg_mem = df["avg_memory_utilization"].mean()

            st.write(f"""
**What this graph is:** A scatter plot showing **joint CPU vs Memory behavior** across assets.  
- **X-axis:** Average CPU utilization (%).  
- **Y-axis:** Average Memory utilization (%).

**What it shows in your data:** Correlation **{corr:.2f}**. Ranges: CPU **{low_cpu:.2f}% → {peak_cpu:.2f}%**, Memory **{low_mem:.2f}% → {peak_mem:.2f}%**. Averages at **CPU {avg_cpu:.2f}%**, **Memory {avg_mem:.2f}%**.

**Overall:** Points near the diagonal are **balanced**; deviations mark **CPU-bound** or **Memory-bound** assets—prime targets for right-sizing.

**How to read it operationally:**  
1) **Peaks:** Upper-right cluster ⇒ pre-scale capacity and harden critical paths.  
2) **Plateaus:** Dense diagonal ⇒ sustain policies; monitor drift and seasonality.  
3) **Downswings:** After fixes, dispersion should narrow—validate impact.  
4) **Mix:** Join with incident/SLA logs so critical apps don’t sit as outliers.

**Why this matters:** Imbalance is **debt**. The farther assets stray from balance, the more you pay in waste, latency, and escalations. Balance safeguards **cost**, **performance**, and **satisfaction**.
""")

            # --- Graph 2: Heatmap for workload density ---
            fig_heat = px.density_heatmap(
                df,
                x="avg_cpu_utilization",
                y="avg_memory_utilization",
                title="Workload Density Heatmap (CPU vs Memory Utilization)",
                nbinsx=20, nbinsy=20
            )
            st.plotly_chart(fig_heat, use_container_width=True, key="workload_corr_heatmap")

            st.write(f"""
**What this graph is:** A density heatmap pinpointing **where most assets operate** on CPU and Memory jointly.  
- **X-axis:** Average CPU utilization (%).  
- **Y-axis:** Average Memory utilization (%).

**What it shows in your data:** The darkest cluster sits near **CPU {avg_cpu:.2f}%** and **Memory {avg_mem:.2f}%** (dominant zone). Sparse corners denote rare but **high-risk** stress states.

**Overall:** Tight central clustering implies **predictable load** (simpler planning); broad spread or hot corners imply **volatile demand** and scaling risk.

**How to read it operationally:**  
1) **Peaks:** Dense high-high cells ⇒ stage capacity and protect critical paths.  
2) **Plateaus:** Stable mid-band ⇒ keep guardrails; track seasonal drift.  
3) **Downswings:** After tuning, heat should consolidate—verify quarterly.  
4) **Mix:** Overlay component/region to ensure resilience where it matters most.

**Why this matters:** Unmanaged hotspots are **debt**—they raise outage probability and user pain. Keeping density in a healthy zone preserves **budget**, **resilience**, and **experience**.
""")

            # --- CIO Recommendation Tables ---
            cio_corr = {
                "cost": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Consolidate workloads with similar utilization profiles | Phase 1: Identify clusters where CPU and Memory operate near the mean values so that workloads with similar behaviour are grouped and easier to manage collectively.<br><br>Phase 2: Merge underused instances inside these clusters onto fewer nodes that can run at healthier utilization without breaching performance targets.<br><br>Phase 3: Reassign or retire excess resources after consolidation and monitor cost reports to ensure that the expected reduction in compute and hosting spend is realized. | - Reduces redundant compute capacity and energy costs by eliminating multiple lightly used instances that could comfortably run on a smaller number of well utilized nodes.<br><br>- Lowers operational overhead because there are fewer servers and configurations to patch, monitor, and support within the consolidated cluster.<br><br>- Increases utilisation consistency across the environment which makes capacity planning simpler and more accurate for future growth.<br><br>- Creates clearer pools of capacity which can be managed as units, improving flexibility when workloads need to be scaled or rebalanced later.<br><br> | Formula: Savings = (Idle Nodes × Avg Monthly Cost). Dataset mean: CPU {avg_cpu:.2f}%, Mem {avg_mem:.2f}%. | Heatmap concentration around midrange supports consolidation. |
| Reallocate resources from low-load to high-load components | Phase 1: Detect outliers where CPU utilization is below 30% while Memory is above 70% or the reverse so that clear misalignment between allocated resources and actual demand is visible.<br><br>Phase 2: Adjust allocations by moving workloads, resizing instances, or changing resource quotas so that high demand components receive sufficient capacity and low demand components no longer hold unused resources.<br><br>Phase 3: Validate post change utilization and performance to confirm that reallocation reduced imbalance without introducing new performance issues or capacity risks. | - Prevents over-provisioning by aligning CPU and Memory allocation more closely with real workload patterns which reduces waste in underused dimensions.<br><br>- Improves performance on stressed components because they gain access to capacity that was previously sitting idle elsewhere in the estate.<br><br>- Reduces the likelihood of dual bottlenecks where one resource is constrained while another remains underutilized which often leads to confusing incident behaviour.<br><br>- Supports more predictable behaviour under load since resources are sized according to combined CPU and Memory requirements instead of arbitrary defaults.<br><br> | Formula: Rebalanced Capacity × Cost per Core. Dataset extremes: CPU {low_cpu:.2f}% – {peak_cpu:.2f}%. | Scatter outliers mark imbalance zones. |
| Automate right-sizing policies | Phase 1: Establish target CPU and Memory ratios for each component type based on observed correlation so that right sizing rules reflect the way workloads truly consume resources.<br><br>Phase 2: Implement auto-scaling or policy driven resizing that nudges instances toward these targets whenever utilization drifts significantly above or below the desired band.<br><br>Phase 3: Periodically review right sizing outcomes by comparing pre and post change utilization and cost to ensure the policies continue to drive savings without harming performance. | - Minimizes idle resource spending by continually aligning allocated capacity with actual usage patterns rather than letting mis-sized instances persist indefinitely.<br><br>- Reduces manual tuning work for engineers who would otherwise need to adjust CPU and Memory allocations asset by asset.<br><br>- Improves consistency across the environment because similar workloads are automatically steered toward similar utilization profiles which simplifies governance.<br><br>- Strengthens the link between optimization actions and financial outcomes since policy driven changes can be measured in terms of concrete cost reductions and stability improvements.<br><br> | Formula: Rightsized % × Total Cost. Dataset shows imbalance at correlation {corr:.2f}. | Scatter spread indicates resizing need. |
""",
                "performance": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Optimize task distribution based on utilization balance | Phase 1: Identify which workloads are CPU heavy and which are Memory heavy by analysing their positions on the scatter plot so that complementary workloads can be paired on the same nodes.<br><br>Phase 2: Place CPU heavy workloads onto nodes that have spare CPU but stable Memory usage and place Memory heavy workloads where Memory headroom exists, balancing each node’s combined resource profile.<br><br>Phase 3: Monitor throughput, queue lengths, and response times after redistribution to verify that the new placement increases effective capacity and reduces contention. | - Increases system throughput by ensuring that CPU and Memory on each node are both used efficiently rather than having one resource saturated while the other remains underused.<br><br>- Reduces performance bottlenecks caused by stacking similar heavy workloads on the same node which often leads to slowdowns and timeouts under load.<br><br>- Improves the resilience of services during peaks because workloads are spread in a way that avoids overloading a single resource dimension on any particular asset.<br><br>- Supports more graceful degradation in extreme scenarios since well balanced nodes handle stress better than nodes where one resource is already at its limit.<br><br> | Formula: Δ Throughput × Avg Request Time. Dataset: correlation {corr:.2f}. | Points along diagonal reflect ideal pairings. |
| Apply predictive analytics for joint resource peaks | Phase 1: Use historical CPU and Memory data to identify times when both resources peak together and model how often these joint spikes occur for different services and components.<br><br>Phase 2: Forecast future joint spikes using these patterns and pre scale infrastructure or adjust workload scheduling so that capacity is available before combined load reaches critical levels.<br><br>Phase 3: Compare actual performance and incident patterns in predicted peak periods against prior periods without predictive preparation to measure the benefit and refine the forecasting model. | - Prevents performance degradation during periods where both CPU and Memory would otherwise spike simultaneously by ensuring extra capacity is available in advance.<br><br>- Reduces firefighting during high stress events because infrastructure is already sized and shaped for expected joint demand instead of reacting after users are impacted.<br><br>- Improves SLA compliance for complex workloads that stress multiple resources at once which are often the most business critical.<br><br>- Provides better insight into multi dimensional load patterns which can inform long term architectural decisions and system redesign work.<br><br> | Formula: SLA Violations Avoided × Cost per Incident. | Heatmap hotspots show joint utilization bursts. |
| Standardize monitoring thresholds | Phase 1: Define alert ranges that consider both CPU and Memory utilization together rather than only individual thresholds so that monitoring reflects real combined stress on components.<br><br>Phase 2: Configure alerts and dashboards to trigger when assets move outside these joint ranges, making it easy to spot when either resource balance or total load becomes unhealthy.<br><br>Phase 3: Review alert performance and adjust thresholds using historical data so that true problems are caught early while unnecessary noise is minimized. | - Improves responsiveness because alerts highlight the conditions that are most correlated with real performance issues instead of relying on simplistic single metric triggers.<br><br>- Reduces alert fatigue for operations teams since thresholds are tuned to realistic joint utilisation patterns which lowers the number of false positives.<br><br>- Increases the quality of incident triage information as alerts already point to the combined CPU and Memory context rather than leaving engineers to reconstruct it manually.<br><br>- Helps maintain consistent monitoring practices across different services and teams which simplifies operations and governance.<br><br> | Formula: Reduction in Mean-Time-to-Detect × Impact Cost. Dataset mean zone = CPU {avg_cpu:.2f}% / Mem {avg_mem:.2f}%. | Graph clusters justify threshold tuning. |
""",
                "satisfaction": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Maintain consistent performance for balanced workloads | Phase 1: Focus tuning and capacity protection on the balanced region near the diagonal where most user facing workloads operate so that the core experience remains stable.<br><br>Phase 2: Continuously monitor user latency and error rates for services mapped to this balanced zone and quickly intervene if metrics deviate from expected ranges.<br><br>Phase 3: Periodically review whether key workloads are drifting away from the balanced region and adjust infrastructure or code to bring them back into a stable operating band. | - Ensures uniform experience for end users who rely on the majority of workloads that sit in the balanced zone, reducing visible performance variance across different times and locations.<br><br>- Lowers the number of complaints related to random slowdowns because the main services people use are kept within a well controlled utilisation envelope.<br><br>- Builds confidence in the reliability of digital services which supports higher adoption and usage of self service channels and online processes.<br><br>- Provides a clear focus area for optimisation efforts that directly aligns with what most users feel when they interact with the system.<br><br> | Formula: Latency Drop × Active Sessions. Dataset mid-cluster = CPU {avg_cpu:.2f}% / Mem {avg_mem:.2f}%. | Balanced region confirms optimal user performance. |
| Communicate infrastructure balance improvements | Phase 1: Prepare clear summaries that show how infrastructure balance has improved over time, using before and after charts for correlation and density to illustrate the shift.<br><br>Phase 2: Link these technical improvements to service KPIs such as reduced incident rates, faster response times, or higher availability so that stakeholders see the real world impact.<br><br>Phase 3: Share these updates regularly with business and technology leaders to keep them informed and gather feedback on where further improvements are needed. | - Strengthens stakeholder confidence by demonstrating that infrastructure is being actively tuned to provide a smoother and more reliable experience for users.<br><br>- Makes it easier to justify future investment in capacity, tooling, or optimisation as stakeholders can see the tangible benefits from previous rounds of work.<br><br>- Encourages shared ownership of performance outcomes because both IT and business teams understand how infrastructure changes support their goals.<br><br>- Reduces misunderstanding about the causes of performance issues since stakeholders can see where balance has improved and where hotspots still exist.<br><br> | Formula: CSAT Gain × Engagement Rate. | Scatter visual supports measurable stability. |
| Implement transparent performance dashboards | Phase 1: Publish real-time or near real-time dashboards that show joint CPU and Memory load for key services in a format that is accessible to both technical teams and informed business stakeholders.<br><br>Phase 2: Allow customers or internal users to view high level performance indicators, where appropriate, so they understand when the system is under stress and when it is operating normally.<br><br>Phase 3: Use insights from dashboard usage and user feedback to refine which metrics are displayed and how often they are updated so that the information remains meaningful and trusted. | - Builds trust and reduces perceived downtime because users can see that issues are recognized and are being managed rather than assuming nothing is happening behind the scenes.<br><br>- Lowers the volume of repeated inquiries to service desks or support teams since users can self check the current state of the system.<br><br>- Encourages a culture of transparency where performance challenges are acknowledged and addressed openly rather than hidden until they become crises.<br><br>- Helps align expectations during busy periods because stakeholders can see the same information that operations teams are using to guide decisions.<br><br> | Formula: Inquiry Reduction × Cost per Inquiry. | Heatmap’s clear zones aid communication clarity. |
"""
            }
            render_cio_tables("Workload Correlation — CIO Recommendations", cio_corr)
        else:
            st.warning("⚠️ Required columns 'avg_cpu_utilization' and 'avg_memory_utilization' not found in dataset.")
