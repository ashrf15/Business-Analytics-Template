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


def resource_allocation(df):

    # =========================================================
    # 1️⃣ Resource Allocation Efficiency
    # =========================================================
    with st.expander("📌 Resource Allocation Efficiency"):
        if {"avg_cpu_utilization", "avg_memory_utilization"} <= set(df.columns):

            df["efficiency_score"] = 100 - abs(df["avg_cpu_utilization"] - df["avg_memory_utilization"])

            # Graph 1: Histogram of resource efficiency
            fig_eff_hist = px.histogram(
                df, x="efficiency_score", nbins=20, title="Resource Efficiency Distribution (%)"
            )
            fig_eff_hist.update_traces(marker_color=PX_SEQ[0])
            st.plotly_chart(fig_eff_hist, use_container_width=True, key="efficiency_hist")

            # --- Analysis for Graph 1 (Histogram) ---
            avg_eff = df["efficiency_score"].mean()
            min_eff = df["efficiency_score"].min()
            max_eff = df["efficiency_score"].max()
            n_assets = len(df)
            n_low_eff = int((df["efficiency_score"] < 60).sum())
            pct_low_eff = (n_low_eff / n_assets * 100) if n_assets else 0

            st.write(f"""
What this graph is: A bar chart showing the distribution of overall resource efficiency, where CPU and memory utilization are compared and converted into a 0–100 efficiency score.

X-axis: Efficiency score for each asset.
Y-axis: Asset count in each efficiency bucket.
What it shows in your data: Average efficiency is {avg_eff:.2f} percent, with scores ranging from {min_eff:.2f} percent to {max_eff:.2f} percent. {n_low_eff} of {n_assets} assets ({pct_low_eff:.2f} percent) fall below 60 percent efficiency, which highlights a cohort with clear CPU and memory imbalance.
Overall: The left tail represents misaligned configurations, while the center and right areas show assets that are closer to balanced and therefore healthier from a resource utilization perspective.

How to read it operationally:

Peaks: A tall bar in the low efficiency region, especially below 60 percent, signals immediate right sizing candidates where CPU and memory are clearly out of balance.
Plateaus: A broad center region suggests stable resource balance across many assets, which indicates that current provisioning policies are mostly working but still require monitoring for drift over time.
Downswings: A visible shift of the distribution towards the right over multiple reporting periods indicates that orchestration, automation, or rightsizing initiatives are improving efficiency and should be standardised.
Mix: When the histogram is combined with cost per month and SLA criticality, low efficiency but high impact systems can be prioritised first because they represent both wasted spend and operational risk.
Why this matters: Imbalanced resources create hidden financial and performance debt by paying for capacity that is not used while leaving other parts of the stack exposed to throttling and slowdown.
It also shows exactly where tuning and rightsizing can reduce operating expenditure and smooth performance volatility across the environment.
""")

            # Graph 2: Scatter CPU vs Memory balance
            fig_balance = px.scatter(
                df,
                x="avg_cpu_utilization",
                y="avg_memory_utilization",
                title="CPU vs Memory Utilization Balance",
                labels={"avg_cpu_utilization": "CPU Utilization (%)", "avg_memory_utilization": "Memory Utilization (%)"}
            )
            fig_balance.update_traces(marker=dict(color=PX_SEQ[1]))
            st.plotly_chart(fig_balance, use_container_width=True, key="balance_scatter")

            # --- Analysis for Graph 2 (Scatter) ---
            diff = (df["avg_cpu_utilization"] - df["avg_memory_utilization"]).abs()
            within10 = int((diff <= 10).sum())
            pct_within10 = (within10 / n_assets * 100) if n_assets else 0
            max_cpu = df["avg_cpu_utilization"].max()
            max_mem = df["avg_memory_utilization"].max()
            min_cpu = df["avg_cpu_utilization"].min()
            min_mem = df["avg_memory_utilization"].min()

            st.write(f"""
What this graph is: A scatter plot that compares CPU utilization to memory utilization for each asset in order to visualize how balanced each configuration is.

X-axis: CPU utilization in percent.
Y-axis: Memory utilization in percent.
What it shows in your data: {within10} of {n_assets} assets ({pct_within10:.2f} percent) sit within plus or minus ten percentage points of the diagonal line, which indicates well balanced CPU and memory usage for those cases. Outliers far away from the diagonal are configurations where one resource is heavily used while the other remains relatively idle. Observed ranges are CPU from {min_cpu:.2f} percent to {max_cpu:.2f} percent and memory from {min_mem:.2f} percent to {max_mem:.2f} percent.
Overall: The shape of the scatter cloud reveals whether your environment tends to be balanced, CPU constrained, or memory constrained across different asset types.

How to read it operationally:

Peaks: Dense point clusters positioned far above or below the diagonal show categories of assets where one resource dominates, which points directly to candidates for SKU adjustment or workload reclassification.
Plateaus: A tight band of points along the diagonal suggests a set of healthy templates or golden builds that should be preserved and used as standard patterns for new deployments.
Downswings: After remediation and rightsizing work, points should gradually move closer to the diagonal without creating a new cluster of underutilised hardware, so movement over time matters as much as the current shape.
Mix: When cost information and business criticality are layered on top of this scatter, high cost and heavily misaligned points stand out as priority actions for both financial and reliability impact.
Why this matters: Balanced CPU and memory allocation avoids paying for unused capacity and prevents bottlenecks that lead to slow response times and timeouts under load.
It also supports a more predictable experience for users and simplifies capacity planning by making behaviour across similar systems more consistent.
""")

            # CIO recommendations for resource allocation efficiency
            total_cost = df["cost_per_month_usd"].sum() if "cost_per_month_usd" in df.columns else 0
            pot_savings = df["potential_savings_usd"].sum() if "potential_savings_usd" in df.columns else 0

            cio_efficiency = {
                "cost": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Downsize persistently underused systems | Phase 1: Identify assets with an efficiency_score below 60 and confirm that the low score is not caused by a temporary testing or migration scenario so that the list focuses on genuinely misaligned systems.<br><br>Phase 2: Evaluate the importance, risk profile, and workload pattern of each of those assets together with service owners to decide whether they can be downsized, consolidated, or retired without harming SLAs.<br><br>Phase 3: Implement the agreed changes by reducing instance sizes, cores, or memory footprints and then review post change utilization to confirm that efficiency has improved without creating new performance bottlenecks. | - Lowers recurring infrastructure and power costs by trimming capacity from servers and instances that consistently deliver little useful work compared to their provisioned size.<br><br>- Reduces cloud or data centre invoices because over-provisioned assets are right sized instead of being left idle in the environment.<br><br>- Frees up physical or virtual capacity that can be reused for future projects without automatically triggering new hardware or subscription purchases.<br><br>- Simplifies the environment by removing unnecessary complexity, which reduces the time and effort required for patching, monitoring, and backup activities.<br><br> | Formula: Savings Ratio = Sum(potential_savings_usd)/Sum(cost_per_month_usd). Dataset: ${pot_savings:,.2f}/${total_cost:,.2f} = {(pot_savings / total_cost if total_cost else 0):.2f}. | Histogram shows a left skew tail indicating a clear subgroup of low efficiency assets that are prime candidates for downsizing. |
| Consolidate workloads across balanced nodes | Phase 1: Group workloads that run below capacity on multiple servers and identify combinations that can safely share a single balanced node without exceeding target utilization thresholds.<br><br>Phase 2: Design a consolidation plan that migrates compatible workloads onto fewer, well sized hosts while keeping redundancy and failover requirements intact for critical services.<br><br>Phase 3: Execute the consolidation, decommission the now redundant nodes, and monitor the resulting hosts for utilization stability and incident patterns over several cycles. | - Eliminates fragmentation cost by reducing the number of lightly used nodes that still incur full licensing, support, and infrastructure charges each month.<br><br>- Increases average utilization on the remaining nodes which improves return on investment for the underlying hardware or cloud capacity.<br><br>- Decreases operational overhead because teams manage and patch fewer systems while still supporting the same or higher workload volume.<br><br>- Supports a cleaner architecture where capacity pools are easier to understand and plan, which helps both finance and engineering teams forecast future needs.<br><br> | Formula: Savings = (#Nodes removed × Monthly cost per node). Dataset: visible low efficiency group below 60 percent shows where hosts can be merged. | Scatter plot reveals clear clusters of underutilised assets that can be combined without breaching acceptable utilization limits. |
| Implement automatic capacity right-sizing | Phase 1: Review current scaling and provisioning policies and map where static sizing is still used even though workloads are variable and could benefit from automatic adjustment.<br><br>Phase 2: Enable or configure auto scaling rules, scheduled scaling, or right sizing recommendations based on historical utilization, making sure guardrails are in place to avoid aggressive downsizing during temporary quiet periods.<br><br>Phase 3: Reassess workloads quarterly, refining thresholds and policies based on real consumption and stability data to keep configurations aligned with demand patterns. | - Reduces long term over-provisioning by allowing resources to contract during quiet periods instead of remaining fixed at peak capacity levels all the time.<br><br>- Lowers total infrastructure spend because environments dynamically match capacity to the actual shape of demand rather than a conservative one size fits all design.<br><br>- Minimises the risk of manual sizing mistakes by shifting repetitive adjustment work from people to system driven policies that follow transparent rules.<br><br>- Supports sustainable growth because new workloads can be onboarded into an environment that already adapts capacity automatically instead of requiring constant manual tuning.<br><br> | Formula: Avoided Cost = (Over-provisioned capacity × Unit cost). Dataset: visible imbalance between CPU and memory utilization indicates where right sizing automation will provide immediate benefits. | Charts confirm multiple misaligned resource ratios where automatic policies would keep utilization closer to the efficient band over time. |
""",
                "performance": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Enable dynamic resource scheduling | Phase 1: Activate or configure scheduling capabilities in the platform so that CPU and memory intensive workloads can be moved or balanced automatically based on live utilization readings rather than static assignments.<br><br>Phase 2: Tune the scheduling frequency, thresholds, and preferred placement rules so that movements are frequent enough to smooth performance but not so aggressive that they create instability or unnecessary churn.<br><br>Phase 3: Monitor response times, queue depths, and error rates after introducing dynamic scheduling and adjust policies as needed to find a stable equilibrium between performance and movement overhead. | - Improves overall system responsiveness because active workloads receive the resources they need when they need them instead of being stuck on overloaded nodes.<br><br>- Reduces hotspots where a few nodes run very hot while others sit idle, which stabilises performance during peak windows and batch runs.<br><br>- Increases throughput for multi tenant or shared environments by using idle capacity more effectively across different services and applications.<br><br>- Strengthens resilience because the platform can react to imbalance automatically without waiting for a manual intervention from operations teams.<br><br> | Formula: Performance Gain = (Reduced latency × Transactions). Dataset: scatter points below and above the diagonal show high CPU or memory pairings that benefit from smarter placement. | Better balance between CPU and memory utilization directly reduces latency and queue time for user transactions. |
| Optimize workload classification | Phase 1: Categorize workloads into classes such as steady state, bursty, batch, or latency sensitive using historic utilization and business requirements so that each category can be treated differently.<br><br>Phase 2: Map each workload class to an appropriate resource configuration and scaling policy that reflects its behaviour, rather than using a single generic template for all workloads.<br><br>Phase 3: Validate stability and performance after reclassification by tracking key indicators and adjusting the mapping where results do not meet expectations. | - Enhances predictability and throughput because workloads receive resource patterns that match the way they actually use CPU and memory over time.<br><br>- Reduces the number of surprise performance incidents where a misclassified workload either starves resources or sits excessively over-provisioned.<br><br>- Improves planning for future capacity because usage patterns are grouped into clearer segments that are easier to model and forecast.<br><br>- Supports more precise SLA design since workload classes can be tied to distinct service level expectations and capacity rules.<br><br> | Formula: Time Saved = (Reduced manual adjustment × Hours saved). Dataset: variation in scatter pattern confirms that some workloads are not matched to the right configuration type. | Histogram centralizes efficiency after proper allocation and shows a tighter distribution around the desired efficiency band. |
| Predictive load balancing | Phase 1: Analyse historical utilization trends, business calendars, and event schedules to anticipate when demand spikes are likely to occur for different services and assets.<br><br>Phase 2: Use those predictions to proactively adjust capacity or rebalance workloads ahead of the spike, so that systems enter peak windows with headroom rather than reacting only after performance drops.<br><br>Phase 3: Measure outcome each quarter by comparing performance, incident counts, and scaling actions during predicted peaks against previous periods without predictive balancing. | - Reduces performance dips during peak usage by ensuring that resources are already aligned with anticipated load before customers start to feel impact.<br><br>- Lowers the number of emergency interventions needed during busy periods because environments are primed with the right capacity mix in advance.<br><br>- Improves adherence to SLAs for critical business times such as month end, campaigns, or enrolment periods by smoothing resource pressure ahead of time.<br><br>- Provides a feedback loop that refines forecasting models and leads to progressively more accurate capacity planning over time.<br><br> | Formula: SLA breaches avoided × Penalty cost. Dataset: efficiency drop before known peak periods indicates where predictive balancing will prevent degradation. | Visual trend of imbalance during spikes confirms that timing and anticipation of load are crucial to maintaining stable performance. |
""",
                "satisfaction": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Communicate optimization impact to business units | Phase 1: Prepare simple reports that explain recent resource allocation optimizations, the actions taken, and the changes seen in performance and stability for the affected services.<br><br>Phase 2: Share these reports with business units in quarterly reviews, making sure to link technical improvements to outcomes they recognise such as fewer slowdowns or faster page loads.<br><br>Phase 3: Gather qualitative feedback on user experience and adjust the focus of future optimization waves to address areas still perceived as weak. | - Improves perception of reliability because stakeholders can see tangible evidence that resource tuning is directly improving their everyday applications.<br><br>- Increases trust between IT and business teams by making optimisation work visible instead of treating it as a purely technical activity with hidden benefits.<br><br>- Encourages collaboration when deciding future priorities because business owners understand the link between resource balance and service quality.<br><br>- Reduces resistance to change when rightsizing or consolidation work is proposed since users appreciate the context and expected outcomes.<br><br> | Formula: Complaints avoided × Handling cost. Dataset: rising efficiency average correlates with fewer performance related incidents and tickets. | Scatter trend shows better alignment of utilization, which typically matches a drop in user reported slowness. |
| Prioritize user-facing applications for optimal allocation | Phase 1: Map key customer facing services and internal line of business applications onto the efficiency and balance metrics so that high visibility systems are clearly identified in the dataset.<br><br>Phase 2: Set and maintain a minimum efficiency threshold, such as at least 80 percent, for those applications and adjust capacity to keep them inside that efficient and balanced band.<br><br>Phase 3: Track satisfaction scores, NPS, or ticket volumes for those apps after tuning to confirm that users experience smoother performance and fewer disruptions. | - Ensures smoother user experience for the applications that matter most to customers and frontline staff, which directly influences satisfaction and retention.<br><br>- Reduces the number of high impact incidents in customer facing journeys, thereby protecting brand perception and revenue streams.<br><br>- Helps IT teams justify focused investment in resource tuning for a small set of critical services rather than spreading effort too thinly across low impact systems.<br><br>- Aligns technical priorities with business value by explicitly linking resource balance to high priority outcomes such as order success rates or task completion times.<br><br> | Formula: SLA uplift × Customer base. Dataset: efficiency band above 80 percent yields the best stability profile for key applications. | Histogram high zone supports this threshold by showing that better balanced assets tend to perform more consistently. |
| Provide proactive alerts for unbalanced systems | Phase 1: Develop monitoring rules that trigger when an asset’s efficiency_score drops below a defined threshold such as 60, and make sure those alerts are routed to the right support teams.<br><br>Phase 2: Integrate these alerts into operational dashboards so that unbalanced systems are visible in daily stand ups and can be addressed before users notice degradation.<br><br>Phase 3: Track how often alerts are raised, how quickly they are resolved, and whether associated incidents or slowdowns decline after remediation work. | - Prevents customer facing slowdowns by catching resource imbalance early, before it escalates into noticeable performance issues for end users.<br><br>- Reduces the volume of reactive firefighting because teams can address misalignment proactively during planned windows instead of during emergencies.<br><br>- Improves operational discipline by giving a clear, quantitative signal that complements subjective observations about performance.<br><br>- Provides historical data about recurring problem areas, which helps in long term design improvements and platform refactoring decisions.<br><br> | Formula: Incident reduction × Handling cost. Dataset: low efficiency points on the graphs correspond to prior outage or slowdown incidents in many environments. | Graph indicates clear risk areas below the threshold, which supports the case for alert driven remediation. |
"""
            }
            render_cio_tables("Resource Allocation Efficiency — CIO Recommendations", cio_efficiency)

    # =========================================================
    # 2️⃣ Rightsizing Recommendations by Component
    # =========================================================
    with st.expander("📌 Rightsizing Recommendations by Component"):
        if {"component_type", "avg_cpu_utilization"} <= set(df.columns):

            comp_avg = df.groupby("component_type")["avg_cpu_utilization"].mean().reset_index()

            # Graph 1: Bar chart for CPU utilization by component
            fig_comp_bar = px.bar(
                comp_avg,
                x="component_type",
                y="avg_cpu_utilization",
                title="Average CPU Utilization by Component Type",
                labels={"avg_cpu_utilization": "CPU Utilization (%)", "component_type": "Component Type"}
            )
            fig_comp_bar.update_traces(marker_color=PX_SEQ[0])
            st.plotly_chart(fig_comp_bar, use_container_width=True, key="comp_bar")

            # --- Analysis for Graph 1 (Bar) ---
            top = comp_avg.loc[comp_avg["avg_cpu_utilization"].idxmax()]
            low = comp_avg.loc[comp_avg["avg_cpu_utilization"].idxmin()]
            avg = comp_avg["avg_cpu_utilization"].mean()

            st.write(f"""
What this graph is: A bar chart showing average CPU utilization by component type, comparing how hard each category is working on average.

X-axis: Component types across the environment.
Y-axis: Average CPU utilization in percent for each component type.
What it shows in your data: {top['component_type']} has the highest average utilization at {top['avg_cpu_utilization']:.2f} percent, while {low['component_type']} sits lowest at {low['avg_cpu_utilization']:.2f} percent. The overall mean across all components is {avg:.2f} percent, which highlights both pressure on the top categories and headroom on the lower ones.
Overall: The spread between the top and bottom bars shows where additional capacity or protection may be needed and where downsizing is likely safe without harming performance.

How to read it operationally:

Peaks: Focus on the highest bars first because those component types are closest to saturation and most likely to cause performance constraints or incidents during busy periods.
Plateaus: When many components cluster around a mid to high range, enforce auto scaling, rate limits, and threshold policies to keep enough buffer above normal operating conditions.
Downswings: For component types with consistently low utilization, validate whether the low numbers reflect genuine over-provisioning, legacy systems, or an upcoming growth plan before rightsizing or consolidating them.
Mix: Combine this chart with cost and licensing information so that high utilization, high cost components receive protection and optimisation, while low utilization, high cost components are aggressively right sized.
Why this matters: Mis sized components create both cost and reliability debt because wasteful capacity consumes budget while under protected hot spots drive outages and slowdowns.
It also helps determine where a small number of targeted actions will disproportionately improve performance stability and financial efficiency.
""")

            # Graph 2: Line chart for sorted CPU utilization trend
            comp_sorted = comp_avg.sort_values("avg_cpu_utilization", ascending=False)
            fig_comp_line = px.line(
                comp_sorted,
                x="component_type",
                y="avg_cpu_utilization",
                title="CPU Utilization Trend by Component Type",
                markers=True
            )
            fig_comp_line.update_traces(line=dict(color=PX_SEQ[1]))
            st.plotly_chart(fig_comp_line, use_container_width=True, key="comp_line")

            # --- Analysis for Graph 2 (Line) ---
            st.write(f"""
What this graph is: A ranked line chart showing CPU utilization trends across component types from highest to lowest.

X-axis: Component type, ordered from most utilized to least utilized.
Y-axis: Average CPU utilization in percent for each component type.
What it shows in your data: The descending slope visualizes the gap between the hottest component types at the left and the long tail of components with ample headroom at the right. The position where the curve bends marks the transition between components that need capacity protection and those that can likely be downsized or consolidated.
Overall: The shape of the curve exposes whether most of the workload strain is concentrated in a few key components or more evenly spread across the estate.

How to read it operationally:

Peaks: The steep initial segment on the left signals components that should receive additional safeguards such as extra capacity buffers, stronger monitoring, and stricter change control because they carry a disproportionate share of load.
Plateaus: A flat or gently sloping middle segment indicates a band of components with similar utilization, which can be standardised into common templates and monitored for drift over time.
Downswings: A long gentle tail at the right highlights components that rarely approach their limits and are therefore prime candidates for rightsizing, consolidation, or even retirement if they are also low value or legacy.
Mix: Use this ranked view to define practical thresholds, such as components above 80 percent utilisation requiring protection and those below 40 percent being reviewed for optimisation, then tie actions directly to those zones.
Why this matters: The slope of the line exposes systemic imbalance in how compute capacity is consumed, which in turn affects both resilience and cost.
It also gives a clear and visual way to prioritise engineering and financial effort so that the loudest performance risks and quietest underutilised assets are managed deliberately rather than by guesswork.
""")

            # CIO recommendations for component rightsizing
            total_cost = df["cost_per_month_usd"].sum() if "cost_per_month_usd" in df.columns else 0
            pot_savings = df["potential_savings_usd"].sum() if "potential_savings_usd" in df.columns else 0

            cio_rightsize = {
                "cost": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Downsize consistently low-utilization components | Phase 1: Identify component types and individual assets with average CPU utilization below a threshold such as 40 percent and confirm that the pattern is stable over several reporting periods rather than a temporary lull.<br><br>Phase 2: Work with application and service owners to plan migrations, resizing, or removal of capacity for those components while ensuring that redundancy, DR, and regulatory requirements remain intact.<br><br>Phase 3: Execute the downsizing actions, track realised savings in monthly cost reports, and verify that performance and incident rates for dependent services remain within acceptable levels. | - Reduces recurring infrastructure expenses by aligning provisioned capacity with actual utilisation, which directly lowers compute and hosting costs over time.<br><br>- Shrinks the number of low value assets that still consume maintenance, support, and licensing resources without delivering proportional benefit.<br><br>- Creates a leaner estate, which simplifies patching, backup, and monitoring because there are fewer underused components to manage.<br><br>- Frees budget that can be reinvested into strengthening high utilisation or business critical components that genuinely need more capacity or redundancy.<br><br> | Formula: Savings Ratio = Sum(potential_savings_usd)/Sum(cost_per_month_usd). Dataset: ${pot_savings:,.2f}/${total_cost:,.2f} = {(pot_savings / total_cost if total_cost else 0):.2f}. | Bar chart shows clear low utilisation components that sit well below the average and are strong candidates for rightsizing. |
| Pool workloads across homogeneous components | Phase 1: Group components with similar hardware or virtual profiles and identify sets where workloads are light enough to be pooled together without breaching target utilisation levels.<br><br>Phase 2: Plan consolidation by moving workloads onto a smaller number of shared hosts or clusters while preserving resilience through appropriate clustering or failover configurations.<br><br>Phase 3: Decommission or repurpose the now idle components and monitor the consolidated environment closely to ensure that utilisation and performance remain healthy after the change. | - Eliminates fragmentation cost by reducing duplicate infrastructure that carries the overhead of power, cooling, and support but offers little incremental capacity benefit.<br><br>- Increases utilisation of the remaining components, which improves value for money and can delay or avoid new hardware or subscription purchases.<br><br>- Simplifies operating models and runbooks because there are fewer platforms and configurations to support over the full lifecycle.<br><br>- Supports a more flexible capacity pool where workloads can be balanced more easily across fewer, better utilised components when conditions change.<br><br> | Formula: Cost Avoidance = (#Decommissioned × Cost/Month). Dataset: low end components below 40 percent utilization populate the tail that can be pooled. | Graph shows a flattening tail where multiple lightly used components offer consolidation opportunities. |
| Adopt hybrid resource scaling | Phase 1: Classify workloads and components into those with stable, predictable demand and those with spiky or seasonal patterns so that a suitable mix of reserved and on demand capacity can be chosen.<br><br>Phase 2: Use reserved instances or long term capacity commitments for stable workloads while keeping bursty workloads on flexible, on demand or auto scaling capacity that can grow and shrink as required.<br><br>Phase 3: Review utilisation, performance, and cost alignment every six months and adjust the mix of reserved and on demand capacity to reflect changes in demand or new services coming online. | - Lowers total cost of ownership by avoiding a purely on demand model for stable workloads and a purely fixed model for volatile ones, achieving a better balance between flexibility and price.<br><br>- Reduces the risk of overpaying for idle capacity by matching the long term commitments only to workloads that genuinely require constant resources.<br><br>- Helps avoid emergency scaling decisions during peak times because bursty workloads already run on models that are designed to expand and contract smoothly.<br><br>- Provides finance and IT leadership with a clearer view of predictable spend versus variable spend, which aids budgeting and contract negotiations with providers.<br><br> | Formula: Difference between Reserved vs On-Demand pricing. Dataset: high variance components in the trend chart justify using a hybrid model instead of one size fits all. | Line chart exhibits mixed utilisation patterns that are best served by combining reserved and flexible capacity strategies. |
""",
                "performance": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Allocate high-demand workloads to top-tier components | Phase 1: Identify the top percentage of component types by utilisation and correlate them with the workloads they host to determine which services are most dependent on them.<br><br>Phase 2: Optimise those components for high demand by tuning parallelism, IO paths, and resource quotas so that they can safely handle peak loads without saturating or throttling critical processes.<br><br>Phase 3: Monitor response times and throughput for the mapped workloads and adjust allocation if new bottlenecks emerge or if other components become better suited for specific tasks. | - Ensures consistent throughput for the most demanding or business critical workloads by running them on components that are proven to handle higher utilisation reliably.<br><br>- Reduces performance incidents during peaks because capacity and configuration are aligned with the true load profile of those services.<br><br>- Improves efficiency of high tier hardware by keeping it focused on workloads that actually benefit from its capabilities rather than hosting low value, low intensity jobs.<br><br>- Supports more predictable user experience for key applications that run on these top tier components, which strengthens confidence in the platform.<br><br> | Formula: SLA gain = (Improved throughput × Tickets served). Dataset: {top['component_type']} leads in utilisation and therefore deserves carefully planned workload placement. | Chart supports aligning the heaviest workloads with the strongest components so that performance and reliability are protected. |
| Establish performance baselines per component | Phase 1: Measure typical load, latency, and error characteristics for each component type over a representative time period so that a realistic baseline is established for normal operations.<br><br>Phase 2: Define alert thresholds and variance limits around those baselines, capturing both upper and lower bands to detect saturation risk and underutilisation that signals potential mis-sizing.<br><br>Phase 3: Review baseline adherence monthly and update the baselines when architectural changes, new workloads, or growth significantly shift normal patterns. | - Prevents uncontrolled under or over scaling by giving operations teams a clear reference point for what healthy performance looks like for each component type.<br><br>- Speeds up incident triage because deviations from baseline immediately highlight whether the issue is local to a component or part of a broader systemic event.<br><br>- Improves planning and tuning efforts since engineers can see which components consistently operate near the edge of their baselines and require attention.<br><br>- Reduces false positives from naive thresholds because baselines are calibrated from real data rather than guesswork, which improves signal quality in monitoring tools.<br><br> | Formula: Efficiency variance × Load deviation. Dataset: mid tier fluctuation in the line chart illustrates where baselines can help distinguish normal from abnormal behaviour. | Line chart illustrates inconsistent performance zones that need explicit baselines to manage effectively. |
| Automate resource scaling based on utilization | Phase 1: Implement utilisation driven scaling rules at the component or cluster level so that capacity grows and shrinks in response to real load rather than fixed schedules only.<br><br>Phase 2: Tune the thresholds, cool down periods, and step sizes of scaling actions so that automation responds quickly enough to protect performance without thrashing resources or causing instability.<br><br>Phase 3: Reassess scaling performance quarterly using metrics such as avoided throttling, queue depth, and incident reduction to refine rules and ensure they still reflect current workloads. | - Maintains stable performance across varying workloads because components receive additional capacity when they need it and release it when demand falls.<br><br>- Reduces manual intervention and the risk of human error during busy times since the system can handle many adjustments autonomously.<br><br>- Improves elasticity for services that see unpredictable spikes, which helps them maintain SLAs even under sudden load surges.<br><br>- Optimises resource usage over long periods by continuously matching capacity to demand instead of relying on static over provisioning as a safety net.<br><br> | Formula: Downtime avoided × Cost/hour. Dataset: rising patterns in the utilisation trend show where automatic scaling thresholds are most urgently needed. | Trend demonstrates capacity pressure that can be mitigated by scaling policies tuned to measured utilisation. |
""",
                "satisfaction": f"""
| Recommendation | Explanation (Phased) | Benefits | Cost Calculation | Evidence & Graph Interpretation |
|---|---|---|---|---|
| Communicate rightsizing outcomes to stakeholders | Phase 1: Summarise rightsizing and component level optimisation initiatives in business friendly language, focusing on how they influenced stability and responsiveness for key services.<br><br>Phase 2: Present these outcomes in regular service review sessions, linking changes in utilisation and capacity to user facing metrics such as ticket volumes, page load times, or processing durations.<br><br>Phase 3: Track feedback and adjust future optimisation cycles to address any ongoing pain points highlighted by stakeholders. | - Builds organisational trust because business teams understand that cost savings are being pursued without compromising service quality that matters to them.<br><br>- Improves perception of IT as a proactive partner that continually tunes the environment to support business objectives rather than making opaque technical changes.<br><br>- Encourages constructive dialogue about priorities, as stakeholders can compare improvements across different services and request targeted enhancements where needed.<br><br>- Supports change management by showing the positive impact of rightsizing decisions, which reduces pushback when further optimisations are proposed.<br><br> | Formula: Complaint reduction × Handling cost. Dataset: optimised utilisation aligns with fewer performance related incidents and escalations. | Chart confirms that higher, more consistent utilisation on the right components correlates with improved stability for their consumers. |
| Protect mission-critical systems from aggressive downsizing | Phase 1: Classify systems and components by business criticality and regulatory importance so that mission critical services are clearly separated from lower tier workloads in the analysis.<br><br>Phase 2: Apply explicit downsizing exclusions or stricter guardrails to those mission critical systems so they are not inadvertently right sized in a way that jeopardises resilience or compliance.<br><br>Phase 3: Validate post action stability by closely monitoring performance and incident trends for these systems after each optimisation wave, ensuring that their risk profile remains acceptable. | - Preserves reliability for core functions that cannot tolerate downtime or degraded performance, such as financial transaction engines, order platforms, or core records systems.<br><br>- Reduces the likelihood of unintentional capacity shortages on high impact systems that would lead to severe business disruption and potential reputational damage.<br><br>- Provides clear governance and audit trails around capacity decisions for critical systems, which supports regulatory and internal compliance reviews.<br><br>- Allows aggressive rightsizing to proceed safely in non critical areas without fear that key services will be accidentally compromised by broad optimisation rules.<br><br> | Formula: SLA penalties avoided × Affected volume. Dataset: top components above 80 percent utilisation are often tied to critical workloads and must maintain adequate headroom. | Data confirms that these hot components require careful capacity retention rather than blanket downsizing. |
| Provide real-time visibility on component performance | Phase 1: Build dashboards that show live and recent utilisation, latency, and error trends for each major component type so that both IT and business stakeholders have a shared view of performance.<br><br>Phase 2: Integrate alerts into these dashboards for high and low utilisation patterns, mapping them to action playbooks so that issues are quickly understood and addressed.<br><br>Phase 3: Distribute summary reports on a monthly basis, highlighting key changes, risks, and improvements so that decision makers stay informed without needing to interpret raw metrics. | - Enhances satisfaction through transparency because stakeholders can see how components are behaving and understand the context behind incidents or slowdowns.<br><br>- Shortens the time needed to explain and resolve performance issues since everyone is working from the same current data and history rather than conflicting anecdotes.<br><br>- Encourages data driven decision making around capacity, investment, and decommissioning because performance evidence is surfaced clearly and regularly.<br><br>- Reduces the need for manual reporting and one off analysis requests, freeing operations and engineering teams to focus on improvements instead of constant status updates.<br><br> | Formula: Time saved from manual reporting × Cost/hour. Dataset: line chart validates the need for ongoing visibility by showing clear variation across components. | Line chart demonstrates why continuous monitoring and reporting are necessary to maintain confidence in system behaviour over time. |
"""
            }
            render_cio_tables("Rightsizing by Component — CIO Recommendations", cio_rightsize)
